from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from datetime import timezone
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.contracts import WS001CommandName, WS001QueryName, command_contracts, query_contracts
from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.inbound_intake import InboundMessageFixture, InboundIntakeSubmission
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.intake import DETERMINISTIC_INTAKE_MODE, IntakeItem
from yarvis_api.models.message import Message
from yarvis_api.models.organization import Organization
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.event import DomainEventRead
from yarvis_api.schemas.intake import IntakeDetailRead, MessageRead


RECEIVE_INTAKE_CONTRACT = command_contracts[WS001CommandName.RECEIVE_INTAKE]
REGISTER_MESSAGE_CONTRACT = command_contracts[WS001CommandName.REGISTER_MESSAGE]
RETRIEVE_INTAKE_DETAIL_CONTRACT = query_contracts[WS001QueryName.RETRIEVE_DETERMINISTIC_INTAKE_DETAIL]


def _principal_organization_id(principal: AuthenticatedPrincipal) -> UUID:
    if principal.organization_id is None:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="trusted principal organization is required",
            details={"missing": "organization_id"},
        )
    try:
        return UUID(principal.organization_id)
    except ValueError as error:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="trusted principal organization identifier is invalid",
            details={"organization_id": principal.organization_id},
        ) from error


@dataclass(slots=True)
class InboundIntakeService:
    persistence: PersistenceRuntime

    def submit(self, submission: InboundIntakeSubmission) -> UUID:
        enforce_command_boundary(
            RECEIVE_INTAKE_CONTRACT,
            metadata=submission.metadata,
            principal=submission.principal,
        )
        idempotency_key = submission.metadata.idempotency_key
        if idempotency_key is None:
            raise ApplicationError(
                code=ApplicationErrorCode.PRECONDITION_FAILED,
                message="idempotency key is required for deterministic inbound intake",
                details={"contract": RECEIVE_INTAKE_CONTRACT.interaction_contract_id},
            )
        idempotency_fingerprint = self._idempotency_fingerprint(submission)
        organization_id = _principal_organization_id(submission.principal)

        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                if session.get(Organization, organization_id) is None:
                    raise ApplicationError(
                        code=ApplicationErrorCode.AUTHORIZATION_DENIED,
                        message="trusted principal organization is not recognized",
                        details={"organization_id": str(organization_id)},
                    )
                existing = self._find_by_idempotency_key(session, organization_id, idempotency_key)
                if existing is not None:
                    return self._replay_intake_id(existing, idempotency_key, idempotency_fingerprint)

                intake = self._create_intake(
                    session=session,
                    fixture=submission.fixture,
                    submission=submission,
                    organization_id=organization_id,
                    idempotency_key=idempotency_key,
                    idempotency_fingerprint=idempotency_fingerprint,
                )
                message = self._create_message(session=session, fixture=submission.fixture, submission=submission, intake=intake)
                self._record_events(session=session, intake=intake, message=message, submission=submission)
                intake_id = intake.id
                unit_of_work.commit()
        except IntegrityError as error:
            if not self._is_idempotency_unique_violation(error):
                raise
            return self._resolve_concurrent_replay(error, organization_id, idempotency_key, idempotency_fingerprint)

        return intake_id

    def load_detail(self, session: Session, intake_id: UUID) -> IntakeDetailRead:
        intake = session.get(IntakeItem, intake_id)
        if intake is None:
            raise ApplicationError(
                code=ApplicationErrorCode.RESOURCE_NOT_FOUND,
                message="intake item not found",
                details={"intake_item_id": str(intake_id)},
            )

        message = session.scalar(
            select(Message)
            .where(Message.intake_item_id == intake_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        intake_events = session.scalars(
            select(DomainEvent)
            .where(DomainEvent.aggregate_type == "intake_item")
            .where(DomainEvent.aggregate_id == intake_id)
            .order_by(DomainEvent.occurred_at, DomainEvent.recorded_at, DomainEvent.id)
        ).all()
        message_events: list[DomainEvent] = []
        if message is not None:
            message_events = session.scalars(
                select(DomainEvent)
                .where(DomainEvent.aggregate_type == "message")
                .where(DomainEvent.aggregate_id == message.id)
                .order_by(DomainEvent.occurred_at, DomainEvent.recorded_at, DomainEvent.id)
            ).all()

        return IntakeDetailRead(
            id=intake.id,
            intake_number=intake.intake_number,
            source_type=intake.source_type,
            content_type=intake.content_type,
            title=intake.title,
            text_content=intake.text_content,
            original_filename=intake.original_filename,
            mime_type=intake.mime_type,
            organization_id=intake.organization_id,
            person_id=intake.person_id,
            case_id=intake.case_id,
            received_at=intake.received_at,
            created_at=intake.created_at,
            source_metadata=intake.source_metadata,
            trace_metadata=intake.trace_metadata,
            message=MessageRead.model_validate(message) if message is not None else None,
            events=[
                DomainEventRead.model_validate(event)
                for event in sorted(
                    (*intake_events, *message_events),
                    key=lambda event: (event.occurred_at, event.recorded_at, str(event.id)),
                )
            ],
        )

    def _create_intake(
        self,
        *,
        session: Session,
        fixture: InboundMessageFixture,
        submission: InboundIntakeSubmission,
        organization_id: UUID,
        idempotency_key: str,
        idempotency_fingerprint: str,
    ) -> IntakeItem:
        intake = IntakeItem(
            source_type=fixture.external_source.value,
            content_type=fixture.content_type,
            title=fixture.subject,
            text_content=fixture.text_body,
            mime_type=fixture.content_type,
            received_at=fixture.received_timestamp,
            source_metadata={
                "external_source": fixture.external_source.value,
                "external_message_id": fixture.external_message_id,
                "connector_delivery_id": fixture.connector_delivery_id,
                "sender": fixture.sender,
                "recipients": list(fixture.recipients),
                "subject": fixture.subject,
                "text_body": fixture.text_body,
                "html_body": fixture.html_body,
                "source_timestamp": fixture.source_timestamp.isoformat(),
                "received_timestamp": fixture.received_timestamp.isoformat(),
                "headers": fixture.headers,
            },
            trace_metadata=self._trace_metadata(submission),
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            intake_mode=DETERMINISTIC_INTAKE_MODE,
        )
        session.add(intake)
        session.flush()
        return intake

    def _create_message(
        self,
        *,
        session: Session,
        fixture: InboundMessageFixture,
        submission: InboundIntakeSubmission,
        intake: IntakeItem,
    ) -> Message:
        enforce_command_boundary(
            REGISTER_MESSAGE_CONTRACT,
            metadata=submission.metadata,
            principal=submission.principal,
        )

        message = Message(
            intake_item_id=intake.id,
            external_source=fixture.external_source.value,
            external_message_id=fixture.external_message_id,
            connector_delivery_id=fixture.connector_delivery_id,
            sender=fixture.sender,
            recipients=list(fixture.recipients),
            subject=fixture.subject,
            text_body=fixture.text_body,
            html_body=fixture.html_body,
            source_timestamp=fixture.source_timestamp,
            received_at=fixture.received_timestamp,
            headers=fixture.headers,
            trace_metadata=self._trace_metadata(submission),
        )
        session.add(message)
        session.flush()
        return message

    def _find_by_idempotency_key(
        self,
        session: Session,
        organization_id: UUID,
        idempotency_key: str,
    ) -> IntakeItem | None:
        return session.scalar(
            select(IntakeItem)
            .where(IntakeItem.organization_id == organization_id)
            .where(IntakeItem.idempotency_key == idempotency_key)
        )

    def _replay_intake_id(
        self,
        intake: IntakeItem,
        idempotency_key: str,
        idempotency_fingerprint: str,
    ) -> UUID:
        if intake.idempotency_fingerprint != idempotency_fingerprint:
            raise ApplicationError(
                code=ApplicationErrorCode.CONFLICT,
                message="idempotency key was previously used for a different inbound request",
                details={"idempotency_key": idempotency_key},
            )
        return intake.id

    def _resolve_concurrent_replay(
        self,
        original_error: IntegrityError,
        organization_id: UUID,
        idempotency_key: str,
        idempotency_fingerprint: str,
    ) -> UUID:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            intake = self._find_by_idempotency_key(unit_of_work.session, organization_id, idempotency_key)
            if intake is None:
                raise original_error
            return self._replay_intake_id(intake, idempotency_key, idempotency_fingerprint)

    @staticmethod
    def _is_idempotency_unique_violation(error: IntegrityError) -> bool:
        return (
            isinstance(error.orig, UniqueViolation)
            and error.orig.diag.constraint_name == "uq_intake_items_organization_id_idempotency_key"
        )

    @staticmethod
    def _idempotency_fingerprint(submission: InboundIntakeSubmission) -> str:
        """Hash immutable inbound content; transport correlation and authority are retry metadata."""

        fixture = submission.fixture
        request = {
            "external_source": fixture.external_source.value,
            "external_message_id": fixture.external_message_id,
            "connector_delivery_id": fixture.connector_delivery_id,
            "sender": fixture.sender,
            "recipients": list(fixture.recipients),
            "subject": fixture.subject,
            "text_body": fixture.text_body,
            "html_body": fixture.html_body,
            "content_type": fixture.content_type,
            "source_timestamp": fixture.source_timestamp.astimezone(timezone.utc).isoformat(),
            "received_timestamp": fixture.received_timestamp.astimezone(timezone.utc).isoformat(),
            "headers": fixture.headers,
        }
        canonical = dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return sha256(canonical.encode("utf-8")).hexdigest()

    def _record_events(self, *, session: Session, intake: IntakeItem, message: Message, submission: InboundIntakeSubmission) -> None:
        correlation_id = UUID(str(submission.metadata.correlation_id))
        causation_id = UUID(str(submission.metadata.causation_id)) if submission.metadata.causation_id is not None else None
        record_event(
            session,
            event_type="intake.received",
            aggregate_type="intake_item",
            aggregate_id=intake.id,
            organization_id=intake.organization_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            payload={
                "source_type": intake.source_type,
                "external_message_id": message.external_message_id,
                "message_id": str(message.id),
            },
        )
        record_event(
            session,
            event_type="message.registered",
            aggregate_type="message",
            aggregate_id=message.id,
            organization_id=intake.organization_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            payload={
                "intake_item_id": str(intake.id),
                "message_id": str(message.id),
                "external_message_id": message.external_message_id,
                "sender": message.sender,
                "subject": message.subject,
            },
        )

    def _trace_metadata(self, submission: InboundIntakeSubmission) -> dict[str, object]:
        return {
            "command_id": submission.metadata.command_id,
            "correlation_id": submission.metadata.correlation_id,
            "causation_id": submission.metadata.causation_id,
            "idempotency_key": submission.metadata.idempotency_key,
            "principal": {
                "actor_id": submission.principal.actor_id,
                "organization_id": submission.principal.organization_id,
                "roles": list(submission.principal.roles),
                "permissions": list(submission.principal.permissions),
                "authority": submission.principal.authority,
                "authentication_method": submission.principal.authentication_method,
                "authenticated_at": submission.principal.authenticated_at.isoformat(),
                "is_system_actor": submission.principal.is_system_actor,
                "correlation_id": submission.principal.correlation_id,
            },
        }


@dataclass(frozen=True, slots=True)
class InboundIntakeQueryService:
    """Governed detail retrieval for organization-owned deterministic intake."""

    intake_service: InboundIntakeService

    def load_detail(
        self,
        session: Session,
        intake_id: UUID,
        principal: AuthenticatedPrincipal,
        metadata: RequestMetadata,
    ) -> IntakeDetailRead:
        enforce_query_boundary(
            RETRIEVE_INTAKE_DETAIL_CONTRACT,
            metadata=metadata,
            principal=principal,
        )
        organization_id = _principal_organization_id(principal)
        intake = session.get(IntakeItem, intake_id)
        if intake is None or intake.organization_id is None or intake.organization_id != organization_id:
            raise ApplicationError(
                code=ApplicationErrorCode.RESOURCE_NOT_FOUND,
                message="intake item not found",
                details={"intake_item_id": str(intake_id)},
            )
        return self.intake_service.load_detail(session, intake_id)

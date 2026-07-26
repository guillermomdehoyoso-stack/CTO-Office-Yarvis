"""Governed WS-002A Intake operational-context association services."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID, uuid4

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS002CommandName, WS002QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.operational_context import AssociateIntakeOperationalContextCommand
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.intake import DETERMINISTIC_INTAKE_MODE, IntakeItem
from yarvis_api.models.operational_context import ConnectorMapping, IntakeOperationalContextAssociation, Project, Site
from yarvis_api.models.organization import Organization
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.operational_context import IntakeOperationalContextAssociationRead
from yarvis_api.services.inbound_intake import _principal_organization_id


ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT_CONTRACT = command_contracts[
    WS002CommandName.ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT
]
RETRIEVE_INTAKE_OPERATIONAL_CONTEXT_CONTRACT = query_contracts[
    WS002QueryName.RETRIEVE_INTAKE_OPERATIONAL_CONTEXT
]
_IDEMPOTENCY_CONSTRAINT = "uq_ioca_org_idempotency_key"


def _not_found() -> ApplicationError:
    return ApplicationError(
        code=ApplicationErrorCode.RESOURCE_NOT_FOUND,
        message="operational context resource not found",
        details={"resource": "operational_context"},
    )


@dataclass(slots=True)
class IntakeOperationalContextAssociationService:
    persistence: PersistenceRuntime

    def associate(
        self,
        command: AssociateIntakeOperationalContextCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> IntakeOperationalContextAssociationRead:
        enforce_command_boundary(
            ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT_CONTRACT,
            metadata=metadata,
            principal=principal,
        )
        organization_id = _principal_organization_id(principal)
        idempotency_key = metadata.idempotency_key
        if idempotency_key is None:
            raise ApplicationError(
                code=ApplicationErrorCode.PRECONDITION_FAILED,
                message="idempotency key is required for operational-context association",
                details={"contract": ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT_CONTRACT.interaction_contract_id},
            )
        fingerprint = self._fingerprint(command, metadata)
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                existing_replay = self._find_by_idempotency_key(session, organization_id, idempotency_key)
                if existing_replay is not None:
                    return self._replay(existing_replay, fingerprint, idempotency_key)
                self._validate_context(session, command, organization_id)
                existing_association = session.scalar(
                    select(IntakeOperationalContextAssociation).where(
                        IntakeOperationalContextAssociation.intake_item_id == command.intake_item_id
                    )
                )
                if existing_association is not None:
                    raise self._conflict("intake item already has an immutable operational-context association")
                association = IntakeOperationalContextAssociation(
                    id=uuid4(),
                    intake_item_id=command.intake_item_id,
                    organization_id=organization_id,
                    site_id=command.site_id,
                    project_id=command.project_id,
                    connector_mapping_id=command.connector_mapping_id,
                    idempotency_key=idempotency_key,
                    idempotency_fingerprint=fingerprint,
                    actor_id=principal.actor_id,
                    correlation_id=UUID(metadata.correlation_id),
                    causation_id=UUID(metadata.causation_id) if metadata.causation_id is not None else None,
                )
                session.add(association)
                session.flush()
                record_event(
                    session,
                    event_type="intake.operational_context_associated",
                    aggregate_type="intake_item",
                    aggregate_id=command.intake_item_id,
                    organization_id=organization_id,
                    correlation_id=association.correlation_id,
                    causation_id=association.causation_id,
                    payload={
                        "interaction_contract_id": "IC-INBOX-EVT-001",
                        "association_id": str(association.id),
                        "site_id": str(association.site_id),
                        "project_id": str(association.project_id),
                        "connector_mapping_id": str(association.connector_mapping_id)
                        if association.connector_mapping_id is not None
                        else None,
                        "actor_id": association.actor_id,
                    },
                )
                result = self._to_read(association)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if not self._is_idempotency_unique_violation(error):
                raise
            return self._resolve_concurrent_replay(organization_id, idempotency_key, fingerprint, error)

    def _validate_context(
        self,
        session: Session,
        command: AssociateIntakeOperationalContextCommand,
        organization_id: UUID,
    ) -> None:
        if session.get(Organization, organization_id) is None:
            raise _not_found()
        intake = session.get(IntakeItem, command.intake_item_id)
        if (
            intake is None
            or intake.organization_id != organization_id
            or intake.intake_mode != DETERMINISTIC_INTAKE_MODE
        ):
            raise _not_found()
        site = session.get(Site, command.site_id)
        if site is None or site.organization_id != organization_id:
            raise _not_found()
        project = session.get(Project, command.project_id)
        if (
            project is None
            or project.organization_id != organization_id
            or project.site_id != command.site_id
        ):
            raise _not_found()
        if command.connector_mapping_id is not None:
            mapping = session.get(ConnectorMapping, command.connector_mapping_id)
            if (
                mapping is None
                or mapping.organization_id != organization_id
                or mapping.project_id != command.project_id
            ):
                raise _not_found()

    def _find_by_idempotency_key(
        self, session: Session, organization_id: UUID, idempotency_key: str
    ) -> IntakeOperationalContextAssociation | None:
        return session.scalar(
            select(IntakeOperationalContextAssociation)
            .where(IntakeOperationalContextAssociation.organization_id == organization_id)
            .where(IntakeOperationalContextAssociation.idempotency_key == idempotency_key)
        )

    def _replay(
        self,
        association: IntakeOperationalContextAssociation,
        fingerprint: str,
        idempotency_key: str,
    ) -> IntakeOperationalContextAssociationRead:
        if association.idempotency_fingerprint != fingerprint:
            raise self._conflict("idempotency key was previously used for a different operational-context command")
        return self._to_read(association)

    def _resolve_concurrent_replay(
        self, organization_id: UUID, idempotency_key: str, fingerprint: str, original_error: IntegrityError
    ) -> IntakeOperationalContextAssociationRead:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            association = self._find_by_idempotency_key(unit_of_work.session, organization_id, idempotency_key)
            if association is None:
                raise original_error
            return self._replay(association, fingerprint, idempotency_key)

    @staticmethod
    def _fingerprint(command: AssociateIntakeOperationalContextCommand, metadata: RequestMetadata) -> str:
        command_content = {
            "intake_item_id": str(command.intake_item_id),
            "site_id": str(command.site_id),
            "project_id": str(command.project_id),
            "connector_mapping_id": str(command.connector_mapping_id) if command.connector_mapping_id else None,
            "correlation_id": metadata.correlation_id,
        }
        canonical = dumps(command_content, separators=(",", ":"), sort_keys=True)
        return sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_idempotency_unique_violation(error: IntegrityError) -> bool:
        return isinstance(error.orig, UniqueViolation) and error.orig.diag.constraint_name == _IDEMPOTENCY_CONSTRAINT

    @staticmethod
    def _conflict(message: str) -> ApplicationError:
        return ApplicationError(
            code=ApplicationErrorCode.CONFLICT,
            message=message,
            details={"contract": "IC-INBOX-CMD-003"},
        )

    @staticmethod
    def _to_read(association: IntakeOperationalContextAssociation) -> IntakeOperationalContextAssociationRead:
        return IntakeOperationalContextAssociationRead(
            association_id=association.id,
            intake_item_id=association.intake_item_id,
            organization_id=association.organization_id,
            site_id=association.site_id,
            project_id=association.project_id,
            connector_mapping_id=association.connector_mapping_id,
            associated_at=association.associated_at,
            correlation_id=association.correlation_id,
            causation_id=association.causation_id,
        )


@dataclass(frozen=True, slots=True)
class IntakeOperationalContextQueryService:
    def retrieve(
        self,
        session: Session,
        intake_item_id: UUID,
        principal: AuthenticatedPrincipal,
        metadata: RequestMetadata,
    ) -> IntakeOperationalContextAssociationRead:
        enforce_query_boundary(RETRIEVE_INTAKE_OPERATIONAL_CONTEXT_CONTRACT, metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        intake = session.get(IntakeItem, intake_item_id)
        if intake is None or intake.organization_id != organization_id:
            raise _not_found()
        association = session.scalar(
            select(IntakeOperationalContextAssociation)
            .where(IntakeOperationalContextAssociation.intake_item_id == intake_item_id)
            .where(IntakeOperationalContextAssociation.organization_id == organization_id)
        )
        if association is None:
            raise _not_found()
        return IntakeOperationalContextAssociationService._to_read(association)

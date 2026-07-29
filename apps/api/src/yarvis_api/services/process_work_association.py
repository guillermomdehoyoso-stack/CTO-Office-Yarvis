"""Process-owned Work links and Mission Work-owned Timeline projection."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS006CommandName, WS006QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.process import LinkProcessInstanceToMissionWorkCommand, UnlinkProcessInstanceFromMissionWorkCommand
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceWorkLink
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.process import ProcessInstanceWorkLinkHistory, ProcessInstanceWorkLinkRead
from yarvis_api.services.inbound_intake import _principal_organization_id


_PROCESS_SOURCE_TYPES = {
    "process_instance.started": "process.started",
    "process_instance.transitioned": "process.transitioned",
    "process_instance.completed": "process.completed",
    "process_instance.cancelled": "process.cancelled",
}
_LINK_SOURCE_TYPES = {
    "process_instance.work_linked": "process.work_linked",
    "process_instance.work_unlinked": "process.work_unlinked",
}


def _not_found() -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "process work association not found", {"resource": "process_instance_work_link"})


def _conflict(reason: str) -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.CONFLICT, reason, {"resource": "process_instance_work_link"})


def _read(link: ProcessInstanceWorkLink) -> ProcessInstanceWorkLinkRead:
    return ProcessInstanceWorkLinkRead.model_validate(link)


@dataclass(slots=True)
class ProcessWorkAssociationService:
    """Own Process-to-Work association state without mutating either lifecycle."""

    persistence: PersistenceRuntime

    def link(self, command: LinkProcessInstanceToMissionWorkCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessInstanceWorkLinkRead:
        enforce_command_boundary(command_contracts[WS006CommandName.LINK_PROCESS_INSTANCE_TO_MISSION_WORK], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._key(metadata)
        fingerprint = self._fingerprint("link", {"process_instance_id": str(command.process_instance_id), "mission_work_item_id": str(command.mission_work_item_id), "relationship_type": command.relationship_type})
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                replay = session.scalar(select(ProcessInstanceWorkLink).where(ProcessInstanceWorkLink.organization_id == organization_id).where(ProcessInstanceWorkLink.link_idempotency_key == key))
                if replay is not None:
                    if replay.link_request_fingerprint != fingerprint:
                        raise _conflict("idempotency key was previously used for a different link request")
                    return _read(replay)
                instance = session.scalar(select(ProcessInstance).where(ProcessInstance.id == command.process_instance_id).where(ProcessInstance.organization_id == organization_id).with_for_update())
                work = session.scalar(select(MissionWorkItem).where(MissionWorkItem.id == command.mission_work_item_id).where(MissionWorkItem.organization_id == organization_id).with_for_update())
                if instance is None or work is None:
                    raise _not_found()
                duplicate = session.scalar(
                    select(ProcessInstanceWorkLink)
                    .where(ProcessInstanceWorkLink.organization_id == organization_id)
                    .where(ProcessInstanceWorkLink.process_instance_id == instance.id)
                    .where(ProcessInstanceWorkLink.mission_work_item_id == work.id)
                    .where(ProcessInstanceWorkLink.relationship_type == command.relationship_type)
                    .where(ProcessInstanceWorkLink.unlinked_at.is_(None))
                )
                if duplicate is not None:
                    raise _conflict("an active association already exists")
                if command.relationship_type == "primary":
                    primary = session.scalar(
                        select(ProcessInstanceWorkLink.id)
                        .where(ProcessInstanceWorkLink.organization_id == organization_id)
                        .where(ProcessInstanceWorkLink.process_instance_id == instance.id)
                        .where(ProcessInstanceWorkLink.relationship_type == "primary")
                        .where(ProcessInstanceWorkLink.unlinked_at.is_(None))
                    )
                    if primary is not None:
                        raise _conflict("a process instance can have only one active primary work association")
                link = ProcessInstanceWorkLink(
                    organization_id=organization_id,
                    mission_work_item_id=work.id,
                    process_instance_id=instance.id,
                    relationship_type=command.relationship_type,
                    created_by_authority_id=principal.actor_id,
                    link_idempotency_key=key,
                    link_request_fingerprint=fingerprint,
                )
                session.add(link)
                session.flush()
                payload = self._payload(link, principal, metadata, authority_scope="process.instance.work.link")
                record_event(session, event_type="process_instance.work_linked", aggregate_type="process_instance_work_link", aggregate_id=link.id, organization_id=organization_id, correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload=payload)
                result = _read(link)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if isinstance(error.orig, UniqueViolation):
                raise _conflict("an active association violates a governed uniqueness rule") from error
            raise

    def unlink(self, command: UnlinkProcessInstanceFromMissionWorkCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessInstanceWorkLinkRead:
        enforce_command_boundary(command_contracts[WS006CommandName.UNLINK_PROCESS_INSTANCE_FROM_MISSION_WORK], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._key(metadata)
        fingerprint = self._fingerprint("unlink", {"process_instance_id": str(command.process_instance_id), "link_id": str(command.link_id)})
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            link = session.scalar(
                select(ProcessInstanceWorkLink)
                .where(ProcessInstanceWorkLink.id == command.link_id)
                .where(ProcessInstanceWorkLink.process_instance_id == command.process_instance_id)
                .where(ProcessInstanceWorkLink.organization_id == organization_id)
                .with_for_update()
            )
            if link is None:
                raise _not_found()
            if link.unlink_idempotency_key is not None:
                if link.unlink_idempotency_key != key or link.unlink_request_fingerprint != fingerprint:
                    raise _conflict("association is already unlinked")
                return _read(link)
            link.unlinked_at = utc_now()
            link.unlink_idempotency_key = key
            link.unlink_request_fingerprint = fingerprint
            payload = self._payload(link, principal, metadata, authority_scope="process.instance.work.unlink")
            payload["unlinked_at"] = link.unlinked_at.isoformat()
            record_event(session, event_type="process_instance.work_unlinked", aggregate_type="process_instance_work_link", aggregate_id=link.id, organization_id=organization_id, correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload=payload)
            result = _read(link)
            unit_of_work.commit()
            return result

    @staticmethod
    def _key(metadata: RequestMetadata) -> str:
        if metadata.idempotency_key is None:
            raise ApplicationError(ApplicationErrorCode.PRECONDITION_FAILED, "idempotency key is required for process work association commands", {"resource": "process_instance_work_link"})
        return metadata.idempotency_key

    @staticmethod
    def _fingerprint(command: str, request: dict[str, object]) -> str:
        return sha256(dumps({"command": command, "request": request}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _payload(
        link: ProcessInstanceWorkLink,
        principal: AuthenticatedPrincipal,
        metadata: RequestMetadata,
        *,
        authority_scope: str,
    ) -> dict[str, object]:
        return {
            "organization_id": str(link.organization_id),
            "process_instance_id": str(link.process_instance_id),
            "mission_work_item_id": str(link.mission_work_item_id),
            "link_id": str(link.id),
            "relationship_type": link.relationship_type,
            "actor_subject_id": principal.actor_id,
            "authority_scope": authority_scope,
            "occurred_at": utc_now().isoformat(),
            "correlation_id": metadata.correlation_id,
            "causation_id": metadata.causation_id,
        }


@dataclass(frozen=True, slots=True)
class ProcessWorkAssociationQueryService:
    def list_for_work(self, session: Session, work_item_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessInstanceWorkLinkHistory:
        enforce_query_boundary(query_contracts[WS006QueryName.LIST_MISSION_WORK_PROCESS_LINKS], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        if session.scalar(select(MissionWorkItem.id).where(MissionWorkItem.id == work_item_id).where(MissionWorkItem.organization_id == organization_id)) is None:
            raise _not_found()
        links = session.scalars(select(ProcessInstanceWorkLink).where(ProcessInstanceWorkLink.organization_id == organization_id).where(ProcessInstanceWorkLink.mission_work_item_id == work_item_id).order_by(ProcessInstanceWorkLink.linked_at.asc(), ProcessInstanceWorkLink.id.asc())).all()
        return ProcessInstanceWorkLinkHistory(items=[_read(link) for link in links])

    def primary_for_instance(self, session: Session, instance_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessInstanceWorkLinkRead:
        enforce_query_boundary(query_contracts[WS006QueryName.RETRIEVE_PROCESS_INSTANCE_PRIMARY_WORK_LINK], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        link = session.scalar(select(ProcessInstanceWorkLink).where(ProcessInstanceWorkLink.organization_id == organization_id).where(ProcessInstanceWorkLink.process_instance_id == instance_id).where(ProcessInstanceWorkLink.relationship_type == "primary").where(ProcessInstanceWorkLink.unlinked_at.is_(None)))
        if link is None:
            raise _not_found()
        return _read(link)

    def history_for_instance(self, session: Session, instance_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessInstanceWorkLinkHistory:
        enforce_query_boundary(query_contracts[WS006QueryName.LIST_PROCESS_INSTANCE_WORK_LINK_HISTORY], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        if session.scalar(select(ProcessInstance.id).where(ProcessInstance.id == instance_id).where(ProcessInstance.organization_id == organization_id)) is None:
            raise _not_found()
        links = session.scalars(select(ProcessInstanceWorkLink).where(ProcessInstanceWorkLink.organization_id == organization_id).where(ProcessInstanceWorkLink.process_instance_id == instance_id).order_by(ProcessInstanceWorkLink.linked_at.asc(), ProcessInstanceWorkLink.id.asc())).all()
        return ProcessInstanceWorkLinkHistory(items=[_read(link) for link in links])


@dataclass(slots=True)
class ProcessMissionWorkTimelineProjector:
    """Mission Work-owned, replay-safe projection of Process Domain Events."""

    persistence: PersistenceRuntime

    def project_instance(self, process_instance_id: UUID) -> None:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            links = session.scalars(select(ProcessInstanceWorkLink).where(ProcessInstanceWorkLink.process_instance_id == process_instance_id).where(ProcessInstanceWorkLink.unlinked_at.is_(None))).all()
            for link in links:
                for event in session.scalars(select(DomainEvent).where(DomainEvent.aggregate_type == "process_instance").where(DomainEvent.aggregate_id == process_instance_id).where(DomainEvent.event_type.in_(_PROCESS_SOURCE_TYPES)).order_by(DomainEvent.event_sequence.asc())).all():
                    self._project(session, link, event)
            unit_of_work.commit()

    def project_link(self, link_id: UUID) -> None:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            link = session.get(ProcessInstanceWorkLink, link_id)
            if link is None:
                return
            events = session.scalars(
                select(DomainEvent)
                .where(
                    ((DomainEvent.aggregate_type == "process_instance") & (DomainEvent.aggregate_id == link.process_instance_id) & DomainEvent.event_type.in_(_PROCESS_SOURCE_TYPES))
                    | ((DomainEvent.aggregate_type == "process_instance_work_link") & (DomainEvent.aggregate_id == link.id) & DomainEvent.event_type.in_(_LINK_SOURCE_TYPES))
                )
                .order_by(DomainEvent.event_sequence.asc())
            ).all()
            for event in events:
                self._project(session, link, event)
            unit_of_work.commit()

    def _project(self, session: Session, link: ProcessInstanceWorkLink, source: DomainEvent) -> None:
        event_type = _PROCESS_SOURCE_TYPES.get(source.event_type) or _LINK_SOURCE_TYPES.get(source.event_type)
        if event_type is None:
            return
        if source.event_type in _LINK_SOURCE_TYPES and source.payload.get("mission_work_item_id") != str(link.mission_work_item_id):
            return
        exists = session.scalar(select(MissionWorkEvent.id).where(MissionWorkEvent.organization_id == link.organization_id).where(MissionWorkEvent.work_item_id == link.mission_work_item_id).where(MissionWorkEvent.source_domain_event_id == source.id))
        if exists is not None:
            return
        work = session.scalar(select(MissionWorkItem).where(MissionWorkItem.id == link.mission_work_item_id).where(MissionWorkItem.organization_id == link.organization_id).with_for_update())
        if work is None:
            return
        definition = session.scalar(select(ProcessDefinition).join(ProcessInstance, ProcessInstance.process_definition_id == ProcessDefinition.id).where(ProcessInstance.id == link.process_instance_id))
        sequence = (session.scalar(select(func.coalesce(func.max(MissionWorkEvent.sequence_number), 0)).where(MissionWorkEvent.organization_id == work.organization_id).where(MissionWorkEvent.work_item_id == work.id)) or 0) + 1
        payload = {"process_instance_id": str(link.process_instance_id), "mission_work_item_id": str(work.id), "relationship_type": link.relationship_type, "process_definition_name": definition.name if definition else None, **source.payload}
        session.add(MissionWorkEvent(organization_id=work.organization_id, work_item_id=work.id, occurred_at=source.occurred_at, event_type=event_type, actor_subject_id=source.payload.get("actor_subject_id"), payload_json=payload, sequence_number=sequence, source_domain_event_id=source.id))
        session.flush()

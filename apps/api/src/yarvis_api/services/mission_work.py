"""Governed transactional Mission Work application services."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS004CommandName, WS004QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_work import (
    AssignMissionWorkItemCommand,
    ChangeMissionWorkItemPriorityCommand,
    ChangeMissionWorkItemStatusCommand,
    CreateMissionWorkItemFromInboxCommand,
    MissionWorkItemFilters,
)
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.mission_inbox import MissionInboxItem
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.mission_work import MissionWorkItemPage, MissionWorkItemRead
from yarvis_api.services.inbound_intake import _principal_organization_id


_CREATE_CONSTRAINTS = {
    "uq_mission_work_items_inbox_identity",
    "uq_mission_work_items_source_identity",
}
_STATUSES = {"open", "assigned", "in_progress", "waiting", "resolved", "cancelled"}
_PRIORITIES = {"low", "normal", "high", "urgent"}
_TRANSITIONS = {
    "open": {"assigned", "in_progress", "waiting", "cancelled"},
    "assigned": {"open", "in_progress", "waiting", "cancelled"},
    "in_progress": {"assigned", "waiting", "resolved", "cancelled"},
    "waiting": {"assigned", "in_progress", "resolved", "cancelled"},
    "resolved": {"open"},
    "cancelled": {"open"},
}


def _not_found() -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "mission work item not found", {"resource": "mission_work_item"})


def _conflict(reason: str) -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.CONFLICT, reason, {"resource": "mission_work_item"})


def _read(item: MissionWorkItem) -> MissionWorkItemRead:
    return MissionWorkItemRead.model_validate(item)


@dataclass(slots=True)
class MissionWorkService:
    persistence: PersistenceRuntime

    def create(self, command: CreateMissionWorkItemFromInboxCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> MissionWorkItemRead:
        enforce_command_boundary(command_contracts[WS004CommandName.CREATE_MISSION_WORK_ITEM_FROM_INBOX], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                inbox = session.scalar(select(MissionInboxItem).where(MissionInboxItem.id == command.inbox_item_id).where(MissionInboxItem.organization_id == organization_id))
                if inbox is None:
                    raise _not_found()
                duplicate = session.scalar(
                    select(MissionWorkItem.id)
                    .where(MissionWorkItem.organization_id == organization_id)
                    .where(MissionWorkItem.source_type == inbox.source_type)
                    .where(MissionWorkItem.source_id == inbox.source_id)
                )
                if duplicate is not None:
                    raise _conflict("mission work item already exists for this inbox item")
                item = MissionWorkItem(
                    organization_id=organization_id,
                    inbox_item_id=inbox.id,
                    source_type=inbox.source_type,
                    source_id=inbox.source_id,
                    title=inbox.title,
                    summary=inbox.summary,
                    priority=inbox.priority if inbox.priority in _PRIORITIES else "normal",
                    created_by_subject_id=principal.actor_id,
                )
                session.add(item)
                session.flush()
                self._event(session, item, "mission.work_item_created", {"work_item_id": str(item.id), "inbox_item_id": str(item.inbox_item_id), "source_type": item.source_type, "source_id": str(item.source_id), "status": item.status, "priority": item.priority}, metadata, principal)
                result = _read(item)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if isinstance(error.orig, UniqueViolation) and error.orig.diag.constraint_name in _CREATE_CONSTRAINTS:
                raise _conflict("mission work item already exists for this inbox item") from error
            raise

    def assign(self, command: AssignMissionWorkItemCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> MissionWorkItemRead:
        return self._mutate(command.work_item_id, WS004CommandName.ASSIGN_MISSION_WORK_ITEM, metadata, principal, lambda session, item: self._assign(session, item, command.assignee_subject_id, metadata, principal))

    def change_status(self, command: ChangeMissionWorkItemStatusCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> MissionWorkItemRead:
        return self._mutate(command.work_item_id, WS004CommandName.CHANGE_MISSION_WORK_ITEM_STATUS, metadata, principal, lambda session, item: self._status(session, item, command.status, metadata, principal))

    def change_priority(self, command: ChangeMissionWorkItemPriorityCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> MissionWorkItemRead:
        return self._mutate(command.work_item_id, WS004CommandName.CHANGE_MISSION_WORK_ITEM_PRIORITY, metadata, principal, lambda session, item: self._priority(session, item, command.priority, metadata, principal))

    def _mutate(self, work_item_id: UUID, contract_name: WS004CommandName, metadata: RequestMetadata, principal: AuthenticatedPrincipal, mutation) -> MissionWorkItemRead:
        enforce_command_boundary(command_contracts[contract_name], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            item = session.scalar(select(MissionWorkItem).where(MissionWorkItem.id == work_item_id).where(MissionWorkItem.organization_id == organization_id))
            if item is None:
                raise _not_found()
            changed = mutation(session, item)
            result = _read(item)
            if changed:
                unit_of_work.commit()
            return result

    def _assign(self, session: Session, item: MissionWorkItem, assignee: str | None, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> bool:
        if assignee == item.assignee_subject_id:
            return False
        if assignee is None:
            if item.assignee_subject_id is None:
                return False
            if item.status != "assigned":
                raise _conflict("only an assigned work item can be unassigned")
            previous = item.assignee_subject_id
            item.assignee_subject_id, item.assigned_at, item.status = None, None, "open"
            self._changed(item)
            self._event(session, item, "mission.work_item_unassigned", {"work_item_id": str(item.id), "previous_assignee_subject_id": previous, "version": item.version}, metadata, principal)
            return True
        previous = item.assignee_subject_id
        item.assignee_subject_id, item.assigned_at = assignee, utc_now()
        if item.status == "open":
            item.status = "assigned"
        self._changed(item)
        self._event(session, item, "mission.work_item_assigned", {"work_item_id": str(item.id), "previous_assignee_subject_id": previous, "assignee_subject_id": assignee, "version": item.version}, metadata, principal)
        return True

    def _status(self, session: Session, item: MissionWorkItem, status: str, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> bool:
        if status not in _STATUSES:
            raise _conflict("unsupported mission work status")
        if status == item.status:
            return False
        if status not in _TRANSITIONS[item.status]:
            raise _conflict("invalid mission work status transition")
        previous = item.status
        item.status = status
        now = utc_now()
        if status == "in_progress" and item.started_at is None:
            item.started_at = now
        if status == "resolved":
            item.resolved_at = now
        elif previous == "resolved":
            item.resolved_at = None
        self._changed(item, now)
        self._event(session, item, "mission.work_item_status_changed", {"work_item_id": str(item.id), "previous_status": previous, "status": status, "version": item.version}, metadata, principal)
        return True

    def _priority(self, session: Session, item: MissionWorkItem, priority: str, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> bool:
        if priority not in _PRIORITIES:
            raise _conflict("unsupported mission work priority")
        if priority == item.priority:
            return False
        previous = item.priority
        item.priority = priority
        self._changed(item)
        self._event(session, item, "mission.work_item_priority_changed", {"work_item_id": str(item.id), "previous_priority": previous, "priority": priority, "version": item.version}, metadata, principal)
        return True

    @staticmethod
    def _changed(item: MissionWorkItem, now=None) -> None:
        item.version += 1
        item.updated_at = now or utc_now()

    @staticmethod
    def _event(session: Session, item: MissionWorkItem, event_type: str, payload: dict[str, object], metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> None:
        record_event(session, event_type=event_type, aggregate_type="mission_work_item", aggregate_id=item.id, organization_id=item.organization_id, correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload=payload)


@dataclass(frozen=True, slots=True)
class MissionWorkQueryService:
    def list(self, session: Session, principal: AuthenticatedPrincipal, metadata: RequestMetadata, filters: MissionWorkItemFilters) -> MissionWorkItemPage:
        enforce_query_boundary(query_contracts[WS004QueryName.LIST_MISSION_WORK_ITEMS], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        query = select(MissionWorkItem).where(MissionWorkItem.organization_id == organization_id)
        for column, value in ((MissionWorkItem.status, filters.status), (MissionWorkItem.priority, filters.priority), (MissionWorkItem.assignee_subject_id, filters.assignee_subject_id), (MissionWorkItem.inbox_item_id, filters.inbox_item_id), (MissionWorkItem.source_type, filters.source_type), (MissionWorkItem.source_id, filters.source_id)):
            if value is not None:
                query = query.where(column == value)
        column = {"updated_at": MissionWorkItem.updated_at, "created_at": MissionWorkItem.created_at, "priority": MissionWorkItem.priority, "status": MissionWorkItem.status}.get(filters.sort)
        if column is None:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "unsupported mission work sort field", {"sort": filters.sort})
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = session.scalars(query.order_by(column.desc(), MissionWorkItem.id.desc()).offset(filters.offset).limit(filters.limit)).all()
        return MissionWorkItemPage(items=[_read(item) for item in items], total=total, limit=filters.limit, offset=filters.offset)

    def retrieve(self, session: Session, work_item_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> MissionWorkItemRead:
        enforce_query_boundary(query_contracts[WS004QueryName.RETRIEVE_MISSION_WORK_ITEM], metadata=metadata, principal=principal)
        item = session.scalar(select(MissionWorkItem).where(MissionWorkItem.id == work_item_id).where(MissionWorkItem.organization_id == _principal_organization_id(principal)))
        if item is None:
            raise _not_found()
        return _read(item)

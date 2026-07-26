"""Deterministic Mission Inbox projection and governed query services."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS003QueryName, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_inbox import MissionInboxFilters
from yarvis_api.application.service_boundary import enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.intake import DETERMINISTIC_INTAKE_MODE, IntakeItem
from yarvis_api.models.mission_inbox import MissionInboxItem, ProjectionCheckpoint
from yarvis_api.models.operational_context import IntakeOperationalContextAssociation
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.mission_inbox import MissionInboxItemRead, MissionInboxPage
from yarvis_api.services.inbound_intake import _principal_organization_id


MISSION_INBOX_PROJECTION = "mission_inbox_v1"
MISSION_INBOX_PROJECTION_VERSION = 1
_INPUT_EVENTS = {"intake.received", "intake.operational_context_associated"}


def _not_found() -> ApplicationError:
    return ApplicationError(
        code=ApplicationErrorCode.RESOURCE_NOT_FOUND,
        message="mission inbox item not found",
        details={"resource": "mission_inbox_item"},
    )


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    projected_events: int
    last_event_sequence: int


@dataclass(slots=True)
class MissionInboxProjectionService:
    persistence: PersistenceRuntime

    def project_pending_events(self) -> ProjectionResult:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            checkpoint = self._checkpoint(session)
            events = session.scalars(
                select(DomainEvent)
                .where(DomainEvent.event_sequence > checkpoint.last_event_sequence)
                .order_by(DomainEvent.event_sequence)
            ).all()
            for event in events:
                if event.event_type in _INPUT_EVENTS:
                    self._project_event(session, event)
                checkpoint.last_event_sequence = event.event_sequence
                checkpoint.updated_at = utc_now()
            result = ProjectionResult(len(events), checkpoint.last_event_sequence)
            unit_of_work.commit()
            return result

    def rebuild_projection(self) -> ProjectionResult:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            session.execute(delete(MissionInboxItem))
            session.execute(delete(ProjectionCheckpoint).where(ProjectionCheckpoint.projection_name == MISSION_INBOX_PROJECTION))
            checkpoint = self._checkpoint(session)
            events = session.scalars(select(DomainEvent).order_by(DomainEvent.event_sequence)).all()
            for event in events:
                if event.event_type in _INPUT_EVENTS:
                    self._project_event(session, event)
                checkpoint.last_event_sequence = event.event_sequence
                checkpoint.updated_at = utc_now()
            result = ProjectionResult(len(events), checkpoint.last_event_sequence)
            unit_of_work.commit()
            return result

    @staticmethod
    def _checkpoint(session: Session) -> ProjectionCheckpoint:
        checkpoint = session.scalar(
            select(ProjectionCheckpoint).where(ProjectionCheckpoint.projection_name == MISSION_INBOX_PROJECTION)
        )
        if checkpoint is None:
            checkpoint = ProjectionCheckpoint(
                projection_name=MISSION_INBOX_PROJECTION,
                organization_id=None,
                last_event_sequence=0,
                projection_version=MISSION_INBOX_PROJECTION_VERSION,
            )
            session.add(checkpoint)
            session.flush()
        return checkpoint

    def _project_event(self, session: Session, event: DomainEvent) -> None:
        if event.organization_id is None:
            return
        if event.event_type == "intake.received":
            self._project_intake(session, event)
        elif event.event_type == "intake.operational_context_associated":
            self._project_context(session, event)

    def _project_intake(self, session: Session, event: DomainEvent) -> MissionInboxItem | None:
        intake = session.get(IntakeItem, event.aggregate_id)
        if (
            intake is None
            or intake.organization_id != event.organization_id
            or intake.intake_mode != DETERMINISTIC_INTAKE_MODE
        ):
            return None
        item = session.scalar(
            select(MissionInboxItem)
            .where(MissionInboxItem.organization_id == event.organization_id)
            .where(MissionInboxItem.source_type == "deterministic_intake")
            .where(MissionInboxItem.source_id == intake.id)
        )
        if item is None:
            item = MissionInboxItem(
                organization_id=event.organization_id,
                source_type="deterministic_intake",
                source_id=intake.id,
                intake_item_id=intake.id,
                title=intake.title.strip() if intake.title and intake.title.strip() else "Deterministic Intake",
                summary=None,
                status="open",
                priority="normal",
                received_at=intake.received_at,
                last_activity_at=event.occurred_at,
                projected_at=utc_now(),
                source_event_id=event.id,
                projection_version=MISSION_INBOX_PROJECTION_VERSION,
            )
            session.add(item)
        else:
            item.last_activity_at = max(item.last_activity_at, event.occurred_at)
            item.source_event_id = event.id
            item.projected_at = utc_now()
        session.flush()
        return item

    def _project_context(self, session: Session, event: DomainEvent) -> None:
        item = self._project_intake(session, event)
        if item is None:
            return
        association_id = event.payload.get("association_id")
        if not isinstance(association_id, str):
            return
        association = session.get(IntakeOperationalContextAssociation, UUID(association_id))
        if association is None or association.organization_id != item.organization_id:
            return
        item.site_id = association.site_id
        item.project_id = association.project_id
        item.connector_mapping_id = association.connector_mapping_id
        item.last_activity_at = max(item.last_activity_at, event.occurred_at)
        item.source_event_id = event.id
        item.projected_at = utc_now()


@dataclass(frozen=True, slots=True)
class MissionInboxQueryService:
    def list(
        self,
        session: Session,
        principal: AuthenticatedPrincipal,
        metadata: RequestMetadata,
        filters: MissionInboxFilters,
    ) -> MissionInboxPage:
        enforce_query_boundary(query_contracts[WS003QueryName.LIST_MISSION_INBOX], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        query = select(MissionInboxItem).where(MissionInboxItem.organization_id == organization_id)
        for column, value in (
            (MissionInboxItem.status, filters.status),
            (MissionInboxItem.priority, filters.priority),
            (MissionInboxItem.site_id, filters.site_id),
            (MissionInboxItem.project_id, filters.project_id),
            (MissionInboxItem.source_type, filters.source_type),
        ):
            if value is not None:
                query = query.where(column == value)
        sort_column = {
            "received_at": MissionInboxItem.received_at,
            "last_activity_at": MissionInboxItem.last_activity_at,
            "priority": MissionInboxItem.priority,
        }.get(filters.sort)
        if sort_column is None:
            raise ApplicationError(
                code=ApplicationErrorCode.VALIDATION_FAILED,
                message="unsupported mission inbox sort field",
                details={"sort": filters.sort},
            )
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = session.scalars(query.order_by(sort_column.desc(), MissionInboxItem.id.desc()).offset(filters.offset).limit(filters.limit)).all()
        return MissionInboxPage(
            items=[MissionInboxItemRead.model_validate(item) for item in items],
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    def retrieve(
        self, session: Session, inbox_item_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata
    ) -> MissionInboxItemRead:
        enforce_query_boundary(query_contracts[WS003QueryName.RETRIEVE_MISSION_INBOX_ITEM], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        item = session.scalar(
            select(MissionInboxItem)
            .where(MissionInboxItem.id == inbox_item_id)
            .where(MissionInboxItem.organization_id == organization_id)
        )
        if item is None:
            raise _not_found()
        return MissionInboxItemRead.model_validate(item)

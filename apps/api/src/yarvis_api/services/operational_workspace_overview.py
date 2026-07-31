"""Bounded, read-only composition for the organization Operational Workspace."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS008QueryName, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.service_boundary import enforce_query_boundary
from yarvis_api.models.mission_inbox import MissionInboxItem
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.operational_context import Project, Site
from yarvis_api.models.operational_task import OperationalTask, TaskDependency
from yarvis_api.models.organization import Organization
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceWorkLink
from yarvis_api.schemas.operational_workspace_overview import (
    OperationalWorkspaceActivityRead,
    OperationalWorkspaceContextRead,
    OperationalWorkspaceOverviewRead,
    OperationalWorkspaceProcessRead,
    OperationalWorkspaceSummaryRead,
    OperationalWorkspaceTaskRead,
)
from yarvis_api.services.inbound_intake import _principal_organization_id

_ACTIVE_TASK_STATUSES = ("planned", "ready", "in_progress")
_PRIORITY_ORDER = case({"urgent": 0, "high": 1, "normal": 2, "low": 3}, value=OperationalTask.priority, else_=4)


def _not_found(resource: str) -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, f"{resource} not found", {"resource": resource})


@dataclass(frozen=True, slots=True)
class OperationalWorkspaceOverviewQueryService:
    """Composes canonical state; it owns no Workspace persistence or events."""

    def retrieve(
        self,
        session: Session,
        principal: AuthenticatedPrincipal,
        metadata: RequestMetadata,
        *,
        site_id: UUID | None,
        project_id: UUID | None,
        task_limit: int,
        process_limit: int,
        activity_limit: int,
    ) -> OperationalWorkspaceOverviewRead:
        enforce_query_boundary(query_contracts[WS008QueryName.RETRIEVE_OPERATIONAL_WORKSPACE_OVERVIEW], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        organization = session.scalar(select(Organization).where(Organization.id == organization_id))
        if organization is None:
            raise _not_found("organization")
        site = self._site(session, organization_id, site_id) if site_id else None
        project = self._project(session, organization_id, project_id, site_id) if project_id else None
        context_filters = []
        if site_id:
            context_filters.extend((MissionInboxItem.organization_id == organization_id, MissionInboxItem.site_id == site_id))
        if project_id:
            context_filters.extend((MissionInboxItem.organization_id == organization_id, MissionInboxItem.project_id == project_id))

        task_base = select(OperationalTask, MissionInboxItem.site_id, MissionInboxItem.project_id).join(
            MissionWorkItem, (MissionWorkItem.id == OperationalTask.mission_work_item_id) & (MissionWorkItem.organization_id == OperationalTask.organization_id)
        ).outerjoin(MissionInboxItem, (MissionInboxItem.id == MissionWorkItem.inbox_item_id) & (MissionInboxItem.organization_id == MissionWorkItem.organization_id)).where(
            OperationalTask.organization_id == organization_id, *context_filters
        )
        active_all_rows = session.execute(task_base.where(OperationalTask.status.in_(_ACTIVE_TASK_STATUSES)).order_by(_PRIORITY_ORDER, OperationalTask.due_at.asc().nulls_last(), OperationalTask.updated_at.desc(), OperationalTask.id)).all()
        blocked_ids = set(session.scalars(select(TaskDependency.successor_task_id).join(OperationalTask, (OperationalTask.id == TaskDependency.predecessor_task_id) & (OperationalTask.organization_id == TaskDependency.organization_id)).where(TaskDependency.organization_id == organization_id, TaskDependency.closed_at.is_(None), OperationalTask.status != "completed")).all())
        blocked_all_rows = [row for row in active_all_rows if row[0].id in blocked_ids]
        active_rows = active_all_rows[:task_limit]
        blocked_rows = blocked_all_rows[:task_limit]
        active_tasks = [self._task(row, row[0].id in {item[0].id for item in blocked_rows}) for row in active_rows]
        blocked_tasks = [self._task(row, True) for row in blocked_rows]
        now = metadata.requested_at
        summary = OperationalWorkspaceSummaryRead(
            active_task_count=len(active_all_rows),
            blocked_task_count=len(blocked_all_rows),
            overdue_task_count=sum(task.due_at is not None and task.due_at < now for task, _, _ in active_all_rows),
            unassigned_task_count=sum(task.assignee_subject_id is None for task, _, _ in active_all_rows),
            active_process_count=0,
            recent_activity_count=0,
        )
        process_base = select(ProcessInstance, ProcessDefinition, MissionInboxItem.site_id, MissionInboxItem.project_id).join(
            ProcessDefinition, (ProcessDefinition.id == ProcessInstance.process_definition_id) & (ProcessDefinition.organization_id == ProcessInstance.organization_id)
        ).outerjoin(ProcessInstanceWorkLink, (ProcessInstanceWorkLink.process_instance_id == ProcessInstance.id) & (ProcessInstanceWorkLink.organization_id == ProcessInstance.organization_id) & (ProcessInstanceWorkLink.unlinked_at.is_(None)) & (ProcessInstanceWorkLink.relationship_type == "primary")).outerjoin(
            MissionWorkItem, (MissionWorkItem.id == ProcessInstanceWorkLink.mission_work_item_id) & (MissionWorkItem.organization_id == ProcessInstanceWorkLink.organization_id)
        ).outerjoin(MissionInboxItem, (MissionInboxItem.id == MissionWorkItem.inbox_item_id) & (MissionInboxItem.organization_id == MissionWorkItem.organization_id)).where(
            ProcessInstance.organization_id == organization_id, ProcessInstance.lifecycle == "active", *context_filters
        ).order_by(ProcessInstance.updated_at.desc(), ProcessInstance.id)
        process_all_rows = session.execute(process_base).all()
        process_rows = process_all_rows[:process_limit]
        processes = [OperationalWorkspaceProcessRead(id=i.id, process_definition_id=d.id, process_definition_name=d.name, lifecycle=i.lifecycle, started_at=i.created_at, updated_at=i.updated_at, site_id=s, project_id=p) for i, d, s, p in process_rows]
        summary.active_process_count = len(process_all_rows)
        activity_rows = session.execute(select(MissionWorkEvent, MissionInboxItem.site_id, MissionInboxItem.project_id).join(MissionWorkItem, (MissionWorkItem.id == MissionWorkEvent.work_item_id) & (MissionWorkItem.organization_id == MissionWorkEvent.organization_id)).outerjoin(MissionInboxItem, (MissionInboxItem.id == MissionWorkItem.inbox_item_id) & (MissionInboxItem.organization_id == MissionWorkItem.organization_id)).where(MissionWorkEvent.organization_id == organization_id, *context_filters).order_by(MissionWorkEvent.occurred_at.desc(), MissionWorkEvent.id.desc()).limit(activity_limit)).all()
        activity = [OperationalWorkspaceActivityRead(id=e.id, work_item_id=e.work_item_id, event_type=e.event_type, occurred_at=e.occurred_at, actor_subject_id=e.actor_subject_id) for e, _, _ in activity_rows]
        summary.recent_activity_count = len(activity)
        return OperationalWorkspaceOverviewRead(context=OperationalWorkspaceContextRead(organization_id=organization_id, organization_name=organization.display_name, site_id=site_id, site_reference=site.reference if site else None, project_id=project_id, project_reference=project.reference if project else None), summary=summary, active_tasks=active_tasks, blocked_tasks=blocked_tasks, active_processes=processes, recent_activity=activity)

    @staticmethod
    def _task(row, is_blocked: bool) -> OperationalWorkspaceTaskRead:
        task, site_id, project_id = row
        return OperationalWorkspaceTaskRead(id=task.id, title=task.title, status=task.status, priority=task.priority, assignee_subject_id=task.assignee_subject_id, due_at=task.due_at, version=task.version, site_id=site_id, project_id=project_id, is_blocked=is_blocked)

    @staticmethod
    def _site(session: Session, organization_id: UUID, site_id: UUID) -> Site:
        site = session.scalar(select(Site).where(Site.id == site_id, Site.organization_id == organization_id))
        if site is None:
            raise _not_found("site")
        return site

    @staticmethod
    def _project(session: Session, organization_id: UUID, project_id: UUID, site_id: UUID | None) -> Project:
        clauses = [Project.id == project_id, Project.organization_id == organization_id]
        if site_id:
            clauses.append(Project.site_id == site_id)
        project = session.scalar(select(Project).where(*clauses))
        if project is None:
            raise _not_found("project")
        return project

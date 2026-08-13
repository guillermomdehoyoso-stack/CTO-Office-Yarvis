"""Governed Mission Work Queue API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.mission_work_authority import mission_work_principal_from_envelope
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_work import AddMissionWorkItemCommentCommand, AssignMissionWorkItemCommand, ChangeMissionWorkItemPriorityCommand, ChangeMissionWorkItemStatusCommand, CreateMissionWorkItemFromInboxCommand, MissionWorkItemFilters
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.schemas.mission_work import AssignmentRequest, CommentRequest, CreateMissionWorkItemRequest, MissionWorkEventRead, MissionWorkItemPage, MissionWorkItemRead, MissionWorkTimeline, PriorityRequest, StatusRequest
from yarvis_api.schemas.process import ProcessInstanceWorkLinkHistory
from yarvis_api.schemas.operational_workspace import OperationalWorkspaceRead


router = APIRouter(prefix="/mission/work-items", tags=["mission-work"])


def _metadata(principal, command_id: str | None = None, query_id: str | None = None) -> RequestMetadata:
    return RequestMetadata(requested_at=utc_now(), correlation_id=principal.correlation_id or str(uuid4()), command_id=command_id, query_id=query_id)


def _resolved_mission_work_principal(request: Request, db: Session, *, required_scope: str):
    authenticated = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    envelope = AuthorityResolutionService().resolve(
        db, external_subject=authenticated.actor_id, selector=None,
        authentication_source=authenticated.authentication_method,
        correlation_id=authenticated.correlation_id or str(uuid4()),
    )
    return mission_work_principal_from_envelope(envelope, required_scope=required_scope)


@router.post("", response_model=MissionWorkItemRead, status_code=status.HTTP_201_CREATED)
def create_work_item(payload: CreateMissionWorkItemRequest, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.create")
    return request.app.state.yarvis.mission_work_service.create(CreateMissionWorkItemFromInboxCommand(payload.inbox_item_id), _metadata(principal, command_id="create_mission_work_item_from_inbox"), principal)


@router.get("", response_model=MissionWorkItemPage)
def list_work_items(request: Request, status: str | None = None, priority: str | None = None, assignee_subject_id: str | None = None, inbox_item_id: UUID | None = None, source_type: str | None = None, source_id: UUID | None = None, sort: str = "updated_at", limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)) -> MissionWorkItemPage:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.read")
    return request.app.state.yarvis.mission_work_query_service.list(db, principal, _metadata(principal, query_id="list_mission_work_items"), MissionWorkItemFilters(status, priority, assignee_subject_id, inbox_item_id, source_type, source_id, sort, limit, offset))


@router.get("/{work_item_id}", response_model=MissionWorkItemRead)
def retrieve_work_item(work_item_id: UUID, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.read")
    return request.app.state.yarvis.mission_work_query_service.retrieve(db, work_item_id, principal, _metadata(principal, query_id="retrieve_mission_work_item"))


@router.get("/{work_item_id}/workspace", response_model=OperationalWorkspaceRead)
def retrieve_operational_workspace(work_item_id: UUID, request: Request, currency: str = Query(..., min_length=3, max_length=3), db: Session = Depends(get_db)) -> OperationalWorkspaceRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.read")
    return request.app.state.yarvis.operational_workspace_query_service.retrieve(
        db, work_item_id, currency, principal, _metadata(principal, query_id="retrieve_operational_workspace")
    )


@router.get("/{work_item_id}/timeline", response_model=MissionWorkTimeline)
def retrieve_work_item_timeline(work_item_id: UUID, request: Request, db: Session = Depends(get_db)) -> MissionWorkTimeline:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.read")
    return request.app.state.yarvis.mission_work_query_service.timeline(db, work_item_id, principal, _metadata(principal, query_id="retrieve_mission_work_timeline"))


@router.get("/{work_item_id}/process-links", response_model=ProcessInstanceWorkLinkHistory)
def list_work_item_process_links(work_item_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceWorkLinkHistory:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.process_work_association_query_service.list_for_work(db, work_item_id, principal, _metadata(principal, query_id="list_mission_work_process_links"))


@router.post("/{work_item_id}/comments", response_model=MissionWorkEventRead, status_code=status.HTTP_201_CREATED)
def add_work_item_comment(work_item_id: UUID, payload: CommentRequest, request: Request, db: Session = Depends(get_db)) -> MissionWorkEventRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.create")
    return request.app.state.yarvis.mission_work_service.add_comment(
        AddMissionWorkItemCommentCommand(work_item_id, payload.comment),
        _metadata(principal, command_id="add_mission_work_item_comment"),
        principal,
    )


@router.post("/{work_item_id}/assignment", response_model=MissionWorkItemRead)
def assign_work_item(work_item_id: UUID, payload: AssignmentRequest, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.assign")
    return request.app.state.yarvis.mission_work_service.assign(AssignMissionWorkItemCommand(work_item_id, payload.assignee_subject_id), _metadata(principal, command_id="assign_mission_work_item"), principal)


@router.post("/{work_item_id}/status", response_model=MissionWorkItemRead)
def change_work_item_status(work_item_id: UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.status.change")
    return request.app.state.yarvis.mission_work_service.change_status(ChangeMissionWorkItemStatusCommand(work_item_id, payload.status), _metadata(principal, command_id="change_mission_work_item_status"), principal)


@router.post("/{work_item_id}/priority", response_model=MissionWorkItemRead)
def change_work_item_priority(work_item_id: UUID, payload: PriorityRequest, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = _resolved_mission_work_principal(request, db, required_scope="mission.work.priority.change")
    return request.app.state.yarvis.mission_work_service.change_priority(ChangeMissionWorkItemPriorityCommand(work_item_id, payload.priority), _metadata(principal, command_id="change_mission_work_item_priority"), principal)

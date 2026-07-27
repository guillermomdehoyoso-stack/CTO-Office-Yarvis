"""Governed Mission Work Queue API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_work import AssignMissionWorkItemCommand, ChangeMissionWorkItemPriorityCommand, ChangeMissionWorkItemStatusCommand, CreateMissionWorkItemFromInboxCommand, MissionWorkItemFilters
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.schemas.mission_work import AssignmentRequest, CreateMissionWorkItemRequest, MissionWorkItemPage, MissionWorkItemRead, PriorityRequest, StatusRequest


router = APIRouter(prefix="/mission/work-items", tags=["mission-work"])


def _metadata(principal, command_id: str | None = None, query_id: str | None = None) -> RequestMetadata:
    return RequestMetadata(requested_at=utc_now(), correlation_id=principal.correlation_id or str(uuid4()), command_id=command_id, query_id=query_id)


@router.post("", response_model=MissionWorkItemRead, status_code=status.HTTP_201_CREATED)
def create_work_item(payload: CreateMissionWorkItemRequest, request: Request) -> MissionWorkItemRead:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_service.create(CreateMissionWorkItemFromInboxCommand(payload.inbox_item_id), _metadata(principal, command_id="create_mission_work_item_from_inbox"), principal)


@router.get("", response_model=MissionWorkItemPage)
def list_work_items(request: Request, status: str | None = None, priority: str | None = None, assignee_subject_id: str | None = None, inbox_item_id: UUID | None = None, source_type: str | None = None, source_id: UUID | None = None, sort: str = "updated_at", limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)) -> MissionWorkItemPage:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_query_service.list(db, principal, _metadata(principal, query_id="list_mission_work_items"), MissionWorkItemFilters(status, priority, assignee_subject_id, inbox_item_id, source_type, source_id, sort, limit, offset))


@router.get("/{work_item_id}", response_model=MissionWorkItemRead)
def retrieve_work_item(work_item_id: UUID, request: Request, db: Session = Depends(get_db)) -> MissionWorkItemRead:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_query_service.retrieve(db, work_item_id, principal, _metadata(principal, query_id="retrieve_mission_work_item"))


@router.post("/{work_item_id}/assignment", response_model=MissionWorkItemRead)
def assign_work_item(work_item_id: UUID, payload: AssignmentRequest, request: Request) -> MissionWorkItemRead:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_service.assign(AssignMissionWorkItemCommand(work_item_id, payload.assignee_subject_id), _metadata(principal, command_id="assign_mission_work_item"), principal)


@router.post("/{work_item_id}/status", response_model=MissionWorkItemRead)
def change_work_item_status(work_item_id: UUID, payload: StatusRequest, request: Request) -> MissionWorkItemRead:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_service.change_status(ChangeMissionWorkItemStatusCommand(work_item_id, payload.status), _metadata(principal, command_id="change_mission_work_item_status"), principal)


@router.post("/{work_item_id}/priority", response_model=MissionWorkItemRead)
def change_work_item_priority(work_item_id: UUID, payload: PriorityRequest, request: Request) -> MissionWorkItemRead:
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.mission_work_service.change_priority(ChangeMissionWorkItemPriorityCommand(work_item_id, payload.priority), _metadata(principal, command_id="change_mission_work_item_priority"), principal)

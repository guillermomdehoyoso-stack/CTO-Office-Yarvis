"""Governed Process Runtime API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.process_authority import process_principal_from_envelope
from yarvis_api.application.process import CancelProcessInstanceCommand, LinkProcessInstanceToMissionWorkCommand, StartProcessInstanceCommand, TransitionProcessInstanceCommand, UnlinkProcessInstanceFromMissionWorkCommand
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.schemas.process import (
    CancelProcessInstanceRequest,
    LinkProcessInstanceToMissionWorkRequest,
    ProcessInstancePage,
    ProcessInstanceRead,
    ProcessInstanceTimeline,
    ProcessInstanceWorkLinkHistory,
    ProcessInstanceWorkLinkRead,
    StartProcessInstanceRequest,
    TransitionProcessInstanceRequest,
    UnlinkProcessInstanceFromMissionWorkRequest,
)


router = APIRouter(prefix="/process-instances", tags=["process-runtime"])


def _principal(request: Request, db: Session, scope: str):
    authenticated=request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request)); envelope=AuthorityResolutionService().resolve(db,external_subject=authenticated.actor_id,selector=None,authentication_source=authenticated.authentication_method,correlation_id=authenticated.correlation_id or str(uuid4())); return process_principal_from_envelope(envelope,required_scope=scope)


def _query_metadata(principal, query_id: str) -> RequestMetadata:
    return RequestMetadata(requested_at=utc_now(), correlation_id=principal.correlation_id or str(uuid4()), query_id=query_id)


@router.post("", response_model=ProcessInstanceRead, status_code=status.HTTP_201_CREATED)
def start_process_instance(payload: StartProcessInstanceRequest, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceRead:
    principal = _principal(request, db, "process.instance.start")
    result = request.app.state.yarvis.process_runtime_service.start(
        StartProcessInstanceCommand(payload.process_definition_id),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="start_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )
    request.app.state.yarvis.process_mission_work_timeline_projector.project_instance(result.id)
    return result


@router.get("", response_model=ProcessInstancePage)
def list_process_instances(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)) -> ProcessInstancePage:
    principal = _principal(request, db, "process.instance.read")
    return request.app.state.yarvis.process_runtime_query_service.list(db, principal, _query_metadata(principal, "list_process_instances"), limit, offset)


@router.get("/{process_instance_id}", response_model=ProcessInstanceRead)
def retrieve_process_instance(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceRead:
    principal = _principal(request, db, "process.instance.read")
    return request.app.state.yarvis.process_runtime_query_service.retrieve(db, process_instance_id, principal, _query_metadata(principal, "retrieve_process_instance"))


@router.post("/{process_instance_id}/transitions", response_model=ProcessInstanceRead)
def transition_process_instance(process_instance_id: UUID, payload: TransitionProcessInstanceRequest, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceRead:
    principal = _principal(request, db, "process.instance.transition")
    result = request.app.state.yarvis.process_runtime_service.transition(
        TransitionProcessInstanceCommand(process_instance_id, payload.transition_id, payload.expected_version),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="transition_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key, expected_aggregate_version=payload.expected_version),
        principal,
    )
    request.app.state.yarvis.process_mission_work_timeline_projector.project_instance(result.id)
    return result


@router.post("/{process_instance_id}/cancel", response_model=ProcessInstanceRead)
def cancel_process_instance(process_instance_id: UUID, payload: CancelProcessInstanceRequest, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceRead:
    principal = _principal(request, db, "process.instance.cancel")
    result = request.app.state.yarvis.process_runtime_service.cancel(
        CancelProcessInstanceCommand(process_instance_id, payload.expected_version, payload.reason),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="cancel_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key, expected_aggregate_version=payload.expected_version),
        principal,
    )
    request.app.state.yarvis.process_mission_work_timeline_projector.project_instance(result.id)
    return result


@router.get("/{process_instance_id}/timeline", response_model=ProcessInstanceTimeline)
def retrieve_process_instance_timeline(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceTimeline:
    principal = _principal(request, db, "process.instance.read")
    return request.app.state.yarvis.process_runtime_query_service.timeline(db, process_instance_id, principal, _query_metadata(principal, "retrieve_process_instance_timeline"))


@router.post("/{process_instance_id}/work-links", response_model=ProcessInstanceWorkLinkRead, status_code=status.HTTP_201_CREATED)
def link_process_instance_to_work(process_instance_id: UUID, payload: LinkProcessInstanceToMissionWorkRequest, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceWorkLinkRead:
    principal = _principal(request, db, "process.instance.work.link")
    result = request.app.state.yarvis.process_work_association_service.link(
        LinkProcessInstanceToMissionWorkCommand(process_instance_id, payload.mission_work_item_id, payload.relationship_type),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="link_process_instance_to_mission_work", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )
    request.app.state.yarvis.process_mission_work_timeline_projector.project_link(result.id)
    return result


@router.post("/{process_instance_id}/work-links/{link_id}/unlink", response_model=ProcessInstanceWorkLinkRead)
def unlink_process_instance_from_work(process_instance_id: UUID, link_id: UUID, payload: UnlinkProcessInstanceFromMissionWorkRequest, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceWorkLinkRead:
    principal = _principal(request, db, "process.instance.work.unlink")
    result = request.app.state.yarvis.process_work_association_service.unlink(
        UnlinkProcessInstanceFromMissionWorkCommand(process_instance_id, link_id),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="unlink_process_instance_from_mission_work", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )
    request.app.state.yarvis.process_mission_work_timeline_projector.project_link(result.id)
    return result


@router.get("/{process_instance_id}/work-links", response_model=ProcessInstanceWorkLinkHistory)
def list_process_instance_work_link_history(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceWorkLinkHistory:
    principal = _principal(request, db, "process.instance.read")
    return request.app.state.yarvis.process_work_association_query_service.history_for_instance(db, process_instance_id, principal, _query_metadata(principal, "list_process_instance_work_link_history"))


@router.get("/{process_instance_id}/primary-work-link", response_model=ProcessInstanceWorkLinkRead)
def retrieve_process_instance_primary_work_link(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceWorkLinkRead:
    principal = _principal(request, db, "process.instance.read")
    return request.app.state.yarvis.process_work_association_query_service.primary_for_instance(db, process_instance_id, principal, _query_metadata(principal, "retrieve_process_instance_primary_work_link"))

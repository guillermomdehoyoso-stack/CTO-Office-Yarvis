"""Governed Process Runtime API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.process import CancelProcessInstanceCommand, StartProcessInstanceCommand, TransitionProcessInstanceCommand
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.schemas.process import (
    CancelProcessInstanceRequest,
    ProcessInstancePage,
    ProcessInstanceRead,
    ProcessInstanceTimeline,
    StartProcessInstanceRequest,
    TransitionProcessInstanceRequest,
)


router = APIRouter(prefix="/process-instances", tags=["process-runtime"])


def _principal(request: Request):
    return request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))


def _query_metadata(principal, query_id: str) -> RequestMetadata:
    return RequestMetadata(requested_at=utc_now(), correlation_id=principal.correlation_id or str(uuid4()), query_id=query_id)


@router.post("", response_model=ProcessInstanceRead, status_code=status.HTTP_201_CREATED)
def start_process_instance(payload: StartProcessInstanceRequest, request: Request) -> ProcessInstanceRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_service.start(
        StartProcessInstanceCommand(payload.process_definition_id),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="start_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )


@router.get("", response_model=ProcessInstancePage)
def list_process_instances(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)) -> ProcessInstancePage:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_query_service.list(db, principal, _query_metadata(principal, "list_process_instances"), limit, offset)


@router.get("/{process_instance_id}", response_model=ProcessInstanceRead)
def retrieve_process_instance(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_query_service.retrieve(db, process_instance_id, principal, _query_metadata(principal, "retrieve_process_instance"))


@router.post("/{process_instance_id}/transitions", response_model=ProcessInstanceRead)
def transition_process_instance(process_instance_id: UUID, payload: TransitionProcessInstanceRequest, request: Request) -> ProcessInstanceRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_service.transition(
        TransitionProcessInstanceCommand(process_instance_id, payload.transition_id, payload.expected_version),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="transition_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key, expected_aggregate_version=payload.expected_version),
        principal,
    )


@router.post("/{process_instance_id}/cancel", response_model=ProcessInstanceRead)
def cancel_process_instance(process_instance_id: UUID, payload: CancelProcessInstanceRequest, request: Request) -> ProcessInstanceRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_service.cancel(
        CancelProcessInstanceCommand(process_instance_id, payload.expected_version, payload.reason),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="cancel_process_instance", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key, expected_aggregate_version=payload.expected_version),
        principal,
    )


@router.get("/{process_instance_id}/timeline", response_model=ProcessInstanceTimeline)
def retrieve_process_instance_timeline(process_instance_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessInstanceTimeline:
    principal = _principal(request)
    return request.app.state.yarvis.process_runtime_query_service.timeline(db, process_instance_id, principal, _query_metadata(principal, "retrieve_process_instance_timeline"))

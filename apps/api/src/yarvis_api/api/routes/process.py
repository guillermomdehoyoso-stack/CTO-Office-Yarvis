"""Governed administrative API for versioned operational process definitions."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.process import (
    AddProcessStageCommand,
    AddProcessTransitionCommand,
    CreateProcessDefinitionCommand,
    CreateProcessVersionCommand,
    DeleteProcessStageCommand,
    DeleteProcessTransitionCommand,
    ProcessLifecycleCommand,
    UpdateProcessStageCommand,
    UpdateProcessTransitionCommand,
)
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.schemas.process import (
    ProcessDefinitionCreateRequest,
    ProcessDefinitionListItem,
    ProcessDefinitionRead,
    ProcessStageCreateRequest,
    ProcessStageUpdateRequest,
    ProcessTransitionCreateRequest,
    ProcessTransitionUpdateRequest,
)


router = APIRouter(prefix="/process-definitions", tags=["process-definitions"])


def _metadata(principal, command_id: str | None = None, query_id: str | None = None) -> RequestMetadata:
    return RequestMetadata(
        requested_at=utc_now(),
        correlation_id=principal.correlation_id or str(uuid4()),
        command_id=command_id,
        query_id=query_id,
    )


def _principal(request: Request):
    return request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))


@router.post("", response_model=ProcessDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_process_definition(payload: ProcessDefinitionCreateRequest, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.create(
        CreateProcessDefinitionCommand(payload.name, payload.description),
        _metadata(principal, command_id="create_process_definition"),
        principal,
    )


@router.get("", response_model=list[ProcessDefinitionListItem])
def list_process_definitions(request: Request, db: Session = Depends(get_db)) -> list[ProcessDefinitionListItem]:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_query_service.list(
        db,
        principal,
        _metadata(principal, query_id="list_process_definitions"),
    )


@router.get("/{process_definition_id}", response_model=ProcessDefinitionRead)
def retrieve_process_definition(process_definition_id: UUID, request: Request, db: Session = Depends(get_db)) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_query_service.retrieve(
        db,
        process_definition_id,
        principal,
        _metadata(principal, query_id="retrieve_process_definition"),
    )


@router.post("/{process_definition_id}/versions", response_model=ProcessDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_process_version(process_definition_id: UUID, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.create_version(
        CreateProcessVersionCommand(process_definition_id),
        _metadata(principal, command_id="create_process_version"),
        principal,
    )


@router.post("/{process_definition_id}/stages", response_model=ProcessDefinitionRead)
def add_process_stage(process_definition_id: UUID, payload: ProcessStageCreateRequest, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.add_stage(
        AddProcessStageCommand(process_definition_id, payload.stage_key, payload.name, payload.description, payload.stage_type, payload.display_order, payload.metadata_json),
        _metadata(principal, command_id="add_process_stage"),
        principal,
    )


@router.put("/{process_definition_id}/stages/{stage_id}", response_model=ProcessDefinitionRead)
def update_process_stage(process_definition_id: UUID, stage_id: UUID, payload: ProcessStageUpdateRequest, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.update_stage(
        UpdateProcessStageCommand(process_definition_id, stage_id, payload.stage_key, payload.name, payload.description, payload.stage_type, payload.display_order, payload.metadata_json),
        _metadata(principal, command_id="update_process_stage"),
        principal,
    )


@router.delete("/{process_definition_id}/stages/{stage_id}", response_model=ProcessDefinitionRead)
def delete_process_stage(process_definition_id: UUID, stage_id: UUID, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.delete_stage(
        DeleteProcessStageCommand(process_definition_id, stage_id),
        _metadata(principal, command_id="delete_process_stage"),
        principal,
    )


@router.post("/{process_definition_id}/transitions", response_model=ProcessDefinitionRead)
def add_process_transition(process_definition_id: UUID, payload: ProcessTransitionCreateRequest, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.add_transition(
        AddProcessTransitionCommand(process_definition_id, payload.from_stage_id, payload.to_stage_id, payload.name),
        _metadata(principal, command_id="add_process_transition"),
        principal,
    )


@router.put("/{process_definition_id}/transitions/{transition_id}", response_model=ProcessDefinitionRead)
def update_process_transition(process_definition_id: UUID, transition_id: UUID, payload: ProcessTransitionUpdateRequest, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.update_transition(
        UpdateProcessTransitionCommand(process_definition_id, transition_id, payload.name),
        _metadata(principal, command_id="update_process_transition"),
        principal,
    )


@router.delete("/{process_definition_id}/transitions/{transition_id}", response_model=ProcessDefinitionRead)
def delete_process_transition(process_definition_id: UUID, transition_id: UUID, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.delete_transition(
        DeleteProcessTransitionCommand(process_definition_id, transition_id),
        _metadata(principal, command_id="delete_process_transition"),
        principal,
    )


@router.post("/{process_definition_id}/publish", response_model=ProcessDefinitionRead)
def publish_process_definition(process_definition_id: UUID, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.publish(
        ProcessLifecycleCommand(process_definition_id),
        _metadata(principal, command_id="publish_process_definition"),
        principal,
    )


@router.post("/{process_definition_id}/retire", response_model=ProcessDefinitionRead)
def retire_process_definition(process_definition_id: UUID, request: Request) -> ProcessDefinitionRead:
    principal = _principal(request)
    return request.app.state.yarvis.process_definition_service.retire(
        ProcessLifecycleCommand(process_definition_id),
        _metadata(principal, command_id="retire_process_definition"),
        principal,
    )

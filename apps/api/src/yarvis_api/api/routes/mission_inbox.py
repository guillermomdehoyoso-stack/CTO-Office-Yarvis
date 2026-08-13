"""Governed read-only Mission Inbox API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.intake_authority import intake_principal_from_envelope
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_inbox import MissionInboxFilters
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.schemas.mission_inbox import MissionInboxItemRead, MissionInboxPage


router = APIRouter(prefix="/mission/inbox", tags=["mission-inbox"])


def _metadata(principal_correlation_id: str | None, query_id: str) -> RequestMetadata:
    return RequestMetadata(
        requested_at=utc_now(),
        correlation_id=principal_correlation_id or str(uuid4()),
        query_id=query_id,
    )


def _resolved_mission_inbox_principal(request: Request, db: Session):
    authenticated = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    envelope = AuthorityResolutionService().resolve(
        db,
        external_subject=authenticated.actor_id,
        selector=None,
        authentication_source=authenticated.authentication_method,
        correlation_id=authenticated.correlation_id or str(uuid4()),
    )
    return intake_principal_from_envelope(envelope, required_scope="mission.inbox.read")


@router.get("", response_model=MissionInboxPage)
def list_mission_inbox(
    request: Request,
    status: str | None = None,
    priority: str | None = None,
    site_id: UUID | None = None,
    project_id: UUID | None = None,
    source_type: str | None = None,
    sort: str = "last_activity_at",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> MissionInboxPage:
    principal = _resolved_mission_inbox_principal(request, db)
    return request.app.state.yarvis.mission_inbox_query_service.list(
        db,
        principal,
        _metadata(principal.correlation_id, "list_mission_inbox"),
        MissionInboxFilters(status, priority, site_id, project_id, source_type, sort, limit, offset),
    )


@router.get("/{inbox_item_id}", response_model=MissionInboxItemRead)
def retrieve_mission_inbox_item(inbox_item_id: UUID, request: Request, db: Session = Depends(get_db)) -> MissionInboxItemRead:
    principal = _resolved_mission_inbox_principal(request, db)
    return request.app.state.yarvis.mission_inbox_query_service.retrieve(
        db,
        inbox_item_id,
        principal,
        _metadata(principal.correlation_id, "retrieve_mission_inbox_item"),
    )

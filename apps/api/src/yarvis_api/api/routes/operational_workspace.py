"""Organization-scoped, read-only Operational Workspace API."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.mission_work_authority import mission_work_principal_from_envelope
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.schemas.operational_workspace_overview import OperationalWorkspaceOverviewRead

router = APIRouter(prefix="/operational-workspace", tags=["operational-workspace"])


@router.get("", response_model=OperationalWorkspaceOverviewRead)
def retrieve_operational_workspace(
    request: Request,
    site_id: UUID | None = None,
    project_id: UUID | None = None,
    activity_limit: int = Query(25, ge=1, le=100),
    task_limit: int = Query(50, ge=1, le=100),
    process_limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> OperationalWorkspaceOverviewRead:
    authenticated = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    envelope = AuthorityResolutionService().resolve(
        db, external_subject=authenticated.actor_id, selector=None,
        authentication_source=authenticated.authentication_method,
        correlation_id=authenticated.correlation_id or str(uuid4()),
    )
    principal = mission_work_principal_from_envelope(envelope, required_scope="mission.work.read")
    metadata = RequestMetadata(utc_now(), principal.correlation_id or str(uuid4()), query_id="retrieve_operational_workspace_overview")
    return request.app.state.yarvis.operational_workspace_overview_query_service.retrieve(
        db, principal, metadata, site_id=site_id, project_id=project_id, task_limit=task_limit,
        process_limit=process_limit, activity_limit=activity_limit,
    )

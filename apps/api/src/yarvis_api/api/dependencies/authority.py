"""F-011 server-side authority dependency for bounded Governance handlers."""

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService


def authority_envelope(
    request: Request,
    db: Session = Depends(get_db),
    selector: str | None = Header(default=None, alias="X-Yarvis-Organization-Selector"),
    subject: str = Header(..., alias="X-Yarvis-Subject", min_length=1, max_length=255),
):
    authenticated = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return AuthorityResolutionService().resolve(
        db,
        external_subject=subject,
        selector=selector,
        authentication_source=authenticated.authentication_method,
        correlation_id=authenticated.correlation_id or "00000000-0000-0000-0000-000000000000",
    )

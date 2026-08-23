"""Productive OIDC HTTP mechanisms and server-side session surface."""

import base64
import hashlib
import secrets
from datetime import timedelta
from typing import NoReturn
from urllib.parse import urlencode

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.models.organization import Organization
from yarvis_api.models.productive_auth import OIDCAuthenticationAttempt
from yarvis_api.services.bootstrap_handoff import BootstrapIdentityHandoffService
from yarvis_api.services.oidc import OIDCClient, oidc_denied
from yarvis_api.services.productive_auth import ProductiveSessionService

router = APIRouter(prefix="/auth", tags=["authentication"])


def _h(v):
    return hashlib.sha256(v.encode()).hexdigest()


def _b64(v):
    return base64.urlsafe_b64encode(v).rstrip(b"=").decode()


def _deny() -> NoReturn:
    oidc_denied()


def _client_key(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


@router.get("/login")
async def login(request: Request, redirect: str = Query("/"), db: Session = Depends(get_db)):
    s = request.app.state.yarvis.settings
    request.app.state.yarvis.auth_rate_limiter.require("login", _client_key(request), limit=10, window_seconds=600)
    if s.auth_mode != "oidc" or not all(
        (s.oidc_issuer, s.oidc_client_id, s.oidc_redirect_uri, s.oidc_attempt_encryption_key)
    ):
        _deny()
    if redirect not in {x.strip() for x in s.oidc_post_login_redirect_allowlist.split(",")} or not redirect.startswith(
        "/"
    ):
        _deny()
    oidc = OIDCClient(s)
    d = await oidc.discovery()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    cipher = Fernet(s.oidc_attempt_encryption_key.get_secret_value().encode())
    db.add(
        OIDCAuthenticationAttempt(
            state_hash=_h(state),
            nonce_hash=_h(nonce),
            pkce_verifier_encrypted=cipher.encrypt(verifier.encode()).decode(),
            redirect_path=redirect,
            expires_at=utc_now() + timedelta(minutes=10),
            status="pending",
        )
    )
    db.commit()
    q = urlencode(
        {
            "response_type": "code",
            "client_id": s.oidc_client_id,
            "redirect_uri": s.oidc_redirect_uri,
            "scope": "openid",
            "state": state,
            "nonce": nonce,
            "code_challenge": _b64(hashlib.sha256(verifier.encode()).digest()),
            "code_challenge_method": "S256",
            "response_mode": "form_post",
        }
    )
    return RedirectResponse(d["authorization_endpoint"] + "?" + q, 302)


@router.post("/callback")
async def callback(
    request: Request,
    code: str = Form(..., min_length=1, max_length=4096),
    state: str = Form(..., min_length=32, max_length=512),
    db: Session = Depends(get_db),
):
    s = request.app.state.yarvis.settings
    request.app.state.yarvis.auth_rate_limiter.require("callback", _client_key(request), limit=20, window_seconds=600)
    a = db.scalar(
        select(OIDCAuthenticationAttempt).where(OIDCAuthenticationAttempt.state_hash == _h(state)).with_for_update()
    )
    if a is None or a.status != "pending" or utc_now() >= a.expires_at:
        _deny()
    # Consume before provider I/O. Any replay, including after an upstream
    # timeout, fails closed and cannot reuse the authorization response.
    a.status = "failed"
    try:
        v = (
            Fernet(s.oidc_attempt_encryption_key.get_secret_value().encode())
            .decrypt(a.pkce_verifier_encrypted.encode(), ttl=900)
            .decode()
        )
    except (InvalidToken, AttributeError):
        db.commit()
        _deny()
    db.commit()
    oidc = OIDCClient(s)
    d = await oidc.discovery()
    raw = await oidc.exchange(d, code=code, verifier=v)
    claims = await oidc.validate_id_token(d, raw, a.nonce_hash)
    if s.bootstrap_enabled:
        assert s.oidc_issuer is not None and s.oidc_attempt_encryption_key is not None
        BootstrapIdentityHandoffService().record(
            db,
            attempt=a,
            issuer=s.oidc_issuer,
            subject=str(claims["sub"]),
            encryption_key=s.oidc_attempt_encryption_key.get_secret_value(),
        )
        db.commit()
    service = ProductiveSessionService(s)
    principal = service.resolve_binding(db, s.oidc_issuer, str(claims["sub"]))
    _, raw_session, csrf, _ = service.create(db, principal)
    a.status = "consumed"
    a.consumed_at = utc_now()
    a.pkce_verifier_encrypted = "consumed"
    db.commit()
    response = RedirectResponse(a.redirect_path, 303)
    response.set_cookie(
        s.session_cookie_name,
        raw_session,
        max_age=s.session_absolute_seconds,
        httponly=True,
        secure=s.environment == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "yarvis_csrf",
        csrf,
        max_age=s.session_absolute_seconds,
        httponly=False,
        secure=s.environment == "production",
        samesite="lax",
        path="/",
    )
    return response


@router.get("/session")
def current(request: Request, db: Session = Depends(get_db)):
    request.app.state.yarvis.auth_rate_limiter.require("session", _client_key(request), limit=120, window_seconds=60)
    item, e = ProductiveSessionService(request.app.state.yarvis.settings).authenticate(db, request)
    organization = db.get(Organization, e.organization_id)
    if organization is None:
        _deny()
    db.commit()
    return {
        "authenticated": True,
        "organization_id": str(e.organization_id),
        "organization_label": organization.display_name,
        "capabilities": sorted(e.validated_permissions),
        "expires_at": item.absolute_expires_at.isoformat(),
    }


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    s = request.app.state.yarvis.settings
    request.app.state.yarvis.auth_rate_limiter.require("logout", _client_key(request), limit=30, window_seconds=60)
    service = ProductiveSessionService(s)
    service.logout(db, request)
    db.commit()
    response.delete_cookie(s.session_cookie_name, path="/", secure=s.environment == "production", httponly=True)
    response.delete_cookie("yarvis_csrf", path="/", secure=s.environment == "production")

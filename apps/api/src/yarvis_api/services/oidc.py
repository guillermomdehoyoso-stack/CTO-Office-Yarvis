"""Provider-neutral OIDC discovery, code exchange and ID-token validation."""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any, NoReturn
from urllib.parse import urlparse

import httpx
import jwt

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import Settings

logger = logging.getLogger(__name__)

_DENIAL_STAGES = frozenset(
    {
        "token_exchange",
        "token_response",
        "id_token_payload",
        "jwks_fetch",
        "jwks_response",
        "jwt_header",
        "jwt_algorithm",
        "jwt_key",
        "jwt_validation",
        "claims_shape",
        "nonce_mismatch",
        "configuration",
        "unspecified",
    }
)
_TOKEN_RESPONSE_ERRORS = frozenset(
    {
        "invalid_client",
        "invalid_grant",
        "invalid_request",
        "unauthorized_client",
        "unsupported_grant_type",
        "access_denied",
    }
)


def oidc_denied(
    stage: str = "unspecified", *, http_status_family: str = "unspecified", oauth_error: str = "unspecified"
) -> NoReturn:
    safe_stage = stage if stage in _DENIAL_STAGES else "unspecified"
    if safe_stage == "token_response":
        safe_status = http_status_family if http_status_family in _TOKEN_RESPONSE_STATUS_FAMILIES else "http_other"
        safe_error = oauth_error if oauth_error in _TOKEN_RESPONSE_ERRORS else "unspecified"
        logger.warning(
            "oidc_authentication_denied stage=%s http_status_family=%s oauth_error=%s",
            safe_stage,
            safe_status,
            safe_error,
        )
    else:
        logger.warning("oidc_authentication_denied stage=%s", safe_stage)
    raise ApplicationError(
        ApplicationErrorCode.AUTHORIZATION_DENIED,
        "authentication denied",
        {"reason": "oidc_denied"},
    )


_TOKEN_RESPONSE_STATUS_FAMILIES = frozenset(
    {"http_400", "http_401", "http_403", "http_429", "http_5xx", "http_other"}
)


def _http_status_family(status_code: int) -> str:
    if status_code in (400, 401, 403, 429):
        return f"http_{status_code}"
    if 500 <= status_code <= 599:
        return "http_5xx"
    return "http_other"


def _token_response_denied(response: httpx.Response) -> NoReturn:
    oauth_error = "unspecified"
    if len(response.content) <= 262144:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("error") in _TOKEN_RESPONSE_ERRORS:
            oauth_error = payload["error"]
    oidc_denied(
        "token_response",
        http_status_family=_http_status_family(response.status_code),
        oauth_error=oauth_error,
    )


class OIDCClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def _json(self, url: str, *, fetch_stage: str, response_stage: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5, connect=3),
                follow_redirects=False,
                limits=httpx.Limits(max_connections=10),
            ) as client:
                response = await client.request(kwargs.pop("method", "GET"), url, **kwargs)
        except httpx.HTTPError:
            oidc_denied(fetch_stage)
        if response.status_code != 200 or len(response.content) > 262144:
            if response_stage == "token_response":
                _token_response_denied(response)
            oidc_denied(response_stage)
        try:
            payload = response.json()
        except ValueError:
            oidc_denied(response_stage)
        if not isinstance(payload, dict):
            oidc_denied(response_stage)
        return payload

    async def discovery(self) -> dict[str, Any]:
        issuer = self.settings.oidc_issuer
        if not issuer:
            oidc_denied("configuration")
        document = await self._json(
            issuer.rstrip("/") + "/.well-known/openid-configuration",
            fetch_stage="configuration",
            response_stage="configuration",
        )
        if document.get("issuer") != issuer:
            oidc_denied("configuration")
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            endpoint = document.get(key)
            if not isinstance(endpoint, str) or len(endpoint) > 2048:
                oidc_denied("configuration")
            if self.settings.environment == "production" and urlparse(endpoint).scheme != "https":
                oidc_denied("configuration")
        return document

    async def exchange(self, discovery: dict[str, Any], *, code: str, verifier: str) -> str:
        secret = self.settings.oidc_client_secret
        if secret is None:
            oidc_denied("configuration")
        token = await self._json(
            discovery["token_endpoint"],
            fetch_stage="token_exchange",
            response_stage="token_response",
            method="POST",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.settings.oidc_redirect_uri,
                "client_id": self.settings.oidc_client_id,
                "client_secret": secret.get_secret_value(),
                "code_verifier": verifier,
            },
        )
        raw = token.get("id_token", "")
        if not isinstance(raw, str) or len(raw) > 16384:
            oidc_denied("id_token_payload")
        return raw

    async def validate_id_token(self, discovery: dict[str, Any], raw: str, nonce_hash: str) -> dict[str, Any]:
        jwks = await self._json(
            discovery["jwks_uri"], fetch_stage="jwks_fetch", response_stage="jwks_response"
        )
        try:
            header = jwt.get_unverified_header(raw)
        except jwt.PyJWTError:
            oidc_denied("jwt_header")
        allowed = {item.strip() for item in self.settings.oidc_allowed_algorithms.split(",") if item.strip()}
        if header.get("alg") not in allowed or header.get("alg") == "none":
            oidc_denied("jwt_algorithm")
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == header.get("kid")), None)
        if key is None:
            oidc_denied("jwt_key")
        try:
            claims = jwt.decode(
                raw,
                jwt.PyJWK.from_dict(key).key,
                algorithms=[header["alg"]],
                audience=self.settings.oidc_client_id,
                issuer=self.settings.oidc_issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
            )
        except jwt.PyJWTError:
            oidc_denied("jwt_validation")
        if len(claims) > 32 or any(len(str(value)) > 4096 for value in claims.values()):
            oidc_denied("claims_shape")
        actual_nonce_hash = hashlib.sha256(str(claims.get("nonce", "")).encode()).hexdigest()
        if not secrets.compare_digest(actual_nonce_hash, nonce_hash):
            oidc_denied("nonce_mismatch")
        return claims

"""Provider-neutral OIDC discovery, code exchange and ID-token validation."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any, NoReturn
from urllib.parse import urlparse

import httpx
import jwt

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.config import Settings


def oidc_denied() -> NoReturn:
    raise ApplicationError(
        ApplicationErrorCode.AUTHORIZATION_DENIED,
        "authentication denied",
        {"reason": "oidc_denied"},
    )


class OIDCClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def _json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5, connect=3),
                follow_redirects=False,
                limits=httpx.Limits(max_connections=10),
            ) as client:
                response = await client.request(kwargs.pop("method", "GET"), url, **kwargs)
        except httpx.HTTPError:
            oidc_denied()
        if response.status_code != 200 or len(response.content) > 262144:
            oidc_denied()
        try:
            payload = response.json()
        except ValueError:
            oidc_denied()
        if not isinstance(payload, dict):
            oidc_denied()
        return payload

    async def discovery(self) -> dict[str, Any]:
        issuer = self.settings.oidc_issuer
        if not issuer:
            oidc_denied()
        document = await self._json(issuer.rstrip("/") + "/.well-known/openid-configuration")
        if document.get("issuer") != issuer:
            oidc_denied()
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            endpoint = document.get(key)
            if not isinstance(endpoint, str) or len(endpoint) > 2048:
                oidc_denied()
            if self.settings.environment == "production" and urlparse(endpoint).scheme != "https":
                oidc_denied()
        return document

    async def exchange(self, discovery: dict[str, Any], *, code: str, verifier: str) -> str:
        secret = self.settings.oidc_client_secret
        if secret is None:
            oidc_denied()
        token = await self._json(
            discovery["token_endpoint"],
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
            oidc_denied()
        return raw

    async def validate_id_token(self, discovery: dict[str, Any], raw: str, nonce_hash: str) -> dict[str, Any]:
        jwks = await self._json(discovery["jwks_uri"])
        try:
            header = jwt.get_unverified_header(raw)
        except jwt.PyJWTError:
            oidc_denied()
        allowed = {item.strip() for item in self.settings.oidc_allowed_algorithms.split(",") if item.strip()}
        if header.get("alg") not in allowed or header.get("alg") == "none":
            oidc_denied()
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == header.get("kid")), None)
        if key is None:
            oidc_denied()
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
            oidc_denied()
        if len(claims) > 32 or any(len(str(value)) > 4096 for value in claims.values()):
            oidc_denied()
        actual_nonce_hash = hashlib.sha256(str(claims.get("nonce", "")).encode()).hexdigest()
        if not secrets.compare_digest(actual_nonce_hash, nonce_hash):
            oidc_denied()
        return claims

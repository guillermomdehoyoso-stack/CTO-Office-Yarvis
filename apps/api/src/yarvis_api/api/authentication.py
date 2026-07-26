"""Transport-layer authentication adapters for deterministic development and test flows."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from yarvis_api.application.authentication import AuthenticatedPrincipal, TransportAuthenticationRequest
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.ports import AuthenticationPort
from yarvis_api.clock import utc_now
from yarvis_api.config import Settings

_TRUSTED_TOKEN = "deterministic-inbound-intake"


def transport_authentication_request(request: Request) -> TransportAuthenticationRequest:
    return TransportAuthenticationRequest(
        headers={key.lower(): value for key, value in request.headers.items()},
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client is not None else None,
    )


def _parse_list(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    if len(set(items)) != len(items):
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="invalid authentication headers",
            details={"reason": "duplicate_list_entries"},
        )
    return items


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ApplicationError(
        code=ApplicationErrorCode.AUTHORIZATION_DENIED,
        message="invalid authentication headers",
        details={"reason": "invalid_boolean_header"},
    )


@dataclass(slots=True)
class DeterministicAuthenticationProvider(AuthenticationPort):
    settings: Settings

    def authenticate(self, request: TransportAuthenticationRequest) -> AuthenticatedPrincipal:
        if self.settings.environment not in {"local", "test"}:
            raise ApplicationError(
                code=ApplicationErrorCode.AUTHORIZATION_DENIED,
                message="deterministic authentication provider is disabled",
                details={"environment": self.settings.environment},
            )

        headers = {key.lower(): value for key, value in request.headers.items()}
        actor_id = headers.get("x-yarvis-actor") or headers.get("x-yarvis-actor-id")
        authority = headers.get("x-yarvis-authority") or headers.get("x-yarvis-authority-scope")
        organization_id = headers.get("x-yarvis-organization") or headers.get("x-yarvis-authority-organization-id")
        trusted_token = headers.get("x-yarvis-auth-token") or headers.get("x-yarvis-authority-token")

        if not actor_id:
            raise ApplicationError(
                code=ApplicationErrorCode.AUTHORIZATION_DENIED,
                message="missing trusted principal actor",
                details={"missing": "actor"},
            )
        if not authority:
            raise ApplicationError(
                code=ApplicationErrorCode.AUTHORIZATION_DENIED,
                message="missing trusted principal authority",
                details={"missing": "authority"},
            )
        if trusted_token != _TRUSTED_TOKEN:
            raise ApplicationError(
                code=ApplicationErrorCode.AUTHORIZATION_DENIED,
                message="invalid trusted principal token",
                details={"reason": "invalid_token"},
            )

        roles = _parse_list(headers.get("x-yarvis-roles"))
        permissions = _parse_list(headers.get("x-yarvis-permissions"))
        is_system_actor = _parse_bool(headers.get("x-yarvis-system-actor"))
        correlation_id = headers.get("x-yarvis-correlation-id") or headers.get("x-correlation-id")
        auth_method = headers.get("x-yarvis-auth-method") or "trusted-header-dev"

        return AuthenticatedPrincipal(
            actor_id=actor_id,
            organization_id=organization_id,
            roles=roles,
            permissions=permissions,
            authority=authority,
            authentication_method=auth_method,
            authenticated_at=utc_now(),
            is_system_actor=is_system_actor,
            correlation_id=correlation_id,
        )

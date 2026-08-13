"""Narrow F-011 compatibility adapter for Operational Economics contracts."""

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.clock import utc_now


def economics_principal_from_envelope(
    envelope: IdentityAuthorityEnvelope, *, required_scope: str
) -> AuthenticatedPrincipal:
    """Project one validated Economics scope without reading transport data."""

    envelope.require(required_scope)
    return AuthenticatedPrincipal(
        actor_id=str(envelope.principal_id), organization_id=str(envelope.organization_id), roles=(),
        permissions=tuple(sorted(envelope.validated_permissions)), authority=required_scope,
        authentication_method=envelope.authentication_source, authenticated_at=utc_now(),
        is_system_actor=False, correlation_id=envelope.correlation_id,
    )

"""Narrow authority projection for the Netpay master contracts."""

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.clock import utc_now

_SCOPES = frozenset({"netpay.master.read", "netpay.master.manage"})


def netpay_master_principal_from_envelope(
    envelope: IdentityAuthorityEnvelope, *, required_scope: str
) -> AuthenticatedPrincipal:
    """Project only a validated Netpay scope; transport data is never read."""
    if required_scope not in _SCOPES:
        raise ValueError("required_scope must be a Netpay master scope")
    envelope.require(required_scope)
    return AuthenticatedPrincipal(
        actor_id=str(envelope.principal_id), organization_id=str(envelope.organization_id),
        roles=(), permissions=tuple(sorted(envelope.validated_permissions)),
        authority=required_scope, authentication_method=envelope.authentication_source,
        authenticated_at=utc_now(), is_system_actor=False, correlation_id=envelope.correlation_id,
    )

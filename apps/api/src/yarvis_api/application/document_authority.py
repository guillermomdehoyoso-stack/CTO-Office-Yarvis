"""Narrow F-011 compatibility adapter for legacy Document Registry contracts."""

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.clock import utc_now


_DOCUMENT_SCOPES = frozenset({
    "document.read",
    "document.create",
    "document.metadata.update",
    "document.version.add",
    "document.archive",
    "document.association.link",
    "document.association.unlink",
})


def document_principal_from_envelope(
    envelope: IdentityAuthorityEnvelope,
    *,
    required_scope: str,
) -> AuthenticatedPrincipal:
    """Project one validated Document Registry scope without reading transport data."""

    if required_scope not in _DOCUMENT_SCOPES:
        raise ValueError("required_scope must be an authorized Document Registry scope")
    envelope.require(required_scope)
    return AuthenticatedPrincipal(
        actor_id=str(envelope.principal_id),
        organization_id=str(envelope.organization_id),
        roles=(),
        permissions=tuple(sorted(envelope.validated_permissions)),
        authority=required_scope,
        authentication_method=envelope.authentication_source,
        authenticated_at=utc_now(),
        is_system_actor=False,
        correlation_id=envelope.correlation_id,
    )

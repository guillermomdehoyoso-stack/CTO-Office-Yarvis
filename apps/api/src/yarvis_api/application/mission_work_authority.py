"""Narrow F-011 compatibility adapter for legacy Mission Work contracts."""

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.clock import utc_now


_MISSION_WORK_SCOPES = frozenset({
    "mission.work.read",
    "mission.work.create",
    "mission.work.assign",
    "mission.work.status.change",
    "mission.work.priority.change",
})


def mission_work_principal_from_envelope(envelope: IdentityAuthorityEnvelope, *, required_scope: str) -> AuthenticatedPrincipal:
    """Project one validated Mission Work scope without reading transport data."""

    if required_scope not in _MISSION_WORK_SCOPES:
        raise ValueError("required_scope must be an authorized Mission Work scope")
    envelope.require(required_scope)
    return AuthenticatedPrincipal(
        actor_id=str(envelope.principal_id), organization_id=str(envelope.organization_id), roles=(),
        permissions=tuple(sorted(envelope.validated_permissions)), authority=required_scope,
        authentication_method=envelope.authentication_source, authenticated_at=utc_now(),
        is_system_actor=False, correlation_id=envelope.correlation_id,
    )

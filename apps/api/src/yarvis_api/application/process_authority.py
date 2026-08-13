from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.clock import utc_now


def process_principal_from_envelope(envelope: IdentityAuthorityEnvelope, *, required_scope: str) -> AuthenticatedPrincipal:
    envelope.require(required_scope)
    return AuthenticatedPrincipal(str(envelope.principal_id), str(envelope.organization_id), (), tuple(sorted(envelope.validated_permissions)), required_scope, envelope.authentication_source, utc_now(), False, envelope.correlation_id)

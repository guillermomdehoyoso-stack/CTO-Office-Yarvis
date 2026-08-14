"""Narrow Netpay Inbox projection from a persistence-resolved envelope."""

from yarvis_api.application.authority import IdentityAuthorityEnvelope

_SCOPES = frozenset({"netpay.inbox.read", "netpay.inbox.manage"})


def netpay_inbox_envelope(envelope: IdentityAuthorityEnvelope, *, required_scope: str) -> IdentityAuthorityEnvelope:
    if required_scope not in _SCOPES:
        raise ValueError("invalid Netpay Inbox scope")
    envelope.require(required_scope)
    return IdentityAuthorityEnvelope(envelope.principal_id, envelope.organization_id, frozenset(envelope.validated_permissions & _SCOPES), envelope.authentication_source, envelope.correlation_id)

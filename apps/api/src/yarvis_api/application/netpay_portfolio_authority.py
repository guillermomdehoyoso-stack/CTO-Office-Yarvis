"""Fail-closed authority projection for the Netpay commerce portfolio."""

from yarvis_api.application.authority import IdentityAuthorityEnvelope

PORTFOLIO_READ = "netpay.portfolio.read"
PORTFOLIO_SENSITIVE_READ = "netpay.portfolio.sensitive.read"
PORTFOLIO_RECONCILIATION_READ = "netpay.portfolio.reconciliation.read"
_SCOPES = frozenset({PORTFOLIO_READ, PORTFOLIO_SENSITIVE_READ, PORTFOLIO_RECONCILIATION_READ})


def netpay_portfolio_envelope(envelope: IdentityAuthorityEnvelope, *, required_scope: str) -> IdentityAuthorityEnvelope:
    if required_scope not in _SCOPES:
        raise ValueError("invalid Netpay portfolio scope")
    envelope.require(required_scope)
    return IdentityAuthorityEnvelope(
        envelope.principal_id,
        envelope.organization_id,
        frozenset(envelope.validated_permissions & _SCOPES),
        envelope.authentication_source,
        envelope.correlation_id,
    )

from uuid import uuid4

import pytest

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.intake_authority import intake_principal_from_envelope


def _envelope(*permissions: str) -> IdentityAuthorityEnvelope:
    return IdentityAuthorityEnvelope(uuid4(), uuid4(), frozenset(permissions), "local-test", "corr-1")


def test_adapter_projects_only_a_validated_intake_scope() -> None:
    envelope = _envelope("inbound.read", "inbound.intake", "radar.read")
    principal = intake_principal_from_envelope(envelope, required_scope="inbound.intake")
    assert principal.actor_id == str(envelope.principal_id)
    assert principal.organization_id == str(envelope.organization_id)
    assert principal.authority == "inbound.intake"
    assert set(principal.permissions) == set(envelope.validated_permissions)


def test_adapter_denies_missing_scope_and_rejects_non_intake_scope() -> None:
    with pytest.raises(ApplicationError) as denied:
        intake_principal_from_envelope(_envelope("inbound.read"), required_scope="inbound.intake")
    assert denied.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED
    with pytest.raises(ValueError):
        intake_principal_from_envelope(_envelope("radar.read"), required_scope="radar.read")

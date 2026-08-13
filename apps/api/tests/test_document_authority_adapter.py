from uuid import uuid4

import pytest

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.document_authority import document_principal_from_envelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode


def _envelope(*permissions: str) -> IdentityAuthorityEnvelope:
    return IdentityAuthorityEnvelope(uuid4(), uuid4(), frozenset(permissions), "local-test", "corr-1")


def test_adapter_projects_only_a_validated_document_scope() -> None:
    envelope = _envelope("document.read", "document.create", "radar.read")
    principal = document_principal_from_envelope(envelope, required_scope="document.create")
    assert principal.actor_id == str(envelope.principal_id)
    assert principal.organization_id == str(envelope.organization_id)
    assert principal.authority == "document.create"
    assert set(principal.permissions) == set(envelope.validated_permissions)


def test_adapter_denies_missing_scope_and_rejects_non_document_scope() -> None:
    with pytest.raises(ApplicationError) as denied:
        document_principal_from_envelope(_envelope("document.read"), required_scope="document.create")
    assert denied.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED
    with pytest.raises(ValueError):
        document_principal_from_envelope(_envelope("radar.read"), required_scope="radar.read")

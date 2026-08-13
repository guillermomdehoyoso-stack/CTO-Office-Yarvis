from uuid import uuid4

import pytest

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError
from yarvis_api.application.operational_task_authority import task_principal_from_envelope


def _envelope(*permissions: str) -> IdentityAuthorityEnvelope:
    return IdentityAuthorityEnvelope(uuid4(), uuid4(), frozenset(permissions), "local-test", str(uuid4()))


def test_adapter_projects_only_the_requested_validated_task_scope() -> None:
    envelope = _envelope("task.create", "task.update", "task.assign")

    principal = task_principal_from_envelope(envelope, required_scope="task.update")

    assert principal.actor_id == str(envelope.principal_id)
    assert principal.organization_id == str(envelope.organization_id)
    assert principal.authority == "task.update"
    assert set(principal.permissions) == set(envelope.validated_permissions)
    with pytest.raises(ApplicationError):
        task_principal_from_envelope(envelope, required_scope="task.cancel")


def test_query_identity_preserves_persisted_subject_and_organization_without_task_read() -> None:
    envelope = _envelope("task.create")

    principal = task_principal_from_envelope(envelope, required_scope=None)

    assert principal.actor_id == str(envelope.principal_id)
    assert principal.organization_id == str(envelope.organization_id)
    assert principal.authority == "persistence-resolved-query"
    assert "task.read" not in principal.permissions

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.intake import DETERMINISTIC_INTAKE_MODE, IntakeItem, LEGACY_INTAKE_MODE
from yarvis_api.models.operational_context import (
    ConnectorMapping,
    IntakeOperationalContextAssociation,
    Project,
    Site,
)
from yarvis_api.models.organization import Organization


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()
ASSOCIATE_HEADERS = {
    "x-yarvis-actor": "operator:context-01",
    "x-yarvis-organization": str(ORGANIZATION_ID),
    "x-yarvis-authority": "inbound.context.associate",
    "x-yarvis-auth-token": "deterministic-inbound-intake",
}


def _headers(*, organization_id: UUID = ORGANIZATION_ID, authority: str = "inbound.context.associate") -> dict[str, str]:
    return {**ASSOCIATE_HEADERS, "x-yarvis-organization": str(organization_id), "x-yarvis-authority": authority}


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(id=ORGANIZATION_ID, legal_name="WS002A Tenant", display_name="WS002A Tenant"),
                Organization(id=OTHER_ORGANIZATION_ID, legal_name="WS002A Other", display_name="WS002A Other"),
            )
        )
        session.commit()


def _intake_payload(*, idempotency_key: str) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "external_source": "email",
        "external_message_id": uuid4().hex,
        "sender": "sender@example.com",
        "recipients": ["ops@example.com"],
        "subject": "Operational context intake",
        "text_body": "Operational context intake body",
        "content_type": "message/rfc822",
        "source_timestamp": now,
        "received_timestamp": now,
        "correlation_id": str(uuid4()),
        "idempotency_key": idempotency_key,
    }


def _create_intake(*, organization_id: UUID = ORGANIZATION_ID) -> UUID:
    response = client.post(
        "/intake/deterministic",
        json=_intake_payload(idempotency_key=f"intake-{uuid4().hex}"),
        headers=_headers(organization_id=organization_id, authority="inbound.intake"),
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


def _seed_context(*, organization_id: UUID = ORGANIZATION_ID, site_id: UUID | None = None, project_site_id: UUID | None = None):
    with app.state.yarvis.persistence.create_session() as session:
        site = Site(id=site_id or uuid4(), organization_id=organization_id, reference=f"site-{uuid4().hex}")
        session.add(site)
        session.flush()
        project = Project(
            id=uuid4(),
            organization_id=organization_id,
            site_id=project_site_id or site.id,
            reference=f"project-{uuid4().hex}",
        )
        session.add(project)
        session.flush()
        mapping = ConnectorMapping(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project.id,
            connector_reference=f"mapping-{uuid4().hex}",
        )
        session.add(mapping)
        site_id, project_id, mapping_id = site.id, project.id, mapping.id
        session.commit()
        return site_id, project_id, mapping_id


def _association_payload(site_id: UUID, project_id: UUID, mapping_id: UUID | None = None, *, key: str | None = None):
    return {
        "site_id": str(site_id),
        "project_id": str(project_id),
        "connector_mapping_id": str(mapping_id) if mapping_id is not None else None,
        "idempotency_key": key or f"association-{uuid4().hex}",
        "correlation_id": str(uuid4()),
    }


def test_associate_intake_operational_context_persists_hierarchy_and_event() -> None:
    intake_id = _create_intake()
    site_id, project_id, mapping_id = _seed_context()
    payload = _association_payload(site_id, project_id, mapping_id)

    response = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["organization_id"] == str(ORGANIZATION_ID)
    assert body["site_id"] == str(site_id)
    assert body["project_id"] == str(project_id)
    assert body["connector_mapping_id"] == str(mapping_id)
    with app.state.yarvis.persistence.create_session() as session:
        association = session.scalar(select(IntakeOperationalContextAssociation))
        event = session.scalar(
            select(DomainEvent).where(DomainEvent.event_type == "intake.operational_context_associated")
        )
        assert association is not None
        assert event is not None
        assert session.get(IntakeItem, intake_id).intake_mode == DETERMINISTIC_INTAKE_MODE
        assert association.organization_id == ORGANIZATION_ID
        assert event.aggregate_id == intake_id
        assert event.payload["association_id"] == str(association.id)
        assert "text_body" not in event.payload


def test_association_replay_returns_original_and_creates_no_duplicate_event() -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    payload = _association_payload(site_id, project_id, key="association-replay")
    first = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())
    second = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())

    assert first.status_code == second.status_code == 201
    assert first.json()["association_id"] == second.json()["association_id"]
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(IntakeOperationalContextAssociation)) == 1
        assert session.scalar(
            select(func.count()).select_from(DomainEvent).where(
                DomainEvent.event_type == "intake.operational_context_associated"
            )
        ) == 1


def test_optional_connector_mapping_is_supported_and_request_cannot_supply_organization() -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    payload = _association_payload(site_id, project_id)
    payload["organization_id"] = str(OTHER_ORGANIZATION_ID)

    rejected = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())
    assert rejected.status_code == 422

    payload.pop("organization_id")
    response = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())
    assert response.status_code == 201
    assert response.json()["organization_id"] == str(ORGANIZATION_ID)
    assert response.json()["connector_mapping_id"] is None


def test_existing_association_with_another_key_is_immutable_conflict() -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    first = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id, key="association-first"),
        headers=_headers(),
    )
    conflict = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id, key="association-other"),
        headers=_headers(),
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "CONFLICT"


def test_same_key_with_different_context_is_a_conflict() -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    other_site_id, other_project_id, _ = _seed_context()
    first = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id, key="association-conflicting-reuse"),
        headers=_headers(),
    )
    conflict = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(other_site_id, other_project_id, key="association-conflicting-reuse"),
        headers=_headers(),
    )
    assert first.status_code == 201
    assert conflict.status_code == 409


@pytest.mark.parametrize("target", ("intake", "site", "project", "mapping"))
def test_cross_tenant_and_hierarchy_targets_are_concealed(target: str) -> None:
    intake_id = _create_intake()
    site_id, project_id, mapping_id = _seed_context()
    other_site_id, other_project_id, other_mapping_id = _seed_context(organization_id=OTHER_ORGANIZATION_ID)
    if target == "intake":
        intake_id = _create_intake(organization_id=OTHER_ORGANIZATION_ID)
    elif target == "site":
        site_id = other_site_id
    elif target == "project":
        project_id = other_project_id
    else:
        mapping_id = other_mapping_id
    response = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id, mapping_id),
        headers=_headers(),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_project_under_another_site_is_concealed() -> None:
    intake_id = _create_intake()
    site_id, _, _ = _seed_context()
    second_site_id, second_project_id, _ = _seed_context()
    response = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, second_project_id),
        headers=_headers(),
    )

    assert second_site_id != site_id
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_command_requires_exact_authority_and_query_returns_same_tenant_association() -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    denied = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id),
        headers=_headers(authority="inbound.read"),
    )
    assert denied.status_code == 403

    payload = _association_payload(site_id, project_id)
    created = client.post(f"/intake/deterministic/{intake_id}/operational-context", json=payload, headers=_headers())
    query = client.get(
        f"/intake/deterministic/{intake_id}/operational-context",
        headers=_headers(authority="inbound.read"),
    )
    concealed = client.get(
        f"/intake/deterministic/{intake_id}/operational-context",
        headers=_headers(organization_id=OTHER_ORGANIZATION_ID, authority="inbound.read"),
    )

    assert created.status_code == 201
    assert query.status_code == 200
    assert query.json()["association_id"] == created.json()["association_id"]
    assert concealed.status_code == 404


@pytest.mark.parametrize("header", ("x-yarvis-actor", "x-yarvis-authority", "x-yarvis-organization"))
def test_command_rejects_missing_trusted_principal_context(header: str) -> None:
    intake_id = _create_intake()
    site_id, project_id, _ = _seed_context()
    headers = _headers()
    headers.pop(header)
    response = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id),
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"


def test_same_idempotency_key_is_isolated_by_organization() -> None:
    first_intake_id = _create_intake()
    first_site_id, first_project_id, _ = _seed_context()
    second_intake_id = _create_intake(organization_id=OTHER_ORGANIZATION_ID)
    second_site_id, second_project_id, _ = _seed_context(organization_id=OTHER_ORGANIZATION_ID)
    key = "association-cross-tenant-key"

    first = client.post(
        f"/intake/deterministic/{first_intake_id}/operational-context",
        json=_association_payload(first_site_id, first_project_id, key=key),
        headers=_headers(),
    )
    second = client.post(
        f"/intake/deterministic/{second_intake_id}/operational-context",
        json=_association_payload(second_site_id, second_project_id, key=key),
        headers=_headers(organization_id=OTHER_ORGANIZATION_ID),
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["association_id"] != second.json()["association_id"]


def test_legacy_null_intake_is_concealed() -> None:
    with app.state.yarvis.persistence.create_session() as session:
        legacy = IntakeItem(source_type="manual_text", content_type="text/plain", text_content="legacy")
        session.add(legacy)
        session.commit()
        legacy_id = legacy.id
    site_id, project_id, _ = _seed_context()
    response = client.post(
        f"/intake/deterministic/{legacy_id}/operational-context",
        json=_association_payload(site_id, project_id),
        headers=_headers(),
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "source_metadata, idempotency_key, idempotency_fingerprint",
    (
        ({}, None, None),
        ({"external_source": "email", "connector_delivery_id": "incidental"}, "incidental-key", "0" * 64),
    ),
)
def test_tenant_owned_non_deterministic_intake_is_concealed(
    source_metadata: dict[str, object], idempotency_key: str | None, idempotency_fingerprint: str | None
) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        intake = IntakeItem(
            source_type="manual_text",
            content_type="text/plain",
            text_content="non-deterministic",
            organization_id=ORGANIZATION_ID,
            intake_mode=LEGACY_INTAKE_MODE,
            source_metadata=source_metadata,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
        )
        session.add(intake)
        session.commit()
        intake_id = intake.id
    site_id, project_id, _ = _seed_context()

    response = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json=_association_payload(site_id, project_id),
        headers=_headers(),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def _commit_expect_integrity_error(item: object) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add(item)
        with pytest.raises(IntegrityError):
            session.commit()


def test_database_rejects_invalid_hierarchy_and_association_ownership() -> None:
    first_site_id, first_project_id, first_mapping_id = _seed_context()
    second_site_id, second_project_id, second_mapping_id = _seed_context()
    other_site_id, other_project_id, _ = _seed_context(organization_id=OTHER_ORGANIZATION_ID)
    intake_id = _create_intake()

    _commit_expect_integrity_error(
        Project(id=uuid4(), organization_id=OTHER_ORGANIZATION_ID, site_id=first_site_id, reference="cross-tenant-project")
    )
    _commit_expect_integrity_error(
        ConnectorMapping(
            id=uuid4(),
            organization_id=OTHER_ORGANIZATION_ID,
            project_id=first_project_id,
            connector_reference="cross-tenant-mapping",
        )
    )
    _commit_expect_integrity_error(
        IntakeOperationalContextAssociation(
            id=uuid4(),
            intake_item_id=intake_id,
            organization_id=OTHER_ORGANIZATION_ID,
            site_id=other_site_id,
            project_id=other_project_id,
            idempotency_key="association-cross-tenant-intake",
            idempotency_fingerprint="0" * 64,
            actor_id="operator:context-01",
            correlation_id=uuid4(),
        )
    )
    _commit_expect_integrity_error(
        IntakeOperationalContextAssociation(
            id=uuid4(),
            intake_item_id=intake_id,
            organization_id=ORGANIZATION_ID,
            site_id=first_site_id,
            project_id=second_project_id,
            idempotency_key="association-wrong-site",
            idempotency_fingerprint="1" * 64,
            actor_id="operator:context-01",
            correlation_id=uuid4(),
        )
    )
    _commit_expect_integrity_error(
        IntakeOperationalContextAssociation(
            id=uuid4(),
            intake_item_id=intake_id,
            organization_id=ORGANIZATION_ID,
            site_id=first_site_id,
            project_id=first_project_id,
            connector_mapping_id=second_mapping_id,
            idempotency_key="association-wrong-mapping",
            idempotency_fingerprint="2" * 64,
            actor_id="operator:context-01",
            correlation_id=uuid4(),
        )
    )
    with app.state.yarvis.persistence.create_session() as session:
        session.add(
            IntakeOperationalContextAssociation(
                id=uuid4(),
                intake_item_id=intake_id,
                organization_id=ORGANIZATION_ID,
                site_id=first_site_id,
                project_id=first_project_id,
                connector_mapping_id=first_mapping_id,
                idempotency_key="association-valid-hierarchy",
                idempotency_fingerprint="3" * 64,
                actor_id="operator:context-01",
                correlation_id=uuid4(),
            )
        )
        session.commit()


def test_database_enforces_reference_uniqueness_scopes() -> None:
    first_site_id, first_project_id, _ = _seed_context()
    second_site_id, second_project_id, _ = _seed_context()

    with app.state.yarvis.persistence.create_session() as session:
        session.add(Site(id=uuid4(), organization_id=ORGANIZATION_ID, reference="site-duplicate"))
        session.commit()
    _commit_expect_integrity_error(Site(id=uuid4(), organization_id=ORGANIZATION_ID, reference="site-duplicate"))
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Site(id=uuid4(), organization_id=OTHER_ORGANIZATION_ID, reference="site-duplicate"))
        session.commit()

    with app.state.yarvis.persistence.create_session() as session:
        session.add(Project(id=uuid4(), organization_id=ORGANIZATION_ID, site_id=first_site_id, reference="project-duplicate"))
        session.commit()
    _commit_expect_integrity_error(Project(id=uuid4(), organization_id=ORGANIZATION_ID, site_id=first_site_id, reference="project-duplicate"))
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Project(id=uuid4(), organization_id=ORGANIZATION_ID, site_id=second_site_id, reference="project-duplicate"))
        session.commit()

    with app.state.yarvis.persistence.create_session() as session:
        session.add(
            ConnectorMapping(
                id=uuid4(),
                organization_id=ORGANIZATION_ID,
                project_id=first_project_id,
                connector_reference="mapping-duplicate",
            )
        )
        session.commit()
    _commit_expect_integrity_error(
        ConnectorMapping(id=uuid4(), organization_id=ORGANIZATION_ID, project_id=first_project_id, connector_reference="mapping-duplicate")
    )
    with app.state.yarvis.persistence.create_session() as session:
        session.add(
            ConnectorMapping(
                id=uuid4(),
                organization_id=ORGANIZATION_ID,
                project_id=second_project_id,
                connector_reference="mapping-duplicate",
            )
        )
        session.commit()

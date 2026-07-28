from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "process.definition.manage") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:process",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(id=ORGANIZATION_ID, legal_name="Processes", display_name="Processes"),
                Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other", display_name="Other"),
            )
        )
        session.commit()


def _create(*, name: str | None = None, organization_id: UUID = ORGANIZATION_ID) -> dict:
    response = client.post(
        "/process-definitions",
        json={"name": name or f"Process {uuid4().hex}", "description": "generic operational flow"},
        headers=_headers(organization_id),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _stage(definition_id: str, key: str, stage_type: str, display_order: int, *, organization_id: UUID = ORGANIZATION_ID) -> dict:
    response = client.post(
        f"/process-definitions/{definition_id}/stages",
        json={
            "stage_key": key,
            "name": key.replace("_", " ").title(),
            "description": None,
            "stage_type": stage_type,
            "display_order": display_order,
            "metadata_json": {"generic": True},
        },
        headers=_headers(organization_id),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _valid_definition(organization_id: UUID = ORGANIZATION_ID) -> dict:
    definition = _create(organization_id=organization_id)
    definition = _stage(definition["id"], "begin", "start", 0, organization_id=organization_id)
    return _stage(definition["id"], "complete", "terminal", 1, organization_id=organization_id)


def _event_types(definition_id: str) -> list[str]:
    with app.state.yarvis.persistence.create_session() as session:
        return list(
            session.scalars(
                select(DomainEvent.event_type)
                .where(DomainEvent.aggregate_id == UUID(definition_id))
                .order_by(DomainEvent.event_sequence.asc())
            )
        )


def test_draft_crud_list_detail_and_same_version_transition_validation() -> None:
    definition = _create(name="Generic Onboarding")
    definition = _stage(definition["id"], "begin", "start", 0)
    start_id = definition["stages"][0]["id"]
    definition = _stage(definition["id"], "complete", "terminal", 1)
    terminal_id = next(stage["id"] for stage in definition["stages"] if stage["stage_key"] == "complete")

    transition = client.post(
        f"/process-definitions/{definition['id']}/transitions",
        json={"from_stage_id": start_id, "to_stage_id": terminal_id, "name": "complete"},
        headers=_headers(),
    )
    assert transition.status_code == 200, transition.text
    assert transition.json()["transitions"][0]["name"] == "complete"

    changed_stage = client.put(
        f"/process-definitions/{definition['id']}/stages/{start_id}",
        json={"stage_key": "begin", "name": "Begin work", "stage_type": "start", "display_order": 0},
        headers=_headers(),
    )
    assert changed_stage.status_code == 200, changed_stage.text
    transition_id = changed_stage.json()["transitions"][0]["id"]
    changed_transition = client.put(
        f"/process-definitions/{definition['id']}/transitions/{transition_id}",
        json={"name": "complete work"},
        headers=_headers(),
    )
    assert changed_transition.status_code == 200, changed_transition.text
    deleted_transition = client.delete(
        f"/process-definitions/{definition['id']}/transitions/{transition_id}",
        headers=_headers(),
    )
    assert deleted_transition.status_code == 200, deleted_transition.text
    deleted_stage = client.delete(
        f"/process-definitions/{definition['id']}/stages/{terminal_id}",
        headers=_headers(),
    )
    assert deleted_stage.status_code == 200, deleted_stage.text
    assert [stage["stage_key"] for stage in deleted_stage.json()["stages"]] == ["begin"]

    definition = _stage(definition["id"], "complete", "terminal", 1)
    terminal_id = next(stage["id"] for stage in definition["stages"] if stage["stage_key"] == "complete")
    restored = client.post(
        f"/process-definitions/{definition['id']}/transitions",
        json={"from_stage_id": start_id, "to_stage_id": terminal_id, "name": "complete"},
        headers=_headers(),
    )
    assert restored.status_code == 200, restored.text

    listed = client.get("/process-definitions", headers=_headers(authority="process.definition.read"))
    assert listed.status_code == 200
    assert [(item["name"], item["version"]) for item in listed.json()] == [("Generic Onboarding", 1)]
    detail = client.get(f"/process-definitions/{definition['id']}", headers=_headers(authority="process.definition.read"))
    assert detail.status_code == 200
    assert [stage["stage_key"] for stage in detail.json()["stages"]] == ["begin", "complete"]

    duplicate = client.post(
        f"/process-definitions/{definition['id']}/stages",
        json={"stage_key": "begin", "name": "Duplicate", "stage_type": "work", "display_order": 2},
        headers=_headers(),
    )
    assert duplicate.status_code == 409

    external = _valid_definition()
    invalid_transition = client.post(
        f"/process-definitions/{definition['id']}/transitions",
        json={"from_stage_id": start_id, "to_stage_id": external["stages"][0]["id"], "name": "invalid"},
        headers=_headers(),
    )
    assert invalid_transition.status_code == 400


def test_publish_requires_exactly_one_start_and_a_terminal_then_published_version_is_immutable() -> None:
    invalid = _create()
    no_start = client.post(f"/process-definitions/{invalid['id']}/publish", headers=_headers())
    assert no_start.status_code == 400

    definition = _valid_definition()
    published = client.post(f"/process-definitions/{definition['id']}/publish", headers=_headers())
    assert published.status_code == 200, published.text
    assert published.json()["lifecycle"] == "published"

    stage = published.json()["stages"][0]
    immutable = client.put(
        f"/process-definitions/{definition['id']}/stages/{stage['id']}",
        json={"stage_key": stage["stage_key"], "name": "Changed", "stage_type": "start", "display_order": 0},
        headers=_headers(),
    )
    assert immutable.status_code == 409
    assert _event_types(definition["id"]) == ["process_definition.created", "process_definition.published"]


def test_new_version_clones_published_graph_and_retirement_records_append_only_events() -> None:
    published = _valid_definition()
    publish = client.post(f"/process-definitions/{published['id']}/publish", headers=_headers())
    assert publish.status_code == 200

    version = client.post(f"/process-definitions/{published['id']}/versions", headers=_headers())
    assert version.status_code == 201, version.text
    clone = version.json()
    assert clone["version"] == 2 and clone["lifecycle"] == "draft"
    assert [stage["stage_key"] for stage in clone["stages"]] == ["begin", "complete"]

    retired = client.post(f"/process-definitions/{published['id']}/retire", headers=_headers())
    assert retired.status_code == 200 and retired.json()["lifecycle"] == "retired"
    assert _event_types(published["id"]) == [
        "process_definition.created",
        "process_definition.published",
        "process_definition.retired",
    ]
    assert _event_types(clone["id"]) == ["process_definition.version_created"]


def test_cross_tenant_resources_are_concealed_and_authority_is_required() -> None:
    definition = _create()
    hidden = client.get(
        f"/process-definitions/{definition['id']}",
        headers=_headers(OTHER_ORGANIZATION_ID, "process.definition.read"),
    )
    assert hidden.status_code == 404
    denied = client.get(f"/process-definitions/{definition['id']}", headers=_headers(authority="mission.work.read"))
    assert denied.status_code == 403
    denied_create = client.post("/process-definitions", json={"name": "Denied"}, headers=_headers(authority="process.definition.read"))
    assert denied_create.status_code == 403


def test_process_definition_events_are_append_only_and_organization_scoped() -> None:
    own = _valid_definition()
    other = _valid_definition(OTHER_ORGANIZATION_ID)
    hidden = client.get(f"/process-definitions/{other['id']}", headers=_headers(authority="process.definition.read"))
    assert hidden.status_code == 404

    events = _event_types(own["id"])
    assert events == ["process_definition.created"]
    with app.state.yarvis.persistence.create_session() as session:
        count = session.scalar(
            select(func.count())
            .select_from(DomainEvent)
            .where(DomainEvent.organization_id == ORGANIZATION_ID)
            .where(DomainEvent.aggregate_id == UUID(own["id"]))
        )
    assert count == 1

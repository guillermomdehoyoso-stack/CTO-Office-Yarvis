from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.process import ProcessInstanceEvent


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "process.definition.manage") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:process-runtime",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((
            Organization(id=ORGANIZATION_ID, legal_name="Runtime", display_name="Runtime"),
            Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other Runtime", display_name="Other Runtime"),
        ))
        session.commit()


def _definition(organization_id: UUID = ORGANIZATION_ID) -> dict:
    created = client.post("/process-definitions", json={"name": f"Runtime {uuid4().hex}"}, headers=_headers(organization_id))
    assert created.status_code == 201, created.text
    definition = created.json()
    for key, stage_type, order in (("start", "start", 0), ("work", "work", 1), ("done", "terminal", 2)):
        response = client.post(
            f"/process-definitions/{definition['id']}/stages",
            json={"stage_key": key, "name": key.title(), "stage_type": stage_type, "display_order": order},
            headers=_headers(organization_id),
        )
        assert response.status_code == 200, response.text
        definition = response.json()
    stage_ids = {stage["stage_key"]: stage["id"] for stage in definition["stages"]}
    for source, target in (("start", "work"), ("work", "done")):
        response = client.post(
            f"/process-definitions/{definition['id']}/transitions",
            json={"from_stage_id": stage_ids[source], "to_stage_id": stage_ids[target], "name": f"{source}-to-{target}"},
            headers=_headers(organization_id),
        )
        assert response.status_code == 200, response.text
        definition = response.json()
    published = client.post(f"/process-definitions/{definition['id']}/publish", headers=_headers(organization_id))
    assert published.status_code == 200, published.text
    return published.json()


def _start(definition_id: str, *, organization_id: UUID = ORGANIZATION_ID, key: str | None = None) -> dict:
    response = client.post(
        "/process-instances",
        json={"process_definition_id": definition_id, "idempotency_key": key or uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers(organization_id, "process.instance.start"),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _transition(instance_id: str, transition_id: str, version: int, *, key: str | None = None, organization_id: UUID = ORGANIZATION_ID):
    return client.post(
        f"/process-instances/{instance_id}/transitions",
        json={"transition_id": transition_id, "expected_version": version, "idempotency_key": key or uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers(organization_id, "process.instance.transition"),
    )


def test_start_transition_completion_timeline_and_idempotent_start() -> None:
    definition = _definition()
    start_key = uuid4().hex
    instance = _start(definition["id"], key=start_key)
    replay = _start(definition["id"], key=start_key)
    assert instance["id"] == replay["id"]
    assert instance["lifecycle"] == "active" and instance["version"] == 1
    transitions = {transition["name"]: transition["id"] for transition in definition["transitions"]}
    work = _transition(instance["id"], transitions["start-to-work"], 1)
    assert work.status_code == 200 and work.json()["lifecycle"] == "active" and work.json()["version"] == 2
    completed = _transition(instance["id"], transitions["work-to-done"], 2)
    assert completed.status_code == 200, completed.text
    assert completed.json()["lifecycle"] == "completed" and completed.json()["version"] == 3
    timeline = client.get(f"/process-instances/{instance['id']}/timeline", headers=_headers(authority="process.instance.read"))
    assert timeline.status_code == 200
    events = timeline.json()["items"]
    assert [event["sequence_number"] for event in events] == [1, 2, 3, 4]
    assert [event["event_type"] for event in events] == ["process_instance.started", "process_instance.transitioned", "process_instance.transitioned", "process_instance.completed"]
    with app.state.yarvis.persistence.create_session() as session:
        event_types = session.scalars(
            select(DomainEvent.event_type).where(DomainEvent.aggregate_id == UUID(instance["id"])).order_by(DomainEvent.event_sequence.asc())
        ).all()
    assert event_types == ["process_instance.started", "process_instance.transitioned", "process_instance.transitioned", "process_instance.completed"]


def test_retired_definition_blocks_new_instance_but_existing_instance_can_continue() -> None:
    definition = _definition()
    instance = _start(definition["id"])
    retired = client.post(f"/process-definitions/{definition['id']}/retire", headers=_headers())
    assert retired.status_code == 200
    denied = client.post(
        "/process-instances",
        json={"process_definition_id": definition["id"], "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers(authority="process.instance.start"),
    )
    assert denied.status_code == 409
    transition_id = next(item["id"] for item in definition["transitions"] if item["name"] == "start-to-work")
    assert _transition(instance["id"], transition_id, 1).status_code == 200


def test_cancel_is_final_idempotent_and_requires_reason() -> None:
    instance = _start(_definition()["id"])
    cancel_key = uuid4().hex
    payload = {"expected_version": 1, "reason": "Operator stopped the process.", "idempotency_key": cancel_key, "correlation_id": str(uuid4())}
    cancelled = client.post(f"/process-instances/{instance['id']}/cancel", json=payload, headers=_headers(authority="process.instance.cancel"))
    assert cancelled.status_code == 200 and cancelled.json()["lifecycle"] == "cancelled"
    replay = client.post(f"/process-instances/{instance['id']}/cancel", json=payload, headers=_headers(authority="process.instance.cancel"))
    assert replay.status_code == 200 and replay.json()["id"] == instance["id"]
    assert client.post(f"/process-instances/{instance['id']}/cancel", json={**payload, "idempotency_key": uuid4().hex, "expected_version": 2}, headers=_headers(authority="process.instance.cancel")).status_code == 409
    assert client.post(f"/process-instances/{instance['id']}/cancel", json={**payload, "reason": ""}, headers=_headers(authority="process.instance.cancel")).status_code == 422


def test_runtime_is_tenant_scoped_authorized_and_events_are_append_only() -> None:
    instance = _start(_definition()["id"])
    hidden = client.get(f"/process-instances/{instance['id']}", headers=_headers(OTHER_ORGANIZATION_ID, "process.instance.read"))
    denied = client.get(f"/process-instances/{instance['id']}", headers=_headers(authority="process.definition.read"))
    assert hidden.status_code == 404
    assert denied.status_code == 403
    event_id = client.get(f"/process-instances/{instance['id']}/timeline", headers=_headers(authority="process.instance.read")).json()["items"][0]["id"]
    with app.state.yarvis.persistence.create_session() as session:
        with pytest.raises(DBAPIError):
            session.execute(update(ProcessInstanceEvent).where(ProcessInstanceEvent.id == UUID(event_id)).values(event_type="changed"))
            session.commit()
        session.rollback()
        with pytest.raises(DBAPIError):
            session.execute(delete(ProcessInstanceEvent).where(ProcessInstanceEvent.id == UUID(event_id)))
            session.commit()
        session.rollback()

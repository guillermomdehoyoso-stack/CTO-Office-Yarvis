from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.process import ProcessInstanceWorkLink
from yarvis_api.models.process import ProcessInstance, ProcessTransition


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "process.instance.work.link") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:process-work-link",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((Organization(id=ORGANIZATION_ID, legal_name="Association", display_name="Association"), Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other", display_name="Other")))
        session.commit()


def _work(organization_id: UUID = ORGANIZATION_ID) -> UUID:
    work_id = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(MissionWorkItem(id=work_id, organization_id=organization_id, inbox_item_id=uuid4(), source_type="test", source_id=uuid4(), title="Associated work", status="open", priority="normal", created_by_subject_id="operator:test"))
        session.commit()
    return work_id


def _instance(organization_id: UUID = ORGANIZATION_ID) -> dict:
    definition = client.post("/process-definitions", json={"name": f"Association {uuid4().hex}"}, headers=_headers(organization_id, "process.definition.manage")).json()
    for key, stage_type, order in (("start", "start", 0), ("finish", "terminal", 1)):
        definition = client.post(f"/process-definitions/{definition['id']}/stages", json={"stage_key": key, "name": key.title(), "stage_type": stage_type, "display_order": order}, headers=_headers(organization_id, "process.definition.manage")).json()
    stages = {item["stage_key"]: item["id"] for item in definition["stages"]}
    definition = client.post(f"/process-definitions/{definition['id']}/transitions", json={"from_stage_id": stages["start"], "to_stage_id": stages["finish"], "name": "finish"}, headers=_headers(organization_id, "process.definition.manage")).json()
    assert client.post(f"/process-definitions/{definition['id']}/publish", headers=_headers(organization_id, "process.definition.manage")).status_code == 200
    response = client.post("/process-instances", json={"process_definition_id": definition["id"], "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(organization_id, "process.instance.start"))
    assert response.status_code == 201, response.text
    return response.json()


def _link(instance_id: str, work_id: UUID, *, key: str | None = None, organization_id: UUID = ORGANIZATION_ID):
    return client.post(f"/process-instances/{instance_id}/work-links", json={"mission_work_item_id": str(work_id), "relationship_type": "primary", "idempotency_key": key or uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(organization_id))


def test_link_is_tenant_scoped_idempotent_and_projects_process_history() -> None:
    instance, work_id, key = _instance(), _work(), uuid4().hex
    linked = _link(instance["id"], work_id, key=key)
    replay = _link(instance["id"], work_id, key=key)
    assert linked.status_code == 201, linked.text
    assert replay.status_code == 201 and replay.json()["id"] == linked.json()["id"]
    timeline = client.get(f"/mission/work-items/{work_id}/timeline", headers=_headers(authority="mission.work.read"))
    assert timeline.status_code == 200
    assert [event["event_type"] for event in timeline.json()["items"]] == ["process.started", "process.work_linked"]
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(ProcessInstanceWorkLink)) == 1
        assert session.scalar(select(func.count()).select_from(MissionWorkEvent).where(MissionWorkEvent.work_item_id == work_id)) == 2
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type == "process_instance.work_linked")) == 1


def test_primary_constraint_history_and_multiple_instances_per_work() -> None:
    work_id, first, second = _work(), _instance(), _instance()
    linked = _link(first["id"], work_id)
    assert linked.status_code == 201
    assert _link(first["id"], _work()).status_code == 409
    assert _link(second["id"], work_id).status_code == 201
    unlink_payload = {"idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}
    unlinked = client.post(f"/process-instances/{first['id']}/work-links/{linked.json()['id']}/unlink", json=unlink_payload, headers=_headers(authority="process.instance.work.unlink"))
    assert unlinked.status_code == 200 and unlinked.json()["unlinked_at"] is not None
    replay = client.post(f"/process-instances/{first['id']}/work-links/{linked.json()['id']}/unlink", json=unlink_payload, headers=_headers(authority="process.instance.work.unlink"))
    assert replay.status_code == 200 and replay.json()["id"] == linked.json()["id"]
    assert _link(first["id"], work_id).status_code == 201
    history = client.get(f"/process-instances/{first['id']}/work-links", headers=_headers(authority="process.instance.read"))
    assert history.status_code == 200 and len(history.json()["items"]) == 2


def test_cross_tenant_and_missing_resources_are_concealed() -> None:
    instance, work_id = _instance(), _work()
    assert _link(instance["id"], work_id, organization_id=OTHER_ORGANIZATION_ID).status_code == 404
    assert _link(str(uuid4()), work_id).status_code == 404
    assert _link(instance["id"], uuid4()).status_code == 404


def test_transition_completion_and_cancellation_are_projected_without_lifecycle_coupling() -> None:
    work_id, instance = _work(), _instance()
    assert _link(instance["id"], work_id).status_code == 201
    with app.state.yarvis.persistence.create_session() as session:
        process = session.get(ProcessInstance, UUID(instance["id"]))
        transition_id = session.scalar(select(ProcessTransition.id).where(ProcessTransition.process_definition_id == process.process_definition_id))
    completed = client.post(f"/process-instances/{instance['id']}/transitions", json={"transition_id": str(transition_id), "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority="process.instance.transition"))
    assert completed.status_code == 200 and completed.json()["lifecycle"] == "completed"
    event_types = [item["event_type"] for item in client.get(f"/mission/work-items/{work_id}/timeline", headers=_headers(authority="mission.work.read")).json()["items"]]
    assert "process.transitioned" in event_types and "process.completed" in event_types

    cancelled_work, cancelled_instance = _work(), _instance()
    assert _link(cancelled_instance["id"], cancelled_work).status_code == 201
    cancelled = client.post(f"/process-instances/{cancelled_instance['id']}/cancel", json={"expected_version": 1, "reason": "No longer required", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority="process.instance.cancel"))
    assert cancelled.status_code == 200 and cancelled.json()["lifecycle"] == "cancelled"
    cancelled_events = [item["event_type"] for item in client.get(f"/mission/work-items/{cancelled_work}/timeline", headers=_headers(authority="mission.work.read")).json()["items"]]
    assert "process.cancelled" in cancelled_events

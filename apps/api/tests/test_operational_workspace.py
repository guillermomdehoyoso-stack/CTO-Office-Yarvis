"""Focused conformance coverage for the WS-006E read-only workspace."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from yarvis_api.main import app
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceEvent, ProcessInstanceWorkLink, ProcessStage


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.read") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:workspace",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def workspace_subject(clean_database) -> tuple[UUID, UUID]:
    now = datetime.now(timezone.utc)
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((
            Organization(id=ORGANIZATION_ID, legal_name="Workspace", display_name="Workspace"),
            Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other workspace", display_name="Other workspace"),
        ))
        session.flush()
        work = MissionWorkItem(
            organization_id=ORGANIZATION_ID, inbox_item_id=uuid4(), source_type="test", source_id=uuid4(),
            title="Workspace work", summary="Read composition", status="assigned", priority="high",
            assignee_subject_id="operator:assigned", created_by_subject_id="operator:creator", created_at=now, updated_at=now,
        )
        session.add(work)
        definition = ProcessDefinition(organization_id=ORGANIZATION_ID, name="Workspace process", version=1, lifecycle="published", created_at=now, updated_at=now, published_at=now)
        session.add(definition)
        session.flush()
        stage = ProcessStage(organization_id=ORGANIZATION_ID, process_definition_id=definition.id, stage_key="work", name="Work", stage_type="work", display_order=1)
        session.add(stage)
        session.flush()
        instance = ProcessInstance(
            organization_id=ORGANIZATION_ID, process_definition_id=definition.id, process_definition_version=1,
            current_stage_id=stage.id, lifecycle="active", created_by_subject_id="operator:creator", created_at=now,
            updated_at=now, version=1, start_idempotency_key=uuid4().hex, start_request_fingerprint="a" * 64,
        )
        session.add(instance)
        session.flush()
        session.add_all((
            ProcessInstanceWorkLink(organization_id=ORGANIZATION_ID, mission_work_item_id=work.id, process_instance_id=instance.id, relationship_type="primary", linked_at=now, created_by_authority_id="process.instance.work.link", link_idempotency_key=uuid4().hex, link_request_fingerprint="b" * 64),
            MissionWorkEvent(organization_id=ORGANIZATION_ID, work_item_id=work.id, occurred_at=now, event_type="work_item.created", actor_subject_id="operator:creator", payload_json={"work_item_id": str(work.id)}, sequence_number=1),
            ProcessInstanceEvent(organization_id=ORGANIZATION_ID, process_instance_id=instance.id, occurred_at=now, event_type="process_instance.transitioned", actor_subject_id="operator:creator", payload_json={"previous_stage_key": "start", "stage_key": "work"}, sequence_number=1),
        ))
        session.commit()
        return work.id, instance.id


def _record(subject_type: str, subject_id: UUID, fact_type: str, amount: str) -> None:
    response = client.post(
        "/operational-economics/facts",
        json={
            "subject_type": subject_type, "subject_id": str(subject_id), "fact_type": fact_type,
            "amount": amount, "currency": "MXN", "effective_at": "2026-07-29T00:00:00+00:00",
            "source_type": "test", "source_reference": uuid4().hex, "evidence_references": [],
            "idempotency_key": uuid4().hex, "correlation_id": str(uuid4()),
        }, headers=_headers(authority="economics.fact.record"),
    )
    assert response.status_code == 201, response.text


def test_workspace_composes_owner_read_models_without_economic_rollup(workspace_subject: tuple[UUID, UUID]) -> None:
    work_id, instance_id = workspace_subject
    _record("mission_work_item", work_id, "revenue_expected", "1000.00")
    _record("process_instance", instance_id, "revenue_expected", "200.00")
    response = client.get(f"/mission/work-items/{work_id}/workspace?currency=MXN", headers=_headers())
    assert response.status_code == 200, response.text
    workspace = response.json()
    assert workspace["work_item"]["id"] == str(work_id)
    assert workspace["participants"] == ["operator:assigned", "operator:creator"]
    assert workspace["active_process_instance_count"] == 1
    assert workspace["historical_process_instance_count"] == 0
    assert workspace["economic_summary"]["expected_revenue"] == "1000.00"
    assert workspace["process_instances"][0]["economic_summary"]["expected_revenue"] == "200.00"
    assert workspace["timeline"]["items"][0]["sequence_number"] == 1
    assert workspace["process_instances"][0]["last_transition"]["event_type"] == "process_instance.transitioned"


def test_workspace_conceals_cross_tenant_work_and_enforces_authority(workspace_subject: tuple[UUID, UUID]) -> None:
    work_id, _ = workspace_subject
    assert client.get(f"/mission/work-items/{work_id}/workspace?currency=MXN", headers=_headers(OTHER_ORGANIZATION_ID)).status_code == 404
    assert client.get(f"/mission/work-items/{work_id}/workspace?currency=MXN", headers=_headers(authority="process.instance.read")).status_code == 403

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.organization import Organization


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.create") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:mission-work",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(id=ORGANIZATION_ID, legal_name="Work", display_name="Work"),
                Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other", display_name="Other"),
            )
        )
        session.commit()


def _inbox(organization_id: UUID = ORGANIZATION_ID, *, subject: str = "Governed work") -> UUID:
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/intake/deterministic",
        json={
            "external_source": "email",
            "external_message_id": uuid4().hex,
            "sender": "sender@example.com",
            "recipients": ["ops@example.com"],
            "subject": subject,
            "text_body": "private",
            "content_type": "message/rfc822",
            "source_timestamp": now,
            "received_timestamp": now,
            "correlation_id": str(uuid4()),
            "idempotency_key": uuid4().hex,
        },
        headers=_headers(organization_id, "inbound.intake"),
    )
    assert response.status_code == 201, response.text
    inbox = client.get("/mission/inbox", headers=_headers(organization_id, "mission.inbox.read")).json()["items"]
    return UUID(next(item["id"] for item in inbox if item["title"] == subject))


def _create(inbox_id: UUID, organization_id: UUID = ORGANIZATION_ID):
    return client.post("/mission/work-items", json={"inbox_item_id": str(inbox_id)}, headers=_headers(organization_id))


def _new_item(*, organization_id: UUID = ORGANIZATION_ID, subject: str | None = None) -> dict:
    response = _create(_inbox(organization_id, subject=subject or f"Work {uuid4().hex}"), organization_id)
    assert response.status_code == 201, response.text
    return response.json()


def _event_count(work_item_id: str, event_type: str | None = None) -> int:
    with app.state.yarvis.persistence.create_session() as session:
        query = select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == UUID(work_item_id))
        if event_type:
            query = query.where(DomainEvent.event_type == event_type)
        return session.scalar(query) or 0


def _latest_event(work_item_id: str, event_type: str) -> DomainEvent:
    with app.state.yarvis.persistence.create_session() as session:
        event = session.scalar(
            select(DomainEvent)
            .where(DomainEvent.aggregate_id == UUID(work_item_id), DomainEvent.event_type == event_type)
            .order_by(DomainEvent.event_sequence.desc())
        )
        assert event is not None
        return event


def _detail(work_item_id: str, organization_id: UUID = ORGANIZATION_ID) -> dict:
    response = client.get(f"/mission/work-items/{work_item_id}", headers=_headers(organization_id, "mission.work.read"))
    assert response.status_code == 200, response.text
    return response.json()


def _status(work_item_id: str, status: str, organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.status.change"):
    return client.post(f"/mission/work-items/{work_item_id}/status", json={"status": status}, headers=_headers(organization_id, authority))


def _assignment(work_item_id: str, assignee: str | None, organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.assign"):
    return client.post(f"/mission/work-items/{work_item_id}/assignment", json={"assignee_subject_id": assignee}, headers=_headers(organization_id, authority))


def _priority(work_item_id: str, priority: str, organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.priority.change"):
    return client.post(f"/mission/work-items/{work_item_id}/priority", json={"priority": priority}, headers=_headers(organization_id, authority))


def _reach_status(work_item_id: str, status: str) -> None:
    paths = {
        "open": (),
        "assigned": ("assigned",),
        "in_progress": ("in_progress",),
        "waiting": ("waiting",),
        "resolved": ("in_progress", "resolved"),
        "cancelled": ("cancelled",),
    }
    for state in paths[status]:
        assert _status(work_item_id, state).status_code == 200


@pytest.mark.parametrize(
    ("initial", "target"),
    (
        ("open", "assigned"), ("open", "in_progress"), ("open", "waiting"), ("open", "cancelled"),
        ("assigned", "open"), ("assigned", "in_progress"), ("assigned", "waiting"), ("assigned", "cancelled"),
        ("in_progress", "assigned"), ("in_progress", "waiting"), ("in_progress", "resolved"), ("in_progress", "cancelled"),
        ("waiting", "assigned"), ("waiting", "in_progress"), ("waiting", "resolved"), ("waiting", "cancelled"),
        ("resolved", "open"), ("cancelled", "open"),
    ),
)
def test_complete_status_transition_matrix_records_one_event(initial: str, target: str) -> None:
    item = _new_item()
    item_id = item["id"]
    _reach_status(item_id, initial)
    before = _detail(item_id)
    event_count = _event_count(item_id, "mission.work_item_status_changed")

    response = _status(item_id, target)

    assert response.status_code == 200, response.text
    changed = response.json()
    assert changed["status"] == target
    assert changed["version"] == before["version"] + 1
    assert changed["updated_at"] >= before["updated_at"]
    assert _event_count(item_id, "mission.work_item_status_changed") == event_count + 1
    event = _latest_event(item_id, "mission.work_item_status_changed")
    assert event.payload == {
        "work_item_id": item_id,
        "previous_status": initial,
        "status": target,
        "version": changed["version"],
    }


@pytest.mark.parametrize(
    ("initial", "target"),
    (("open", "resolved"), ("assigned", "resolved"), ("resolved", "assigned"), ("resolved", "cancelled"), ("cancelled", "assigned"), ("cancelled", "resolved")),
)
def test_invalid_status_transitions_are_conflicts_and_rollback(initial: str, target: str) -> None:
    item = _new_item()
    item_id = item["id"]
    _reach_status(item_id, initial)
    before = _detail(item_id)
    events = _event_count(item_id)

    response = _status(item_id, target)

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"
    assert _detail(item_id) == before
    assert _event_count(item_id) == events


def test_timestamp_and_assignment_semantics_preserve_first_start_and_no_ops() -> None:
    item_id = _new_item()["id"]
    assigned = _assignment(item_id, "operator:one").json()
    assert assigned["status"] == "assigned" and assigned["assigned_at"] is not None
    same_assignment = _assignment(item_id, "operator:one").json()
    assert same_assignment["version"] == assigned["version"]
    assert same_assignment["assigned_at"] == assigned["assigned_at"]
    first_start = _status(item_id, "in_progress").json()
    assert first_start["started_at"] is not None
    waiting = _status(item_id, "waiting").json()
    reentered = _status(item_id, "in_progress").json()
    assert reentered["started_at"] == first_start["started_at"]
    resolved = _status(item_id, "resolved").json()
    assert resolved["resolved_at"] is not None
    reopened = _status(item_id, "open").json()
    assert reopened["resolved_at"] is None
    no_op_before = _detail(item_id)
    no_op = _status(item_id, "open").json()
    assert no_op["version"] == no_op_before["version"]
    assert no_op["updated_at"] == no_op_before["updated_at"]
    assert no_op["started_at"] == first_start["started_at"]
    assert waiting["version"] < reentered["version"] < resolved["version"] < reopened["version"]


def test_assignment_rules_and_rejected_unassignment_are_governed() -> None:
    item_id = _new_item()["id"]
    assigned = _assignment(item_id, "operator:one").json()
    reassigned = _assignment(item_id, "operator:two").json()
    assert reassigned["status"] == "assigned"
    assert reassigned["version"] == assigned["version"] + 1
    no_op = _assignment(item_id, "operator:two").json()
    assert no_op["version"] == reassigned["version"]
    unassigned = _assignment(item_id, None).json()
    assert unassigned["status"] == "open" and unassigned["assignee_subject_id"] is None and unassigned["assigned_at"] is None
    open_no_op = _assignment(item_id, None).json()
    assert open_no_op["version"] == unassigned["version"]

    for rejected_status in ("in_progress", "waiting", "resolved", "cancelled"):
        rejected_item = _new_item()["id"]
        assert _assignment(rejected_item, "operator:one").status_code == 200
        assert _status(rejected_item, "in_progress").status_code == 200
        if rejected_status == "waiting":
            assert _status(rejected_item, "waiting").status_code == 200
        elif rejected_status == "resolved":
            assert _status(rejected_item, "resolved").status_code == 200
        elif rejected_status == "cancelled":
            assert _status(rejected_item, "cancelled").status_code == 200
        before = _detail(rejected_item)
        events = _event_count(rejected_item)
        response = _assignment(rejected_item, None)
        assert response.status_code == 409 and response.json()["code"] == "CONFLICT"
        assert _detail(rejected_item) == before
        assert _event_count(rejected_item) == events


@pytest.mark.parametrize(
    ("endpoint", "payload", "required_authority"),
    (
        ("/mission/work-items", {"inbox_item_id": "{inbox_id}"}, "mission.work.create"),
        ("/mission/work-items/{work_id}/assignment", {"assignee_subject_id": "operator:two"}, "mission.work.assign"),
        ("/mission/work-items/{work_id}/status", {"status": "waiting"}, "mission.work.status.change"),
        ("/mission/work-items/{work_id}/priority", {"priority": "high"}, "mission.work.priority.change"),
    ),
)
def test_mutation_authorities_are_directly_enforced(endpoint: str, payload: dict, required_authority: str) -> None:
    inbox_id = _inbox()
    work_id = _new_item()["id"]
    url = endpoint.format(inbox_id=inbox_id, work_id=work_id)
    body = {key: (str(inbox_id) if value == "{inbox_id}" else value) for key, value in payload.items()}
    response = client.post(url, json=body, headers=_headers(authority="mission.work.read"))
    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert required_authority != "mission.work.read"


def test_read_authority_and_actor_are_required() -> None:
    item_id = _new_item()["id"]
    for url in ("/mission/work-items", f"/mission/work-items/{item_id}"):
        response = client.get(url, headers=_headers(authority="mission.work.create"))
        assert response.status_code == 403 and response.json()["code"] == "AUTHORIZATION_DENIED"
        headers = _headers(authority="mission.work.read")
        headers.pop("x-yarvis-actor")
        response = client.get(url, headers=headers)
        assert response.status_code == 403 and response.json()["code"] == "AUTHORIZATION_DENIED"


def test_cross_tenant_operations_are_concealed() -> None:
    own = _new_item()
    other_inbox = _inbox(OTHER_ORGANIZATION_ID)
    other = _new_item(organization_id=OTHER_ORGANIZATION_ID)
    operations = (
        ("post", "/mission/work-items", {"inbox_item_id": str(other_inbox)}, "mission.work.create"),
        ("get", f"/mission/work-items/{other['id']}", None, "mission.work.read"),
        ("post", f"/mission/work-items/{other['id']}/assignment", {"assignee_subject_id": "operator:two"}, "mission.work.assign"),
        ("post", f"/mission/work-items/{other['id']}/assignment", {"assignee_subject_id": None}, "mission.work.assign"),
        ("post", f"/mission/work-items/{other['id']}/status", {"status": "waiting"}, "mission.work.status.change"),
        ("post", f"/mission/work-items/{other['id']}/priority", {"priority": "high"}, "mission.work.priority.change"),
    )
    for method, url, payload, authority in operations:
        response = getattr(client, method)(url, json=payload, headers=_headers(authority=authority)) if payload is not None else getattr(client, method)(url, headers=_headers(authority=authority))
        assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _detail(own["id"])["organization_id"] if "organization_id" in own else True


def test_list_filters_and_tenant_scoped_and_semantics() -> None:
    first = _new_item(subject="First")
    second = _new_item(subject="Second")
    third = _new_item(subject="Third")
    _new_item(organization_id=OTHER_ORGANIZATION_ID, subject="Other")
    assert _assignment(first["id"], "operator:one").status_code == 200
    assert _status(first["id"], "in_progress").status_code == 200
    assert _priority(first["id"], "urgent").status_code == 200
    assert _priority(second["id"], "high").status_code == 200
    assert _status(third["id"], "waiting").status_code == 200
    items = {item["id"]: item for item in client.get("/mission/work-items", headers=_headers(authority="mission.work.read")).json()["items"]}
    first_item, second_item, third_item = items[first["id"]], items[second["id"]], items[third["id"]]
    cases = (
        (f"status={first_item['status']}", {first["id"]}),
        (f"priority={second_item['priority']}", {second["id"]}),
        ("assignee_subject_id=operator%3Aone", {first["id"]}),
        (f"inbox_item_id={first_item['inbox_item_id']}", {first["id"]}),
        (f"source_type={first_item['source_type']}", {first["id"], second["id"], third["id"]}),
        (f"source_id={second_item['source_id']}", {second["id"]}),
        (f"status={first_item['status']}&priority={first_item['priority']}&assignee_subject_id=operator%3Aone", {first["id"]}),
    )
    for query, expected_ids in cases:
        response = client.get(f"/mission/work-items?{query}", headers=_headers(authority="mission.work.read"))
        assert response.status_code == 200, response.text
        assert {item["id"] for item in response.json()["items"]} == expected_ids
        assert response.json()["total"] == len(expected_ids)
    no_match = client.get("/mission/work-items?assignee_subject_id=missing", headers=_headers(authority="mission.work.read")).json()
    assert no_match["items"] == [] and no_match["total"] == 0
    assert third_item["assignee_subject_id"] is None
    unfiltered = client.get("/mission/work-items", headers=_headers(authority="mission.work.read")).json()
    assert unfiltered["total"] == 3


def test_list_sorting_pagination_and_stable_tie_breaker() -> None:
    items = [_new_item(subject=f"Sort {number}") for number in range(4)]
    with app.state.yarvis.persistence.create_session() as session:
        tied_at = datetime.now(timezone.utc) - timedelta(days=1)
        for item in items:
            persisted = session.get(MissionWorkItem, UUID(item["id"]))
            assert persisted is not None
            persisted.updated_at = tied_at
            persisted.created_at = tied_at
        session.commit()
    default = client.get("/mission/work-items", headers=_headers(authority="mission.work.read")).json()
    assert default["limit"] == 50 and default["offset"] == 0
    expected = sorted((item["id"] for item in items), reverse=True)
    assert [item["id"] for item in default["items"]] == expected
    for sort in ("updated_at", "created_at", "priority", "status"):
        response = client.get(f"/mission/work-items?sort={sort}&limit=100", headers=_headers(authority="mission.work.read"))
        assert response.status_code == 200 and response.json()["limit"] == 100
    for query in ("limit=101", "limit=-1", "offset=-1"):
        response = client.get(f"/mission/work-items?{query}", headers=_headers(authority="mission.work.read"))
        assert response.status_code == 422
    invalid = client.get("/mission/work-items?sort=created_by_subject_id", headers=_headers(authority="mission.work.read"))
    assert invalid.status_code == 400 and invalid.json()["code"] == "VALIDATION_FAILED"
    page_one = client.get("/mission/work-items?limit=2&offset=0", headers=_headers(authority="mission.work.read")).json()["items"]
    page_two = client.get("/mission/work-items?limit=2&offset=2", headers=_headers(authority="mission.work.read")).json()["items"]
    assert {item["id"] for item in page_one}.isdisjoint({item["id"] for item in page_two})


def test_priority_mutations_no_ops_validation_and_event_payload() -> None:
    item_id = _new_item()["id"]
    for priority in ("low", "normal", "high", "urgent"):
        before = _detail(item_id)
        events = _event_count(item_id, "mission.work_item_priority_changed")
        response = _priority(item_id, priority)
        assert response.status_code == 200
        changed = response.json()
        if priority == before["priority"]:
            assert changed["version"] == before["version"]
            assert _event_count(item_id, "mission.work_item_priority_changed") == events
        else:
            assert changed["version"] == before["version"] + 1
            assert _event_count(item_id, "mission.work_item_priority_changed") == events + 1
            assert _latest_event(item_id, "mission.work_item_priority_changed").payload == {
                "work_item_id": item_id,
                "previous_priority": before["priority"],
                "priority": priority,
                "version": changed["version"],
            }
    before_no_op = _detail(item_id)
    no_op_events = _event_count(item_id, "mission.work_item_priority_changed")
    same = _priority(item_id, "urgent").json()
    assert same["version"] == before_no_op["version"] and same["updated_at"] == before_no_op["updated_at"]
    assert _event_count(item_id, "mission.work_item_priority_changed") == no_op_events
    before = _detail(item_id)
    events = _event_count(item_id)
    invalid = _priority(item_id, "invalid")
    assert invalid.status_code == 409 and invalid.json()["code"] == "CONFLICT"
    assert _detail(item_id) == before and _event_count(item_id) == events


def test_create_snapshots_governed_fields_and_duplicate_is_atomic() -> None:
    inbox_id = _inbox(subject="Snapshot")
    response = _create(inbox_id)
    assert response.status_code == 201
    item = response.json()
    assert item["status"] == "open" and item["version"] == 1
    assert item["title"] == "Snapshot" and item["summary"] is None
    assert item["source_type"] == "deterministic_intake" and item["source_id"]
    assert item["priority"] == "normal" and item["created_by_subject_id"] == "operator:mission-work"
    assert "private" not in response.text and "headers" not in response.text
    event = _latest_event(item["id"], "mission.work_item_created")
    assert event.payload == {
        "work_item_id": item["id"], "inbox_item_id": item["inbox_item_id"], "source_type": "deterministic_intake",
        "source_id": item["source_id"], "status": "open", "priority": "normal",
    }
    duplicate = _create(inbox_id)
    assert duplicate.status_code == 409 and duplicate.json()["code"] == "CONFLICT"
    assert _event_count(item["id"]) == 1
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(MissionWorkItem)) == 1


def test_work_queue_survives_inbox_rebuild_without_duplicate_creation() -> None:
    item = _new_item(subject="Rebuild survival")
    original = _detail(item["id"])
    app.state.yarvis.mission_inbox_projection_service.rebuild_projection()
    preserved = _detail(item["id"])
    assert preserved == original
    inbox = client.get("/mission/inbox", headers=_headers(authority="mission.inbox.read")).json()["items"]
    assert any(
        entry["source_type"] == original["source_type"]
        and entry["source_id"] == original["source_id"]
        for entry in inbox
    )
    rebuilt_inbox = next(
        entry
        for entry in inbox
        if entry["source_type"] == original["source_type"] and entry["source_id"] == original["source_id"]
    )
    assert rebuilt_inbox["id"] != original["inbox_item_id"]
    duplicate = _create(UUID(rebuilt_inbox["id"]))
    assert duplicate.status_code == 409 and duplicate.json()["code"] == "CONFLICT"
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(MissionWorkItem)) == 1
        assert session.scalar(
            select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type == "mission.work_item_created")
        ) == 1

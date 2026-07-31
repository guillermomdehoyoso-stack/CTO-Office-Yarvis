from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.operational_task import OperationalTaskEvent
from yarvis_api.models.organization import Organization


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(authority: str, organization_id: UUID = ORGANIZATION_ID, *, include_authority: bool = True) -> dict[str, str]:
    headers = {
        "x-yarvis-actor": "operator:task",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }
    if include_authority:
        headers["x-yarvis-authority"] = authority
    return headers


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((
            Organization(id=ORGANIZATION_ID, legal_name="Tasks", display_name="Tasks"),
            Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other Tasks", display_name="Other Tasks"),
        ))
        session.commit()


def _work(organization_id: UUID = ORGANIZATION_ID) -> UUID:
    work_id = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(MissionWorkItem(id=work_id, organization_id=organization_id, inbox_item_id=uuid4(), source_type="test", source_id=uuid4(), title="Task work", summary=None, created_by_subject_id="operator:task"))
        session.commit()
    return work_id


def _create(work_id: UUID, *, key: str | None = None, title: str = "Task", organization_id: UUID = ORGANIZATION_ID, authority: str = "task.create"):
    return client.post("/mission/tasks", json={"mission_work_item_id": str(work_id), "title": title, "idempotency_key": key or uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority, organization_id))


def _counts(task_id: UUID, work_id: UUID) -> tuple[int, int, int]:
    with app.state.yarvis.persistence.create_session() as session:
        return (
            session.scalar(select(func.count()).select_from(OperationalTaskEvent).where(OperationalTaskEvent.task_id == task_id)),
            session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == task_id)),
            session.scalar(select(func.count()).select_from(MissionWorkEvent).where(MissionWorkEvent.work_item_id == work_id)),
        )


def test_all_task_command_authorities_are_exact_and_missing_context_is_denied() -> None:
    work_id = _work()
    created = _create(work_id).json()
    calls = (
        ("task.create", lambda authority: _create(work_id, authority=authority)),
        ("task.update", lambda authority: client.put(f"/mission/tasks/{created['id']}", json={"title": "Updated", "priority": "normal", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
        ("task.assign", lambda authority: client.post(f"/mission/tasks/{created['id']}/assignment", json={"assignee_subject_id": "operator:two", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
        ("task.transition", lambda authority: client.post(f"/mission/tasks/{created['id']}/transition", json={"status": "ready", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
        ("task.complete", lambda authority: client.post(f"/mission/tasks/{created['id']}/complete", json={"completion_note": "done", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
        ("task.cancel", lambda authority: client.post(f"/mission/tasks/{created['id']}/cancel", json={"reason": "stop", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
        ("task.dependency.manage", lambda authority: client.post(f"/mission/tasks/{created['id']}/dependencies", json={"predecessor_task_id": str(uuid4()), "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers(authority))),
    )
    for expected, call in calls:
        assert call("wrong.authority").status_code == 403
        assert call(expected).status_code != 403
    missing = client.post("/mission/tasks", json={"mission_work_item_id": str(work_id), "title": "No authority", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers("task.create", include_authority=False))
    assert missing.status_code == 403


def test_create_replay_conflict_and_organization_scope() -> None:
    work_id, other_work_id, key = _work(), _work(OTHER_ORGANIZATION_ID), uuid4().hex
    first = _create(work_id, key=key)
    replay = _create(work_id, key=key)
    conflict = _create(work_id, key=key, title="Different")
    other = _create(other_work_id, key=key, organization_id=OTHER_ORGANIZATION_ID)
    assert first.status_code == replay.status_code == other.status_code == 201
    assert first.json()["id"] == replay.json()["id"] and first.json()["id"] != other.json()["id"]
    assert conflict.status_code == 409


def test_mutation_and_dependency_replays_do_not_duplicate_events_or_versions() -> None:
    work_id = _work()
    task = _create(work_id).json()
    predecessor = _create(work_id, title="Predecessor").json()
    task_id, predecessor_id = UUID(task["id"]), UUID(predecessor["id"])

    operations = (
        ("put", f"/mission/tasks/{task_id}", {"title": "Updated", "priority": "normal", "expected_version": 1}, "task.update"),
        ("post", f"/mission/tasks/{task_id}/assignment", {"assignee_subject_id": "operator:two", "expected_version": 2}, "task.assign"),
        ("post", f"/mission/tasks/{task_id}/transition", {"status": "ready", "expected_version": 3}, "task.transition"),
        ("post", f"/mission/tasks/{task_id}/transition", {"status": "in_progress", "expected_version": 4}, "task.transition"),
        ("post", f"/mission/tasks/{task_id}/complete", {"completion_note": "done", "expected_version": 5}, "task.complete"),
    )
    for method, path, payload, authority in operations:
        key = uuid4().hex
        request = {**payload, "idempotency_key": key, "correlation_id": str(uuid4())}
        first = getattr(client, method)(path, json=request, headers=_headers(authority))
        before = _counts(task_id, work_id)
        stale_replay = getattr(client, method)(path, json=request, headers=_headers(authority))
        after = _counts(task_id, work_id)
        assert first.status_code == stale_replay.status_code == 200
        assert first.json()["id"] == stale_replay.json()["id"]
        assert before == after

    cancelled = _create(work_id, title="Cancelled").json()
    cancel_key = uuid4().hex
    cancel = {"reason": "stop", "expected_version": 1, "idempotency_key": cancel_key, "correlation_id": str(uuid4())}
    assert client.post(f"/mission/tasks/{cancelled['id']}/cancel", json=cancel, headers=_headers("task.cancel")).status_code == 200
    assert client.post(f"/mission/tasks/{cancelled['id']}/cancel", json=cancel, headers=_headers("task.cancel")).status_code == 200

    add_key = uuid4().hex
    add = {"predecessor_task_id": str(predecessor_id), "idempotency_key": add_key, "correlation_id": str(uuid4())}
    assert client.post(f"/mission/tasks/{task_id}/dependencies", json=add, headers=_headers("task.dependency.manage")).status_code == 204
    before = _counts(task_id, work_id)
    assert client.post(f"/mission/tasks/{task_id}/dependencies", json=add, headers=_headers("task.dependency.manage")).status_code == 204
    assert _counts(task_id, work_id) == before
    remove_key = uuid4().hex
    remove = client.delete(f"/mission/tasks/{task_id}/dependencies/{predecessor_id}?idempotency_key={remove_key}", headers=_headers("task.dependency.manage"))
    assert remove.status_code == 204
    before = _counts(task_id, work_id)
    assert client.delete(f"/mission/tasks/{task_id}/dependencies/{predecessor_id}?idempotency_key={remove_key}", headers=_headers("task.dependency.manage")).status_code == 204
    assert _counts(task_id, work_id) == before


def test_cross_organization_task_is_concealed_and_migration_constraints_exist() -> None:
    other_work_id = _work(OTHER_ORGANIZATION_ID)
    task = _create(other_work_id, organization_id=OTHER_ORGANIZATION_ID).json()
    hidden = client.get(f"/mission/tasks/{task['id']}", headers=_headers("task.create"))
    assert hidden.status_code == 404
    with app.state.yarvis.persistence.create_session() as session:
        constraints = {item["name"] for item in inspect(session.bind).get_unique_constraints("operational_tasks")}
        event_constraints = {item["name"] for item in inspect(session.bind).get_unique_constraints("operational_task_events")}
    assert "uq_operational_tasks_create_idempotency" in constraints
    assert "uq_operational_task_events_idempotency" in event_constraints
    assert ScriptDirectory.from_config(Config("alembic.ini")).get_heads() == ["20260730_20"]

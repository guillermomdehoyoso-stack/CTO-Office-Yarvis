from datetime import datetime, timezone
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
from yarvis_api.models.operational_task import OperationalTask, OperationalTaskEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.persistence import UnitOfWork
from yarvis_api.services.operational_task import TaskMissionWorkTimelineProjector


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


_SUBJECTS = {
    "task.create": "planner", "task.update": "planner", "task.assign": "assigner",
    "task.transition": "lifecycle", "task.complete": "lifecycle", "task.cancel": "lifecycle",
    "task.dependency.manage": "dependency",
}


def _headers(authority: str, organization_id: UUID = ORGANIZATION_ID, *, include_authority: bool = True, subject: str | None = None, **forged_headers: str) -> dict[str, str]:
    subject = subject or _SUBJECTS.get(authority, "unmapped")
    if organization_id == OTHER_ORGANIZATION_ID:
        subject += "-other"
    headers = {
        "x-yarvis-subject": f"operator:task:{subject}",
        "x-yarvis-auth-token": "deterministic-inbound-intake",
        **forged_headers,
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
        for organization_id, subject, role in (
            (ORGANIZATION_ID, "operator:task:planner", "task_planner"),
            (ORGANIZATION_ID, "operator:task:assigner", "task_assigner"),
            (ORGANIZATION_ID, "operator:task:lifecycle", "task_lifecycle_operator"),
            (ORGANIZATION_ID, "operator:task:dependency", "task_dependency_manager"),
            (ORGANIZATION_ID, "operator:task:foreign", "economics_viewer"),
            (OTHER_ORGANIZATION_ID, "operator:task:planner-other", "task_planner"),
        ):
            principal = Principal(external_subject=subject, status="active")
            session.add(principal)
            session.flush()
            session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role=role))
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
    no_header = client.post("/mission/tasks", json={"mission_work_item_id": str(work_id), "title": "No authority header", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}, headers=_headers("task.create", include_authority=False))
    assert no_header.status_code == 201


def test_create_replay_conflict_and_organization_scope() -> None:
    work_id, other_work_id, key = _work(), _work(OTHER_ORGANIZATION_ID), uuid4().hex
    first = _create(work_id, key=key)
    replay = _create(work_id, key=key)
    conflict = _create(work_id, key=key, title="Different")
    other = _create(other_work_id, key=key, organization_id=OTHER_ORGANIZATION_ID)
    assert first.status_code == replay.status_code == other.status_code == 201
    assert first.json()["id"] == replay.json()["id"] and first.json()["id"] != other.json()["id"]
    assert conflict.status_code == 409


def test_task_authority_is_persisted_and_revocation_precedes_replay() -> None:
    work_id = _work()
    key = "revoked-task-replay"
    created = _create(work_id, key=key)
    assert created.status_code == 201
    forged_assignment = client.post(
        f"/mission/tasks/{created.json()['id']}/assignment",
        json={"assignee_subject_id": "operator:two", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers("task.create", **{"x-yarvis-authority": "task.assign"}),
    )
    assert forged_assignment.status_code == 403
    foreign_role = client.post(
        "/mission/tasks", json={"mission_work_item_id": str(work_id), "title": "Foreign role", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers("task.create", subject="foreign", **{"x-yarvis-authority": "task.create"}),
    )
    assert foreign_role.status_code == 403
    forged_organization = client.post(
        "/mission/tasks", json={"mission_work_item_id": str(work_id), "title": "Header organization", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers("task.create", **{"x-yarvis-organization": str(OTHER_ORGANIZATION_ID)}),
    )
    assert forged_organization.status_code == 201
    forged_token = client.post(
        "/mission/tasks", json={"mission_work_item_id": str(work_id), "title": "Forged token", "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())},
        headers=_headers("task.create", **{"x-yarvis-auth-token": "forged"}),
    )
    assert forged_token.status_code == 403
    with app.state.yarvis.persistence.create_session() as session:
        membership = session.scalar(select(PrincipalMembership).join(Principal).where(Principal.external_subject == "operator:task:planner"))
        assert membership is not None
        membership.status = "revoked"
        membership.revoked_at = datetime.now(timezone.utc)
        session.commit()
    denied_replay = _create(work_id, key=key)
    assert denied_replay.status_code == 403


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


def test_projection_runs_once_after_each_commit_and_never_for_replays(monkeypatch) -> None:
    calls: list[UUID] = []
    original_project = TaskMissionWorkTimelineProjector.project_task

    def project_once(projector: TaskMissionWorkTimelineProjector, task_id: UUID) -> None:
        calls.append(task_id)
        original_project(projector, task_id)

    monkeypatch.setattr(TaskMissionWorkTimelineProjector, "project_task", project_once)
    work_id = _work()
    task = _create(work_id).json()
    predecessor = _create(work_id, title="Predecessor").json()
    task_id, predecessor_id = UUID(task["id"]), UUID(predecessor["id"])
    create_calls = len(calls)
    assert _create(work_id, key="replayed-create").status_code == 201
    # The distinct key above is a normal create; exact replays below add no calls.
    create_key = uuid4().hex
    created = _create(work_id, key=create_key, title="Replay target").json()
    before_replay = len(calls)
    assert _create(work_id, key=create_key, title="Replay target").status_code == 201
    assert len(calls) == before_replay

    operations = (
        ("put", f"/mission/tasks/{task_id}", {"title": "Updated", "priority": "normal", "expected_version": 1}, "task.update"),
        ("post", f"/mission/tasks/{task_id}/assignment", {"assignee_subject_id": "operator:two", "expected_version": 2}, "task.assign"),
        ("post", f"/mission/tasks/{task_id}/transition", {"status": "ready", "expected_version": 3}, "task.transition"),
        ("post", f"/mission/tasks/{task_id}/transition", {"status": "in_progress", "expected_version": 4}, "task.transition"),
        ("post", f"/mission/tasks/{task_id}/complete", {"completion_note": "done", "expected_version": 5}, "task.complete"),
    )
    for method, path, payload, authority in operations:
        request = {**payload, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}
        assert getattr(client, method)(path, json=request, headers=_headers(authority)).status_code == 200
        before_replay = len(calls)
        assert getattr(client, method)(path, json=request, headers=_headers(authority)).status_code == 200
        assert len(calls) == before_replay

    cancelled = _create(work_id, title="Cancelled").json()
    cancel = {"reason": "stop", "expected_version": 1, "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}
    assert client.post(f"/mission/tasks/{cancelled['id']}/cancel", json=cancel, headers=_headers("task.cancel")).status_code == 200
    before_replay = len(calls)
    assert client.post(f"/mission/tasks/{cancelled['id']}/cancel", json=cancel, headers=_headers("task.cancel")).status_code == 200
    assert len(calls) == before_replay

    add = {"predecessor_task_id": str(predecessor_id), "idempotency_key": uuid4().hex, "correlation_id": str(uuid4())}
    assert client.post(f"/mission/tasks/{task_id}/dependencies", json=add, headers=_headers("task.dependency.manage")).status_code == 204
    before_replay = len(calls)
    assert client.post(f"/mission/tasks/{task_id}/dependencies", json=add, headers=_headers("task.dependency.manage")).status_code == 204
    assert len(calls) == before_replay
    remove_key = uuid4().hex
    assert client.delete(f"/mission/tasks/{task_id}/dependencies/{predecessor_id}?idempotency_key={remove_key}", headers=_headers("task.dependency.manage")).status_code == 204
    before_replay = len(calls)
    assert client.delete(f"/mission/tasks/{task_id}/dependencies/{predecessor_id}?idempotency_key={remove_key}", headers=_headers("task.dependency.manage")).status_code == 204
    assert len(calls) == before_replay
    assert len(calls) > create_calls


def test_rollback_does_not_project(monkeypatch) -> None:
    calls: list[UUID] = []
    monkeypatch.setattr(TaskMissionWorkTimelineProjector, "project_task", lambda _projector, task_id: calls.append(task_id))

    def fail_commit(*_args, **_kwargs) -> None:
        raise RuntimeError("forced task commit failure")

    monkeypatch.setattr(UnitOfWork, "commit", fail_commit)
    work_id = _work()
    key = uuid4().hex
    with pytest.raises(RuntimeError, match="forced task commit failure"):
        _create(work_id, key=key)
    assert calls == []
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(OperationalTask).where(OperationalTask.create_idempotency_key == key)) == 0
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type == "operational_task.created")) == 0
        assert session.scalar(select(func.count()).select_from(MissionWorkEvent).where(MissionWorkEvent.work_item_id == work_id)) == 0


def test_projector_failure_surfaces_after_task_commit_without_partial_timeline(monkeypatch) -> None:
    work_id = _work()
    key = uuid4().hex
    original_commit = UnitOfWork.commit
    commit_count = 0

    def fail_projector_commit(unit_of_work: UnitOfWork) -> None:
        nonlocal commit_count
        commit_count += 1
        if commit_count == 2:
            raise RuntimeError("forced timeline projection failure")
        original_commit(unit_of_work)

    monkeypatch.setattr(UnitOfWork, "commit", fail_projector_commit)
    with pytest.raises(RuntimeError, match="forced timeline projection failure"):
        _create(work_id, key=key)
    with app.state.yarvis.persistence.create_session() as session:
        task = session.scalar(select(OperationalTask).where(OperationalTask.create_idempotency_key == key))
        assert task is not None
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == task.id)) == 1
        assert session.scalar(select(func.count()).select_from(MissionWorkEvent).where(MissionWorkEvent.work_item_id == work_id)) == 0


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
    script = ScriptDirectory.from_config(Config("alembic.ini"))
    assert script.get_heads() == [script.get_current_head()]

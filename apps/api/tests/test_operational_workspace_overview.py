from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from yarvis_api.clock import utc_now
from yarvis_api.main import app
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.mission_inbox import MissionInboxItem
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.operational_context import Project, Site
from yarvis_api.models.operational_task import OperationalTask, TaskDependency
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceWorkLink, ProcessStage
from yarvis_api.models.domain_event import DomainEvent
from sqlalchemy import event, func, select


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.read") -> dict[str, str]:
    subject = "workspace-overview:viewer" + ("-other" if organization_id == OTHER_ORGANIZATION_ID else "")
    return {"x-yarvis-subject": subject, "x-yarvis-actor": "forged-workspace-actor", "x-yarvis-organization": str(organization_id), "x-yarvis-authority": authority, "x-yarvis-auth-token": "deterministic-inbound-intake"}


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((Organization(id=ORGANIZATION_ID, legal_name="Workspace", display_name="Workspace"), Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other Workspace", display_name="Other Workspace")))
        session.flush()
        for organization_id, subject in ((ORGANIZATION_ID, "workspace-overview:viewer"), (OTHER_ORGANIZATION_ID, "workspace-overview:viewer-other")):
            principal = Principal(external_subject=subject, status="active")
            session.add(principal); session.flush(); session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role="mission_work_viewer"))
        session.commit()


def _work(*, organization_id: UUID = ORGANIZATION_ID, site_id: UUID | None = None, project_id: UUID | None = None, title: str = "Task", status: str = "planned", due_at=None, assignee: str | None = None, priority: str = "normal", task_id: UUID | None = None, updated_at: datetime | None = None, event_id: UUID | None = None, event_at: datetime | None = None) -> tuple[UUID, UUID]:
    now = utc_now()
    intake_id, inbox_id, work_id, task_id = uuid4(), uuid4(), uuid4(), task_id or uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(IntakeItem(id=intake_id, organization_id=organization_id, source_type="other", content_type="text/plain", title=title, text_content=title, idempotency_key=uuid4().hex, intake_mode="deterministic", received_at=now))
        session.add(MissionInboxItem(id=inbox_id, organization_id=organization_id, source_type="test", source_id=uuid4(), intake_item_id=intake_id, site_id=site_id, project_id=project_id, title=title, status="open", priority="normal", received_at=now, last_activity_at=now))
        session.add(MissionWorkItem(id=work_id, organization_id=organization_id, inbox_item_id=inbox_id, source_type="test", source_id=uuid4(), title=title, summary=None, created_by_subject_id="operator:workspace"))
        session.add(OperationalTask(id=task_id, organization_id=organization_id, mission_work_item_id=work_id, title=title, status=status, priority=priority, due_at=due_at, assignee_subject_id=assignee, updated_at=updated_at or now, cancellation_reason="test cancellation" if status == "cancelled" else None, create_idempotency_key=uuid4().hex, create_request_fingerprint="f" * 64))
        session.add(MissionWorkEvent(id=event_id or uuid4(), organization_id=organization_id, work_item_id=work_id, event_type="task.created", actor_subject_id="operator:workspace", payload_json={}, sequence_number=1, occurred_at=event_at or now))
        session.commit()
    return work_id, task_id


def _process(*, work_id: UUID | None = None, lifecycle: str = "active", instance_id: UUID | None = None, updated_at: datetime | None = None) -> UUID:
    definition_id, stage_id, instance_id = uuid4(), uuid4(), instance_id or uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(ProcessDefinition(id=definition_id, organization_id=ORGANIZATION_ID, name=f"Process {definition_id}", version=1, lifecycle="published"))
        session.flush()
        session.add(ProcessStage(id=stage_id, organization_id=ORGANIZATION_ID, process_definition_id=definition_id, stage_key="start", name="Start", stage_type="start", display_order=1))
        session.flush()
        session.add(ProcessInstance(id=instance_id, organization_id=ORGANIZATION_ID, process_definition_id=definition_id, process_definition_version=1, current_stage_id=stage_id, lifecycle=lifecycle, updated_at=updated_at or utc_now(), created_by_subject_id="operator:workspace", start_idempotency_key=uuid4().hex, start_request_fingerprint="f" * 64))
        if work_id is not None:
            session.add(ProcessInstanceWorkLink(organization_id=ORGANIZATION_ID, process_instance_id=instance_id, mission_work_item_id=work_id, relationship_type="primary", link_idempotency_key=uuid4().hex, link_request_fingerprint="f" * 64))
        session.commit()
    return instance_id


def test_workspace_is_tenant_scoped_filters_context_and_reports_task_summary() -> None:
    site_id, project_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Site(id=site_id, organization_id=ORGANIZATION_ID, reference="SITE-A"))
        session.flush()
        session.add(Project(id=project_id, organization_id=ORGANIZATION_ID, site_id=site_id, reference="PROJECT-A"))
        session.commit()
    work_id, predecessor_id = _work(site_id=site_id, project_id=project_id, title="Predecessor", status="ready")
    blocked_work_id, blocked_id = _work(site_id=site_id, project_id=project_id, title="Blocked", due_at=utc_now() - timedelta(days=1))
    contextless_work_id, contextless_task_id = _work(title="Other context")
    with app.state.yarvis.persistence.create_session() as session:
        session.add(TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=predecessor_id, successor_task_id=blocked_id))
        session.commit()
    response = client.get(f"/operational-workspace?site_id={site_id}&project_id={project_id}&task_limit=1&activity_limit=1", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["context"]["site_reference"] == "SITE-A"
    assert body["context"]["project_reference"] == "PROJECT-A"
    assert body["summary"] == {"active_task_count": 2, "blocked_task_count": 1, "overdue_task_count": 1, "unassigned_task_count": 2, "active_process_count": 0, "recent_activity_count": 1}
    assert len(body["active_tasks"]) == len(body["recent_activity"]) == 1
    assert body["blocked_tasks"][0]["id"] == str(blocked_id)
    assert body["recent_activity"][0]["work_item_id"] in {str(work_id), str(blocked_work_id)}

    organization_workspace = client.get("/operational-workspace", headers=_headers())
    assert organization_workspace.status_code == 200
    assert str(contextless_task_id) in {item["id"] for item in organization_workspace.json()["active_tasks"]}
    assert str(contextless_work_id) in {item["work_item_id"] for item in organization_workspace.json()["recent_activity"]}


def test_workspace_conceals_foreign_or_invalid_context_and_ignores_forged_authority_headers() -> None:
    foreign_site = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Site(id=foreign_site, organization_id=OTHER_ORGANIZATION_ID, reference="OTHER"))
        session.commit()
    assert client.get("/operational-workspace", headers=_headers(authority="wrong.authority")).status_code == 200
    missing_authority = _headers()
    del missing_authority["x-yarvis-authority"]
    assert client.get("/operational-workspace", headers=missing_authority).status_code == 200
    assert client.get(f"/operational-workspace?site_id={foreign_site}", headers=_headers()).status_code == 404
    assert client.get(f"/operational-workspace?project_id={uuid4()}", headers=_headers()).status_code == 404


def test_workspace_limit_validation_and_terminal_task_exclusion() -> None:
    _work(title="Active")
    _work(title="Completed", status="completed")
    response = client.get("/operational-workspace?task_limit=1&activity_limit=1", headers=_headers())
    assert response.status_code == 200
    assert response.json()["summary"]["active_task_count"] == 1
    assert len(response.json()["active_tasks"]) == len(response.json()["recent_activity"]) == 1
    assert client.get("/operational-workspace?task_limit=0", headers=_headers()).status_code == 422
    assert client.get("/operational-workspace?process_limit=101", headers=_headers()).status_code == 422


def test_empty_workspace_and_read_query_have_no_side_effects() -> None:
    with app.state.yarvis.persistence.create_session() as session:
        before = tuple(session.scalar(select(func.count()).select_from(model)) for model in (DomainEvent, OperationalTask, MissionWorkItem, MissionWorkEvent, ProcessInstance))
    response = client.get("/operational-workspace", headers=_headers())
    assert response.status_code == 200
    assert response.json()["summary"] == {"active_task_count": 0, "blocked_task_count": 0, "overdue_task_count": 0, "unassigned_task_count": 0, "active_process_count": 0, "recent_activity_count": 0}
    assert all(response.json()[field] == [] for field in ("active_tasks", "blocked_tasks", "active_processes", "recent_activity"))
    with app.state.yarvis.persistence.create_session() as session:
        after = tuple(session.scalar(select(func.count()).select_from(model)) for model in (DomainEvent, OperationalTask, MissionWorkItem, MissionWorkEvent, ProcessInstance))
    assert after == before


def test_process_lifecycle_and_contextless_process_scope() -> None:
    site_id, project_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Site(id=site_id, organization_id=ORGANIZATION_ID, reference="S")); session.flush()
        session.add(Project(id=project_id, organization_id=ORGANIZATION_ID, site_id=site_id, reference="P")); session.commit()
    linked_work, _ = _work(site_id=site_id, project_id=project_id)
    linked_active, contextless_active, terminal = _process(work_id=linked_work), _process(), _process(lifecycle="completed")
    organization_ids = {item["id"] for item in client.get("/operational-workspace", headers=_headers()).json()["active_processes"]}
    assert {str(linked_active), str(contextless_active)}.issubset(organization_ids)
    assert str(terminal) not in organization_ids
    filtered_ids = {item["id"] for item in client.get(f"/operational-workspace?site_id={site_id}&project_id={project_id}", headers=_headers()).json()["active_processes"]}
    assert str(linked_active) in filtered_ids and str(contextless_active) not in filtered_ids


@pytest.mark.parametrize("predecessor_status,closed,blocked", [("completed", False, False), ("planned", False, True), ("ready", False, True), ("in_progress", False, True), ("cancelled", False, True), ("planned", True, False)])
def test_blocked_dependency_matrix(predecessor_status: str, closed: bool, blocked: bool) -> None:
    _, predecessor = _work(title="predecessor", status=predecessor_status)
    _, successor = _work(title="successor")
    with app.state.yarvis.persistence.create_session() as session:
        edge = TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=predecessor, successor_task_id=successor)
        if closed:
            edge.closed_at = utc_now()
        session.add(edge); session.commit()
    body = client.get("/operational-workspace", headers=_headers()).json()
    active_ids = {item["id"] for item in body["active_tasks"]}
    blocked_ids = {item["id"] for item in body["blocked_tasks"]}
    assert str(successor) in active_ids
    assert (str(successor) in blocked_ids) is blocked


def test_multiple_predecessors_are_deduplicated_and_closed_edges_are_ignored() -> None:
    _, completed_one = _work(status="completed")
    _, completed_two = _work(status="completed")
    _, blocking_one = _work(status="planned")
    _, blocking_two = _work(status="in_progress")
    _, clear_successor = _work(title="clear")
    _, blocked_successor = _work(title="blocked")
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((
            TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=completed_one, successor_task_id=clear_successor),
            TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=completed_two, successor_task_id=clear_successor),
            TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=blocking_one, successor_task_id=blocked_successor),
            TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=blocking_two, successor_task_id=blocked_successor),
            TaskDependency(organization_id=ORGANIZATION_ID, predecessor_task_id=blocking_one, successor_task_id=clear_successor, closed_at=utc_now()),
        ))
        session.commit()
    body = client.get("/operational-workspace", headers=_headers()).json()
    active_ids = [item["id"] for item in body["active_tasks"]]
    blocked_ids = [item["id"] for item in body["blocked_tasks"]]
    assert active_ids.count(str(clear_successor)) == active_ids.count(str(blocked_successor)) == 1
    assert str(clear_successor) not in blocked_ids
    assert blocked_ids.count(str(blocked_successor)) == 1
    assert body["summary"]["blocked_task_count"] == 1


def test_context_matrix_and_query_statement_upper_bound() -> None:
    site_a, site_b, project_a, project_b, foreign_project = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((Site(id=site_a, organization_id=ORGANIZATION_ID, reference="A"), Site(id=site_b, organization_id=ORGANIZATION_ID, reference="B"), Site(id=uuid4(), organization_id=OTHER_ORGANIZATION_ID, reference="Foreign")))
        session.flush()
        session.add_all((Project(id=project_a, organization_id=ORGANIZATION_ID, site_id=site_a, reference="PA"), Project(id=project_b, organization_id=ORGANIZATION_ID, site_id=site_b, reference="PB"), Project(id=foreign_project, organization_id=OTHER_ORGANIZATION_ID, site_id=session.scalar(select(Site.id).where(Site.organization_id == OTHER_ORGANIZATION_ID)), reference="FP")))
        session.commit()
    _work(site_id=site_a, project_id=project_a)
    contextless_work, _ = _work()
    _process(work_id=contextless_work)
    for query in (f"?site_id={site_a}", f"?project_id={project_a}", f"?site_id={site_a}&project_id={project_a}"):
        assert client.get(f"/operational-workspace{query}", headers=_headers()).status_code == 200
    for query in (f"?site_id={site_a}&project_id={project_b}", f"?project_id={foreign_project}", f"?site_id={uuid4()}", f"?project_id={uuid4()}"):
        assert client.get(f"/operational-workspace{query}", headers=_headers()).status_code == 404
    statements: list[str] = []
    engine = app.state.yarvis.persistence.engine
    def count_statement(*_args) -> None:
        statements.append("sql")

    event.listen(engine, "before_cursor_execute", count_statement)
    try:
        assert client.get("/operational-workspace", headers=_headers()).status_code == 200
    finally:
        event.remove(engine, "before_cursor_execute", count_statement)
    # Six bounded composition queries leave headroom for framework/session work;
    # a per-row query path would exceed this with the populated fixture.
    assert len(statements) <= 8


def test_deterministic_task_process_and_activity_ordering() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, urgent = _work(title="urgent", priority="urgent", due_at=base + timedelta(days=3), task_id=UUID(int=5), updated_at=base, event_at=base - timedelta(seconds=1))
    _, early = _work(title="early", priority="high", due_at=base + timedelta(days=1), task_id=UUID(int=4), updated_at=base, event_at=base - timedelta(seconds=1))
    _, newer = _work(title="newer", priority="high", due_at=base + timedelta(days=2), task_id=UUID(int=3), updated_at=base + timedelta(hours=1), event_id=UUID(int=30), event_at=base + timedelta(hours=2))
    _, tied_low = _work(title="tie", priority="low", due_at=None, task_id=UUID(int=2), updated_at=base, event_id=UUID(int=20), event_at=base)
    _, tied_high = _work(title="tie", priority="low", due_at=None, task_id=UUID(int=9), updated_at=base, event_id=UUID(int=21), event_at=base)
    newest_process = _process(instance_id=UUID(int=31), updated_at=base + timedelta(hours=2))
    tied_low_process = _process(instance_id=UUID(int=32), updated_at=base)
    tied_high_process = _process(instance_id=UUID(int=33), updated_at=base)
    body = client.get("/operational-workspace?task_limit=100&process_limit=100&activity_limit=100", headers=_headers()).json()
    task_ids = [item["id"] for item in body["active_tasks"]]
    assert task_ids[:3] == [str(urgent), str(early), str(newer)]
    assert task_ids[-2:] == [str(tied_low), str(tied_high)]
    process_ids = [item["id"] for item in body["active_processes"]]
    assert process_ids == [str(newest_process), str(tied_low_process), str(tied_high_process)]
    activity_ids = [item["id"] for item in body["recent_activity"]]
    assert activity_ids[:3] == [str(UUID(int=30)), str(UUID(int=21)), str(UUID(int=20))]


@pytest.mark.parametrize("parameter", ("task_limit", "process_limit", "activity_limit"))
def test_complete_limit_matrix_and_independence(parameter: str) -> None:
    for index in range(3):
        work_id, _ = _work(title=f"task-{index}")
        _process(work_id=work_id)
    for value in ("0", "-1", "101", "invalid"):
        response = client.get(f"/operational-workspace?{parameter}={value}", headers=_headers())
        assert response.status_code == 422
        assert "detail" in response.json()
    minimum = client.get(f"/operational-workspace?{parameter}=1", headers=_headers()).json()
    maximum = client.get(f"/operational-workspace?{parameter}=100", headers=_headers()).json()
    assert len(maximum["active_tasks"]) == len(maximum["active_processes"]) == len(maximum["recent_activity"]) == 3
    collection = {"task_limit": "active_tasks", "process_limit": "active_processes", "activity_limit": "recent_activity"}[parameter]
    assert len(minimum[collection]) == 1
    assert minimum["summary"]["recent_activity_count"] == len(minimum["recent_activity"])
    combined = client.get("/operational-workspace?task_limit=1&process_limit=2&activity_limit=3", headers=_headers()).json()
    assert [len(combined[key]) for key in ("active_tasks", "active_processes", "recent_activity")] == [1, 2, 3]

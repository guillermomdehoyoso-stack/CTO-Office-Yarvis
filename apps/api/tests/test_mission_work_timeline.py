from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import DBAPIError

from yarvis_api.main import app
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.organization import Organization


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.read") -> dict[str, str]:
    return {
        "x-yarvis-actor": "operator:mission-timeline",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(id=ORGANIZATION_ID, legal_name="Timeline", display_name="Timeline"),
                Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other Timeline", display_name="Other Timeline"),
            )
        )
        session.commit()


def _inbox(organization_id: UUID = ORGANIZATION_ID) -> UUID:
    now = datetime.now(timezone.utc).isoformat()
    subject = f"Timeline {uuid4().hex}"
    response = client.post(
        "/intake/deterministic",
        json={
            "external_source": "email",
            "external_message_id": uuid4().hex,
            "sender": "timeline@example.com",
            "recipients": ["ops@example.com"],
            "subject": subject,
            "text_body": "timeline evidence",
            "content_type": "message/rfc822",
            "source_timestamp": now,
            "received_timestamp": now,
            "correlation_id": str(uuid4()),
            "idempotency_key": uuid4().hex,
        },
        headers=_headers(organization_id, "inbound.intake"),
    )
    assert response.status_code == 201, response.text
    items = client.get("/mission/inbox", headers=_headers(organization_id, "mission.inbox.read")).json()["items"]
    return UUID(next(item["id"] for item in items if item["title"] == subject))


def _new_item(organization_id: UUID = ORGANIZATION_ID) -> dict:
    response = client.post(
        "/mission/work-items",
        json={"inbox_item_id": str(_inbox(organization_id))},
        headers=_headers(organization_id, "mission.work.create"),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _timeline(work_item_id: str, organization_id: UUID = ORGANIZATION_ID, authority: str = "mission.work.read") -> dict:
    return client.get(f"/mission/work-items/{work_item_id}/timeline", headers=_headers(organization_id, authority))


def test_timeline_records_append_only_events_in_stable_incremental_order() -> None:
    item = _new_item()
    work_item_id = item["id"]
    assert client.post(
        f"/mission/work-items/{work_item_id}/assignment",
        json={"assignee_subject_id": "operator:one"},
        headers=_headers(authority="mission.work.assign"),
    ).status_code == 200
    assert client.post(
        f"/mission/work-items/{work_item_id}/priority",
        json={"priority": "high"},
        headers=_headers(authority="mission.work.priority.change"),
    ).status_code == 200
    assert client.post(
        f"/mission/work-items/{work_item_id}/assignment",
        json={"assignee_subject_id": None},
        headers=_headers(authority="mission.work.assign"),
    ).status_code == 200
    assert client.post(
        f"/mission/work-items/{work_item_id}/assignment",
        json={"assignee_subject_id": "operator:one"},
        headers=_headers(authority="mission.work.assign"),
    ).status_code == 200
    assert client.post(
        f"/mission/work-items/{work_item_id}/status",
        json={"status": "in_progress"},
        headers=_headers(authority="mission.work.status.change"),
    ).status_code == 200
    comment = client.post(
        f"/mission/work-items/{work_item_id}/comments",
        json={"comment": "Verified by the operations team."},
        headers=_headers(authority="mission.work.create"),
    )
    assert comment.status_code == 201, comment.text

    timeline = _timeline(work_item_id)

    assert timeline.status_code == 200, timeline.text
    items = timeline.json()["items"]
    assert [item["sequence_number"] for item in items] == [1, 2, 3, 4, 5, 6, 7]
    assert [item["event_type"] for item in items] == [
        "work_item.created",
        "work_item.assigned",
        "work_item.priority_changed",
        "work_item.unassigned",
        "work_item.assigned",
        "work_item.status_changed",
        "comment.added",
    ]
    assert items[1]["payload"] == {
        "work_item_id": work_item_id,
        "previous_status": "open",
        "status": "assigned",
        "previous_assignee_subject_id": None,
        "assignee_subject_id": "operator:one",
        "version": 2,
    }
    assert items[3]["payload"] == {
        "work_item_id": work_item_id,
        "previous_status": "assigned",
        "status": "open",
        "previous_assignee_subject_id": "operator:one",
        "assignee_subject_id": None,
        "version": 4,
    }
    assert items[-1]["actor_subject_id"] == "operator:mission-timeline"
    assert items[-1]["payload"] == {
        "work_item_id": work_item_id,
        "comment": "Verified by the operations team.",
    }


def test_timeline_is_empty_for_a_preexisting_work_item_without_history() -> None:
    work_item_id = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(
            MissionWorkItem(
                id=work_item_id,
                organization_id=ORGANIZATION_ID,
                inbox_item_id=uuid4(),
                source_type="legacy",
                source_id=uuid4(),
                title="Preexisting work",
                summary=None,
                created_by_subject_id="operator:legacy",
            )
        )
        session.commit()

    timeline = _timeline(str(work_item_id))

    assert timeline.status_code == 200, timeline.text
    assert timeline.json() == {"items": []}


def test_timeline_events_cannot_be_updated_or_deleted() -> None:
    item = _new_item()
    event_id = _timeline(item["id"]).json()["items"][0]["id"]

    with app.state.yarvis.persistence.create_session() as session:
        with pytest.raises(DBAPIError):
            session.execute(update(MissionWorkEvent).where(MissionWorkEvent.id == UUID(event_id)).values(event_type="changed"))
            session.commit()
        session.rollback()
        with pytest.raises(DBAPIError):
            session.execute(delete(MissionWorkEvent).where(MissionWorkEvent.id == UUID(event_id)))
            session.commit()
        session.rollback()

    timeline = _timeline(item["id"])
    assert timeline.status_code == 200
    assert timeline.json()["items"][0]["event_type"] == "work_item.created"


def test_comment_and_timeline_authorities_are_enforced() -> None:
    item = _new_item()
    timeline = _timeline(item["id"], authority="mission.work.create")
    comment = client.post(
        f"/mission/work-items/{item['id']}/comments",
        json={"comment": "Not allowed."},
        headers=_headers(authority="mission.work.read"),
    )

    assert timeline.status_code == 403 and timeline.json()["code"] == "AUTHORIZATION_DENIED"
    assert comment.status_code == 403 and comment.json()["code"] == "AUTHORIZATION_DENIED"


def test_timeline_conceals_other_organization_work_item() -> None:
    other_item = _new_item(OTHER_ORGANIZATION_ID)

    response = _timeline(other_item["id"])

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_comment_is_an_additional_event_and_never_changes_prior_evidence() -> None:
    item = _new_item()
    before = _timeline(item["id"]).json()["items"]
    response = client.post(
        f"/mission/work-items/{item['id']}/comments",
        json={"comment": "Internal note."},
        headers=_headers(authority="mission.work.create"),
    )
    after = _timeline(item["id"]).json()["items"]

    assert response.status_code == 201
    assert after[0] == before[0]
    assert len(after) == len(before) + 1
    assert after[-1]["event_type"] == "comment.added"
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(
            select(func.count()).select_from(MissionWorkEvent).where(MissionWorkEvent.work_item_id == UUID(item["id"]))
        ) == 2

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from yarvis_api.main import app
from yarvis_api.models.mission_inbox import MissionInboxItem, ProjectionCheckpoint
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.operational_context import ConnectorMapping, Project, Site
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.mission_inbox import MISSION_INBOX_PROJECTION, MissionInboxProjectionService


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(*, organization_id: UUID = ORGANIZATION_ID, authority: str = "inbound.intake") -> dict[str, str]:
    subject = {"inbound.intake": "operator:mission-intake", "inbound.context.associate": "operator:mission-context", "mission.inbox.read": "operator:mission-inbox"}.get(authority, "operator:mission-intake")
    if organization_id == OTHER_ORGANIZATION_ID:
        subject += "-other"
    return {
        "x-yarvis-subject": subject,
        "x-yarvis-actor": subject,
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def organizations(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(id=ORGANIZATION_ID, legal_name="Mission Inbox", display_name="Mission Inbox"),
                Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other Mission Inbox", display_name="Other Mission Inbox"),
            )
        )
        session.flush()
        for subject, organization_id, role in (
            ("operator:mission-intake", ORGANIZATION_ID, "inbound_operator"),
            ("operator:mission-context", ORGANIZATION_ID, "inbound_context_operator"),
            ("operator:mission-inbox", ORGANIZATION_ID, "mission_inbox_viewer"),
            ("operator:mission-intake-other", OTHER_ORGANIZATION_ID, "inbound_operator"),
            ("operator:mission-context-other", OTHER_ORGANIZATION_ID, "inbound_context_operator"),
            ("operator:mission-inbox-other", OTHER_ORGANIZATION_ID, "mission_inbox_viewer"),
        ):
            principal = Principal(external_subject=subject, status="active")
            session.add(principal); session.flush()
            session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role=role))
        session.commit()


def _create_intake(*, organization_id: UUID = ORGANIZATION_ID, subject: str = "Inbox subject") -> UUID:
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/intake/deterministic",
        json={
            "external_source": "email",
            "external_message_id": uuid4().hex,
            "sender": "sender@example.com",
            "recipients": ["ops@example.com"],
            "subject": subject,
            "text_body": "must not enter mission inbox",
            "content_type": "message/rfc822",
            "source_timestamp": now,
            "received_timestamp": now,
            "correlation_id": str(uuid4()),
            "idempotency_key": f"inbox-{uuid4().hex}",
        },
        headers=_headers(organization_id=organization_id),
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


def _context(organization_id: UUID = ORGANIZATION_ID) -> tuple[UUID, UUID, UUID]:
    with app.state.yarvis.persistence.create_session() as session:
        site = Site(organization_id=organization_id, reference=f"site-{uuid4().hex}")
        session.add(site)
        session.flush()
        project = Project(organization_id=organization_id, site_id=site.id, reference=f"project-{uuid4().hex}")
        session.add(project)
        session.flush()
        mapping = ConnectorMapping(
            organization_id=organization_id,
            project_id=project.id,
            connector_reference=f"mapping-{uuid4().hex}",
        )
        session.add(mapping)
        session.commit()
        return site.id, project.id, mapping.id


def test_deterministic_intake_projects_one_safe_mission_item() -> None:
    _create_intake(subject="Governed title")
    response = client.get("/mission/inbox", headers=_headers(authority="mission.inbox.read"))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Governed title"
    assert "text_body" not in body["items"][0]
    assert body["items"][0]["summary"] is None
    assert body["items"][0]["connector_mapping_id"] is None
    app.state.yarvis.mission_inbox_projection_service.project_pending_events()
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(MissionInboxItem)) == 1
        assert session.scalar(select(ProjectionCheckpoint).where(ProjectionCheckpoint.projection_name == MISSION_INBOX_PROJECTION))


def test_context_event_enriches_same_item_and_rebuild_is_deterministic() -> None:
    intake_id = _create_intake()
    site_id, project_id, mapping_id = _context()
    response = client.post(
        f"/intake/deterministic/{intake_id}/operational-context",
        json={
            "site_id": str(site_id),
            "project_id": str(project_id),
            "connector_mapping_id": str(mapping_id),
            "idempotency_key": f"context-{uuid4().hex}",
            "correlation_id": str(uuid4()),
        },
        headers=_headers(authority="inbound.context.associate"),
    )
    assert response.status_code == 201
    before = client.get("/mission/inbox", headers=_headers(authority="mission.inbox.read")).json()["items"][0]
    app.state.yarvis.mission_inbox_projection_service.rebuild_projection()
    after = client.get("/mission/inbox", headers=_headers(authority="mission.inbox.read")).json()["items"][0]
    assert (after["site_id"], after["project_id"], after["connector_mapping_id"]) == (
        str(site_id),
        str(project_id),
        str(mapping_id),
    )
    assert after["source_id"] == before["source_id"]


def test_mission_inbox_authorization_filters_pagination_and_concealment() -> None:
    own_id = _create_intake(subject="Own")
    _create_intake(organization_id=OTHER_ORGANIZATION_ID, subject="Other")
    denied = client.get("/mission/inbox", headers=_headers(authority="inbound.read"))
    assert denied.status_code == 403
    listed = client.get("/mission/inbox?source_type=deterministic_intake&limit=1&offset=0", headers=_headers(authority="mission.inbox.read"))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    own_item_id = UUID(listed.json()["items"][0]["id"])
    assert client.get(f"/mission/inbox/{own_item_id}", headers=_headers(authority="mission.inbox.read")).status_code == 200
    with app.state.yarvis.persistence.create_session() as session:
        other_item = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id != own_id))
    concealed = client.get(f"/mission/inbox/{other_item.id}", headers=_headers(authority="mission.inbox.read"))
    assert concealed.status_code == 404
    assert concealed.json()["code"] == "RESOURCE_NOT_FOUND"


def test_projection_failure_rolls_back_checkpoint_and_retries(monkeypatch) -> None:
    intake_id = _create_intake()
    service = app.state.yarvis.mission_inbox_projection_service
    with app.state.yarvis.persistence.create_session() as session:
        checkpoint = session.scalar(select(ProjectionCheckpoint))
        before_sequence = checkpoint.last_event_sequence
        before_title = session.scalar(
            select(MissionInboxItem.title).where(MissionInboxItem.intake_item_id == intake_id)
        )
        session.add(
            DomainEvent(
                event_type="intake.received",
                aggregate_type="intake_item",
                aggregate_id=intake_id,
                organization_id=ORGANIZATION_ID,
                payload={},
            )
        )
        session.commit()
    original = MissionInboxProjectionService._project_event
    def fail_after_item_mutation(projection_service, session, event) -> None:
        original(projection_service, session, event)
        item = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == intake_id))
        assert item is not None
        item.title = "must roll back"
        session.flush()
        raise RuntimeError("projection failure")

    monkeypatch.setattr(MissionInboxProjectionService, "_project_event", fail_after_item_mutation)
    with pytest.raises(RuntimeError, match="projection failure"):
        service.project_pending_events()
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(ProjectionCheckpoint)).last_event_sequence == before_sequence
        assert session.scalar(select(MissionInboxItem.title).where(MissionInboxItem.intake_item_id == intake_id)) == before_title
    monkeypatch.setattr(MissionInboxProjectionService, "_project_event", original)
    assert service.project_pending_events().last_event_sequence > before_sequence
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(MissionInboxItem)) == 1


def test_list_filters_ordering_pagination_and_bounds() -> None:
    first_id = _create_intake(subject="First")
    second_id = _create_intake(subject="Second")
    site_id, project_id, _ = _context()
    with app.state.yarvis.persistence.create_session() as session:
        first = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == first_id))
        second = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == second_id))
        first.status, first.priority, first.site_id, first.project_id = "open", "normal", site_id, project_id
        second.status, second.priority = "closed", "high"
        session.commit()
    headers = _headers(authority="mission.inbox.read")
    filtered = client.get(f"/mission/inbox?status=open&priority=normal&site_id={site_id}&project_id={project_id}", headers=headers)
    assert filtered.status_code == 200 and filtered.json()["total"] == 1
    assert client.get("/mission/inbox?source_type=deterministic_intake", headers=headers).json()["total"] == 2
    assert client.get("/mission/inbox?sort=unknown", headers=headers).status_code == 400
    assert client.get("/mission/inbox?limit=101", headers=headers).status_code == 422
    assert client.get("/mission/inbox?offset=-1", headers=headers).status_code == 422
    page = client.get("/mission/inbox?limit=1&offset=1", headers=headers).json()
    assert page["limit"] == 1 and page["offset"] == 1 and len(page["items"]) == 1


def test_read_model_database_constraints_are_enforced() -> None:
    intake_id = _create_intake()
    with app.state.yarvis.persistence.create_session() as session:
        existing = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == intake_id))
        session.add(
            MissionInboxItem(
                organization_id=ORGANIZATION_ID,
                source_type=existing.source_type,
                source_id=existing.source_id,
                intake_item_id=intake_id,
                title="duplicate",
                summary=None,
                status="open",
                priority="normal",
                received_at=existing.received_at,
                last_activity_at=existing.last_activity_at,
                projected_at=existing.projected_at,
                projection_version=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    with app.state.yarvis.persistence.create_session() as session:
        existing = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == intake_id))
        assert existing is not None
        session.add(
            MissionInboxItem(
                organization_id=ORGANIZATION_ID,
                source_type="invalid_foreign_key",
                source_id=uuid4(),
                intake_item_id=existing.intake_item_id,
                site_id=uuid4(),
                title="invalid foreign key",
                summary=None,
                status="open",
                priority="normal",
                received_at=existing.received_at,
                last_activity_at=existing.last_activity_at,
                projected_at=existing.projected_at,
                projection_version=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    other_intake_id = _create_intake(organization_id=OTHER_ORGANIZATION_ID)
    with app.state.yarvis.persistence.create_session() as session:
        existing = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == intake_id))
        other = session.scalar(select(MissionInboxItem).where(MissionInboxItem.intake_item_id == other_intake_id))
        assert existing is not None and other is not None
        session.add(
            MissionInboxItem(
                organization_id=OTHER_ORGANIZATION_ID,
                source_type=existing.source_type,
                source_id=existing.source_id,
                intake_item_id=other.intake_item_id,
                title="same source in another tenant",
                summary=None,
                status="open",
                priority="normal",
                received_at=other.received_at,
                last_activity_at=other.last_activity_at,
                projected_at=other.projected_at,
                projection_version=1,
            )
        )
        session.commit()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(
            ProjectionCheckpoint(
                projection_name="another_projection",
                organization_id=OTHER_ORGANIZATION_ID,
                last_event_sequence=0,
                projection_version=1,
            )
        )
        session.commit()
        session.add(ProjectionCheckpoint(projection_name="another_projection", last_event_sequence=0, projection_version=1))
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize(
    "headers, expected_status",
    (
        ({}, 403),
        ({key: value for key, value in _headers(authority="mission.inbox.read").items() if key != "x-yarvis-actor"}, 200),
        ({key: value for key, value in _headers(authority="mission.inbox.read").items() if key != "x-yarvis-authority"}, 200),
        (_headers(authority="inbound.read"), 403),
    ),
)
def test_mission_inbox_requires_governed_read_authority(headers: dict[str, str], expected_status: int) -> None:
    response = client.get("/mission/inbox", headers=headers)

    assert response.status_code == expected_status
    if expected_status == 403:
        assert response.json()["code"] == "AUTHORIZATION_DENIED"


def test_detail_has_governed_fields_and_matches_missing_item_concealment() -> None:
    _create_intake(subject="Governed detail")
    headers = _headers(authority="mission.inbox.read")
    item = client.get("/mission/inbox", headers=headers).json()["items"][0]
    detail = client.get(f"/mission/inbox/{item['id']}", headers=headers)
    missing = client.get(f"/mission/inbox/{uuid4()}", headers=headers)

    assert detail.status_code == 200
    assert set(detail.json()) == {
        "id", "source_type", "source_id", "intake_item_id", "site_id", "project_id", "connector_mapping_id",
        "title", "summary", "status", "priority", "received_at", "last_activity_at", "projected_at", "projection_version",
    }
    assert "must not enter mission inbox" not in detail.text
    assert missing.status_code == 404
    assert missing.json()["code"] == "RESOURCE_NOT_FOUND"

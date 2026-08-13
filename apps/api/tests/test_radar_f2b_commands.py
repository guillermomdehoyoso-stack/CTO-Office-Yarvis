from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.api.routes import radar as radar_routes
from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.radar import RadarActivity, RadarCommandReceipt, RadarMerchant, RadarRequest

client = TestClient(app)


def setup():
    with app.state.yarvis.persistence.create_session() as db:
        org, other = Organization(legal_name="F2B", display_name="F2B", status="active"), Organization(legal_name="Other", display_name="Other", status="active")
        operator, viewer, foreign = Principal(external_subject="f2b:operator", status="active"), Principal(external_subject="f2b:viewer", status="active"), Principal(external_subject="f2b:foreign", status="active")
        db.add_all((org, other, operator, viewer, foreign)); db.flush()
        membership = PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="radar_operator")
        db.add_all((membership, PrincipalMembership(principal_id=viewer.id, organization_id=org.id, role="radar_viewer"), PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="radar_operator"))); db.flush()
        organization_id, membership_id = org.id, membership.id
        db.commit()
    headers = lambda subject, key: {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "X-Yarvis-Workspace": "f2b", "Idempotency-Key": key}
    created = client.post("/radar/requests", headers=headers("f2b:operator", "create"), json={"merchant": {"trade_name": "F2B merchant", "products": ["tpv"]}, "free_text": "request", "classification": "alta_tpv"})
    assert created.status_code == 201
    return organization_id, membership_id, created.json(), headers


def counts(org):
    with app.state.yarvis.persistence.create_session() as db:
        return tuple(db.scalar(select(func.count()).select_from(model).where(model.organization_id == org)) for model in (RadarCommandReceipt, RadarActivity, DomainEvent))


@pytest.mark.parametrize("route,payload,event", [
    ("checklist/{item}", {"received": True}, "radar.request_checklist_updated"),
    ("next-action", {"next_action": "call"}, "radar.request_next_action_set"),
    ("notes", {"note": "private operational note"}, "radar.request_note_added"),
])
def test_f2b_commands_replay_conflict_authority_and_events(route, payload, event):
    org, membership_id, request, headers = setup()
    path = route.format(item=request["checklist"][0]["id"])
    url = f"/radar/requests/{request['id']}/{path}"
    missing = client.patch(url, headers={k: v for k, v in headers("f2b:operator", "unused").items() if k != "Idempotency-Key"}, json=payload) if route != "notes" else client.post(url, headers={k: v for k, v in headers("f2b:operator", "unused").items() if k != "Idempotency-Key"}, json=payload)
    assert missing.status_code == 422
    method = client.post if route == "notes" else client.patch
    first, replay = method(url, headers=headers("f2b:operator", "same"), json=payload), method(url, headers=headers("f2b:operator", "same"), json=payload)
    assert first.status_code == replay.status_code == 200 and first.json() == replay.json()
    assert counts(org) == (2, 3, 2)
    different = {**payload, next(iter(payload)): False if route.startswith("checklist") else "different"}
    assert method(url, headers=headers("f2b:operator", "same"), json=different).status_code == 409
    assert counts(org) == (2, 3, 2)
    assert method(url, headers=headers("f2b:viewer", "viewer"), json=payload).status_code == 403
    assert method(url, headers=headers("f2b:foreign", "foreign"), json=payload).status_code == 404
    command_type = {"checklist/{item}": "radar.checklist.update", "next-action": "radar.request.update", "notes": "radar.note.create"}[route]
    with app.state.yarvis.persistence.create_session() as db:
        event_row = db.scalar(select(DomainEvent).where(DomainEvent.event_type == event)); receipt = db.scalar(select(RadarCommandReceipt).where(RadarCommandReceipt.command_type == command_type))
        assert event_row and receipt and event_row.causation_id == receipt.command_id and event_row.correlation_id == receipt.correlation_id
        assert "private operational note" not in str(event_row.payload)
        membership = db.get(PrincipalMembership, membership_id); membership.status = "revoked"
        from yarvis_api.clock import utc_now
        membership.revoked_at = utc_now(); db.commit()
    assert method(url, headers=headers("f2b:operator", "same"), json=payload).status_code == 403


def test_f2b_rollback_and_retry(monkeypatch):
    org, _, request, headers = setup()
    url = f"/radar/requests/{request['id']}/notes"
    original = radar_routes.record_event
    monkeypatch.setattr(radar_routes, "record_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("derived failure")))
    with pytest.raises(RuntimeError, match="derived failure"):
        client.post(url, headers=headers("f2b:operator", "rollback"), json={"note": "retry"})
    assert counts(org) == (1, 2, 1)
    monkeypatch.setattr(radar_routes, "record_event", original)
    assert client.post(url, headers=headers("f2b:operator", "rollback"), json={"note": "retry"}).status_code == 200
    assert counts(org) == (2, 3, 2)

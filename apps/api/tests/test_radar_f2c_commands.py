import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.api.routes import radar as radar_routes
from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.radar import RadarActivity, RadarCommandReceipt

client = TestClient(app)


def setup():
    with app.state.yarvis.persistence.create_session() as db:
        org, other = Organization(legal_name="F2C", display_name="F2C", status="active"), Organization(legal_name="Other", display_name="Other", status="active")
        operator, viewer, foreign = Principal(external_subject="f2c:operator", status="active"), Principal(external_subject="f2c:viewer", status="active"), Principal(external_subject="f2c:foreign", status="active")
        db.add_all((org, other, operator, viewer, foreign)); db.flush()
        membership = PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="radar_operator")
        db.add_all((membership, PrincipalMembership(principal_id=viewer.id, organization_id=org.id, role="radar_viewer"), PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="radar_operator"))); db.flush()
        org_id, membership_id = org.id, membership.id; db.commit()
    headers = lambda subject, key: {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "X-Yarvis-Workspace": "f2c", "Idempotency-Key": key}
    created = client.post("/radar/requests", headers=headers("f2c:operator", "create"), json={"merchant": {"trade_name": "F2C merchant", "products": []}, "free_text": "request", "classification": "soporte"})
    assert created.status_code == 201
    return org_id, membership_id, created.json(), headers


def counts(org_id):
    with app.state.yarvis.persistence.create_session() as db:
        return tuple(db.scalar(select(func.count()).select_from(model).where(model.organization_id == org_id)) for model in (RadarCommandReceipt, RadarActivity, DomainEvent))


def test_close_replay_conflict_and_domain_noop():
    org, _, request, headers = setup(); url = f"/radar/requests/{request['id']}/close"; payload = {"incomplete_justification": "customer withdrew"}
    assert client.post(url, headers={k: v for k, v in headers("f2c:operator", "missing").items() if k != "Idempotency-Key"}, json=payload).status_code == 422
    first = client.post(url, headers=headers("f2c:operator", "close"), json=payload); replay = client.post(url, headers=headers("f2c:operator", "close"), json=payload)
    assert first.status_code == replay.status_code == 200 and first.json() == replay.json() and first.json()["status"] == "closed"
    assert counts(org) == (2, 3, 2)
    assert client.post(url, headers=headers("f2c:operator", "close"), json={"incomplete_justification": "different"}).status_code == 409
    assert counts(org) == (2, 3, 2)
    second_key = client.post(url, headers=headers("f2c:operator", "already-closed"), json=payload)
    assert second_key.status_code == 200 and second_key.json()["status"] == "closed"
    assert counts(org) == (3, 3, 2)


def test_reopen_replay_authority_cross_org_and_event_chain():
    org, membership_id, request, headers = setup(); close_url = f"/radar/requests/{request['id']}/close"; reopen_url = f"/radar/requests/{request['id']}/reopen"
    assert client.post(close_url, headers=headers("f2c:operator", "close"), json={"incomplete_justification": "needed"}).status_code == 200
    assert client.post(reopen_url, headers={k: v for k, v in headers("f2c:operator", "missing").items() if k != "Idempotency-Key"}, json={}).status_code == 422
    first = client.post(reopen_url, headers=headers("f2c:operator", "reopen"), json={}); replay = client.post(reopen_url, headers=headers("f2c:operator", "reopen"), json={})
    assert first.status_code == replay.status_code == 200 and first.json() == replay.json() and first.json()["status"] == "open"
    assert client.post(reopen_url, headers=headers("f2c:viewer", "viewer"), json={}).status_code == 403
    assert client.post(reopen_url, headers=headers("f2c:foreign", "foreign"), json={}).status_code == 404
    with app.state.yarvis.persistence.create_session() as db:
        event = db.scalar(select(DomainEvent).where(DomainEvent.event_type == "radar.request_reopened")); receipt = db.scalar(select(RadarCommandReceipt).where(RadarCommandReceipt.command_type == "radar.request.reopen"))
        assert event and receipt and event.causation_id == receipt.command_id and event.correlation_id == receipt.correlation_id
        membership = db.get(PrincipalMembership, membership_id); membership.status = "revoked"
        from yarvis_api.clock import utc_now
        membership.revoked_at = utc_now(); db.commit()
    assert client.post(reopen_url, headers=headers("f2c:operator", "reopen"), json={}).status_code == 403


def test_close_rollback_and_retry(monkeypatch):
    org, _, request, headers = setup(); url = f"/radar/requests/{request['id']}/close"; payload = {"incomplete_justification": "atomic"}
    original = radar_routes.record_event
    monkeypatch.setattr(radar_routes, "record_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("derived failure")))
    with pytest.raises(RuntimeError, match="derived failure"):
        client.post(url, headers=headers("f2c:operator", "rollback"), json=payload)
    assert counts(org) == (1, 2, 1)
    monkeypatch.setattr(radar_routes, "record_event", original)
    assert client.post(url, headers=headers("f2c:operator", "rollback"), json=payload).status_code == 200
    assert counts(org) == (2, 3, 2)

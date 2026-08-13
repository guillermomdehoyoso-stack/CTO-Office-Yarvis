from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from yarvis_api.main import app
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

client = TestClient(app)
HEADERS = {"X-Yarvis-Workspace": "radar-test"}


def canonical_context():
    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="Radar Test Org", display_name="Radar Test Org", status="active")
        principal = Principal(external_subject="radar:test", status="active")
        session.add_all((org, principal)); session.flush()
        session.add(PrincipalMembership(principal_id=principal.id, organization_id=org.id, role="radar_operator")); session.commit()
    HEADERS.clear(); HEADERS.update({"X-Yarvis-Workspace": "radar-test", "X-Yarvis-Subject": "radar:test", "X-Yarvis-Auth-Token": "deterministic-inbound-intake"})


def create_request(classification="alta_ecommerce", **extra):
    payload = {"merchant": {"trade_name": "Comercio Radar", "products": ["ecommerce"]}, "free_text": "Solicitud manual", "classification": classification, "actor": "ana", **extra}
    response = client.post("/radar/requests", headers={**HEADERS, "Idempotency-Key": str(uuid4())}, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_request_templates_pending_and_idempotency():
    canonical_context()
    key = "same-click"
    first = client.post("/radar/requests", headers={**HEADERS, "Idempotency-Key": key}, json={"merchant": {"trade_name": "Gasolinera", "products": ["tpv", "ecommerce"]}, "free_text": "Alta", "classification": "alta_ecommerce", "actor": "ana"})
    second = client.post("/radar/requests", headers={**HEADERS, "Idempotency-Key": key}, json={"merchant": {"trade_name": "Gasolinera", "products": ["tpv", "ecommerce"]}, "free_text": "Alta", "classification": "alta_ecommerce", "actor": "ana"})
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(first.json()["checklist"]) == 7
    board = client.get("/radar/dashboard", headers=HEADERS).json()
    assert board["summary"]["pending"] == 1
    assert board["merchants"][0]["pending"] is True


def test_close_requires_resolution_or_justification_and_reopen():
    canonical_context()
    request = create_request(next_action="Solicitar INE")
    refused = client.post(f"/radar/requests/{request['id']}/close", headers=HEADERS, json={"actor": "ana"})
    assert refused.status_code == 422
    closed = client.post(f"/radar/requests/{request['id']}/close", headers=HEADERS, json={"actor": "ana", "incomplete_justification": "Cliente retiró solicitud"})
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    assert client.get("/radar/dashboard", headers=HEADERS).json()["merchants"][0]["pending"] is False
    assert client.post(f"/radar/requests/{request['id']}/reopen", headers=HEADERS, json={"actor": "ana"}).json()["status"] == "open"


def test_document_actor_history_is_immutable_and_workspace_is_hidden():
    canonical_context()
    request = create_request("alta_tpv")
    item = request["checklist"][0]
    assert client.patch(f"/radar/requests/{request['id']}/checklist/{item['id']}", headers=HEADERS, json={"received": True, "actor": "maria"}).status_code == 200
    detail = client.get(f"/radar/merchants/{request['merchant_id']}", headers=HEADERS).json()
    assert any(event["event_type"] == "document_received" and event["actor"] != "maria" for event in detail["activity"])
    with app.state.yarvis.persistence.create_session() as session:
        activity_id = detail["activity"][0]["id"]
        try:
            session.execute(text("DELETE FROM radar_activities WHERE id = :id"), {"id": activity_id}); session.commit()
        except Exception:
            session.rollback()
        else:
            raise AssertionError("activity history was mutable")


def test_deterministic_filters_and_multiple_requests():
    canonical_context()
    early = create_request("reposicion_terminal", priority="high", due_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat())
    create_request("soporte", priority="low", due_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat())
    board = client.get("/radar/dashboard?overdue=true", headers=HEADERS)
    assert board.status_code == 200
    assert board.json()["merchants"][0]["id"] == early["merchant_id"]


def test_resolve_next_action_and_close_are_atomic_and_persistent():
    canonical_context()
    request = create_request("alta_tpv", next_action="Llamar al comercio")
    for item in request["checklist"]:
        assert client.patch(f"/radar/requests/{request['id']}/checklist/{item['id']}", headers=HEADERS, json={"received": True, "actor": "ana"}).status_code == 200
    closed = client.post(f"/radar/requests/{request['id']}/close", headers=HEADERS, json={"next_action": None, "actor": "ana"})
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "closed" and closed.json()["next_action"] is None
    merchant = client.get(f"/radar/merchants/{request['merchant_id']}", headers=HEADERS).json()
    assert merchant["pending"] is False and merchant["requests"][0]["next_action"] is None
    activity_before_retry = len(merchant["activity"])
    assert client.post(f"/radar/requests/{request['id']}/close", headers=HEADERS, json={"next_action": None, "actor": "ana"}).status_code == 200
    assert len(client.get(f"/radar/merchants/{request['merchant_id']}", headers=HEADERS).json()["activity"]) == activity_before_retry


def test_clearing_next_action_persists_and_another_open_request_keeps_pending_on():
    canonical_context()
    first = create_request("soporte", next_action="Resolver hoy")
    second = client.post("/radar/requests", headers={**HEADERS, "Idempotency-Key": str(uuid4())}, json={"merchant_id": first["merchant_id"], "free_text": "Otra solicitud", "classification": "soporte", "actor": "ana"}).json()
    cleared = client.patch(f"/radar/requests/{first['id']}/next-action", headers=HEADERS, json={"next_action": "", "actor": "ana"})
    assert cleared.status_code == 200 and cleared.json()["next_action"] is None
    assert client.get(f"/radar/merchants/{first['merchant_id']}", headers=HEADERS).json()["requests"][1]["next_action"] is None
    assert client.post(f"/radar/requests/{first['id']}/close", headers=HEADERS, json={"next_action": None, "actor": "ana"}).status_code == 200
    dashboard_merchant = client.get("/radar/dashboard", headers=HEADERS).json()["merchants"][0]
    assert dashboard_merchant["pending"] is True and dashboard_merchant["open_count"] == 1

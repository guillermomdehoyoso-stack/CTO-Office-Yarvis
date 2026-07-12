from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.database import SessionLocal
from yarvis_api.main import app
from yarvis_api.models.checklist import DocumentType, RequirementFulfillment

client = TestClient(app)


def setup_case():
    types = client.get("/case-types").json()
    cfe = next(item for item in types if item["code"] == "cfe_residential_interconnection")
    org = client.post("/organizations", json={"legal_name": f"Operational {uuid4().hex}"}).json()
    case = client.post("/cases", json={"title": "Operational CFE", "case_type": "cfe", "case_type_id": cfe["id"], "owner_organization_id": org["id"]}).json()
    checklist = client.post(f"/cases/{case['id']}/checklists").json()
    intake = client.post("/intake", json={"source_type": "manual_text", "content_type": "text/plain", "text_content": "Recibo"}).json()
    client.post(f"/intake/{intake['id']}/link-case/{case['id']}")
    return case, checklist, intake


def fulfill(case, checklist, intake, code="cfe_bill"):
    requirement = next(item for item in checklist["requirements"] if item["code"] == code)
    return client.post(f"/case-checklists/{checklist['id']}/requirements/{requirement['id']}/fulfill", json={"intake_item_id": intake["id"]}).json()


def test_manual_review_validity_rejection_and_fallbacks():
    case, checklist, intake = setup_case()
    item = fulfill(case, checklist, intake)
    assert client.post(f"/requirement-fulfillments/{item['id']}/review", json={"confirmed_by": "reviewer"}).json()["status"] == "under_review"
    date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    validated = client.post(f"/requirement-fulfillments/{item['id']}/validate", json={"document_date": date.isoformat(), "reviewed_by": "reviewer"}).json()
    assert validated["valid_until"].startswith("2026-04-01")
    another = fulfill(case, checklist, intake, "client_id")
    assert client.post(f"/requirement-fulfillments/{another['id']}/validate", json={"valid_from": date.isoformat()}).json()["valid_until"] is None
    rejected = fulfill(case, checklist, intake, "power_of_attorney")
    assert client.post(f"/requirement-fulfillments/{rejected['id']}/reject", json={}).status_code == 422
    assert client.post(f"/requirement-fulfillments/{rejected['id']}/reject", json={"rejection_reason": "ilegible"}).json()["rejection_reason"] == "ilegible"


def test_validity_date_sources_persist_and_catalog_changes_do_not_rewrite(monkeypatch):
    from yarvis_api.api.routes import checklists
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(checklists, "utc_now", lambda: fixed)
    case, checklist, intake = setup_case()
    first = fulfill(case, checklist, intake)
    assert client.post(f"/requirement-fulfillments/{first['id']}/validate", json={"valid_from": fixed.isoformat()}).json()["valid_until"].startswith("2026-04-01")
    with SessionLocal() as db:
        persisted = db.get(RequirementFulfillment, first["id"])
        assert persisted.valid_until == fixed + timedelta(days=90)
        document_type = db.scalar(__import__("sqlalchemy").select(DocumentType).where(DocumentType.code == "cfe_bill"))
        document_type.validity_days = 1
        db.commit(); db.refresh(persisted)
        assert persisted.valid_until == fixed + timedelta(days=90)
    second = fulfill(case, checklist, intake, "client_id")
    assert client.post(f"/requirement-fulfillments/{second['id']}/validate", json={}).json()["valid_until"] is None


def test_operational_alerts_idempotency_resolution_suggestions_and_events():
    case, checklist, intake = setup_case()
    first = client.post(f"/cases/{case['id']}/evaluate-operational-state")
    assert first.status_code == 200
    alerts = client.get(f"/cases/{case['id']}/alerts").json()
    missing = next(alert for alert in alerts if alert["alert_type"] == "missing_requirement")
    assert client.post(f"/cases/{case['id']}/evaluate-operational-state").status_code == 200
    assert len([alert for alert in client.get(f"/cases/{case['id']}/alerts").json() if alert["alert_type"] == "missing_requirement" and alert["source_entity_id"] == missing["source_entity_id"]]) == 1
    suggestions = client.get(f"/cases/{case['id']}/next-action-suggestions").json()
    assert suggestions
    suggestion = suggestions[0]
    assert client.post(f"/next-action-suggestions/{suggestion['id']}/accept").json()["status"] == "accepted"
    assert client.post(f"/next-action-suggestions/{suggestion['id']}/dismiss").json()["status"] == "dismissed"
    assert client.post(f"/next-action-suggestions/{suggestion['id']}/complete").json()["status"] == "completed"
    item = fulfill(case, checklist, intake)
    client.post(f"/requirement-fulfillments/{item['id']}/validate", json={"document_date": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()})
    client.post(f"/cases/{case['id']}/evaluate-operational-state")
    types = {alert["alert_type"] for alert in client.get(f"/cases/{case['id']}/alerts").json()}
    assert "expired_requirement" in types
    events = {event["event_type"] for event in client.get(f"/cases/{case['id']}/events").json()}
    assert {"alert.created", "next_action.proposed", "fulfillment.validated", "fulfillment.expired"} <= events

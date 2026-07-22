from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.catalogs import load_catalogs
from yarvis_api.main import app

client = TestClient(app)


def case_type(code="cfe_residential_interconnection"):
    return next(item for item in client.get("/case-types").json() if item["code"] == code)


def case_with_checklist(case_type_code="cfe_residential_interconnection"):
    suffix = uuid4().hex
    organization = client.post("/organizations", json={"legal_name": f"Checklist Org {suffix}"}).json()
    case = client.post("/cases", json={"title": f"CFE {suffix}", "case_type": "cfe", "case_type_id": case_type(case_type_code)["id"], "owner_organization_id": organization["id"]}).json()
    checklist = client.post(f"/cases/{case['id']}/checklists").json()
    return case, checklist


def intake_for(case):
    intake = client.post("/intake", json={"source_type": "manual_text", "content_type": "text/plain", "text_content": "Recibo CFE recibido"}).json()
    assert client.post(f"/intake/{intake['id']}/link-case/{case['id']}").status_code == 200
    return intake


def test_catalogs_are_idempotent_and_listed():
    with app.state.yarvis.persistence.create_session() as session:
        load_catalogs(session); session.commit()
    assert len(client.get("/case-types").json()) == 2
    assert {item["code"] for item in client.get("/document-types").json()} >= {"cfe_bill", "government_id"}


def test_create_confirm_and_reject_classification():
    case, _ = case_with_checklist(); intake = intake_for(case)
    document_type = next(item for item in client.get("/document-types").json() if item["code"] == "cfe_bill")
    proposed = client.post(f"/intake/{intake['id']}/classifications", json={"document_type_id": document_type["id"], "proposed_case_type_id": case_type()["id"], "confidence": 100})
    assert proposed.status_code == 201
    assert client.post(f"/intake-classifications/{proposed.json()['id']}/confirm", json={"confirmed_by": "operator"}).json()["status"] == "confirmed"
    another = client.post(f"/intake/{intake['id']}/classifications", json={}).json()
    assert client.post(f"/intake-classifications/{another['id']}/reject").json()["status"] == "rejected"


def test_checklist_prevents_duplicate_and_fulfillment_paths():
    case, checklist = case_with_checklist("netpay_merchant_onboarding"); intake = intake_for(case)
    assert client.post(f"/cases/{case['id']}/checklists").status_code == 409
    requirement = checklist["requirements"][0]
    assert client.post(f"/case-checklists/{checklist['id']}/requirements/{requirement['id']}/fulfill", json={}).status_code == 422
    received = client.post(f"/case-checklists/{checklist['id']}/requirements/{requirement['id']}/fulfill", json={"intake_item_id": intake["id"]})
    assert received.status_code == 201
    assert client.post(f"/requirement-fulfillments/{received.json()['id']}/validate").json()["status"] == "valid"
    evidence = client.post(f"/cases/{case['id']}/evidence", json={"evidence_type": "photo", "title": "Foto"}).json()
    other = checklist["requirements"][1]
    rejected = client.post(f"/case-checklists/{checklist['id']}/requirements/{other['id']}/fulfill", json={"evidence_id": evidence["id"]}).json()
    assert client.post(f"/requirement-fulfillments/{rejected['id']}/reject").json()["status"] == "rejected"


def test_not_applicable_and_progress_to_completion_and_events():
    case, checklist = case_with_checklist("netpay_merchant_onboarding"); intake = intake_for(case)
    conditional = next(item for item in checklist["requirements"] if not item["required"])
    assert client.post(f"/case-checklists/{checklist['id']}/requirements/{conditional['id']}/not-applicable", json={}).status_code == 422
    assert client.post(f"/case-checklists/{checklist['id']}/requirements/{conditional['id']}/not-applicable", json={"notes": "No aplica"}).status_code == 201
    first = checklist["requirements"][0]
    partial = client.post(f"/case-checklists/{checklist['id']}/requirements/{first['id']}/fulfill", json={"intake_item_id": intake["id"]}).json()
    client.post(f"/requirement-fulfillments/{partial['id']}/validate")
    assert client.get(f"/case-checklists/{checklist['id']}").json()["progress_percent"] > 0
    for requirement in checklist["requirements"]:
        if requirement["required"] and requirement["id"] != first["id"]:
            fulfillment = client.post(f"/case-checklists/{checklist['id']}/requirements/{requirement['id']}/fulfill", json={"intake_item_id": intake["id"]}).json()
            client.post(f"/requirement-fulfillments/{fulfillment['id']}/validate")
    complete = client.get(f"/case-checklists/{checklist['id']}").json()
    assert complete["progress_percent"] == 100.0
    events = [event["event_type"] for event in client.get(f"/cases/{case['id']}/events").json()]
    assert {"checklist.created", "checklist.requirement_received", "checklist.requirement_validated", "checklist.requirement_not_applicable"} <= set(events)

from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.main import app

client = TestClient(app)


def create_case():
    suffix = uuid4().hex
    organization = client.post("/organizations", json={"legal_name": f"Intake Org {suffix}"}).json()
    response = client.post("/cases", json={"title": f"Case {suffix}", "case_type": "cfe", "owner_organization_id": organization["id"]})
    assert response.status_code == 201, response.text
    return organization, response.json()


def create_intake():
    response = client.post("/intake", json={"source_type": "manual_text", "content_type": "text/plain", "text_content": "Cliente solicitó una actualización"})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_manual_text_intake_emits_event():
    intake = create_intake()
    assert intake["intake_number"].startswith("INT-")
    assert client.get(f"/intake/{intake['id']}").status_code == 200


def test_intake_can_reference_organization_and_person():
    suffix = uuid4().hex
    organization = client.post("/organizations", json={"legal_name": f"Reference Org {suffix}"}).json()
    person = client.post("/people", json={"display_name": f"Person {suffix}"}).json()
    response = client.post("/intake", json={"source_type": "manual_text", "content_type": "text/plain", "text_content": "Reference intake", "organization_id": organization["id"], "person_id": person["id"]})
    assert response.status_code == 201, response.text
    assert response.json()["organization_id"] == organization["id"]
    assert response.json()["person_id"] == person["id"]


def test_empty_intake_is_rejected():
    response = client.post("/intake", json={"source_type": "manual_text", "content_type": "text/plain"})
    assert response.status_code == 422


def test_link_intake_to_case_and_reject_duplicate_link():
    _, case = create_case()
    intake = create_intake()
    response = client.post(f"/intake/{intake['id']}/link-case/{case['id']}")
    assert response.status_code == 200, response.text
    assert response.json()["case_id"] == case["id"]
    assert client.post(f"/intake/{intake['id']}/link-case/{case['id']}").status_code == 409


def test_link_rejects_missing_case():
    intake = create_intake()
    assert client.post(f"/intake/{intake['id']}/link-case/{uuid4()}").status_code == 404


def test_create_and_list_evidence_and_events_in_chronological_order():
    _, case = create_case()
    intake = create_intake()
    assert client.post(f"/intake/{intake['id']}/link-case/{case['id']}").status_code == 200
    evidence = client.post(f"/cases/{case['id']}/evidence", json={"intake_item_id": intake["id"], "evidence_type": "message", "title": "Solicitud recibida"})
    assert evidence.status_code == 201, evidence.text
    evidence_list = client.get(f"/cases/{case['id']}/evidence")
    assert evidence_list.status_code == 200
    assert evidence_list.json()[0]["id"] == evidence.json()["id"]
    events = client.get(f"/cases/{case['id']}/events")
    assert events.status_code == 200
    event_types = [event["event_type"] for event in events.json()]
    assert event_types == ["case.created", "intake.linked_to_case", "evidence.created"]
    assert [event["occurred_at"] for event in events.json()] == sorted(event["occurred_at"] for event in events.json())


def test_case_created_and_intake_events_are_recorded():
    _, case = create_case()
    intake = create_intake()
    client.post(f"/intake/{intake['id']}/link-case/{case['id']}")
    event_types = [event["event_type"] for event in client.get(f"/cases/{case['id']}/events").json()]
    assert "case.created" in event_types
    assert "intake.linked_to_case" in event_types


def test_events_have_no_update_or_delete_endpoints():
    _, case = create_case()
    assert client.put(f"/cases/{case['id']}/events").status_code == 405
    assert client.delete(f"/cases/{case['id']}/events").status_code == 405

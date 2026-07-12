from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.main import app

client = TestClient(app)


def create_context():
    suffix = uuid4().hex
    organization = client.post("/organizations", json={"legal_name": f"Conversation Org {suffix}"}).json()
    person = client.post("/people", json={"display_name": f"Person {suffix}"}).json()
    case = client.post(
        "/cases",
        json={
            "title": f"Case {suffix}",
            "case_type": "cfe",
            "owner_organization_id": organization["id"],
            "primary_person_id": person["id"],
        },
    ).json()
    return organization, person, case


def test_create_list_and_message_conversation_creates_intake_item():
    organization, person, case = create_context()
    conversation = client.post(
        "/conversations",
        json={
            "title": "Soporte",
            "organization_id": organization["id"],
            "person_id": person["id"],
            "case_id": case["id"],
        },
    ).json()
    assert conversation["title"] == "Soporte"
    assert client.get("/conversations").status_code == 200

    response = client.post(
        f"/conversations/{conversation['id']}/messages",
        json={"text_content": "Necesito ayuda con la solicitud"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["intake_item_id"] is not None
    assert body["message"]["conversation_id"] == conversation["id"]

    detail = client.get(f"/conversations/{conversation['id']}").json()
    assert detail["messages"][0]["text_content"] == "Necesito ayuda con la solicitud"

    intake = client.get(f"/intake/{body['intake_item_id']}").json()
    assert intake["case_id"] == case["id"]


def test_attachment_is_registered_as_metadata_and_context_can_be_confirmed():
    organization, person, case = create_context()
    conversation = client.post(
        "/conversations",
        json={
            "title": "Adjuntos",
            "organization_id": organization["id"],
            "person_id": person["id"],
            "case_id": case["id"],
        },
    ).json()

    attachment = client.post(
        f"/conversations/{conversation['id']}/attachments",
        json={"original_filename": "invoice.pdf", "description": "Factura", "mime_type": "application/pdf"},
    )
    assert attachment.status_code == 201, attachment.text
    intake_id = attachment.json()["intake_item_id"]

    intake = client.get(f"/intake/{intake_id}").json()
    assert intake["original_filename"] == "invoice.pdf"

    confirmed = client.post(
        f"/intake/{intake_id}/confirm-context",
        json={
            "organization_id": organization["id"],
            "person_id": person["id"],
            "case_id": case["id"],
            "evidence_type": "document",
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"

    evidence = client.get(f"/cases/{case['id']}/evidence").json()
    assert evidence[0]["intake_item_id"] == intake_id

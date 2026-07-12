from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.main import app

client = TestClient(app)


def create_organization():
    suffix = uuid4().hex
    response = client.post("/organizations", json={"legal_name": f"Organization {suffix}", "organization_type": "business"})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_organization_persists_in_postgresql():
    organization = create_organization()
    assert organization["display_name"] == organization["legal_name"]
    assert client.get(f"/organizations/{organization['id']}").json()["id"] == organization["id"]


def test_create_person():
    response = client.post("/people", json={"first_name": "Juan", "last_name": "Manuel", "email": f"juan.{uuid4().hex}@example.com"})
    assert response.status_code == 201, response.text
    assert response.json()["display_name"] == "Juan Manuel"


def test_create_case_linked_to_organization():
    organization = create_organization()
    response = client.post("/cases", json={"title": "Expediente CFE", "case_type": "cfe", "owner_organization_id": organization["id"]})
    assert response.status_code == 201, response.text
    assert response.json()["owner_organization_id"] == organization["id"]
    assert response.json()["case_number"].startswith("CAS-")


def test_create_case_with_primary_person():
    organization = create_organization()
    person = client.post("/people", json={"display_name": "Primary Person"}).json()
    response = client.post("/cases", json={"title": "Alta NetPay", "case_type": "netpay", "owner_organization_id": organization["id"], "primary_person_id": person["id"]})
    assert response.status_code == 201, response.text
    assert response.json()["primary_person_id"] == person["id"]


def test_case_requires_existing_organization():
    response = client.post("/cases", json={"title": "Invalid owner", "case_type": "general", "owner_organization_id": str(uuid4())})
    assert response.status_code == 422


def test_missing_entities_return_404():
    missing_id = uuid4()
    assert client.get(f"/organizations/{missing_id}").status_code == 404
    assert client.get(f"/people/{missing_id}").status_code == 404
    assert client.get(f"/cases/{missing_id}").status_code == 404

from fastapi.testclient import TestClient

from yarvis_api.main import app
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

client = TestClient(app)


def _setup():
    with app.state.yarvis.persistence.create_session() as db:
        org, other = Organization(legal_name="Master Org", display_name="Master Org", status="active"), Organization(legal_name="Other Org", display_name="Other Org", status="active")
        operator, viewer, foreign = Principal(external_subject="master:operator", status="active"), Principal(external_subject="master:viewer", status="active"), Principal(external_subject="master:foreign", status="active")
        db.add_all((org, other, operator, viewer, foreign)); db.flush()
        db.add_all((PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_master_operator"), PrincipalMembership(principal_id=viewer.id, organization_id=org.id, role="netpay_master_viewer"), PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="netpay_master_operator")))
        db.commit()
    def headers(subject, key): return {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "Idempotency-Key": key}
    return headers


def test_master_creates_branch_without_store_then_manages_reference_and_replays():
    headers = _setup()
    created = client.post("/netpay/master/clients", headers=headers("master:operator", "client"), json={"display_name": "Cliente Uno", "primary_email": "uno@example.test"})
    assert created.status_code == 201
    assert client.post("/netpay/master/clients", headers=headers("master:operator", "client"), json={"display_name": "Cliente Uno", "primary_email": "uno@example.test"}).json() == created.json()
    company = client.post(f"/netpay/master/clients/{created.json()['id']}/companies", headers=headers("master:operator", "company"), json={"legal_name": "Empresa Uno", "tax_identifier": "MX-1"})
    assert company.status_code == 201
    branch = client.post(f"/netpay/master/companies/{company.json()['id']}/branches", headers=headers("master:operator", "branch"), json={"commercial_name": "Sucursal Centro", "branch_kind": "physical", "address": "Uno", "locality": "CDMX", "postal_code": "01000"})
    assert branch.status_code == 201 and branch.json()["store_reference"] is None
    store_url = f"/netpay/master/branches/{branch.json()['id']}/store-reference"
    store = client.put(store_url, headers=headers("master:operator", "store"), json={"store_id": "STORE-1", "source_type": "human"})
    assert store.status_code == 201 and store.json()["store_id"] == "STORE-1"
    corrected = client.put(store_url, headers=headers("master:operator", "correct"), json={"store_id": "STORE-2", "source_type": "human", "confirmed": True})
    assert corrected.status_code == 201 and corrected.json()["store_id"] == "STORE-2"
    assert client.get(f"/netpay/master/branches/{branch.json()['id']}", headers=headers("master:viewer", "read")).status_code == 200
    assert client.post("/netpay/master/clients", headers=headers("master:viewer", "denied"), json={"display_name": "No"}).status_code == 403
    assert client.delete(store_url, headers=headers("master:operator", "remove")).status_code == 204


def test_master_conceals_cross_tenant_and_ignores_forged_authority_headers():
    headers = _setup()
    created = client.post("/netpay/master/clients", headers=headers("master:operator", "client"), json={"display_name": "Client"})
    forged = headers("master:viewer", "forged") | {"X-Yarvis-Authority": "netpay.master.manage", "X-Yarvis-Organization": "other"}
    assert client.post("/netpay/master/clients", headers=forged, json={"display_name": "Forged"}).status_code == 403
    assert client.get(f"/netpay/master/branches/{created.json()['id']}", headers=headers("master:foreign", "foreign")).status_code == 404

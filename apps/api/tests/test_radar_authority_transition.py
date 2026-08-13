from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.radar import RadarActivity, RadarMerchant, RadarRequest

client = TestClient(app)


def headers(subject: str, workspace: str = "compatibility-only", **extra: str) -> dict[str, str]:
    return {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "X-Yarvis-Workspace": workspace, **extra}


def context():
    with app.state.yarvis.persistence.create_session() as db:
        org_a, org_b = Organization(legal_name="A", display_name="A", status="active"), Organization(legal_name="B", display_name="B", status="active")
        radar_a, radar_b, governor = Principal(external_subject="radar-a", status="active"), Principal(external_subject="radar-b", status="active"), Principal(external_subject="governor-a", status="active")
        db.add_all((org_a, org_b, radar_a, radar_b, governor)); db.flush()
        db.add_all((PrincipalMembership(principal_id=radar_a.id, organization_id=org_a.id, role="radar_operator"), PrincipalMembership(principal_id=radar_b.id, organization_id=org_b.id, role="radar_operator"), PrincipalMembership(principal_id=governor.id, organization_id=org_a.id, role="foundation_membership_operator")))
        db.commit()
        return org_a.id, org_b.id, radar_a.id, radar_b.id, governor.id


def test_canonical_commands_reads_cross_org_and_revocation_are_effective():
    org_a, org_b, radar_a, _radar_b, governor = context()
    created = client.post("/radar/requests", headers=headers("radar-a", "forged-workspace", **{"Idempotency-Key": "canonical-create", "X-Yarvis-Authority": "admin", "X-Yarvis-Organization": str(org_b), "X-Yarvis-Permissions": "*"}), json={"merchant": {"trade_name": "Canonical", "products": ["tpv"]}, "free_text": "request", "classification": "alta_tpv", "actor": "forged"})
    assert created.status_code == 201, created.text
    request = created.json(); merchant_id = request["merchant_id"]
    assert client.get("/radar/dashboard", headers=headers("radar-a", "another-forged-workspace")).json()["merchants"][0]["id"] == merchant_id
    assert client.get("/radar/dashboard", headers=headers("radar-b")).json()["merchants"] == []
    assert client.get(f"/radar/merchants/{merchant_id}", headers=headers("radar-b")).status_code == 404
    before = None
    with app.state.yarvis.persistence.create_session() as db:
        before = db.scalar(select(func.count()).select_from(RadarActivity))
    assert client.post("/radar/requests", headers=headers("radar-b", **{"Idempotency-Key": "foreign-create"}), json={"merchant_id": merchant_id, "free_text": "foreign", "classification": "soporte"}).status_code == 404
    assert client.patch(f"/radar/requests/{request['id']}/checklist/{request['checklist'][0]['id']}", headers=headers("radar-b", **{"Idempotency-Key": "foreign-checklist"}), json={"received": True}).status_code == 404
    assert client.patch(f"/radar/requests/{request['id']}/next-action", headers=headers("radar-b", **{"Idempotency-Key": "foreign-next-action"}), json={"next_action": "foreign"}).status_code == 404
    assert client.post(f"/radar/requests/{request['id']}/notes", headers=headers("radar-b", **{"Idempotency-Key": "foreign-note"}), json={"note": "foreign"}).status_code == 404
    assert client.post(f"/radar/requests/{request['id']}/close", headers=headers("radar-b", **{"Idempotency-Key": "foreign-close"}), json={"incomplete_justification": "foreign"}).status_code == 404
    assert client.post(f"/radar/requests/{request['id']}/reopen", headers=headers("radar-b", **{"Idempotency-Key": "foreign-reopen"}), json={}).status_code == 404
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(RadarActivity)) == before
        assert db.scalar(select(RadarMerchant.organization_id).where(RadarMerchant.id == merchant_id)) == org_a
        assert db.scalar(select(RadarRequest.organization_id).where(RadarRequest.id == request["id"])) == org_a
    revoked = client.post(f"/governance/memberships/{db_membership_id(radar_a, org_a)}/revoke", headers={**headers("governor-a"), "Idempotency-Key": "revoke-radar-a"}, params={"causation_id": str(uuid4())})
    assert revoked.status_code == 200, revoked.text
    denied = client.get("/radar/dashboard", headers=headers("radar-a"))
    assert denied.status_code == 403


def db_membership_id(principal_id, organization_id):
    with app.state.yarvis.persistence.create_session() as db:
        return str(db.scalar(select(PrincipalMembership.id).where(PrincipalMembership.principal_id == principal_id, PrincipalMembership.organization_id == organization_id)))

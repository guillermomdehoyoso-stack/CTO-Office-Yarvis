from fastapi.testclient import TestClient
from sqlalchemy import select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.netpay_inbox import NetpayInboxCommandReceipt, NetpayServiceCase
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

client = TestClient(app)


def _setup():
    with app.state.yarvis.persistence.create_session() as db:
        org, other = Organization(legal_name="Inbox Org", display_name="Inbox Org", status="active"), Organization(legal_name="Inbox Other", display_name="Inbox Other", status="active")
        operator, viewer, foreign = Principal(external_subject="inbox:operator", status="active"), Principal(external_subject="inbox:viewer", status="active"), Principal(external_subject="inbox:foreign", status="active")
        db.add_all((org, other, operator, viewer, foreign)); db.flush()
        db.add_all((PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_inbox_operator"), PrincipalMembership(principal_id=viewer.id, organization_id=org.id, role="netpay_inbox_viewer"), PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="netpay_inbox_operator")))
        master = NetpayClient(organization_id=org.id, display_name="Client", normalized_name="client", created_by_principal_id=operator.id, updated_by_principal_id=operator.id)
        db.add(master); db.flush()
        company = NetpayCompany(organization_id=org.id, client_id=master.id, legal_name="Company", normalized_legal_name="company", created_by_principal_id=operator.id, updated_by_principal_id=operator.id)
        db.add(company); db.flush()
        branch = NetpayBranch(organization_id=org.id, company_id=company.id, commercial_name="Branch", normalized_commercial_name="branch", branch_match_key="branch", branch_kind="physical", created_by_principal_id=operator.id, updated_by_principal_id=operator.id)
        db.add(branch); db.flush()
        ids = (org.id, master.id, company.id, branch.id)
        db.commit()
    def h(subject, key): return {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "Idempotency-Key": key}
    return *ids, h


def test_inbox_create_replay_event_and_tenant_queries():
    org, master, company, branch, h = _setup()
    payload = {"client_id": str(master), "company_id": str(company), "branch_id": str(branch), "case_type_key": "branch_onboarding", "original_description": "Open branch", "product": "tpv"}
    first = client.post("/netpay/inbox/cases", headers=h("inbox:operator", "case"), json=payload)
    replay = client.post("/netpay/inbox/cases", headers=h("inbox:operator", "case"), json=payload)
    assert first.status_code == 201 and replay.status_code == 201 and replay.json() == first.json()
    assert client.get("/netpay/inbox", headers=h("inbox:viewer", "read")).json()["total"] == 1
    assert client.get(f"/netpay/inbox/cases/{first.json()['id']}", headers=h("inbox:foreign", "foreign")).status_code == 404
    with app.state.yarvis.persistence.create_session() as db:
        assert len(db.scalars(select(NetpayServiceCase)).all()) == len(db.scalars(select(NetpayInboxCommandReceipt)).all()) == 1
        assert len(db.scalars(select(DomainEvent).where(DomainEvent.event_type == "netpay_service_case.created")).all()) == 1


def test_inbox_authority_and_fingerprint_conflict():
    org, master, company, branch, h = _setup()
    payload = {"client_id": str(master), "company_id": str(company), "case_type_key": "unclassified", "original_description": "x"}
    assert client.post("/netpay/inbox/cases", headers=h("inbox:viewer", "x") | {"X-Yarvis-Authority": "netpay.inbox.manage"}, json=payload).status_code == 403
    assert client.post("/netpay/inbox/cases", headers=h("inbox:operator", "same"), json=payload).status_code == 201
    assert client.post("/netpay/inbox/cases", headers=h("inbox:operator", "same"), json=payload | {"original_description": "changed"}).status_code == 409

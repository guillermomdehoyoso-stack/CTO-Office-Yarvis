from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.netpay_inbox import NetpayCaseChecklistItem, NetpayInboxCommandReceipt, NetpayServiceCase
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


def test_create_replay_preserves_original_body_after_assignment():
    _, master, company, _, h = _setup()
    payload = {
        "client_id": str(master),
        "company_id": str(company),
        "case_type_key": "unclassified",
        "original_description": "replay snapshot",
    }
    created = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "create-snapshot"),
        json=payload,
    )
    assert created.status_code == 201

    assigned = client.put(
        f"/netpay/inbox/cases/{created.json()['id']}/assignment",
        headers=h("inbox:operator", "assign-after-create"),
        json={"responsible_principal_id": created.json().get("created_by_principal_id")},
    )
    assert assigned.status_code == 200

    replay = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "create-snapshot"),
        json=payload,
    )
    assert replay.status_code == 201
    assert replay.json() == created.json()


def _principal_id(subject: str):
    with app.state.yarvis.persistence.create_session() as db:
        return db.scalar(select(Principal.id).where(Principal.external_subject == subject))


def test_b2_five_commands_replay_events_and_requires_attention():
    org_id, master, company, _, h = _setup()
    operator_id = _principal_id("inbox:operator")
    viewer_id = _principal_id("inbox:viewer")
    created = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "b2-create"),
        json={
            "client_id": str(master),
            "company_id": str(company),
            "case_type_key": "unclassified",
            "original_description": "B2 flow",
            "expected_outcome": "Case handled",
        },
    )
    assert created.status_code == 201
    case_id = created.json()["id"]
    with app.state.yarvis.persistence.create_session() as db:
        item = db.get(NetpayServiceCase, case_id)
        checklist = NetpayCaseChecklistItem(
            organization_id=item.organization_id,
            case_id=item.id,
            template_version=1,
            requirement_key="identity",
            required=True,
            created_by_principal_id=operator_id,
            updated_by_principal_id=operator_id,
        )
        db.add(checklist)
        db.commit()
        checklist_id = checklist.id

    checked = client.put(
        f"/netpay/inbox/cases/{case_id}/checklist/{checklist_id}",
        headers=h("inbox:operator", "b2-checklist"),
        json={"status": "confirmed", "safe_evidence_reference": "DOC-SAFE-1"},
    )
    assert checked.status_code == 200
    assert checked.json()["checklist"][0]["status"] == "confirmed"

    assigned = client.put(
        f"/netpay/inbox/cases/{case_id}/assignment",
        headers=h("inbox:operator", "b2-assign"),
        json={"responsible_principal_id": str(viewer_id)},
    )
    assert assigned.status_code == 200
    assert assigned.json()["responsible_principal_id"] == str(viewer_id)

    action = client.put(
        f"/netpay/inbox/cases/{case_id}/next-action",
        headers=h("inbox:operator", "b2-action"),
        json={
            "description": "Contact customer",
            "responsible_principal_id": str(viewer_id),
            "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "status": "open",
            "origin": "human",
        },
    )
    assert action.status_code == 200
    assert action.json()["requires_attention"] is False

    overdue = client.put(
        f"/netpay/inbox/cases/{case_id}/next-action",
        headers=h("inbox:operator", "b2-action-overdue"),
        json={
            "description": "Overdue follow-up",
            "responsible_principal_id": str(viewer_id),
            "due_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "status": "open",
            "origin": "human",
        },
    )
    assert overdue.status_code == 200
    assert overdue.json()["requires_attention"] is True

    transitioned = client.put(
        f"/netpay/inbox/cases/{case_id}/state",
        headers=h("inbox:operator", "b2-state"),
        json={"state": "triage"},
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["state"] == "triage"

    noted = client.post(
        f"/netpay/inbox/cases/{case_id}/activities",
        headers=h("inbox:operator", "b2-note"),
        json={"activity_type": "note", "safe_summary": "Customer contacted", "external_reference": "CRM-1"},
    )
    assert noted.status_code == 201
    assert noted.json()["activities"][-1]["summary"].endswith("[ref:CRM-1]")

    checklist_replay = client.put(
        f"/netpay/inbox/cases/{case_id}/checklist/{checklist_id}",
        headers=h("inbox:operator", "b2-checklist"),
        json={"status": "confirmed", "safe_evidence_reference": "DOC-SAFE-1"},
    )
    assert checklist_replay.json() == checked.json()
    assert client.put(
        f"/netpay/inbox/cases/{case_id}/checklist/{checklist_id}",
        headers=h("inbox:operator", "b2-checklist"),
        json={"status": "rejected"},
    ).status_code == 409

    detail = client.get(f"/netpay/inbox/cases/{case_id}", headers=h("inbox:viewer", "read-b2"))
    assert detail.status_code == 200
    with app.state.yarvis.persistence.create_session() as db:
        events = db.scalars(select(DomainEvent).where(DomainEvent.aggregate_id == UUID(case_id))).all()
        assert any(event.event_type == "netpay_service_case.state_changed" for event in events)
        assert any(event.event_type == "netpay_service_case.activity_recorded" for event in events)
        assert all("Customer contacted" not in str(event.payload) for event in events)
        receipts = db.scalars(select(NetpayInboxCommandReceipt).where(NetpayInboxCommandReceipt.organization_id == org_id)).all()
        assert all("deterministic-inbound-intake" not in str(receipt.result_response_body) for receipt in receipts)


def test_b2_authority_membership_terminal_and_franchise_steps():
    _, master, company, _, h = _setup()
    foreign_id = _principal_id("inbox:foreign")
    created = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "b2-security-create"),
        json={"client_id": str(master), "company_id": str(company), "case_type_key": "unclassified", "original_description": "security"},
    )
    case_id = created.json()["id"]
    assert client.put(
        f"/netpay/inbox/cases/{case_id}/assignment",
        headers=h("inbox:operator", "foreign-assignee"),
        json={"responsible_principal_id": str(foreign_id)},
    ).status_code == 404
    assert client.put(
        f"/netpay/inbox/cases/{case_id}/assignment",
        headers=h("inbox:viewer", "viewer-forged") | {"X-Yarvis-Authority": "netpay.inbox.manage"},
        json={"responsible_principal_id": None},
    ).status_code == 403
    assert client.put(
        f"/netpay/inbox/cases/{case_id}/state",
        headers=h("inbox:operator", "cancel-no-reason"),
        json={"state": "cancelled"},
    ).status_code == 409
    cancelled = client.put(
        f"/netpay/inbox/cases/{case_id}/state",
        headers=h("inbox:operator", "cancel-reason"),
        json={"state": "cancelled", "reason": "Duplicate request"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["requires_attention"] is False
    assert client.post(
        f"/netpay/inbox/cases/{case_id}/activities",
        headers=h("inbox:operator", "terminal-note"),
        json={"activity_type": "note", "safe_summary": "must fail"},
    ).status_code == 409

    franchise = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "franchise-create"),
        json={"client_id": str(master), "company_id": str(company), "case_type_key": "unclassified", "original_description": "franchise"},
    )
    classified = client.put(
        f"/netpay/inbox/cases/{franchise.json()['id']}/classification",
        headers=h("inbox:operator", "franchise-classify"),
        json={"case_type_key": "franchisee_change", "product": "not_applicable", "priority": "normal"},
    )
    assert classified.status_code == 200
    assert [step["ordinal"] for step in classified.json()["steps"]] == list(range(1, 8))


def test_b2_revoked_membership_denies_before_replay():
    _, master, company, _, h = _setup()
    created = client.post(
        "/netpay/inbox/cases",
        headers=h("inbox:operator", "revocation-create"),
        json={"client_id": str(master), "company_id": str(company), "case_type_key": "unclassified", "original_description": "revocation"},
    )
    case_id = created.json()["id"]
    first = client.put(
        f"/netpay/inbox/cases/{case_id}/assignment",
        headers=h("inbox:operator", "revocation-replay"),
        json={"responsible_principal_id": None},
    )
    assert first.status_code == 200
    with app.state.yarvis.persistence.create_session() as db:
        principal_id = db.scalar(select(Principal.id).where(Principal.external_subject == "inbox:operator"))
        membership = db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal_id))
        membership.status = "revoked"
        membership.revoked_at = datetime.now(timezone.utc)
        db.commit()
    replay = client.put(
        f"/netpay/inbox/cases/{case_id}/assignment",
        headers=h("inbox:operator", "revocation-replay"),
        json={"responsible_principal_id": None},
    )
    assert replay.status_code == 403

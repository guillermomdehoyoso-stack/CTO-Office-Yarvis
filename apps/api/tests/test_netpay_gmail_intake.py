from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Barrier
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text

from yarvis_api.api.routes import netpay_gmail_intake as gmail_routes
from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.netpay_gmail_intake import (
    NetpayCandidateCommercialIntakeTrace,
    NetpayCandidateHumanFollowUp,
    NetpayCandidateQualification,
    NetpayDossierEvidenceReference,
    NetpayGmailCommandReceipt,
    NetpayGmailConnection,
    NetpayGmailOAuthAttempt,
    NetpayGmailSourceItem,
    NetpayGmailSyncRun,
    NetpayIntakeCandidate,
)
from yarvis_api.models.netpay_inbox import CommercialIntakeCommandReceipt, CommercialIntakeItem, NetpayServiceCase
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.netpay_gmail_google_provider import GoogleOAuthResult
from yarvis_api.services.netpay_gmail_provider import DEFAULT_FAKE_GMAIL_PROVIDER, GmailSourceMessage
from yarvis_api.services.netpay_gmail_secret_store import InMemoryGmailSecretStore

client = TestClient(app)


def _headers(subject: str, key: str) -> dict[str, str]:
    return {
        "X-Yarvis-Subject": subject,
        "X-Yarvis-Auth-Token": "deterministic-inbound-intake",
        "Idempotency-Key": key,
    }


def _setup() -> tuple[object, object, object, object]:
    with app.state.yarvis.persistence.create_session() as db:
        db.execute(
            text(
                "TRUNCATE netpay_dossier_requirement_reviews, "
                "netpay_dossier_evidence_references, netpay_candidate_onboarding_dossiers"
            )
        )
        db.execute(delete(NetpayCandidateCommercialIntakeTrace))
        db.execute(delete(NetpayCandidateQualification))
        db.execute(delete(CommercialIntakeItem))
        db.execute(delete(NetpayCandidateHumanFollowUp))
        db.execute(delete(NetpayGmailCommandReceipt))
        db.execute(delete(NetpayGmailSourceItem))
        db.execute(delete(NetpayGmailSyncRun))
        db.execute(delete(NetpayGmailConnection))
        db.commit()
        org = Organization(legal_name="Synthetic Stores Org", display_name="Synthetic Stores Org", status="active")
        other = Organization(legal_name="Synthetic Other Org", display_name="Synthetic Other Org", status="active")
        operator = Principal(external_subject="gmail:d1:operator", status="active")
        foreign = Principal(external_subject="gmail:d1:foreign", status="active")
        db.add_all((org, other, operator, foreign))
        db.flush()
        db.add_all(
            (
                PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_inbox_operator"),
                PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="netpay_inbox_operator"),
            )
        )
        db.commit()
        return org.id, other.id, operator.id, foreign.id


def test_h2q_qualification_is_append_only_idempotent_scoped_and_previewable() -> None:
    _setup()
    app.dependency_overrides[gmail_routes.gmail_provider] = lambda: DEFAULT_FAKE_GMAIL_PROVIDER
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-h2q", _fixture(datetime.now(timezone.utc))[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "h2q-connect"),
        json={
            "provider_account_id": "synthetic-h2q",
            "label_id": "LABEL_STORES",
            "credential_secret_ref": "synthetic",
            "query": "newer_than:30d",
        },
    ).json()
    synced = client.post(
        f"/netpay/gmail/connections/{connection['id']}/sync", headers=_headers("gmail:d1:operator", "h2q-sync"), json={}
    )
    assert synced.status_code == 201, synced.text
    assert synced.json()["status"] == "succeeded"
    candidate = client.get("/netpay/gmail/candidates", headers=_headers("gmail:d1:operator", "h2q-list")).json()[
        "items"
    ][0]
    before = {key: candidate[key] for key in ("state", "facts", "owner_id", "reviewed_at", "disposition_reason")}
    payload = {
        "applicant_kind": "persona_moral",
        "legal_person_name": {
            "value": "Empresa Sintética SA",
            "verification": "operator_reported",
            "source_field": "body",
        },
        "representative_name": {
            "value": "Persona Sintética",
            "verification": "operator_reported",
            "source_field": "body",
        },
        "brand_name": {"value": "Marca Sintética", "verification": "operator_confirmed", "source_field": "subject"},
        "requested_products": ["tpv", "ecommerce"],
        "branches": [
            {
                "draft_key": "branch-1",
                "name": "Sucursal Sintética Uno",
                "requested_products": ["tpv"],
                "verification": "operator_reported",
                "source_field": "body",
            },
            {
                "draft_key": "branch-2",
                "name": "Sucursal Sintética Dos",
                "requested_products": ["ecommerce"],
                "verification": "unresolved",
                "source_field": "body",
            },
        ],
        "rationale": "Revisión sintética.",
    }
    created = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications",
        headers=_headers("gmail:d1:operator", "h2q-create"),
        json=payload,
    )
    replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications",
        headers=_headers("gmail:d1:operator", "h2q-create"),
        json=payload,
    )
    assert created.status_code == replay.status_code == 201 and replay.json() == created.json()
    conflict = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications",
        headers=_headers("gmail:d1:operator", "h2q-create"),
        json={**payload, "rationale": "changed"},
    )
    assert conflict.status_code == 409
    page = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications", headers=_headers("gmail:d1:operator", "h2q-read")
    ).json()
    assert len(page) == 1 and len(page[0]["payload"]["branches"]) == 2
    preview = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake-preview",
        headers=_headers("gmail:d1:operator", "h2q-preview"),
    )
    assert preview.status_code == 200 and preview.json()["product_interest"] == "mixed"
    promoted_payload = {
        key: preview.json()[key]
        for key in (
            "qualification_id",
            "provisional_company_name",
            "provisional_contact_name",
            "product_interest",
            "summary",
            "priority",
            "next_action",
        )
    }
    promoted = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake",
        headers=_headers("gmail:d1:operator", "h2i-promote"),
        json=promoted_payload,
    )
    promoted_replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake",
        headers=_headers("gmail:d1:operator", "h2i-promote"),
        json=promoted_payload,
    )
    assert promoted.status_code == promoted_replay.status_code == 201
    assert promoted.json() == promoted_replay.json()
    assert len(promoted.json()["branch_drafts"]) == 2
    promoted_readback = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake-preview",
        headers=_headers("gmail:d1:operator", "h2i-readback"),
    )
    assert promoted_readback.status_code == 200
    assert (
        promoted_readback.json()["promotion_trace"]["commercial_intake_id"] == promoted.json()["commercial_intake_id"]
    )
    assert promoted_readback.json()["existing_intake"]["next_action"] == preview.json()["next_action"]
    assert len(promoted_readback.json()["promotion_trace"]["branch_drafts"]) == 2
    after = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}", headers=_headers("gmail:d1:operator", "h2q-after")
    ).json()
    assert {key: after[key] for key in before} == before
    foreign = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications",
        headers=_headers("gmail:d1:foreign", "h2q-foreign"),
    )
    assert foreign.status_code == 404
    app.dependency_overrides.clear()


def test_h2d_snapshot_reviews_shared_evidence_completion_and_terminal_candidate_independence() -> None:
    org_id, _, _, _ = _setup()
    app.dependency_overrides[gmail_routes.gmail_provider] = lambda: DEFAULT_FAKE_GMAIL_PROVIDER
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-h2d", _fixture(datetime.now(timezone.utc))[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "h2d-connect"),
        json={"provider_account_id": "synthetic-h2d", "label_id": "LABEL_STORES", "credential_secret_ref": "synthetic"},
    ).json()
    assert (
        client.post(
            f"/netpay/gmail/connections/{connection['id']}/sync",
            headers=_headers("gmail:d1:operator", "h2d-sync"),
            json={},
        ).status_code
        == 201
    )
    candidate = client.get("/netpay/gmail/candidates", headers=_headers("gmail:d1:operator", "h2d-list")).json()[
        "items"
    ][0]
    source_before = client.get(
        f"/netpay/gmail/source-items/{candidate['source_item_id']}", headers=_headers("gmail:d1:operator", "h2d-source")
    ).json()
    follow_up = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
        headers=_headers("gmail:d1:operator", "h2d-note"),
        json={"kind": "general_follow_up", "note": "Synthetic preserved note.", "occurred_at": None},
    )
    assert follow_up.status_code == 201
    branches = [
        {
            "draft_key": f"branch-{index}",
            "name": f"Sucursal Sintética {index}",
            "requested_products": ["tpv", "ecommerce"],
            "verification": "operator_reported",
            "source_field": "operator_review",
        }
        for index in range(1, 6)
    ]
    qualification = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/qualifications",
        headers=_headers("gmail:d1:operator", "h2d-qualification"),
        json={
            "applicant_kind": "persona_moral",
            "legal_person_name": {
                "value": "Empresa Sintética",
                "verification": "operator_reported",
                "source_field": "operator_review",
            },
            "representative_name": {
                "value": "Representante Sintético",
                "verification": "operator_reported",
                "source_field": "operator_review",
            },
            "brand_name": {
                "value": "Marca Sintética",
                "verification": "operator_reported",
                "source_field": "operator_review",
            },
            "requested_products": ["tpv", "ecommerce"],
            "branches": branches,
            "rationale": "Synthetic H2-D conformance.",
        },
    ).json()
    preview = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake-preview",
        headers=_headers("gmail:d1:operator", "h2d-preview"),
    ).json()
    promoted = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/commercial-intake",
        headers=_headers("gmail:d1:operator", "h2d-promote"),
        json={
            key: preview[key]
            for key in (
                "qualification_id",
                "provisional_company_name",
                "provisional_contact_name",
                "product_interest",
                "summary",
                "priority",
                "next_action",
            )
        },
    ).json()
    accepted = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/review",
        headers=_headers("gmail:d1:operator", "h2d-accept"),
        json={"action": "accept", "owner_type": "commercial_intake", "owner_id": promoted["commercial_intake_id"]},
    )
    assert accepted.status_code == 200 and accepted.json()["immutable"] is True
    create_payload = {
        "qualification_id": qualification["id"],
        "catalog_sha256": "4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b",
        "confirmed": True,
    }
    dossier_preview = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier-preview",
        headers=_headers("gmail:d1:operator", "h2d-dossier-preview"),
    )
    assert dossier_preview.status_code == 200
    assert dossier_preview.json()["existing"] is False
    assert dossier_preview.json()["candidate_terminal"] is True
    assert dossier_preview.json()["products"] == ["ecommerce", "tpv"]
    assert len(dossier_preview.json()["branches"]) == 5
    assert dossier_preview.json()["blocker_count"] == len(dossier_preview.json()["requirements"])
    created = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier",
        headers=_headers("gmail:d1:operator", "h2d-create"),
        json=create_payload,
    )
    replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier",
        headers=_headers("gmail:d1:operator", "h2d-create"),
        json=create_payload,
    )
    assert created.status_code == replay.status_code == 201 and created.json() == replay.json()
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier",
            headers=_headers("gmail:d1:foreign", "h2d-create"),
            json=create_payload,
        ).status_code
        == 404
    )
    dossier = created.json()
    assert dossier["catalog_version"] == "1.0.0"
    assert dossier["products"] == ["ecommerce", "tpv"] and len(dossier["branches"]) == 5
    assert dossier["complete"] is False and dossier["blockers"]
    branch_addresses = [item for item in dossier["requirements"] if item["key"] == "branch_address_proof"]
    assert len(branch_addresses) == 5
    evidence = {
        "source_item_id": candidate["source_item_id"],
        "attachment_index": 0,
        "suggestion": "unverified synthetic suggestion",
    }
    first = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
        headers=_headers("gmail:d1:operator", "h2d-shared-1"),
        json={
            "requirement_snapshot_key": branch_addresses[0]["snapshot_key"],
            "state": "attachment_detected",
            "evidence": evidence,
        },
    )
    first_replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
        headers=_headers("gmail:d1:operator", "h2d-shared-1"),
        json={
            "requirement_snapshot_key": branch_addresses[0]["snapshot_key"],
            "state": "attachment_detected",
            "evidence": evidence,
        },
    )
    assert first.status_code == first_replay.status_code == 201 and first.json() == first_replay.json()
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", "h2d-shared-1"),
            json={
                "requirement_snapshot_key": branch_addresses[0]["snapshot_key"],
                "state": "under_review",
                "evidence": evidence,
            },
        ).status_code
        == 409
    )
    second = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
        headers=_headers("gmail:d1:operator", "h2d-shared-2"),
        json={
            "requirement_snapshot_key": branch_addresses[1]["snapshot_key"],
            "state": "attachment_detected",
            "evidence": evidence,
        },
    ).json()
    first_evidence_id = next(
        item for item in first.json()["requirements"] if item["snapshot_key"] == branch_addresses[0]["snapshot_key"]
    )["history"][-1]["evidence"]["id"]
    second_evidence_id = next(
        item for item in second["requirements"] if item["snapshot_key"] == branch_addresses[1]["snapshot_key"]
    )["history"][-1]["evidence"]["id"]
    assert first_evidence_id == second_evidence_id
    state_target = dossier["requirements"][0]["snapshot_key"]
    for index, state in enumerate(("under_review", "observed", "not_applicable", "pending"), start=1):
        result = client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", f"h2d-state-{index}"),
            json={"requirement_snapshot_key": state_target, "state": state, "comment": "Synthetic attributed review."},
        )
        assert result.status_code == 201, result.text
    current = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier", headers=_headers("gmail:d1:operator", "h2d-read")
    ).json()
    address = next(item for item in current["requirements"] if item["key"] == "branch_address_proof")
    tax = next(item for item in current["requirements"] if item["key"] == "tax_status_certificate")
    photos = next(item for item in current["requirements"] if item["key"] == "branch_premises_photos")
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", "h2d-age-rejected"),
            json={
                "requirement_snapshot_key": address["snapshot_key"],
                "state": "validated",
                "comment": "Synthetic review.",
                "review_data": {"document_date": (datetime.now(timezone.utc) - timedelta(days=61)).date().isoformat()},
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", "h2d-holder-rejected"),
            json={
                "requirement_snapshot_key": tax["snapshot_key"],
                "state": "validated",
                "comment": "Synthetic review.",
                "review_data": {
                    "document_date": datetime.now(timezone.utc).date().isoformat(),
                    "holder": "Synthetic Holder",
                    "holder_correspondence": "does_not_match",
                },
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", "h2d-photos-rejected"),
            json={
                "requirement_snapshot_key": photos["snapshot_key"],
                "state": "validated",
                "comment": "Synthetic review.",
                "review_data": {"interior_count": 2, "facade_count": 1},
            },
        ).status_code
        == 422
    )

    def validation_data(requirement: dict) -> dict:
        key = requirement["key"]
        values: dict = {}
        if requirement.get("maximum_age_days") is not None:
            values["document_date"] = (datetime.now(timezone.utc) - timedelta(days=60)).date().isoformat()
        if key in {"receiving_account_bank_statement", "tax_status_certificate"}:
            values["holder"] = "Synthetic Holder"
        if key == "tax_status_certificate":
            values["holder_correspondence"] = "matches"
        if key == "branch_premises_photos":
            values.update({"interior_count": 2, "facade_count": 2})
        if key == "branch_manager_contact":
            values.update({"name": "Synthetic Manager", "phone": "0000000000", "email": "manager@example.invalid"})
        return values

    reusable_manager_review_id = None
    for index, requirement in enumerate(current["requirements"], start=1):
        review_data = validation_data(requirement)
        if requirement["key"] == "branch_manager_contact" and reusable_manager_review_id:
            review_data = {"shared_contact_review_id": reusable_manager_review_id}
        result = client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier/reviews",
            headers=_headers("gmail:d1:operator", f"h2d-complete-{index}"),
            json={
                "requirement_snapshot_key": requirement["snapshot_key"],
                "state": "validated",
                "comment": "Synthetic human validation.",
                "review_data": review_data,
            },
        )
        assert result.status_code == 201, result.text
        if requirement["key"] == "branch_manager_contact" and reusable_manager_review_id is None:
            reviewed_requirement = next(
                item for item in result.json()["requirements"] if item["snapshot_key"] == requirement["snapshot_key"]
            )
            reusable_manager_review_id = reviewed_requirement["history"][-1]["id"]
    readback = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/dossier", headers=_headers("gmail:d1:operator", "h2d-final")
    )
    assert readback.status_code == 200 and readback.json()["complete"] is True and readback.json()["blockers"] == []
    assert readback.json()["state_counts"]["validated"] == len(readback.json()["requirements"])
    manager_histories = [
        item["history"][-1] for item in readback.json()["requirements"] if item["key"] == "branch_manager_contact"
    ]
    assert sum("name" in item["review_data"] for item in manager_histories) == 1
    assert sum("shared_contact_review_id" in item["review_data"] for item in manager_histories) == 4
    assert (
        client.get(
            f"/netpay/gmail/candidates/{candidate['id']}/dossier", headers=_headers("gmail:d1:foreign", "h2d-foreign")
        ).status_code
        == 404
    )
    candidate_after = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}", headers=_headers("gmail:d1:operator", "h2d-candidate-after")
    ).json()
    assert candidate_after["state"] == "accepted" and candidate_after["immutable"] is True
    source_after = client.get(
        f"/netpay/gmail/source-items/{candidate['source_item_id']}",
        headers=_headers("gmail:d1:operator", "h2d-source-after"),
    ).json()
    assert source_after["source_fingerprint"] == source_before["source_fingerprint"]
    assert (
        client.get(
            f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
            headers=_headers("gmail:d1:operator", "h2d-note-after"),
        ).json()["total"]
        == 1
    )
    with app.state.yarvis.persistence.create_session() as db:
        assert (
            len(
                db.scalars(
                    select(NetpayDossierEvidenceReference).where(
                        NetpayDossierEvidenceReference.organization_id == org_id
                    )
                ).all()
            )
            == 1
        )
        events = db.scalars(
            select(DomainEvent).where(
                DomainEvent.organization_id == org_id,
                DomainEvent.event_type == "netpay.candidate_dossier_requirement_reviewed",
            )
        ).all()
        assert events and all("comment" not in event.payload for event in events)
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(Exception, match="append-only"):
            db.execute(
                text("update netpay_candidate_onboarding_dossiers set catalog_version='mutated' where id=:id"),
                {"id": dossier["id"]},
            )
            db.flush()
    app.dependency_overrides.clear()


def test_h1_candidate_human_follow_up_is_append_only_tenant_scoped_and_idempotent() -> None:
    org_id, _, operator_id, _ = _setup()
    app.dependency_overrides[gmail_routes.gmail_provider] = lambda: DEFAULT_FAKE_GMAIL_PROVIDER
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-follow-up-account", _fixture(datetime.now(timezone.utc))[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "h1-connect"),
        json={
            "provider_account_id": "synthetic-follow-up-account",
            "label_id": "LABEL_STORES",
            "credential_secret_ref": "synthetic-follow-up-ref",
        },
    ).json()
    client.post(
        f"/netpay/gmail/connections/{connection['id']}/sync",
        headers=_headers("gmail:d1:operator", "h1-sync"),
        json={},
    )
    candidate = client.get("/netpay/gmail/candidates", headers=_headers("gmail:d1:operator", "h1-list")).json()[
        "items"
    ][0]
    source = client.get(
        f"/netpay/gmail/source-items/{candidate['source_item_id']}",
        headers=_headers("gmail:d1:operator", "h1-source"),
    ).json()
    unchanged = {
        key: candidate[key]
        for key in (
            "state",
            "request_type",
            "facts",
            "owner_type",
            "owner_id",
            "disposition_reason",
            "suggested_next_action",
        )
    }
    payload = {
        "kind": "meeting",
        "note": "Synthetic operator meeting; outcome remains unconfirmed.",
        "occurred_at": None,
    }
    created = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
        headers=_headers("gmail:d1:operator", "h1-follow-up"),
        json=payload,
    )
    replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
        headers=_headers("gmail:d1:operator", "h1-follow-up"),
        json=payload,
    )
    assert created.status_code == replay.status_code == 201
    assert replay.json() == created.json()
    assert created.json()["occurred_at"] is None
    assert created.json()["provenance_kind"] == "operator_reported"
    assert created.json()["created_by_principal_id"] == str(operator_id)
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
            headers=_headers("gmail:d1:operator", "h1-follow-up"),
            json={**payload, "note": "Changed synthetic payload."},
        ).status_code
        == 409
    )

    occurred_at = "2026-10-10T16:30:00Z"
    for index, kind in enumerate(("call", "agreement", "pending_item", "general_follow_up"), start=1):
        result = client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
            headers=_headers("gmail:d1:operator", f"h1-kind-{index}"),
            json={"kind": kind, "note": f"Synthetic {kind} entry.", "occurred_at": occurred_at},
        )
        assert result.status_code == 201
        assert result.json()["occurred_at"].startswith("2026-10-10T16:30:00")

    assert (
        client.get(
            f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
            headers=_headers("gmail:d1:foreign", "h1-cross-query"),
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/follow-ups",
            headers=_headers("gmail:d1:foreign", "h1-cross-command"),
            json=payload,
        ).status_code
        == 404
    )

    page = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}/follow-ups?limit=100",
        headers=_headers("gmail:d1:operator", "h1-readback"),
    )
    assert page.status_code == 200
    assert page.json()["total"] == 5
    assert [item["recorded_at"] for item in page.json()["items"]] == sorted(
        item["recorded_at"] for item in page.json()["items"]
    )
    after = client.get(
        f"/netpay/gmail/candidates/{candidate['id']}", headers=_headers("gmail:d1:operator", "h1-after")
    ).json()
    assert {key: after[key] for key in unchanged} == unchanged
    after_source = client.get(
        f"/netpay/gmail/source-items/{candidate['source_item_id']}",
        headers=_headers("gmail:d1:operator", "h1-source-after"),
    ).json()
    assert after_source["source_fingerprint"] == source["source_fingerprint"]

    with app.state.yarvis.persistence.create_session() as db:
        rows = db.scalars(
            select(NetpayCandidateHumanFollowUp)
            .where(
                NetpayCandidateHumanFollowUp.organization_id == org_id,
                NetpayCandidateHumanFollowUp.candidate_id == UUID(candidate["id"]),
            )
            .order_by(NetpayCandidateHumanFollowUp.recorded_at, NetpayCandidateHumanFollowUp.id)
        ).all()
        events = db.scalars(
            select(DomainEvent).where(
                DomainEvent.organization_id == org_id,
                DomainEvent.event_type == "netpay.candidate_human_follow_up_recorded",
            )
        ).all()
        assert len(rows) == len(events) == 5
        assert all("note" not in event.payload for event in events)
        assert "Synthetic operator meeting" not in str([event.payload for event in events])
    app.dependency_overrides.clear()


def _fixture(now: datetime) -> list[GmailSourceMessage]:
    return [
        GmailSourceMessage(
            message_id="synthetic-message-001",
            thread_id="synthetic-thread-stores",
            received_at=now - timedelta(days=1),
            sender="synthetic.sender@example.invalid",
            recipient="netpay@example.invalid",
            subject="Alta de e-commerce Stores para nuevas sucursales",
            body="<p>Solicitud sintética para Stores.</p><script>alert('ignored')</script>",
            label_ids=frozenset({"LABEL_STORES"}),
            attachments=({"name": "alta.pdf", "mime_type": "application/pdf", "size": 128},),
        ),
        GmailSourceMessage(
            message_id="synthetic-message-002",
            thread_id="synthetic-thread-stores",
            received_at=now - timedelta(days=2),
            sender="synthetic.sender@example.invalid",
            recipient="netpay@example.invalid",
            subject="Re: Alta de e-commerce Stores",
            body="Falta confirmar el cliente sintético.",
            label_ids=frozenset({"LABEL_STORES"}),
        ),
        GmailSourceMessage(
            message_id="synthetic-message-old",
            thread_id="synthetic-thread-old",
            received_at=now - timedelta(days=31),
            subject="Fuera de ventana",
            body="No debe entrar en el backfill.",
            label_ids=frozenset({"LABEL_STORES"}),
        ),
    ]


def test_d1_gmail_entry_processing_persistence_query_and_idempotency() -> None:
    org_id, other_id, _, _ = _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-stores-account", _fixture(now))
    headers = _headers("gmail:d1:operator", "gmail-connect-1")

    created = client.post(
        "/netpay/gmail/connections",
        headers=headers,
        json={
            "provider_account_id": "synthetic-stores-account",
            "label_id": "LABEL_STORES",
            "query": "newer_than:30d",
            "credential_secret_ref": "synthetic-ref-stores",
        },
    )
    assert created.status_code == 201
    connection_id = created.json()["id"]
    assert "credential_secret_ref" not in created.json()

    validated = client.post(
        f"/netpay/gmail/connections/{connection_id}/validate",
        headers=_headers("gmail:d1:operator", "gmail-validate-1"),
    )
    assert validated.status_code == 200
    assert validated.json()["state"] == "ready"

    synced = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-1"),
        json={"backfill_days": 30},
    )
    assert synced.status_code == 201
    assert synced.json()["status"] == "succeeded"
    assert synced.json()["captured_count"] == 2
    assert synced.json()["deduplicated_count"] == 0
    assert synced.json()["cursor_after"]
    assert (
        client.post(
            f"/netpay/gmail/connections/{connection_id}/sync",
            headers=_headers("gmail:d1:operator", "gmail-sync-too-wide"),
            json={"backfill_days": 31},
        ).status_code
        == 422
    )

    replay = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-1"),
        json={"backfill_days": 30},
    )
    assert replay.status_code == 201
    assert replay.json() == synced.json()

    second_run = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-2"),
        json={"backfill_days": 30},
    )
    assert second_run.status_code == 201
    assert second_run.json()["captured_count"] == 0
    assert second_run.json()["deduplicated_count"] == 2
    assert second_run.json()["cursor_after"] == synced.json()["cursor_after"]

    page = client.get("/netpay/gmail/source-items", headers=_headers("gmail:d1:operator", "gmail-read-1"))
    assert page.status_code == 200
    assert page.json()["total"] == 2
    first = next(item for item in page.json()["items"] if item["gmail_message_id"] == "synthetic-message-001")
    assert first["gmail_thread_id"] == "synthetic-thread-stores"
    assert first["plain_excerpt"]
    assert "alert" not in first["plain_excerpt"]
    assert first["attachment_metadata"] == [{"name": "alta.pdf", "mime_type": "application/pdf", "size": 128}]
    assert first["provenance"]["label_id"] == "LABEL_STORES"

    detail = client.get(
        f"/netpay/gmail/source-items/{first['id']}", headers=_headers("gmail:d1:operator", "gmail-read-2")
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == first["id"]
    assert (
        client.get(
            f"/netpay/gmail/source-items/{first['id']}",
            headers={**_headers("gmail:d1:operator", "gmail-foreign"), "X-Yarvis-Organization-Selector": str(other_id)},
        ).status_code
        == 404
    )

    with app.state.yarvis.persistence.create_session() as db:
        assert (
            db.scalar(select(NetpayGmailSourceItem).where(NetpayGmailSourceItem.organization_id == org_id)) is not None
        )
        assert db.scalar(select(NetpayGmailConnection).where(NetpayGmailConnection.id == connection_id)).cursor
        event_types = {
            event.event_type
            for event in db.scalars(select(DomainEvent).where(DomainEvent.organization_id == org_id)).all()
        }
        assert {
            "netpay.gmail.source_connected",
            "netpay.gmail.manual_sync_started",
            "netpay.gmail.manual_sync_completed",
            "netpay.gmail.source_item_captured",
            "netpay.gmail.source_item_deduplicated",
        } <= event_types
        assert db.scalar(select(CommercialIntakeItem).where(CommercialIntakeItem.organization_id == org_id)) is None
        assert db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.organization_id == org_id)) is None


def test_google_first_content_sync_ignores_bootstrap_cursor_and_running_sync_is_rejected() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    messages = _fixture(now)

    class RecordingGoogleProvider:
        provider_kind = "google"

        def __init__(self) -> None:
            self.cursor: str | None = "not-called"

        def list_messages(self, **kwargs):
            self.cursor = kwargs["cursor"]
            return messages

    provider = RecordingGoogleProvider()
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-stores-account", messages)
    created = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "google-first-connect"),
        json={
            "provider_account_id": "synthetic-stores-account",
            "label_id": "LABEL_STORES",
            "query": "",
            "credential_secret_ref": "synthetic-ref-stores",
        },
    )
    connection_id = UUID(created.json()["id"])
    with app.state.yarvis.persistence.create_session() as db:
        connection = db.get(NetpayGmailConnection, connection_id)
        assert connection is not None
        connection.provider_kind = "google"
        connection.state = "ready"
        connection.cursor = "profile-bootstrap-cursor"
        connection.manifest_status = "approved"
        connection.manifest_entries = [
            {"handle": f"opaque-{index}", "received_at": now.isoformat()} for index in range(10)
        ]
        connection.manifest_approved_at = now
        db.commit()

    app.dependency_overrides[gmail_routes.gmail_provider] = lambda: provider
    try:
        synced = client.post(
            f"/netpay/gmail/connections/{connection_id}/sync",
            headers=_headers("gmail:d1:operator", "google-first-sync"),
            json={"backfill_days": 30},
        )
        assert synced.status_code == 201
        assert synced.json()["captured_count"] == 2
        assert provider.cursor is None

        with app.state.yarvis.persistence.create_session() as db:
            connection = db.get(NetpayGmailConnection, connection_id)
            assert connection is not None
            connection.state = "running"
            db.commit()
        rejected = client.post(
            f"/netpay/gmail/connections/{connection_id}/sync",
            headers=_headers("gmail:d1:operator", "google-overlap-sync"),
            json={"backfill_days": 30},
        )
        assert rejected.status_code == 409
        assert rejected.json()["detail"]["code"] == "gmail_sync_in_progress"
    finally:
        app.dependency_overrides.pop(gmail_routes.gmail_provider, None)


def test_d1_changed_replay_is_quarantined_and_cursor_does_not_advance() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-conflict-account", _fixture(now)[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "conflict-connect"),
        json={
            "provider_account_id": "synthetic-conflict-account",
            "label_id": "LABEL_STORES",
            "credential_secret_ref": "synthetic-ref",
        },
    ).json()
    connection_id = connection["id"]
    first = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "conflict-sync-1"),
        json={},
    )
    assert first.status_code == 201
    cursor = first.json()["cursor_after"]
    DEFAULT_FAKE_GMAIL_PROVIDER.seed(
        "synthetic-conflict-account",
        [replace(_fixture(now)[0], body="changed synthetic body")],
    )
    conflict = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "conflict-sync-2"),
        json={},
    )
    assert conflict.status_code == 201
    assert conflict.json()["status"] == "partially_failed"
    assert conflict.json()["conflict_count"] == 1
    assert conflict.json()["cursor_after"] is None
    with app.state.yarvis.persistence.create_session() as db:
        item = db.scalar(
            select(NetpayGmailSourceItem).where(NetpayGmailSourceItem.gmail_message_id == "synthetic-message-001")
        )
        assert item is not None
        assert item.plain_excerpt != "changed synthetic body"
        assert item.conflict_fingerprint is not None
        assert (
            db.scalar(select(NetpayGmailConnection).where(NetpayGmailConnection.id == connection_id)).cursor == cursor
        )


def test_d1_label_validation_fails_closed() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-label-account", _fixture(now)[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "label-connect"),
        json={
            "provider_account_id": "synthetic-label-account",
            "label_id": "WRONG_LABEL",
            "credential_secret_ref": "synthetic-ref",
        },
    ).json()
    validation = client.post(
        f"/netpay/gmail/connections/{connection['id']}/validate",
        headers=_headers("gmail:d1:operator", "label-validate"),
    )
    assert validation.status_code == 422
    assert validation.json()["detail"]["code"] == "label_not_found"
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(NetpayGmailSourceItem)) is None


def test_d2_extracts_facts_correlates_cross_thread_and_preserves_non_inference() -> None:
    org_id, other_id, _, _ = _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed(
        "synthetic-d2-account",
        [
            GmailSourceMessage(
                message_id="synthetic-shipment-001",
                thread_id="synthetic-thread-shipment",
                received_at=now - timedelta(days=3),
                sender="synthetic.sender@example.invalid",
                recipient="netpay@example.invalid",
                subject="Detalle de Envío - Caso 00199130",
                body=(
                    "Producto: Rollo Individual 18 mts Netpay; Cantidad: 18; "
                    "Paquetería: FedEx; Guía: 878325984682; "
                    "Estado: Esperando recolección; Número de serie: vacío"
                ),
                label_ids=frozenset({"LABEL_NETPAY"}),
            ),
            GmailSourceMessage(
                message_id="synthetic-followup-001",
                thread_id="synthetic-thread-followup",
                received_at=now - timedelta(days=1),
                sender="synthetic.sender@example.invalid",
                recipient="netpay@example.invalid",
                subject="Seguimiento caso 00199130",
                body="Comercio: Sucursal sintética sin identificador verificable",
                label_ids=frozenset({"LABEL_NETPAY"}),
            ),
        ],
    )
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "d2-connect"),
        json={
            "provider_account_id": "synthetic-d2-account",
            "label_id": "LABEL_NETPAY",
            "credential_secret_ref": "synthetic-ref-d2",
        },
    ).json()
    first_sync = client.post(
        f"/netpay/gmail/connections/{connection['id']}/sync",
        headers=_headers("gmail:d1:operator", "d2-sync-1"),
        json={"backfill_days": 30},
    )
    assert first_sync.status_code == 201
    assert first_sync.json()["captured_count"] == 2

    candidates = client.get(
        "/netpay/gmail/candidates",
        headers=_headers("gmail:d1:operator", "d2-candidates"),
    )
    assert candidates.status_code == 200
    assert candidates.json()["total"] == 2
    shipment = next(item for item in candidates.json()["items"] if item["request_type"] == "consumable_shipment")
    assert shipment["ticket_references"] == ["00199130"]
    assert shipment["shipment_facts"] == {
        "carrier": "FedEx",
        "tracking_number": "878325984682",
        "reported_state": "Esperando recolección",
    }
    assert shipment["terminal_serials"] == []
    assert shipment["correlation_key"] == "ticket:00199130"
    assert len(shipment["related_candidate_ids"]) == 1
    assert "verified_commerce_identifier" in shipment["missing_data"]
    assert any(
        fact["value"] == "reported_state_only; delivery, activation and return remain unconfirmed"
        for fact in shipment["inferences"]
    )

    second_sync = client.post(
        f"/netpay/gmail/connections/{connection['id']}/sync",
        headers=_headers("gmail:d1:operator", "d2-sync-2"),
        json={"backfill_days": 30},
    )
    assert second_sync.status_code == 201
    assert second_sync.json()["captured_count"] == 0
    assert second_sync.json()["deduplicated_count"] == 2
    with app.state.yarvis.persistence.create_session() as db:
        assert (
            len(db.scalars(select(NetpayIntakeCandidate).where(NetpayIntakeCandidate.organization_id == org_id)).all())
            == 2
        )

    assert (
        client.get(
            f"/netpay/gmail/candidates/{shipment['id']}",
            headers={
                **_headers("gmail:d1:operator", "d2-foreign"),
                "X-Yarvis-Organization-Selector": str(other_id),
            },
        ).status_code
        == 404
    )


def test_d2_review_is_idempotent_and_final_disposition_is_immutable() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-review-account", _fixture(now)[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "review-connect"),
        json={
            "provider_account_id": "synthetic-review-account",
            "label_id": "LABEL_STORES",
            "credential_secret_ref": "synthetic-review-ref",
        },
    ).json()
    client.post(
        f"/netpay/gmail/connections/{connection['id']}/sync",
        headers=_headers("gmail:d1:operator", "review-sync"),
        json={},
    )
    candidate = client.get("/netpay/gmail/candidates", headers=_headers("gmail:d1:operator", "review-list")).json()[
        "items"
    ][0]
    payload = {"action": "reject", "reason": "synthetic fixture disposition"}
    reviewed = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/review",
        headers=_headers("gmail:d1:operator", "review-final"),
        json=payload,
    )
    replay = client.post(
        f"/netpay/gmail/candidates/{candidate['id']}/review",
        headers=_headers("gmail:d1:operator", "review-final"),
        json=payload,
    )
    assert reviewed.status_code == replay.status_code == 200
    assert replay.json() == reviewed.json()
    assert reviewed.json()["state"] == "rejected"
    assert (
        client.post(
            f"/netpay/gmail/candidates/{candidate['id']}/review",
            headers=_headers("gmail:d1:operator", "review-after-final"),
            json={"action": "edit", "priority": "high"},
        ).status_code
        == 409
    )


class _FakeOAuthCoordinator:
    def authorization_url(self, *, state: str, code_verifier: str) -> str:
        assert len(code_verifier) >= 43
        return f"https://accounts.example.invalid/authorize?state={state}&scope=gmail.readonly"

    def exchange(self, *, state: str, code: str, code_verifier: str) -> GoogleOAuthResult:
        assert state and code == "synthetic-code" and len(code_verifier) >= 43
        return GoogleOAuthResult(
            token_payload={
                "token": "synthetic-access-token",
                "refresh_token": "synthetic-refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "synthetic-client",
                "client_secret": "synthetic-secret",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            },
            email_address="pilot@example.invalid",
            history_id="synthetic-history-1",
            label_id="Label_1",
        )


def test_gate_a_oauth_state_pkce_expiry_replay_and_mailbox_binding(monkeypatch) -> None:
    org_id, _, _, _ = _setup()
    store = InMemoryGmailSecretStore()
    binding_ref = store.put("binding", {"expected_email": "pilot@example.invalid"})
    app.dependency_overrides[gmail_routes.gmail_secret_store] = lambda: store
    app.dependency_overrides[gmail_routes.gmail_oauth_coordinator] = _FakeOAuthCoordinator
    monkeypatch.setattr(
        gmail_routes,
        "get_settings",
        lambda: SimpleNamespace(
            gmail_mailbox_binding=binding_ref,
            gmail_post_connect_redirect_uri="http://127.0.0.1:5173/netpay-inbox/gmail",
        ),
    )
    try:
        started = client.post(
            "/netpay/gmail/oauth/start",
            headers=_headers("gmail:d1:operator", "oauth-start"),
        )
        assert started.status_code == 200
        state = parse_qs(urlparse(started.json()["authorization_url"]).query)["state"][0]
        callback = client.get(
            "/netpay/gmail/oauth/callback",
            params={"state": state, "code": "synthetic-code"},
            follow_redirects=False,
        )
        assert callback.status_code == 303
        assert callback.headers["location"].endswith("/netpay-inbox/gmail")
        replay = client.get(
            "/netpay/gmail/oauth/callback",
            params={"state": state, "code": "synthetic-code"},
            follow_redirects=False,
        )
        assert replay.status_code == 409
        attempt_secret_count = len([key for key in store.values if "/oauth-attempts/" in key])
        duplicate_start = client.post(
            "/netpay/gmail/oauth/start",
            headers=_headers("gmail:d1:operator", "oauth-duplicate-start"),
        )
        assert duplicate_start.status_code == 409
        assert duplicate_start.json()["detail"]["code"] == "gmail_connection_already_ready"
        assert len([key for key in store.values if "/oauth-attempts/" in key]) == attempt_secret_count
        with app.state.yarvis.persistence.create_session() as db:
            connection = db.scalar(select(NetpayGmailConnection).where(NetpayGmailConnection.organization_id == org_id))
            assert connection is not None
            assert connection.provider_kind == "google"
            assert connection.provider_account_id == "pilot@example.invalid"
            assert connection.credential_secret_ref.startswith("memory://netpay-gmail/")
            credential_reference = connection.credential_secret_ref
            db.delete(connection)
            db.commit()
        store.delete(credential_reference)

        expired = client.post(
            "/netpay/gmail/oauth/start",
            headers=_headers("gmail:d1:operator", "oauth-expired-start"),
        )
        expired_state = parse_qs(urlparse(expired.json()["authorization_url"]).query)["state"][0]
        with app.state.yarvis.persistence.create_session() as db:
            attempt = db.scalar(select(NetpayGmailOAuthAttempt).where(NetpayGmailOAuthAttempt.consumed_at.is_(None)))
            assert attempt is not None
            attempt.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        assert (
            client.get(
                "/netpay/gmail/oauth/callback",
                params={"state": expired_state, "code": "synthetic-code"},
                follow_redirects=False,
            ).status_code
            == 409
        )

        attempt_secret_count = len([key for key in store.values if "/oauth-attempts/" in key])
        mismatch_start = client.post(
            "/netpay/gmail/oauth/start",
            headers=_headers("gmail:d1:operator", "oauth-mismatch-start"),
        )
        mismatch_state = parse_qs(urlparse(mismatch_start.json()["authorization_url"]).query)["state"][0]
        store.put("binding", {"expected_email": "different@example.invalid"})
        credential_count = len([key for key in store.values if "/credentials/" in key])
        mismatch = client.get(
            "/netpay/gmail/oauth/callback",
            params={"state": mismatch_state, "code": "synthetic-code"},
            follow_redirects=False,
        )
        assert mismatch.status_code == 422
        assert mismatch.json()["detail"]["code"] == "mailbox_mismatch"
        assert (
            client.get(
                "/netpay/gmail/oauth/callback",
                params={"state": mismatch_state, "code": "synthetic-code"},
                follow_redirects=False,
            ).status_code
            == 409
        )
        assert len([key for key in store.values if "/credentials/" in key]) == credential_count
        assert len([key for key in store.values if "/oauth-attempts/" in key]) == attempt_secret_count
    finally:
        app.dependency_overrides.clear()


def _h2i_ready_candidate() -> tuple[str, dict, object, object]:
    org_id, foreign_org_id, _, _ = _setup()
    app.dependency_overrides[gmail_routes.gmail_provider] = lambda: DEFAULT_FAKE_GMAIL_PROVIDER
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-h2i", _fixture(datetime.now(timezone.utc))[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "h2i-connect"),
        json={"provider_account_id": "synthetic-h2i", "label_id": "LABEL_STORES", "credential_secret_ref": "synthetic"},
    )
    assert connection.status_code == 201
    sync = client.post(
        f"/netpay/gmail/connections/{connection.json()['id']}/sync",
        headers=_headers("gmail:d1:operator", "h2i-sync"),
        json={},
    )
    assert sync.status_code == 201
    candidate_id = client.get("/netpay/gmail/candidates", headers=_headers("gmail:d1:operator", "h2i-list")).json()[
        "items"
    ][0]["id"]
    qualification = client.post(
        f"/netpay/gmail/candidates/{candidate_id}/qualifications",
        headers=_headers("gmail:d1:operator", "h2i-qualify"),
        json={
            "applicant_kind": "persona_moral",
            "legal_person_name": {
                "value": "Empresa Sintética",
                "verification": "operator_reported",
                "source_field": "body",
            },
            "representative_name": None,
            "brand_name": None,
            "requested_products": ["tpv", "ecommerce"],
            "branches": [
                {
                    "draft_key": "one", "name": "Sucursal Uno", "requested_products": ["tpv"],
                    "verification": "operator_reported", "source_field": "body",
                },
                {
                    "draft_key": "two", "name": "Sucursal Dos", "requested_products": ["ecommerce"],
                    "verification": "operator_reported", "source_field": "body",
                },
            ],
            "rationale": "Synthetic H2-I review",
        },
    )
    assert qualification.status_code == 201
    preview = client.get(
        f"/netpay/gmail/candidates/{candidate_id}/commercial-intake-preview",
        headers=_headers("gmail:d1:operator", "h2i-preview"),
    )
    assert preview.status_code == 200
    assert preview.json()["qualification_id"] == qualification.json()["id"]
    payload = {key: preview.json()[key] for key in (
        "qualification_id", "provisional_company_name", "provisional_contact_name",
        "product_interest", "summary", "priority", "next_action",
    )}
    return candidate_id, payload, org_id, foreign_org_id


def test_h2i_payload_conflict_tenant_isolation_and_owner_delegation() -> None:
    candidate_id, payload, org_id, foreign_org_id = _h2i_ready_candidate()
    path = f"/netpay/gmail/candidates/{candidate_id}/commercial-intake"
    try:
        foreign = client.post(path, headers=_headers("gmail:d1:foreign", "h2i-foreign"), json=payload)
        assert foreign.status_code == 404
        with app.state.yarvis.persistence.create_session() as db:
            assert db.scalar(select(func.count()).select_from(CommercialIntakeItem)) == 0
        first = client.post(path, headers=_headers("gmail:d1:operator", "h2i-specific"), json=payload)
        assert first.status_code == 201, first.text
        replay = client.post(path, headers=_headers("gmail:d1:operator", "h2i-specific"), json=payload)
        assert replay.status_code == 201 and replay.json() == first.json()
        changed = client.post(
            path, headers=_headers("gmail:d1:operator", "h2i-specific"),
            json={**payload, "summary": "Changed synthetic payload"},
        )
        assert changed.status_code == 409
        with app.state.yarvis.persistence.create_session() as db:
            assert db.scalar(select(func.count()).select_from(CommercialIntakeItem)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayCandidateCommercialIntakeTrace)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayServiceCase)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayClient)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayCompany)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayBranch)) == 0
            assert db.scalar(select(func.count()).select_from(CommercialIntakeItem).where(
                CommercialIntakeItem.organization_id == foreign_org_id,
            )) == 0
            assert db.scalar(select(func.count()).select_from(CommercialIntakeCommandReceipt).where(
                CommercialIntakeCommandReceipt.organization_id == org_id,
                CommercialIntakeCommandReceipt.command_type == "IC-NETPAY-CMD-020",
            )) == 1
            owner_receipt = db.scalar(select(CommercialIntakeCommandReceipt).where(
                CommercialIntakeCommandReceipt.organization_id == org_id,
                CommercialIntakeCommandReceipt.command_type == "IC-NETPAY-CMD-020",
            ))
            assert owner_receipt is not None
            assert str(owner_receipt.result_resource_id) == first.json()["commercial_intake_id"]
            assert db.scalar(select(func.count()).select_from(DomainEvent).where(
                DomainEvent.organization_id == org_id,
                DomainEvent.event_type == "netpay_commercial_intake.created",
            )) == 1
    finally:
        app.dependency_overrides.clear()


def test_h2i_two_real_concurrent_promotions_create_one_owner_record(monkeypatch) -> None:
    candidate_id, payload, _, _ = _h2i_ready_candidate()
    path = f"/netpay/gmail/candidates/{candidate_id}/commercial-intake"
    barrier = Barrier(2)
    original_receipt = gmail_routes._receipt

    def concurrent_receipt(*args, **kwargs):
        result = original_receipt(*args, **kwargs)
        if kwargs.get("command") == "IC-NETPAY-CMD-039" and result is None:
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(gmail_routes, "_receipt", concurrent_receipt)
    try:
        def submit(key: str):
            return client.post(path, headers=_headers("gmail:d1:operator", key), json=payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(submit, f"h2i-concurrent-{index}") for index in range(2)]
            results = [future.result(timeout=20) for future in futures]
        assert sorted(result.status_code for result in results) == [201, 409]
        with app.state.yarvis.persistence.create_session() as db:
            assert db.scalar(select(func.count()).select_from(CommercialIntakeItem)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayCandidateCommercialIntakeTrace)) == 1
            assert db.scalar(select(func.count()).select_from(CommercialIntakeCommandReceipt)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayGmailCommandReceipt).where(
                NetpayGmailCommandReceipt.command_type == "IC-NETPAY-CMD-039",
            )) == 1
            assert db.scalar(select(func.count()).select_from(DomainEvent).where(
                DomainEvent.event_type == "netpay_commercial_intake.created",
            )) == 1
            assert db.scalar(select(func.count()).select_from(NetpayServiceCase)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayClient)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayCompany)) == 0
            assert db.scalar(select(func.count()).select_from(NetpayBranch)) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("changed_payload, expected_codes", [
    (False, [201, 201]),
    (True, [201, 409]),
])
def test_h2i_concurrent_same_key_replay_or_payload_conflict(monkeypatch, changed_payload, expected_codes) -> None:
    candidate_id, payload, _, _ = _h2i_ready_candidate()
    path = f"/netpay/gmail/candidates/{candidate_id}/commercial-intake"
    barrier = Barrier(2)
    original_receipt = gmail_routes._receipt

    def concurrent_receipt(*args, **kwargs):
        result = original_receipt(*args, **kwargs)
        if kwargs.get("command") == "IC-NETPAY-CMD-039" and result is None:
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(gmail_routes, "_receipt", concurrent_receipt)
    try:
        def submit(body):
            return client.post(path, headers=_headers("gmail:d1:operator", "h2i-same-key"), json=body)

        second_payload = {**payload, "summary": "Different synthetic summary"} if changed_payload else payload
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(submit, body) for body in (payload, second_payload)]
            results = [future.result(timeout=20) for future in futures]
        assert sorted(result.status_code for result in results) == expected_codes
        if not changed_payload:
            assert results[0].json() == results[1].json()
        with app.state.yarvis.persistence.create_session() as db:
            assert db.scalar(select(func.count()).select_from(CommercialIntakeItem)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayCandidateCommercialIntakeTrace)) == 1
            assert db.scalar(select(func.count()).select_from(CommercialIntakeCommandReceipt)) == 1
            assert db.scalar(select(func.count()).select_from(NetpayGmailCommandReceipt).where(
                NetpayGmailCommandReceipt.command_type == "IC-NETPAY-CMD-039",
            )) == 1
    finally:
        app.dependency_overrides.clear()

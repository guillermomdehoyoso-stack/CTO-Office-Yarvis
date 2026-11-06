from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_netpay_operational_data import setup_data

from yarvis_api.application.authority import IdentityAuthorityEnvelope, permissions_for_role
from yarvis_api.main import app
from yarvis_api.models.netpay_equipment_identity import (
    NetpayEquipmentEvidence,
    NetpayEquipmentIdentity,
    NetpayStoreEquipmentLink,
)
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.netpay_protection_case import (
    NetpayProtectionCase,
    NetpayProtectionCaseHistory,
    NetpayProtectionCommandReceipt,
    NetpayProtectionSensitiveAccess,
)
from yarvis_api.services.netpay_protection_cases import (
    ProtectionCaseError,
    assign_and_plan,
    decide_recovery_path,
    list_cases,
    open_case,
    record_contact_attempt,
    resolve_store_equipment_link,
    retrieve_case,
    retrieve_store_equipment_identity,
)


def authority(org, actor, role="netpay_operations_operator"):
    return IdentityAuthorityEnvelope(actor, org, permissions_for_role(role), "synthetic-test", "c3-correlation")


def fixture_link(*, confirmed=False, pii=False):
    store_id = setup_data()
    with app.state.yarvis.persistence.create_session() as db:
        store = db.get(NetpayStoreReference, store_id)
        if pii:
            branch = db.get(NetpayBranch, store.branch_id)
            company = db.get(NetpayCompany, branch.company_id)
            client = db.get(NetpayClient, company.client_id)
            client.primary_contact_name = "Synthetic Person"
            client.primary_email = "synthetic@example.invalid"
            client.primary_phone = "+520000000000"
        terminal = NetpayEquipmentIdentity(
            organization_id=store.organization_id,
            identity_kind="terminal",
            original_value="SYN-T",
            normalized_value="syn-t",
            normalization_method="synthetic_exact",
        )
        serial = NetpayEquipmentIdentity(
            organization_id=store.organization_id,
            identity_kind="serial",
            original_value="SYN-S",
            normalized_value="syn-s",
            normalization_method="synthetic_exact",
        )
        db.add_all((terminal, serial))
        db.flush()
        evidence = NetpayEquipmentEvidence(
            organization_id=store.organization_id,
            identity_id=serial.id,
            source_profile="synthetic_c3_temporality_v1",
            source_batch_reference="synthetic_fixture",
            source_hash="f" * 64,
            source_sheet="synthetic",
            source_row_reference="1",
            original_value="SYN-S",
            normalized_value="syn-s",
            normalization_method="synthetic_exact",
        )
        db.add(evidence)
        db.flush()
        link = NetpayStoreEquipmentLink(
            organization_id=store.organization_id,
            store_reference_id=store.id,
            terminal_identity_id=terminal.id,
            serial_identity_id=serial.id,
            evidence_id=evidence.id,
            candidate_store_reference_ids=[],
            resolution_status="confirmed" if confirmed else "pending",
            aggregate_version=1,
        )
        db.add(link)
        db.commit()
        return store.organization_id, store.created_by_principal_id, link.id


def test_synthetic_temporality_is_strict_and_real_evidence_is_not_accepted():
    org, actor, link_id = fixture_link()
    auth = authority(org, actor)
    now = datetime.now(timezone.utc)
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(ProtectionCaseError, match="invalid_temporal_interval"):
            resolve_store_equipment_link(
                db,
                authority=auth,
                link_id=link_id,
                expected_version=1,
                observed_at=now,
                valid_from=now,
                valid_to=now,
                idempotency_key="bad-window",
                local_disposable=True,
            )
        with pytest.raises(ProtectionCaseError, match="synthetic_profile_forbidden"):
            resolve_store_equipment_link(
                db,
                authority=auth,
                link_id=link_id,
                expected_version=1,
                observed_at=now,
                valid_from=now - timedelta(days=1),
                valid_to=now + timedelta(days=1),
                idempotency_key="not-local",
                local_disposable=False,
            )
        result = resolve_store_equipment_link(
            db,
            authority=auth,
            link_id=link_id,
            expected_version=1,
            observed_at=now,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            idempotency_key="valid-window",
            local_disposable=True,
        )
        assert result == {"result": "transition_applied", "link_id": str(link_id), "version": 2, "status": "confirmed"}
        assert (
            resolve_store_equipment_link(
                db,
                authority=auth,
                link_id=link_id,
                expected_version=1,
                observed_at=now,
                valid_from=now - timedelta(days=1),
                valid_to=now + timedelta(days=1),
                idempotency_key="valid-window",
                local_disposable=True,
            )
            == result
        )


def test_case_lifecycle_replay_catalogs_queue_and_no_c4_state():
    org, actor, link_id = fixture_link(confirmed=True)
    auth = authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        created = open_case(
            db,
            authority=auth,
            source_kind="link",
            source_id=link_id,
            cause_code="no_usage",
            expected_source_version=1,
            idempotency_key="open",
            correlation_id="corr",
        )
        assert created["status"] == "contact_pending"
        assert (
            open_case(
                db,
                authority=auth,
                source_kind="link",
                source_id=link_id,
                cause_code="no_usage",
                expected_source_version=1,
                idempotency_key="open",
                correlation_id="corr",
            )
            == created
        )
        with pytest.raises(ProtectionCaseError, match="idempotency_conflict"):
            open_case(
                db,
                authority=auth,
                source_kind="link",
                source_id=link_id,
                cause_code="pending_temporality",
                expected_source_version=1,
                idempotency_key="open",
                correlation_id="corr",
            )
        with pytest.raises(ProtectionCaseError, match="unsupported_catalog_value"):
            open_case(
                db,
                authority=auth,
                source_kind="link",
                source_id=link_id,
                cause_code="free text",
                expected_source_version=1,
                idempotency_key="bad",
                correlation_id="corr",
            )
        case_id = created["case_id"]
        planned = assign_and_plan(
            db,
            authority=auth,
            case_id=case_id,
            expected_version=1,
            assigned_principal_id=actor,
            next_action_code="contact_merchant",
            commitment_at=None,
            target_status="ready_to_contact",
            idempotency_key="plan",
            correlation_id="corr",
        )
        assert planned["version"] == 2
        stale = assign_and_plan(
            db,
            authority=auth,
            case_id=case_id,
            expected_version=1,
            assigned_principal_id=actor,
            next_action_code="contact_merchant",
            commitment_at=None,
            target_status="ready_to_contact",
            idempotency_key="stale-plan",
            correlation_id="corr",
        )
        assert stale == {"result": "stale_version", "case_id": case_id, "version": 2}
        assert (
            assign_and_plan(
                db,
                authority=auth,
                case_id=case_id,
                expected_version=1,
                assigned_principal_id=actor,
                next_action_code="contact_merchant",
                commitment_at=None,
                target_status="ready_to_contact",
                idempotency_key="stale-plan",
                correlation_id="corr",
            )
            == stale
        )
        assert db.scalar(select(func.count()).select_from(NetpayProtectionCaseHistory)) == 2
        queue = list_cases(db, authority=auth)
        assert queue["items"][0]["status"] == "ready_to_contact"
        assert "email" not in str(queue).lower() and "phone" not in str(queue).lower()
        with pytest.raises(ProtectionCaseError, match="invalid_transition"):
            decide_recovery_path(
                db,
                authority=auth,
                case_id=case_id,
                expected_version=2,
                recovery_path_code="reactivate",
                idempotency_key="premature",
                correlation_id="corr",
            )


def test_protected_contact_requires_server_permissions_and_is_not_persisted():
    org, actor, link_id = fixture_link(confirmed=True, pii=True)
    ops = authority(org, actor)
    reader = authority(org, actor, "netpay_inbox_portfolio_reader")
    with app.state.yarvis.persistence.create_session() as db:
        created = open_case(
            db,
            authority=ops,
            source_kind="link",
            source_id=link_id,
            cause_code="no_usage",
            expected_source_version=1,
            idempotency_key="open-contact",
            correlation_id="corr",
        )
        planned = assign_and_plan(
            db,
            authority=ops,
            case_id=created["case_id"],
            expected_version=1,
            assigned_principal_id=actor,
            next_action_code="contact_merchant",
            commitment_at=None,
            target_status="ready_to_contact",
            idempotency_key="plan-contact",
            correlation_id="corr",
        )
        with pytest.raises(ProtectionCaseError, match="forbidden"):
            retrieve_case(
                db,
                authority=reader,
                case_id=created["case_id"],
                include_contact=True,
                purpose_code="merchant_recovery_contact",
            )
        with pytest.raises(ProtectionCaseError, match="unsupported_catalog_value"):
            retrieve_case(db, authority=ops, case_id=created["case_id"], include_contact=True, purpose_code="free text")
        detail = retrieve_case(
            db,
            authority=ops,
            case_id=created["case_id"],
            include_contact=True,
            purpose_code="merchant_recovery_contact",
        )
        assert detail["contact"]["email"] == "synthetic@example.invalid"
        client = db.scalar(select(NetpayClient).where(NetpayClient.organization_id == org))
        client.primary_email = "updated@example.invalid"
        db.flush()
        with pytest.raises(ProtectionCaseError, match="contact_reference_stale"):
            record_contact_attempt(
                db,
                authority=ops,
                case_id=created["case_id"],
                expected_version=planned["version"],
                channel_code="email",
                result_code="reached",
                access_reference=detail["contact_access_reference"],
                idempotency_key="stale-contact",
                correlation_id="corr",
            )
        detail = retrieve_case(
            db,
            authority=ops,
            case_id=created["case_id"],
            include_contact=True,
            purpose_code="merchant_recovery_contact",
        )
        attempted = record_contact_attempt(
            db,
            authority=ops,
            case_id=created["case_id"],
            expected_version=planned["version"],
            channel_code="email",
            result_code="reached",
            access_reference=detail["contact_access_reference"],
            idempotency_key="attempt",
            correlation_id="corr",
        )
        assert attempted["status"] == "contact_attempted"
        persisted = " ".join(
            str(value)
            for model in (NetpayProtectionCase, NetpayProtectionCaseHistory, NetpayProtectionCommandReceipt)
            for value in db.scalars(select(model)).all()
        )
        assert "synthetic@example.invalid" not in persisted
        assert "updated@example.invalid" not in persisted
        assert "+520000000000" not in persisted
        assert db.scalar(select(func.count()).select_from(NetpayProtectionSensitiveAccess)) == 2


def test_distinct_keys_concurrently_open_one_case_and_safe_receipts():
    org, actor, link_id = fixture_link(confirmed=True)
    auth = authority(org, actor)

    def invoke(index):
        with app.state.yarvis.persistence.create_session() as db:
            result = open_case(
                db,
                authority=auth,
                source_kind="link",
                source_id=link_id,
                cause_code="no_usage",
                expected_source_version=1,
                idempotency_key=f"race-{index}",
                correlation_id="corr",
            )
            db.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(invoke, range(2)))
    assert sorted(result["result"] for result in results) == ["case_already_exists", "created"]
    assert len({result["case_id"] for result in results}) == 1
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(NetpayProtectionCase)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayProtectionCaseHistory)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayProtectionCommandReceipt)) == 2


def test_queries_conceal_foreign_tenant_and_identity_is_minimized():
    org, actor, link_id = fixture_link()
    auth = authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        identity = retrieve_store_equipment_identity(db, authority=auth, source_kind="link", source_id=link_id)
        assert identity["has_terminal"] and identity["has_serial"] and not identity["has_mid"]
        foreign = IdentityAuthorityEnvelope(
            uuid4(), uuid4(), permissions_for_role("netpay_operations_operator"), "synthetic-test", "foreign"
        )
        with pytest.raises(ProtectionCaseError, match="resource_not_found"):
            retrieve_store_equipment_identity(db, authority=foreign, source_kind="link", source_id=link_id)


def test_case_history_is_database_append_only():
    org, actor, link_id = fixture_link(confirmed=True)
    with app.state.yarvis.persistence.create_session() as db:
        open_case(
            db,
            authority=authority(org, actor),
            source_kind="link",
            source_id=link_id,
            cause_code="no_usage",
            expected_source_version=1,
            idempotency_key="append-only",
            correlation_id="corr",
        )
        db.commit()
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(
                text(
                    "UPDATE netpay_protection_case_history "
                    "SET action_code = 'mutated'"
                )
            )
        db.rollback()
        history = db.scalar(select(NetpayProtectionCaseHistory))
        assert history is not None
        assert history.action_code == "case_opened"

        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text("DELETE FROM netpay_protection_case_history"))
        db.rollback()
        history = db.scalar(select(NetpayProtectionCaseHistory))
        assert history is not None
        assert history.action_code == "case_opened"
        assert db.scalar(select(func.count()).select_from(NetpayProtectionCaseHistory)) == 1

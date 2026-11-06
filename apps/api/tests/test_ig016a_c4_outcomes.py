from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_netpay_operational_data import setup_data

from yarvis_api.application.authority import IdentityAuthorityEnvelope, permissions_for_role
from yarvis_api.main import app
from yarvis_api.models.netpay_master import NetpayStoreReference
from yarvis_api.models.netpay_protection_case import (
    NetpayProtectionCase,
    NetpayProtectionFinancialSnapshot,
    NetpayProtectionOutcomeAssessment,
    NetpayProtectionOutcomeEvidence,
    NetpayProtectionOutcomeReceipt,
)
from yarvis_api.services.netpay_protection_cases import ProtectionCaseError
from yarvis_api.services.netpay_protection_outcomes import (
    close_protection_case,
    record_outcome_evidence,
    retrieve_outcome_assessment,
)


def _authority(org, actor, role="netpay_operations_operator"):
    return IdentityAuthorityEnvelope(actor, org, permissions_for_role(role), "synthetic-test", "c4-correlation")


def _case(status="monitoring"):
    store_id = setup_data()
    with app.state.yarvis.persistence.create_session() as db:
        store = db.get(NetpayStoreReference, store_id)
        case = NetpayProtectionCase(
            organization_id=store.organization_id,
            source_kind="link",
            source_id=uuid4(),
            store_reference_id=store.id,
            cause_code="no_usage",
            status=status,
            aggregate_version=1,
            terminal_at=datetime.now(timezone.utc) if status == "unrecoverable" else None,
        )
        db.add(case)
        db.commit()
        return store.organization_id, store.created_by_principal_id, case.id


def _times():
    now = datetime.now(timezone.utc)
    return {
        "valid_from": now - timedelta(days=4),
        "occurred_at": now - timedelta(days=2),
        "observed_at": now - timedelta(days=1),
        "valid_to": now + timedelta(days=1),
    }


def _record(db, auth, case_id, *, version=1, key="outcome", supersedes=None, **overrides):
    values = {
        "authority": auth,
        "case_id": case_id,
        "expected_case_version": version,
        "profile_version": "synthetic_c4_activity_v1",
        "evidence_kind": "activity",
        "source_reference": "synthetic:activity:1",
        "identity_scope": "equipment_exact",
        "idempotency_key": key,
        "correlation_id": "corr",
        "local_disposable": True,
        "supersedes_evidence_id": supersedes,
        **_times(),
    }
    values.update(overrides)
    return record_outcome_evidence(db, **values)


def _financial(
    db,
    auth,
    case_id,
    *,
    version,
    supersedes,
    key="financial",
    components=None,
    category="recovered_amount_supported",
):
    return _record(
        db,
        auth,
        case_id,
        version=version,
        key=key,
        supersedes=supersedes,
        profile_version="synthetic_c4_financial_effect_v1",
        evidence_kind="financial",
        source_reference="synthetic:financial:1",
        identity_scope="equipment_exact",
        period_key="2026-10",
        financial_category=category,
        financial_certainty="supported" if category != "avoided_penalty_projected" else "projected",
        financial_components=components
        or [
            {"fingerprint": "penalty-1", "category": "penalty", "amount": "-10.005", "currency": "MXN"},
            {"fingerprint": "credit-1", "category": "credit", "amount": "12.00", "currency": "MXN"},
        ],
    )


def test_closed_profiles_reject_real_authority_and_temporal_errors():
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(ProtectionCaseError, match="synthetic_profile_forbidden"):
            _record(db, auth, case_id, local_disposable=False)
        with pytest.raises(ProtectionCaseError, match="unsupported_profile"):
            _record(db, auth, case_id, profile_version="real_source_v1")
        now = datetime.now(timezone.utc)
        with pytest.raises(ProtectionCaseError, match="invalid_temporal_interval"):
            _record(db, auth, case_id, occurred_at=now, observed_at=now, valid_from=now, valid_to=now)
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeEvidence)) == 0


def test_verified_financial_closure_replay_rounding_and_conflict_are_atomic():
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        operational = _record(db, auth, case_id)
        financial = _financial(db, auth, case_id, version=2, supersedes=operational["evidence_id"])
        assert financial["amount"] == "10.00"
        closed = close_protection_case(
            db,
            authority=auth,
            case_id=case_id,
            expected_case_version=2,
            closure_kind="verified_with_financial_effect",
            gap_reason=None,
            idempotency_key="close",
            correlation_id="corr",
        )
        assert closed["result"] == "closed"
        assert (
            close_protection_case(
                db,
                authority=auth,
                case_id=case_id,
                expected_case_version=2,
                closure_kind="verified_with_financial_effect",
                gap_reason=None,
                idempotency_key="close",
                correlation_id="corr",
            )
            == closed
        )
        conflict = close_protection_case(
            db,
            authority=auth,
            case_id=case_id,
            expected_case_version=2,
            closure_kind="closed_with_evidence_gap",
            gap_reason="missing_operational_evidence",
            idempotency_key="close",
            correlation_id="corr",
        )
        assert conflict == {"result": "idempotency_conflict"}
        assert db.get(NetpayProtectionCase, case_id).aggregate_version == 3
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeEvidence)) == 2
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeReceipt)) == 4


@pytest.mark.parametrize(
    ("status", "kind", "gap", "prepare", "expected_error"),
    [
        ("monitoring", "verified_with_financial_effect", None, False, "operational_outcome_required"),
        ("monitoring", "verified_financial_pending", "financial_window_pending", False, "operational_outcome_required"),
        ("monitoring", "closed_with_evidence_gap", None, False, "evidence_gap_required"),
        ("monitoring", "not_recoverable", "not_recoverable", False, "not_recoverable_reason_required"),
    ],
)
def test_each_closure_kind_has_deterministic_rejection(status, kind, gap, prepare, expected_error):
    org, actor, case_id = _case(status)
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(ProtectionCaseError, match=expected_error):
            close_protection_case(
                db,
                authority=_authority(org, actor),
                case_id=case_id,
                expected_case_version=1,
                closure_kind=kind,
                gap_reason=gap,
                idempotency_key=f"reject-{kind}",
                correlation_id="corr",
            )
        assert db.get(NetpayProtectionCase, case_id).status == status


@pytest.mark.parametrize(
    ("status", "kind", "gap", "operational"),
    (
        ("reactivation_agreed", "verified_financial_pending", "financial_window_pending", True),
        ("monitoring", "closed_with_evidence_gap", "missing_operational_evidence", False),
        ("unrecoverable", "not_recoverable", "not_recoverable", False),
    ),
)
def test_each_nonfinancial_closure_kind_is_allowed(status, kind, gap, operational):
    org, actor, case_id = _case(status)
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        version = 1
        if operational:
            _record(db, auth, case_id, key=f"operation-{kind}")
            version = 2
        result = close_protection_case(
            db,
            authority=auth,
            case_id=case_id,
            expected_case_version=version,
            closure_kind=kind,
            gap_reason=gap,
            idempotency_key=f"close-{kind}",
            correlation_id="corr",
        )
        assert result["closure_kind"] == kind


def test_post_close_supersession_marks_stale_and_rejects_branch_cycle_and_cross_tenant():
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        original = _record(db, auth, case_id)
        close_protection_case(
            db,
            authority=auth,
            case_id=case_id,
            expected_case_version=2,
            closure_kind="verified_financial_pending",
            gap_reason="financial_window_pending",
            idempotency_key="close-stale",
            correlation_id="corr",
        )
        corrected = _record(
            db,
            auth,
            case_id,
            version=3,
            key="correction",
            supersedes=original["evidence_id"],
            source_reference="synthetic:activity:corrected",
        )
        detail = retrieve_outcome_assessment(db, authority=auth, case_id=case_id, include_evidence=True)
        assert detail["assessment_state"] == "assessment_stale"
        assert detail["evidence"]["evidence_id"] == corrected["evidence_id"]
        with pytest.raises(ProtectionCaseError, match="supersession_conflict"):
            _record(db, auth, case_id, version=3, key="branch", supersedes=original["evidence_id"])
        old_id = original["evidence_id"]
        with pytest.raises(ProtectionCaseError, match="invalid_supersession_chain"):
            _record(db, auth, case_id, version=3, key="cycle", supersedes=old_id, evidence_id=old_id)

    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(ProtectionCaseError, match="resource_not_found"):
            _record(
                db,
                _authority(uuid4(), uuid4()),
                case_id,
                key="cross-tenant",
                supersedes=original["evidence_id"],
            )


@pytest.mark.parametrize(
    "components",
    [
        [
            {"fingerprint": "same", "category": "penalty", "amount": "-5", "currency": "MXN"},
            {"fingerprint": "same", "category": "credit", "amount": "5", "currency": "MXN"},
        ],
        [
            {"fingerprint": "root", "category": "penalty", "amount": "-5", "currency": "MXN"},
            {
                "fingerprint": "derived",
                "derived_from": ["root"],
                "category": "credit",
                "amount": "5",
                "currency": "MXN",
            },
        ],
    ],
)
def test_direct_and_transitive_double_counting_leave_no_partial_mutation(components):
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        operation = _record(db, auth, case_id)
        before = db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeEvidence))
        with pytest.raises(ProtectionCaseError, match="overlapping_financial_component"):
            _financial(db, auth, case_id, version=2, supersedes=operation["evidence_id"], components=components)
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeEvidence)) == before
        assert db.scalar(select(func.count()).select_from(NetpayProtectionFinancialSnapshot)) == 0


def test_concurrent_supersession_has_one_winner_and_no_partial_branch():
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        original = _record(db, auth, case_id)
        close_protection_case(
            db,
            authority=auth,
            case_id=case_id,
            expected_case_version=2,
            closure_kind="verified_financial_pending",
            gap_reason="financial_window_pending",
            idempotency_key="concurrent-close",
            correlation_id="corr",
        )
        db.commit()

    def invoke(index):
        with app.state.yarvis.persistence.create_session() as db:
            try:
                result = _record(
                    db,
                    auth,
                    case_id,
                    version=3,
                    key=f"concurrent-correction-{index}",
                    supersedes=original["evidence_id"],
                    source_reference=f"synthetic:correction:{index}",
                )
                db.commit()
                return result["result"]
            except ProtectionCaseError as error:
                db.rollback()
                return str(error)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(invoke, range(2)))
    assert results == ["recorded", "supersession_conflict"]
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeEvidence)) == 2
        assert db.scalar(select(func.count()).select_from(NetpayProtectionOutcomeAssessment)) == 2


def test_query_conceals_foreign_tenant_and_append_only_tables_reject_update_delete():
    org, actor, case_id = _case("reactivation_agreed")
    auth = _authority(org, actor)
    with app.state.yarvis.persistence.create_session() as db:
        operation = _record(db, auth, case_id)
        _financial(db, auth, case_id, version=2, supersedes=operation["evidence_id"])
        db.commit()
        foreign = _authority(uuid4(), uuid4())
        with pytest.raises(ProtectionCaseError, match="resource_not_found"):
            retrieve_outcome_assessment(db, authority=foreign, case_id=case_id)
        for table in (
            "netpay_protection_outcome_evidence",
            "netpay_protection_outcome_assessments",
            "netpay_protection_financial_snapshots",
        ):
            with pytest.raises(DBAPIError, match="append-only"):
                db.execute(text(f"UPDATE {table} SET created_at = created_at"))
            db.rollback()
            before = db.scalar(text(f"SELECT count(*) FROM {table}"))
            with pytest.raises(DBAPIError, match="append-only"):
                db.execute(text(f"DELETE FROM {table}"))
            db.rollback()
            assert db.scalar(text(f"SELECT count(*) FROM {table}")) == before

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from yarvis_api.schemas.historical_evidence import ProfitabilitySummary, TransactionHistoricalAggregate
from yarvis_api.database import SessionLocal
from yarvis_api.schemas.store_intelligence import HumanDecisionEvent, HumanDecisionInput, RecoveryQueueFilters
from yarvis_api.services.recovery_queue_service import append_human_decision, apply_recommendation, build_recovery_queue, is_pending, load_human_decisions
from yarvis_api.services.store_profile_builder import build_store_profiles


NOW = datetime(2025, 2, 1, tzinfo=timezone.utc)


def _current(store_id, field, value, report="netpay_inactive_stores_report", offset=0):
    observation = SimpleNamespace(subject_reference=store_id, field_name=field, observed_value={"value": value}, observed_at=NOW + timedelta(minutes=offset), source_reference=f"row:{offset + 1}", provenance={"worksheet": "Synthetic"}, document_id=None)
    document = SimpleNamespace(id=None, detected_report_type=report)
    return observation, document


def _transaction(store_id="S1", period="2025-01"):
    return TransactionHistoricalAggregate(store_id, period, Decimal("2"), Decimal("10"), Decimal("1"), Decimal("1"), None, [], ["A", "B"], [], [], [], [], [], 1, ["tx:row:2"], [])


def _profit(store_id="S1", period="2025-01", branch="Observed"):
    return ProfitabilitySummary(store_id, period, {"profitability": Decimal("1"), "rent_paid": Decimal("2"), "total_commissions": Decimal("3"), "branch_name_observed": branch}, ["profit:row:2"])


def test_store_id_is_the_only_consolidation_key_and_current_wins():
    evidence = [_current("S1", "store_name", "same", offset=1), _current("S2", "store_name", "same", offset=1), _current("S1", "operational_status", "current", offset=2), _current("S1", "months_no_use", 2, offset=2), _current("S1", "client_id", "C1", offset=2)]
    profiles = build_store_profiles(current_evidence=evidence, transaction_aggregates=[_transaction("S1"), _transaction("S2")], profitability_summaries=[_profit("S1")])
    assert [profile.store_id for profile in profiles] == ["S1", "S2"]
    first = profiles[0]
    assert first.current_operational_status == "current" and first.months_no_use == 2
    assert first.historical_transaction_volume == Decimal("10")
    assert first.current_source_alert is None


def test_unconfirmed_is_not_an_input_and_conflicts_require_review():
    evidence = [_current("S1", "store_name", "A", offset=1), _current("S1", "store_name", "B", offset=1), _current("S1", "months_no_use", 1, offset=1)]
    profile = build_store_profiles(current_evidence=evidence)[0]
    assert profile.current_store_name is None
    assert profile.evidence_completeness == "review_required"
    assert "current_evidence_conflict" in profile.evidence_completeness_reasons
    candidate_observation, candidate_document = _current("S2", "months_no_use", 4)
    candidate_observation.confirmation_status = "candidate"
    assert build_store_profiles(current_evidence=[(candidate_observation, candidate_document)]) == []


def test_recommendation_precedence_and_historical_only_safety():
    current = [_current("S1", "source_alert", "Sin Activación"), _current("S1", "operational_status", "Bloqueado terminal incorrecta"), _current("S1", "months_no_use", 4)]
    profile = build_store_profiles(current_evidence=current, transaction_aggregates=[_transaction()], profitability_summaries=[_profit()])[0]
    evaluated = apply_recommendation(profile)
    assert evaluated.recommended_action == "complete_activation" and evaluated.requires_human_review
    assert "2025-01" in evaluated.recommendation_reason
    historical_only = build_store_profiles(transaction_aggregates=[_transaction("S2")])[0]
    assert apply_recommendation(historical_only).recommended_action is None


def test_terminal_candidate_and_watch_are_secondary_and_deterministic():
    cancellation = build_store_profiles(current_evidence=[_current("S1", "source_alert", "Cobrar Renta o Cancelar"), _current("S1", "months_no_use", 2)])[0]
    evaluated = apply_recommendation(cancellation)
    assert evaluated.recommended_action == "review_rent_or_cancellation"
    assert evaluated.terminal_recovery_candidate and "assignment is not confirmed" in evaluated.terminal_recovery_reason
    watch = build_store_profiles(current_evidence=[_current("S2", "months_no_use", 1)])[0]
    assert not is_pending(apply_recommendation(watch))


def test_filters_order_pending_and_decision_state():
    profiles = build_store_profiles(current_evidence=[
        _current("S2", "months_no_use", 2), _current("S1", "source_alert", "Sin Activación"),
        _current("S1", "months_no_use", 2), _current("S3", "months_no_use", 4),
    ], transaction_aggregates=[_transaction("S3")])
    resolved = HumanDecisionEvent("event", "S3", "contact_for_reactivation", "resolved", None, None, None, NOW)
    profiles = build_store_profiles(current_evidence=[
        _current("S2", "months_no_use", 2), _current("S1", "source_alert", "Sin Activación"), _current("S1", "months_no_use", 2), _current("S3", "months_no_use", 4),
    ], human_decisions=[resolved], transaction_aggregates=[_transaction("S3")])
    result = build_recovery_queue(profiles)
    assert [profile.store_id for profile in result.profiles][:2] == ["S1", "S2"]
    assert result.pending_profiles == 2 and result.counts_by_action == {"complete_activation": 1, "contact_for_reactivation": 1}
    filtered = build_recovery_queue(profiles, RecoveryQueueFilters(minimum_months_no_use=4, pending_action=False))
    assert [profile.store_id for profile in filtered.profiles] == ["S3"]


def test_no_current_name_fallback_and_completeness_reasons_are_explicit():
    profile = build_store_profiles(transaction_aggregates=[_transaction("S1")], profitability_summaries=[_profit("S1")])[0]
    assert profile.current_store_name is None
    assert profile.evidence_completeness == "partial"
    assert profile.evidence_completeness_reasons == ["current_evidence_absent"]


def test_human_decisions_are_append_only_and_invalid_or_unknown_are_rejected():
    with SessionLocal() as db:
        first = append_human_decision(db, HumanDecisionInput("S1", "contact_for_reactivation", "contact_customer", "first", None, "actor"), {"S1"})
        second = append_human_decision(db, HumanDecisionInput("S1", "contact_for_reactivation", "resolved", "second", None, "actor"), {"S1"})
        db.commit()
        events = [event for event in load_human_decisions(db) if event.store_id == "S1"]
        assert [event.decision for event in events] == ["contact_customer", "resolved"]
        assert first.event_id != second.event_id
        with pytest.raises(ValueError, match="invalid decision"):
            append_human_decision(db, HumanDecisionInput("S1", None, "bad"), {"S1"})
        with pytest.raises(ValueError, match="unknown store"):
            append_human_decision(db, HumanDecisionInput("unknown", None, "pending"), {"S1"})

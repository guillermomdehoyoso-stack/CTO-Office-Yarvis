"""Rebuildable Store profiles; store_id is the only consolidation key."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import select

from yarvis_api.models.observation_engine import DocumentRecord, Observation
from yarvis_api.schemas.historical_evidence import ProfitabilitySummary, TransactionHistoricalAggregate
from yarvis_api.schemas.store_intelligence import HumanDecisionEvent, StoreEvidenceReference, StoreOperationalProfile

CURRENT_REPORT_TYPES = {"netpay_weekly_sales_report", "netpay_inactive_stores_report"}
WEEKLY_REPORT_TYPE = "netpay_weekly_sales_report"


def _value(observation: Any) -> Any:
    payload = getattr(observation, "observed_value", None)
    if isinstance(payload, dict):
        return payload.get("value")
    return observation.get("value") if isinstance(observation, dict) else getattr(observation, "value", None)


def _get(item: Any, field: str, default: Any = None) -> Any:
    return item.get(field, default) if isinstance(item, dict) else getattr(item, field, default)


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, Decimal): return value
    if isinstance(value, (int, float)) and not isinstance(value, bool): return Decimal(str(value))
    if isinstance(value, str):
        try: return Decimal(value.replace(",", "").replace("$", "").strip())
        except Exception: return None
    return None


def _month(value: Any) -> str | None:
    if isinstance(value, str) and len(value) == 7 and value[4] == "-": return value
    return None


def _reference(observation: Any, document: Any | None, period: str | None = None) -> StoreEvidenceReference:
    provenance = _get(observation, "provenance", {}) or {}
    return StoreEvidenceReference(
        document_id=str(_get(document, "id")) if document and _get(document, "id") else _get(observation, "document_id") and str(_get(observation, "document_id")),
        document_fingerprint=(provenance.get("document_fingerprint") if isinstance(provenance, dict) else None),
        source_type="current_observation", source_sheet=provenance.get("worksheet") if isinstance(provenance, dict) else None,
        source_row_reference=_get(observation, "source_reference"), reporting_period=period,
        temporal_class="current", observed_at=_get(observation, "observed_at"),
    )


def load_confirmed_current_evidence(db) -> list[tuple[Any, Any]]:
    """Load only promoted Sprint 7.3 evidence; candidate/draft rows never enter profiles."""
    return db.execute(
        select(Observation, DocumentRecord).join(DocumentRecord, DocumentRecord.id == Observation.document_id)
        .where(Observation.confirmation_status == "confirmed", Observation.domain == "netpay", DocumentRecord.detected_report_type.in_(CURRENT_REPORT_TYPES))
        .order_by(Observation.observed_at, Observation.id)
    ).all()


def _latest_field(items: list[tuple[Any, Any]], field_name: str) -> tuple[Any | None, bool, list[StoreEvidenceReference]]:
    candidates = [(observation, document) for observation, document in items if _get(observation, "field_name") == field_name]
    refs = [_reference(observation, document, _month(_value(observation)) if field_name == "reporting_month" else None) for observation, document in candidates]
    if not candidates: return None, False, refs
    newest = max(_get(observation, "observed_at") for observation, _ in candidates)
    latest = [(observation, document) for observation, document in candidates if _get(observation, "observed_at") == newest]
    values = {_value(observation) for observation, _ in latest}
    if len(values) != 1: return None, True, refs
    return _value(latest[0][0]), False, refs


def _sum(values: Iterable[Decimal | None]) -> Decimal | None:
    present = [value for value in values if isinstance(value, Decimal)]
    return sum(present, Decimal("0")) if present else None


def build_store_profiles(
    db=None,
    *,
    current_evidence: Iterable[tuple[Any, Any]] | None = None,
    transaction_aggregates: Iterable[TransactionHistoricalAggregate] = (),
    profitability_summaries: Iterable[ProfitabilitySummary] = (),
    human_decisions: Iterable[HumanDecisionEvent] = (),
    profitability_conflicts: Iterable[tuple[str, str]] = (),
) -> list[StoreOperationalProfile]:
    current = list(current_evidence) if current_evidence is not None else (load_confirmed_current_evidence(db) if db is not None else [])
    grouped_current: dict[str, list[tuple[Any, Any]]] = defaultdict(list)
    for observation, document in current:
        if _get(observation, "confirmation_status", "confirmed") != "confirmed":
            continue
        store_id = _get(observation, "subject_reference")
        if isinstance(store_id, str) and store_id.strip(): grouped_current[store_id.strip()].append((observation, document))
    transactions_by_store: dict[str, list[TransactionHistoricalAggregate]] = defaultdict(list)
    for aggregate in transaction_aggregates: transactions_by_store[aggregate.store_id].append(aggregate)
    profitability_by_store: dict[str, list[ProfitabilitySummary]] = defaultdict(list)
    for summary in profitability_summaries: profitability_by_store[summary.store_id].append(summary)
    decisions_by_store: dict[str, list[HumanDecisionEvent]] = defaultdict(list)
    for decision in human_decisions: decisions_by_store[decision.store_id].append(decision)
    conflict_stores = {store_id for store_id, _ in profitability_conflicts}
    profiles: list[StoreOperationalProfile] = []
    for store_id in sorted(set(grouped_current) | set(transactions_by_store) | set(profitability_by_store)):
        current_rows = grouped_current[store_id]
        transaction_rows = transactions_by_store[store_id]
        profitability_rows = profitability_by_store[store_id]
        reasons: list[str] = []
        provenance: list[StoreEvidenceReference] = []
        values: dict[str, Any] = {}
        field_map = {
            "store_name": "current_store_name", "client_id": "confirmed_client_id", "client_name": "client_name_observed",
            "operational_status": "current_operational_status", "months_no_use": "months_no_use", "source_alert": "current_source_alert",
        }
        conflicts = False
        for source_field, target in field_map.items():
            value, conflict, refs = _latest_field(current_rows, source_field)
            values[target] = value
            provenance.extend(refs)
            conflicts = conflicts or conflict
        weekly_rows = [(observation, document) for observation, document in current_rows if _get(document, "detected_report_type") == WEEKLY_REPORT_TYPE]
        for source_field, target in {"sales_volume": "latest_sales_volume", "transaction_count": "latest_transaction_count", "reporting_month": "latest_reporting_period"}.items():
            value, conflict, refs = _latest_field(weekly_rows, source_field)
            values[target] = _decimal(value) if target != "latest_reporting_period" else _month(value)
            provenance.extend(refs)
            conflicts = conflicts or conflict
        months = values.get("months_no_use")
        if isinstance(months, float) and months.is_integer(): months = int(months)
        if not isinstance(months, int): months = None
        values["months_no_use"] = months
        alert = str(values.get("current_source_alert") or "")
        status = str(values.get("current_operational_status") or "")
        norm_alert, norm_status = _normal(alert), _normal(status)
        activation_failure = "sin activacion" in norm_alert
        operational_block = "terminal incorrecta" in norm_status or "cambio terminal" in norm_status
        historical_periods = sorted({item.reporting_period for item in transaction_rows} | {item.reporting_period for item in profitability_rows})
        products = sorted({product for item in transaction_rows for product in item.products_observed})
        branch_values = {item.canonical_fields.get("branch_name_observed") for item in profitability_rows if item.canonical_fields.get("branch_name_observed")}
        branch = next(iter(branch_values)) if len(branch_values) == 1 else None
        if len(branch_values) > 1: reasons.append("historical_branch_conflict")
        for item in transaction_rows:
            provenance.extend(StoreEvidenceReference(None, None, "historical_evidence", None, reference, item.reporting_period, "historical", None) for reference in item.provenance_references)
        for item in profitability_rows:
            provenance.extend(StoreEvidenceReference(None, None, "historical_evidence", None, reference, item.reporting_period, "historical", None) for reference in item.provenance_references)
        if conflicts: reasons.append("current_evidence_conflict")
        if store_id in conflict_stores: reasons.append("duplicate_historical_profitability_conflict")
        has_current = bool(current_rows)
        has_activity = values.get("latest_sales_volume") is not None or values.get("latest_transaction_count") is not None
        has_inactivity = months is not None
        has_historical = bool(transaction_rows or profitability_rows)
        if conflicts or store_id in conflict_stores:
            completeness = "review_required"
        elif has_current and (has_activity or has_inactivity) and values.get("confirmed_client_id"):
            completeness = "complete"
            if not has_historical: reasons.append("historical_context_absent")
        else:
            completeness = "partial"
            if not has_current: reasons.append("current_evidence_absent")
            if has_current and not values.get("confirmed_client_id"): reasons.append("client_id_missing")
            if has_current and not has_activity and not has_inactivity: reasons.append("current_activity_or_inactivity_absent")
        latest_decision = max(decisions_by_store[store_id], key=lambda event: event.created_at) if decisions_by_store[store_id] else None
        profiles.append(StoreOperationalProfile(
            store_id=store_id, **values, historical_reporting_periods=historical_periods,
            historical_transaction_volume=_sum(item.historical_transaction_volume for item in transaction_rows),
            historical_transaction_count=_sum(item.historical_transaction_count for item in transaction_rows),
            historical_profitability=_sum(_decimal(item.canonical_fields.get("profitability")) for item in profitability_rows),
            historical_rent_paid=_sum(_decimal(item.canonical_fields.get("rent_paid")) for item in profitability_rows),
            historical_total_commissions=_sum(_decimal(item.canonical_fields.get("total_commissions")) for item in profitability_rows),
            products_observed=products, branch_name_observed=branch, activation_failure=activation_failure,
            operational_block=operational_block, churn_status="churn_candidate" if months is not None and months >= 2 else "watch" if months == 1 else None,
            has_historical_value_evidence=has_historical, evidence_completeness=completeness,
            evidence_completeness_reasons=sorted(set(reasons)), requires_human_review=conflicts or store_id in conflict_stores,
            latest_human_decision=latest_decision.decision if latest_decision else None,
            latest_human_note=latest_decision.operational_note if latest_decision else None,
            next_follow_up_date=latest_decision.next_follow_up_date if latest_decision else None,
            provenance_summary=provenance,
        ))
    return profiles


def _normal(value: str) -> str:
    import unicodedata
    return "".join(char for char in unicodedata.normalize("NFD", value).casefold() if unicodedata.category(char) != "Mn")

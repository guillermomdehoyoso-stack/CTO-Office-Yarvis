"""Typed, ORM-free contracts for rebuildable Store Intelligence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class StoreEvidenceReference:
    document_id: str | None
    document_fingerprint: str | None
    source_type: str
    source_sheet: str | None
    source_row_reference: str | None
    reporting_period: str | None
    temporal_class: str
    observed_at: datetime | None


@dataclass(frozen=True)
class StoreOperationalProfile:
    store_id: str
    current_store_name: str | None = None
    confirmed_client_id: str | None = None
    client_name_observed: str | None = None
    current_operational_status: str | None = None
    months_no_use: int | None = None
    current_source_alert: str | None = None
    latest_sales_volume: Decimal | None = None
    latest_transaction_count: Decimal | None = None
    latest_reporting_period: str | None = None
    historical_reporting_periods: list[str] = field(default_factory=list)
    historical_transaction_volume: Decimal | None = None
    historical_transaction_count: Decimal | None = None
    historical_profitability: Decimal | None = None
    historical_rent_paid: Decimal | None = None
    historical_total_commissions: Decimal | None = None
    products_observed: list[str] = field(default_factory=list)
    branch_name_observed: str | None = None
    activation_failure: bool = False
    operational_block: bool = False
    churn_status: str | None = None
    has_historical_value_evidence: bool = False
    evidence_completeness: str = "partial"
    evidence_completeness_reasons: list[str] = field(default_factory=list)
    recommended_action: str | None = None
    recommendation_reason: str | None = None
    action_priority: str | None = None
    requires_human_review: bool = False
    terminal_recovery_candidate: bool = False
    terminal_recovery_reason: str | None = None
    latest_human_decision: str | None = None
    latest_human_note: str | None = None
    next_follow_up_date: date | None = None
    provenance_summary: list[StoreEvidenceReference] = field(default_factory=list)


@dataclass(frozen=True)
class RecoveryQueueFilters:
    recommended_action: str | None = None
    action_priority: str | None = None
    minimum_months_no_use: int | None = None
    operational_block: bool | None = None
    activation_failure: bool | None = None
    has_historical_value_evidence: bool | None = None
    pending_action: bool | None = None
    client_id: str | None = None


@dataclass(frozen=True)
class HumanDecisionInput:
    store_id: str
    recommendation_at_decision_time: str | None
    decision: str
    operational_note: str | None = None
    next_follow_up_date: date | None = None
    actor_identifier: str | None = None


@dataclass(frozen=True)
class HumanDecisionEvent:
    event_id: str
    store_id: str
    recommendation_at_decision_time: str | None
    decision: str
    operational_note: str | None
    next_follow_up_date: date | None
    actor_identifier: str | None
    created_at: datetime


@dataclass(frozen=True)
class RecoveryQueueResult:
    profiles: list[StoreOperationalProfile]
    total_profiles: int
    pending_profiles: int
    counts_by_action: dict[str, int]
    applied_filters: RecoveryQueueFilters

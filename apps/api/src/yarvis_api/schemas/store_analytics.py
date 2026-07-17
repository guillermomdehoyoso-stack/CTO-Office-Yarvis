"""Pure, typed portfolio analytics contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from yarvis_api.schemas.store_intelligence import StoreOperationalProfile

@dataclass(frozen=True)
class AnalyticsEvidenceSummary:
    has_current_evidence: bool; has_historical_evidence: bool; evidence_completeness: str; reporting_periods: list[str]; provenance_reference_count: int

@dataclass(frozen=True)
class StoreAnalyticsFinding:
    store_id: str; finding_type: str; analytical_segment: str; attention_level: str; title: str; reason: str; recommended_next_step: str | None; current_recommended_action: str | None; months_no_use: int | None; operational_block: bool; activation_failure: bool; terminal_recovery_candidate: bool; has_historical_value_evidence: bool; historical_reporting_periods: list[str]; latest_reporting_period: str | None; latest_human_decision: str | None; pending_action: bool; evidence_summary: AnalyticsEvidenceSummary; ranking_factors: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class StorePortfolioMetrics:
    total_profiles: int; current_only_profiles: int; historical_only_profiles: int; current_and_historical_profiles: int; complete_profiles: int; partial_profiles: int; review_required_profiles: int; profiles_with_recommendations: int; pending_profiles: int; activation_failures: int; operational_blocks: int; inactive_one_month: int; inactive_two_to_three_months: int; inactive_four_or_more_months: int; terminal_recovery_candidates: int; historical_value_without_current_evidence: int; profiles_without_client_id: int; counts_by_recommended_action: dict[str,int]; counts_by_analytical_segment: dict[str,int]

@dataclass(frozen=True)
class StoreAnalyticsFilters:
    analytical_segment: str | None = None; attention_level: str | None = None; minimum_months_no_use: int | None = None; has_historical_value_evidence: bool | None = None; operational_block: bool | None = None; activation_failure: bool | None = None; terminal_recovery_candidate: bool | None = None; pending_action: bool | None = None; evidence_completeness: str | None = None; client_id: str | None = None

@dataclass(frozen=True)
class StoreAnalyticsResult:
    findings: list[StoreAnalyticsFinding]; portfolio_metrics: StorePortfolioMetrics; applied_filters: StoreAnalyticsFilters; total_findings: int

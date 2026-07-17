from dataclasses import replace
from yarvis_api.schemas.store_analytics import StoreAnalyticsFilters, StoreAnalyticsResult, StorePortfolioMetrics
from yarvis_api.schemas.store_intelligence import StoreOperationalProfile
from yarvis_api.services.store_analytics_service import analyze_store_portfolio, classify_store_analytics

def p(store, **values):
    base=StoreOperationalProfile(store_id=store,current_store_name="current",latest_reporting_period="2025-01",evidence_completeness="complete")
    return replace(base,**values)

def test_typed_segments_precedence_and_immutability():
    profiles=[p("a",evidence_completeness="review_required",activation_failure=True),p("b",activation_failure=True),p("c",operational_block=True,recommended_action="investigate_terminal_assignment"),p("d",recommended_action="review_rent_or_cancellation",has_historical_value_evidence=True,historical_reporting_periods=["2024-01"]),p("e",recommended_action="contact_for_reactivation",months_no_use=3,has_historical_value_evidence=True),p("f",recommended_action="contact_for_reactivation",months_no_use=2),p("g",recommended_action="monitor_inactivity",months_no_use=1),p("h",evidence_completeness="partial"),StoreOperationalProfile("i",has_historical_value_evidence=True,historical_reporting_periods=["2024-01"]),p("j")]
    result=analyze_store_portfolio(profiles)
    assert isinstance(result,StoreAnalyticsResult) and isinstance(result.portfolio_metrics,StorePortfolioMetrics)
    primary={f.store_id:f.analytical_segment for f in result.findings if f.finding_type!="terminal_recovery_review"}
    assert [primary[x] for x in "abcdefghij"]==["evidence_review","activation_recovery","terminal_assignment_issue","cancellation_protection","reactivation_with_history","reactivation_without_history","inactivity_watch","incomplete_profile","historical_context_only","healthy_current_store"]
    assert profiles[0].recommended_action is None

def test_filters_ranking_decisions_terminal_and_metrics():
    active=p("b",recommended_action="contact_for_reactivation",months_no_use=4,has_historical_value_evidence=True,requires_human_review=True,terminal_recovery_candidate=True)
    closed=replace(active,store_id="a",latest_human_decision="resolved")
    activation=p("c",activation_failure=True,recommended_action="complete_activation",requires_human_review=True)
    result=analyze_store_portfolio([closed,active,activation],StoreAnalyticsFilters(pending_action=True))
    assert [f.store_id for f in result.findings][:2]==["c","b"]
    assert all(f.pending_action for f in result.findings)
    terminal=classify_store_analytics(active)
    assert any(f.finding_type=="terminal_recovery_review" and "not confirmed" in f.reason for f in terminal)
    all_result=analyze_store_portfolio([closed,active,activation])
    assert all_result.portfolio_metrics.pending_profiles==2
    assert all_result.portfolio_metrics.counts_by_analytical_segment["reactivation_with_history"]==2

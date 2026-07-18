"""Runtime composition only; no workbook reads or policy implementation."""
from datetime import datetime, timezone
from yarvis_api.schemas.store_analytics import StoreAnalyticsFilters
from yarvis_api.schemas.store_intelligence import HumanDecisionEvent, HumanDecisionInput, RecoveryQueueFilters, StoreOperationalProfile
from yarvis_api.schemas.store_intelligence_api import StoreIntelligenceSummary
from yarvis_api.services.recovery_queue_service import append_human_decision, build_recovery_queue, load_human_decisions
from yarvis_api.services.store_analytics_service import analyze_store_portfolio
from yarvis_api.services.store_profile_builder import build_store_profiles

class StoreIntelligenceRuntime:
    def __init__(self, db): self.db=db
    def profiles(self) -> list[StoreOperationalProfile]:
        base=build_store_profiles(self.db,human_decisions=load_human_decisions(self.db))
        return build_recovery_queue(base).profiles
    def recovery_queue(self, filters: RecoveryQueueFilters|None=None):
        return build_recovery_queue(self.profiles(),filters)
    def analytics(self, filters: StoreAnalyticsFilters|None=None):
        return analyze_store_portfolio(self.profiles(),filters)
    def profile(self,store_id:str):
        return next((p for p in self.profiles() if p.store_id==store_id),None)
    def decision(self,decision:HumanDecisionInput)->HumanDecisionEvent:
        return append_human_decision(self.db,decision,{p.store_id for p in self.profiles()})
    def summary(self)->StoreIntelligenceSummary:
        queue=self.recovery_queue(); analytics=self.analytics(); metrics=analytics.portfolio_metrics; segments=metrics.counts_by_analytical_segment
        return StoreIntelligenceSummary(metrics.total_profiles,queue.pending_profiles,metrics.profiles_with_recommendations,segments.get("evidence_review",0),metrics.activation_failures,metrics.operational_blocks,metrics.counts_by_recommended_action.get("review_rent_or_cancellation",0),segments.get("reactivation_with_history",0),segments.get("reactivation_without_history",0),metrics.terminal_recovery_candidates,segments.get("historical_context_only",0),segments.get("incomplete_profile",0),datetime.now(timezone.utc))

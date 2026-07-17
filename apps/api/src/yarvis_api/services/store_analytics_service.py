"""Pure deterministic analytics over already-built StoreOperationalProfile values."""
from __future__ import annotations
from collections import Counter
from dataclasses import replace

from yarvis_api.schemas.store_analytics import AnalyticsEvidenceSummary, StoreAnalyticsFilters, StoreAnalyticsFinding, StoreAnalyticsResult, StorePortfolioMetrics
from yarvis_api.schemas.store_intelligence import StoreOperationalProfile

_ATTENTION={"evidence_review":"critical","activation_recovery":"critical","terminal_assignment_issue":"critical","cancellation_protection":"critical","reactivation_with_history":"high","reactivation_without_history":"medium","inactivity_watch":"low","incomplete_profile":"low","historical_context_only":"informational","healthy_current_store":"informational"}
_ARANK={"critical":0,"high":1,"medium":2,"low":3,"informational":4}

def _current(p):
    return any((p.latest_reporting_period,p.current_operational_status,p.current_source_alert,p.months_no_use,p.latest_sales_volume,p.latest_transaction_count,p.activation_failure,p.operational_block,p.churn_status,p.current_store_name))
def _historical(p): return bool(p.has_historical_value_evidence or p.historical_reporting_periods)
def _pending(p): return bool(p.requires_human_review and p.recommended_action and p.recommended_action!="monitor_inactivity" and p.latest_human_decision not in {"resolved","no_action"})
def _segment(p):
    current=_current(p)
    if p.evidence_completeness=="review_required": return "evidence_review"
    if p.activation_failure and current: return "activation_recovery"
    if p.operational_block and p.recommended_action in {"investigate_terminal_assignment","investigate_terminal_replacement"}: return "terminal_assignment_issue"
    if p.recommended_action=="review_rent_or_cancellation" and current: return "cancellation_protection"
    if p.recommended_action=="contact_for_reactivation" and current: return "reactivation_with_history" if p.has_historical_value_evidence else "reactivation_without_history"
    if p.recommended_action=="monitor_inactivity" and current: return "inactivity_watch"
    if p.evidence_completeness=="partial" and current: return "incomplete_profile"
    if _historical(p) and not current: return "historical_context_only"
    return "healthy_current_store"

def _content(p, segment):
    data={
      "evidence_review":("Evidence requires review","Available evidence cannot be resolved deterministically.","Review the conflicting evidence before taking operational action."),
      "activation_recovery":("Activation recovery required","Current evidence indicates that activation was not completed.","Verify onboarding requirements and complete activation with the merchant."),
      "cancellation_protection":("Cancellation review requires context","Current evidence requests review of rent charge or cancellation.","Review current merchant status and documented history before deciding whether to charge rent or cancel."),
      "reactivation_with_history":("Reactivation opportunity","Current evidence shows inactivity and accepted historical commercial activity exists.","Contact the merchant and verify whether commercial reactivation is viable."),
      "reactivation_without_history":("Reactivation review","Current evidence shows inactivity, but no accepted historical commercial evidence is available.","Contact the merchant to clarify current use and commercial status."),
      "inactivity_watch":("Inactivity monitoring","Current evidence shows one month without use.","Monitor the next reporting cycle before escalation."),
      "incomplete_profile":("Incomplete operational evidence","Available current evidence is incomplete.","Complete the missing evidence before relying on the profile for broader analysis."),
      "historical_context_only":("Historical context only","Historical commercial evidence exists, but no confirmed current operational evidence is available.","Obtain current evidence before generating operational recommendations."),
      "healthy_current_store":("No current operational exception","No current recovery or operational exception is indicated by the available confirmed evidence.",None),
    }
    if segment=="terminal_assignment_issue":
      replacement=p.recommended_action=="investigate_terminal_replacement"
      return ("Terminal replacement issue" if replacement else "Terminal assignment issue", "Current operational status indicates a pending terminal replacement." if replacement else "Current operational status indicates an incorrect terminal assignment.","Review the current terminal assignment or replacement case.")
    return data[segment]

def _finding(p, segment, finding_type=None, title=None, reason=None, step=None):
    title0,reason0,step0=_content(p,segment); pending=_pending(p)
    if p.latest_human_decision in {"resolved","no_action"}: reason0 += " Latest human decision closed the pending state."
    if segment=="cancellation_protection" and p.has_historical_value_evidence: reason0 += " Historical commercial activity exists and should be reviewed before cancellation."
    if segment=="reactivation_with_history" and p.months_no_use is not None: reason0 += f" Current evidence shows {p.months_no_use} months without use."
    if segment=="incomplete_profile" and p.evidence_completeness_reasons: reason0 += " Missing evidence: " + ", ".join(sorted(p.evidence_completeness_reasons)) + "."
    factors=[]
    for key, applies in [("pending_action",pending),("evidence_review",segment=="evidence_review"),(f"{_ATTENTION[segment]}_attention",True),("activation_failure",p.activation_failure),("operational_block",p.operational_block),("cancellation_review",p.recommended_action=="review_rent_or_cancellation"),("terminal_recovery_candidate",p.terminal_recovery_candidate),(f"inactivity_{p.months_no_use}_months",bool(p.months_no_use and p.months_no_use>=4)),("historical_value_evidence",p.has_historical_value_evidence),("deterministic_store_id_tiebreak",True)]:
      if applies: factors.append(key)
    return StoreAnalyticsFinding(p.store_id,finding_type or {"evidence_review":"evidence_conflict","activation_recovery":"activation_failure","terminal_assignment_issue":"terminal_operational_block","cancellation_protection":"cancellation_review","reactivation_with_history":"reactivation_opportunity","reactivation_without_history":"reactivation_review","inactivity_watch":"inactivity_monitoring","incomplete_profile":"incomplete_evidence","historical_context_only":"historical_only","healthy_current_store":"no_current_issue"}[segment],segment,_ATTENTION[segment],title or title0,reason or reason0,step if step is not None else step0,p.recommended_action,p.months_no_use,p.operational_block,p.activation_failure,p.terminal_recovery_candidate,p.has_historical_value_evidence,list(p.historical_reporting_periods),p.latest_reporting_period,p.latest_human_decision,pending,AnalyticsEvidenceSummary(_current(p),_historical(p),p.evidence_completeness,list(p.historical_reporting_periods),len(p.provenance_summary)),factors)

def classify_store_analytics(profile: StoreOperationalProfile)->list[StoreAnalyticsFinding]:
    segment=_segment(profile); result=[_finding(profile,segment)]
    if profile.terminal_recovery_candidate:
      result.append(_finding(profile,segment,"terminal_recovery_review","Terminal recovery review candidate","Current policy marks this Store for terminal recovery review; terminal assignment and physical recoverability are not confirmed.","Review the documented terminal recovery case."))
    return result

def rank_analytics_findings(findings):
    return sorted(findings,key=lambda f:(not f.pending_action,f.analytical_segment!="evidence_review",_ARANK[f.attention_level],not f.activation_failure,not f.operational_block,f.current_recommended_action!="review_rent_or_cancellation",not f.terminal_recovery_candidate,-(f.months_no_use or 0),not f.has_historical_value_evidence,{"review_required":0,"complete":1,"partial":2}.get(f.evidence_summary.evidence_completeness,3),f.store_id,f.finding_type))

def calculate_portfolio_metrics(profiles):
    current=[_current(p) for p in profiles]; historical=[_historical(p) for p in profiles]; primary=Counter(_segment(p) for p in profiles); actions=Counter(p.recommended_action for p in profiles if p.recommended_action)
    return StorePortfolioMetrics(len(profiles),sum(c and not h for c,h in zip(current,historical)),sum(h and not c for c,h in zip(current,historical)),sum(c and h for c,h in zip(current,historical)),sum(p.evidence_completeness=="complete" for p in profiles),sum(p.evidence_completeness=="partial" for p in profiles),sum(p.evidence_completeness=="review_required" for p in profiles),sum(bool(p.recommended_action) for p in profiles),sum(_pending(p) for p in profiles),sum(p.activation_failure for p in profiles),sum(p.operational_block for p in profiles),sum(p.months_no_use==1 for p in profiles),sum(p.months_no_use in {2,3} for p in profiles),sum(bool(p.months_no_use and p.months_no_use>=4) for p in profiles),sum(p.terminal_recovery_candidate for p in profiles),sum(h and not c for c,h in zip(current,historical)),sum(p.confirmed_client_id is None for p in profiles),dict(actions),dict(primary))

def _match(f,filters):
    p=f
    return all((filters.analytical_segment is None or p.analytical_segment==filters.analytical_segment,filters.attention_level is None or p.attention_level==filters.attention_level,filters.minimum_months_no_use is None or (p.months_no_use is not None and p.months_no_use>=filters.minimum_months_no_use),filters.has_historical_value_evidence is None or p.has_historical_value_evidence==filters.has_historical_value_evidence,filters.operational_block is None or p.operational_block==filters.operational_block,filters.activation_failure is None or p.activation_failure==filters.activation_failure,filters.terminal_recovery_candidate is None or p.terminal_recovery_candidate==filters.terminal_recovery_candidate,filters.pending_action is None or p.pending_action==filters.pending_action,filters.evidence_completeness is None or p.evidence_summary.evidence_completeness==filters.evidence_completeness))

def analyze_store_portfolio(profiles,filters=None):
    applied=filters or StoreAnalyticsFilters(); findings=[f for p in profiles for f in classify_store_analytics(p) if _match(f,applied) and (applied.client_id is None or p.confirmed_client_id==applied.client_id)]
    return StoreAnalyticsResult(rank_analytics_findings(findings),calculate_portfolio_metrics(profiles),applied,len(findings))

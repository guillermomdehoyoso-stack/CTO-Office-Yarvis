"""Deterministic Store Intelligence policy, filtering, ordering and decisions."""
from __future__ import annotations

import unicodedata
from dataclasses import replace
from datetime import date
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.observation_engine import Observation
from yarvis_api.schemas.store_intelligence import (
    HumanDecisionEvent, HumanDecisionInput, RecoveryQueueFilters, RecoveryQueueResult, StoreOperationalProfile,
)

ALLOWED_DECISIONS = {"pending", "contact_customer", "investigate_terminal", "request_terminal_return", "attempt_reactivation", "review_rent", "review_cancellation", "no_action", "resolved"}
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2, None: 3}


def _normal(value: str | None) -> str:
    text = unicodedata.normalize("NFD", str(value or "")).casefold()
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def apply_recommendation(profile: StoreOperationalProfile) -> StoreOperationalProfile:
    """Return exactly one primary recommendation; historical-only stores are never recommended."""
    if not profile.provenance_summary or not any(reference.temporal_class == "current" for reference in profile.provenance_summary):
        return profile
    alert, status, months = _normal(profile.current_source_alert), _normal(profile.current_operational_status), profile.months_no_use
    action = priority = reason = None
    requires_review = False
    if "sin activacion" in alert:
        action, priority, reason, requires_review = "complete_activation", "high", "Current source indicates activation was not completed.", True
    elif "terminal incorrecta" in status:
        action, priority, reason, requires_review = "investigate_terminal_assignment", "high", "Current operational status indicates an incorrect terminal assignment.", True
    elif "cambio terminal" in status:
        action, priority, reason, requires_review = "investigate_terminal_replacement", "high", "Current operational status indicates a pending terminal replacement.", True
    elif "cobrar renta o cancelar" in alert:
        action, priority, reason, requires_review = "review_rent_or_cancellation", "high", "Current source requests rent charge or cancellation review.", True
    elif isinstance(months, int) and months >= 2:
        action, priority, reason, requires_review = "contact_for_reactivation", "high" if months >= 4 else "medium", f"Current evidence shows {months} months without use.", True
    elif months == 1:
        action, priority, reason = "monitor_inactivity", "low", "Current evidence shows 1 month without use; monitor before escalation."
    if reason and profile.has_historical_value_evidence and profile.historical_reporting_periods:
        reason += f" Historical commercial activity exists for: {', '.join(sorted(profile.historical_reporting_periods))}."
    terminal_candidate = bool(months is not None and months >= 2 and action == "review_rent_or_cancellation" and not profile.activation_failure)
    return replace(
        profile, recommended_action=action, action_priority=priority, recommendation_reason=reason,
        requires_human_review=requires_review or profile.requires_human_review,
        terminal_recovery_candidate=terminal_candidate,
        terminal_recovery_reason="Candidate for terminal recovery review; terminal assignment is not confirmed." if terminal_candidate else None,
    )


def is_pending(profile: StoreOperationalProfile) -> bool:
    return bool(profile.requires_human_review and profile.recommended_action and profile.recommended_action != "monitor_inactivity" and profile.latest_human_decision not in {"resolved", "no_action"})


def _matches(profile: StoreOperationalProfile, filters: RecoveryQueueFilters) -> bool:
    if filters.recommended_action is not None and profile.recommended_action != filters.recommended_action: return False
    if filters.action_priority is not None and profile.action_priority != filters.action_priority: return False
    if filters.minimum_months_no_use is not None and (profile.months_no_use is None or profile.months_no_use < filters.minimum_months_no_use): return False
    if filters.operational_block is not None and profile.operational_block != filters.operational_block: return False
    if filters.activation_failure is not None and profile.activation_failure != filters.activation_failure: return False
    if filters.has_historical_value_evidence is not None and profile.has_historical_value_evidence != filters.has_historical_value_evidence: return False
    if filters.pending_action is not None and is_pending(profile) != filters.pending_action: return False
    return filters.client_id is None or profile.confirmed_client_id == filters.client_id


def _sort_key(profile: StoreOperationalProfile):
    return (
        not is_pending(profile), _PRIORITY_RANK.get(profile.action_priority, 3),
        not profile.activation_failure, not profile.operational_block,
        -(profile.months_no_use or 0), not profile.has_historical_value_evidence, profile.store_id,
    )


def build_recovery_queue(profiles: list[StoreOperationalProfile], filters: RecoveryQueueFilters | None = None) -> RecoveryQueueResult:
    applied = filters or RecoveryQueueFilters()
    evaluated = [apply_recommendation(profile) for profile in profiles]
    selected = sorted((profile for profile in evaluated if _matches(profile, applied)), key=_sort_key)
    pending = [profile for profile in selected if is_pending(profile)]
    counts: dict[str, int] = {}
    for profile in pending:
        if profile.recommended_action:
            counts[profile.recommended_action] = counts.get(profile.recommended_action, 0) + 1
        if profile.terminal_recovery_candidate:
            counts["terminal_recovery_candidate"] = counts.get("terminal_recovery_candidate", 0) + 1
    return RecoveryQueueResult(selected, len(selected), len(pending), counts, applied)


def _event_to_decision(event: DomainEvent) -> HumanDecisionEvent:
    payload = event.payload
    follow_up = payload.get("next_follow_up_date")
    return HumanDecisionEvent(
        str(event.id), payload["store_id"], payload.get("recommendation_at_decision_time"), payload["decision"],
        payload.get("operational_note"), date.fromisoformat(follow_up) if follow_up else None,
        payload.get("actor_identifier"), event.occurred_at,
    )


def load_human_decisions(db) -> list[HumanDecisionEvent]:
    events = db.scalars(select(DomainEvent).where(DomainEvent.event_type == "recovery_queue.decision_recorded").order_by(DomainEvent.occurred_at, DomainEvent.id)).all()
    return [_event_to_decision(event) for event in events]


def append_human_decision(db, decision: HumanDecisionInput, known_store_ids: set[str]) -> HumanDecisionEvent:
    if decision.decision not in ALLOWED_DECISIONS: raise ValueError("invalid decision")
    if decision.store_id not in known_store_ids: raise ValueError("unknown store")
    event = record_event(
        db, event_type="recovery_queue.decision_recorded", aggregate_type="netpay_store_recovery",
        aggregate_id=uuid5(NAMESPACE_URL, f"netpay-store:{decision.store_id}"),
        payload={"store_id": decision.store_id, "recommendation_at_decision_time": decision.recommendation_at_decision_time,
                 "decision": decision.decision, "operational_note": decision.operational_note,
                 "next_follow_up_date": decision.next_follow_up_date.isoformat() if decision.next_follow_up_date else None,
                 "actor_identifier": decision.actor_identifier},
    )
    db.flush()
    return _event_to_decision(event)


# Compatibility adapter for the unregistered route; it keeps all policy in this module.
def recovery_queue(profiles, *, action_type=None, priority=None, client_id=None):
    if profiles and isinstance(profiles[0], dict): raise TypeError("StoreOperationalProfile is required")
    return build_recovery_queue(profiles, RecoveryQueueFilters(action_type, priority, None, None, None, None, None, client_id)).profiles


def append_decision(db, *, store_id, payload):
    follow_up = payload.get("next_follow_up_date")
    if isinstance(follow_up, str): follow_up = date.fromisoformat(follow_up)
    decision = HumanDecisionInput(store_id, payload.get("recommendation_at_decision_time"), payload.get("decision"), payload.get("note"), follow_up, payload.get("actor_identifier"))
    known = {item[0] for item in db.execute(select(Observation.subject_reference).where(Observation.confirmation_status == "confirmed", Observation.domain == "netpay")).all() if item[0]}
    if store_id not in known: raise ValueError("unknown store")
    return append_human_decision(db, decision, known).decision

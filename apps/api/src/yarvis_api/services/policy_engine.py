from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.models.observation_engine import AttentionItem, OperationalPolicy, PolicyEvaluation


ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "in",
    "not_in",
    "days_since_greater_than",
    "exists",
    "missing",
}


def _days_since(value: str | datetime) -> int:
    if isinstance(value, datetime):
        base = value
    else:
        base = datetime.fromisoformat(value.replace("Z", "+00:00"))
    now = utc_now()
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return (now - base).days


def _evaluate_condition(condition: dict, facts: dict) -> tuple[str, bool | None]:
    field = condition.get("field")
    operator = condition.get("operator")
    target = condition.get("value")

    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"unsupported operator: {operator}")

    present = field in facts and facts[field] is not None
    current = facts.get(field)

    if operator == "exists":
        return f"{field} exists={present}", present
    if operator == "missing":
        return f"{field} missing={not present}", not present

    if not present:
        return f"{field} missing", None

    if operator == "equals":
        return f"{field} == {target}", current == target
    if operator == "not_equals":
        return f"{field} != {target}", current != target
    if operator == "greater_than":
        return f"{field} > {target}", current > target
    if operator == "greater_than_or_equal":
        return f"{field} >= {target}", current >= target
    if operator == "less_than":
        return f"{field} < {target}", current < target
    if operator == "less_than_or_equal":
        return f"{field} <= {target}", current <= target
    if operator == "in":
        return f"{field} in {target}", current in target
    if operator == "not_in":
        return f"{field} not_in {target}", current not in target
    if operator == "days_since_greater_than":
        days = _days_since(current)
        return f"days_since({field})={days} > {target}", days > target
    raise ValueError(f"unsupported operator: {operator}")


def validate_policy_configuration(configuration: dict) -> None:
    conditions = configuration.get("conditions")
    if not isinstance(conditions, list) or not conditions:
        raise ValueError("configuration.conditions must be a non-empty list")
    for condition in conditions:
        if condition.get("operator") not in ALLOWED_OPERATORS:
            raise ValueError(f"unsupported operator: {condition.get('operator')}")


def evaluate_policy(
    db: Session,
    *,
    policy: OperationalPolicy,
    subject_type: str,
    subject_id: str,
    facts: dict,
    evidence_references: list[dict],
) -> PolicyEvaluation:
    validate_policy_configuration(policy.configuration)

    conditions = policy.configuration.get("conditions", [])
    explanations: list[str] = []
    statuses: list[bool | None] = []

    for condition in conditions:
        explanation, result = _evaluate_condition(condition, facts)
        explanations.append(explanation)
        statuses.append(result)

    if any(result is None for result in statuses):
        result_status = "insufficient_data"
    elif all(statuses):
        result_status = "matched"
    else:
        result_status = "not_matched"

    if facts.get("has_identity_conflict"):
        result_status = "conflict"

    evaluation = PolicyEvaluation(
        policy_id=policy.id,
        subject_type=subject_type,
        subject_id=subject_id,
        result_status=result_status,
        explanation="; ".join(explanations),
        input_snapshot={
            "policy_key": policy.policy_key,
            "policy_version": policy.version,
            "facts": facts,
            "conditions": conditions,
        },
        evidence_references=evidence_references or [],
        evaluated_at=utc_now(),
    )
    db.add(evaluation)
    db.flush()

    if result_status in {"matched", "insufficient_data", "conflict"}:
        action = _recommended_action(policy.policy_key, result_status)
        item = AttentionItem(
            subject_type=subject_type,
            subject_id=subject_id,
            policy_key=policy.policy_key,
            severity=policy.severity,
            explanation=evaluation.explanation,
            recommended_action=action,
            requires_human_approval=policy.requires_human_approval,
            status="open",
        )
        db.add(item)
        db.flush()

    return evaluation


def _recommended_action(policy_key: str, result_status: str) -> str:
    mapping = {
        "netpay.store.watch_inactivity": "review_store",
        "netpay.store.churn_candidate": "review_churn",
        "netpay.store.critical_sales_drop": "review_store",
        "netpay.asset.recovery_review": "review_asset_recovery",
    }
    if result_status == "insufficient_data":
        return "investigate_missing_data"
    if result_status == "conflict":
        return "resolve_conflict"
    return mapping.get(policy_key, "review_store")


def get_active_policy(db: Session, policy_key: str) -> OperationalPolicy | None:
    return db.scalar(
        select(OperationalPolicy)
        .where(OperationalPolicy.policy_key == policy_key)
        .where(OperationalPolicy.status == "active")
        .order_by(OperationalPolicy.version.desc())
    )

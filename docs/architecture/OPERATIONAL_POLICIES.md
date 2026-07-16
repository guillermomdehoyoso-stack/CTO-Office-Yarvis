# Operational Policies

Operational policies are data/configuration interpreted by application code.

No dynamic code execution is allowed.
No eval(), exec(), user scripts, or arbitrary expression language is allowed.

## Policy Shape

Each policy uses:
- policy_key
- domain
- version
- status
- description
- input facts
- conditions
- output
- severity
- human approval requirement
- explanation template
- effective_from
- effective_until

## Deterministic Operators

Allowed operators:
- equals
- not_equals
- greater_than
- greater_than_or_equal
- less_than
- less_than_or_equal
- in
- not_in
- days_since_greater_than
- exists
- missing

## Evaluation Rules

- Policies run on resolved operational state and explicit facts.
- Evaluation output includes matched status, explanation, input snapshot, policy version, and evidence/observation references when available.
- `insufficient_data` is returned when required facts are missing.
- `conflict` is returned when conflicting identity/state signals are present.

## NetPay Initial Policies

1. netpay.store.watch_inactivity
- Default threshold: inactive_days >= 30
- Output: watch
- Human approval required.

2. netpay.store.churn_candidate
- Default threshold: inactive_days >= 60
- Output: churn_candidate
- Cancellation is never automatic.
- Human review is required.
- Open replacement/shipment/service case may suspend recommendation.
- Insufficient data returns insufficient_data.

3. netpay.store.critical_sales_drop
- Conditions include historical volume threshold and sales_drop_percentage threshold.
- Output: critical_store_review.

4. netpay.asset.recovery_review
- Conditions include churn candidate state, asset assignment, and no active shipment/replacement.
- Output: asset_recovery_review.

All thresholds are configurable per policy version.

# Operational Economics Metric Catalog

**Status:** Draft for Ratification  
**Checkpoint:** OV-001  
**Authority:** [Operational Economics Architecture](OPERATIONAL_ECONOMICS_ARCHITECTURE.md)

This catalog defines metric meaning, not implementation, accounting policy, or UI.
Every result must carry scope, organization, currency, as-of time, fact-selection
policy, source fact identities, freshness, and missing-data status.

| ID | Metric | Formula / selection | Meaning and exclusions |
| --- | --- | --- | --- |
| OEM-001 | Expected revenue | Sum current `revenue/expected` facts. | Plausible anticipated value; excludes contracted revenue and cash. |
| OEM-002 | Contracted revenue | Sum current `revenue/contracted` facts. | Committed commercial value; excludes cash and invoice/accounting status. |
| OEM-003 | Revenue basis | Contracted revenue if present; otherwise expected revenue. | Declared policy for profit/margin; never adds both by default. |
| OEM-004 | Estimated cost | Sum current `cost` and `labor_cost` facts at `estimated`. | Planning estimate; excludes committed/incurred cost. |
| OEM-005 | Committed cost | Sum current `cost` and `labor_cost` facts at `committed`. | Authorized/committed operational obligation; not necessarily paid or incurred. |
| OEM-006 | Incurred cost | Sum current `cost` and `labor_cost` facts at `incurred`. | Cost observed as consumed/recognized operationally; not automatically cash. |
| OEM-007 | Labor/time cost | Sum current `labor_cost` facts, grouped by state. | Monetary valuation of labor/time; preserves quantity/rate evidence where supplied. |
| OEM-008 | Cash in | Sum `cash_in/incurred` facts. | Observable incoming cash; not revenue by implication. |
| OEM-009 | Cash out | Sum `cash_out/incurred` facts. | Observable outgoing cash; not cost by implication. |
| OEM-010 | Current net cash | OEM-008 minus OEM-009. | Cash position for the scope; not profit. |
| OEM-011 | Cost to complete | Current `cost` plus `labor_cost` facts at `forecast_to_complete`. | Forward-looking remaining cost; selects latest non-superseded forecast. |
| OEM-012 | Projected total cost | OEM-006 plus OEM-011. | Incurred cost plus remaining cost; does not add estimated cost. |
| OEM-013 | Expected final profit | OEM-003 minus OEM-012. | Operational forecast; not booked profit or legal result. |
| OEM-014 | Expected final margin | OEM-013 divided by OEM-003. | Undefined when revenue basis is zero, unknown, or mixed-currency. |

## Metric States

- **AVAILABLE:** all required inputs are usable in one currency.
- **PARTIAL:** some input facts are missing or restricted; output names the gap.
- **UNAVAILABLE:** no valid required basis, a currency conversion is missing, or a
  policy-required input is unknown.
- **MIXED_CURRENCY:** aggregation is prohibited until a traceable conversion is
  provided.

No metric treats unavailable inputs as zero. A metric snapshot must expose its state
along with its numeric output, if any.

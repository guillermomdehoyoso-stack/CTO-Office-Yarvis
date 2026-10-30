"""Read-only reconciliation, exact tenant/Store/period; no allocation or bank assertion."""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select

from yarvis_api.models.netpay_operational_data import OperationalDataBatch, StoreProfitabilityFact
from yarvis_api.services.netpay_commission_settlement import concept_candidate, exact_sum, verified_rows


def settlements(db, organization_id, period=None, *, include_details=False):
    query = select(OperationalDataBatch).where(
        OperationalDataBatch.organization_id == organization_id,
        OperationalDataBatch.dataset_type == "commission_settlement",
        OperationalDataBatch.status == "accepted",
        OperationalDataBatch.settlement_effective.is_(True),
        OperationalDataBatch.currency_code == "MXN",
    )
    if period:
        query = query.where(OperationalDataBatch.reporting_period == period)
    result = []
    for batch in db.scalars(query.order_by(OperationalDataBatch.reporting_period.desc())).all():
        rows = verified_rows(db, batch)
        facts = db.scalars(
            select(StoreProfitabilityFact)
            .join(OperationalDataBatch, StoreProfitabilityFact.batch_id == OperationalDataBatch.id)
            .where(
                StoreProfitabilityFact.organization_id == organization_id,
                OperationalDataBatch.organization_id == organization_id,
                OperationalDataBatch.status == "accepted",
                OperationalDataBatch.currency_code == "MXN",
                StoreProfitabilityFact.reporting_period == batch.reporting_period,
                StoreProfitabilityFact.effective_status == "effective",
            )
        ).all()
        by_store = {f.store_reference_id: f for f in facts}
        groups, details = defaultdict(lambda: Decimal(0)), []
        observed_stores = set()
        for row in rows:
            p = row.controlled_payload
            fact = by_store.get(row.store_reference_id)
            reasons = ["concept_mapping_pending", "entity_mapping_pending"]
            if not p["store_id"]:
                reasons.append("store_missing")
            elif row.store_reference_id is None:
                reasons.append("store_unmatched")
            if fact is None:
                reasons.append("missing_core")
            elif fact.metric_definition_version != "ap_aq_ar_v2":
                reasons.append("commission_components_unavailable")
            if row.store_reference_id:
                observed_stores.add(row.store_reference_id)
            group_key = (p["entity_original"], p["concept_original"], p["store_id"])
            groups[group_key] = exact_sum([groups[group_key], Decimal(p["amount_signed"])])
            details.append(
                {
                    **p,
                    "source_sheet": batch.selected_sheet,
                    "source_hash": batch.source_hash,
                    "concept_candidate": concept_candidate(p["concept_original"]),
                    "comparability": "unconfirmed",
                    "reasons": reasons,
                    "core_commission": str(fact.commission_v2_exact)
                    if fact and fact.commission_v2_exact is not None
                    else None,
                }
            )
        # Source text does not certify external adjustments or mapping to AP/AQ/AR.
        item = {
            "batch_id": str(batch.id),
            "reporting_period": batch.reporting_period,
            "currency_code": "MXN",
            "source_hash": batch.source_hash,
            "source_sheet": batch.selected_sheet,
            "announced_payment_date": batch.settlement_metadata["announced_payment_date"],
            "net_reported": batch.settlement_metadata["net_reported"],
            "positive": batch.settlement_metadata["positive"],
            "negative": batch.settlement_metadata["negative"],
            "confirmed_adjustments": None,
            "unexplained_difference": None,
            "difference_reason": "concept_and_entity_mapping_pending",
            "bank_status": "not_confirmed",
            "mapping_version": "unconfirmed_v1",
        }
        if include_details:
            item.update(
                movements=details,
                movement_count=len(details),
                groups=[
                    {"entity": e, "concept": c, "store_id": s, "amount": str(v)} for (e, c, s), v in groups.items()
                ],
                core_without_settlement=[
                    str(f.store_reference_id) for f in facts if f.store_reference_id not in observed_stores
                ],
            )
        result.append(item)
    return result

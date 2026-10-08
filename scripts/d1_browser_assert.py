"""Assert durable synthetic D1 facts after one browser suite run."""

import json

from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.netpay_operational_data import (
    NoUsageCampaignEntry,
    OperationalDataBatch,
    OperationalDataRow,
    StoreProfitabilityFact,
)


def main() -> None:
    with app.state.yarvis.persistence.create_session() as db:
        batches = db.scalars(
            select(OperationalDataBatch).where(OperationalDataBatch.status == "accepted")
        ).all()
        by_type = {batch.dataset_type: batch for batch in batches}
        assert set(by_type) == {"monthly_store_profitability", "no_usage_campaign"}
        facts = {
            "monthly_store_profitability": db.scalar(
                select(func.count(StoreProfitabilityFact.id)).where(
                    StoreProfitabilityFact.batch_id == by_type["monthly_store_profitability"].id
                )
            ),
            "no_usage_campaign": db.scalar(
                select(func.count(NoUsageCampaignEntry.id)).where(
                    NoUsageCampaignEntry.batch_id == by_type["no_usage_campaign"].id
                )
            ),
        }
        assert facts == {"monthly_store_profitability": 1, "no_usage_campaign": 1}
        row_counts = {
            dataset_type: db.scalar(
                select(func.count(OperationalDataRow.id)).where(OperationalDataRow.batch_id == batch.id)
            )
            for dataset_type, batch in by_type.items()
        }
        assert row_counts == {"monthly_store_profitability": 1, "no_usage_campaign": 1}
        print(json.dumps({"accepted_batches": len(batches), "facts": facts, "persisted_rows": row_counts}))


if __name__ == "__main__":
    main()

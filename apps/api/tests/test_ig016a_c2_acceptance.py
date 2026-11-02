from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from test_netpay_operational_data import setup_data

from yarvis_api.main import app
from yarvis_api.models.netpay_master import NetpayStoreReference
from yarvis_api.models.netpay_no_usage_acceptance import (
    NetpayNoUsageBatch,
    NetpayNoUsageHistory,
    NetpayNoUsageReceipt,
)
from yarvis_api.services import netpay_no_usage_acceptance as service
from yarvis_api.services.netpay_no_usage_acceptance import AcceptanceError, accept_sources, create_checkpoint, readback
from yarvis_api.services.netpay_no_usage_recovery_preview import SourceBytes

DIGEST = "a" * 64


def context():
    store_id = setup_data()
    with app.state.yarvis.persistence.create_session() as db:
        store = db.get(NetpayStoreReference, store_id)
        return store.organization_id, store.created_by_principal_id


def preview():
    return {
        "preview_digest": DIGEST,
        "sources": [
            {"profile": name, "version": "1", "sha256": char * 64, "signature": (char.upper()) * 64}
            for name, char in (
                ("netpay_no_usage_oct26_v1", "1"),
                ("netpay_global_equipment_oct26_v1", "2"),
                ("netpay_ticket97580_equipment_client_oct26_v1", "3"),
            )
        ],
        "matching": {
            "exact_evidenced": 20,
            "resolution_status": "pending",
            "resolution_reason": "pending_temporality",
            "missing_equipment_match": 12,
            "equipment_with_client": 118,
            "missing_store_and_client": 18,
            "ambiguous": 0,
            "contradictory": 0,
            "period_cutoff": "unknown",
        },
    }


def sources():
    return tuple(SourceBytes(item["profile"], b"synthetic", item["sha256"]) for item in preview()["sources"])


@pytest.fixture
def controlled_c1(monkeypatch):
    monkeypatch.setattr(service, "preview_no_usage_recovery_sources", lambda *args, **kwargs: preview())
    monkeypatch.setattr(service, "_parse", lambda source, **kwargs: {"rows": []})


def test_checkpoint_accept_replay_readback_and_minimization(controlled_c1):
    org, actor = context()
    with app.state.yarvis.persistence.create_session() as db:
        checkpoint = create_checkpoint(
            db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=True
        )
        first = accept_sources(
            db,
            organization_id=org,
            actor_principal_id=actor,
            checkpoint_id=checkpoint.id,
            sources=sources(),
            preview_digest=DIGEST,
            idempotency_key="accept-1",
            expected_contract_version="1.0.0",
            authorized=True,
        )
        checkpoint_id = checkpoint.id
        db.commit()
    with app.state.yarvis.persistence.create_session() as db:
        replay = accept_sources(
            db,
            organization_id=org,
            actor_principal_id=actor,
            checkpoint_id=checkpoint_id,
            sources=sources(),
            preview_digest=DIGEST,
            idempotency_key="accept-1",
            expected_contract_version="1.0.0",
            authorized=True,
        )
        assert replay["batch_id"] == first["batch_id"] and replay["replay"] is True
        result = readback(db, organization_id=org, batch_id=first["batch_id"], authorized=True)
        assert result["counts"]["exact_evidenced"] == 20
        assert result["counts"]["resolution_status"] == "pending"
        assert result["classifications"]["missing_store_and_client"] == 18
        assert "email" not in str(result).lower() and "phone" not in str(result).lower()
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageBatch)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageReceipt)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageHistory)) == 1


def test_checkpoint_and_idempotency_guards(controlled_c1):
    org, actor = context()
    with app.state.yarvis.persistence.create_session() as db:
        checkpoint = create_checkpoint(
            db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=True
        )
        checkpoint.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        with pytest.raises(AcceptanceError, match="checkpoint_expired"):
            accept_sources(
                db,
                organization_id=org,
                actor_principal_id=actor,
                checkpoint_id=checkpoint.id,
                sources=sources(),
                preview_digest=DIGEST,
                idempotency_key="expired",
                expected_contract_version="1.0.0",
                authorized=True,
            )
        checkpoint.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        first = accept_sources(
            db,
            organization_id=org,
            actor_principal_id=actor,
            checkpoint_id=checkpoint.id,
            sources=sources(),
            preview_digest=DIGEST,
            idempotency_key="conflict",
            expected_contract_version="1.0.0",
            authorized=True,
        )
        with pytest.raises(AcceptanceError, match="idempotency_conflict"):
            accept_sources(
                db,
                organization_id=org,
                actor_principal_id=actor,
                checkpoint_id=uuid4(),
                sources=sources(),
                preview_digest=DIGEST,
                idempotency_key="conflict",
                expected_contract_version="1.0.0",
                authorized=True,
            )
        assert first["status"] == "accepted"


def test_forbidden_stale_and_tenant_concealment(controlled_c1):
    org, actor = context()
    with app.state.yarvis.persistence.create_session() as db:
        with pytest.raises(AcceptanceError, match="forbidden"):
            create_checkpoint(db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=False)
        checkpoint = create_checkpoint(
            db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=True
        )
        with pytest.raises(AcceptanceError, match="stale_version"):
            accept_sources(
                db,
                organization_id=org,
                actor_principal_id=actor,
                checkpoint_id=checkpoint.id,
                sources=sources(),
                preview_digest=DIGEST,
                idempotency_key="stale",
                expected_contract_version="0",
                authorized=True,
            )


def test_same_source_set_is_single_under_distinct_keys_and_concurrency(controlled_c1):
    org, actor = context()
    with app.state.yarvis.persistence.create_session() as db:
        checkpoint_ids = []
        for _ in range(2):
            checkpoint = create_checkpoint(
                db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=True
            )
            checkpoint_ids.append(checkpoint.id)
        db.commit()

    def accept(index: int):
        with app.state.yarvis.persistence.create_session() as db:
            result = accept_sources(
                db,
                organization_id=org,
                actor_principal_id=actor,
                checkpoint_id=checkpoint_ids[index],
                sources=sources(),
                preview_digest=DIGEST,
                idempotency_key=f"concurrent-{index}",
                expected_contract_version="1.0.0",
                authorized=True,
            )
            db.commit()
            return result["batch_id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        batch_ids = list(executor.map(accept, range(2)))

    assert len(set(batch_ids)) == 1
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageBatch)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageReceipt)) == 2
        assert db.scalar(select(func.count()).select_from(NetpayNoUsageHistory)) == 1


def test_acceptance_history_is_database_append_only(controlled_c1):
    org, actor = context()
    with app.state.yarvis.persistence.create_session() as db:
        checkpoint = create_checkpoint(
            db, organization_id=org, actor_principal_id=actor, preview=preview(), authorized=True
        )
        accept_sources(
            db,
            organization_id=org,
            actor_principal_id=actor,
            checkpoint_id=checkpoint.id,
            sources=sources(),
            preview_digest=DIGEST,
            idempotency_key="append-only",
            expected_contract_version="1.0.0",
            authorized=True,
        )
        db.commit()
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text("DELETE FROM netpay_no_usage_history"))

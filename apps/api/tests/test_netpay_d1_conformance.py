"""Synthetic D1 conformance against the real migrated PostgreSQL database."""

import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Event, Lock
from time import monotonic, sleep
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select, text
from sqlalchemy.engine import Engine
from test_netpay_operational_data import headers, setup_data, upload

from yarvis_api.api.routes.netpay_data import _lock
from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.netpay_master import NetpayBranch, NetpayStoreReference
from yarvis_api.models.netpay_operational_data import (
    NoUsageCampaignEntry,
    OperationalDataBatch,
    OperationalDataCommandReceipt,
    OperationalDataRow,
    StoreProfitabilityFact,
)
from yarvis_api.models.principal import Principal, PrincipalMembership

DATASETS = ("monthly_store_profitability", "no_usage_campaign")


def preview(dataset=DATASETS[0], key="upload", value: int | str = 10, period="2026-08", newline="\n"):
    if dataset == DATASETS[0]:
        content = f"Store ID,Mes,Rentabilidad{newline}SYN-STORE-001,{period},{value}{newline}"
    else:
        content = f"RFC,Store ID,Periodo,Meses sin uso{newline}RFC-SYN-ALLOW,SYN-STORE-001,{period},{value}{newline}"
    result = upload("synthetic.csv", content.encode(), dataset, key, "RFC-SYN-ALLOW")
    assert result.status_code in (200, 201), result.text
    return result.json()


def command(batch, action, key, subject="data:operator", reference=None):
    client = TestClient(app)
    try:
        path = f"/netpay/data/datasets/{batch['id']}"
        if action == "match":
            return client.put(
                f"{path}/rows/{batch['rows'][0]['id']}/match",
                headers=headers(subject, key),
                json={"store_reference_id": str(reference)},
            )
        return client.post(
            f"{path}/{action}",
            headers=headers(subject, key),
            json={"preview_token": batch["preview_token"]} if action == "accept" else None,
        )
    finally:
        client.close()


def readback(batch):
    client = TestClient(app)
    try:
        response = client.get(f"/netpay/data/datasets/{batch['id']}/results", headers=headers())
        assert response.status_code == 200, response.text
        return response.json()
    finally:
        client.close()


def race(first, second, *, independent=False):
    """Hold winner after its real DB lock; observe the loser waiting in pg_locks."""
    acquired, release = Event(), Event()
    claimed, guard, holder = [], Lock(), []

    def after_cursor(conn, cursor, statement, parameters, context, executemany):
        if "netpay_operational_data_batches" not in statement or "FOR UPDATE" not in statement:
            return
        with guard:
            if claimed:
                return
            claimed.append(True)
            holder.append(conn.connection.driver_connection.info.backend_pid)
        if claimed:
            acquired.set()
            assert release.wait(15), "test did not release real PostgreSQL lock"

    event.listen(Engine, "after_cursor_execute", after_cursor)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            winner = pool.submit(first)
            try:
                assert acquired.wait(10), "winner failed to reach persistence lock"
                loser = pool.submit(second)
                if independent:
                    second_result = loser.result(timeout=10)
                    assert second_result.status_code == 200
                    assert not winner.done(), "held batch should still be locked"
                    release.set()
                    return winner.result(timeout=10), second_result
                deadline, waiting = monotonic() + 10, False
                while monotonic() < deadline:
                    with app.state.yarvis.persistence.create_session() as observer:
                        waiting = bool(
                            observer.scalar(
                                text(
                                    "SELECT EXISTS (SELECT 1 FROM pg_stat_activity "
                                    "WHERE :holder = ANY(pg_blocking_pids(pid)) AND pid <> :holder)"
                                ),
                                {"holder": holder[0]},
                            )
                        )
                    if waiting:
                        break
                    sleep(0.01)
                assert waiting and not loser.done(), "independent transaction did not contend in PostgreSQL"
            finally:
                release.set()
            return winner.result(timeout=10), loser.result(timeout=10)
    finally:
        event.remove(Engine, "after_cursor_execute", after_cursor)


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("unchanged", [False, True])
@pytest.mark.parametrize("same_key", [False, True])
def test_real_concurrent_accept_is_one_transition(dataset, unchanged, same_key):
    setup_data()
    baseline = preview(dataset)
    if unchanged:
        assert command(baseline, "accept", "baseline").status_code == 200
        batch = preview(dataset, "equivalent", newline="\r\n")
        assert batch["row_counts"]["unchanged"] == 1
    else:
        batch = baseline
    first, second = race(
        lambda: command(batch, "accept", "accept-one"),
        lambda: command(batch, "accept", "accept-one" if same_key else "accept-two"),
    )
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert command(batch, "accept", "accept-one").json() == first.json()
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(StoreProfitabilityFact if dataset == DATASETS[0] else NoUsageCampaignEntry).count() == 1
        events = db.scalars(
            select(DomainEvent).where(
                DomainEvent.aggregate_id == UUID(batch["id"]),
                DomainEvent.event_type == "netpay.operational_dataset.accepted",
            )
        ).all()
        assert len(events) == 1
        receipts = db.scalars(
            select(OperationalDataCommandReceipt).where(
                OperationalDataCommandReceipt.result_batch_id == UUID(batch["id"]),
                OperationalDataCommandReceipt.command_type == "IC-NETPAY-CMD-028",
            )
        ).all()
        assert len(receipts) == (1 if same_key else 2)
        assert all(receipt.result_response_body["status"] == "accepted" for receipt in receipts)
    assert len(readback(batch)) == 1


@pytest.mark.parametrize("first_action", ["accept", "reject"])
@pytest.mark.parametrize("unchanged", [False, True])
def test_real_accept_reject_race_has_durable_loser(first_action, unchanged):
    setup_data()
    batch = preview()
    if unchanged:
        assert command(batch, "accept", "baseline").status_code == 200
        batch = preview(key="equivalent", newline="\r\n")
    other = "reject" if first_action == "accept" else "accept"
    first, second = race(lambda: command(batch, first_action, "winner"), lambda: command(batch, other, "loser"))
    assert first.status_code == 200 and second.status_code == 409
    assert command(batch, other, "loser").json() == second.json()
    with app.state.yarvis.persistence.create_session() as db:
        persisted = db.get(OperationalDataBatch, UUID(batch["id"]))
        assert persisted is not None and persisted.status == ("accepted" if first_action == "accept" else "rejected")
        facts = db.query(StoreProfitabilityFact).filter_by(batch_id=UUID(batch["id"])).count()
        assert facts == (1 if first_action == "accept" and not unchanged else 0)
        receipt = db.scalar(
            select(OperationalDataCommandReceipt).where(OperationalDataCommandReceipt.idempotency_key == "loser")
        )
        assert receipt is not None and receipt.result_status_code == 409
        assert receipt.actor_principal_id and receipt.created_at
        assert receipt.result_response_body["detail"] == second.json()["detail"]
    assert len(readback(batch)) == (1 if first_action == "accept" else 0)


@pytest.mark.parametrize("same_key", [False, True])
def test_real_reject_reject_is_one_event(same_key):
    setup_data()
    batch = preview()
    first, second = race(
        lambda: command(batch, "reject", "reject"),
        lambda: command(batch, "reject", "reject" if same_key else "reject-two"),
    )
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(DomainEvent).filter_by(event_type="netpay.operational_dataset.rejected").count() == 1
        assert db.query(StoreProfitabilityFact).count() == 0


def test_error_receipt_is_inserted_while_idempotency_lock_is_held():
    setup_data()
    batch = preview()
    assert command(batch, "accept", "accept").status_code == 200
    observed = []

    def before_insert(conn, cursor, statement, parameters, context, executemany):
        if (
            statement.startswith("INSERT INTO netpay_operational_data_command_receipts")
            and parameters.get("result_status_code") == 409
        ):
            held = conn.exec_driver_sql(
                "SELECT count(*) FROM pg_locks WHERE pid = pg_backend_pid() AND locktype = 'advisory' AND granted"
            ).scalar_one()
            assert held >= 1
            observed.append(held)

    event.listen(Engine, "before_cursor_execute", before_insert)
    try:
        failed = command(batch, "reject", "error-receipt")
        assert failed.status_code == 409
    finally:
        event.remove(Engine, "before_cursor_execute", before_insert)
    assert len(observed) == 1
    assert command(batch, "reject", "error-receipt").json() == failed.json()


@pytest.mark.parametrize("dataset", DATASETS)
def test_unchanged_provenance_survives_later_changes_and_reload(dataset):
    setup_data()
    first = preview(dataset)
    assert command(first, "accept", "first").status_code == 200
    original = readback(first)[0]
    equivalent = preview(dataset, "equivalent", newline="\r\n")
    accepted = command(equivalent, "accept", "equivalent-accept")
    assert accepted.status_code == 200 and accepted.json()["row_counts"]["unchanged"] == 1
    duplicate = preview(dataset, "retry", newline="\r\n")
    assert duplicate["id"] == equivalent["id"] and duplicate["duplicate_upload"]
    changed = preview(dataset, "changed", value=20)
    assert command(changed, "accept", "changed-accept").status_code == 200
    result = readback(equivalent)[0]
    assert result == {**original, "result": "unchanged"}
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(OperationalDataBatch).count() == 3
        assert db.query(StoreProfitabilityFact if dataset == DATASETS[0] else NoUsageCampaignEntry).count() == 2
        row = db.scalar(select(OperationalDataRow).where(OperationalDataRow.batch_id == UUID(equivalent["id"])))
        assert row is not None and row.controlled_payload["accepted_fact_id"] == original["source_fact_id"]


@pytest.mark.parametrize("dataset", DATASETS)
def test_accept_recomputes_stale_unchanged_projection(dataset):
    setup_data()
    first = preview(dataset)
    assert command(first, "accept", "first").status_code == 200
    stale = preview(dataset, "stale", newline="\r\n")
    intervening = preview(dataset, "intervening", value=30)
    assert command(intervening, "accept", "intervening-accept").status_code == 200
    result = command(stale, "accept", "stale-accept")
    assert result.status_code == 200 and result.json()["row_counts"]["projected_updates"] == 1
    assert readback(stale)[0]["source_batch_id"] == stale["id"]


def test_period_and_nonfinite_validation_and_conflicting_upload_key():
    setup_data()
    batch = preview(period="2026/8")
    assert batch["reporting_period"] == "2026-08"
    assert command(batch, "accept", "accept").status_code == 200
    conflict = upload("synthetic.csv", b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-08,11\n", DATASETS[0], "upload")
    assert conflict.status_code == 409
    for index, period in enumerate(("2026-13", "invalid")):
        invalid = preview(key=f"invalid-{index}", period=period)
        assert invalid["row_counts"]["invalid"] == 1
        assert command(invalid, "accept", f"invalid-accept-{index}").status_code == 409
    invalid = preview(key="infinite", value="inf")
    assert invalid["row_counts"]["invalid"] == 1


@pytest.mark.parametrize("action", ["accept", "reject", "match"])
@pytest.mark.parametrize("authority", ["viewer", "revoked", "foreign"])
def test_d1_mutations_require_effective_authority(action, authority):
    store_id = setup_data()
    batch = preview()
    subject = "data:operator"
    with app.state.yarvis.persistence.create_session() as db:
        principal = db.scalar(select(Principal).where(Principal.external_subject == subject))
        assert principal is not None
        membership = db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id))
        assert membership is not None
        if authority == "viewer":
            membership.role = "netpay_inbox_viewer"
        elif authority == "revoked":
            membership.status, membership.revoked_at = "revoked", datetime.now(timezone.utc)
        else:
            subject = "data:foreign"
        db.commit()
    response = command(batch, action, "unauthorized", subject, store_id)
    assert response.status_code == (404 if authority == "foreign" else 403)
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(StoreProfitabilityFact).count() == 0
        assert db.query(OperationalDataCommandReceipt).filter_by(idempotency_key="unauthorized").count() == 0


@pytest.mark.parametrize("first_action", ["match", "accept"])
def test_real_match_accept_race_preserves_association(first_action):
    store_id = setup_data()
    batch = preview()
    second_action = "accept" if first_action == "match" else "match"
    first, second = race(
        lambda: command(batch, first_action, "first", reference=store_id),
        lambda: command(batch, second_action, "second", reference=store_id),
    )
    assert first.status_code == 200
    assert second.status_code == (409 if first_action == "match" else 404)
    with app.state.yarvis.persistence.create_session() as db:
        row = db.scalar(select(OperationalDataRow).where(OperationalDataRow.batch_id == UUID(batch["id"])))
        assert row is not None and row.store_reference_id == store_id
        if first_action == "match":
            assert row.resolved_by_principal_id is not None
            receipt = db.scalar(
                select(OperationalDataCommandReceipt).where(OperationalDataCommandReceipt.idempotency_key == "first")
            )
            assert (
                receipt is not None
                and receipt.created_at
                and receipt.actor_principal_id == row.resolved_by_principal_id
            )
            assert receipt.result_response_body["_audit"]["request"]["reason_code"] == "confirm_exact_store_id"
            assert receipt.result_response_body["_audit"]["authority"] == "netpay.inbox.manage"
            assert receipt.result_response_body["_audit"]["authentication_source"]
            assert receipt.result_response_body["_audit"]["request"]["row_id"] == str(row.id)


def test_matching_rejects_master_correction_and_inactive_reference():
    store_id = setup_data()
    batch = preview()
    with app.state.yarvis.persistence.create_session() as db:
        reference = db.get(NetpayStoreReference, store_id)
        assert reference is not None
        reference.store_id, reference.normalized_store_id = "OTHER-SYN", "othersyn"
        db.commit()
    assert command(batch, "match", "mismatch", reference=store_id).status_code == 409
    assert command(batch, "accept", "changed-master").status_code == 409
    with app.state.yarvis.persistence.create_session() as db:
        reference = db.get(NetpayStoreReference, store_id)
        assert reference is not None
        reference.active = False
        db.commit()
    assert command(batch, "match", "inactive", reference=store_id).status_code == 404


def add_store(store_id, identifier="SYN-STORE-002"):
    with app.state.yarvis.persistence.create_session() as db:
        original = db.get(NetpayStoreReference, store_id)
        assert original is not None
        branch = db.get(NetpayBranch, original.branch_id)
        assert branch is not None
        extra = NetpayBranch(
            organization_id=original.organization_id,
            company_id=branch.company_id,
            commercial_name=identifier,
            normalized_commercial_name=identifier,
            branch_match_key=identifier,
            branch_kind="physical",
            created_by_principal_id=original.created_by_principal_id,
            updated_by_principal_id=original.updated_by_principal_id,
        )
        db.add(extra)
        db.flush()
        reference = NetpayStoreReference(
            organization_id=original.organization_id,
            branch_id=extra.id,
            store_id=identifier,
            normalized_store_id=identifier.lower().replace("-", ""),
            source_type="synthetic",
            created_by_principal_id=original.created_by_principal_id,
            updated_by_principal_id=original.updated_by_principal_id,
        )
        db.add(reference)
        db.commit()
        return reference.id


def test_independent_batches_do_not_share_an_organization_lock():
    setup_data()
    first, second = preview(key="first"), preview(key="second", period="2026-09")
    accepted, other = race(
        lambda: command(first, "accept", "first-accept"),
        lambda: command(second, "accept", "second-accept"),
        independent=True,
    )
    assert accepted.status_code == other.status_code == 200
    assert readback(first)[0]["reporting_period"] == "2026-08"
    assert readback(second)[0]["reporting_period"] == "2026-09"


@pytest.mark.parametrize("dataset", DATASETS)
def test_mixed_snapshot_preserves_membership_and_rejects_mixed_periods(dataset):
    store = setup_data()
    extra = add_store(store)
    first = preview(dataset)
    assert command(first, "accept", "first").status_code == 200
    if dataset == DATASETS[0]:
        content = b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-08,10\nSYN-STORE-002,2026-08,20\n"
    else:
        content = (
            b"RFC,Store ID,Periodo,Meses sin uso\nRFC-SYN-ALLOW,SYN-STORE-001,2026-08,10\n"
            b"RFC-SYN-ALLOW,SYN-STORE-002,2026-08,20\n"
        )
    mixed = upload("mixed.csv", content, dataset, "mixed", "RFC-SYN-ALLOW").json()
    accepted = command(mixed, "accept", "mixed-accept")
    assert accepted.status_code == 200
    assert accepted.json()["row_counts"]["unchanged"] == accepted.json()["row_counts"]["projected_inserts"] == 1
    results = readback(mixed)
    assert {row["store_reference_id"] for row in results} == {str(store), str(extra)}
    later = preview(dataset, "smaller", newline="\r\n")
    assert command(later, "accept", "smaller-accept").status_code == 200
    assert [row["store_reference_id"] for row in readback(later)] == [str(store)]
    assert len(readback(mixed)) == 2
    invalid = upload(
        "mixed-period.csv", content.replace(b"002,2026-08", b"002,2026-09"), dataset, "mixed-period", "RFC-SYN-ALLOW"
    ).json()
    assert invalid["reporting_period"] is None
    response = command(invalid, "accept", "mixed-period-accept")
    assert response.status_code == 409 and response.json()["detail"] == "dataset_requires_single_period"


@pytest.mark.parametrize("corruption", ["foreign", "period", "dataset", "rejected", "payload", "pointer"])
def test_provenance_corruption_fails_closed(corruption):
    setup_data()
    batch = preview()
    assert command(batch, "accept", "accept").status_code == 200
    equivalent = preview(key="equivalent", newline="\r\n")
    assert command(equivalent, "accept", "equivalent-accept").status_code == 200
    with app.state.yarvis.persistence.create_session() as db:
        source = db.get(OperationalDataBatch, UUID(batch["id"]))
        fact = db.scalar(select(StoreProfitabilityFact))
        assert source is not None and fact is not None
        if corruption == "foreign":
            principal = db.scalar(select(Principal).where(Principal.external_subject == "data:foreign"))
            assert principal is not None
            membership = db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id))
            assert membership is not None
            fact.organization_id = membership.organization_id
        elif corruption == "period":
            fact.reporting_period = "2026-09"
        elif corruption == "dataset":
            source.dataset_type = DATASETS[1]
        elif corruption == "rejected":
            source.status = "rejected"
        elif corruption == "payload":
            fact.profitability = 999
        else:
            row = db.scalar(select(OperationalDataRow).where(OperationalDataRow.batch_id == UUID(equivalent["id"])))
            assert row is not None
            row.controlled_payload = {**row.controlled_payload, "accepted_fact_id": "invalid-pointer"}
        db.commit()
    response = TestClient(app).get(f"/netpay/data/datasets/{equivalent['id']}/results", headers=headers())
    assert response.status_code == 409 and response.json()["detail"] == "accepted_provenance_unverified"


def test_rejected_source_is_not_used_for_unchanged():
    setup_data()
    batch = preview()
    assert command(batch, "accept", "accept").status_code == 200
    with app.state.yarvis.persistence.create_session() as db:
        source = db.get(OperationalDataBatch, UUID(batch["id"]))
        assert source is not None
        source.status = "rejected"  # Simulate inconsistent legacy history, never an API transition.
        db.commit()
    equivalent = preview(key="equivalent", newline="\r\n")
    assert equivalent["row_counts"]["unchanged"] == 0
    assert command(equivalent, "accept", "new-accept").status_code == 200
    assert readback(equivalent)[0]["source_batch_id"] == equivalent["id"]


def test_manual_matching_never_replaces_confirmed_match_concurrently():
    store = setup_data()
    other = add_store(store)
    batch = preview()
    first, second = race(
        lambda: command(batch, "match", "valid", reference=store),
        lambda: command(batch, "match", "incompatible", reference=other),
    )
    assert first.status_code == 200 and second.status_code == 409
    assert second.json()["detail"] == "confirmed_match_cannot_be_replaced"
    assert command(first.json(), "accept", "accept").status_code == 200
    assert readback(batch)[0]["store_reference_id"] == str(store)


def test_filter_replay_cannot_switch_to_another_rfc_with_the_same_store():
    setup_data()
    content = (
        b"RFC,Store ID,Periodo,Meses sin uso\nRFC-SYN-OTHER,SYN-STORE-001,2026-08,99\n"
        b"RFC-SYN-ALLOW,SYN-STORE-001,2026-08,2\n"
    )
    initial = upload("filter.csv", content, DATASETS[1], "initial", "RFC-SYN-ALLOW")
    assert initial.status_code == 201 and initial.json()["rows"][0]["source_row_number"] == 3
    for key in ("initial", "different-key"):
        conflict = upload("filter.csv", content, DATASETS[1], key, "RFC-SYN-OTHER")
        assert conflict.status_code == 409
    assert command(initial.json(), "accept", "accept").status_code == 200
    assert readback(initial.json())[0]["months_without_usage"] == 2


@pytest.mark.parametrize("dataset", DATASETS)
def test_cross_batch_acceptance_serializes_only_the_same_fact_series(dataset):
    store_id = setup_data()
    first, second = preview(dataset), preview(dataset, "other", newline="\r\n")
    with app.state.yarvis.persistence.create_session() as blocker:
        store = blocker.get(NetpayStoreReference, store_id)
        assert store is not None
        _lock(blocker, ["d1-fact", str(store.organization_id), dataset, str(store_id), "2026-08"])
        pid = blocker.scalar(text("SELECT pg_backend_pid()"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            one = pool.submit(command, first, "accept", "one")
            two = pool.submit(command, second, "accept", "two")
            try:
                deadline, waiting = monotonic() + 15, 0
                while monotonic() < deadline:
                    with app.state.yarvis.persistence.create_session() as observer:
                        waiting = observer.scalar(
                            text("SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"),
                            {"pid": pid},
                        )
                    if waiting == 2:
                        break
                    sleep(0.01)
                assert waiting == 2 and not one.done() and not two.done()
            finally:
                blocker.commit()
            results = [one.result(timeout=15), two.result(timeout=15)]
    assert all(response.status_code == 200 for response in results)
    assert sorted(response.json()["row_counts"]["unchanged"] for response in results) == [0, 1]
    assert readback(first)[0]["source_fact_id"] == readback(second)[0]["source_fact_id"]
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(StoreProfitabilityFact if dataset == DATASETS[0] else NoUsageCampaignEntry).count() == 1


def test_manual_matching_is_tenant_scoped_and_creates_no_business_actions():
    from yarvis_api.models.mission_inbox import MissionInboxItem
    from yarvis_api.models.netpay import NetpayDeviceAssignment, NetpayShipment
    from yarvis_api.models.netpay_inbox import CommercialIntakeItem, NetpayCaseNextAction, NetpayServiceCase
    from yarvis_api.models.operational_task import OperationalTask

    store = setup_data()
    client = TestClient(app)
    foreign = client.post(
        "/netpay/data/datasets",
        headers=headers("data:foreign", "foreign-upload"),
        data={"dataset_type": DATASETS[0]},
        files={"file": ("synthetic.csv", b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-08,10\n")},
    )
    assert foreign.status_code == 201
    assert command(foreign.json(), "match", "cross-tenant", "data:foreign", store).status_code == 404
    batch = preview()
    result = command(batch, "match", "manual", reference=store)
    assert result.status_code == 200
    with app.state.yarvis.persistence.create_session() as db:
        for model in (
            CommercialIntakeItem,
            NetpayCaseNextAction,
            NetpayServiceCase,
            OperationalTask,
            MissionInboxItem,
            NetpayDeviceAssignment,
            NetpayShipment,
        ):
            assert db.query(model).count() == 0


def test_manual_resolution_of_unmatched_row_refreshes_preview_counts():
    store = setup_data()
    with app.state.yarvis.persistence.create_session() as db:
        reference = db.get(NetpayStoreReference, store)
        assert reference is not None
        reference.active = False
        db.commit()
    batch = preview()
    assert batch["row_counts"]["unmatched"] == batch["row_counts"]["conflicts"] == 1
    with app.state.yarvis.persistence.create_session() as db:
        reference = db.get(NetpayStoreReference, store)
        assert reference is not None
        reference.active = True
        db.commit()
    matched = command(batch, "match", "resolve", reference=store)
    assert matched.status_code == 200
    counts = matched.json()["row_counts"]
    assert counts["unmatched"] == counts["conflicts"] == counts["invalid"] == 0
    assert counts["matched"] == counts["valid"] == counts["projected_inserts"] == 1
    assert command(matched.json(), "accept", "accept").status_code == 200
    assert len(readback(batch)) == 1


@pytest.mark.parametrize("revoked", [False, True])
def test_preview_upload_and_readback_use_persisted_authority(revoked):
    setup_data()
    batch = preview()
    with app.state.yarvis.persistence.create_session() as db:
        principal = db.scalar(select(Principal).where(Principal.external_subject == "data:operator"))
        assert principal is not None
        membership = db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id))
        assert membership is not None
        if revoked:
            membership.status, membership.revoked_at = "revoked", datetime.now(timezone.utc)
        else:
            membership.role = "netpay_inbox_viewer"
        db.commit()
    client = TestClient(app)
    created = upload("forbidden.csv", b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-09,5\n", DATASETS[0], "forbidden")
    assert created.status_code == 403
    read = client.get(f"/netpay/data/datasets/{batch['id']}", headers=headers())
    assert read.status_code == (403 if revoked else 200)
    foreign = client.get(f"/netpay/data/datasets/{batch['id']}/results", headers=headers("data:foreign"))
    assert foreign.status_code == 404


@contextmanager
def real_http_server():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "yarvis_api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", headers=headers(), timeout=10) as client:
            deadline = monotonic() + 30
            while True:
                assert process.poll() is None, "synthetic API server exited"
                try:
                    if client.get("/netpay/data/datasets").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                assert monotonic() < deadline, "synthetic API server did not start"
                sleep(0.05)
            yield client
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.parametrize("dataset", DATASETS)
def test_http_e2e_survives_api_process_restart(dataset):
    setup_data()
    content = (
        b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026/8,10\n"
        if dataset == DATASETS[0]
        else b"RFC,Store ID,Periodo,Meses sin uso\nRFC-SYN-ALLOW,SYN-STORE-001,2026/8,2\n"
        b"RFC-SYN-OTHER,OTHER-001,2026/8,99\n"
    )
    form = {"dataset_type": dataset, "rfc_filter": "RFC-SYN-ALLOW"}
    with real_http_server() as client:
        created = client.post(
            "/netpay/data/datasets",
            data=form,
            files={"file": ("synthetic.csv", content)},
            headers={"Idempotency-Key": "http-upload"},
        )
        assert created.status_code == 201
        batch = created.json()
        assert batch["reporting_period"] == "2026-08"
        assert len(batch["rows"]) == 1 and "RFC-SYN" not in created.text and "OTHER-001" not in created.text
        accepted = client.post(
            f"/netpay/data/datasets/{batch['id']}/accept",
            json={"preview_token": batch["preview_token"]},
            headers={"Idempotency-Key": "http-accept"},
        )
        assert accepted.status_code == 200
        original = client.get(f"/netpay/data/datasets/{batch['id']}/results").json()
        assert len(original) == 1 and original[0]["source_batch_id"] == batch["id"]
    with real_http_server() as restarted:
        assert restarted.get(f"/netpay/data/datasets/{batch['id']}").json() == accepted.json()
        assert restarted.get(f"/netpay/data/datasets/{batch['id']}/results").json() == original
        replay = restarted.post(
            "/netpay/data/datasets",
            data=form,
            files={"file": ("synthetic.csv", content)},
            headers={"Idempotency-Key": "http-reupload"},
        )
        assert replay.status_code == 200 and replay.json()["id"] == batch["id"]
        assert restarted.get("/netpay/data/datasets").json()["total"] == 1

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from test_netpay_operational_data import setup_data

from yarvis_api.main import app
from yarvis_api.models.netpay_equipment_identity import (
    NetpayEquipmentEvidence,
    NetpayEquipmentIdentity,
    NetpayEquipmentIdentityDecision,
    NetpayStoreEquipmentLink,
)
from yarvis_api.models.netpay_master import NetpayBranch, NetpayStoreReference
from yarvis_api.models.organization import Organization
from yarvis_api.services.netpay_equipment_identity import (
    EquipmentObservation,
    IdentityConflict,
    record_observation,
    supersede,
)


def context():
    store_id = setup_data()
    with app.state.yarvis.persistence.create_session() as db:
        store = db.get(NetpayStoreReference, store_id)
        return store.organization_id, store_id


def observation(org, store=None, key="identity-1", row="2", **changes):
    base = EquipmentObservation(
        organization_id=org,
        idempotency_key=key,
        source_profile="synthetic_global_v1",
        source_batch_reference="synthetic-batch",
        source_hash="a" * 64,
        source_sheet="Synthetic",
        source_row_reference=row,
        observed_period="2026-09",
        valid_from=date(2026, 9, 1),
        valid_to=date(2026, 9, 30),
        store_reference_id=store,
        terminal=" tpv-001 ",
        mid="mid-01",
        serial="ser-01",
    )
    return replace(base, **changes)


def persist(item):
    with app.state.yarvis.persistence.create_session() as db:
        link = record_observation(db, item)
        db.commit()
        return link.id


def second_store(org):
    with app.state.yarvis.persistence.create_session() as db:
        first = db.scalar(select(NetpayStoreReference).where(NetpayStoreReference.organization_id == org))
        branch = NetpayBranch(
            organization_id=org,
            company_id=first.branch_id and db.get(NetpayBranch, first.branch_id).company_id,
            commercial_name="Synthetic Second",
            normalized_commercial_name="syntheticsecond",
            branch_match_key="synthetic-second",
            branch_kind="physical",
            created_by_principal_id=first.created_by_principal_id,
            updated_by_principal_id=first.updated_by_principal_id,
        )
        db.add(branch)
        db.flush()
        store = NetpayStoreReference(
            organization_id=org,
            branch_id=branch.id,
            store_id="SYN-STORE-002",
            normalized_store_id="synstore002",
            source_type="synthetic",
            created_by_principal_id=first.created_by_principal_id,
            updated_by_principal_id=first.updated_by_principal_id,
        )
        db.add(store)
        db.commit()
        return store.id


def test_multiple_equipment_and_original_normalized_provenance():
    org, store = context()
    first = persist(observation(org, store))
    second = persist(observation(org, store, key="identity-2", row="3", terminal="TPV-002", serial="SER-02"))
    assert first != second
    with app.state.yarvis.persistence.create_session() as db:
        identities = db.scalars(
            select(NetpayEquipmentIdentity).where(NetpayEquipmentIdentity.organization_id == org)
        ).all()
        assert {item.identity_kind for item in identities} == {"terminal", "mid", "serial"}
        terminal = next(item for item in identities if item.normalized_value == "TPV001")
        assert terminal.original_value == " tpv-001 " and terminal.normalization_method == "uppercase_alnum_v1"
        evidence = db.scalars(
            select(NetpayEquipmentEvidence).where(NetpayEquipmentEvidence.identity_id == terminal.id)
        ).one()
        assert (evidence.source_batch_reference, evidence.source_sheet, evidence.source_row_reference) == (
            "synthetic-batch",
            "Synthetic",
            "2",
        )


def test_pending_ambiguous_and_nonexistent_store_is_not_created():
    org, store = context()
    other = second_store(org)
    terminal_pending = persist(observation(org, None, mid=None, serial=None))
    serial_pending = persist(observation(org, None, key="serial-pending", row="3", terminal=None, mid=None))
    ambiguous = persist(observation(org, None, key="ambiguous", row="4", candidate_store_reference_ids=(store, other)))
    with app.state.yarvis.persistence.create_session() as db:
        assert db.get(NetpayStoreEquipmentLink, terminal_pending).resolution_status == "pending"
        assert db.get(NetpayStoreEquipmentLink, serial_pending).resolution_status == "pending"
        assert db.get(NetpayStoreEquipmentLink, ambiguous).resolution_status == "ambiguous"
        count = db.scalar(select(func.count()).select_from(NetpayStoreReference))
    with pytest.raises(ValueError, match="does not exist"):
        persist(observation(org, uuid4(), key="missing"))
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(NetpayStoreReference)) == count


def test_overlapping_serial_is_contradictory_but_other_organization_is_isolated():
    org, store = context()
    other = second_store(org)
    persist(observation(org, store))
    contradictory = persist(observation(org, other, key="contradiction", row="3", terminal="TPV-099", mid="MID-99"))
    with app.state.yarvis.persistence.create_session() as db:
        assert db.get(NetpayStoreEquipmentLink, contradictory).resolution_status == "contradictory"
        foreign_org = db.scalar(select(Organization.id).where(Organization.legal_name == "Other Data Org"))
    foreign = persist(observation(foreign_org, None, key="foreign", row="4"))
    with app.state.yarvis.persistence.create_session() as db:
        foreign_link = db.get(NetpayStoreEquipmentLink, foreign)
        assert foreign_link.organization_id == foreign_org
        assert foreign_link.resolution_status == "pending"


def test_distinct_evidence_for_the_same_identity_is_preserved():
    org, store = context()
    first = persist(observation(org, store))
    second = persist(
        observation(
            org,
            store,
            key="second-evidence",
            row="9",
            source_batch_reference="synthetic-batch-2",
            source_hash="b" * 64,
        )
    )
    assert first != second
    with app.state.yarvis.persistence.create_session() as db:
        serial = db.scalar(
            select(NetpayEquipmentIdentity).where(
                NetpayEquipmentIdentity.organization_id == org,
                NetpayEquipmentIdentity.identity_kind == "serial",
                NetpayEquipmentIdentity.normalized_value == "SER01",
            )
        )
        evidence = db.scalars(
            select(NetpayEquipmentEvidence)
            .where(NetpayEquipmentEvidence.identity_id == serial.id)
            .order_by(NetpayEquipmentEvidence.source_row_reference)
        ).all()
        assert [(item.source_batch_reference, item.source_row_reference) for item in evidence] == [
            ("synthetic-batch", "2"),
            ("synthetic-batch-2", "9"),
        ]


def test_replay_conflict_concurrency_and_append_only_history():
    org, store = context()
    item = observation(org, store)
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(persist, (item, item)))
    assert ids[0] == ids[1]
    with pytest.raises(IdentityConflict):
        persist(replace(item, terminal="different"))
    with app.state.yarvis.persistence.create_session() as db:
        link = supersede(
            db,
            organization_id=org,
            link_id=ids[0],
            expected_version=1,
            reason="synthetic correction",
            evidence_reference="synthetic:3",
        )
        db.commit()
        assert link.aggregate_version == 2 and link.resolution_status == "superseded"
    with app.state.yarvis.persistence.create_session() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(NetpayEquipmentIdentityDecision)
                .where(NetpayEquipmentIdentityDecision.link_id == ids[0])
            )
            == 2
        )
        with pytest.raises(IdentityConflict, match="stale"):
            supersede(
                db,
                organization_id=org,
                link_id=ids[0],
                expected_version=1,
                reason="stale",
                evidence_reference="synthetic:4",
            )

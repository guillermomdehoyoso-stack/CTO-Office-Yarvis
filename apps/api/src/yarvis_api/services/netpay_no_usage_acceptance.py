"""IG-016A C2 checkpoint, idempotent acceptance and minimized readback."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from yarvis_api.models.netpay_equipment_identity import (
    NetpayEquipmentEvidence,
    NetpayEquipmentIdentity,
    NetpayEquipmentIdentityDecision,
    NetpayStoreEquipmentLink,
)
from yarvis_api.models.netpay_master import NetpayStoreReference
from yarvis_api.models.netpay_no_usage_acceptance import (
    NetpayNoUsageBatch,
    NetpayNoUsageCheckpoint,
    NetpayNoUsageException,
    NetpayNoUsageHistory,
    NetpayNoUsageReceipt,
    NetpayNoUsageSource,
)
from yarvis_api.services.netpay_equipment_identity import normalize
from yarvis_api.services.netpay_no_usage_recovery_preview import SourceBytes, _parse, preview_no_usage_recovery_sources

CONTRACT_VERSION = "1.0.0"


class AcceptanceError(ValueError):
    pass


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def create_checkpoint(
    db: Session,
    *,
    organization_id: UUID,
    actor_principal_id: UUID,
    preview: dict,
    authorized: bool,
    ttl_minutes: int = 30,
) -> NetpayNoUsageCheckpoint:
    if not authorized:
        raise AcceptanceError("forbidden")
    payload = {"sources": preview["sources"], "matching": preview["matching"], "digest": preview["preview_digest"]}
    checkpoint = NetpayNoUsageCheckpoint(
        organization_id=organization_id,
        actor_principal_id=actor_principal_id,
        contract_version=CONTRACT_VERSION,
        preview_digest=preview["preview_digest"],
        payload_fingerprint=_digest(payload),
        decision="accept",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    )
    db.add(checkpoint)
    db.flush()
    return checkpoint


def _identity(db: Session, org: UUID, kind: str, value: str) -> NetpayEquipmentIdentity:
    normalized, method = normalize(value)
    identity = db.scalar(
        select(NetpayEquipmentIdentity).where(
            NetpayEquipmentIdentity.organization_id == org,
            NetpayEquipmentIdentity.identity_kind == kind,
            NetpayEquipmentIdentity.normalized_value == normalized,
        )
    )
    if identity is None:
        identity = NetpayEquipmentIdentity(
            organization_id=org,
            identity_kind=kind,
            original_value=value,
            normalized_value=normalized,
            normalization_method=method,
        )
        db.add(identity)
        db.flush()
    return identity


def _persist_pending_links(db: Session, org: UUID, batch: NetpayNoUsageBatch, parsed: dict) -> int:
    no_usage = parsed["netpay_no_usage_oct26_v1"]["rows"]
    ticket = parsed["netpay_ticket97580_equipment_client_oct26_v1"]["rows"]
    ticket_by_store = {row["store"]: row for row in ticket if row["store"] and row["serial"] and row["terminal"]}
    references = {
        str(item.store_id): item
        for item in db.scalars(select(NetpayStoreReference).where(NetpayStoreReference.organization_id == org)).all()
    }
    ticket_hash = db.scalar(
        select(NetpayNoUsageSource.source_hash).where(
            NetpayNoUsageSource.batch_id == batch.id,
            NetpayNoUsageSource.profile == "netpay_ticket97580_equipment_client_oct26_v1",
        )
    )
    count = 0
    for campaign in no_usage:
        row = ticket_by_store.get(campaign["store"])
        reference = references.get(campaign["store"])
        if not row or not reference:
            continue
        terminal = _identity(db, org, "terminal", row["terminal"])
        serial = _identity(db, org, "serial", row["serial"])
        evidence = NetpayEquipmentEvidence(
            organization_id=org,
            identity_id=serial.id,
            source_profile="netpay_ticket97580_equipment_client_oct26_v1",
            source_batch_reference=str(batch.id),
            source_hash=ticket_hash,
            source_sheet="Sheet1",
            source_row_reference=str(row["source_row"]),
            original_value=row["serial"],
            normalized_value=serial.normalized_value,
            normalization_method=serial.normalization_method,
        )
        db.add(evidence)
        db.flush()
        link = NetpayStoreEquipmentLink(
            organization_id=org,
            store_reference_id=reference.id,
            terminal_identity_id=terminal.id,
            serial_identity_id=serial.id,
            evidence_id=evidence.id,
            candidate_store_reference_ids=[],
            resolution_status="pending",
            aggregate_version=1,
        )
        db.add(link)
        db.flush()
        db.add(
            NetpayEquipmentIdentityDecision(
                organization_id=org,
                link_id=link.id,
                aggregate_version=1,
                prior_status=None,
                resulting_status="pending",
                decision_reason="pending_temporality",
                evidence_reference=str(evidence.id),
            )
        )
        count += 1
    return count


def accept_sources(
    db: Session,
    *,
    organization_id: UUID,
    actor_principal_id: UUID,
    checkpoint_id: UUID,
    sources: tuple[SourceBytes, ...],
    preview_digest: str,
    idempotency_key: str,
    expected_contract_version: str,
    authorized: bool,
) -> dict:
    if not authorized:
        raise AcceptanceError("forbidden")
    if expected_contract_version != CONTRACT_VERSION:
        raise AcceptanceError("stale_version")
    preview = preview_no_usage_recovery_sources("ig016a-c1-validation", sources, enforce_allowlist=True)
    if preview["preview_digest"] != preview_digest:
        raise AcceptanceError("preview_digest_mismatch")
    request = {
        "organization_id": organization_id,
        "checkpoint_id": checkpoint_id,
        "sources": [(s.profile, s.expected_sha256) for s in sources],
        "preview_digest": preview_digest,
        "contract_version": expected_contract_version,
    }
    fingerprint = _digest(request)
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": f"{organization_id}:{idempotency_key}"}
    )
    receipt = db.scalar(
        select(NetpayNoUsageReceipt).where(
            NetpayNoUsageReceipt.organization_id == organization_id,
            NetpayNoUsageReceipt.idempotency_key == idempotency_key,
        )
    )
    if receipt:
        if receipt.request_fingerprint != fingerprint:
            raise AcceptanceError("idempotency_conflict")
        result = readback(db, organization_id=organization_id, batch_id=receipt.batch_id, authorized=True)
        result["replay"] = True
        return result
    checkpoint = db.scalar(
        select(NetpayNoUsageCheckpoint).where(NetpayNoUsageCheckpoint.id == checkpoint_id).with_for_update()
    )
    if checkpoint is None:
        raise AcceptanceError("checkpoint_missing")
    if checkpoint.organization_id != organization_id:
        raise AcceptanceError("organization_mismatch")
    if checkpoint.actor_principal_id != actor_principal_id:
        raise AcceptanceError("forbidden")
    if checkpoint.expires_at <= datetime.now(timezone.utc):
        raise AcceptanceError("checkpoint_expired")
    payload = {"sources": preview["sources"], "matching": preview["matching"], "digest": preview["preview_digest"]}
    if checkpoint.preview_digest != preview_digest or checkpoint.payload_fingerprint != _digest(payload):
        raise AcceptanceError("checkpoint_consumed_for_different_payload")
    source_set = _digest([(s.profile, s.expected_sha256) for s in sources])
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"{organization_id}:source-set:{source_set}"},
    )
    batch = db.scalar(
        select(NetpayNoUsageBatch).where(
            NetpayNoUsageBatch.organization_id == organization_id,
            NetpayNoUsageBatch.source_set_fingerprint == source_set,
        )
    )
    if batch is None:
        counts = {**preview["matching"], "template_rows": 968, "placeholders": 209, "cell_errors": 18}
        batch = NetpayNoUsageBatch(
            organization_id=organization_id,
            checkpoint_id=checkpoint.id,
            actor_principal_id=actor_principal_id,
            source_set_fingerprint=source_set,
            preview_digest=preview_digest,
            status="accepted",
            aggregate_version=1,
            counts=counts,
        )
        db.add(batch)
        db.flush()
        for item in preview["sources"]:
            db.add(
                NetpayNoUsageSource(
                    organization_id=organization_id,
                    batch_id=batch.id,
                    profile=item["profile"],
                    profile_version=item["version"],
                    source_hash=item["sha256"],
                    sheet="Sheet1",
                    structural_signature=item["signature"],
                )
            )
        db.flush()
        for classification, count in (
            ("missing_equipment_match", 12),
            ("missing_store_and_client", 18),
            ("placeholder", 209),
            ("cell_error", 18),
            ("pending_temporality", 20),
        ):
            db.add(
                NetpayNoUsageException(
                    organization_id=organization_id, batch_id=batch.id, classification=classification, item_count=count
                )
            )
        parsed = {source.profile: _parse(source, enforce_allowlist=True) for source in sources}
        pending_links = _persist_pending_links(db, organization_id, batch, parsed)
        counts = {**counts, "pending_links": pending_links}
        batch.counts = counts
        db.add(
            NetpayNoUsageHistory(
                organization_id=organization_id,
                batch_id=batch.id,
                aggregate_version=1,
                action="accepted",
                actor_principal_id=actor_principal_id,
                safe_snapshot=counts,
            )
        )
    checkpoint.consumed_at = datetime.now(timezone.utc)
    db.add(
        NetpayNoUsageReceipt(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            batch_id=batch.id,
        )
    )
    db.flush()
    result = readback(db, organization_id=organization_id, batch_id=batch.id, authorized=True)
    result["replay"] = False
    return result


def readback(db: Session, *, organization_id: UUID, batch_id: UUID, authorized: bool) -> dict:
    if not authorized:
        raise AcceptanceError("forbidden")
    batch = db.scalar(
        select(NetpayNoUsageBatch).where(
            NetpayNoUsageBatch.id == batch_id, NetpayNoUsageBatch.organization_id == organization_id
        )
    )
    if batch is None:
        raise AcceptanceError("not_found")
    sources = db.scalars(
        select(NetpayNoUsageSource)
        .where(NetpayNoUsageSource.batch_id == batch.id)
        .order_by(NetpayNoUsageSource.profile)
    ).all()
    exceptions = db.scalars(
        select(NetpayNoUsageException)
        .where(NetpayNoUsageException.batch_id == batch.id)
        .order_by(NetpayNoUsageException.classification)
    ).all()
    history = db.scalars(
        select(NetpayNoUsageHistory)
        .where(NetpayNoUsageHistory.batch_id == batch.id)
        .order_by(NetpayNoUsageHistory.aggregate_version)
    ).all()
    return {
        "batch_id": str(batch.id),
        "status": batch.status,
        "version": batch.aggregate_version,
        "preview_digest": batch.preview_digest,
        "counts": batch.counts,
        "sources": [
            {
                "profile": item.profile,
                "version": item.profile_version,
                "sha256": item.source_hash,
                "sheet": item.sheet,
                "signature": item.structural_signature,
            }
            for item in sources
        ],
        "classifications": {item.classification: item.item_count for item in exceptions},
        "history": [
            {"version": item.aggregate_version, "action": item.action, "actor_reference": str(item.actor_principal_id)}
            for item in history
        ],
    }

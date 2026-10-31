"""Internal IG-016 Gate B identity resolution; no public contracts or routes."""

from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from json import dumps
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from yarvis_api.models.netpay_equipment_identity import (
    NetpayEquipmentEvidence,
    NetpayEquipmentIdentity,
    NetpayEquipmentIdentityDecision,
    NetpayEquipmentIdentityReceipt,
    NetpayStoreEquipmentLink,
)
from yarvis_api.models.netpay_master import NetpayStoreReference


class IdentityConflict(ValueError):
    pass


@dataclass(frozen=True)
class EquipmentObservation:
    organization_id: UUID
    idempotency_key: str
    source_profile: str
    source_batch_reference: str
    source_hash: str
    source_sheet: str
    source_row_reference: str
    observed_period: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    store_reference_id: UUID | None = None
    candidate_store_reference_ids: tuple[UUID, ...] = ()
    terminal: str | None = None
    mid: str | None = None
    serial: str | None = None


def normalize(value: str) -> tuple[str, str]:
    original = value.strip()
    normalized = "".join(character for character in original.upper() if character.isalnum())
    if not normalized:
        raise ValueError("identity value must contain letters or digits")
    return normalized, "uppercase_alnum_v1"


def _fingerprint(observation: EquipmentObservation) -> str:
    return sha256(dumps(asdict(observation), sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _identity(
    db: Session, observation: EquipmentObservation, kind: str, value: str
) -> tuple[NetpayEquipmentIdentity, NetpayEquipmentEvidence]:
    normalized, method = normalize(value)
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"{observation.organization_id}:{kind}:{normalized}"},
    )
    identity = db.scalar(
        select(NetpayEquipmentIdentity).where(
            NetpayEquipmentIdentity.organization_id == observation.organization_id,
            NetpayEquipmentIdentity.identity_kind == kind,
            NetpayEquipmentIdentity.normalized_value == normalized,
        )
    )
    if identity is None:
        identity = NetpayEquipmentIdentity(
            organization_id=observation.organization_id,
            identity_kind=kind,
            original_value=value,
            normalized_value=normalized,
            normalization_method=method,
        )
        db.add(identity)
        db.flush()
    evidence = NetpayEquipmentEvidence(
        organization_id=observation.organization_id,
        identity_id=identity.id,
        source_profile=observation.source_profile,
        source_batch_reference=observation.source_batch_reference,
        source_hash=observation.source_hash,
        source_sheet=observation.source_sheet,
        source_row_reference=observation.source_row_reference,
        observed_period=observation.observed_period,
        valid_from=observation.valid_from,
        valid_to=observation.valid_to,
        original_value=value,
        normalized_value=normalized,
        normalization_method=method,
    )
    db.add(evidence)
    db.flush()
    return identity, evidence


def _overlaps(link: NetpayStoreEquipmentLink, start: date | None, end: date | None) -> bool:
    return (link.valid_to is None or start is None or link.valid_to >= start) and (
        end is None or link.valid_from is None or link.valid_from <= end
    )


def record_observation(db: Session, observation: EquipmentObservation) -> NetpayStoreEquipmentLink:
    fingerprint = _fingerprint(observation)
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"{observation.organization_id}:{observation.idempotency_key}"},
    )
    receipt = db.scalar(
        select(NetpayEquipmentIdentityReceipt)
        .where(
            NetpayEquipmentIdentityReceipt.organization_id == observation.organization_id,
            NetpayEquipmentIdentityReceipt.idempotency_key == observation.idempotency_key,
        )
        .with_for_update()
    )
    if receipt:
        if receipt.request_fingerprint != fingerprint:
            raise IdentityConflict("idempotency key reused with a different observation")
        return db.get(NetpayStoreEquipmentLink, receipt.result_link_id)
    if not any((observation.terminal, observation.mid, observation.serial)):
        raise ValueError("at least one equipment identity is required")
    if observation.store_reference_id:
        store = db.scalar(
            select(NetpayStoreReference).where(
                NetpayStoreReference.organization_id == observation.organization_id,
                NetpayStoreReference.id == observation.store_reference_id,
            )
        )
        if store is None:
            raise ValueError("store reference does not exist in organization")
    if observation.candidate_store_reference_ids:
        candidates = set(
            db.scalars(
                select(NetpayStoreReference.id).where(
                    NetpayStoreReference.organization_id == observation.organization_id,
                    NetpayStoreReference.id.in_(observation.candidate_store_reference_ids),
                )
            ).all()
        )
        if candidates != set(observation.candidate_store_reference_ids):
            raise ValueError("candidate Store reference does not exist in organization")
    identities: dict[str, NetpayEquipmentIdentity] = {}
    evidence: NetpayEquipmentEvidence | None = None
    for kind, value in (("terminal", observation.terminal), ("mid", observation.mid), ("serial", observation.serial)):
        if value:
            identities[kind], evidence = _identity(db, observation, kind, value)
    status = (
        "ambiguous"
        if len(observation.candidate_store_reference_ids) > 1
        else "confirmed"
        if observation.store_reference_id
        else "pending"
    )
    serial = identities.get("serial")
    if serial and observation.store_reference_id:
        existing = db.scalars(
            select(NetpayStoreEquipmentLink)
            .where(
                NetpayStoreEquipmentLink.organization_id == observation.organization_id,
                NetpayStoreEquipmentLink.serial_identity_id == serial.id,
                NetpayStoreEquipmentLink.resolution_status.in_(("confirmed", "contradictory")),
            )
            .with_for_update()
        ).all()
        if any(
            item.store_reference_id != observation.store_reference_id
            and _overlaps(item, observation.valid_from, observation.valid_to)
            for item in existing
        ):
            status = "contradictory"
    assert evidence is not None
    link = NetpayStoreEquipmentLink(
        organization_id=observation.organization_id,
        store_reference_id=observation.store_reference_id,
        terminal_identity_id=getattr(identities.get("terminal"), "id", None),
        mid_identity_id=getattr(identities.get("mid"), "id", None),
        serial_identity_id=getattr(serial, "id", None),
        evidence_id=evidence.id,
        candidate_store_reference_ids=[str(item) for item in observation.candidate_store_reference_ids],
        valid_from=observation.valid_from,
        valid_to=observation.valid_to,
        resolution_status=status,
    )
    db.add(link)
    db.flush()
    db.add(
        NetpayEquipmentIdentityDecision(
            organization_id=observation.organization_id,
            link_id=link.id,
            aggregate_version=1,
            prior_status=None,
            resulting_status=status,
            decision_reason="synthetic_identity_observation",
            evidence_reference=f"{observation.source_batch_reference}:{observation.source_sheet}:{observation.source_row_reference}",
        )
    )
    db.add(
        NetpayEquipmentIdentityReceipt(
            organization_id=observation.organization_id,
            idempotency_key=observation.idempotency_key,
            request_fingerprint=fingerprint,
            result_link_id=link.id,
        )
    )
    db.flush()
    return link


def supersede(
    db: Session, *, organization_id: UUID, link_id: UUID, expected_version: int, reason: str, evidence_reference: str
) -> NetpayStoreEquipmentLink:
    link = db.scalar(
        select(NetpayStoreEquipmentLink)
        .where(NetpayStoreEquipmentLink.organization_id == organization_id, NetpayStoreEquipmentLink.id == link_id)
        .with_for_update()
    )
    if link is None:
        raise ValueError("identity link not found")
    if link.aggregate_version != expected_version:
        raise IdentityConflict("stale aggregate version")
    prior = link.resolution_status
    link.resolution_status = "superseded"
    link.aggregate_version += 1
    db.add(
        NetpayEquipmentIdentityDecision(
            organization_id=organization_id,
            link_id=link.id,
            aggregate_version=link.aggregate_version,
            prior_status=prior,
            resulting_status="superseded",
            decision_reason=reason,
            evidence_reference=evidence_reference,
        )
    )
    db.flush()
    return link

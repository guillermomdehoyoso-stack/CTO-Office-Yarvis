"""IG-016A C3 local synthetic case, queue and protected-contact services."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.models.netpay_equipment_identity import NetpayEquipmentEvidence, NetpayStoreEquipmentLink
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.netpay_no_usage_acceptance import NetpayNoUsageException
from yarvis_api.models.netpay_protection_case import (
    NetpayProtectionCase,
    NetpayProtectionCaseHistory,
    NetpayProtectionCommandReceipt,
    NetpayProtectionSensitiveAccess,
)

CASE_REASONS = frozenset({"no_usage", "missing_equipment_match", "missing_store_and_client", "pending_temporality"})
NEXT_ACTIONS = frozenset(
    {"resolve_identity", "obtain_contact", "contact_merchant", "follow_up_reactivation", "follow_up_return", "escalate"}
)
CONTACT_CHANNELS = frozenset({"phone", "email", "other_authorized"})
CONTACT_RESULTS = frozenset({"reached", "no_answer", "invalid_contact", "follow_up_required"})
RECOVERY_PATHS = frozenset({"reactivate", "return_equipment", "monitor", "unrecoverable"})
ESCALATION_REASONS = frozenset(
    {"identity_blocked", "contact_blocked", "authority_blocked", "business_decision_required"}
)
PURPOSE_CODES = frozenset({"merchant_recovery_contact"})

TRANSITIONS = {
    "identity_pending": {"contact_pending", "ready_to_contact", "escalated", "unrecoverable"},
    "contact_pending": {"ready_to_contact", "escalated", "unrecoverable"},
    "ready_to_contact": {"contact_attempted", "escalated", "unrecoverable"},
    "contact_attempted": {
        "ready_to_contact",
        "reactivation_agreed",
        "return_requested",
        "monitoring",
        "escalated",
        "unrecoverable",
    },
    "reactivation_agreed": {"monitoring", "escalated", "unrecoverable"},
    "return_requested": {"monitoring", "escalated", "unrecoverable"},
    "monitoring": {"ready_to_contact", "contact_attempted", "escalated", "unrecoverable"},
    "escalated": {
        "identity_pending",
        "contact_pending",
        "ready_to_contact",
        "contact_attempted",
        "monitoring",
        "unrecoverable",
    },
    "unrecoverable": set(),
}


class ProtectionCaseError(ValueError):
    pass


def _require(authority: IdentityAuthorityEnvelope, organization_id: UUID, *permissions: str) -> None:
    if authority.organization_id != organization_id:
        raise ProtectionCaseError("resource_not_found")
    for permission in permissions:
        try:
            authority.require(permission)
        except Exception as error:
            raise ProtectionCaseError("forbidden") from error


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _catalog(value: str, allowed: frozenset[str]) -> str:
    if value not in allowed:
        raise ProtectionCaseError("unsupported_catalog_value")
    return value


def _receipt(db: Session, organization_id: UUID, key: str, fingerprint: str) -> dict | None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": f"c3:{organization_id}:{key}"})
    receipt = db.scalar(
        select(NetpayProtectionCommandReceipt).where(
            NetpayProtectionCommandReceipt.organization_id == organization_id,
            NetpayProtectionCommandReceipt.idempotency_key == key,
        )
    )
    if receipt is None:
        return None
    if receipt.request_fingerprint != fingerprint:
        raise ProtectionCaseError("idempotency_conflict")
    return dict(receipt.response_body)


def _save_receipt(
    db: Session, *, organization_id: UUID, command_id: str, key: str, fingerprint: str, case_id: UUID | None, body: dict
) -> dict:
    db.add(
        NetpayProtectionCommandReceipt(
            organization_id=organization_id,
            command_id=command_id,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            case_id=case_id,
            response_body=body,
        )
    )
    db.flush()
    return body


def resolve_store_equipment_link(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    link_id: UUID,
    expected_version: int,
    observed_at: datetime,
    valid_from: datetime,
    valid_to: datetime | None,
    idempotency_key: str,
    local_disposable: bool,
) -> dict:
    organization_id = authority.organization_id
    _require(authority, organization_id, "netpay.inbox.manage", "netpay.portfolio.reconciliation.read")
    payload = {
        "link": link_id,
        "version": expected_version,
        "observed_at": observed_at,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }
    fingerprint = _digest(payload)
    replay = _receipt(db, organization_id, idempotency_key, fingerprint)
    if replay is not None:
        return replay
    if not local_disposable:
        raise ProtectionCaseError("synthetic_profile_forbidden")
    if any(item.tzinfo is None for item in (observed_at, valid_from) if item is not None) or (
        valid_to and valid_to.tzinfo is None
    ):
        raise ProtectionCaseError("invalid_temporal_interval")
    if valid_to is not None and valid_to <= valid_from:
        raise ProtectionCaseError("invalid_temporal_interval")
    if observed_at < valid_from or (valid_to is not None and observed_at >= valid_to):
        raise ProtectionCaseError("invalid_temporal_interval")
    link = db.scalar(
        select(NetpayStoreEquipmentLink)
        .where(NetpayStoreEquipmentLink.id == link_id, NetpayStoreEquipmentLink.organization_id == organization_id)
        .with_for_update()
    )
    if link is None:
        raise ProtectionCaseError("resource_not_found")
    evidence = db.scalar(select(NetpayEquipmentEvidence).where(NetpayEquipmentEvidence.id == link.evidence_id))
    if (
        evidence is None
        or evidence.source_profile != "synthetic_c3_temporality_v1"
        or evidence.source_batch_reference != "synthetic_fixture"
    ):
        raise ProtectionCaseError("synthetic_profile_required")
    if link.aggregate_version != expected_version:
        body = {"result": "stale_version", "link_id": str(link.id), "version": link.aggregate_version}
        return _save_receipt(
            db,
            organization_id=organization_id,
            command_id="IC-NETPAY-CMD-044",
            key=idempotency_key,
            fingerprint=fingerprint,
            case_id=None,
            body=body,
        )
    link.valid_from = valid_from.date()
    link.valid_to = valid_to.date() if valid_to else None
    link.resolution_status = "confirmed"
    link.aggregate_version += 1
    body = {
        "result": "transition_applied",
        "link_id": str(link.id),
        "version": link.aggregate_version,
        "status": "confirmed",
    }
    return _save_receipt(
        db,
        organization_id=organization_id,
        command_id="IC-NETPAY-CMD-044",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=None,
        body=body,
    )


def retrieve_store_equipment_identity(
    db: Session, *, authority: IdentityAuthorityEnvelope, source_kind: str, source_id: UUID
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.portfolio.reconciliation.read")
    if source_kind == "link":
        item = db.scalar(
            select(NetpayStoreEquipmentLink).where(
                NetpayStoreEquipmentLink.id == source_id, NetpayStoreEquipmentLink.organization_id == org
            )
        )
        if item is None:
            raise ProtectionCaseError("resource_not_found")
        return {
            "source_kind": "link",
            "source_id": str(item.id),
            "store_reference_id": str(item.store_reference_id) if item.store_reference_id else None,
            "status": item.resolution_status,
            "version": item.aggregate_version,
            "has_terminal": item.terminal_identity_id is not None,
            "has_serial": item.serial_identity_id is not None,
            "has_mid": item.mid_identity_id is not None,
        }
    item = db.scalar(
        select(NetpayNoUsageException).where(
            NetpayNoUsageException.id == source_id, NetpayNoUsageException.organization_id == org
        )
    )
    if item is None:
        raise ProtectionCaseError("resource_not_found")
    return {
        "source_kind": "batch_exception",
        "source_id": str(item.id),
        "classification": item.classification,
        "item_count": item.item_count,
    }


def open_case(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    source_kind: str,
    source_id: UUID,
    cause_code: str,
    expected_source_version: int | None,
    idempotency_key: str,
    correlation_id: str,
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.inbox.manage", "netpay.portfolio.reconciliation.read")
    _catalog(cause_code, CASE_REASONS)
    if source_kind not in {"link", "batch_exception"}:
        raise ProtectionCaseError("unsupported_catalog_value")
    payload = {
        "source_kind": source_kind,
        "source_id": source_id,
        "cause": cause_code,
        "source_version": expected_source_version,
    }
    fingerprint = _digest(payload)
    replay = _receipt(db, org, idempotency_key, fingerprint)
    if replay is not None:
        return replay
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"c3-source:{org}:{source_kind}:{source_id}:{cause_code}"},
    )
    existing = db.scalar(
        select(NetpayProtectionCase).where(
            NetpayProtectionCase.organization_id == org,
            NetpayProtectionCase.source_kind == source_kind,
            NetpayProtectionCase.source_id == source_id,
            NetpayProtectionCase.cause_code == cause_code,
            NetpayProtectionCase.terminal_at.is_(None),
        )
    )
    if existing:
        body = {"result": "case_already_exists", "case_id": str(existing.id), "version": existing.aggregate_version}
        return _save_receipt(
            db,
            organization_id=org,
            command_id="IC-NETPAY-CMD-045",
            key=idempotency_key,
            fingerprint=fingerprint,
            case_id=existing.id,
            body=body,
        )
    store_id = None
    status = "identity_pending"
    if source_kind == "link":
        source = db.scalar(
            select(NetpayStoreEquipmentLink).where(
                NetpayStoreEquipmentLink.id == source_id, NetpayStoreEquipmentLink.organization_id == org
            )
        )
        if source is None:
            raise ProtectionCaseError("resource_not_found")
        if expected_source_version != source.aggregate_version:
            body = {"result": "stale_version", "source_id": str(source.id), "version": source.aggregate_version}
            return _save_receipt(
                db,
                organization_id=org,
                command_id="IC-NETPAY-CMD-045",
                key=idempotency_key,
                fingerprint=fingerprint,
                case_id=None,
                body=body,
            )
        store_id = source.store_reference_id
        if source.resolution_status == "confirmed":
            status = "contact_pending"
    else:
        source = db.scalar(
            select(NetpayNoUsageException).where(
                NetpayNoUsageException.id == source_id, NetpayNoUsageException.organization_id == org
            )
        )
        if source is None:
            raise ProtectionCaseError("resource_not_found")
    case = NetpayProtectionCase(
        organization_id=org,
        source_kind=source_kind,
        source_id=source_id,
        store_reference_id=store_id,
        cause_code=cause_code,
        status=status,
        aggregate_version=1,
    )
    db.add(case)
    db.flush()
    db.add(
        NetpayProtectionCaseHistory(
            organization_id=org,
            case_id=case.id,
            aggregate_version=1,
            prior_status=None,
            resulting_status=status,
            action_code="case_opened",
            reason_code=cause_code,
            actor_principal_id=authority.principal_id,
            correlation_id=correlation_id,
        )
    )
    body = {"result": "created", "case_id": str(case.id), "version": 1, "status": status}
    return _save_receipt(
        db,
        organization_id=org,
        command_id="IC-NETPAY-CMD-045",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case.id,
        body=body,
    )


def _mutate(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_version: int,
    idempotency_key: str,
    command_id: str,
    payload: dict,
    target: str,
    action: str,
    reason: str,
    correlation_id: str,
    sensitive: bool = False,
    updates: dict | None = None,
) -> dict:
    org = authority.organization_id
    permissions = ["netpay.inbox.manage"] + (["netpay.portfolio.sensitive.read"] if sensitive else [])
    _require(authority, org, *permissions)
    fingerprint = _digest({"case": case_id, "version": expected_version, **payload})
    replay = _receipt(db, org, idempotency_key, fingerprint)
    if replay is not None:
        return replay
    case = db.scalar(
        select(NetpayProtectionCase)
        .where(NetpayProtectionCase.id == case_id, NetpayProtectionCase.organization_id == org)
        .with_for_update()
    )
    if case is None:
        raise ProtectionCaseError("resource_not_found")
    if case.aggregate_version != expected_version:
        body = {"result": "stale_version", "case_id": str(case.id), "version": case.aggregate_version}
        return _save_receipt(
            db,
            organization_id=org,
            command_id=command_id,
            key=idempotency_key,
            fingerprint=fingerprint,
            case_id=case.id,
            body=body,
        )
    if target not in TRANSITIONS[case.status]:
        raise ProtectionCaseError("invalid_transition")
    prior = case.status
    case.status = target
    case.aggregate_version += 1
    case.updated_at = datetime.now(timezone.utc)
    if target == "unrecoverable":
        case.terminal_at = datetime.now(timezone.utc)
    for key, value in (updates or {}).items():
        setattr(case, key, value)
    db.add(
        NetpayProtectionCaseHistory(
            organization_id=org,
            case_id=case.id,
            aggregate_version=case.aggregate_version,
            prior_status=prior,
            resulting_status=target,
            action_code=action,
            reason_code=reason,
            actor_principal_id=authority.principal_id,
            correlation_id=correlation_id,
        )
    )
    body = {
        "result": "transition_applied",
        "case_id": str(case.id),
        "version": case.aggregate_version,
        "status": target,
    }
    return _save_receipt(
        db,
        organization_id=org,
        command_id=command_id,
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case.id,
        body=body,
    )


def assign_and_plan(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_version: int,
    assigned_principal_id: UUID,
    next_action_code: str,
    commitment_at: datetime | None,
    target_status: str,
    idempotency_key: str,
    correlation_id: str,
) -> dict:
    _catalog(next_action_code, NEXT_ACTIONS)
    return _mutate(
        db,
        authority=authority,
        case_id=case_id,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        command_id="IC-NETPAY-CMD-046",
        payload={
            "assignee": assigned_principal_id,
            "next": next_action_code,
            "commitment": commitment_at,
            "target": target_status,
        },
        target=target_status,
        action="assigned_and_planned",
        reason=next_action_code,
        correlation_id=correlation_id,
        updates={
            "assigned_principal_id": assigned_principal_id,
            "next_action_code": next_action_code,
            "commitment_at": commitment_at,
        },
    )


def record_contact_attempt(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_version: int,
    channel_code: str,
    result_code: str,
    access_reference: str,
    idempotency_key: str,
    correlation_id: str,
) -> dict:
    _catalog(channel_code, CONTACT_CHANNELS)
    _catalog(result_code, CONTACT_RESULTS)
    access = db.scalar(
        select(NetpayProtectionSensitiveAccess).where(
            NetpayProtectionSensitiveAccess.opaque_reference == access_reference,
            NetpayProtectionSensitiveAccess.organization_id == authority.organization_id,
            NetpayProtectionSensitiveAccess.case_id == case_id,
            NetpayProtectionSensitiveAccess.actor_principal_id == authority.principal_id,
        )
    )
    if access is None or access.expires_at <= datetime.now(timezone.utc):
        raise ProtectionCaseError("contact_reference_invalid")
    case = db.scalar(
        select(NetpayProtectionCase).where(
            NetpayProtectionCase.id == case_id,
            NetpayProtectionCase.organization_id == authority.organization_id,
        )
    )
    current = _contact(db, case) if case is not None else None
    if current is None or current[1] != access.master_version:
        raise ProtectionCaseError("contact_reference_stale")
    return _mutate(
        db,
        authority=authority,
        case_id=case_id,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        command_id="IC-NETPAY-CMD-047",
        payload={"channel": channel_code, "result": result_code, "access": access_reference},
        target="contact_attempted",
        action="contact_attempted",
        reason=result_code,
        correlation_id=correlation_id,
        sensitive=True,
    )


def decide_recovery_path(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_version: int,
    recovery_path_code: str,
    idempotency_key: str,
    correlation_id: str,
) -> dict:
    _catalog(recovery_path_code, RECOVERY_PATHS)
    target = {
        "reactivate": "reactivation_agreed",
        "return_equipment": "return_requested",
        "monitor": "monitoring",
        "unrecoverable": "unrecoverable",
    }[recovery_path_code]
    return _mutate(
        db,
        authority=authority,
        case_id=case_id,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        command_id="IC-NETPAY-CMD-048",
        payload={"path": recovery_path_code},
        target=target,
        action="recovery_path_decided",
        reason=recovery_path_code,
        correlation_id=correlation_id,
    )


def list_cases(
    db: Session, *, authority: IdentityAuthorityEnvelope, status: str | None = None, limit: int = 50, offset: int = 0
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.portfolio.read")
    if limit < 1 or limit > 100 or offset < 0:
        raise ProtectionCaseError("invalid_pagination")
    query = select(NetpayProtectionCase).where(NetpayProtectionCase.organization_id == org)
    if status:
        query = query.where(NetpayProtectionCase.status == status)
    rows = db.scalars(
        query.order_by(NetpayProtectionCase.created_at, NetpayProtectionCase.id).limit(limit).offset(offset)
    ).all()
    return {
        "items": [
            {
                "case_id": str(row.id),
                "status": row.status,
                "cause_code": row.cause_code,
                "version": row.aggregate_version,
                "next_action_code": row.next_action_code,
                "contact_available": row.contact_available,
            }
            for row in rows
        ],
        "limit": limit,
        "offset": offset,
    }


def _contact(db: Session, case: NetpayProtectionCase) -> tuple[dict, str] | None:
    if case.store_reference_id is None:
        return None
    row = db.execute(
        select(NetpayClient, NetpayCompany, NetpayBranch, NetpayStoreReference)
        .join(NetpayCompany, NetpayCompany.client_id == NetpayClient.id)
        .join(NetpayBranch, NetpayBranch.company_id == NetpayCompany.id)
        .join(NetpayStoreReference, NetpayStoreReference.branch_id == NetpayBranch.id)
        .where(
            NetpayStoreReference.id == case.store_reference_id,
            NetpayStoreReference.organization_id == case.organization_id,
            NetpayStoreReference.active.is_(True),
            NetpayClient.status == "active",
            NetpayCompany.status == "active",
            NetpayBranch.status == "active",
        )
    ).first()
    if not row:
        return None
    client, company, branch, store = row
    contact = {
        "name": branch.contact_name or company.contact_name or client.primary_contact_name,
        "email": branch.contact_email or company.contact_email or client.primary_email,
        "phone": branch.contact_phone or company.contact_phone or client.primary_phone,
    }
    if not any(contact.values()):
        return None
    return contact, _digest(
        {
            "client": client.updated_at,
            "company": company.updated_at,
            "branch": branch.updated_at,
            "store": store.updated_at,
        }
    )


def retrieve_case(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    include_contact: bool = False,
    purpose_code: str | None = None,
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.portfolio.read")
    case = db.scalar(
        select(NetpayProtectionCase).where(
            NetpayProtectionCase.id == case_id, NetpayProtectionCase.organization_id == org
        )
    )
    if case is None:
        raise ProtectionCaseError("resource_not_found")
    history = db.scalars(
        select(NetpayProtectionCaseHistory)
        .where(NetpayProtectionCaseHistory.case_id == case.id)
        .order_by(NetpayProtectionCaseHistory.aggregate_version)
    ).all()
    result = {
        "case_id": str(case.id),
        "status": case.status,
        "cause_code": case.cause_code,
        "version": case.aggregate_version,
        "history": [
            {
                "version": h.aggregate_version,
                "from": h.prior_status,
                "to": h.resulting_status,
                "action_code": h.action_code,
                "reason_code": h.reason_code,
            }
            for h in history
        ],
    }
    if not include_contact:
        return result
    _require(authority, org, "netpay.portfolio.sensitive.read")
    _catalog(purpose_code or "", PURPOSE_CODES)
    found = _contact(db, case)
    if found is None:
        raise ProtectionCaseError("contact_unavailable")
    contact, master_version = found
    opaque = secrets.token_hex(24)
    db.add(
        NetpayProtectionSensitiveAccess(
            organization_id=org,
            case_id=case.id,
            actor_principal_id=authority.principal_id,
            purpose_code=purpose_code or "",
            master_version=master_version,
            opaque_reference=opaque,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
    )
    db.flush()
    result["contact"] = contact
    result["contact_access_reference"] = opaque
    result["contact_access_expires_in_seconds"] = 300
    return result

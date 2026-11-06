"""IG-016A C4 local synthetic outcome and financial assessment services."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid4

from sqlalchemy import exists, select, text
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.models.netpay_protection_case import (
    NetpayProtectionCase,
    NetpayProtectionCaseHistory,
    NetpayProtectionFinancialSnapshot,
    NetpayProtectionOutcomeAssessment,
    NetpayProtectionOutcomeEvidence,
    NetpayProtectionOutcomeReceipt,
)
from yarvis_api.services.netpay_protection_cases import ProtectionCaseError

PROFILES = frozenset(
    {
        "synthetic_c4_activity_v1",
        "synthetic_c4_return_inventory_v1",
        "synthetic_c4_financial_effect_v1",
    }
)
CERTAINTIES = {"projected": 0, "supported": 1, "confirmed": 2}
OPERATIONAL_VERIFIED = frozenset({"reactivation_verified", "equipment_return_verified"})
CLOSURE_GAPS = frozenset(
    {
        "financial_window_pending",
        "financial_source_incomplete",
        "missing_operational_evidence",
        "contradictory_evidence",
        "not_recoverable",
    }
)


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require(authority: IdentityAuthorityEnvelope, organization_id: UUID, *permissions: str) -> None:
    if authority.organization_id != organization_id:
        raise ProtectionCaseError("resource_not_found")
    for permission in permissions:
        try:
            authority.require(permission)
        except Exception as error:
            raise ProtectionCaseError("forbidden") from error


def _save_receipt(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    command_id: str,
    key: str,
    fingerprint: str,
    case_id: UUID | None,
    body: dict,
) -> dict:
    db.add(
        NetpayProtectionOutcomeReceipt(
            organization_id=authority.organization_id,
            command_id=command_id,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            case_id=case_id,
            response_body=body,
        )
    )
    db.flush()
    return body


def _attempt(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    command_id: str,
    key: str,
    fingerprint: str,
    case_id: UUID | None,
) -> dict | None:
    org = authority.organization_id
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": f"c4:{org}:{key}"})
    exact = db.scalar(
        select(NetpayProtectionOutcomeReceipt).where(
            NetpayProtectionOutcomeReceipt.organization_id == org,
            NetpayProtectionOutcomeReceipt.idempotency_key == key,
            NetpayProtectionOutcomeReceipt.request_fingerprint == fingerprint,
        )
    )
    if exact is not None:
        return dict(exact.response_body)
    prior = db.scalar(
        select(NetpayProtectionOutcomeReceipt).where(
            NetpayProtectionOutcomeReceipt.organization_id == org,
            NetpayProtectionOutcomeReceipt.idempotency_key == key,
        )
    )
    if prior is not None:
        return _save_receipt(
            db,
            authority=authority,
            command_id=command_id,
            key=key,
            fingerprint=fingerprint,
            case_id=case_id,
            body={"result": "idempotency_conflict"},
        )
    return None


def _current_evidence(db: Session, org: UUID, case_id: UUID) -> NetpayProtectionOutcomeEvidence | None:
    child = NetpayProtectionOutcomeEvidence.__table__.alias("evidence_child")
    return db.scalar(
        select(NetpayProtectionOutcomeEvidence)
        .where(
            NetpayProtectionOutcomeEvidence.organization_id == org,
            NetpayProtectionOutcomeEvidence.case_id == case_id,
            ~exists(select(1).where(child.c.supersedes_evidence_id == NetpayProtectionOutcomeEvidence.id)),
        )
        .order_by(NetpayProtectionOutcomeEvidence.created_at.desc())
    )


def _current_assessment(db: Session, org: UUID, case_id: UUID) -> NetpayProtectionOutcomeAssessment | None:
    child = NetpayProtectionOutcomeAssessment.__table__.alias("assessment_child")
    return db.scalar(
        select(NetpayProtectionOutcomeAssessment)
        .where(
            NetpayProtectionOutcomeAssessment.organization_id == org,
            NetpayProtectionOutcomeAssessment.case_id == case_id,
            ~exists(select(1).where(child.c.supersedes_assessment_id == NetpayProtectionOutcomeAssessment.id)),
        )
        .order_by(NetpayProtectionOutcomeAssessment.created_at.desc())
    )


def _current_snapshot(db: Session, org: UUID, case_id: UUID) -> NetpayProtectionFinancialSnapshot | None:
    child = NetpayProtectionFinancialSnapshot.__table__.alias("snapshot_child")
    return db.scalar(
        select(NetpayProtectionFinancialSnapshot)
        .where(
            NetpayProtectionFinancialSnapshot.organization_id == org,
            NetpayProtectionFinancialSnapshot.case_id == case_id,
            ~exists(select(1).where(child.c.supersedes_snapshot_id == NetpayProtectionFinancialSnapshot.id)),
        )
        .order_by(NetpayProtectionFinancialSnapshot.created_at.desc())
    )


def _validate_temporal(
    *, profile: str, occurred_at: datetime, observed_at: datetime, valid_from: datetime, valid_to: datetime
) -> None:
    if profile not in PROFILES:
        raise ProtectionCaseError("unsupported_profile")
    if any(value.tzinfo is None for value in (occurred_at, observed_at, valid_from, valid_to)):
        raise ProtectionCaseError("invalid_temporal_interval")
    if not valid_from < valid_to or not valid_from < occurred_at <= observed_at or occurred_at >= valid_to:
        raise ProtectionCaseError("invalid_temporal_interval")
    if occurred_at > datetime.now(timezone.utc):
        raise ProtectionCaseError("future_evidence")


def _money(
    components: list[dict], category: str, certainty: str
) -> tuple[Decimal | None, str | None, list[dict]]:
    if certainty not in CERTAINTIES:
        raise ProtectionCaseError("invalid_certainty")
    tokens: set[str] = set()
    currencies = {item.get("currency") for item in components if item.get("currency")}
    for item in components:
        fingerprint = item.get("fingerprint")
        lineage = [fingerprint, *(item.get("derived_from") or [])]
        if not fingerprint or any(token in tokens for token in lineage):
            raise ProtectionCaseError("overlapping_financial_component")
        tokens.update(lineage)
    if len(currencies) > 1:
        raise ProtectionCaseError("incompatible_currency")
    values = [(item.get("category"), Decimal(str(item.get("amount")))) for item in components]
    penalties = abs(sum((min(value, Decimal("0")) for kind, value in values if kind == "penalty"), Decimal("0")))
    credits = sum((max(value, Decimal("0")) for kind, value in values if kind == "credit"), Decimal("0"))
    baseline = sum((abs(value) for kind, value in values if kind == "baseline_penalty"), Decimal("0"))
    observed = sum((abs(value) for kind, value in values if kind == "observed_penalty"), Decimal("0"))
    if category == "recovered_amount_supported":
        amount = min(credits, penalties)
    elif category in {"penalty_non_recurrence_supported", "avoided_penalty_projected"}:
        amount = max(Decimal("0"), baseline - observed)
    elif category == "applied_penalty_observed":
        amount = penalties
    elif category == "credit_observed":
        amount = credits
    elif category == "financial_effect_not_calculable":
        return None, next(iter(currencies), None), components
    else:
        raise ProtectionCaseError("unsupported_financial_category")
    if category == "avoided_penalty_projected" and certainty != "projected":
        raise ProtectionCaseError("invalid_certainty")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN), next(iter(currencies), None), components


def record_outcome_evidence(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_case_version: int,
    profile_version: str,
    evidence_kind: str,
    source_reference: str,
    identity_scope: str,
    occurred_at: datetime,
    observed_at: datetime,
    valid_from: datetime,
    valid_to: datetime,
    idempotency_key: str,
    correlation_id: str,
    local_disposable: bool,
    supersedes_evidence_id: UUID | None = None,
    evidence_id: UUID | None = None,
    period_key: str | None = None,
    financial_category: str | None = None,
    financial_certainty: str = "supported",
    financial_components: list[dict] | None = None,
) -> dict:
    org = authority.organization_id
    if supersedes_evidence_id is not None and not isinstance(supersedes_evidence_id, UUID):
        supersedes_evidence_id = UUID(str(supersedes_evidence_id))
    if evidence_id is not None and not isinstance(evidence_id, UUID):
        evidence_id = UUID(str(evidence_id))
    _require(authority, org, "netpay.inbox.manage", "netpay.portfolio.reconciliation.read")
    if not local_disposable:
        raise ProtectionCaseError("synthetic_profile_forbidden")
    _validate_temporal(
        profile=profile_version,
        occurred_at=occurred_at,
        observed_at=observed_at,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    payload = {
        "case": case_id,
        "version": expected_case_version,
        "profile": profile_version,
        "kind": evidence_kind,
        "reference": source_reference,
        "scope": identity_scope,
        "occurred": occurred_at,
        "observed": observed_at,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "supersedes": supersedes_evidence_id,
        "period": period_key,
        "financial_category": financial_category,
        "certainty": financial_certainty,
        "components": financial_components,
    }
    fingerprint = _digest(payload)
    replay = _attempt(
        db,
        authority=authority,
        command_id="IC-NETPAY-CMD-049",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case_id,
    )
    if replay is not None:
        return replay
    case = db.scalar(
        select(NetpayProtectionCase)
        .where(NetpayProtectionCase.id == case_id, NetpayProtectionCase.organization_id == org)
        .with_for_update()
    )
    if case is None:
        raise ProtectionCaseError("resource_not_found")
    if case.aggregate_version != expected_case_version:
        return _save_receipt(
            db,
            authority=authority,
            command_id="IC-NETPAY-CMD-049",
            key=idempotency_key,
            fingerprint=fingerprint,
            case_id=case.id,
            body={"result": "stale_version", "case_id": str(case.id), "version": case.aggregate_version},
        )
    prior_evidence = None
    prior_assessment = None
    prior_snapshot = None
    if supersedes_evidence_id is not None:
        if evidence_id == supersedes_evidence_id:
            raise ProtectionCaseError("invalid_supersession_chain")
        prior_evidence = db.scalar(
            select(NetpayProtectionOutcomeEvidence).where(
                NetpayProtectionOutcomeEvidence.id == supersedes_evidence_id,
                NetpayProtectionOutcomeEvidence.organization_id == org,
                NetpayProtectionOutcomeEvidence.case_id == case.id,
            )
        )
        if prior_evidence is None:
            raise ProtectionCaseError("resource_not_found")
        if _current_evidence(db, org, case.id).id != prior_evidence.id:
            raise ProtectionCaseError("supersession_conflict")
        prior_assessment = _current_assessment(db, org, case.id)
        prior_snapshot = _current_snapshot(db, org, case.id)
    money_result = None
    if profile_version == "synthetic_c4_financial_effect_v1":
        money_result = _money(financial_components or [], financial_category or "", financial_certainty)
    evidence = NetpayProtectionOutcomeEvidence(
        id=evidence_id or uuid4(),
        organization_id=org,
        case_id=case.id,
        evidence_kind=evidence_kind,
        profile_version=profile_version,
        source_authority="synthetic_fixture",
        source_reference=source_reference,
        evidence_fingerprint=fingerprint,
        identity_scope=identity_scope,
        occurred_at=occurred_at,
        observed_at=observed_at,
        valid_from=valid_from,
        valid_to=valid_to,
        period_key=period_key,
        amount=money_result[0] if money_result else None,
        currency=money_result[1] if money_result else None,
        supersedes_evidence_id=supersedes_evidence_id,
        actor_principal_id=authority.principal_id,
        correlation_id=correlation_id,
    )
    if profile_version == "synthetic_c4_activity_v1":
        if evidence_kind != "activity" or identity_scope not in {"store", "equipment_exact"}:
            raise ProtectionCaseError("invalid_activity_evidence")
        assessment_kind = "reactivation_verified" if identity_scope == "equipment_exact" else "supported_store_level"
        certainty = "confirmed" if identity_scope == "equipment_exact" else "supported"
    elif profile_version == "synthetic_c4_return_inventory_v1":
        if identity_scope != "equipment_exact" or evidence_kind not in {"return_received", "return_in_transit"}:
            raise ProtectionCaseError("invalid_return_evidence")
        assessment_kind = "equipment_return_verified" if evidence_kind == "return_received" else "return_in_transit"
        certainty = "confirmed" if evidence_kind == "return_received" else "supported"
    else:
        if evidence_kind != "financial" or not period_key or not financial_category:
            raise ProtectionCaseError("invalid_financial_evidence")
        assessment_kind = (
            prior_assessment.assessment_kind
            if prior_assessment and prior_assessment.assessment_kind in OPERATIONAL_VERIFIED
            else "financial_effect"
        )
        certainty = min(
            (prior_assessment.certainty if prior_assessment else financial_certainty, financial_certainty),
            key=CERTAINTIES.__getitem__,
        )
    db.add(evidence)
    db.flush()
    assessment = NetpayProtectionOutcomeAssessment(
        organization_id=org,
        case_id=case.id,
        evidence_id=evidence.id,
        assessment_kind=assessment_kind,
        certainty=certainty,
        rule_version="synthetic_c4_rules_v1",
        supersedes_assessment_id=prior_assessment.id if prior_assessment else None,
    )
    db.add(assessment)
    db.flush()
    snapshot = None
    if profile_version == "synthetic_c4_financial_effect_v1":
        amount, currency, components = money_result
        snapshot = NetpayProtectionFinancialSnapshot(
            organization_id=org,
            case_id=case.id,
            evidence_id=evidence.id,
            assessment_id=assessment.id,
            category=financial_category,
            certainty=financial_certainty,
            currency=currency,
            amount=amount,
            period_key=period_key,
            components=components,
            supersedes_snapshot_id=prior_snapshot.id if prior_snapshot else None,
        )
        db.add(snapshot)
        db.flush()
    if (
        profile_version != "synthetic_c4_financial_effect_v1"
        and assessment_kind in OPERATIONAL_VERIFIED
        and case.terminal_at is None
    ):
        prior_status = case.status
        case.status = assessment_kind
        case.aggregate_version += 1
        case.updated_at = datetime.now(timezone.utc)
        db.add(
            NetpayProtectionCaseHistory(
                organization_id=org,
                case_id=case.id,
                aggregate_version=case.aggregate_version,
                prior_status=prior_status,
                resulting_status=case.status,
                action_code="outcome_evidence_recorded",
                reason_code=assessment_kind,
                actor_principal_id=authority.principal_id,
                correlation_id=correlation_id,
                evidence_reference=str(evidence.id),
            )
        )
    body = {
        "result": "recorded",
        "case_id": str(case.id),
        "case_version": case.aggregate_version,
        "evidence_id": str(evidence.id),
        "assessment_id": str(assessment.id),
        "assessment_kind": assessment_kind,
        "certainty": certainty,
        "snapshot_id": str(snapshot.id) if snapshot else None,
        "amount": str(snapshot.amount) if snapshot and snapshot.amount is not None else None,
        "currency": snapshot.currency if snapshot else None,
    }
    return _save_receipt(
        db,
        authority=authority,
        command_id="IC-NETPAY-CMD-049",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case.id,
        body=body,
    )


def close_protection_case(
    db: Session,
    *,
    authority: IdentityAuthorityEnvelope,
    case_id: UUID,
    expected_case_version: int,
    closure_kind: str,
    gap_reason: str | None,
    idempotency_key: str,
    correlation_id: str,
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.inbox.manage", "netpay.portfolio.reconciliation.read")
    payload = {"case": case_id, "version": expected_case_version, "closure": closure_kind, "gap": gap_reason}
    fingerprint = _digest(payload)
    replay = _attempt(
        db,
        authority=authority,
        command_id="IC-NETPAY-CMD-050",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case_id,
    )
    if replay is not None:
        return replay
    case = db.scalar(
        select(NetpayProtectionCase)
        .where(NetpayProtectionCase.id == case_id, NetpayProtectionCase.organization_id == org)
        .with_for_update()
    )
    if case is None:
        raise ProtectionCaseError("resource_not_found")
    if case.aggregate_version != expected_case_version:
        return _save_receipt(
            db,
            authority=authority,
            command_id="IC-NETPAY-CMD-050",
            key=idempotency_key,
            fingerprint=fingerprint,
            case_id=case.id,
            body={"result": "stale_version", "case_id": str(case.id), "version": case.aggregate_version},
        )
    evidence = _current_evidence(db, org, case.id)
    assessment = _current_assessment(db, org, case.id)
    snapshot = _current_snapshot(db, org, case.id)
    operational = assessment is not None and assessment.assessment_kind in OPERATIONAL_VERIFIED
    if closure_kind == "verified_with_financial_effect":
        if not operational:
            raise ProtectionCaseError("operational_outcome_required")
        if snapshot is None or snapshot.amount is None:
            raise ProtectionCaseError("financial_snapshot_required")
        if gap_reason is not None:
            raise ProtectionCaseError("unexpected_gap_reason")
    elif closure_kind == "verified_financial_pending":
        if not operational:
            raise ProtectionCaseError("operational_outcome_required")
        if gap_reason not in {"financial_window_pending", "financial_source_incomplete"}:
            raise ProtectionCaseError("pending_reason_required")
        if snapshot is not None and snapshot.amount is not None:
            raise ProtectionCaseError("unexpected_financial_amount")
    elif closure_kind == "closed_with_evidence_gap":
        if gap_reason not in CLOSURE_GAPS:
            raise ProtectionCaseError("evidence_gap_required")
        if operational:
            raise ProtectionCaseError("verified_outcome_conflict")
        if snapshot is not None and snapshot.amount is not None:
            raise ProtectionCaseError("unexpected_financial_amount")
    elif closure_kind == "not_recoverable":
        if case.status != "unrecoverable":
            raise ProtectionCaseError("not_recoverable_reason_required")
        if operational:
            raise ProtectionCaseError("successful_outcome_conflict")
        if snapshot is not None and snapshot.amount is not None and snapshot.amount > 0:
            raise ProtectionCaseError("recovery_amount_forbidden")
        if gap_reason != "not_recoverable":
            raise ProtectionCaseError("not_recoverable_reason_required")
    else:
        raise ProtectionCaseError("unsupported_closure_kind")
    prior = case.status
    case.status = "closed"
    case.aggregate_version += 1
    case.terminal_at = datetime.now(timezone.utc)
    case.updated_at = case.terminal_at
    case.closure_kind = closure_kind
    case.closure_evidence_id = evidence.id if evidence else None
    case.closure_snapshot_id = snapshot.id if snapshot else None
    db.add(
        NetpayProtectionCaseHistory(
            organization_id=org,
            case_id=case.id,
            aggregate_version=case.aggregate_version,
            prior_status=prior,
            resulting_status="closed",
            action_code="case_closed",
            reason_code=closure_kind,
            actor_principal_id=authority.principal_id,
            correlation_id=correlation_id,
            evidence_reference=str(evidence.id) if evidence else None,
        )
    )
    body = {
        "result": "closed",
        "case_id": str(case.id),
        "version": case.aggregate_version,
        "closure_kind": closure_kind,
        "evidence_id": str(evidence.id) if evidence else None,
        "snapshot_id": str(snapshot.id) if snapshot else None,
        "gap_reason": gap_reason,
    }
    return _save_receipt(
        db,
        authority=authority,
        command_id="IC-NETPAY-CMD-050",
        key=idempotency_key,
        fingerprint=fingerprint,
        case_id=case.id,
        body=body,
    )


def retrieve_outcome_assessment(
    db: Session, *, authority: IdentityAuthorityEnvelope, case_id: UUID, include_evidence: bool = False
) -> dict:
    org = authority.organization_id
    _require(authority, org, "netpay.portfolio.read")
    if include_evidence:
        _require(authority, org, "netpay.portfolio.reconciliation.read")
    case = db.scalar(
        select(NetpayProtectionCase).where(
            NetpayProtectionCase.id == case_id, NetpayProtectionCase.organization_id == org
        )
    )
    if case is None:
        raise ProtectionCaseError("resource_not_found")
    evidence = _current_evidence(db, org, case.id)
    assessment = _current_assessment(db, org, case.id)
    snapshot = _current_snapshot(db, org, case.id)
    stale = case.closure_evidence_id is not None and (evidence is None or case.closure_evidence_id != evidence.id)
    body = {
        "case_id": str(case.id),
        "case_version": case.aggregate_version,
        "status": case.status,
        "closure_kind": case.closure_kind,
        "assessment_state": "assessment_stale" if stale else "current",
        "assessment_kind": assessment.assessment_kind if assessment else None,
        "certainty": assessment.certainty if assessment else None,
        "financial": {
            "category": snapshot.category,
            "certainty": snapshot.certainty,
            "amount": str(snapshot.amount) if snapshot.amount is not None else None,
            "currency": snapshot.currency,
            "period_key": snapshot.period_key,
        }
        if snapshot
        else None,
    }
    if include_evidence and evidence:
        body["evidence"] = {
            "evidence_id": str(evidence.id),
            "profile_version": evidence.profile_version,
            "source_reference": evidence.source_reference,
            "occurred_at": evidence.occurred_at.isoformat(),
            "supersedes_evidence_id": str(evidence.supersedes_evidence_id)
            if evidence.supersedes_evidence_id
            else None,
        }
    return body

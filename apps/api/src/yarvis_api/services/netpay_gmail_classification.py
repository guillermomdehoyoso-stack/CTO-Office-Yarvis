"""Deterministic, explainable D2 extraction for bounded Gmail source text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.models.netpay_gmail_intake import NetpayGmailSourceItem, NetpayIntakeCandidate
from yarvis_api.models.netpay_master import NetpayBranch, NetpayCompany, NetpayStoreReference

RULE_VERSION = "d2-rules-v2"


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _values(pattern: str, text: str) -> list[str]:
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return list(dict.fromkeys(match.strip() for match in matches if match.strip()))


def readable_message_text(value: str) -> str:
    """Build a review view while leaving the immutable source excerpt untouched."""

    text = re.sub(r"\s+", " ", value).strip()
    if len(text) < 240:
        return text
    marker = text[: min(100, len(text))]
    repeated_at = text.find(marker, len(marker))
    if repeated_at >= len(text) // 3:
        return text[:repeated_at].strip()
    return text


def _new_branch_observations(text: str) -> tuple[str | None, list[str]]:
    """Extract repeated merchant/branch names without relying on a known brand."""

    words = text.split()
    heading_windows: list[list[str]] = []
    for index, word in enumerate(words):
        if _fold(word.rstrip(".:")) == "direccion" and word.endswith((".", ":")):
            heading_windows.append(words[max(0, index - 8) : index])
    if len(heading_windows) >= 2:
        shared: list[str] | None = None
        for size in range(1, 4):
            first = heading_windows[0]
            candidates = [first[start : start + size] for start in range(len(first) - size + 1)]
            repeated = next(
                (
                    candidate
                    for candidate in reversed(candidates)
                    if all(
                        any(
                            [_fold(value) for value in window[start : start + size]]
                            == [_fold(value) for value in candidate]
                            for start in range(len(window) - size + 1)
                        )
                        for window in heading_windows[1:]
                    )
                ),
                None,
            )
            if repeated:
                shared = repeated
        if shared:
            folded_shared = [_fold(value) for value in shared]
            branches: list[str] = []
            for window in heading_windows:
                starts = [
                    start
                    for start in range(len(window) - len(shared) + 1)
                    if [_fold(value) for value in window[start : start + len(shared)]] == folded_shared
                ]
                if starts:
                    branches.append(" ".join(window[starts[-1] :]).strip(" .;,:-"))
            if len(branches) == len(heading_windows):
                return " ".join(shared), list(dict.fromkeys(branches))

    match = re.search(
        r"(?:nueva(?:s)?\s+sucursal(?:es)?|alta\s+de\s+(?:\d+\s+)?sucursal(?:es)?)\s*:\s*(.+?)"
        r"(?=\s+(?:adjunto|anexo|documentaci[oó]n|me\s+apoyar[ií]a|favor\s+de|saludos)\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, []
    block = re.sub(r"\s+", " ", match.group(1)).strip(" .;,:-")
    words = block.split()
    best: tuple[list[str], list[int]] | None = None
    for size in range(1, min(4, len(words))):
        prefix = words[:size]
        folded_prefix = [_fold(value) for value in prefix]
        positions = [
            index
            for index in range(0, len(words) - size + 1)
            if [_fold(value) for value in words[index : index + size]] == folded_prefix
        ]
        if len(positions) >= 2:
            best = (prefix, positions)
    if best is None:
        branches = [item.strip() for item in re.split(r"\s*(?:,|;|\by\b)\s*", block) if item.strip()]
        return None, branches
    prefix, positions = best
    branches = []
    for index, start in enumerate(positions):
        end = positions[index + 1] if index + 1 < len(positions) else len(words)
        branch = " ".join(words[start:end]).strip(" .;,:-")
        if branch:
            branches.append(branch)
    return " ".join(prefix), branches


@dataclass(frozen=True, slots=True)
class CandidateExtraction:
    request_type: str
    product: str
    ticket_references: list[str]
    commerce_hints: list[dict[str, str]]
    terminal_serials: list[str]
    shipment_facts: dict[str, str]
    facts: list[dict[str, str]]
    inferences: list[dict[str, str]]
    contradictions: list[dict[str, str]]
    missing_data: list[str]
    correlation_key: str | None
    priority: str
    next_action: str
    confidence: float
    reasons: list[str]


def extract_candidate(source: NetpayGmailSourceItem) -> CandidateExtraction:
    readable_body = readable_message_text(source.plain_excerpt)
    text = " ".join(part for part in (source.subject or "", readable_body) if part)
    folded = _fold(text)
    tickets = _values(r"(?:caso|ticket|folio)\s*[:#-]?\s*(\d{5,})", text)
    tracking = _values(r"(?:gu[ií]a|tracking)\s*[:#-]?\s*([A-Z0-9-]{8,})", text)
    serials = [
        value
        for value in _values(r"(?:n[uú]mero\s+de\s+serie|serie|serial)\s*[:#-]?\s*([A-Z0-9-]{4,})", text)
        if _fold(value) not in {"vacio", "n/a", "ninguno"}
    ]
    stores = _values(r"(?:store\s*id|comercio\s*id)\s*[:#-]?\s*([A-Z0-9-]{2,100})", text)
    commerce_names = _values(
        r"(?:comercio|sucursal)\s*:\s*(.+?)(?=\s+(?:adjunto|anexo|documentaci[oó]n|me\s+apoyar[ií]a|saludos)\b|[;,.\n]|$)",
        text,
    )
    observed_merchant, observed_branches = _new_branch_observations(text)
    if observed_branches:
        commerce_names = [
            value for value in commerce_names if not all(branch in value for branch in observed_branches)
        ]
    subject_commerce = re.search(
        r"(?:e-?commerce)\s+(.+?)\s+ID\s+(\d{2,})\s*$",
        source.subject or "",
        flags=re.IGNORECASE,
    )
    carriers = ("FedEx", "DHL", "UPS", "Estafeta", "Paquetexpress")
    carrier = next((name for name in carriers if _fold(name) in folded), None)
    reported_states = _values(r"(?:estado(?:\s+reportado)?|estatus)\s*:\s*([^;,.\n]{2,80})", text)

    request_type = "unclassified"
    product = "not_applicable"
    reasons: list[str] = []
    ecommerce_mentioned = "e-commerce" in folded or "ecommerce" in folded
    rejection_review = ecommerce_mentioned and any(
        value in folded for value in ("revision de rechazos", "decision manager")
    )
    if rejection_review:
        request_type, product = "support_or_incident", "ecommerce"
        reasons.append("ecommerce_rejection_review")
    elif ecommerce_mentioned and any(value in folded for value in ("alta", "activar", "activacion")):
        request_type, product = "ecommerce_activation", "ecommerce"
        reasons.append("ecommerce_activation_keyword")
    elif ecommerce_mentioned:
        product = "ecommerce"
    if re.search(r"\bnueva(?:s)?\s+sucursal(?:es)?\b|\balta\s+de\s+(?:\d+\s+)?sucursal(?:es)?\b", folded):
        request_type = "new_branch"
        reasons.append("new_branch_keyword")
    if any(word in folded for word in ("terminal", "tpv", "pinpad")):
        product = "tpv" if product == "not_applicable" else "mixed"
        if any(word in folded for word in ("reemplazo", "reposicion", "sustitucion")):
            request_type = "terminal_replacement"
            reasons.append("terminal_replacement_keyword")
    if tracking or carrier or "detalle de envio" in folded or "envio" in folded:
        request_type = (
            "consumable_shipment" if any(word in folded for word in ("rollo", "consumible")) else "shipment_follow_up"
        )
        reasons.append("shipment_evidence")
    if any(word in folded for word in ("urgente", "critico", "inmediato")):
        priority = "urgent"
    elif any(word in folded for word in ("bloqueado", "incidente critico")):
        priority = "high"
    else:
        priority = "normal"

    shipment: dict[str, str] = {}
    if carrier:
        shipment["carrier"] = carrier
    if tracking:
        shipment["tracking_number"] = tracking[0]
    if reported_states:
        shipment["reported_state"] = reported_states[0]

    facts: list[dict[str, str]] = []
    for value in tickets:
        facts.append({"field": "ticket", "value": value, "source": "message_text"})
    for value in serials:
        facts.append({"field": "terminal_serial", "value": value, "source": "message_text"})
    for field, value in shipment.items():
        facts.append({"field": field, "value": value, "source": "message_text"})
    for value in stores:
        facts.append({"field": "store_id", "value": value, "source": "message_text"})

    if observed_merchant:
        facts.append(
            {
                "field": "commerce_name",
                "value": observed_merchant,
                "source": "message_body",
                "verification": "unverified",
            }
        )
        commerce_names.append(observed_merchant)
    for value in observed_branches:
        facts.append(
            {
                "field": "branch_name",
                "value": value,
                "source": "message_body",
                "verification": "unverified",
            }
        )
    if observed_branches:
        facts.append(
            {
                "field": "requested_action",
                "value": "new_branch_onboarding",
                "source": "message_body",
                "attribution": "reported_by_message",
            }
        )

    if subject_commerce:
        observed_name, observed_id = (value.strip() for value in subject_commerce.groups())
        facts.extend(
            [
                {
                    "field": "commerce_name",
                    "value": observed_name,
                    "source": "message_subject",
                    "verification": "unverified",
                },
                {
                    "field": "external_identifier",
                    "value": observed_id,
                    "source": "message_subject",
                    "identifier_type": "unspecified",
                    "verification": "unverified",
                },
            ]
        )
        commerce_names.append(observed_name)
    if rejection_review:
        facts.append(
            {
                "field": "requested_action",
                "value": "review_ecommerce_rejections_and_response_codes",
                "source": "message_text",
                "attribution": "reported_by_message",
            }
        )
        reported_claims = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+|\s+[•]\s+", readable_body)
            if re.search(r"\b\d+(?:%|\s+(?:Order IDs|de ellos|veces))\b", sentence, flags=re.IGNORECASE)
        ]
        facts.extend(
            {
                "field": "reported_claim",
                "value": claim[:500],
                "source": "message_body",
                "attribution": "reported_by_message",
                "verification": "unverified",
            }
            for claim in reported_claims[:8]
        )

    hints = [{"kind": "store_id", "value": value} for value in stores]
    hints.extend({"kind": "unverified_name", "value": value} for value in commerce_names)
    if subject_commerce:
        hints.append({"kind": "unverified_identifier", "value": subject_commerce.group(2)})
    missing: list[str] = []
    if not tickets:
        missing.append("ticket_or_case")
    if not stores:
        missing.append("verified_commerce_identifier")
    if "shipment_evidence" in reasons and not tracking:
        missing.append("tracking_number")
    if "terminal" in folded and not serials:
        missing.append("terminal_serial")

    correlation_key = next(
        (
            value
            for value in (
                f"ticket:{tickets[0]}" if tickets else None,
                f"tracking:{tracking[0]}" if tracking else None,
                f"serial:{serials[0]}" if serials else None,
                f"store:{stores[0].upper()}" if stores else None,
            )
            if value is not None
        ),
        None,
    )
    fallback_next_action = (
        "Vincular el comercio con un identificador verificable"
        if "verified_commerce_identifier" in missing
        else "Revisar evidencia y confirmar la vinculación propuesta"
    )
    next_action = (
        "Identificar el comercio con evidencia verificable y canalizar la revisión de rechazos "
        "de e-commerce/Decision Manager y códigos de respuesta reportados"
        if rejection_review
        else fallback_next_action
    )
    inferences = [
        {
            "field": "next_action",
            "value": next_action,
            "basis": "deterministic_rule",
        }
    ]
    if shipment.get("reported_state"):
        inferences.append(
            {
                "field": "shipment_interpretation",
                "value": "reported_state_only; delivery, activation and return remain unconfirmed",
                "basis": "non_inference_guardrail",
            }
        )
    confidence = min(0.98, 0.35 + 0.12 * len(reasons) + 0.08 * min(len(facts), 4))
    return CandidateExtraction(
        request_type=request_type,
        product=product,
        ticket_references=tickets,
        commerce_hints=hints,
        terminal_serials=serials,
        shipment_facts=shipment,
        facts=facts,
        inferences=inferences,
        contradictions=[],
        missing_data=missing,
        correlation_key=correlation_key,
        priority=priority,
        next_action=next_action,
        confidence=confidence,
        reasons=reasons or ["no_closed_catalog_rule_matched"],
    )


def reprocess_unreviewed_candidate_from_source(
    candidate: NetpayIntakeCandidate,
    source: NetpayGmailSourceItem,
) -> None:
    """Refresh only a disposable D2 projection from its immutable local source."""

    if candidate.source_item_id != source.id or candidate.source_fingerprint != source.source_fingerprint:
        raise ValueError("candidate_source_mismatch")
    if (
        candidate.immutable
        or candidate.reviewed_at is not None
        or candidate.reviewed_by_principal_id is not None
        or candidate.owner_type is not None
        or candidate.owner_id is not None
        or candidate.state in {"accepted", "rejected", "duplicate", "linked"}
    ):
        raise ValueError("candidate_human_decision_present")

    result = extract_candidate(source)
    candidate.request_type = result.request_type
    candidate.product = result.product
    candidate.description = readable_message_text(source.plain_excerpt)
    candidate.ticket_references = result.ticket_references
    candidate.commerce_hints = result.commerce_hints
    candidate.terminal_serials = result.terminal_serials
    candidate.shipment_facts = result.shipment_facts
    candidate.facts = result.facts
    candidate.inferences = result.inferences
    candidate.missing_data = result.missing_data
    candidate.correlation_key = result.correlation_key
    candidate.priority = result.priority
    candidate.suggested_next_action = result.next_action
    candidate.follow_up_at = source.provider_received_at + timedelta(
        days=2 if result.priority in {"urgent", "high"} else 5
    )
    candidate.extraction_method = "deterministic"
    candidate.extraction_version = RULE_VERSION
    candidate.confidence = result.confidence
    candidate.extraction_reasons = [*result.reasons, "local_source_reprocessed_after_rule_fix"]


def create_candidate_from_source(db: Session, source: NetpayGmailSourceItem) -> NetpayIntakeCandidate:
    existing = db.scalar(
        select(NetpayIntakeCandidate).where(
            NetpayIntakeCandidate.organization_id == source.organization_id,
            NetpayIntakeCandidate.source_item_id == source.id,
        )
    )
    if existing is not None:
        return existing
    result = extract_candidate(source)
    client_id: UUID | None = None
    company_id: UUID | None = None
    branch_id: UUID | None = None
    store_reference_id: UUID | None = None
    store_hints = [item["value"] for item in result.commerce_hints if item["kind"] == "store_id"]
    if store_hints:
        store = db.scalar(
            select(NetpayStoreReference).where(
                NetpayStoreReference.organization_id == source.organization_id,
                NetpayStoreReference.normalized_store_id == store_hints[0].strip().lower(),
                NetpayStoreReference.active.is_(True),
            )
        )
        if store is not None:
            branch = db.scalar(
                select(NetpayBranch).where(
                    NetpayBranch.organization_id == source.organization_id,
                    NetpayBranch.id == store.branch_id,
                )
            )
            company = (
                db.scalar(
                    select(NetpayCompany).where(
                        NetpayCompany.organization_id == source.organization_id,
                        NetpayCompany.id == branch.company_id,
                    )
                )
                if branch is not None
                else None
            )
            if branch is not None and company is not None:
                client_id = company.client_id
                company_id = company.id
                branch_id = branch.id
                store_reference_id = store.id

    contradictions: list[dict[str, str]] = []
    if result.correlation_key:
        related = db.scalars(
            select(NetpayIntakeCandidate).where(
                NetpayIntakeCandidate.organization_id == source.organization_id,
                NetpayIntakeCandidate.correlation_key == result.correlation_key,
            )
        ).all()
        for item in related:
            old_state = item.shipment_facts.get("reported_state")
            new_state = result.shipment_facts.get("reported_state")
            if old_state and new_state and _fold(old_state) != _fold(new_state):
                contradictions.append(
                    {
                        "field": "shipment.reported_state",
                        "earlier": old_state,
                        "current": new_state,
                        "related_candidate_id": str(item.id),
                    }
                )

    linked = store_reference_id is not None
    state = "needs_review" if linked else "pending_link"
    candidate = NetpayIntakeCandidate(
        organization_id=source.organization_id,
        source_item_id=source.id,
        connection_id=source.connection_id,
        source_fingerprint=source.source_fingerprint,
        received_at=source.provider_received_at,
        state=state,
        request_type=result.request_type,
        product=result.product,
        description=readable_message_text(source.plain_excerpt),
        ticket_references=result.ticket_references,
        commerce_hints=result.commerce_hints,
        terminal_serials=result.terminal_serials,
        shipment_facts=result.shipment_facts,
        facts=result.facts,
        inferences=result.inferences,
        contradictions=contradictions,
        missing_data=[value for value in result.missing_data if value != "verified_commerce_identifier" or not linked],
        correlation_key=result.correlation_key,
        client_id=client_id,
        company_id=company_id,
        branch_id=branch_id,
        store_reference_id=store_reference_id,
        priority=result.priority,
        suggested_next_action=result.next_action,
        follow_up_at=source.provider_received_at + timedelta(days=2 if result.priority in {"urgent", "high"} else 5),
        extraction_method="deterministic",
        extraction_version=RULE_VERSION,
        confidence=result.confidence,
        extraction_reasons=result.reasons,
    )
    db.add(candidate)
    db.flush()
    return candidate

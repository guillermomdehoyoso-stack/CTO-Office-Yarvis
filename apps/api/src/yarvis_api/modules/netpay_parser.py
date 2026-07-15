from __future__ import annotations

import re
from typing import Any


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
FOLIO_RE = re.compile(r"\bfolio(?:\s*netpay)?\s*[:#-]?\s*([A-Z0-9-]{5,40})", re.IGNORECASE)
TRACKING_RE = re.compile(r"\b(?:gu(?:i|í)a|tracking|rastreo)\s*(?:no\.?|n[uú]mero|#|:)?\s*([A-Z0-9-]{8,40})", re.IGNORECASE)
STORE_ID_RE = re.compile(r"\bstore\s*id\s*[:#-]?\s*([A-Z0-9-]{3,30})", re.IGNORECASE)
SERIAL_RE = re.compile(r"\b(?:serie|serial|tpv)\s*[:#-]?\s*([A-Z0-9-]{4,40})", re.IGNORECASE)
CUSTOMER_RE = re.compile(r"\bcliente\s*[:#-]?\s*(.+)", re.IGNORECASE)
MERCHANT_RE = re.compile(r"\bcomercio\s*[:#-]?\s*(.+)", re.IGNORECASE)
BRANCH_RE = re.compile(r"\b(?:sucursal|branch)\s*[:#-]?\s*(.+)", re.IGNORECASE)
LOGISTICS_RECIPIENT_RE = re.compile(r"\b(?:destinatario|recipient)\s*[:#-]?\s*(.+)", re.IGNORECASE)
ADDRESS_RE = re.compile(r"\b(?:domicilio|address)\s*[:#-]?\s*(.+)", re.IGNORECASE)
CITY_RE = re.compile(r"\b(?:ciudad|city)\s*[:#-]?\s*(.+)", re.IGNORECASE)
STATE_RE = re.compile(r"\b(?:estado|state)\s*[:#-]?\s*(.+)", re.IGNORECASE)
POSTAL_RE = re.compile(r"\b(?:cp|c[óo]digo\s*postal|postal\s*code)\s*[:#-]?\s*([0-9]{4,10})", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(?:tel[ée]fono|phone)\s*[:#-]?\s*([0-9+()\-\s]{7,30})", re.IGNORECASE)


def _field(value: str | None, confidence: float, source_reference: str | None, method: str = "regex", source_type: str = "email") -> dict[str, Any]:
    return {
        "value": value,
        "confidence": confidence if value else 0.0,
        "provenance": "parser",
        "source_reference": source_reference,
        "confirmation_status": "candidate",
        "extraction_method": method,
        "source_type": source_type,
        "confirmed_by_user": None,
        "confirmed_at": None,
    }


def _normalize_addresses(values: list[str] | None) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        for item in EMAIL_RE.findall(value or ""):
            lowered = item.lower().strip()
            if lowered and lowered not in seen:
                seen.add(lowered)
                result.append(lowered)
    return result


def normalize_body(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def detect_folio(subject: str, body: str) -> str | None:
    combined = f"{subject}\n{body}"
    match = FOLIO_RE.search(combined)
    return match.group(1).upper() if match else None


def detect_tracking_numbers(subject: str, body: str) -> list[str]:
    combined = f"{subject}\n{body}"
    values = [item.upper() for item in TRACKING_RE.findall(combined)]
    dedup: list[str] = []
    for value in values:
        if value not in dedup:
            dedup.append(value)
    return dedup


def detect_movement(subject: str, body: str) -> str:
    text = f"{subject}\n{body}".lower()
    outbound_hits = sum(keyword in text for keyword in ("envio", "envío", "entrega", "salida", "embarque"))
    collection_hits = sum(keyword in text for keyword in ("recoleccion", "recolección", "devolucion", "devolución", "retiro"))
    if outbound_hits > collection_hits and outbound_hits > 0:
        return "outbound"
    if collection_hits > outbound_hits and collection_hits > 0:
        return "collection"
    return "unknown"


def forwarded_alias(body: str) -> str | None:
    for line in body.split("\n"):
        lower = line.lower().strip()
        if lower.startswith(("to:", "para:")):
            matches = EMAIL_RE.findall(line)
            if matches:
                return matches[0].lower()
    return None


def resolve_operational_recipient(
    *,
    delivered_to: str | None,
    x_original_to: str | None,
    original_recipient: str | None,
    to_addresses: list[str],
    cc_addresses: list[str],
    forwarded: str | None,
) -> dict[str, Any]:
    candidates = [
        (delivered_to, "delivered_to", 1.0),
        (x_original_to, "x_original_to", 0.95),
        (original_recipient, "original_recipient", 0.9),
        (to_addresses[0] if to_addresses else None, "to", 0.8),
        (cc_addresses[0] if cc_addresses else None, "cc", 0.65),
        (forwarded, "forwarded_alias", 0.55),
    ]
    for candidate, source, confidence in candidates:
        addresses = EMAIL_RE.findall(candidate or "")
        if addresses:
            return {
                "email_recipient": _field(addresses[0].lower(), confidence, source, method="header-resolution"),
                "resolution_source": source,
                "resolution_confidence": confidence,
            }
    return {
        "email_recipient": _field(None, 0.0, None, method="header-resolution"),
        "resolution_source": "none",
        "resolution_confidence": 0.0,
    }


def _extract_line(pattern: re.Pattern[str], text: str, source_reference: str) -> dict[str, Any]:
    match = pattern.search(text)
    return _field(match.group(1).strip().upper() if match else None, 0.92 if match else 0.0, source_reference)


def _extract_tracking_numbers(subject: str, body: str) -> list[dict[str, Any]]:
    combined = f"{subject}\n{body}"
    values = [item.upper().strip() for item in TRACKING_RE.findall(combined)]
    dedup: list[str] = []
    for value in values:
        if value not in dedup:
            dedup.append(value)
    return [_field(item, 0.94, "body_or_subject") for item in dedup]


def parse_email(payload: dict) -> dict:
    subject = (payload.get("subject") or "").strip()
    body = normalize_body(payload.get("body") or "")

    to_addresses = _normalize_addresses(payload.get("to_addresses"))
    cc_addresses = _normalize_addresses(payload.get("cc_addresses"))
    reply_to_addresses = _normalize_addresses(payload.get("reply_to_addresses"))
    delivered_to = (payload.get("delivered_to") or "").strip() or None
    x_original_to = (payload.get("x_original_to") or "").strip() or None
    original_recipient = (payload.get("original_recipient") or "").strip() or None

    forwarded = forwarded_alias(body)
    email_recipient_resolution = resolve_operational_recipient(
        delivered_to=delivered_to,
        x_original_to=x_original_to,
        original_recipient=original_recipient,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        forwarded=forwarded,
    )

    all_recipients: list[str] = []
    for value in [delivered_to, x_original_to, original_recipient, forwarded]:
        all_recipients.extend([item.lower() for item in EMAIL_RE.findall(value or "")])
    for source in (to_addresses, cc_addresses, reply_to_addresses):
        for item in source:
            if item not in all_recipients:
                all_recipients.append(item)

    folio = detect_folio(subject, body)
    tracking_fields = _extract_tracking_numbers(subject, body)
    movement_type = detect_movement(subject, body)

    combined = f"{subject}\n{body}"
    store = _extract_line(STORE_ID_RE, combined, "body_or_subject")
    serial = _extract_line(SERIAL_RE, combined, "body_or_subject")
    customer = _extract_line(CUSTOMER_RE, body, "body")
    merchant = _extract_line(MERCHANT_RE, body, "body")
    branch = _extract_line(BRANCH_RE, body, "body")
    logistics_recipient = _extract_line(LOGISTICS_RECIPIENT_RE, body, "body")
    address = _extract_line(ADDRESS_RE, body, "body")
    city = _extract_line(CITY_RE, body, "body")
    state = _extract_line(STATE_RE, body, "body")
    postal_code = _extract_line(POSTAL_RE, body, "body")
    phone = _extract_line(PHONE_RE, body, "body")

    extracted_fields = {
        "folio": _field(folio, 0.95 if folio else 0.0, "body_or_subject"),
        "tracking": tracking_fields[0] if tracking_fields else _field(None, 0.0, None),
        "serial": serial,
        "store_id": store,
        "customer": customer,
        "merchant": merchant,
        "branch": branch,
        "logistics_recipient": logistics_recipient,
        "address": address,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "phone": phone,
    }

    operational_resolution = {
        "email_recipient": email_recipient_resolution["email_recipient"],
        "operational_recipient": _field(
            email_recipient_resolution["email_recipient"]["value"],
            email_recipient_resolution["resolution_confidence"],
            email_recipient_resolution["resolution_source"],
            method="operational-resolution",
        ),
        "physical_delivery_destination": _field(address["value"], address["confidence"], "body", method="logistics-resolution"),
    }

    return {
        "subject": subject,
        "body_normalized": body,
        "folio": folio,
        "tracking_numbers": [item["value"] for item in tracking_fields if item["value"]],
        "movement_type": movement_type,
        "to_addresses": to_addresses,
        "cc_addresses": cc_addresses,
        "reply_to_addresses": reply_to_addresses,
        "delivered_to": delivered_to,
        "x_original_to": x_original_to,
        "original_recipient": original_recipient,
        "recipient_addresses": all_recipients,
        "operational_recipient": operational_resolution["operational_recipient"]["value"],
        "recipient_resolution_source": email_recipient_resolution["resolution_source"],
        "recipient_resolution_confidence": email_recipient_resolution["resolution_confidence"],
        "physical_destination_resolution_source": operational_resolution["physical_delivery_destination"]["source_reference"],
        "physical_destination_resolution_confidence": operational_resolution["physical_delivery_destination"]["confidence"],
        "store_id": store["value"],
        "device_serial": serial["value"],
        "extracted_fields": extracted_fields,
        "operational_resolution": operational_resolution,
        "tracking_logistics": [
            {
                "tracking_number": tracking["value"],
                "direction": movement_type,
                "folio": folio,
                "store_id": store["value"],
                "device_serial": serial["value"],
                "extracted_fields": {
                    "tracking": tracking,
                    "customer": customer,
                    "merchant": merchant,
                    "branch": branch,
                    "logistics_recipient": logistics_recipient,
                    "address": address,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "phone": phone,
                },
            }
            for tracking in tracking_fields
            if tracking["value"]
        ],
    }

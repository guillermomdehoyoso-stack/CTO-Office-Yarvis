"""Application service for the read-only Netpay Gmail Intake D1 slice."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from yarvis_api.models.domain_event import record_event
from yarvis_api.models.netpay_gmail_intake import (
    NetpayGmailConnection,
    NetpayGmailSourceItem,
    NetpayGmailSyncRun,
)
from yarvis_api.services.netpay_gmail_classification import create_candidate_from_source
from yarvis_api.services.netpay_gmail_provider import GmailProviderError, GmailSourceMessage, GmailSourceProvider

MAX_EXCERPT_LENGTH = 4096
MAX_BACKFILL_DAYS = 30


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() in {"script", "style", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "template"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def sanitize_plain_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    text = html.unescape(" ".join(parser.parts))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_EXCERPT_LENGTH]


def _safe_address(value: str | None) -> str | None:
    if value is None:
        return None
    return sanitize_plain_text(value)[:255] or None


def _safe_attachments(items: tuple[dict[str, str | int], ...]) -> list[dict[str, str | int]]:
    safe: list[dict[str, str | int]] = []
    for item in items:
        name = sanitize_plain_text(str(item.get("name", "attachment")))[:255]
        mime = sanitize_plain_text(str(item.get("mime_type", "application/octet-stream")))[:128]
        size = item.get("size", 0)
        safe_size = int(size) if isinstance(size, int) and size >= 0 else 0
        safe.append({"name": name, "mime_type": mime, "size": safe_size})
    return safe


def source_fingerprint(message: GmailSourceMessage) -> str:
    body_digest = hashlib.sha256(message.body.encode("utf-8")).hexdigest()
    canonical = {
        "message_id": message.message_id,
        "thread_id": message.thread_id,
        "received_at": message.normalized_received_at().isoformat(),
        "sender": message.sender,
        "recipient": message.recipient,
        "subject": message.subject,
        "body_digest": body_digest,
        "labels": sorted(message.label_ids),
        "attachments": _safe_attachments(message.attachments),
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SyncResult:
    run: NetpayGmailSyncRun
    replayed: bool = False


def _cursor_for(message: GmailSourceMessage) -> str:
    return message.provider_cursor or f"{message.normalized_received_at().isoformat()}::{message.message_id}"


def run_manual_sync(
    db: Session,
    *,
    connection: NetpayGmailConnection,
    provider: GmailSourceProvider,
    actor_principal_id: UUID,
    correlation_id: UUID | None = None,
    backfill_days: int = MAX_BACKFILL_DAYS,
    now: datetime | None = None,
) -> SyncResult:
    if not 1 <= backfill_days <= MAX_BACKFILL_DAYS:
        raise ValueError("backfill_days must be between 1 and 30")
    if connection.state in {"revoked", "disconnected"}:
        raise ValueError("connection is not usable")
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    window_start = clock - timedelta(days=backfill_days)
    correlation = correlation_id or uuid4()
    cursor_before = connection.cursor
    has_persisted_sources = bool(
        db.scalar(
            select(func.count())
            .select_from(NetpayGmailSourceItem)
            .where(
                NetpayGmailSourceItem.organization_id == connection.organization_id,
                NetpayGmailSourceItem.connection_id == connection.id,
            )
        )
    )
    run = NetpayGmailSyncRun(
        organization_id=connection.organization_id,
        connection_id=connection.id,
        status="running",
        window_start=window_start,
        window_end=clock,
        cursor_before=cursor_before,
        correlation_id=correlation,
        actor_principal_id=actor_principal_id,
    )
    db.add(run)
    db.flush()
    connection.state = "running"
    try:
        messages = provider.list_messages(
            provider_account_id=connection.provider_account_id,
            label_id=connection.label_id,
            query=connection.query,
            credential_secret_ref=connection.credential_secret_ref,
            cursor=connection.cursor if connection.provider_kind == "google" and has_persisted_sources else None,
            window_start=window_start,
            window_end=clock,
        )
    except GmailProviderError as error:
        run.status = "failed"
        run.failure_code = error.code
        run.completed_at = clock
        connection.state = "failed"
        connection.last_error_code = error.code
        connection.last_sync_at = clock
        return SyncResult(run)

    accepted_messages = [message for message in messages if window_start <= message.normalized_received_at() <= clock]
    accepted_messages.sort(key=lambda item: (item.normalized_received_at(), item.message_id))
    latest_cursor = cursor_before
    conflict = False
    for message in accepted_messages:
        fingerprint = source_fingerprint(message)
        existing = db.scalar(
            select(NetpayGmailSourceItem).where(
                NetpayGmailSourceItem.organization_id == connection.organization_id,
                NetpayGmailSourceItem.connection_id == connection.id,
                NetpayGmailSourceItem.provider_account_id == connection.provider_account_id,
                NetpayGmailSourceItem.gmail_message_id == message.message_id,
            )
        )
        if existing is not None:
            if existing.source_fingerprint == fingerprint:
                run.deduplicated_count += 1
                create_candidate_from_source(db, existing)
                record_event(
                    db,
                    event_type="netpay.gmail.source_item_deduplicated",
                    aggregate_type="netpay_gmail_source_item",
                    aggregate_id=existing.id,
                    organization_id=connection.organization_id,
                    correlation_id=correlation,
                    causation_id=run.id,
                    payload={"source_item_id": str(existing.id), "reason": "replayed_message"},
                )
            else:
                conflict = True
                run.conflict_count += 1
                existing.conflict_detected_at = clock
                existing.conflict_fingerprint = fingerprint
                record_event(
                    db,
                    event_type="netpay.gmail.source_item_deduplicated",
                    aggregate_type="netpay_gmail_source_item",
                    aggregate_id=existing.id,
                    organization_id=connection.organization_id,
                    correlation_id=correlation,
                    causation_id=run.id,
                    payload={"source_item_id": str(existing.id), "reason": "fingerprint_conflict"},
                )
            latest_cursor = max(latest_cursor or "", _cursor_for(message))
            continue

        source = NetpayGmailSourceItem(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            provider_account_id=connection.provider_account_id,
            gmail_message_id=message.message_id,
            gmail_thread_id=message.thread_id,
            provider_received_at=message.normalized_received_at(),
            synchronized_at=clock,
            sender=_safe_address(message.sender),
            recipient=_safe_address(message.recipient),
            subject=sanitize_plain_text(message.subject or "")[:500] or None,
            plain_excerpt=sanitize_plain_text(message.body),
            source_fingerprint=fingerprint,
            attachment_metadata=_safe_attachments(message.attachments),
            provenance={
                "provider": provider.provider_kind,
                "label_id": connection.label_id,
                "query": connection.query,
                "thread_id_present": bool(message.thread_id),
            },
        )
        db.add(source)
        db.flush()
        candidate = create_candidate_from_source(db, source)
        run.captured_count += 1
        latest_cursor = max(latest_cursor or "", _cursor_for(message))
        record_event(
            db,
            event_type="netpay.gmail.source_item_captured",
            aggregate_type="netpay_gmail_source_item",
            aggregate_id=source.id,
            organization_id=connection.organization_id,
            correlation_id=correlation,
            causation_id=run.id,
            payload={"source_item_id": str(source.id), "thread_id_present": bool(message.thread_id)},
        )
        record_event(
            db,
            event_type="netpay.gmail.intake_candidate_created",
            aggregate_type="netpay_intake_candidate",
            aggregate_id=candidate.id,
            organization_id=connection.organization_id,
            correlation_id=correlation,
            causation_id=source.id,
            payload={"candidate_id": str(candidate.id), "source_item_id": str(source.id)},
        )

    run.status = "partially_failed" if conflict else "succeeded"
    run.failure_code = "source_fingerprint_conflict" if conflict else None
    run.cursor_after = None if conflict else latest_cursor
    run.completed_at = clock
    connection.last_sync_at = clock
    connection.last_error_code = run.failure_code
    connection.state = run.status
    if not conflict:
        connection.cursor = latest_cursor
    return SyncResult(run)

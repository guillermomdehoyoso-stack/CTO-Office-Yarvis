"""Inbound intake contracts used by the deterministic F-002 slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.metadata import RequestMetadata


class InboundSourceType(StrEnum):
    EMAIL = "email"
    MANUAL_TEXT = "manual_text"
    MANUAL_UPLOAD = "manual_upload"
    OTHER = "other"


def _require_nonblank(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must be nonblank")


def _require_timezone_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class InboundMessageFixture:
    external_source: InboundSourceType
    external_message_id: str
    sender: str
    recipients: tuple[str, ...]
    subject: str
    text_body: str
    source_timestamp: datetime
    received_timestamp: datetime
    content_type: str = "message/rfc822"
    connector_delivery_id: str | None = None
    html_body: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_nonblank("external_message_id", self.external_message_id)
        _require_nonblank("sender", self.sender)
        _require_nonblank("subject", self.subject)
        _require_nonblank("text_body", self.text_body)
        _require_nonblank("content_type", self.content_type)
        if not self.recipients or any(not recipient.strip() for recipient in self.recipients):
            raise ValueError("recipients must contain at least one nonblank recipient")
        _require_timezone_aware("source_timestamp", self.source_timestamp)
        _require_timezone_aware("received_timestamp", self.received_timestamp)
        if self.connector_delivery_id is not None:
            _require_nonblank("connector_delivery_id", self.connector_delivery_id)
        if self.html_body is not None and not self.html_body.strip():
            raise ValueError("html_body must be nonblank when provided")
        object.__setattr__(self, "headers", dict(self.headers))


@dataclass(frozen=True, slots=True)
class InboundIntakeSubmission:
    fixture: InboundMessageFixture
    metadata: RequestMetadata
    principal: AuthenticatedPrincipal


@runtime_checkable
class InboundInboxPort(Protocol):
    def adapt(self, submission: object) -> InboundMessageFixture: ...


@dataclass(frozen=True, slots=True)
class InboundIntakeResult:
    intake_item_id: str
    message_id: str
    correlation_id: str
    causation_id: str | None
    idempotency_key: str | None

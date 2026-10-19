"""Provider-neutral Gmail source port and deterministic local fixture adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


class GmailProviderError(RuntimeError):
    """Safe provider failure that is suitable for a controlled API response."""

    def __init__(self, code: str, message: str = "provider validation failed") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class GmailSourceMessage:
    message_id: str
    thread_id: str
    received_at: datetime
    sender: str | None = None
    recipient: str | None = None
    subject: str | None = None
    body: str = ""
    label_ids: frozenset[str] = field(default_factory=frozenset)
    attachments: tuple[dict[str, str | int], ...] = ()
    provider_cursor: str | None = None

    def normalized_received_at(self) -> datetime:
        value = self.received_at
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class GmailMessageMetadata:
    message_id: str
    received_at: datetime


class GmailSourceProvider(Protocol):
    provider_kind: str

    def validate_binding(
        self, *, provider_account_id: str, label_id: str, credential_secret_ref: str | None = None
    ) -> None: ...

    def discover_message_metadata(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None,
        window_start: datetime,
        window_end: datetime,
        limit: int,
    ) -> list[GmailMessageMetadata]: ...

    def list_messages(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None = None,
        cursor: str | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> list[GmailSourceMessage]: ...


class FakeGmailProvider:
    """In-memory local provider used by D1 tests and synthetic demonstrations.

    It exposes only a read operation. Fixtures are seeded by the test harness,
    never by a Gmail network client or a production credential.
    """

    provider_kind = "fake"

    def __init__(self) -> None:
        self._fixtures: dict[str, tuple[GmailSourceMessage, ...]] = {}

    def seed(self, provider_account_id: str, messages: list[GmailSourceMessage]) -> None:
        account = provider_account_id.strip()
        if not account:
            raise ValueError("provider account is required")
        self._fixtures[account] = tuple(messages)

    def clear(self) -> None:
        self._fixtures.clear()

    def validate_binding(
        self, *, provider_account_id: str, label_id: str, credential_secret_ref: str | None = None
    ) -> None:
        del credential_secret_ref
        messages = self._fixtures.get(provider_account_id)
        if messages is None:
            raise GmailProviderError("provider_account_not_seeded")
        if not label_id.strip():
            raise GmailProviderError("label_id_missing")
        if not any(label_id in message.label_ids for message in messages):
            raise GmailProviderError("label_not_found")

    def discover_message_metadata(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None,
        window_start: datetime,
        window_end: datetime,
        limit: int,
    ) -> list[GmailMessageMetadata]:
        del query, credential_secret_ref
        self.validate_binding(provider_account_id=provider_account_id, label_id=label_id)
        return [
            GmailMessageMetadata(message.message_id, message.normalized_received_at())
            for message in self._fixtures[provider_account_id]
            if label_id in message.label_ids and window_start <= message.normalized_received_at() <= window_end
        ][:limit]

    def list_messages(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None = None,
        cursor: str | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> list[GmailSourceMessage]:
        del query, credential_secret_ref, cursor, window_start, window_end
        messages = self._fixtures.get(provider_account_id)
        if messages is None:
            raise GmailProviderError("provider_account_not_seeded")
        requested_label = label_id.strip()
        if not requested_label:
            raise GmailProviderError("label_id_missing")
        if not any(requested_label in message.label_ids for message in messages):
            raise GmailProviderError("label_not_found")
        return [message for message in messages if requested_label in message.label_ids]


DEFAULT_FAKE_GMAIL_PROVIDER = FakeGmailProvider()

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

    def normalized_received_at(self) -> datetime:
        value = self.received_at
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class GmailSourceProvider(Protocol):
    def list_messages(self, *, provider_account_id: str, label_id: str, query: str) -> list[GmailSourceMessage]: ...


class FakeGmailProvider:
    """In-memory local provider used by D1 tests and synthetic demonstrations.

    It exposes only a read operation. Fixtures are seeded by the test harness,
    never by a Gmail network client or a production credential.
    """

    def __init__(self) -> None:
        self._fixtures: dict[str, tuple[GmailSourceMessage, ...]] = {}

    def seed(self, provider_account_id: str, messages: list[GmailSourceMessage]) -> None:
        account = provider_account_id.strip()
        if not account:
            raise ValueError("provider account is required")
        self._fixtures[account] = tuple(messages)

    def clear(self) -> None:
        self._fixtures.clear()

    def list_messages(self, *, provider_account_id: str, label_id: str, query: str) -> list[GmailSourceMessage]:
        del query  # The fixture adapter has no search language; the label boundary remains mandatory.
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

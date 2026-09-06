"""Entirely synthetic, in-memory Netpay intake mechanics authorized by ADR-018."""

from __future__ import annotations

import hashlib
import re
import threading
from dataclasses import dataclass, replace
from html.parser import HTMLParser
from typing import Callable, Literal, Protocol

Category = Literal[
    "commercial_contact_or_rfq",
    "tpv_physical",
    "ecommerce",
    "support_or_incident",
    "unclassified",
]
Decision = Literal["accept", "reject", "request_correction"]

CATEGORIES: tuple[Category, ...] = (
    "commercial_contact_or_rfq",
    "tpv_physical",
    "ecommerce",
    "support_or_incident",
    "unclassified",
)
SYNTHETIC_MAILBOX_BINDING = "synthetic-mailbox-binding"
SYNTHETIC_LABEL_ID = "synthetic-label"
SYNTHETIC_ORGANIZATION_ID = "synthetic-organization"
SYNTHETIC_PRINCIPAL_ID = "synthetic-reviewer"
SYNTHETIC_MEMBERSHIP_ID = "synthetic-membership"
SYNTHETIC_REVIEWER_ROLE = "synthetic-reviewer-role"


class SyntheticIntakeError(RuntimeError):
    """Controlled failure that contains no source content."""


class _PlainTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def sanitize_and_redact(value: str) -> str:
    """Produce deterministic synthetic plain text before byte truncation."""

    parser = _PlainTextExtractor()
    parser.feed(value)
    parser.close()
    plain = " ".join(parser.parts)
    plain = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", plain)
    plain = re.sub(r"(?i)\b(?:token|secret|password)\s*[:=]\s*\S+", "[REDACTED_SECRET]", plain)
    return " ".join(plain.split())


def truncate_utf8(value: str, maximum_bytes: int = 4096) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return value
    return encoded[:maximum_bytes].decode("utf-8", errors="ignore")


def excerpt_from(value: str) -> str:
    return truncate_utf8(sanitize_and_redact(value))


@dataclass(frozen=True, slots=True)
class SyntheticMessage:
    fixture_id: str
    body: str
    attachment_metadata: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    fixture_id: str
    provider_message_hash: str
    source_fingerprint: str
    mailbox_binding_id: str
    label_id: str
    expected_category: Category
    expected_excerpt: str


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    fixture_id: str
    provider_message_hash: str
    source_fingerprint: str
    mailbox_binding_id: str
    label_id: str
    organization_id: str
    proposed_category: Category
    excerpt: str
    attachment_metadata: tuple[str, ...]
    decision: Decision | None = None
    reviewer_principal_id: str | None = None


@dataclass(frozen=True, slots=True)
class CommercialIntakeBoundaryProjection:
    candidate_id: str
    organization_id: str
    kind: str
    channel: str
    summary: str
    product_interest: str
    provenance: str


@dataclass(frozen=True, slots=True)
class SyntheticOrganization:
    organization_id: str = SYNTHETIC_ORGANIZATION_ID


@dataclass(frozen=True, slots=True)
class SyntheticPrincipal:
    principal_id: str = SYNTHETIC_PRINCIPAL_ID


@dataclass(frozen=True, slots=True)
class SyntheticMembership:
    membership_id: str = SYNTHETIC_MEMBERSHIP_ID
    principal_id: str = SYNTHETIC_PRINCIPAL_ID
    organization_id: str = SYNTHETIC_ORGANIZATION_ID
    role: str = SYNTHETIC_REVIEWER_ROLE
    active: bool = True


class SyntheticProvider(Protocol):
    def messages(self) -> tuple[SyntheticMessage, ...]: ...


_FIXTURE_SPECS: tuple[tuple[str, str, Category, str], ...] = (
    (
        "SYN-MSG-001",
        "Synthetic RFQ for terminals contact@example.invalid",
        "commercial_contact_or_rfq",
        "Synthetic RFQ for terminals [REDACTED_EMAIL]",
    ),
    (
        "SYN-MSG-002",
        "Synthetic physical TPV activation request",
        "tpv_physical",
        "Synthetic physical TPV activation request",
    ),
    ("SYN-MSG-003", "Synthetic ecommerce checkout request", "ecommerce", "Synthetic ecommerce checkout request"),
    (
        "SYN-MSG-004",
        "Synthetic support incident: terminal offline",
        "support_or_incident",
        "Synthetic support incident: terminal offline",
    ),
    (
        "SYN-MSG-005",
        "Synthetic message without a known category",
        "unclassified",
        "Synthetic message without a known category",
    ),
    (
        "SYN-MSG-006",
        "<script>synthetic-script-text</script><b>Synthetic commercial contact</b> secret=fixture-only",
        "commercial_contact_or_rfq",
        "synthetic-script-text Synthetic commercial contact [REDACTED_SECRET]",
    ),
    ("SYN-MSG-007", "Synthetic TPV physical device request", "tpv_physical", "Synthetic TPV physical device request"),
    (
        "SYN-MSG-008",
        "Synthetic ecommerce integration question",
        "ecommerce",
        "Synthetic ecommerce integration question",
    ),
    (
        "SYN-MSG-009",
        "Synthetic incident requiring support",
        "support_or_incident",
        "Synthetic incident requiring support",
    ),
    ("SYN-MSG-010", "🙂" * 1100, "unclassified", "🙂" * 1024),
)


def _safe_hash(prefix: str, fixture_id: str) -> str:
    return hashlib.sha256(f"{prefix}:{fixture_id}".encode()).hexdigest()


SYNTHETIC_MESSAGES: tuple[SyntheticMessage, ...] = tuple(
    SyntheticMessage(fixture_id, body, ("synthetic-metadata-only",)) for fixture_id, body, _, _ in _FIXTURE_SPECS
)
SYNTHETIC_MANIFEST: tuple[ManifestEntry, ...] = tuple(
    ManifestEntry(
        fixture_id=fixture_id,
        provider_message_hash=_safe_hash("provider", fixture_id),
        source_fingerprint=_safe_hash("source", fixture_id),
        mailbox_binding_id=SYNTHETIC_MAILBOX_BINDING,
        label_id=SYNTHETIC_LABEL_ID,
        expected_category=category,
        expected_excerpt=expected_excerpt,
    )
    for fixture_id, _, category, expected_excerpt in _FIXTURE_SPECS
)


class FakeSyntheticProvider:
    def messages(self) -> tuple[SyntheticMessage, ...]:
        return SYNTHETIC_MESSAGES


def deterministic_classifier(message: SyntheticMessage) -> Category:
    fixture = next((entry for entry in SYNTHETIC_MANIFEST if entry.fixture_id == message.fixture_id), None)
    if fixture is None:
        raise SyntheticIntakeError("synthetic manifest mismatch")
    return fixture.expected_category


class SyntheticIntakeHarness:
    """Atomic in-memory candidate workflow; it owns no productive state."""

    def __init__(
        self,
        provider: SyntheticProvider | None = None,
        classifier: Callable[[SyntheticMessage], str] = deterministic_classifier,
        fail_at_fixture: str | None = None,
    ) -> None:
        self._provider = provider or FakeSyntheticProvider()
        self._classifier = classifier
        self._fail_at_fixture = fail_at_fixture
        self._candidates: dict[str, Candidate] = {}
        self._projections: dict[str, CommercialIntakeBoundaryProjection] = {}
        self._checkpoint: str | None = None
        self._enabled = True
        self._lock = threading.RLock()
        self.organization = SyntheticOrganization()
        self.principal = SyntheticPrincipal()
        self.membership = SyntheticMembership()

    @property
    def checkpoint(self) -> str | None:
        with self._lock:
            return self._checkpoint

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def list_candidates(self) -> tuple[Candidate, ...]:
        with self._lock:
            self._require_enabled()
            return tuple(self._candidates[key] for key in sorted(self._candidates))

    def get_candidate(self, candidate_id: str) -> Candidate:
        with self._lock:
            self._require_enabled()
            try:
                return self._candidates[candidate_id]
            except KeyError as exc:
                raise SyntheticIntakeError("synthetic candidate not found") from exc

    def synchronize(self) -> tuple[Candidate, ...]:
        with self._lock:
            self._require_enabled()
            if self._checkpoint == "synthetic-manifest-complete":
                return self.list_candidates()
            messages = self._provider.messages()
            manifest = {entry.fixture_id: entry for entry in SYNTHETIC_MANIFEST}
            if len(messages) != 10 or len({item.fixture_id for item in messages}) != 10:
                raise SyntheticIntakeError("synthetic provider cardinality mismatch")
            staged: dict[str, Candidate] = {}
            for message in messages:
                if message.fixture_id == self._fail_at_fixture:
                    raise SyntheticIntakeError("controlled synthetic synchronization failure")
                entry = manifest.get(message.fixture_id)
                if entry is None:
                    raise SyntheticIntakeError("synthetic manifest mismatch")
                category = self._classifier(message)
                if category not in CATEGORIES:
                    raise SyntheticIntakeError("synthetic category rejected")
                excerpt = excerpt_from(message.body)
                if category != entry.expected_category or excerpt != entry.expected_excerpt:
                    raise SyntheticIntakeError("synthetic oracle mismatch")
                candidate_id = f"candidate-{message.fixture_id.lower()}"
                staged[candidate_id] = Candidate(
                    candidate_id=candidate_id,
                    fixture_id=message.fixture_id,
                    provider_message_hash=entry.provider_message_hash,
                    source_fingerprint=entry.source_fingerprint,
                    mailbox_binding_id=entry.mailbox_binding_id,
                    label_id=entry.label_id,
                    organization_id=self.organization.organization_id,
                    proposed_category=category,  # type: ignore[arg-type]
                    excerpt=excerpt,
                    attachment_metadata=message.attachment_metadata,
                )
            if set(manifest) != {candidate.fixture_id for candidate in staged.values()}:
                raise SyntheticIntakeError("synthetic manifest omission")
            self._candidates = staged
            self._checkpoint = "synthetic-manifest-complete"
            return self.list_candidates()

    def decide(self, candidate_id: str, decision: Decision) -> Candidate:
        with self._lock:
            self._require_enabled()
            if decision not in ("accept", "reject", "request_correction"):
                raise SyntheticIntakeError("synthetic decision rejected")
            if not self.membership.active or self.membership.principal_id != self.principal.principal_id:
                raise SyntheticIntakeError("synthetic reviewer authority rejected")
            if self.membership.organization_id != self.organization.organization_id:
                raise SyntheticIntakeError("synthetic reviewer authority rejected")
            candidate = self.get_candidate(candidate_id)
            if candidate.decision is not None:
                if candidate.decision == decision:
                    return candidate
                raise SyntheticIntakeError("synthetic decision conflict")
            decided = replace(candidate, decision=decision, reviewer_principal_id=self.principal.principal_id)
            self._candidates[candidate_id] = decided
            if decision == "accept" and candidate.proposed_category == "commercial_contact_or_rfq":
                self._projections[candidate_id] = CommercialIntakeBoundaryProjection(
                    candidate_id=candidate_id,
                    organization_id=self.organization.organization_id,
                    kind="rfq",
                    channel="synthetic",
                    summary=candidate.excerpt,
                    product_interest="other",
                    provenance=candidate.source_fingerprint,
                )
            return decided

    def projection_for(self, candidate_id: str) -> CommercialIntakeBoundaryProjection | None:
        with self._lock:
            return self._projections.get(candidate_id)

    def disable(self) -> None:
        with self._lock:
            self._candidates = {}
            self._projections = {}
            self._checkpoint = None
            self._enabled = False

    def _require_enabled(self) -> None:
        if not self._enabled:
            raise SyntheticIntakeError("synthetic harness disabled")

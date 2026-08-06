"""Trace lifecycle, inspection boundary, and best-effort recording policy."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from uuid import UUID, uuid4

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.ports import TraceInspectionAuthorizer
from yarvis_api.models.application_trace import ApplicationTrace
from yarvis_api.observability.logging import emit_observability_event
from yarvis_api.observability.metrics import ObservabilityMetrics
from yarvis_api.observability.redaction import sanitize_text
from yarvis_api.persistence.application_trace_store import ApplicationTraceStore

MAX_TRACE_REFERENCES = 32
TRACE_REFERENCE_TYPES = frozenset(
    {
        "unknown",
        "intake_item",
        "external_source",
        "domain_event",
        "event",
        "result",
        "retry",
        "compensation",
    }
)


def _normalize_references(value: object, *, field_name: str) -> tuple["TraceReference", ...]:
    """Accept only bounded list/tuple reference collections and freeze them."""

    if not isinstance(value, (list, tuple)):
        raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, f"invalid {field_name} trace references")
    if len(value) > MAX_TRACE_REFERENCES or not all(isinstance(item, TraceReference) for item in value):
        raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, f"invalid {field_name} trace references")
    return tuple(value)


def _optional_reference(value: object, *, field_name: str) -> "TraceReference | None":
    if value is None or isinstance(value, TraceReference):
        return value
    raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, f"invalid {field_name} trace reference")


class TraceEntryKind(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TraceAuthorizationDecision(StrEnum):
    GRANTED = "granted"
    DENIED = "denied"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True, slots=True)
class TraceReference:
    """Closed, scalar-only trace reference; it cannot carry payload or state."""

    reference_type: str
    reference_id: str | None = None
    contract_id: str | None = None
    contract_version: str | None = None
    owner_context: str | None = None
    relation: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reference_type, str) or not self.reference_type.strip():
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid trace reference")
        normalized_type = self.reference_type.strip()
        if normalized_type not in TRACE_REFERENCE_TYPES:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid trace reference")
        object.__setattr__(self, "reference_type", normalized_type)
        for name in ("reference_type", "reference_id", "contract_id", "contract_version", "owner_context", "relation"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 255):
                raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid trace reference")

    def as_dict(self) -> dict[str, str]:
        return {name: value for name in ("reference_type", "reference_id", "contract_id", "contract_version", "owner_context", "relation") if (value := getattr(self, name)) is not None}


@dataclass(frozen=True, slots=True)
class TraceContext:
    interaction_contract_id: str
    contract_version: str
    owner_module_id: str
    owning_context: str
    correlation_id: str
    actor_id: str | None = None
    organization_id: UUID | None = None
    causation_id: str | None = None
    authorization_decision: TraceAuthorizationDecision = TraceAuthorizationDecision.NOT_EVALUATED
    object_reference: TraceReference = field(default_factory=lambda: TraceReference("unknown"))
    provenance_references: Sequence[TraceReference] = ()
    evidence_references: Sequence[TraceReference] = ()
    retry_reference: TraceReference | None = None
    compensation_reference: TraceReference | None = None

    def __post_init__(self) -> None:
        for name in ("interaction_contract_id", "contract_version", "owner_module_id", "owning_context", "correlation_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonblank")
        if not isinstance(self.object_reference, TraceReference):
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid trace reference")
        object.__setattr__(self, "provenance_references", _normalize_references(self.provenance_references, field_name="provenance"))
        object.__setattr__(self, "evidence_references", _normalize_references(self.evidence_references, field_name="evidence"))
        object.__setattr__(self, "retry_reference", _optional_reference(self.retry_reference, field_name="retry"))
        object.__setattr__(self, "compensation_reference", _optional_reference(self.compensation_reference, field_name="compensation"))


class DenyAllTraceInspectionAuthorizer:
    def may_inspect(self, *, trace_id: UUID | None, correlation_id: str | None) -> bool:
        return False


@dataclass(slots=True)
class TraceSession:
    _recorder: "TraceRecorder"
    _context: TraceContext
    trace_id: UUID
    _started: bool
    _start_attempted: bool = False
    _started_at: float = field(default_factory=perf_counter)
    _terminal: bool = False

    def succeed(
        self,
        *,
        result_reference: TraceReference | None = None,
        event_references: Sequence[TraceReference] = (),
    ) -> None:
        if self._terminal:
            return
        normalized_events = _normalize_references(event_references, field_name="event")
        normalized_result = _optional_reference(result_reference, field_name="result")
        self._terminal = True
        self._recorder._append_terminal(
            self,
            TraceEntryKind.SUCCEEDED,
            result_reference=normalized_result,
            event_references=normalized_events,
        )

    def fail(self, error: BaseException) -> None:
        if self._terminal:
            return
        self._terminal = True
        self._recorder._append_terminal(
            self,
            TraceEntryKind.FAILED,
            error=error,
        )


class TraceOperation(AbstractContextManager[TraceSession]):
    def __init__(self, session: TraceSession) -> None:
        self._session = session

    def __enter__(self) -> TraceSession:
        return self._session

    def __exit__(self, exc_type: object, exc: BaseException | None, traceback: object) -> bool:
        if exc is not None:
            self._session.fail(exc)
        elif not self._session._terminal:
            self._session.succeed()
        return False


@dataclass(slots=True)
class TraceRecorder:
    store: ApplicationTraceStore
    metrics: ObservabilityMetrics
    logger: logging.Logger

    def begin(self, context: TraceContext) -> TraceSession:
        trace_id = uuid4()
        session = TraceSession(self, context, trace_id, _started=False)
        self._ensure_started(session)
        return session

    def observe(self, context: TraceContext) -> TraceOperation:
        return TraceOperation(self.begin(context))

    def _ensure_started(self, session: TraceSession) -> bool:
        """Persist the started entry only after terminal inputs are validated."""

        if session._started:
            return True
        if session._start_attempted:
            return False
        session._start_attempted = True
        try:
            self.store.append(self._entry(session, TraceEntryKind.STARTED))
        except Exception as error:
            self._record_observability_failure("trace_start_failed", error, session.trace_id)
            return False
        else:
            session._started = True
            self.metrics.increment("yarvis_trace_entries_total")
            return True

    def _append_terminal(
        self,
        session: TraceSession,
        entry_kind: TraceEntryKind,
        *,
        result_reference: TraceReference | None = None,
        event_references: Sequence[TraceReference] = (),
        error: BaseException | None = None,
    ) -> None:
        duration = perf_counter() - session._started_at
        self.metrics.observe_duration("yarvis_handler_duration_seconds", duration)
        if entry_kind == TraceEntryKind.FAILED:
            self.metrics.increment("yarvis_handler_failures_total")
        if not self._ensure_started(session):
            return
        try:
            self.store.append(
                self._entry(
                    session,
                    entry_kind,
                    result_reference=result_reference,
                    event_references=event_references,
                    error=error,
                )
            )
        except Exception as recording_error:
            self._record_observability_failure("trace_terminal_failed", recording_error, session.trace_id)
        else:
            self.metrics.increment("yarvis_trace_entries_total")

    def _entry(
        self,
        session: TraceSession,
        entry_kind: TraceEntryKind,
        *,
        result_reference: TraceReference | None = None,
        event_references: Sequence[TraceReference] = (),
        error: BaseException | None = None,
    ) -> ApplicationTrace:
        context = session._context
        error_code: str | None = None
        if isinstance(error, ApplicationError):
            error_code = error.code.value
        elif error is not None:
            error_code = ApplicationErrorCode.INFRASTRUCTURE_FAILURE.value
        return ApplicationTrace(
            trace_id=session.trace_id,
            sequence=1 if entry_kind == TraceEntryKind.STARTED else 2,
            entry_kind=entry_kind.value,
            interaction_contract_id=context.interaction_contract_id,
            contract_version=context.contract_version,
            owner_module_id=context.owner_module_id,
            owning_context=context.owning_context,
            actor_id=context.actor_id,
            organization_id=context.organization_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            authorization_decision=context.authorization_decision.value,
            object_reference=context.object_reference.as_dict(),
            result_reference=result_reference.as_dict() if result_reference is not None else {},
            event_references=[reference.as_dict() for reference in event_references],
            provenance_references=[reference.as_dict() for reference in context.provenance_references],
            evidence_references=[reference.as_dict() for reference in context.evidence_references],
            retry_reference=context.retry_reference.as_dict() if context.retry_reference else None,
            compensation_reference=context.compensation_reference.as_dict() if context.compensation_reference else None,
            error_code=error_code,
            error_type=error.__class__.__name__ if error is not None else None,
            failure_summary=(
                sanitize_text(error.message)
                if isinstance(error, ApplicationError)
                else sanitize_text(error)
                if error is not None
                else None
            ),
            occurred_at=datetime.now(timezone.utc),
        )

    def _record_observability_failure(self, event: str, error: BaseException, trace_id: UUID) -> None:
        self.metrics.increment("yarvis_trace_recording_failures_total")
        emit_observability_event(
            self.logger,
            event,
            trace_id=str(trace_id),
            error_type=error.__class__.__name__,
            error_summary=sanitize_text(error),
        )


@dataclass(frozen=True, slots=True)
class TraceInspectionService:
    store: ApplicationTraceStore
    authorizer: TraceInspectionAuthorizer

    def by_trace_id(self, trace_id: UUID) -> tuple[ApplicationTrace, ...]:
        if not self.authorizer.may_inspect(trace_id=trace_id, correlation_id=None):
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "trace inspection is not authorized")
        return self.store.list_by_trace_id(trace_id)

    def by_correlation_id(self, correlation_id: str) -> tuple[ApplicationTrace, ...]:
        if not self.authorizer.may_inspect(trace_id=None, correlation_id=correlation_id):
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "trace inspection is not authorized")
        return self.store.list_by_correlation_id(correlation_id)

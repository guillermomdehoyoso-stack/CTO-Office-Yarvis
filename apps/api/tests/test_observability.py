from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from yarvis_api.api.errors import application_error_payload, error_to_http_status
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.main import app
from yarvis_api.models.application_trace import ApplicationTrace
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.observability.metrics import ObservabilityMetrics
from yarvis_api.observability.logging import StructuredLogFormatter
from yarvis_api.observability.readiness import ReadinessReport
from yarvis_api.observability.redaction import sanitize_mapping
from yarvis_api.observability.tracing import MAX_TRACE_REFERENCES, TRACE_REFERENCE_TYPES, TraceAuthorizationDecision, TraceContext, TraceInspectionService, TraceRecorder, TraceReference


def _context(**overrides: object) -> TraceContext:
    values: dict[str, object] = {
        "interaction_contract_id": "IC-INBOX-CMD-001",
        "contract_version": "1.0",
        "owner_module_id": "observation_evidence",
        "owning_context": "Intake",
        "correlation_id": "corr-f012",
        "actor_id": "user:operator",
        "authorization_decision": TraceAuthorizationDecision.NOT_EVALUATED,
        "object_reference": TraceReference("intake_item", owner_context="Intake"),
    }
    values.update(overrides)
    return TraceContext(**values)  # type: ignore[arg-type]


def _count() -> int:
    with app.state.yarvis.persistence.create_session() as session:
        return session.scalar(select(func.count()).select_from(ApplicationTrace)) or 0


def test_error_categories_and_public_translation_are_sanitized() -> None:
    required = {
        "VALIDATION_FAILED", "AUTHORIZATION_DENIED", "INVARIANT_VIOLATION", "CONFLICT",
        "DEPENDENCY_UNAVAILABLE", "STALE_PROJECTION", "UNCERTAIN_RESULT", "COMMAND_REJECTED",
        "EXECUTION_FAILED", "INFRASTRUCTURE_FAILURE",
    }
    assert required <= set(ApplicationErrorCode.__members__)

    error = ApplicationError(
        ApplicationErrorCode.INFRASTRUCTURE_FAILURE,
        "postgres password SELECT * FROM confidential",
        {"authorization": "Bearer secret", "safe": "reference"},
    )
    payload = application_error_payload(error)
    assert error_to_http_status(error) == 500
    assert payload["message"] == "request could not be completed"
    assert payload["details"] == {"authorization": "[REDACTED]", "safe": "reference"}


def test_deep_redaction_and_structured_logging_never_emit_secret_values() -> None:
    value = sanitize_mapping({"outer": {"cookie": "super-secret"}, "items": [{"api_key": "key-value"}]})
    assert value == {"outer": {"cookie": "[REDACTED]"}, "items": [{"api_key": "[REDACTED]"}]}
    record = logging.LogRecord("yarvis.observability", logging.INFO, __file__, 0, "trace persisted", (), None)
    record.observability = {"authorization": "Bearer hidden", "nested": value}  # type: ignore[attr-defined]
    rendered = StructuredLogFormatter().format(record)
    assert "super-secret" not in rendered
    assert "key-value" not in rendered
    assert json.loads(rendered)["authorization"] == "[REDACTED]"


def test_free_text_redaction_is_deep_idempotent_and_preserves_useful_text() -> None:
    from yarvis_api.observability.redaction import sanitize_text

    source = "safe context; password: super-secret; Token: super-secret; Authorization: Bearer abc.def.ghi; api_key = private-value; Cookie: session=private-session; {'Authorization': 'Bearer quoted-token'}"
    redacted = sanitize_text(source)
    assert "safe context" in redacted
    assert all(value not in redacted for value in ("super-secret", "abc.def.ghi", "private-value", "private-session", "quoted-token"))
    assert sanitize_text(redacted) == redacted


def test_trace_references_reject_payload_state_headers_and_nested_values() -> None:
    with pytest.raises(ApplicationError) as invalid_context:
        _context(object_reference={"payload": {"card_number": "4111111111111111"}})
    assert invalid_context.value.code == ApplicationErrorCode.VALIDATION_FAILED
    for value in ({"state": {"customer": "x"}}, {"headers": {"Authorization": "Bearer secret"}}, {"response": {"body": "x"}}):
        with pytest.raises(ApplicationError):
            _context(object_reference=value)
    with pytest.raises(ApplicationError):
        TraceReference("x" * 256)
    for invalid_type in (None, "", "   ", "unapproved"):
        with pytest.raises(ApplicationError) as error:
            TraceReference(invalid_type)  # type: ignore[arg-type]
        assert error.value.code == ApplicationErrorCode.VALIDATION_FAILED
    assert TraceReference(" intake_item ").reference_type == "intake_item"
    assert "intake_item" in TRACE_REFERENCE_TYPES


def test_reference_collections_are_bounded_typed_and_immutable() -> None:
    reference = TraceReference("event", reference_id="one")
    maximum = [reference] * MAX_TRACE_REFERENCES
    context = _context(provenance_references=maximum, evidence_references=tuple(maximum))
    assert isinstance(context.provenance_references, tuple)
    assert len(context.provenance_references) == MAX_TRACE_REFERENCES
    maximum.clear()
    assert len(context.provenance_references) == MAX_TRACE_REFERENCES
    for invalid in ({"reference_type": "event"}, "text", (item for item in [reference]), [reference, object()]):
        with pytest.raises(ApplicationError):
            _context(provenance_references=invalid)
    with pytest.raises(ApplicationError):
        _context(evidence_references=[reference] * (MAX_TRACE_REFERENCES + 1))
    trace = app.state.yarvis.trace_recorder.begin(_context())
    trace.succeed(event_references=[reference] * MAX_TRACE_REFERENCES)
    with pytest.raises(ApplicationError):
        app.state.yarvis.trace_recorder.begin(_context()).succeed(event_references=[reference] * (MAX_TRACE_REFERENCES + 1))


def test_duration_metrics_use_constant_size_aggregates() -> None:
    metrics = ObservabilityMetrics()
    for value in range(10_000):
        metrics.observe_duration("bounded", value / 10_000)
    aggregate = metrics.snapshot()["durations"]["bounded"]
    assert aggregate["count"] == 10_000
    assert aggregate["min_seconds"] == 0.0
    assert aggregate["max_seconds"] > 0.9
    assert len(metrics._durations["bounded"]) == 4


def test_trace_started_succeeded_is_sanitized_and_append_only(clean_database) -> None:
    recorder = app.state.yarvis.trace_recorder
    trace = recorder.begin(_context())
    trace.succeed(result_reference=TraceReference("intake_item", "result-1"), event_references=[TraceReference("domain_event", contract_id="evt-1")])

    rows = app.state.yarvis.trace_inspection_service.store.list_by_trace_id(trace.trace_id)
    assert [row.entry_kind for row in rows] == ["started", "succeeded"]
    assert rows[0].object_reference == {"reference_type": "intake_item", "owner_context": "Intake"}
    assert rows[1].result_reference == {"reference_type": "intake_item", "reference_id": "result-1"}
    assert rows[1].event_references == [{"reference_type": "domain_event", "contract_id": "evt-1"}]

    with app.state.yarvis.persistence.create_session() as session:
        with pytest.raises(DBAPIError):
            session.execute(text("UPDATE application_traces SET sequence = 99 WHERE trace_id = :trace_id"), {"trace_id": trace.trace_id})
        session.rollback()
        with pytest.raises(DBAPIError):
            session.execute(text("DELETE FROM application_traces WHERE trace_id = :trace_id"), {"trace_id": trace.trace_id})
        session.rollback()
    assert _count() == 2


def test_postgresql_rejects_invalid_direct_trace_transitions(clean_database) -> None:
    trace = app.state.yarvis.trace_recorder.begin(_context())
    with app.state.yarvis.persistence.create_session() as session:
        source = trace.trace_id
        common = {
            "id": uuid4(),
            "trace_id": uuid4(),
            "source_trace_id": source,
        }
        with pytest.raises(DBAPIError):
            session.execute(
                text(
                    """
                    INSERT INTO application_traces (
                      id, trace_id, sequence, entry_kind, interaction_contract_id, contract_version,
                      owner_module_id, owning_context, actor_id, organization_id, correlation_id,
                      causation_id, authorization_decision, object_reference, result_reference,
                      event_references, provenance_references, evidence_references, occurred_at
                    )
                    SELECT :id, :trace_id, 2, 'succeeded', interaction_contract_id, contract_version,
                      owner_module_id, owning_context, actor_id, organization_id, correlation_id,
                      causation_id, authorization_decision, object_reference, result_reference,
                      event_references, provenance_references, evidence_references, occurred_at
                    FROM application_traces WHERE trace_id = :source_trace_id AND sequence = 1
                    """
                ),
                common,
            )
        session.rollback()
        with pytest.raises(DBAPIError):
            session.execute(
                text(
                    "UPDATE application_traces SET sequence = 2 WHERE trace_id = :trace_id"),
                {"trace_id": source},
            )
        session.rollback()


def test_succeed_without_result_persists_terminal_and_optional_references_are_closed(clean_database) -> None:
    trace = app.state.yarvis.trace_recorder.begin(_context())
    trace.succeed()
    assert [row.entry_kind for row in app.state.yarvis.trace_inspection_service.store.list_by_trace_id(trace.trace_id)] == ["started", "succeeded"]
    for invalid in ({}, "text", [TraceReference("event")], (item for item in []), object()):
        with pytest.raises(ApplicationError) as error:
            app.state.yarvis.trace_recorder.begin(_context()).succeed(result_reference=invalid)  # type: ignore[arg-type]
        assert error.value.code == ApplicationErrorCode.VALIDATION_FAILED
        for field in ("retry_reference", "compensation_reference"):
            with pytest.raises(ApplicationError):
                _context(**{field: invalid})
    context = _context(retry_reference=TraceReference("retry", "r"), compensation_reference=TraceReference("compensation", "c"))
    assert context.retry_reference is not None and context.compensation_reference is not None


def test_invalid_terminal_references_are_rejected_without_partial_terminal_persistence(clean_database) -> None:
    before = _count()
    invalid = {"payload": {"card_number": "4111111111111111"}}
    with pytest.raises(ApplicationError) as result_error:
        app.state.yarvis.trace_recorder.begin(_context()).succeed(result_reference=invalid)  # type: ignore[arg-type]
    assert result_error.value.code == ApplicationErrorCode.VALIDATION_FAILED
    assert _count() == before + 1
    for field in ("retry_reference", "compensation_reference"):
        with pytest.raises(ApplicationError) as reference_error:
            _context(**{field: invalid})
        assert reference_error.value.code == ApplicationErrorCode.VALIDATION_FAILED
        assert _count() == before + 1


def test_maximum_references_round_trip_without_truncation(clean_database) -> None:
    maximum = "x" * 255
    reference = TraceReference(
        "retry",
        reference_id=maximum,
        contract_id=maximum,
        contract_version=maximum,
        owner_context=maximum,
        relation=maximum,
    )
    context = _context(
        retry_reference=reference,
        compensation_reference=TraceReference(
            "compensation",
            reference_id=maximum,
            contract_id=maximum,
            contract_version=maximum,
            owner_context=maximum,
            relation=maximum,
        ),
    )
    trace = app.state.yarvis.trace_recorder.begin(context)
    trace.succeed(result_reference=TraceReference("result", reference_id=maximum))
    rows = app.state.yarvis.trace_inspection_service.store.list_by_trace_id(trace.trace_id)
    assert rows[-1].result_reference["reference_id"] == maximum
    assert rows[-1].retry_reference == reference.as_dict()
    assert rows[-1].compensation_reference["reference_id"] == maximum


def test_trace_started_failed_preserves_business_error_and_sanitizes_failure(clean_database) -> None:
    trace = app.state.yarvis.trace_recorder.begin(_context(correlation_id="corr-failure"))
    error = ApplicationError(ApplicationErrorCode.CONFLICT, "duplicate token value", {"token": "not-safe"})
    trace.fail(error)

    rows = app.state.yarvis.trace_inspection_service.store.list_by_trace_id(trace.trace_id)
    assert [row.entry_kind for row in rows] == ["started", "failed"]
    assert rows[-1].error_code == "CONFLICT"
    assert rows[-1].failure_summary == "duplicate token value"


@dataclass
class _FailingStore:
    def append(self, _: ApplicationTrace) -> None:
        raise RuntimeError("postgres password failure")


@dataclass
class _TerminalFailingStore:
    entries: list[ApplicationTrace]

    def append(self, entry: ApplicationTrace) -> None:
        if self.entries:
            raise RuntimeError("postgres password failure")
        self.entries.append(entry)


def test_trace_recording_failure_does_not_change_success_or_hide_business_failure() -> None:
    metrics = ObservabilityMetrics()
    recorder = TraceRecorder(_FailingStore(), metrics, logging.getLogger("test.f012"))  # type: ignore[arg-type]
    successful = recorder.begin(_context(correlation_id="corr-success"))
    successful.succeed(result_reference=TraceReference("result", "result"))

    terminal_metrics = ObservabilityMetrics()
    terminal_recorder = TraceRecorder(_TerminalFailingStore([]), terminal_metrics, logging.getLogger("test.f012"))
    terminal_success = terminal_recorder.begin(_context(correlation_id="corr-terminal-success"))
    terminal_success.succeed(result_reference=TraceReference("result", "result"))

    with pytest.raises(ValueError, match="business failure"):
        with terminal_recorder.observe(_context(correlation_id="corr-both")):
            raise ValueError("business failure")

    snapshot = metrics.snapshot()
    assert snapshot["counters"]["yarvis_trace_recording_failures_total"] == 1
    assert terminal_metrics.snapshot()["counters"]["yarvis_trace_recording_failures_total"] == 2
    assert terminal_metrics.snapshot()["counters"]["yarvis_handler_failures_total"] == 1


@dataclass(frozen=True)
class _AllowAuthorizer:
    def may_inspect(self, *, trace_id: UUID | None, correlation_id: str | None) -> bool:
        return trace_id is not None or correlation_id is not None


def test_trace_inspection_is_deny_by_default_and_can_be_explicitly_authorized(clean_database) -> None:
    trace = app.state.yarvis.trace_recorder.begin(_context(correlation_id="corr-inspection"))
    trace.succeed()

    with pytest.raises(ApplicationError) as denied:
        app.state.yarvis.trace_inspection_service.by_trace_id(trace.trace_id)
    assert denied.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED

    authorized = TraceInspectionService(app.state.yarvis.trace_inspection_service.store, _AllowAuthorizer())
    assert tuple(row.id for row in authorized.by_trace_id(trace.trace_id)) == tuple(
        row.id for row in app.state.yarvis.trace_inspection_service.store.list_by_trace_id(trace.trace_id)
    )


def test_liveness_readiness_and_metrics_snapshot(clean_database) -> None:
    app.state.yarvis.lifecycle_active = True
    try:
        client = TestClient(app)
        assert client.get("/health").json() == {"status": "ok", "service": "yarvis-api"}
        assert client.get("/ready").json() == {"status": "ready", "service": "yarvis-api"}
        snapshot = client.get("/metrics").json()
    finally:
        app.state.yarvis.lifecycle_active = False
    assert snapshot["gauges"]["yarvis_readiness_ready"] == 1
    assert set(snapshot) == {"counters", "durations", "gauges"}


def test_readiness_dependency_failure_is_sanitized_503(clean_database) -> None:
    original_probe = app.state.yarvis.readiness_probe

    @dataclass(frozen=True)
    class _UnavailableProbe:
        def check(self, **_: object) -> ReadinessReport:
            return ReadinessReport(False, "postgres password unavailable")

    app.state.yarvis.lifecycle_active = True
    app.state.yarvis.readiness_probe = _UnavailableProbe()  # type: ignore[assignment]
    try:
        response = TestClient(app).get("/ready")
    finally:
        app.state.yarvis.readiness_probe = original_probe
        app.state.yarvis.lifecycle_active = False
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "DEPENDENCY_UNAVAILABLE", "message": "service is not ready"}}


def test_intake_reference_flow_records_trace_without_changing_idempotency(clean_database) -> None:
    organization_id = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=organization_id, legal_name="F012 Intake", display_name="F012 Intake"))
        session.flush()
        principal = Principal(external_subject="connector:f012", status="active")
        session.add(principal)
        session.flush()
        session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role="inbound_operator"))
        session.commit()

    correlation_id = uuid4()
    payload = {
        "external_source": "email", "external_message_id": uuid4().hex, "connector_delivery_id": "f012-delivery",
        "sender": "sender@example.com", "recipients": ["ops@example.com"], "subject": "F012 intake",
        "text_body": "body", "content_type": "message/rfc822", "source_timestamp": "2026-08-05T00:00:00Z",
        "received_timestamp": "2026-08-05T00:00:00Z", "headers": {"authorization": "not-persisted"},
        "correlation_id": str(correlation_id), "idempotency_key": "f012-intake-key",
    }
    headers = {
        "x-yarvis-subject": "connector:f012", "x-yarvis-actor": "forged-observability-actor",
        "x-yarvis-organization": str(uuid4()), "x-yarvis-authority": "forged.authority",
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }
    client = TestClient(app)
    first = client.post("/intake/deterministic", json=payload, headers=headers)
    replay = client.post("/intake/deterministic", json=payload, headers=headers)
    assert first.status_code == replay.status_code == 201, (first.text, replay.text)
    assert first.json()["id"] == replay.json()["id"]
    rows = app.state.yarvis.trace_inspection_service.store.list_by_correlation_id(str(correlation_id))
    assert [row.entry_kind for row in rows] == ["started", "succeeded", "started", "succeeded"]
    assert all("authorization" not in str(row.object_reference).lower() or "[REDACTED]" in str(row.object_reference) for row in rows)

from __future__ import annotations

import ast
import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import yarvis_api.synthetic_netpay_intake as intake_module
import yarvis_api.synthetic_netpay_intake_app as app_module
from yarvis_api.bootstrap import create_app
from yarvis_api.config import Settings
from yarvis_api.synthetic_netpay_intake import (
    CATEGORIES,
    SYNTHETIC_MANIFEST,
    SYNTHETIC_MESSAGES,
    FakeSyntheticProvider,
    SyntheticIntakeError,
    SyntheticIntakeHarness,
    SyntheticMembership,
    SyntheticMessage,
    excerpt_from,
)
from yarvis_api.synthetic_netpay_intake_app import (
    ALLOWED_ORIGINS,
    BANNER,
    CSP,
    LOCAL_PORT,
    create_synthetic_app,
    main,
)

HOST = f"127.0.0.1:{LOCAL_PORT}"
ORIGIN = next(value for value in ALLOWED_ORIGINS if "127.0.0.1" in value)


def client_for(app, peer: tuple[str, int] = ("127.0.0.1", 50000)) -> TestClient:
    return TestClient(app, client=peer, headers={"host": HOST})


def mutation_headers(app, **extra: str) -> dict[str, str]:
    return {"host": HOST, "origin": ORIGIN, "x-csrf-token": app.state.csrf_token, **extra}


def test_manifest_oracles_catalog_and_synthetic_boundaries() -> None:
    assert len(SYNTHETIC_MANIFEST) == len({item.fixture_id for item in SYNTHETIC_MANIFEST}) == 10
    assert {item.fixture_id for item in SYNTHETIC_MANIFEST} == {f"SYN-MSG-{number:03}" for number in range(1, 11)}
    assert set(CATEGORIES) == {item.expected_category for item in SYNTHETIC_MANIFEST}
    harness = SyntheticIntakeHarness()
    candidates = harness.synchronize()
    assert len(candidates) == 10
    assert all(item.decision is None and item.reviewer_principal_id is None for item in candidates)
    assert all(
        item.proposed_category == expected.expected_category for item, expected in zip(candidates, SYNTHETIC_MANIFEST)
    )
    assert all(item.excerpt == expected.expected_excerpt for item, expected in zip(candidates, SYNTHETIC_MANIFEST))
    serialized = repr(candidates)
    assert "body=" not in serialized and "raw_payload" not in serialized and "attachment_bytes" not in serialized


def test_manifest_excerpt_oracle_is_independent_of_implementation(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = tuple(item.expected_excerpt for item in SYNTHETIC_MANIFEST)
    assert expected[0] == "Synthetic RFQ for terminals [REDACTED_EMAIL]"
    assert expected[5] == "synthetic-script-text Synthetic commercial contact [REDACTED_SECRET]"
    assert expected[9] == "🙂" * 1024
    monkeypatch.setattr(intake_module, "excerpt_from", lambda _value: "broken-derived-oracle")
    assert tuple(item.expected_excerpt for item in SYNTHETIC_MANIFEST) == expected
    harness = SyntheticIntakeHarness()
    with pytest.raises(SyntheticIntakeError, match="synthetic oracle mismatch"):
        harness.synchronize()
    assert harness.checkpoint is None and harness.list_candidates() == ()


def test_utf8_sanitization_redaction_then_multibyte_truncation() -> None:
    value = "<script>alert(1)</script> contact@example.invalid token=fixture-only " + ("🙂" * 2000)
    result = excerpt_from(value)
    assert "<script>" not in result
    assert "contact@example.invalid" not in result
    assert "fixture-only" not in result
    assert "[REDACTED_EMAIL]" in result and "[REDACTED_SECRET]" in result
    assert len(result.encode("utf-8")) <= 4096
    result.encode("utf-8").decode("utf-8")


def test_atomic_failure_invalid_category_and_idempotency() -> None:
    failing = SyntheticIntakeHarness(fail_at_fixture="SYN-MSG-006")
    with pytest.raises(SyntheticIntakeError):
        failing.synchronize()
    assert failing.checkpoint is None
    assert failing.list_candidates() == ()
    invalid = SyntheticIntakeHarness(classifier=lambda _message: "invalid")
    with pytest.raises(SyntheticIntakeError):
        invalid.synchronize()
    assert invalid.checkpoint is None and invalid.list_candidates() == ()
    harness = SyntheticIntakeHarness()
    first = harness.synchronize()
    second = harness.synchronize()
    assert first == second and len({item.candidate_id for item in second}) == 10


def test_provider_cardinality_and_manifest_omission_fail_closed() -> None:
    class MissingProvider(FakeSyntheticProvider):
        def messages(self) -> tuple[SyntheticMessage, ...]:
            return SYNTHETIC_MESSAGES[:-1]

    harness = SyntheticIntakeHarness(provider=MissingProvider())
    with pytest.raises(SyntheticIntakeError):
        harness.synchronize()
    assert harness.checkpoint is None and harness.list_candidates() == ()


def test_human_decisions_and_synthetic_commercial_projection() -> None:
    harness = SyntheticIntakeHarness()
    candidates = harness.synchronize()
    decisions = ("accept", "reject", "request_correction")
    for index, candidate in enumerate(candidates):
        harness.decide(candidate.candidate_id, decisions[index % 3])  # type: ignore[arg-type]
    assert {item.decision for item in harness.list_candidates()} == set(decisions)
    commercial = next(
        item
        for item in harness.list_candidates()
        if item.proposed_category == "commercial_contact_or_rfq" and item.decision == "accept"
    )
    projection = harness.projection_for(commercial.candidate_id)
    assert projection is not None
    assert projection.channel == "synthetic" and projection.candidate_id == commercial.candidate_id
    assert "CommercialIntakeItem" not in type(projection).__name__


def test_synthetic_decision_requires_active_canonical_synthetic_membership() -> None:
    harness = SyntheticIntakeHarness()
    candidate = harness.synchronize()[0]
    harness.membership = SyntheticMembership(active=False)
    with pytest.raises(SyntheticIntakeError, match="reviewer authority rejected"):
        harness.decide(candidate.candidate_id, "accept")
    assert harness.get_candidate(candidate.candidate_id).decision is None


def test_decision_is_idempotent_but_switching_is_a_conflict() -> None:
    harness = SyntheticIntakeHarness()
    candidate = harness.synchronize()[0]
    first = harness.decide(candidate.candidate_id, "accept")
    assert harness.decide(candidate.candidate_id, "accept") == first
    with pytest.raises(SyntheticIntakeError, match="decision conflict"):
        harness.decide(candidate.candidate_id, "reject")
    assert harness.get_candidate(candidate.candidate_id) == first


def test_disable_is_destructive_only_to_memory_and_fails_closed() -> None:
    harness = SyntheticIntakeHarness()
    harness.synchronize()
    harness.disable()
    assert harness.enabled is False and harness.checkpoint is None
    with pytest.raises(SyntheticIntakeError):
        harness.list_candidates()
    with pytest.raises(SyntheticIntakeError):
        harness.synchronize()


@pytest.mark.parametrize("environment", ["production", "staging", "", "LOCAL"])
def test_invalid_environments_fail_closed(environment: str) -> None:
    with pytest.raises(ValueError):
        create_synthetic_app(environment=environment, operator_acknowledged=True)


def test_operator_acknowledgement_is_required() -> None:
    with pytest.raises(ValueError):
        create_synthetic_app(environment="local", operator_acknowledged=False)


def test_loopback_host_origin_csrf_and_http_methods_are_cumulative() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    harness = app.state.harness
    with client_for(app) as client:
        assert client.get("/", headers={"host": HOST}).status_code == 200
        assert client.post("/synthetic/sync", headers=mutation_headers(app), follow_redirects=False).status_code == 303
        before = len(harness.list_candidates())
        cross_origin = {"host": HOST, "origin": "http://evil.invalid", "x-csrf-token": app.state.csrf_token}
        assert client.post("/synthetic/sync", headers=cross_origin).status_code == 409
        conflicting_referer = mutation_headers(app, referer="http://evil.invalid/path")
        assert client.post("/synthetic/sync", headers=conflicting_referer).status_code == 409
        assert client.post("/synthetic/sync", headers={"host": HOST, "origin": ORIGIN}).status_code == 409
        invalid_csrf = {"host": HOST, "origin": ORIGIN, "x-csrf-token": "synthetic-invalid"}
        assert client.post("/synthetic/sync", headers=invalid_csrf).status_code == 409
        query_csrf = "/synthetic/sync?csrf_token=" + app.state.csrf_token
        assert client.post(query_csrf, headers={"host": HOST, "origin": ORIGIN}).status_code == 409
        invalid_host = {"host": "evil.invalid", "origin": ORIGIN, "x-csrf-token": app.state.csrf_token}
        assert client.post("/synthetic/sync", headers=invalid_host).status_code == 400
        assert client.put("/synthetic/sync", headers=mutation_headers(app)).status_code == 405
        assert len(harness.list_candidates()) == before
    assert app.state.csrf_token is None
    assert harness.enabled is False
    assert app.state.harness is None


@pytest.mark.parametrize("peer", [("203.0.113.4", 9), ("malformed", 9)])
def test_remote_and_malformed_peers_fail_before_read_or_mutation(peer: tuple[str, int]) -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app, peer) as client:
        response = client.get(
            "/synthetic/candidates",
            headers={
                "host": HOST,
                "forwarded": "for=127.0.0.1",
                "x-forwarded-for": "127.0.0.1",
                "x-real-ip": "127.0.0.1",
            },
        )
        assert response.status_code == 403
        assert app.state.harness.checkpoint is None


def _direct_asgi_get(app: Any, *, client: tuple[str, int] | None) -> tuple[int, bytes]:
    sent: list[dict[str, Any]] = []
    request_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/synthetic/candidates",
        "raw_path": b"/synthetic/candidates",
        "query_string": b"",
        "headers": [(b"host", HOST.encode("ascii"))],
        "client": client,
        "server": ("127.0.0.1", LOCAL_PORT),
        "root_path": "",
    }
    asyncio.run(app(scope, receive, send))
    status = next(item["status"] for item in sent if item["type"] == "http.response.start")
    body = b"".join(item.get("body", b"") for item in sent if item["type"] == "http.response.body")
    return status, body


def test_absent_peer_fails_before_reading_harness_state() -> None:
    class ReadDetectingHarness(SyntheticIntakeHarness):
        def list_candidates(self):  # type: ignore[no-untyped-def]
            raise AssertionError("peer rejection must occur before state read")

    app = create_synthetic_app(environment="test", operator_acknowledged=True, harness=ReadDetectingHarness())
    status, body = _direct_asgi_get(app, client=None)
    assert status == 403
    assert b"loopback_peer_required" in body


def test_ipv6_loopback_behavior() -> None:
    ipv6_app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(ipv6_app, ("::1", 50000)) as ipv6:
        assert ipv6.get("/", headers={"host": HOST}).status_code == 200


def test_ui_escapes_active_markup_and_supplies_restrictive_csp() -> None:
    harness = SyntheticIntakeHarness()
    rendered = next(item for item in harness.synchronize() if item.fixture_id == "SYN-MSG-006")
    app = create_synthetic_app(environment="test", operator_acknowledged=True, harness=harness)
    with client_for(app) as client:
        page = client.get(f"/synthetic/candidates/{rendered.candidate_id}", headers={"host": HOST})
        assert page.headers["content-security-policy"] == CSP
        assert "synthetic-script-text Synthetic commercial contact [REDACTED_SECRET]" in page.text
        assert "<script" not in page.text and "<img" not in page.text and "innerHTML" not in page.text
        assert "http://" not in page.text and "https://" not in page.text


def test_decision_requires_post_and_valid_security_then_routes_synthetically() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        sync = client.post("/synthetic/sync", headers=mutation_headers(app), follow_redirects=False)
        assert sync.status_code == 303 and sync.headers["location"] == "/"
        candidate_id = "candidate-syn-msg-001"
        assert client.get(f"/synthetic/candidates/{candidate_id}/decision", headers={"host": HOST}).status_code == 405
        response = client.post(
            f"/synthetic/candidates/{candidate_id}/decision",
            headers=mutation_headers(app, **{"x-synthetic-decision": "accept"}),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/synthetic/candidates/candidate-syn-msg-002"
        assert app.state.harness.projection_for(candidate_id) is not None
        disabled = client.post("/synthetic/disable", headers=mutation_headers(app), follow_redirects=False)
        assert disabled.status_code == 303 and disabled.headers["location"] == "/"
        assert app.state.harness.enabled is False


def test_overview_progress_and_manifest_ordered_decision_redirects() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        initial = client.get("/", headers={"host": HOST})
        assert "Status: enabled" in initial.text and "Reviewed: 0/10" in initial.text
        sync = client.post("/synthetic/sync", headers=mutation_headers(app), follow_redirects=False)
        assert sync.status_code == 303 and sync.headers["location"] == "/"
        overview = client.get("/", headers={"host": HOST})
        assert "Reviewed: 0/10" in overview.text
        assert all(entry.fixture_id in overview.text for entry in SYNTHETIC_MANIFEST)
        assert overview.text.count("decision: pending") == 10

        decisions = ("accept", "reject", "request_correction")
        for index, entry in enumerate(SYNTHETIC_MANIFEST):
            candidate_id = f"candidate-{entry.fixture_id.lower()}"
            decision = decisions[index % len(decisions)]
            response = client.post(
                f"/synthetic/candidates/{candidate_id}/decision",
                headers=mutation_headers(app, **{"x-synthetic-decision": decision}),
                follow_redirects=False,
            )
            expected_location = (
                "/"
                if index == len(SYNTHETIC_MANIFEST) - 1
                else f"/synthetic/candidates/candidate-{SYNTHETIC_MANIFEST[index + 1].fixture_id.lower()}"
            )
            assert response.status_code == 303 and response.headers["location"] == expected_location
            progress = client.get("/", headers={"host": HOST})
            assert f"Reviewed: {index + 1}/10" in progress.text

        complete = client.get("/", headers={"host": HOST})
        assert "Reviewed: 10/10" in complete.text
        for decision in decisions:
            assert f"decision: {decision}" in complete.text
        assert "Commercial Intake boundary projection: present" in complete.text


def test_redirect_targets_ignore_browser_supplied_values() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        client.post("/synthetic/sync", headers=mutation_headers(app))
        response = client.post(
            "/synthetic/candidates/candidate-syn-msg-001/decision?next=https://evil.invalid",
            headers={"host": HOST, "origin": ORIGIN},
            data={
                "csrf_token": app.state.csrf_token,
                "decision": "accept",
                "next": "https://evil.invalid",
                "return_to": "//evil.invalid",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/synthetic/candidates/candidate-syn-msg-002"
        assert "evil.invalid" not in response.headers["location"]


def test_decided_detail_is_read_only_and_projection_is_category_and_decision_gated() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        client.post("/synthetic/sync", headers=mutation_headers(app))
        commercial_id = "candidate-syn-msg-001"
        client.post(
            f"/synthetic/candidates/{commercial_id}/decision",
            headers=mutation_headers(app, **{"x-synthetic-decision": "accept"}),
        )
        detail = client.get(f"/synthetic/candidates/{commercial_id}", headers={"host": HOST})
        assert "Back to overview" in detail.text
        assert "Decision: accept" in detail.text
        assert "Commercial Intake boundary projection" in detail.text
        assert "<button>accept</button>" not in detail.text
        assert "<button>reject</button>" not in detail.text
        assert "<button>request_correction</button>" not in detail.text

        noncommercial_id = "candidate-syn-msg-002"
        client.post(
            f"/synthetic/candidates/{noncommercial_id}/decision",
            headers=mutation_headers(app, **{"x-synthetic-decision": "accept"}),
        )
        noncommercial = client.get(f"/synthetic/candidates/{noncommercial_id}", headers={"host": HOST})
        assert "Back to overview" in noncommercial.text
        assert "Commercial Intake boundary projection" not in noncommercial.text


def test_disable_redirects_to_safe_status_page_and_all_operational_routes_fail_closed() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        client.post("/synthetic/sync", headers=mutation_headers(app))
        prior_csrf = app.state.csrf_token
        disabled = client.post("/synthetic/disable", headers=mutation_headers(app), follow_redirects=False)
        assert disabled.status_code == 303 and disabled.headers["location"] == "/"
        assert app.state.csrf_token is None

        root = client.get("/", headers={"host": HOST})
        assert root.status_code == 200
        assert BANNER in root.text and "Status: disabled" in root.text
        assert "candidate-syn-msg" not in root.text
        assert "csrf_token" not in root.text and prior_csrf not in root.text
        assert "<button" not in root.text

        rejected = [
            client.get("/synthetic/candidates", headers={"host": HOST}),
            client.get("/synthetic/candidates/candidate-syn-msg-001", headers={"host": HOST}),
            client.post("/synthetic/sync", headers={"host": HOST, "origin": ORIGIN, "x-csrf-token": prior_csrf}),
            client.post(
                "/synthetic/candidates/candidate-syn-msg-001/decision",
                headers={"host": HOST, "origin": ORIGIN, "x-csrf-token": prior_csrf},
            ),
        ]
        assert all(response.status_code == 409 for response in rejected)


def test_follow_redirects_produces_a_navigable_human_flow() -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    with client_for(app) as client:
        synced = client.post("/synthetic/sync", headers=mutation_headers(app), follow_redirects=True)
        assert synced.status_code == 200 and "Reviewed: 0/10" in synced.text
        decided = client.post(
            "/synthetic/candidates/candidate-syn-msg-001/decision",
            headers=mutation_headers(app, **{"x-synthetic-decision": "accept"}),
            follow_redirects=True,
        )
        assert decided.status_code == 200
        assert "candidate-syn-msg-002" in decided.text and "Back to overview" in decided.text
        disabled = client.post("/synthetic/disable", headers=mutation_headers(app), follow_redirects=True)
        assert disabled.status_code == 200 and "Status: disabled" in disabled.text


def test_sync_disable_and_reads_are_serialized_without_partial_publication() -> None:
    provider_entered = threading.Event()
    release_provider = threading.Event()
    disable_started = threading.Event()

    class BlockingProvider(FakeSyntheticProvider):
        def messages(self) -> tuple[SyntheticMessage, ...]:
            provider_entered.set()
            assert release_provider.wait(timeout=5)
            return super().messages()

    class SignallingHarness(SyntheticIntakeHarness):
        def disable(self) -> None:
            disable_started.set()
            super().disable()

    harness = SignallingHarness(provider=BlockingProvider())
    sync_thread = threading.Thread(target=harness.synchronize)
    disable_thread = threading.Thread(target=harness.disable)
    sync_thread.start()
    assert provider_entered.wait(timeout=5)
    disable_thread.start()
    assert disable_started.wait(timeout=5)
    release_provider.set()
    sync_thread.join(timeout=5)
    disable_thread.join(timeout=5)
    assert not sync_thread.is_alive() and not disable_thread.is_alive()
    assert harness.enabled is False and harness.checkpoint is None
    with pytest.raises(SyntheticIntakeError, match="disabled"):
        harness.list_candidates()


def test_concurrent_sync_and_decision_preserve_the_decision() -> None:
    provider_entered = threading.Event()
    release_provider = threading.Event()

    class BlockingProvider(FakeSyntheticProvider):
        def messages(self) -> tuple[SyntheticMessage, ...]:
            provider_entered.set()
            assert release_provider.wait(timeout=5)
            return super().messages()

    harness = SyntheticIntakeHarness(provider=BlockingProvider())
    results: list[object] = []
    sync_thread = threading.Thread(target=lambda: results.append(harness.synchronize()))
    decision_thread = threading.Thread(target=lambda: results.append(harness.decide("candidate-syn-msg-001", "accept")))
    sync_thread.start()
    assert provider_entered.wait(timeout=5)
    decision_thread.start()
    release_provider.set()
    sync_thread.join(timeout=5)
    decision_thread.join(timeout=5)
    assert len(results) == 2
    assert harness.get_candidate("candidate-syn-msg-001").decision == "accept"


def test_concurrent_conflicting_decisions_have_one_winner() -> None:
    harness = SyntheticIntakeHarness()
    candidate = harness.synchronize()[0]
    ready = threading.Barrier(3)
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def decide(value: str) -> None:
        ready.wait(timeout=5)
        try:
            harness.decide(candidate.candidate_id, value)  # type: ignore[arg-type]
            outcome = f"accepted:{value}"
        except SyntheticIntakeError:
            outcome = f"conflict:{value}"
        with outcomes_lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=decide, args=(value,)) for value in ("accept", "reject")]
    for thread in threads:
        thread.start()
    ready.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)
    assert len([value for value in outcomes if value.startswith("accepted:")]) == 1
    assert len([value for value in outcomes if value.startswith("conflict:")]) == 1
    assert harness.get_candidate(candidate.candidate_id).decision in {"accept", "reject"}


@pytest.mark.parametrize("environment", ["local", "test"])
def test_supported_entrypoint_uses_fixed_loopback_configuration(
    monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    calls: list[tuple[object, dict[str, object]]] = []
    monkeypatch.setenv("YARVIS_ENVIRONMENT", environment)
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setattr(sys, "argv", ["synthetic", "--acknowledge-synthetic-not-production"])
    monkeypatch.setattr(app_module.uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))
    main()
    assert len(calls) == 1
    assert calls[0][1] == {
        "host": "127.0.0.1",
        "port": LOCAL_PORT,
        "proxy_headers": False,
        "forwarded_allow_ips": "",
    }


@pytest.mark.parametrize(
    ("environment", "arguments"),
    [("production", ["--acknowledge-synthetic-not-production"]), ("local", [])],
)
def test_entrypoint_rejects_invalid_environment_or_missing_acknowledgement(
    monkeypatch: pytest.MonkeyPatch, environment: str, arguments: list[str]
) -> None:
    called = False

    def unexpected_run(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setenv("YARVIS_ENVIRONMENT", environment)
    monkeypatch.setattr(sys, "argv", ["synthetic", *arguments])
    monkeypatch.setattr(app_module.uvicorn, "run", unexpected_run)
    with pytest.raises(ValueError):
        main()
    assert called is False


def test_entrypoint_exposes_no_host_or_port_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("YARVIS_ENVIRONMENT", "local")
    monkeypatch.setattr(
        sys,
        "argv",
        ["synthetic", "--acknowledge-synthetic-not-production", "--host", "0.0.0.0"],
    )
    with pytest.raises(SystemExit):
        main()


def test_operational_failures_do_not_disclose_source_or_tokens(caplog: pytest.LogCaptureFixture) -> None:
    app = create_synthetic_app(environment="test", operator_acknowledged=True)
    csrf_token = app.state.csrf_token
    response_texts: list[str] = []
    with client_for(app) as client:
        response_texts.append(client.get("/synthetic/candidates/missing", headers={"host": HOST}).text)
        response_texts.append(
            client.post(
                "/synthetic/sync",
                headers={"host": HOST, "origin": "http://evil.invalid", "x-csrf-token": "invalid-token"},
            ).text
        )
        with client_for(app, ("203.0.113.4", 9)) as remote_client:
            response_texts.append(
                remote_client.get("/synthetic/candidates", headers={"host": HOST, "x-forwarded-for": "127.0.0.1"}).text
            )
    corpus = "\n".join(response_texts + [record.getMessage() for record in caplog.records])
    prohibited = [
        "contact@example.invalid",
        "fixture-only",
        "<script>",
        SYNTHETIC_MESSAGES[0].body,
        csrf_token,
    ]
    assert all(value and value not in corpus for value in prohibited)


def test_default_yarvis_app_has_no_synthetic_routes() -> None:
    app = create_app(Settings(environment="test"))
    paths = {getattr(route, "path", "") for route in app.routes}
    assert not any(path.startswith("/synthetic") for path in paths)


def test_source_boundary_has_fixed_bind_no_external_provider_or_unsafe_ui() -> None:
    root = Path(__file__).parents[1] / "src" / "yarvis_api"
    domain_source = (root / "synthetic_netpay_intake.py").read_text(encoding="utf-8")
    app_source = (root / "synthetic_netpay_intake_app.py").read_text(encoding="utf-8")
    ast.parse(domain_source)
    ast.parse(app_source)
    assert 'LOOPBACK_BIND = "127.0.0.1"' in app_source
    assert "host=LOOPBACK_BIND" in app_source
    assert "innerHTML" not in app_source
    forbidden = ("googleapiclient", "gmail.googleapis", "oauth2", "gmail.readonly", "requests.", "httpx.")
    assert not any(value in (domain_source + app_source).lower() for value in forbidden)

"""Loopback-only UI and API for the ADR-018 synthetic intake harness."""

from __future__ import annotations

import argparse
import html
import ipaddress
import os
import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncIterator
from urllib.parse import parse_qs, quote

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from yarvis_api.synthetic_netpay_intake import SYNTHETIC_MANIFEST, SyntheticIntakeError, SyntheticIntakeHarness

LOOPBACK_BIND = "127.0.0.1"
LOCAL_PORT = 8765
BANNER = "SYNTHETIC / NOT PRODUCTION"
CSP = "default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
ALLOWED_HOSTS = {f"127.0.0.1:{LOCAL_PORT}", f"localhost:{LOCAL_PORT}"}
ALLOWED_ORIGINS = {f"http://127.0.0.1:{LOCAL_PORT}", f"http://localhost:{LOCAL_PORT}"}


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code, "banner": BANNER}, status_code=status, headers={"Content-Security-Policy": CSP})


def _actual_peer_is_loopback(request: Request) -> bool:
    if request.client is None:
        return False
    try:
        return ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        return False


def _allowed_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    if origin is None and referer is None:
        return False
    if origin is not None and origin not in ALLOWED_ORIGINS:
        return False
    if referer is not None and not any(
        referer == allowed or referer.startswith(f"{allowed}/") for allowed in ALLOWED_ORIGINS
    ):
        return False
    return True


async def _form(request: Request) -> dict[str, str]:
    values = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    return {key: items[-1] for key, items in values.items() if items}


def _candidate_dict(candidate: object) -> dict[str, object]:
    return asdict(candidate)  # type: ignore[arg-type]


def create_synthetic_app(
    *,
    environment: str,
    operator_acknowledged: bool,
    harness: SyntheticIntakeHarness | None = None,
) -> FastAPI:
    if environment not in {"local", "test"}:
        raise ValueError("synthetic intake requires exact local or test environment")
    if not operator_acknowledged:
        raise ValueError("synthetic intake requires explicit operator acknowledgement")
    state = harness or SyntheticIntakeHarness()
    csrf_token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            state.disable()
            app.state.csrf_token = None
            app.state.harness = None

    app = FastAPI(title=BANNER, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.harness = state
    app.state.csrf_token = csrf_token

    @app.middleware("http")
    async def security_boundary(request: Request, call_next):  # type: ignore[no-untyped-def]
        if not _actual_peer_is_loopback(request):
            return _error(403, "loopback_peer_required")
        if request.headers.get("host") not in ALLOWED_HOSTS:
            return _error(400, "invalid_host")
        if request.method not in {"GET", "POST"}:
            return _error(405, "method_not_allowed")
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Synthetic-Peer-Loopback"] = "true"
        return response

    async def authorize_mutation(request: Request) -> dict[str, str]:
        if not _allowed_origin(request):
            raise SyntheticIntakeError("origin rejected")
        form = await _form(request)
        supplied = request.headers.get("x-csrf-token") or form.get("csrf_token")
        expected = app.state.csrf_token
        query_token_present = request.query_params.get("csrf_token") is not None
        if (
            query_token_present
            or not supplied
            or not isinstance(expected, str)
            or not secrets.compare_digest(supplied, expected)
        ):
            raise SyntheticIntakeError("csrf rejected")
        return form

    def page(body: str) -> HTMLResponse:
        document = (
            "<!doctype html><html><head><meta charset='utf-8'><title>"
            f"{BANNER}</title></head><body><header><strong>{BANNER}</strong></header>{body}</body></html>"
        )
        return HTMLResponse(document, headers={"Content-Security-Policy": CSP, "Cache-Control": "no-store"})

    def hidden_token() -> str:
        token = app.state.csrf_token
        if not isinstance(token, str):
            return ""
        return f"<input type='hidden' name='csrf_token' value='{html.escape(token, quote=True)}'>"

    @app.exception_handler(SyntheticIntakeError)
    async def controlled_error(_request: Request, _exc: SyntheticIntakeError) -> JSONResponse:
        return _error(409, "synthetic_operation_rejected")

    @app.get("/")
    async def home() -> HTMLResponse:
        if not state.enabled:
            return page(f"<h1>{BANNER}</h1><p>Status: disabled</p>")
        candidates = state.list_candidates()
        reviewed = sum(item.decision is not None for item in candidates)
        rows = "".join(
            "<li>"
            + (
                "<a href='/synthetic/candidates/"
                f"{html.escape(item.candidate_id, quote=True)}'>{html.escape(item.fixture_id)}</a>"
                if item.decision is None
                else html.escape(item.fixture_id)
            )
            + f" — category: {html.escape(item.proposed_category)}"
            + f" — decision: {html.escape(item.decision or 'pending')}"
            + (" — Commercial Intake boundary projection: present" if state.projection_for(item.candidate_id) else "")
            + "</li>"
            for item in candidates
        )
        return page(
            f"<h1>{BANNER}</h1><p>Status: enabled</p><p>Reviewed: {reviewed}/10</p>"
            "<p>Entirely synthetic local intake.</p>"
            f"<form method='post' action='/synthetic/sync'>{hidden_token()}"
            "<button>Sync 10 synthetic messages</button></form>"
            f"<ul>{rows}</ul><form method='post' action='/synthetic/disable'>{hidden_token()}"
            "<button>Disable</button></form>"
        )

    @app.post("/synthetic/sync")
    async def synchronize(request: Request) -> RedirectResponse:
        await authorize_mutation(request)
        state.synchronize()
        return RedirectResponse(url="/", status_code=303)

    @app.get("/synthetic/candidates")
    async def candidates() -> JSONResponse:
        items = [_candidate_dict(item) for item in state.list_candidates()]
        return JSONResponse({"banner": BANNER, "candidates": items})

    @app.get("/synthetic/candidates/{candidate_id}")
    async def candidate(candidate_id: str) -> Response:
        item = state.get_candidate(candidate_id)
        escaped_id = html.escape(item.candidate_id)
        escaped_category = html.escape(item.proposed_category)
        escaped_excerpt = html.escape(item.excerpt)
        forms = ""
        if item.decision is None:
            decision_action = html.escape(f"/synthetic/candidates/{item.candidate_id}/decision", quote=True)
            forms = "".join(
                f"<form method='post' action='{decision_action}'>"
                f"{hidden_token()}<input type='hidden' name='decision' value='{decision}'>"
                f"<button>{decision}</button></form>"
                for decision in ("accept", "reject", "request_correction")
            )
        projection = state.projection_for(candidate_id)
        projection_html = ""
        if projection is not None:
            safe_fields = "".join(
                f"<dt>{html.escape(key)}</dt><dd>{html.escape(str(value))}</dd>"
                for key, value in asdict(projection).items()
            )
            projection_html = f"<h2>Commercial Intake boundary projection</h2><dl>{safe_fields}</dl>"
        return page(
            "<p><a href='/'>Back to overview</a></p>"
            f"<h1>{escaped_id}</h1><p>Category: {escaped_category}</p>"
            f"<pre>{escaped_excerpt}</pre><p>Decision: {html.escape(item.decision or 'pending')}</p>"
            f"{projection_html}{forms}"
        )

    @app.post("/synthetic/candidates/{candidate_id}/decision")
    async def decide(candidate_id: str, request: Request) -> RedirectResponse:
        form = await authorize_mutation(request)
        decision = form.get("decision") or request.headers.get("x-synthetic-decision")
        if decision not in {"accept", "reject", "request_correction"}:
            raise SyntheticIntakeError("synthetic decision rejected")
        state.decide(candidate_id, decision)  # type: ignore[arg-type]
        candidates_by_fixture = {item.fixture_id: item for item in state.list_candidates()}
        next_pending = next(
            (
                candidates_by_fixture[entry.fixture_id]
                for entry in SYNTHETIC_MANIFEST
                if candidates_by_fixture[entry.fixture_id].decision is None
            ),
            None,
        )
        destination = (
            "/" if next_pending is None else f"/synthetic/candidates/{quote(next_pending.candidate_id, safe='')}"
        )
        return RedirectResponse(url=destination, status_code=303)

    @app.post("/synthetic/disable")
    async def disable(request: Request) -> RedirectResponse:
        await authorize_mutation(request)
        state.disable()
        app.state.csrf_token = None
        return RedirectResponse(url="/", status_code=303)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=BANNER)
    parser.add_argument("--acknowledge-synthetic-not-production", action="store_true")
    args = parser.parse_args()
    environment = os.environ.get("YARVIS_ENVIRONMENT", "")
    app = create_synthetic_app(
        environment=environment,
        operator_acknowledged=args.acknowledge_synthetic_not_production,
    )
    uvicorn.run(app, host=LOOPBACK_BIND, port=LOCAL_PORT, proxy_headers=False, forwarded_allow_ips="")


if __name__ == "__main__":
    main()

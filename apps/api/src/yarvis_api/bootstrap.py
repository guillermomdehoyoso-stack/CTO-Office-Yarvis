"""Canonical API composition root for the Yarvis process."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yarvis_api.canonical_modules import canonical_modules
from yarvis_api.config import Settings, get_settings
from yarvis_api.module_registry import ApplicationModule, ModuleRegistry, build_module_registry


@dataclass(slots=True)
class ApplicationState:
    """Application-scoped technical composition state.

    This state deliberately contains only bootstrap-owned technical information.
    It is not a service locator and must not hold domain state or infrastructure
    implementations.
    """

    settings: Settings
    module_registry: ModuleRegistry
    lifecycle_active: bool = False


@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own deterministic API startup and shutdown boundaries without resources yet."""

    state: ApplicationState = app.state.yarvis
    state.lifecycle_active = True
    try:
        yield
    finally:
        state.lifecycle_active = False


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """Register currently required technical middleware at the composition root."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Reserve the explicit handler boundary; typed error handling belongs to F-012."""


def register_routes(app: FastAPI, module_registry: ModuleRegistry) -> None:
    """Register technical routes and the retained incremental interface baseline."""
    from yarvis_api.api.routes import (
        cases,
        checklists,
        data_intake,
        evidence,
        intake,
        mission_control,
        netpay,
        observations,
        operational_policies,
        organizations,
        people,
        recovery_queue,
    )

    @app.get("/health", tags=["technical"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "yarvis-api"}

    app.include_router(organizations.router)
    app.include_router(people.router)
    app.include_router(cases.router)
    app.include_router(intake.router)
    app.include_router(evidence.router)
    app.include_router(checklists.router)
    app.include_router(data_intake.router)
    app.include_router(mission_control.router)
    app.include_router(netpay.router)
    app.include_router(observations.router)
    app.include_router(operational_policies.router)
    app.include_router(recovery_queue.router)
    for module in module_registry.modules:
        if module.register_routes is not None:
            module.register_routes(app)


def create_app(
    settings: Settings | None = None,
    modules: Iterable[ApplicationModule] | None = None,
) -> FastAPI:
    """Create one isolated FastAPI application from validated typed settings."""

    composed_settings = settings if settings is not None else get_settings()
    module_registry = build_module_registry(canonical_modules() if modules is None else modules)
    documentation_enabled = composed_settings.api_docs_enabled
    app = FastAPI(
        title=composed_settings.app_name,
        version=composed_settings.app_version,
        debug=composed_settings.debug,
        docs_url="/docs" if documentation_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if documentation_enabled else None,
        lifespan=application_lifespan,
    )
    app.state.yarvis = ApplicationState(settings=composed_settings, module_registry=module_registry)
    register_middleware(app, composed_settings)
    register_exception_handlers(app)
    register_routes(app, module_registry)
    return app

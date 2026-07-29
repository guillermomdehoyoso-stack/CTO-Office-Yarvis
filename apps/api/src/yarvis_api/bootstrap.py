"""Canonical API composition root for the Yarvis process."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yarvis_api.api.authentication import DeterministicAuthenticationProvider
from yarvis_api.api.errors import application_error_handler
from yarvis_api.application.errors import ApplicationError
from yarvis_api.application.ports import AuthenticationPort
from yarvis_api.canonical_contracts import canonical_contracts
from yarvis_api.canonical_modules import canonical_modules
from yarvis_api.config import Settings, get_settings
from yarvis_api.contract_registry import ContractDefinition, ContractRegistry, build_contract_registry
from yarvis_api.dispatch import Dispatcher, HandlerDefinition, HandlerRegistry, build_handler_registry
from yarvis_api.module_registry import ApplicationModule, ModuleRegistry, build_module_registry
from yarvis_api.modules.deterministic_inbound import DeterministicInboundInboxAdapter
from yarvis_api.persistence import PersistenceRuntime, build_persistence_runtime
from yarvis_api.services.inbound_intake import InboundIntakeQueryService, InboundIntakeService
from yarvis_api.services.operational_context import IntakeOperationalContextAssociationService, IntakeOperationalContextQueryService
from yarvis_api.services.mission_inbox import MissionInboxProjectionService, MissionInboxQueryService
from yarvis_api.services.mission_work import MissionWorkQueryService, MissionWorkService
from yarvis_api.services.process import ProcessDefinitionQueryService, ProcessDefinitionService, ProcessRuntimeQueryService, ProcessRuntimeService
from yarvis_api.services.process_work_association import ProcessMissionWorkTimelineProjector, ProcessWorkAssociationQueryService, ProcessWorkAssociationService
from yarvis_api.services.operational_economics import OperationalEconomicsQueryService, OperationalEconomicsService
from yarvis_api.services.workspace.io import resolve_workspace_repository_root
from yarvis_api.services.workspace.platform import WorkspacePlatform


@dataclass(slots=True)
class ApplicationState:
    """Application-scoped technical composition state.

    This state deliberately contains only bootstrap-owned technical information.
    It is not a service locator and must not hold domain state or infrastructure
    implementations.
    """

    settings: Settings
    module_registry: ModuleRegistry
    contract_registry: ContractRegistry
    handler_registry: HandlerRegistry
    dispatcher: Dispatcher
    workspace_platform: WorkspacePlatform
    authentication: AuthenticationPort
    deterministic_inbound_adapter: DeterministicInboundInboxAdapter
    inbound_intake_service: InboundIntakeService
    inbound_intake_query_service: InboundIntakeQueryService
    intake_operational_context_association_service: IntakeOperationalContextAssociationService
    intake_operational_context_query_service: IntakeOperationalContextQueryService
    mission_inbox_projection_service: MissionInboxProjectionService
    mission_inbox_query_service: MissionInboxQueryService
    mission_work_service: MissionWorkService
    mission_work_query_service: MissionWorkQueryService
    process_definition_service: ProcessDefinitionService
    process_definition_query_service: ProcessDefinitionQueryService
    process_runtime_service: ProcessRuntimeService
    process_runtime_query_service: ProcessRuntimeQueryService
    process_work_association_service: ProcessWorkAssociationService
    process_work_association_query_service: ProcessWorkAssociationQueryService
    process_mission_work_timeline_projector: ProcessMissionWorkTimelineProjector
    operational_economics_service: OperationalEconomicsService
    operational_economics_query_service: OperationalEconomicsQueryService
    persistence: PersistenceRuntime
    persistence_owner_token: object
    lifecycle_active: bool = False


@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own deterministic API startup and shutdown boundaries without resources yet."""

    state: ApplicationState = app.state.yarvis
    state.lifecycle_active = True
    try:
        yield
    finally:
        state.persistence.dispose(state.persistence_owner_token)
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
    """Register central application-layer error translation."""

    app.add_exception_handler(ApplicationError, application_error_handler)


def register_routes(app: FastAPI, module_registry: ModuleRegistry) -> None:
    """Register technical routes and the retained incremental interface baseline."""
    from yarvis_api.api.routes import (
        cases,
        checklists,
        data_intake,
        evidence,
        intake,
        mission_control,
        mission_inbox,
        mission_work,
        netpay,
        observations,
        operational_policies,
        operational_economics,
        organizations,
        people,
        process,
        process_runtime,
        recovery_queue,
        workspace_api,
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
    app.include_router(mission_inbox.router)
    app.include_router(mission_work.router)
    app.include_router(process.router)
    app.include_router(process_runtime.router)
    app.include_router(netpay.router)
    app.include_router(observations.router)
    app.include_router(operational_policies.router)
    app.include_router(operational_economics.router)
    app.include_router(recovery_queue.router)
    app.include_router(workspace_api.router)
    for module in module_registry.modules:
        if module.register_routes is not None:
            module.register_routes(app)


def create_app(
    settings: Settings | None = None,
    modules: Iterable[ApplicationModule] | None = None,
    contracts: Iterable[ContractDefinition] | None = None,
    handlers: Iterable[HandlerDefinition] | None = None,
    persistence: PersistenceRuntime | None = None,
) -> FastAPI:
    """Create one isolated FastAPI application from validated typed settings."""

    composed_settings = settings if settings is not None else get_settings()
    authentication = DeterministicAuthenticationProvider(composed_settings)
    workspace_root = resolve_workspace_repository_root(composed_settings.workspace_repository_root, Path(__file__).resolve())
    module_registry = build_module_registry(canonical_modules() if modules is None else modules)
    contract_registry = build_contract_registry(
        module_registry,
        canonical_contracts() if contracts is None else contracts,
    )
    persistence_runtime = persistence if persistence is not None else build_persistence_runtime(composed_settings)
    if not persistence_runtime.is_compatible_with(composed_settings):
        raise ValueError("persistence runtime is incompatible with application settings")
    handler_registry = build_handler_registry(
        module_registry,
        contract_registry,
        () if handlers is None else handlers,
    )
    dispatcher = Dispatcher(contract_registry, handler_registry, persistence_runtime)
    deterministic_inbound_adapter = DeterministicInboundInboxAdapter()
    inbound_intake_service = InboundIntakeService(persistence_runtime)
    inbound_intake_query_service = InboundIntakeQueryService(inbound_intake_service)
    intake_operational_context_association_service = IntakeOperationalContextAssociationService(persistence_runtime)
    intake_operational_context_query_service = IntakeOperationalContextQueryService()
    mission_inbox_projection_service = MissionInboxProjectionService(persistence_runtime)
    mission_inbox_query_service = MissionInboxQueryService()
    mission_work_service = MissionWorkService(persistence_runtime)
    mission_work_query_service = MissionWorkQueryService()
    process_definition_service = ProcessDefinitionService(persistence_runtime)
    process_definition_query_service = ProcessDefinitionQueryService()
    process_runtime_service = ProcessRuntimeService(persistence_runtime)
    process_runtime_query_service = ProcessRuntimeQueryService()
    process_work_association_service = ProcessWorkAssociationService(persistence_runtime)
    process_work_association_query_service = ProcessWorkAssociationQueryService()
    process_mission_work_timeline_projector = ProcessMissionWorkTimelineProjector(persistence_runtime)
    operational_economics_service = OperationalEconomicsService(persistence_runtime)
    operational_economics_query_service = OperationalEconomicsQueryService()
    workspace_platform = WorkspacePlatform(workspace_root)
    persistence_owner_token = object()
    persistence_runtime.transfer_ownership(persistence_owner_token)
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
    app.state.yarvis = ApplicationState(
        settings=composed_settings,
        module_registry=module_registry,
        contract_registry=contract_registry,
        handler_registry=handler_registry,
        dispatcher=dispatcher,
        workspace_platform=workspace_platform,
        authentication=authentication,
        deterministic_inbound_adapter=deterministic_inbound_adapter,
        inbound_intake_service=inbound_intake_service,
        inbound_intake_query_service=inbound_intake_query_service,
        intake_operational_context_association_service=intake_operational_context_association_service,
        intake_operational_context_query_service=intake_operational_context_query_service,
        mission_inbox_projection_service=mission_inbox_projection_service,
        mission_inbox_query_service=mission_inbox_query_service,
        mission_work_service=mission_work_service,
        mission_work_query_service=mission_work_query_service,
        process_definition_service=process_definition_service,
        process_definition_query_service=process_definition_query_service,
        process_runtime_service=process_runtime_service,
        process_runtime_query_service=process_runtime_query_service,
        process_work_association_service=process_work_association_service,
        process_work_association_query_service=process_work_association_query_service,
        process_mission_work_timeline_projector=process_mission_work_timeline_projector,
        operational_economics_service=operational_economics_service,
        operational_economics_query_service=operational_economics_query_service,
        persistence=persistence_runtime,
        persistence_owner_token=persistence_owner_token,
    )
    register_middleware(app, composed_settings)
    register_exception_handlers(app)
    register_routes(app, module_registry)
    return app

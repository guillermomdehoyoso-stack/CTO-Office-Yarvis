import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from yarvis_api.bootstrap import create_app
from yarvis_api.config import Settings
from yarvis_api.module_registry import (
    ApplicationModule,
    DuplicateModuleError,
    InvalidModuleDefinitionError,
    MissingModuleDependencyError,
    ModuleDependencyCycleError,
    ModuleRegistry,
    RegistrySealedError,
    build_module_registry,
)


def module(module_id: str, dependencies: tuple[str, ...] = ()) -> ApplicationModule:
    return ApplicationModule(module_id=module_id, display_name=module_id.title(), dependencies=dependencies)


def test_empty_registry_is_valid_and_sealed() -> None:
    registry = build_module_registry()

    assert registry.is_sealed is True
    assert registry.modules == ()


def test_registry_registers_and_retrieves_modules_in_stable_order() -> None:
    registry = ModuleRegistry()
    first = module("core.first")
    second = module("core.second")
    registry.register_many((first, second))
    registry.seal()

    assert registry.contains("core.first") is True
    assert registry.get("core.first") is first
    assert [registered.module_id for registered in registry.modules] == ["core.first", "core.second"]


def test_dependency_order_precedes_dependents_and_preserves_independent_order() -> None:
    registry = build_module_registry(
        (
            module("core.independent"),
            module("core.dependent", ("core.base",)),
            module("core.base"),
            module("core.another-independent"),
        )
    )

    assert [registered.module_id for registered in registry.modules] == [
        "core.independent",
        "core.base",
        "core.dependent",
        "core.another-independent",
    ]


def test_invalid_duplicate_missing_and_cyclic_declarations_fail_safely() -> None:
    with pytest.raises(InvalidModuleDefinitionError):
        module(" ")

    duplicate_registry = ModuleRegistry()
    duplicate_registry.register(module("core.duplicate"))
    with pytest.raises(DuplicateModuleError):
        duplicate_registry.register(module("core.duplicate"))

    with pytest.raises(MissingModuleDependencyError):
        build_module_registry((module("core.missing", ("core.absent",)),))

    with pytest.raises(ModuleDependencyCycleError):
        build_module_registry(
            (
                module("core.first", ("core.second",)),
                module("core.second", ("core.first",)),
            )
        )


def test_sealed_registry_rejects_mutation() -> None:
    registry = build_module_registry((module("core.sealed"),))

    with pytest.raises(RegistrySealedError):
        registry.register(module("core.late"))


def test_applications_receive_isolated_registries_and_register_route_hooks_once() -> None:
    calls: list[str] = []

    def register_test_route(app: FastAPI) -> None:
        calls.append("core.test-route")

        @app.get("/_test/module")
        def test_module_route() -> dict[str, str]:
            return {"module": "core.test-route"}

    test_module = ApplicationModule(
        module_id="core.test-route",
        display_name="Test Route",
        register_routes=register_test_route,
    )
    first = create_app(Settings(environment="test"), modules=(test_module,))
    second = create_app(Settings(environment="test"))

    assert first.state.yarvis.module_registry is not second.state.yarvis.module_registry
    assert [module.module_id for module in first.state.yarvis.module_registry.modules] == ["core.test-route"]
    assert second.state.yarvis.module_registry.modules == ()
    assert calls == ["core.test-route"]
    with TestClient(first) as client:
        assert client.get("/_test/module").json() == {"module": "core.test-route"}
        assert client.get("/health").json() == {"status": "ok", "service": "yarvis-api"}

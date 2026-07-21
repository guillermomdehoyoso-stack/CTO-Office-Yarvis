"""Explicit, deterministic technical registry for Yarvis application modules."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from fastapi import FastAPI

ModuleRouteHook = Callable[[FastAPI], None]
MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:[.-][a-z0-9_]+)*$")


class ModuleRegistryError(ValueError):
    """Base error for deterministic, safe module-registry failures."""


class InvalidModuleDefinitionError(ModuleRegistryError):
    """A module declaration is incomplete or violates the identifier convention."""


class DuplicateModuleError(ModuleRegistryError):
    """A registry already contains the supplied stable module identifier."""


class MissingModuleDependencyError(ModuleRegistryError):
    """A declared dependency is absent from the same registry."""


class ModuleDependencyCycleError(ModuleRegistryError):
    """Declared dependencies cannot be resolved into a deterministic order."""


class RegistrySealedError(ModuleRegistryError):
    """A sealed registry cannot accept further registrations."""


@dataclass(frozen=True, slots=True)
class ApplicationModule:
    """Minimal technical declaration for an application module.

    Module declarations describe composition only. They do not contain domain
    authority, service instances, or self-registration behavior.
    """

    module_id: str
    display_name: str
    dependencies: tuple[str, ...] = ()
    register_routes: ModuleRouteHook | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not MODULE_ID_PATTERN.fullmatch(self.module_id):
            raise InvalidModuleDefinitionError(f"invalid module identifier: {self.module_id!r}")
        if not self.display_name.strip():
            raise InvalidModuleDefinitionError(f"module {self.module_id!r} requires a display name")
        normalized_dependencies = tuple(self.dependencies)
        if len(set(normalized_dependencies)) != len(normalized_dependencies):
            raise InvalidModuleDefinitionError(f"module {self.module_id!r} repeats a dependency")
        for dependency in normalized_dependencies:
            if not MODULE_ID_PATTERN.fullmatch(dependency):
                raise InvalidModuleDefinitionError(
                    f"module {self.module_id!r} declares an invalid dependency: {dependency!r}"
                )
        object.__setattr__(self, "dependencies", normalized_dependencies)


class ModuleRegistry:
    """Per-application registry with explicit registration and sealed ordering."""

    def __init__(self) -> None:
        self._modules: dict[str, ApplicationModule] = {}
        self._ordered_modules: tuple[ApplicationModule, ...] | None = None

    @property
    def is_sealed(self) -> bool:
        return self._ordered_modules is not None

    @property
    def modules(self) -> tuple[ApplicationModule, ...]:
        if self._ordered_modules is not None:
            return self._ordered_modules
        return tuple(self._modules.values())

    def register(self, module: ApplicationModule) -> None:
        if self.is_sealed:
            raise RegistrySealedError("module registry is sealed")
        if module.module_id in self._modules:
            raise DuplicateModuleError(f"duplicate module identifier: {module.module_id}")
        self._modules[module.module_id] = module

    def register_many(self, modules: Iterable[ApplicationModule]) -> None:
        for module in modules:
            self.register(module)

    def get(self, module_id: str) -> ApplicationModule | None:
        return self._modules.get(module_id)

    def contains(self, module_id: str) -> bool:
        return module_id in self._modules

    def seal(self) -> None:
        if self.is_sealed:
            return
        self._validate_dependencies()
        self._ordered_modules = self._resolve_order()

    def _validate_dependencies(self) -> None:
        for module in self._modules.values():
            for dependency in module.dependencies:
                if dependency not in self._modules:
                    raise MissingModuleDependencyError(
                        f"module {module.module_id!r} depends on missing module {dependency!r}"
                    )

    def _resolve_order(self) -> tuple[ApplicationModule, ...]:
        pending = dict(self._modules)
        resolved_ids: set[str] = set()
        ordered: list[ApplicationModule] = []

        while pending:
            next_module = next(
                (
                    module
                    for module in pending.values()
                    if all(dependency in resolved_ids for dependency in module.dependencies)
                ),
                None,
            )
            if next_module is None:
                cycle_ids = ", ".join(pending)
                raise ModuleDependencyCycleError(f"module dependency cycle: {cycle_ids}")
            ordered.append(next_module)
            resolved_ids.add(next_module.module_id)
            del pending[next_module.module_id]

        return tuple(ordered)


def build_module_registry(modules: Iterable[ApplicationModule] = ()) -> ModuleRegistry:
    """Build and seal one explicit registry for a single application instance."""

    registry = ModuleRegistry()
    registry.register_many(modules)
    registry.seal()
    return registry

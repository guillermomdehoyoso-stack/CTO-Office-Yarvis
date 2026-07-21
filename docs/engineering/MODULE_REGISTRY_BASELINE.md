# YARVIS
# Module Registry Baseline

## Status: Implemented Engineering Baseline - F-005 Module Registry

## 1. Work-Package Identity and Purpose

F-005 establishes the one explicit, deterministic technical registry through which an API application instance receives declared Yarvis application modules. It is a composition mechanism, not a domain authority, plugin system, service locator, command bus, or discovery framework.

## 2. Registry Authority and Module Contract

`apps/api/src/yarvis_api/module_registry.py` is the single registry authority. `ApplicationModule` is an immutable declaration containing only a stable `module_id`, a nonblank `display_name`, immutable declared dependencies, and an optional composition-time `register_routes` hook. Versions, capability metadata, enablement, lifecycle hooks, feature flags, and tenant-specific module sets are deferred.

Module identifiers use lower-case dotted or hyphenated segments: `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`. They are semantic deployment-stable identifiers, not import paths, display names, or runtime state.

## 3. Registration, Ordering, and Validation

Modules are supplied explicitly to `build_module_registry()` or the composition root; modules never self-register. `ModuleRegistry` registers declarations in supplied order, validates duplicate identifiers and missing dependencies, then seals into a deterministic topological order. Dependencies always precede dependents; otherwise independent modules preserve supplied registration order.

The registry reports typed, safe errors for invalid declarations, duplicates, missing dependencies, dependency cycles, and mutation after sealing. An empty sealed registry is valid. Sealing produces an immutable module ordering; it does not execute module behavior.

No package scanning, filesystem scanning, `importlib` discovery, entry points, decorators, metaclasses, import side effects, process-global registry, or untyped dictionary is used.

## 4. Bootstrap and Application-State Integration

`create_app(settings=None, modules=None)` constructs one new sealed registry for each FastAPI application instance. The typed registry is stored only in that instance's `ApplicationState` at `app.state.yarvis.module_registry`; it is not a generic container and contains no services or domain state.

After the retained interface routes and neutral `/health` route are registered, each supplied module's optional `register_routes` hook runs once in resolved order. The hook is limited to application composition. No production business module is introduced by F-005; tests define minimal in-memory module declarations.

## 5. Domain Independence, Diagnostics, and Deferred Capabilities

Domain-model code may not import FastAPI, bootstrap, application state, environment variables, or the registry. Registry diagnostics expose only module ID, display name, and resolved order in memory; no HTTP module-list endpoint exists. Module route handlers, configuration, and dependencies are not exposed as diagnostics.

F-005 does not initialize PostgreSQL, run migrations, start workers or schedulers, create a dependency-injection framework, dispatch contracts, add dynamic enablement, implement plugin loading, or introduce future business routes.

## 6. Files, Validation, Findings, and F-006 Readiness

F-005 adds `module_registry.py`, focused registry tests, and architecture conformance for no discovery and domain independence. Bootstrap now composes an isolated sealed registry. `APPLICATION_BOOTSTRAP_BASELINE.md` and `REPOSITORY_STRUCTURE.md` record the changed facts.

Validation covers empty and populated registries, deterministic dependency order, duplicate/missing/cycle/invalid errors, sealing, application isolation, one-time test route hooks, neutral health preservation, no connection attempt, quality checks, complete backend tests, Docker, and HTTP smoke testing.

Findings: none. F-006 Contract Registry may begin after this baseline is committed; no contract registry, binding, or dispatch behavior is implemented here.

## 7. Closing Statement

F-005 gives the modular monolith one explicit composition vocabulary while preserving its central rule: technical composition may be shared, but modules do not acquire or exchange domain authority through the registry.

"""F-013 deterministic conformance controls for the active Foundation."""

from __future__ import annotations

import ast
from pathlib import Path

from yarvis_api.canonical_contracts import canonical_contracts
from yarvis_api.canonical_modules import canonical_modules
from yarvis_api.contract_registry import (
    ContractLifecycle,
    ContractOperationalStatus,
    build_contract_registry,
)
from yarvis_api.module_registry import build_module_registry
from yarvis_api.observability.tracing import TRACE_REFERENCE_TYPES

API_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = API_ROOT / "src" / "yarvis_api"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports.update(node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom))
    return imports


def test_canonical_contract_owners_are_registered_and_registry_is_sealed() -> None:
    modules = canonical_modules()
    contracts = canonical_contracts()
    module_ids = {module.module_id for module in modules}
    registry = build_contract_registry(build_module_registry(modules), contracts)

    assert registry.is_sealed is True
    assert all(contract.owner_module_id in module_ids for contract in contracts)
    assert all(isinstance(contract.lifecycle, ContractLifecycle) for contract in contracts)
    assert all(isinstance(contract.operational_status, ContractOperationalStatus) for contract in contracts)


def test_observability_remains_a_technical_dependency_without_interface_or_dispatch_imports() -> None:
    forbidden_prefixes = (
        "fastapi",
        "yarvis_api.api",
        "yarvis_api.bootstrap",
        "yarvis_api.dispatch",
        "yarvis_api.services",
    )

    for path in (SOURCE_ROOT / "observability").glob("*.py"):
        imports = _imports(path)
        assert all(not module.startswith(forbidden_prefixes) for module in imports), path.name


def test_intake_trace_integration_remains_synchronous_without_later_runtime_dependencies() -> None:
    intake_path = SOURCE_ROOT / "services" / "inbound_intake.py"
    source = intake_path.read_text(encoding="utf-8")
    imports = _imports(intake_path)

    assert "TraceRecorder" in source
    assert "trace_recorder.begin" in source
    assert "trace.succeed" in source
    assert all(
        not module.startswith(("asyncio", "celery", "rq", "yarvis_api.dispatch"))
        for module in imports
    )
    assert all(token not in source for token in ("Thread(", "Queue(", "create_task("))


def test_trace_reference_vocabulary_has_one_authoritative_technical_definition() -> None:
    trace_reference_definitions = [
        path
        for path in SOURCE_ROOT.rglob("*.py")
        if "class TraceReference" in path.read_text(encoding="utf-8")
    ]

    assert trace_reference_definitions == [SOURCE_ROOT / "observability" / "tracing.py"]
    assert TRACE_REFERENCE_TYPES == {
        "unknown",
        "intake_item",
        "external_source",
        "domain_event",
        "event",
        "result",
        "retry",
        "compensation",
    }


def test_f013_conformance_suite_is_covered_by_the_declared_quality_authorities() -> None:
    metadata = (API_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    required_entries = (
        "tests/architecture/**/*.py",
        '"tests/architecture"',
    )

    assert all(entry in metadata for entry in required_entries)

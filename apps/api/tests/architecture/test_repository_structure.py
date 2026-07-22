import ast
from pathlib import Path

from fastapi import FastAPI

from yarvis_api.main import app

API_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_python_package_root_exists() -> None:
    assert (API_ROOT / "src" / "yarvis_api" / "__init__.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "main.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "bootstrap.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "module_registry.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "canonical_modules.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "contract_registry.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "canonical_contracts.py").is_file()


def test_package_metadata_declares_python_312() -> None:
    metadata = (API_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.12,<3.13"' in metadata


def test_runtime_dependency_and_quality_authorities_are_declared() -> None:
    runtime_dependencies = (API_ROOT / "requirements.txt").read_text(encoding="utf-8")
    development_dependencies = (API_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    metadata = (API_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "fastapi==" in runtime_dependencies
    assert "uvicorn[standard]==" in runtime_dependencies
    assert "ruff==" in development_dependencies
    assert "pyright==" in development_dependencies
    assert "[tool.ruff]" in metadata
    assert "[tool.pyright]" in metadata


def test_canonical_fastapi_application_remains_importable() -> None:
    assert isinstance(app, FastAPI)


def test_domain_models_do_not_read_process_environment_directly() -> None:
    domain_files = (API_ROOT / "src" / "yarvis_api" / "models").glob("*.py")
    for path in domain_files:
        content = path.read_text(encoding="utf-8")
        assert "os.getenv" not in content
        assert "os.environ" not in content
        assert "app.state" not in content
        assert "yarvis_api.module_registry" not in content


def test_domain_models_do_not_depend_on_fastapi_or_bootstrap() -> None:
    for path in (API_ROOT / "src" / "yarvis_api" / "models").glob("*.py"):
        imports = {
            alias.name
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.ImportFrom)
        )
        assert all(not module.startswith("fastapi") for module in imports)
        assert all(not module.startswith("yarvis_api.bootstrap") for module in imports)


def test_main_is_a_thin_asgi_adapter_with_one_canonical_factory() -> None:
    main_tree = ast.parse((API_ROOT / "src" / "yarvis_api" / "main.py").read_text(encoding="utf-8"))
    assignments = [node for node in main_tree.body if isinstance(node, ast.Assign)]

    assert len(assignments) == 1
    assert isinstance(assignments[0].value, ast.Call)
    assert isinstance(assignments[0].value.func, ast.Name)
    assert assignments[0].value.func.id == "create_app"


def test_registry_uses_no_discovery_or_global_registration_mechanism() -> None:
    registry_tree = ast.parse((API_ROOT / "src" / "yarvis_api" / "module_registry.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(registry_tree) if isinstance(node, ast.Import) for alias in node.names}
    imports.update(node.module or "" for node in ast.walk(registry_tree) if isinstance(node, ast.ImportFrom))

    assert all(not module.startswith("importlib") for module in imports)
    assert all(not module.startswith("pkgutil") for module in imports)
    assert all(not module.startswith("pathlib") for module in imports)


def test_canonical_module_baseline_remains_an_explicit_technical_declaration() -> None:
    baseline_tree = ast.parse((API_ROOT / "src" / "yarvis_api" / "canonical_modules.py").read_text(encoding="utf-8"))
    imports = {node.module or "" for node in ast.walk(baseline_tree) if isinstance(node, ast.ImportFrom)}

    assert imports == {"yarvis_api.module_registry"}


def test_contract_registry_uses_no_discovery_or_global_registration_mechanism() -> None:
    registry_tree = ast.parse((API_ROOT / "src" / "yarvis_api" / "contract_registry.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(registry_tree) if isinstance(node, ast.Import) for alias in node.names}
    imports.update(node.module or "" for node in ast.walk(registry_tree) if isinstance(node, ast.ImportFrom))

    assert all(not module.startswith("importlib") for module in imports)
    assert all(not module.startswith("pkgutil") for module in imports)
    assert all(not module.startswith("pathlib") for module in imports)
    assert all(not module.startswith("fastapi") for module in imports)


def test_canonical_contract_projection_remains_explicit_technical_metadata() -> None:
    projection_path = API_ROOT / "src" / "yarvis_api" / "canonical_contracts.py"
    projection_tree = ast.parse(projection_path.read_text(encoding="utf-8"))
    imports = {node.module or "" for node in ast.walk(projection_tree) if isinstance(node, ast.ImportFrom)}

    assert imports == {"yarvis_api.contract_registry"}

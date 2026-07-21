from pathlib import Path

from fastapi import FastAPI

from yarvis_api.main import app

API_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_python_package_root_exists() -> None:
    assert (API_ROOT / "src" / "yarvis_api" / "__init__.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "main.py").is_file()


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

from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_python_package_root_exists() -> None:
    assert (API_ROOT / "src" / "yarvis_api" / "__init__.py").is_file()
    assert (API_ROOT / "src" / "yarvis_api" / "main.py").is_file()


def test_package_metadata_declares_python_312() -> None:
    metadata = (API_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.12,<3.13"' in metadata

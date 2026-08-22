from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_digitalocean_runtime_package_keeps_database_credentials_separate() -> None:
    runtime_spec = (REPOSITORY_ROOT / "deploy" / "digitalocean" / "app.yaml").read_text(encoding="utf-8")
    migration_spec = (REPOSITORY_ROOT / "deploy" / "digitalocean" / "migration-job.yaml").read_text(
        encoding="utf-8"
    )

    assert "name: yarvis-pilot" in runtime_spec
    assert "http_port: 8080" in runtime_spec
    assert "http_path: /health" in runtime_spec
    assert "YARVIS_DATABASE_URL" in runtime_spec
    assert "YARVIS_MIGRATOR_DATABASE_URL" not in runtime_spec
    assert "YARVIS_MIGRATOR_DATABASE_URL" in migration_spec
    assert "YARVIS_DATABASE_URL" not in migration_spec
    assert "PRE_DEPLOY" not in runtime_spec
    assert "kind: PRE_DEPLOY" in migration_spec


def test_digitalocean_package_has_no_cloud_storage_or_cloud_run_reference() -> None:
    package = REPOSITORY_ROOT / "deploy" / "digitalocean"
    package_text = "\n".join(path.read_text(encoding="utf-8") for path in package.iterdir() if path.is_file())

    assert "cloud-storage" not in package_text.lower()
    assert "cloud run" not in package_text.lower()
    assert "__REQUIRES_EXACT_APP_PLATFORM_CALLBACK__" in package_text

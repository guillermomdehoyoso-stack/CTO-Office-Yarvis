from __future__ import annotations

from pathlib import Path

from yarvis_api.config import Settings


def _repository_root() -> Path:
    candidates = (*Path(__file__).resolve().parents, Path("/workspace-repository"))
    for candidate in candidates:
        if (candidate / "deploy" / "digitalocean").is_dir():
            return candidate
    raise RuntimeError("repository root is unavailable")


REPOSITORY_ROOT = _repository_root()


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


def test_founder_enrollment_runner_is_separate_and_uses_only_its_administrative_credential() -> None:
    runner_spec = (REPOSITORY_ROOT / "deploy" / "digitalocean" / "founder-enrollment-job.yaml").read_text(
        encoding="utf-8"
    )

    assert "name: yarvis-pilot-founder-enroll" in runner_spec
    assert "name: yarvis-founder-enroll" in runner_spec
    assert "deploy_on_push: false" in runner_spec
    assert "python -m yarvis_api.founder_bootstrap_cli enroll --authorization-file" in runner_spec
    assert "YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL" in runner_spec
    assert "YARVIS_FOUNDER_ENROLLMENT_AUTHORIZATION" in runner_spec
    assert "YARVIS_DATABASE_URL" not in runner_spec
    assert "YARVIS_MIGRATOR_DATABASE_URL" not in runner_spec
    assert "YARVIS_FOUNDER_BOOTSTRAP_ENABLED" in runner_spec


def test_founder_handoff_selector_is_a_separate_read_only_one_shot_job() -> None:
    selector_spec = (
        REPOSITORY_ROOT / "deploy" / "digitalocean" / "founder-handoff-selector-job.yaml"
    ).read_text(encoding="utf-8")
    runtime_spec = (REPOSITORY_ROOT / "deploy" / "digitalocean" / "app.yaml").read_text(encoding="utf-8")

    command = "python -m yarvis_api.founder_bootstrap_cli select-handoff"

    assert "name: yarvis-pilot-founder-select-handoff" in selector_spec
    assert "name: yarvis-founder-select-handoff" in selector_spec
    assert "deploy_on_push: false" in selector_spec
    assert f"run_command: {command}" in selector_spec
    assert selector_spec.count(command) == 1
    assert "YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL" in selector_spec
    for forbidden in (
        "YARVIS_DATABASE_URL",
        "YARVIS_MIGRATOR_DATABASE_URL",
        "YARVIS_FOUNDER_ENROLLMENT_AUTHORIZATION",
        "YARVIS_FOUNDER_BOOTSTRAP_ENABLED",
        "YARVIS_FOUNDER_BOOTSTRAP_PUBLIC_KEY",
        "YARVIS_FOUNDER_BOOTSTRAP_KEY_ID",
        "--authorization-file",
        "founder_bootstrap_cli enroll",
    ):
        assert forbidden not in selector_spec
    assert "select-handoff" not in runtime_spec
    assert "YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL" not in runtime_spec
    assert "__REQUIRES_FOUNDER_BOOTSTRAP_DATABASE_URL__" in selector_spec
    assert "@netpay.com.mx" not in selector_spec
    assert "BEGIN " not in selector_spec


def test_founder_runner_administrative_database_variable_is_accepted_without_runtime_alias() -> None:
    settings = Settings.model_validate(
        {"YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL": "postgresql://synthetic:synthetic@db.test/yarvis"}
    )

    assert settings.database_url == "postgresql://synthetic:synthetic@db.test/yarvis"


def test_digitalocean_package_has_no_cloud_storage_or_cloud_run_reference() -> None:
    package = REPOSITORY_ROOT / "deploy" / "digitalocean"
    package_text = "\n".join(path.read_text(encoding="utf-8") for path in package.iterdir() if path.is_file())

    assert "cloud-storage" not in package_text.lower()
    assert "cloud run" not in package_text.lower()
    assert "__REQUIRES_EXACT_APP_PLATFORM_CALLBACK__" in package_text

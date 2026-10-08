"""Fail closed before D1's destructive synthetic database fixtures."""

import ast
import os
import socket
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
from alembic.config import Config

from yarvis_api.config import Settings
from yarvis_api.persistence.alembic import resolve_migration_database_url

expected = ("postgres", 5432, "/yarvis_test")
for name in (
    "DATABASE_URL",
    "YARVIS_DATABASE_URL",
    "YARVIS_FOUNDER_BOOTSTRAP_DATABASE_URL",
    "YARVIS_MIGRATOR_DATABASE_URL",
    "database_url",
):
    parsed = urlsplit(os.environ[name])
    assert (parsed.hostname, parsed.port, parsed.path) == expected, name
settings = Settings()
parsed = urlsplit(settings.database_url)
assert (parsed.hostname, parsed.port, parsed.path) == expected
assert settings.environment == "test" and settings.auth_mode == "deterministic"
assert settings.workspace_repository_root == Path("/source")
assert not any(name.endswith("_SECRET") and "DATABASE" in name for name in os.environ)
config = Config("alembic.ini")
parsed = urlsplit(resolve_migration_database_url(config.get_main_option("sqlalchemy.url")))
assert (parsed.hostname, parsed.port, parsed.path) == expected
namespace = {}
for node in ast.parse(Path("tests/conftest.py").read_text()).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in {"TEST_URL", "ADMIN_URL"}:
            namespace[node.targets[0].id] = ast.literal_eval(node.value)
assert namespace["TEST_URL"] == settings.database_url
assert urlsplit(namespace["ADMIN_URL"]).path == "/postgres"
with psycopg.connect(namespace["ADMIN_URL"]) as admin, psycopg.connect(settings.database_url, dbname="postgres") as app:
    admin_address = admin.execute("SELECT host(inet_server_addr()), inet_server_port()").fetchone()
    app_address = app.execute("SELECT host(inet_server_addr()), inet_server_port()").fetchone()
    assert admin_address == app_address == (socket.gethostbyname("postgres"), 5432)
    print("POSTGRES_VERSION=" + app.execute("SHOW server_version").fetchone()[0])
print("SETTINGS_FIXTURE_MIGRATION_DESTINATIONS_AGREE=true")
print("ADMIN_AND_APP_SERVER_MATCH=true")
print("ISOLATION_PREFLIGHT_PASSED=true")

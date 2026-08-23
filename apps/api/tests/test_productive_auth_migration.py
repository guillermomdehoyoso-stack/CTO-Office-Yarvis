from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_productive_auth_migration_roundtrip():
    from yarvis_api.main import app

    config = Config("alembic.ini")
    command.downgrade(config, "20260819_41")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert "productive_sessions" not in inspect(connection).get_table_names()
    command.upgrade(config, "head")
    with app.state.yarvis.persistence.engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        assert {
            "external_identity_bindings",
            "identity_provisioning_receipts",
            "oidc_authentication_attempts",
            "productive_sessions",
            "identity_bootstrap_windows",
            "identity_bootstrap_enrollment_receipts",
            "authentication_security_audit",
            "bootstrap_verified_identities",
        } <= tables

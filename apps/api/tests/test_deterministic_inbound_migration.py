from pathlib import Path
from uuid import uuid4

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from yarvis_api.config import Settings
from yarvis_api.persistence.alembic import resolve_migration_database_url

ADMIN_URL = "postgresql://yarvis:yarvis@postgres:5432/postgres"
ALembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
BASE_URL = "postgresql+psycopg://yarvis:yarvis@postgres:5432/{}"


def test_migration_url_uses_settings_when_alembic_url_is_absent() -> None:
    settings = Settings.model_validate({"database_url": "postgresql://settings:settings@database/settings"})
    config = Config(str(ALembic_ini))

    assert config.get_main_option("sqlalchemy.url") is None
    assert resolve_migration_database_url(config.get_main_option("sqlalchemy.url"), settings) == (
        "postgresql+psycopg://settings:settings@database/settings"
    )


def test_migration_url_uses_explicit_programmatic_override() -> None:
    settings = Settings.model_validate({"database_url": "postgresql://settings:settings@database/settings"})
    config = Config(str(ALembic_ini))
    config.set_main_option("sqlalchemy.url", "postgresql://temporary:temporary@database/temporary")

    assert resolve_migration_database_url(config.get_main_option("sqlalchemy.url"), settings) == (
        "postgresql+psycopg://temporary:temporary@database/temporary"
    )


def test_migration_url_preserves_explicit_driver_and_escaped_credentials() -> None:
    settings = Settings.model_validate({"database_url": "postgresql://settings:settings@database/settings"})
    explicit_url = "postgresql+psycopg://user%40tenant:p%40ss%3Aword@database/special"

    assert resolve_migration_database_url(explicit_url, settings) == explicit_url


def _create_temp_database(database_name: str) -> None:
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))


def _drop_temp_database(database_name: str) -> None:
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))


def test_deterministic_inbound_migration_round_trip() -> None:
    database_name = f"yarvis_test_f002_{uuid4().hex}"
    _create_temp_database(database_name)
    engine = create_engine(BASE_URL.format(database_name))
    config = Config(str(ALembic_ini))
    config.set_main_option("sqlalchemy.url", BASE_URL.format(database_name))

    try:
        command.upgrade(config, "20260716_09")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO intake_items (id, intake_number, source_type, content_type, text_content) "
                    "VALUES (:id, :intake_number, :source_type, :content_type, :text_content)"
                ),
                {
                    "id": str(uuid4()),
                    "intake_number": "INT-LEGACY-001",
                    "source_type": "manual_text",
                    "content_type": "text/plain",
                    "text_content": "Legacy intake content",
                },
            )

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert connection.execute(text("select version_num from alembic_version")).scalar_one() == "20260716_11"
            assert "messages" in inspector.get_table_names()
            message_columns = {column["name"] for column in inspector.get_columns("messages")}
            assert {
                "id",
                "intake_item_id",
                "external_source",
                "external_message_id",
                "connector_delivery_id",
                "sender",
                "recipients",
                "subject",
                "text_body",
                "html_body",
                "source_timestamp",
                "received_at",
                "headers",
                "trace_metadata",
                "created_at",
            }.issubset(message_columns)
            message_indexes = {index["name"] for index in inspector.get_indexes("messages")}
            assert {
                "ix_messages_intake_item_id",
                "ix_messages_external_source",
                "ix_messages_external_message_id",
                "ix_messages_connector_delivery_id",
                "ix_messages_sender",
            }.issubset(message_indexes)
            message_fks = inspector.get_foreign_keys("messages")
            assert any(fk["referred_table"] == "intake_items" for fk in message_fks)
            intake_row = connection.execute(
                text("select source_metadata, trace_metadata from intake_items where intake_number = 'INT-LEGACY-001'")
            ).mappings().one()
            assert intake_row["source_metadata"] == {}
            assert intake_row["trace_metadata"] == {}
            intake_columns = {column["name"] for column in inspector.get_columns("intake_items")}
            assert {"idempotency_key", "idempotency_fingerprint"}.issubset(intake_columns)
            intake_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("intake_items")}
            assert "uq_intake_items_organization_id_idempotency_key" in intake_constraints
            assert "uq_intake_items_idempotency_key" not in intake_constraints

            first_organization_id = str(uuid4())
            second_organization_id = str(uuid4())
            for organization_id, suffix in ((first_organization_id, "one"), (second_organization_id, "two")):
                connection.execute(
                    text(
                        "INSERT INTO organizations (id, legal_name, display_name, organization_type, status) "
                        "VALUES (:id, :legal_name, :display_name, 'organization', 'active')"
                    ),
                    {
                        "id": organization_id,
                        "legal_name": f"Migration tenant {suffix}",
                        "display_name": f"Migration tenant {suffix}",
                    },
                )
            insert_intake = text(
                "INSERT INTO intake_items "
                "(id, intake_number, source_type, content_type, text_content, organization_id, idempotency_key) "
                "VALUES (:id, :intake_number, 'manual_text', 'text/plain', 'content', :organization_id, 'shared-key')"
            )
            connection.execute(
                insert_intake,
                {"id": str(uuid4()), "intake_number": "INT-IDEMPOTENCY-001", "organization_id": first_organization_id},
            )
            connection.execute(
                insert_intake,
                {"id": str(uuid4()), "intake_number": "INT-IDEMPOTENCY-002", "organization_id": second_organization_id},
            )
            try:
                connection.execute(
                    insert_intake,
                    {"id": str(uuid4()), "intake_number": "INT-IDEMPOTENCY-003", "organization_id": first_organization_id},
                )
                assert False, "expected duplicate organization/key rejection"
            except IntegrityError:
                pass

        command.downgrade(config, "20260716_09")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert "messages" not in inspector.get_table_names()
            assert "causation_id" not in {column["name"] for column in inspector.get_columns("domain_events")}

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert "messages" in inspector.get_table_names()
            assert "causation_id" in {column["name"] for column in inspector.get_columns("domain_events")}
            assert {"idempotency_key", "idempotency_fingerprint"}.issubset(
                {column["name"] for column in inspector.get_columns("intake_items")}
            )
    finally:
        engine.dispose()
        _drop_temp_database(database_name)

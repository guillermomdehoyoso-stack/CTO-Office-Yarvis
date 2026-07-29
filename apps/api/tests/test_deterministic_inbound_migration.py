from datetime import datetime, timezone
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


def test_mission_work_queue_migration_contract_and_round_trip() -> None:
    database_name = f"yarvis_test_ws004_{uuid4().hex}"
    _create_temp_database(database_name)
    engine = create_engine(BASE_URL.format(database_name))
    config = Config(str(ALembic_ini))
    config.set_main_option("sqlalchemy.url", BASE_URL.format(database_name))

    try:
        command.upgrade(config, "20260726_13")
        with engine.connect() as connection:
            assert "mission_work_items" not in inspect(connection).get_table_names()

        command.upgrade(config, "head")
        with engine.begin() as connection:
            inspector = inspect(connection)
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260729_19"
            assert "mission_work_items" in inspector.get_table_names()
            assert "mission_work_events" in inspector.get_table_names()
            assert {
                "id", "organization_id", "work_item_id", "occurred_at", "event_type", "actor_subject_id",
                "payload_json", "sequence_number", "source_domain_event_id",
            } == {column["name"] for column in inspector.get_columns("mission_work_events")}
            assert "uq_mission_work_events_work_sequence" in {
                constraint["name"] for constraint in inspector.get_unique_constraints("mission_work_events")
            }
            assert {
                "id", "organization_id", "inbox_item_id", "source_type", "source_id", "title", "summary",
                "status", "priority", "assignee_subject_id", "created_by_subject_id", "created_at", "updated_at",
                "assigned_at", "started_at", "resolved_at", "version",
            } == {column["name"] for column in inspector.get_columns("mission_work_items")}
            assert {"ck_mission_work_items_status", "ck_mission_work_items_priority"}.issubset(
                {constraint["name"] for constraint in inspector.get_check_constraints("mission_work_items")}
            )
            assert {
                "uq_mission_work_items_inbox_identity",
                "uq_mission_work_items_source_identity",
            }.issubset({
                constraint["name"] for constraint in inspector.get_unique_constraints("mission_work_items")
            })
            indexes = {index["name"]: index["column_names"] for index in inspector.get_indexes("mission_work_items")}
            expected_indexes = {
                "ix_mission_work_items_org_status_updated": ["organization_id", "status", "updated_at"],
                "ix_mission_work_items_org_assignee_status": ["organization_id", "assignee_subject_id", "status"],
                "ix_mission_work_items_org_priority_updated": ["organization_id", "priority", "updated_at"],
                "ix_mission_work_items_org_source": ["organization_id", "source_type", "source_id"],
                "ix_mission_work_items_org_inbox": ["organization_id", "inbox_item_id"],
            }
            assert expected_indexes.items() <= indexes.items()
            foreign_keys = inspector.get_foreign_keys("mission_work_items")
            assert [foreign_key["referred_table"] for foreign_key in foreign_keys] == ["organizations"]
            assert all("inbox_item_id" not in foreign_key["constrained_columns"] for foreign_key in foreign_keys)

            first_organization_id, second_organization_id, inbox_item_id = uuid4(), uuid4(), uuid4()
            for organization_id in (first_organization_id, second_organization_id):
                connection.execute(
                    text(
                        "INSERT INTO organizations (id, legal_name, display_name, organization_type, status) "
                        "VALUES (:id, :legal_name, :display_name, 'organization', 'active')"
                    ),
                    {"id": str(organization_id), "legal_name": str(organization_id), "display_name": str(organization_id)},
                )

            insert = text(
                "INSERT INTO mission_work_items "
                "(id, organization_id, inbox_item_id, source_type, source_id, title, status, priority, "
                "created_by_subject_id, created_at, updated_at, version) VALUES "
                "(:id, :organization_id, :inbox_item_id, 'email', :source_id, 'Migration work', :status, :priority, "
                "'migration:test', now(), now(), 1)"
            )
            first = {"id": str(uuid4()), "organization_id": str(first_organization_id), "inbox_item_id": str(inbox_item_id), "source_id": str(uuid4()), "status": "open", "priority": "normal"}
            connection.execute(insert, first)
            connection.execute(insert, {**first, "id": str(uuid4()), "organization_id": str(second_organization_id)})
            try:
                with connection.begin_nested():
                    connection.execute(
                        insert,
                        {**first, "id": str(uuid4()), "inbox_item_id": str(uuid4())},
                    )
                assert False, "expected duplicate organization/source rejection"
            except IntegrityError:
                pass
            for invalid_values in (({"id": str(uuid4()), "status": "invalid", "priority": "normal"}), ({"id": str(uuid4()), "status": "open", "priority": "invalid"}), ({"id": str(uuid4()), "status": "open", "priority": "normal"})):
                try:
                    with connection.begin_nested():
                        connection.execute(insert, {**first, **invalid_values})
                    assert False, "expected migration constraint rejection"
                except IntegrityError:
                    pass

        command.downgrade(config, "20260726_13")
        with engine.connect() as connection:
            assert "mission_work_items" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert "mission_work_items" in inspect(connection).get_table_names()
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260729_19"
    finally:
        engine.dispose()
        _drop_temp_database(database_name)


def test_process_runtime_migration_contract_and_round_trip() -> None:
    database_name = f"yarvis_test_ws006c_{uuid4().hex}"
    _create_temp_database(database_name)
    engine = create_engine(BASE_URL.format(database_name))
    config = Config(str(ALembic_ini))
    config.set_main_option("sqlalchemy.url", BASE_URL.format(database_name))

    try:
        command.upgrade(config, "20260727_16")
        with engine.connect() as connection:
            assert "process_instances" not in inspect(connection).get_table_names()

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260729_19"
            assert {"process_instances", "process_instance_events"}.issubset(inspector.get_table_names())
            assert "process_instance_work_links" in inspector.get_table_names()
            assert "source_domain_event_id" in {column["name"] for column in inspector.get_columns("mission_work_events")}
            instance_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("process_instances")}
            assert {"uq_process_instances_id_organization", "uq_process_instances_start_idempotency"}.issubset(
                instance_constraints
            )
            event_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("process_instance_events")}
            assert {"uq_process_instance_events_sequence", "uq_process_instance_events_idempotency"}.issubset(
                event_constraints
            )
            indexes = {index["name"]: index["column_names"] for index in inspector.get_indexes("process_instance_events")}
            assert indexes["ix_process_instance_events_org_instance_sequence"] == [
                "organization_id",
                "process_instance_id",
                "sequence_number",
            ]

        command.downgrade(config, "20260727_16")
        with engine.connect() as connection:
            assert "process_instances" not in inspect(connection).get_table_names()
            assert "process_instance_events" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert {"process_instances", "process_instance_events", "process_instance_work_links"}.issubset(inspect(connection).get_table_names())
    finally:
        engine.dispose()
        _drop_temp_database(database_name)


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

        command.upgrade(config, "20260716_11")
        deterministic_organization_id = str(uuid4())
        deterministic_intake_id = str(uuid4())
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO organizations (id, legal_name, display_name, organization_type, status) "
                    "VALUES (:id, 'Backfill tenant', 'Backfill tenant', 'organization', 'active')"
                ),
                {"id": deterministic_organization_id},
            )
            connection.execute(
                text(
                    "INSERT INTO intake_items "
                    "(id, intake_number, source_type, content_type, text_content, organization_id, idempotency_key, idempotency_fingerprint) "
                    "VALUES (:id, 'INT-DETERMINISTIC-BACKFILL', 'email', 'message/rfc822', 'content', :organization_id, 'backfill-key', :fingerprint)"
                ),
                {"id": deterministic_intake_id, "organization_id": deterministic_organization_id, "fingerprint": "a" * 64},
            )

        command.upgrade(config, "20260726_12")
        tied_event_ids = sorted((uuid4(), uuid4()), key=str)
        tied_timestamp = datetime(2026, 7, 26, tzinfo=timezone.utc)
        with engine.begin() as connection:
            for event_id in tied_event_ids:
                connection.execute(
                    text(
                        "INSERT INTO domain_events "
                        "(id, event_type, aggregate_type, aggregate_id, organization_id, payload, occurred_at, recorded_at) "
                        "VALUES (:id, 'intake.received', 'intake_item', :aggregate_id, :organization_id, "
                        "CAST(:payload AS jsonb), :occurred_at, :recorded_at)"
                    ),
                    {
                        "id": str(event_id),
                        "aggregate_id": deterministic_intake_id,
                        "organization_id": deterministic_organization_id,
                        "payload": "{}",
                        "occurred_at": tied_timestamp,
                        "recorded_at": tied_timestamp,
                    },
                )

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert connection.execute(text("select version_num from alembic_version")).scalar_one() == "20260729_19"
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
                text("select source_metadata, trace_metadata, intake_mode from intake_items where intake_number = 'INT-LEGACY-001'")
            ).mappings().one()
            assert intake_row["source_metadata"] == {}
            assert intake_row["trace_metadata"] == {}
            assert intake_row["intake_mode"] == "legacy"
            assert connection.execute(
                text("select intake_mode from intake_items where intake_number = 'INT-DETERMINISTIC-BACKFILL'")
            ).scalar_one() == "deterministic"
            intake_columns = {column["name"] for column in inspector.get_columns("intake_items")}
            assert {"idempotency_key", "idempotency_fingerprint", "intake_mode"}.issubset(intake_columns)
            intake_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("intake_items")}
            assert "uq_intake_items_organization_id_idempotency_key" in intake_constraints
            assert "uq_intake_items_id_organization_id" in intake_constraints
            assert "uq_intake_items_idempotency_key" not in intake_constraints
            assert {"sites", "projects", "connector_mappings", "intake_operational_context_associations"}.issubset(
                inspector.get_table_names()
            )
            assert {"mission_inbox_items", "projection_checkpoints"}.issubset(inspector.get_table_names())
            mission_inbox_constraints = {
                constraint["name"] for constraint in inspector.get_unique_constraints("mission_inbox_items")
            }
            assert "uq_mission_inbox_items_source_identity" in mission_inbox_constraints
            checkpoint_constraints = {
                constraint["name"] for constraint in inspector.get_unique_constraints("projection_checkpoints")
            }
            assert "uq_projection_checkpoints_projection_name" in checkpoint_constraints
            mission_inbox_indexes = {index["name"] for index in inspector.get_indexes("mission_inbox_items")}
            assert {
                "ix_mission_inbox_items_status",
                "ix_mission_inbox_items_priority",
                "ix_mission_inbox_items_received_at",
                "ix_mission_inbox_items_last_activity_at",
                "ix_mission_inbox_items_project_id",
                "ix_mission_inbox_items_site_id",
            }.issubset(mission_inbox_indexes)
            mission_inbox_fks = {fk["referred_table"] for fk in inspector.get_foreign_keys("mission_inbox_items")}
            assert {"organizations", "intake_items", "sites", "projects", "connector_mappings", "domain_events"}.issubset(
                mission_inbox_fks
            )
            assert "event_sequence" in {column["name"] for column in inspector.get_columns("domain_events")}
            event_sequences = connection.execute(
                text("SELECT id, event_sequence FROM domain_events ORDER BY event_sequence")
            ).mappings().all()
            assert [str(row["id"]) for row in event_sequences] == [str(event_id) for event_id in tied_event_ids]
            assert [row["event_sequence"] for row in event_sequences] == [1, 2]
            next_event_sequence = connection.execute(
                text(
                    "INSERT INTO domain_events "
                    "(id, event_type, aggregate_type, aggregate_id, organization_id, payload, occurred_at) "
                    "VALUES (:id, 'intake.received', 'intake_item', :aggregate_id, :organization_id, "
                    "CAST(:payload AS jsonb), :occurred_at) RETURNING event_sequence"
                ),
                {
                    "id": str(uuid4()),
                    "aggregate_id": deterministic_intake_id,
                    "organization_id": deterministic_organization_id,
                    "payload": "{}",
                    "occurred_at": tied_timestamp,
                },
            ).scalar_one()
            assert next_event_sequence == 3
            event_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("domain_events")}
            assert "uq_domain_events_event_sequence" in event_constraints
            association_columns = {
                column["name"] for column in inspector.get_columns("intake_operational_context_associations")
            }
            assert {
                "intake_item_id",
                "organization_id",
                "site_id",
                "project_id",
                "connector_mapping_id",
                "idempotency_key",
                "idempotency_fingerprint",
                "actor_id",
                "correlation_id",
                "causation_id",
                "associated_at",
            }.issubset(association_columns)
            association_constraints = {
                constraint["name"]
                for constraint in inspector.get_unique_constraints("intake_operational_context_associations")
            }
            assert {
                "uq_intake_operational_context_associations_intake_item_id",
                "uq_ioca_org_idempotency_key",
            }.issubset(association_constraints)

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

        command.downgrade(config, "20260726_12")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert "mission_inbox_items" not in inspector.get_table_names()
            assert "projection_checkpoints" not in inspector.get_table_names()
            assert "event_sequence" not in {column["name"] for column in inspector.get_columns("domain_events")}

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert {"mission_inbox_items", "projection_checkpoints"}.issubset(inspector.get_table_names())
            assert "event_sequence" in {column["name"] for column in inspector.get_columns("domain_events")}

        command.downgrade(config, "20260716_09")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert "messages" not in inspector.get_table_names()
            assert "intake_operational_context_associations" not in inspector.get_table_names()
            assert "mission_inbox_items" not in inspector.get_table_names()
            assert "event_sequence" not in {column["name"] for column in inspector.get_columns("domain_events")}
            assert "causation_id" not in {column["name"] for column in inspector.get_columns("domain_events")}

        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert "messages" in inspector.get_table_names()
            assert "causation_id" in {column["name"] for column in inspector.get_columns("domain_events")}
            assert {"idempotency_key", "idempotency_fingerprint"}.issubset(
                {column["name"] for column in inspector.get_columns("intake_items")}
            )
            assert "intake_operational_context_associations" in inspector.get_table_names()
            assert "mission_inbox_items" in inspector.get_table_names()
            assert "event_sequence" in {column["name"] for column in inspector.get_columns("domain_events")}
    finally:
        engine.dispose()
        _drop_temp_database(database_name)

import os
import shutil

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql

TEST_URL = "postgresql://yarvis:yarvis@postgres:5432/yarvis_test"
TEST_DATABASE_NAME = "yarvis_test"
ADMIN_URL = "postgresql://yarvis:yarvis@postgres:5432/postgres"
os.environ["DATABASE_URL"] = TEST_URL
os.environ["DOCUMENT_STORAGE_ROOT"] = "/tmp/yarvis_test_data"


@pytest.fixture(scope="session", autouse=True)
def test_database():
    assert TEST_DATABASE_NAME.startswith("yarvis_test")
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(TEST_DATABASE_NAME)))
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DATABASE_NAME)))
    try:
        alembic_config = Config("alembic.ini")
        command.upgrade(alembic_config, "head")
        command.upgrade(alembic_config, "head")
        yield
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(TEST_DATABASE_NAME)))


@pytest.fixture(autouse=True)
def clean_database(test_database):
    from yarvis_api.catalogs import load_catalogs
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        session.connection().exec_driver_sql("TRUNCATE TABLE application_traces, radar_command_receipts, radar_activities, radar_checklist_items, radar_requests, radar_merchants, domain_events, principal_memberships, principals, attention_items, policy_evaluations, operational_policies, resolution_decisions, observations, document_records, source_records, netpay_device_assignments, netpay_shipments, netpay_service_cases, next_action_suggestions, operational_alerts, requirement_fulfillments, intake_classifications, case_checklists, evidence, intake_items, checklist_requirements, checklist_templates, cases, people, organizations, document_types, case_types RESTART IDENTITY CASCADE")
        session.commit()
        load_catalogs(session)
        session.commit()
    shutil.rmtree(os.environ["DOCUMENT_STORAGE_ROOT"], ignore_errors=True)

import os

import psycopg
import pytest
from alembic import command
from alembic.config import Config

TEST_URL = "postgresql://yarvis:yarvis@postgres:5432/yarvis_test"
os.environ["DATABASE_URL"] = TEST_URL


@pytest.fixture(scope="session", autouse=True)
def test_database():
    with psycopg.connect("postgresql://yarvis:yarvis@postgres:5432/postgres", autocommit=True) as connection:
        cursor = connection.execute("SELECT 1 FROM pg_database WHERE datname = 'yarvis_test'")
        if cursor.fetchone() is None:
            connection.execute("CREATE DATABASE yarvis_test")
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def clean_database(test_database):
    from yarvis_api.database import SessionLocal
    from yarvis_api.catalogs import load_catalogs
    with SessionLocal() as session:
        session.connection().exec_driver_sql("TRUNCATE TABLE domain_events, attention_items, policy_evaluations, operational_policies, resolution_decisions, observations, document_records, source_records, netpay_device_assignments, netpay_shipments, netpay_service_cases, next_action_suggestions, operational_alerts, requirement_fulfillments, intake_classifications, case_checklists, evidence, intake_items, checklist_requirements, checklist_templates, cases, people, organizations, document_types, case_types RESTART IDENTITY CASCADE")
        session.commit()
        load_catalogs(session)
        session.commit()

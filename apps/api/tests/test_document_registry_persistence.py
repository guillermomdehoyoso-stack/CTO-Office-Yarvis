from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from yarvis_api.clock import utc_now
from yarvis_api.models.document_registry import Document, DocumentAssociation, DocumentVersion
from yarvis_api.models.organization import Organization


ADMIN_URL = "postgresql://yarvis:yarvis@postgres:5432/postgres"
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
BASE_URL = "postgresql+psycopg://yarvis:yarvis@postgres:5432/{}"


def _document(organization_id, **overrides):
    values = {
        "organization_id": organization_id,
        "title": "Document",
        "classification": "general",
        "visibility": "organization",
        "created_by_subject_id": "test",
    }
    values.update(overrides)
    return Document(**values)


def _version(organization_id, document_id, sequence, **overrides):
    values = {
        "organization_id": organization_id,
        "document_id": document_id,
        "sequence": sequence,
        "media_type": "text/plain",
        "checksum_algorithm": "sha256",
        "checksum_value": "a" * 64,
        "storage_provider": "external",
        "external_reference": "https://example.test/artifact",
        "source_kind": "manual",
        "provenance": {},
        "created_by_subject_id": "test",
    }
    values.update(overrides)
    return DocumentVersion(**values)


def _assert_flush_rejected(session, item) -> None:
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(item)
            session.flush()


def test_document_version_ownership_current_version_and_lineage(test_database) -> None:
    from yarvis_api.main import app

    org_one = Organization(id=uuid4(), legal_name="DI ownership one", display_name="DI ownership one")
    org_two = Organization(id=uuid4(), legal_name="DI ownership two", display_name="DI ownership two")
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all([org_one, org_two])
        session.flush()
        first = _document(org_one.id)
        other_document = _document(org_one.id, title="Other")
        foreign_document = _document(org_two.id, title="Foreign")
        session.add_all([first, other_document, foreign_document])
        session.flush()
        first_version = _version(org_one.id, first.id, 1)
        other_version = _version(org_one.id, other_document.id, 1)
        foreign_version = _version(org_two.id, foreign_document.id, 1)
        session.add_all([first_version, other_version, foreign_version])
        session.flush()
        first.current_version_id = first_version.id
        session.commit()

        _assert_flush_rejected(session, _version(org_two.id, first.id, 2))
        first.current_version_id = foreign_version.id
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()

        first = session.get(Document, first.id)
        first.current_version_id = other_version.id
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()

        _assert_flush_rejected(session, _version(org_one.id, first.id, 2, supersedes_version_id=other_version.id))
        _assert_flush_rejected(session, _version(org_one.id, first.id, 2, id=uuid4(), supersedes_version_id=uuid4()))
        self_version = _version(org_one.id, first.id, 2, id=uuid4())
        self_version.supersedes_version_id = self_version.id
        _assert_flush_rejected(session, self_version)


def test_storage_checksum_size_and_sequence_constraints(test_database) -> None:
    from yarvis_api.main import app

    org = Organization(id=uuid4(), legal_name="DI storage", display_name="DI storage")
    with app.state.yarvis.persistence.create_session() as session:
        session.add(org)
        session.flush()
        first = _document(org.id)
        second = _document(org.id, title="Second")
        session.add_all([first, second])
        session.flush()
        provider_key = _version(org.id, first.id, 1, storage_provider="local", storage_key="documents/2026/a.pdf", external_reference=None, byte_size=0)
        external = _version(org.id, first.id, 2, storage_provider="none", external_reference="urn:external:artifact", byte_size=1, supersedes_version_id=provider_key.id)
        same_sequence_other_document = _version(org.id, second.id, 1, storage_provider="unknown", storage_key="provider/object", external_reference=None, byte_size=2)
        session.add_all([provider_key, external, same_sequence_other_document])
        session.commit()

        _assert_flush_rejected(session, _version(org.id, first.id, 1))
        for storage_key in ("", "/tmp/artifact", r"C:\\temp\\artifact", r"\\\\server\\share\\artifact", "../artifact", "folder/../artifact"):
            _assert_flush_rejected(session, _version(org.id, first.id, 3, storage_key=storage_key, external_reference=None))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, storage_key=None, external_reference=None))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, checksum_algorithm=None))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, checksum_value=None))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, checksum_algorithm="", checksum_value="a"))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, checksum_value="", checksum_algorithm="sha256"))
        _assert_flush_rejected(session, _version(org.id, first.id, 3, byte_size=-1))
        # Algorithm values and dual provider/external references intentionally remain provider-neutral metadata.
        accepted = _version(org.id, first.id, 3, checksum_algorithm="future-hash", checksum_value="short", storage_key="provider/key", external_reference="urn:external:copy", byte_size=3)
        session.add(accepted)
        session.commit()


def test_association_history_and_tenant_scoped_document_integrity(test_database) -> None:
    from yarvis_api.main import app

    org_one = Organization(id=uuid4(), legal_name="DI associations one", display_name="DI associations one")
    org_two = Organization(id=uuid4(), legal_name="DI associations two", display_name="DI associations two")
    subject = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all([org_one, org_two])
        session.flush()
        first = _document(org_one.id)
        second = _document(org_one.id, title="Second")
        foreign = _document(org_two.id, title="Foreign")
        session.add_all([first, second, foreign])
        session.flush()
        active = DocumentAssociation(organization_id=org_one.id, document_id=first.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test")
        session.add(active)
        session.commit()

        _assert_flush_rejected(session, DocumentAssociation(organization_id=org_one.id, document_id=first.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test"))
        _assert_flush_rejected(session, DocumentAssociation(organization_id=org_two.id, document_id=first.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test"))
        _assert_flush_rejected(session, DocumentAssociation(organization_id=org_one.id, document_id=first.id, subject_type="unsupported", subject_id=subject, linked_by_subject_id="test"))
        _assert_flush_rejected(session, DocumentAssociation(organization_id=org_one.id, document_id=first.id, subject_type="organization", subject_id=uuid4(), linked_at=utc_now(), unlinked_at=utc_now() - timedelta(seconds=1), linked_by_subject_id="test"))

        active.unlinked_at = utc_now()
        session.commit()
        relink = DocumentAssociation(organization_id=org_one.id, document_id=first.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test")
        independent_same_subject = DocumentAssociation(organization_id=org_one.id, document_id=second.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test")
        foreign_tenant = DocumentAssociation(organization_id=org_two.id, document_id=foreign.id, subject_type="organization", subject_id=subject, linked_by_subject_id="test")
        session.add_all([relink, independent_same_subject, foreign_tenant])
        session.commit()
        history = session.query(DocumentAssociation).filter_by(document_id=first.id, subject_id=subject).order_by(DocumentAssociation.linked_at).all()
        assert len(history) == 2
        assert history[0].id == active.id and history[0].unlinked_at is not None
        assert history[1].id == relink.id and history[1].unlinked_at is None


def test_document_version_is_append_only(test_database) -> None:
    from yarvis_api.main import app

    org = Organization(id=uuid4(), legal_name="DI append only", display_name="DI append only")
    with app.state.yarvis.persistence.create_session() as session:
        session.add(org)
        session.flush()
        document = _document(org.id)
        session.add(document)
        session.flush()
        version = _version(org.id, document.id, 1)
        session.add(version)
        session.commit()
        with session.begin(), pytest.raises(DBAPIError):
            session.execute(text("UPDATE document_versions SET media_type = 'x' WHERE id = :id"), {"id": version.id})
        with session.begin(), pytest.raises(DBAPIError):
            session.execute(text("DELETE FROM document_versions WHERE id = :id"), {"id": version.id})


def test_document_registry_schema_and_migration_round_trip(test_database) -> None:
    database_name = f"yarvis_test_di002a_{uuid4().hex}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
    engine = create_engine(BASE_URL.format(database_name))
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", BASE_URL.format(database_name))
    try:
        command.upgrade(config, "20260730_20")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260802_27"
            assert {"documents", "document_versions", "document_associations"}.issubset(inspector.get_table_names())
            assert {column["name"]: column["nullable"] for column in inspector.get_columns("documents")}["current_version_id"]
            assert {"fk_documents_organization", "fk_documents_current_version_document_organization"}.issubset({item["name"] for item in inspector.get_foreign_keys("documents")})
            assert {"fk_document_versions_document_organization", "fk_document_versions_supersedes_document_organization"}.issubset({item["name"] for item in inspector.get_foreign_keys("document_versions")})
            assert {"fk_document_associations_organization", "fk_document_associations_document_organization"}.issubset({item["name"] for item in inspector.get_foreign_keys("document_associations")})
            assert {"uq_document_versions_sequence", "uq_document_versions_id_document_organization"}.issubset({item["name"] for item in inspector.get_unique_constraints("document_versions")})
            assert {"ck_document_versions_reference", "ck_document_versions_relative_key", "ck_document_versions_not_self_superseding"}.issubset({item["name"] for item in inspector.get_check_constraints("document_versions")})
            indexes = {item["name"]: item for item in inspector.get_indexes("document_associations")}
            assert indexes["uq_document_associations_active"]["unique"]
            assert "unlinked_at IS NULL" in str(indexes["uq_document_associations_active"].get("dialect_options", {}))
            assert connection.execute(text("SELECT 1 FROM pg_trigger WHERE tgname = 'document_versions_append_only'")).scalar_one() == 1
            assert connection.execute(text("SELECT 1 FROM pg_proc WHERE proname = 'document_versions_append_only_guard'")).scalar_one() == 1
        command.downgrade(config, "20260730_20")
        with engine.connect() as connection:
            assert not {"documents", "document_versions", "document_associations"}.intersection(inspect(connection).get_table_names())
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260802_27"
    finally:
        engine.dispose()
        with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))

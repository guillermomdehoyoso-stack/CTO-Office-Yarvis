from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import AddDocumentVersionCommand, CreateDocumentCommand, DocumentAssociationCommand, UnlinkDocumentAssociationCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.services.document_registry import DocumentRegistryQueryService, DocumentRegistryService


def principal(organization_id, authority):
    return AuthenticatedPrincipal("reader", str(organization_id), (), (), authority, "test", datetime.now(timezone.utc), False)


def command_metadata(key):
    return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key=key)


def query_metadata():
    return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), query_id=str(uuid4()))


def create_command(title="Query document"):
    return CreateDocumentCommand(title, "general", "organization", "text/plain", "sha256", "a" * 64, "external", None, "urn:query", "manual", {}, "query.txt", 1)


def version_command(document_id, checksum):
    return AddDocumentVersionCommand(document_id, "text/plain", "sha256", checksum, "external", None, f"urn:query:{checksum}", "manual", {}, "query.txt", 1)


def create_organization(app, name):
    organization = Organization(id=uuid4(), legal_name=name, display_name=name)
    organization_id = organization.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(organization)
        session.commit()
    return organization_id


def test_document_queries_enforce_authority_and_conceal_documents(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI query first")
    second_id = create_organization(app, "DI query second")
    commands = DocumentRegistryService(app.state.yarvis.persistence)
    document = commands.create(create_command(), command_metadata("query-create"), principal(first_id, "document.create"))
    foreign = commands.create(create_command("Foreign query document"), command_metadata("query-foreign"), principal(second_id, "document.create"))
    queries = DocumentRegistryQueryService()
    with app.state.yarvis.persistence.create_session() as session:
        events_before = session.scalar(select(func.count()).select_from(DomainEvent))
        result = queries.get(session, document.id, principal(first_id, "document.read"), query_metadata())
        assert result.id == document.id and result.active_association_count == 0 and result.lifecycle_status == "active"
        for document_id in (uuid4(), foreign.id):
            with pytest.raises(ApplicationError) as error:
                queries.get(session, document_id, principal(first_id, "document.read"), query_metadata())
            assert (error.value.code, error.value.message) == (ApplicationErrorCode.RESOURCE_NOT_FOUND, "document not found")
        for authority in ("", "document.create"):
            with pytest.raises((ApplicationError, ValueError)):
                queries.get(session, document.id, principal(first_id, authority), query_metadata())
        assert session.scalar(select(func.count()).select_from(DomainEvent)) == events_before


def test_version_and_active_association_queries_are_tenant_safe_and_deterministic(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI query versions")
    commands = DocumentRegistryService(app.state.yarvis.persistence)
    document = commands.create(create_command(), command_metadata("versions-create"), principal(organization_id, "document.create"))
    first = commands.add(version_command(document.id, "b" * 64), command_metadata("versions-first"), principal(organization_id, "document.version.add"))
    second = commands.add(version_command(document.id, "c" * 64), command_metadata("versions-second"), principal(organization_id, "document.version.add"))
    active = commands.link(DocumentAssociationCommand(document.id, "organization", organization_id), command_metadata("associations-link"), principal(organization_id, "document.association.link"))
    queries = DocumentRegistryQueryService()
    with app.state.yarvis.persistence.create_session() as session:
        versions = queries.versions(session, document.id, principal(organization_id, "document.read"), query_metadata())
        assert [version.sequence for version in versions] == [1, 2, 3]
        assert [version.id for version in versions][-2:] == [first.id, second.id]
        assert [association.id for association in queries.associations(session, document.id, principal(organization_id, "document.read"), query_metadata())] == [active.id]
    commands.unlink(UnlinkDocumentAssociationCommand(document.id, active.id), command_metadata("associations-unlink"), principal(organization_id, "document.association.unlink"))
    with app.state.yarvis.persistence.create_session() as session:
        assert queries.associations(session, document.id, principal(organization_id, "document.read"), query_metadata()) == []


def test_documents_by_subject_is_active_only_tenant_scoped_and_concealed(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI query subject first")
    second_id = create_organization(app, "DI query subject second")
    commands = DocumentRegistryService(app.state.yarvis.persistence)
    first = commands.create(create_command("First"), command_metadata("subject-first-create"), principal(first_id, "document.create"))
    second = commands.create(create_command("Second"), command_metadata("subject-second-create"), principal(second_id, "document.create"))
    association = commands.link(DocumentAssociationCommand(first.id, "organization", first_id), command_metadata("subject-first-link"), principal(first_id, "document.association.link"))
    commands.link(DocumentAssociationCommand(second.id, "organization", second_id), command_metadata("subject-second-link"), principal(second_id, "document.association.link"))
    queries = DocumentRegistryQueryService()
    with app.state.yarvis.persistence.create_session() as session:
        page = queries.by_subject(session, "organization", first_id, principal(first_id, "document.read"), query_metadata())
        assert [item.id for item in page.items] == [first.id] and (page.total, page.limit, page.offset) == (1, 50, 0)
        for subject_type, subject_id in (("organization", second_id), ("unsupported", uuid4())):
            with pytest.raises(ApplicationError) as error:
                queries.by_subject(session, subject_type, subject_id, principal(first_id, "document.read"), query_metadata())
            assert (error.value.code, error.value.message) == (ApplicationErrorCode.RESOURCE_NOT_FOUND, "document not found")
    commands.unlink(UnlinkDocumentAssociationCommand(first.id, association.id), command_metadata("subject-first-unlink"), principal(first_id, "document.association.unlink"))
    with app.state.yarvis.persistence.create_session() as session:
        assert queries.by_subject(session, "organization", first_id, principal(first_id, "document.read"), query_metadata()).items == []

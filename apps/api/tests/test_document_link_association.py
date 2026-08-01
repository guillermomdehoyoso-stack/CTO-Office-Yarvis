from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import CreateDocumentCommand, DocumentAssociationCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.document_registry import Document, DocumentAssociation, DocumentCommandIdempotency
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.operational_context import Project, Site
from yarvis_api.services.document_registry import DocumentRegistryService


class _FailingCommitRuntime:
    def __init__(self, runtime):
        self.runtime = runtime

    def create_session(self):
        session = self.runtime.create_session()
        session.commit = lambda: (_ for _ in ()).throw(RuntimeError("forced commit failure"))
        return session


def principal(organization_id, authority):
    return AuthenticatedPrincipal(
        "actor", str(organization_id), (), (), authority, "test", datetime.now(timezone.utc), False
    )


def metadata(idempotency_key):
    return RequestMetadata(
        datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key=idempotency_key
    )


def create_command():
    return CreateDocumentCommand(
        "Linked document", "general", "organization", "text/plain", "sha256", "a" * 64,
        "external", None, "urn:document:source", "manual", {}, "linked.txt", 1,
    )


def link_counts(session, organization_id, document_id=None):
    association_query = select(func.count()).select_from(DocumentAssociation).where(
        DocumentAssociation.organization_id == organization_id
    )
    event_query = select(func.count()).select_from(DomainEvent).where(
        DomainEvent.organization_id == organization_id,
        DomainEvent.event_type == "document.associated",
    )
    receipt_query = select(func.count()).select_from(DocumentCommandIdempotency).where(
        DocumentCommandIdempotency.organization_id == organization_id,
        DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-005",
    )
    if document_id:
        association_query = association_query.where(DocumentAssociation.document_id == document_id)
        event_query = event_query.where(DomainEvent.aggregate_id == document_id)
    return (
        session.scalar(association_query),
        session.scalar(event_query),
        session.scalar(receipt_query),
    )


def create_organization(app, name):
    organization = Organization(id=uuid4(), legal_name=name, display_name=name)
    organization_id = organization.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(organization)
        session.commit()
    return organization_id


def create_document(service, organization_id, key):
    return service.create(create_command(), metadata(key), principal(organization_id, "document.create"))


def test_governed_link_replays_and_conflicts_without_duplicate_side_effects(test_database):
    from yarvis_api.main import app

    organization = Organization(
        id=uuid4(), legal_name="DI link organization", display_name="DI link organization"
    )
    organization_id = organization.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(organization)
        session.commit()

    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = service.create(
        create_command(), metadata("link-create"), principal(organization_id, "document.create")
    )
    command = DocumentAssociationCommand(document.id, "organization", organization_id)
    first = service.link(command, metadata("link-key"), principal(organization_id, "document.association.link"))
    replay = service.link(command, metadata("link-key"), principal(organization_id, "document.association.link"))

    assert replay.id == first.id
    with pytest.raises(ApplicationError) as error:
        service.link(
            DocumentAssociationCommand(document.id, "site", uuid4()),
            metadata("link-key"),
            principal(organization_id, "document.association.link"),
        )
    assert error.value.code == ApplicationErrorCode.CONFLICT

    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(DocumentAssociation.document_id == document.id)
        ) == 1
        assert session.scalar(
            select(func.count()).select_from(DomainEvent).where(
                DomainEvent.aggregate_id == document.id, DomainEvent.event_type == "document.associated"
            )
        ) == 1
        assert session.scalar(
            select(func.count()).select_from(DocumentCommandIdempotency).where(
                DocumentCommandIdempotency.organization_id == organization_id,
                DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-005",
                DocumentCommandIdempotency.idempotency_key == "link-key",
            )
        ) == 1


@pytest.mark.parametrize("authority", ["", "document.create"])
def test_link_requires_exact_authority_without_side_effects(test_database, authority):
    from yarvis_api.main import app

    organization_id = create_organization(app, f"DI link authority {authority or 'missing'}")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, f"authority-create-{authority or 'missing'}")

    with pytest.raises((ApplicationError, ValueError)):
        service.link(
            DocumentAssociationCommand(document.id, "organization", organization_id),
            metadata(f"authority-link-{authority or 'missing'}"),
            principal(organization_id, authority),
        )

    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, organization_id, document.id) == (0, 0, 0)


def test_link_conceals_missing_and_foreign_documents_without_side_effects(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI link document first")
    second_id = create_organization(app, "DI link document second")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    foreign_document = create_document(service, second_id, "foreign-document-create")

    for document_id, key in ((uuid4(), "missing-document"), (foreign_document.id, "foreign-document")):
        with pytest.raises(ApplicationError) as error:
            service.link(
                DocumentAssociationCommand(document_id, "organization", first_id),
                metadata(key),
                principal(first_id, "document.association.link"),
            )
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert error.value.message == "document not found"

    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, first_id) == (0, 0, 0)
        assert link_counts(session, second_id, foreign_document.id) == (0, 0, 0)


@pytest.mark.parametrize("subject_type", ["organization", "site", "project", "operational_task", "unsupported"])
def test_link_conceals_missing_or_unsupported_subjects_without_side_effects(test_database, subject_type):
    from yarvis_api.main import app

    organization_id = create_organization(app, f"DI link missing {subject_type}")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, f"missing-subject-create-{subject_type}")

    with pytest.raises(ApplicationError) as error:
        service.link(
            DocumentAssociationCommand(document.id, subject_type, uuid4()),
            metadata(f"missing-subject-{subject_type}"),
            principal(organization_id, "document.association.link"),
        )
    assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert error.value.message == "document not found"
    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, organization_id, document.id) == (0, 0, 0)


def test_link_conceals_foreign_site_and_project_subjects_without_side_effects(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI link subject first")
    second_id = create_organization(app, "DI link subject second")
    foreign_site = Site(id=uuid4(), organization_id=second_id, reference="foreign-site")
    foreign_project = Project(id=uuid4(), organization_id=second_id, site_id=foreign_site.id, reference="foreign-project")
    foreign_site_id, foreign_project_id = foreign_site.id, foreign_project.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(foreign_site)
        session.flush()
        session.add(foreign_project)
        session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, first_id, "foreign-subject-document")

    for subject_type, subject_id in (("site", foreign_site_id), ("project", foreign_project_id)):
        with pytest.raises(ApplicationError) as error:
            service.link(
                DocumentAssociationCommand(document.id, subject_type, subject_id),
                metadata(f"foreign-{subject_type}"),
                principal(first_id, "document.association.link"),
            )
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert error.value.message == "document not found"
    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, first_id, document.id) == (0, 0, 0)


def test_link_idempotency_is_organization_scoped_and_duplicate_is_side_effect_free(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI link scope first")
    second_id = create_organization(app, "DI link scope second")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first_document = create_document(service, first_id, "scope-create-first")
    second_document = create_document(service, second_id, "scope-create-second")
    key = "shared-link-key"

    first = service.link(
        DocumentAssociationCommand(first_document.id, "organization", first_id),
        metadata(key), principal(first_id, "document.association.link"),
    )
    second = service.link(
        DocumentAssociationCommand(second_document.id, "organization", second_id),
        metadata(key), principal(second_id, "document.association.link"),
    )
    assert service.link(
        DocumentAssociationCommand(first_document.id, "organization", first_id),
        metadata(key), principal(first_id, "document.association.link"),
    ).id == first.id
    assert service.link(
        DocumentAssociationCommand(second_document.id, "organization", second_id),
        metadata(key), principal(second_id, "document.association.link"),
    ).id == second.id
    assert service.link(
        DocumentAssociationCommand(first_document.id, "organization", first_id),
        metadata("fresh-duplicate-key"), principal(first_id, "document.association.link"),
    ).id == first.id

    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, first_id, first_document.id) == (1, 1, 1)
        assert link_counts(session, second_id, second_document.id) == (1, 1, 1)


def test_link_commit_failure_rolls_back_and_retry_replays(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI link rollback")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "rollback-create")
    command = DocumentAssociationCommand(document.id, "organization", organization_id)
    request = metadata("rollback-link")

    with pytest.raises(RuntimeError, match="forced commit failure"):
        DocumentRegistryService(_FailingCommitRuntime(app.state.yarvis.persistence)).link(
            command, request, principal(organization_id, "document.association.link")
        )

    with app.state.yarvis.persistence.create_session() as session:
        persisted_document = session.get(Document, document.id)
        assert persisted_document.version == document.version
        assert persisted_document.lifecycle_status == document.lifecycle_status
        assert link_counts(session, organization_id, document.id) == (0, 0, 0)
        assert session.get(Organization, organization_id).status == "active"

    first = service.link(command, request, principal(organization_id, "document.association.link"))
    replay = service.link(command, request, principal(organization_id, "document.association.link"))
    assert replay.id == first.id
    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, organization_id, document.id) == (1, 1, 1)


def test_matching_concurrent_link_replays_winning_receipt(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI link matching race")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "matching-race-create")
    command = DocumentAssociationCommand(document.id, "organization", organization_id)
    request = metadata("matching-race-link")
    barrier = Barrier(2)

    def invoke():
        barrier.wait()
        return DocumentRegistryService(app.state.yarvis.persistence).link(
            command, request, principal(organization_id, "document.association.link")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(lambda _: invoke(), range(2)))

    assert first.id == second.id
    assert service.link(command, request, principal(organization_id, "document.association.link")).id == first.id
    with app.state.yarvis.persistence.create_session() as session:
        persisted_document = session.get(Document, document.id)
        assert persisted_document.version == document.version
        assert persisted_document.lifecycle_status == document.lifecycle_status
        assert session.get(Organization, organization_id).status == "active"
        assert link_counts(session, organization_id, document.id) == (1, 1, 1)
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_not(None),
            )
        ) == 0


def test_mismatched_concurrent_link_conflicts_with_winning_receipt(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI link mismatched race")
    site = Site(id=uuid4(), organization_id=organization_id, reference="race-site")
    site_id = site.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(site)
        session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "mismatched-race-create")
    key = "mismatched-race-link"
    commands = (
        DocumentAssociationCommand(document.id, "organization", organization_id),
        DocumentAssociationCommand(document.id, "site", site_id),
    )
    barrier = Barrier(2)

    def invoke(command):
        barrier.wait()
        try:
            result = DocumentRegistryService(app.state.yarvis.persistence).link(
                command, metadata(key), principal(organization_id, "document.association.link")
            )
            return "success", command, result
        except ApplicationError as error:
            return "conflict", command, error

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(invoke, commands))

    assert sorted(outcome[0] for outcome in outcomes) == ["conflict", "success"]
    winner = next(outcome for outcome in outcomes if outcome[0] == "success")
    loser = next(outcome for outcome in outcomes if outcome[0] == "conflict")
    assert loser[2].code == ApplicationErrorCode.CONFLICT
    assert service.link(
        winner[1], metadata(key), principal(organization_id, "document.association.link")
    ).id == winner[2].id
    with pytest.raises(ApplicationError) as error:
        service.link(loser[1], metadata(key), principal(organization_id, "document.association.link"))
    assert error.value.code == ApplicationErrorCode.CONFLICT

    expected_fingerprint = sha256(
        dumps(
            {
                "contract_id": "IC-DOCUMENT-CMD-005",
                "organization_id": str(organization_id),
                "document_id": str(document.id),
                "subject_type": winner[1].subject_type,
                "subject_id": str(winner[1].subject_id),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    with app.state.yarvis.persistence.create_session() as session:
        receipt = session.scalar(
            select(DocumentCommandIdempotency).where(
                DocumentCommandIdempotency.organization_id == organization_id,
                DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-005",
                DocumentCommandIdempotency.idempotency_key == key,
            )
        )
        assert receipt.request_fingerprint == expected_fingerprint
        assert receipt.aggregate_id == winner[2].id
        assert link_counts(session, organization_id, document.id) == (1, 1, 1)
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_not(None),
            )
        ) == 0
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"
        assert session.get(Site, site_id).reference == "race-site"


def test_different_key_concurrent_link_converges_without_duplicate_receipt(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI link duplicate race")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "duplicate-race-create")
    command = DocumentAssociationCommand(document.id, "organization", organization_id)
    keys = ("duplicate-race-one", "duplicate-race-two")
    barrier = Barrier(2)

    def invoke(key):
        barrier.wait()
        result = DocumentRegistryService(app.state.yarvis.persistence).link(
            command, metadata(key), principal(organization_id, "document.association.link")
        )
        return key, result

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(invoke, keys))

    assert outcomes[0][1].id == outcomes[1][1].id
    with app.state.yarvis.persistence.create_session() as session:
        receipt = session.scalar(
            select(DocumentCommandIdempotency).where(
                DocumentCommandIdempotency.organization_id == organization_id,
                DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-005",
            )
        )
        assert receipt.idempotency_key in keys
        winning_key = receipt.idempotency_key
        losing_key = next(key for key in keys if key != winning_key)
        assert receipt.aggregate_id == outcomes[0][1].id
        assert link_counts(session, organization_id, document.id) == (1, 1, 1)
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_not(None),
            )
        ) == 0
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"

    assert service.link(
        command, metadata(winning_key), principal(organization_id, "document.association.link")
    ).id == outcomes[0][1].id
    assert service.link(
        command, metadata(losing_key), principal(organization_id, "document.association.link")
    ).id == outcomes[0][1].id
    with app.state.yarvis.persistence.create_session() as session:
        assert link_counts(session, organization_id, document.id) == (1, 1, 1)

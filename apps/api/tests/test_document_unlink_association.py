from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import (
    CreateDocumentCommand,
    DocumentAssociationCommand,
    UnlinkDocumentAssociationCommand,
)
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.document_registry import Document, DocumentAssociation, DocumentCommandIdempotency
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.operational_context import Site
from yarvis_api.services.document_registry import DocumentRegistryService


class _FailingCommitRuntime:
    def __init__(self, runtime):
        self.runtime = runtime

    def create_session(self):
        session = self.runtime.create_session()
        session.commit = lambda: (_ for _ in ()).throw(RuntimeError("forced commit failure"))
        return session


def principal(organization_id, authority):
    return AuthenticatedPrincipal("actor", str(organization_id), (), (), authority, "test", datetime.now(timezone.utc), False)


def metadata(key):
    return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key=key)


def create_command():
    return CreateDocumentCommand("Unlinked document", "general", "organization", "text/plain", "sha256", "a" * 64, "external", None, "urn:unlink", "manual", {}, "unlink.txt", 1)


def create_organization(app, name):
    organization = Organization(id=uuid4(), legal_name=name, display_name=name)
    organization_id = organization.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(organization)
        session.commit()
    return organization_id


def create_document(service, organization_id, key):
    return service.create(create_command(), metadata(key), principal(organization_id, "document.create"))


def link(service, document_id, organization_id, key):
    return service.link(
        DocumentAssociationCommand(document_id, "organization", organization_id),
        metadata(key),
        principal(organization_id, "document.association.link"),
    )


def unlink_counts(session, organization_id, document_id=None):
    associations = select(func.count()).select_from(DocumentAssociation).where(
        DocumentAssociation.organization_id == organization_id
    )
    events = select(func.count()).select_from(DomainEvent).where(
        DomainEvent.organization_id == organization_id,
        DomainEvent.event_type == "document.unassociated",
    )
    receipts = select(func.count()).select_from(DocumentCommandIdempotency).where(
        DocumentCommandIdempotency.organization_id == organization_id,
        DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-006",
    )
    if document_id:
        associations = associations.where(DocumentAssociation.document_id == document_id)
        events = events.where(DomainEvent.aggregate_id == document_id)
    return session.scalar(associations), session.scalar(events), session.scalar(receipts)


def test_governed_unlink_replays_and_preserves_history(test_database):
    from yarvis_api.main import app

    organization = Organization(id=uuid4(), legal_name="DI unlink organization", display_name="DI unlink organization")
    organization_id = organization.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(organization)
        session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = service.create(create_command(), metadata("unlink-create"), principal(organization_id, "document.create"))
    linked = service.link(DocumentAssociationCommand(document.id, "organization", organization_id), metadata("unlink-link"), principal(organization_id, "document.association.link"))
    command = UnlinkDocumentAssociationCommand(document.id, linked.id)
    first = service.unlink(command, metadata("unlink-key"), principal(organization_id, "document.association.unlink"))
    replay = service.unlink(command, metadata("unlink-key"), principal(organization_id, "document.association.unlink"))

    assert first.id == replay.id == linked.id
    assert first.unlinked_at == replay.unlinked_at
    assert first.unlinked_by_subject_id == "actor"
    with pytest.raises(ApplicationError) as error:
        service.unlink(UnlinkDocumentAssociationCommand(document.id, uuid4()), metadata("unlink-key"), principal(organization_id, "document.association.unlink"))
    assert error.value.code == ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as session:
        association = session.get(DocumentAssociation, linked.id)
        assert association.unlinked_at is not None and association.unlinked_by_subject_id == "actor"
        assert session.scalar(select(func.count()).select_from(DocumentAssociation).where(DocumentAssociation.id == linked.id)) == 1
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document.id, DomainEvent.event_type == "document.unassociated")) == 1
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id == organization_id, DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-006", DocumentCommandIdempotency.idempotency_key == "unlink-key")) == 1


@pytest.mark.parametrize("authority", ["", "document.association.link"])
def test_unlink_requires_exact_authority_without_side_effects(test_database, authority):
    from yarvis_api.main import app

    organization_id = create_organization(app, f"DI unlink authority {authority or 'missing'}")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, f"authority-create-{authority or 'missing'}")
    association = link(service, document.id, organization_id, f"authority-link-{authority or 'missing'}")
    with pytest.raises((ApplicationError, ValueError)):
        service.unlink(
            UnlinkDocumentAssociationCommand(document.id, association.id),
            metadata(f"authority-unlink-{authority or 'missing'}"),
            principal(organization_id, authority),
        )
    with app.state.yarvis.persistence.create_session() as session:
        current = session.get(DocumentAssociation, association.id)
        assert current.unlinked_at is None
        assert unlink_counts(session, organization_id, document.id) == (1, 0, 0)


def test_unlink_conceals_missing_and_foreign_documents_without_side_effects(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI unlink document first")
    second_id = create_organization(app, "DI unlink document second")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    foreign_document = create_document(service, second_id, "foreign-document-create")
    foreign_association = link(service, foreign_document.id, second_id, "foreign-document-link")
    for document_id, association_id, key in ((uuid4(), uuid4(), "missing-document"), (foreign_document.id, foreign_association.id, "foreign-document")):
        with pytest.raises(ApplicationError) as error:
            service.unlink(UnlinkDocumentAssociationCommand(document_id, association_id), metadata(key), principal(first_id, "document.association.unlink"))
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert error.value.message == "document not found"
    with app.state.yarvis.persistence.create_session() as session:
        assert unlink_counts(session, first_id) == (0, 0, 0)
        assert session.get(DocumentAssociation, foreign_association.id).unlinked_at is None
        assert unlink_counts(session, second_id, foreign_document.id) == (1, 0, 0)


def test_unlink_conceals_missing_foreign_other_document_and_inactive_associations(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI unlink association concealment")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first_document = create_document(service, organization_id, "association-first-document")
    second_document = create_document(service, organization_id, "association-second-document")
    first_association = link(service, first_document.id, organization_id, "association-first-link")
    second_association = link(service, second_document.id, organization_id, "association-second-link")
    service.unlink(UnlinkDocumentAssociationCommand(first_document.id, first_association.id), metadata("make-inactive"), principal(organization_id, "document.association.unlink"))
    before = None
    with app.state.yarvis.persistence.create_session() as session:
        before = unlink_counts(session, organization_id)
    for association_id, key in ((uuid4(), "missing-association"), (second_association.id, "other-document"), (first_association.id, "inactive-association")):
        with pytest.raises(ApplicationError) as error:
            service.unlink(UnlinkDocumentAssociationCommand(first_document.id, association_id), metadata(key), principal(organization_id, "document.association.unlink"))
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert error.value.message == "document not found"
    with app.state.yarvis.persistence.create_session() as session:
        assert unlink_counts(session, organization_id) == before
        assert session.get(DocumentAssociation, second_association.id).unlinked_at is None


def test_unlink_idempotency_is_organization_scoped_and_replay_is_historical(test_database):
    from yarvis_api.main import app

    first_id = create_organization(app, "DI unlink scope first")
    second_id = create_organization(app, "DI unlink scope second")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first_document = create_document(service, first_id, "scope-first-create")
    second_document = create_document(service, second_id, "scope-second-create")
    first_association = link(service, first_document.id, first_id, "scope-first-link")
    second_association = link(service, second_document.id, second_id, "scope-second-link")
    key = "shared-unlink-key"
    first = service.unlink(UnlinkDocumentAssociationCommand(first_document.id, first_association.id), metadata(key), principal(first_id, "document.association.unlink"))
    second = service.unlink(UnlinkDocumentAssociationCommand(second_document.id, second_association.id), metadata(key), principal(second_id, "document.association.unlink"))
    first_replay = service.unlink(UnlinkDocumentAssociationCommand(first_document.id, first_association.id), metadata(key), principal(first_id, "document.association.unlink"))
    second_replay = service.unlink(UnlinkDocumentAssociationCommand(second_document.id, second_association.id), metadata(key), principal(second_id, "document.association.unlink"))
    assert (first_replay.id, first_replay.unlinked_at, first_replay.unlinked_by_subject_id) == (first.id, first.unlinked_at, "actor")
    assert (second_replay.id, second_replay.unlinked_at, second_replay.unlinked_by_subject_id) == (second.id, second.unlinked_at, "actor")
    with app.state.yarvis.persistence.create_session() as session:
        assert unlink_counts(session, first_id, first_document.id) == (1, 1, 1)
        assert unlink_counts(session, second_id, second_document.id) == (1, 1, 1)
        assert session.get(DocumentAssociation, first_association.id).unlinked_at == first.unlinked_at
        assert session.get(DocumentAssociation, second_association.id).unlinked_at == second.unlinked_at


def test_unlink_commit_failure_rolls_back_and_retry_replays(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI unlink rollback")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "rollback-create")
    association = link(service, document.id, organization_id, "rollback-link")
    command = UnlinkDocumentAssociationCommand(document.id, association.id)
    request = metadata("rollback-unlink")

    with pytest.raises(RuntimeError, match="forced commit failure"):
        DocumentRegistryService(_FailingCommitRuntime(app.state.yarvis.persistence)).unlink(
            command, request, principal(organization_id, "document.association.unlink")
        )

    with app.state.yarvis.persistence.create_session() as session:
        current_association = session.get(DocumentAssociation, association.id)
        assert current_association.unlinked_at is None
        assert current_association.unlinked_by_subject_id is None
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"
        assert unlink_counts(session, organization_id, document.id) == (1, 0, 0)

    first = service.unlink(command, request, principal(organization_id, "document.association.unlink"))
    replay = service.unlink(command, request, principal(organization_id, "document.association.unlink"))
    assert (replay.id, replay.unlinked_at, replay.unlinked_by_subject_id) == (
        first.id,
        first.unlinked_at,
        first.unlinked_by_subject_id,
    )
    with app.state.yarvis.persistence.create_session() as session:
        current_association = session.get(DocumentAssociation, association.id)
        assert current_association.unlinked_at == first.unlinked_at
        assert current_association.unlinked_by_subject_id == "actor"
        assert unlink_counts(session, organization_id, document.id) == (1, 1, 1)


def test_matching_concurrent_unlink_replays_winning_receipt(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI unlink matching race")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "matching-race-create")
    association = link(service, document.id, organization_id, "matching-race-link")
    command = UnlinkDocumentAssociationCommand(document.id, association.id)
    request = metadata("matching-race-unlink")
    barrier = Barrier(2)

    def invoke():
        barrier.wait()
        return DocumentRegistryService(app.state.yarvis.persistence).unlink(
            command, request, principal(organization_id, "document.association.unlink")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(lambda _: invoke(), range(2)))

    assert (first.id, first.unlinked_at, first.unlinked_by_subject_id) == (
        second.id,
        second.unlinked_at,
        second.unlinked_by_subject_id,
    )
    assert service.unlink(command, request, principal(organization_id, "document.association.unlink")).id == first.id
    with app.state.yarvis.persistence.create_session() as session:
        current = session.get(DocumentAssociation, association.id)
        assert current.unlinked_at == first.unlinked_at
        assert current.unlinked_by_subject_id == "actor"
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_(None),
            )
        ) == 0
        assert unlink_counts(session, organization_id, document.id) == (1, 1, 1)
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"


def test_mismatched_concurrent_unlink_conflicts_with_winning_receipt(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI unlink mismatched race")
    site = Site(id=uuid4(), organization_id=organization_id, reference="unlink-race-site")
    site_id = site.id
    with app.state.yarvis.persistence.create_session() as session:
        session.add(site)
        session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "mismatched-race-create")
    organization_association = link(service, document.id, organization_id, "mismatched-race-organization-link")
    site_association = service.link(
        DocumentAssociationCommand(document.id, "site", site_id),
        metadata("mismatched-race-site-link"),
        principal(organization_id, "document.association.link"),
    )
    key = "mismatched-race-unlink"
    commands = (
        UnlinkDocumentAssociationCommand(document.id, organization_association.id),
        UnlinkDocumentAssociationCommand(document.id, site_association.id),
    )
    barrier = Barrier(2)

    def invoke(command):
        barrier.wait()
        try:
            result = DocumentRegistryService(app.state.yarvis.persistence).unlink(
                command, metadata(key), principal(organization_id, "document.association.unlink")
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
    assert service.unlink(winner[1], metadata(key), principal(organization_id, "document.association.unlink")).id == winner[2].id
    with pytest.raises(ApplicationError) as error:
        service.unlink(loser[1], metadata(key), principal(organization_id, "document.association.unlink"))
    assert error.value.code == ApplicationErrorCode.CONFLICT

    expected_fingerprint = sha256(
        dumps(
            {
                "contract_id": "IC-DOCUMENT-CMD-006",
                "organization_id": str(organization_id),
                "document_id": str(document.id),
                "association_id": str(winner[1].association_id),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    with app.state.yarvis.persistence.create_session() as session:
        receipt = session.scalar(
            select(DocumentCommandIdempotency).where(
                DocumentCommandIdempotency.organization_id == organization_id,
                DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-006",
                DocumentCommandIdempotency.idempotency_key == key,
            )
        )
        assert receipt.request_fingerprint == expected_fingerprint
        assert receipt.aggregate_id == winner[2].id
        winner_association = session.get(DocumentAssociation, winner[2].id)
        loser_association_id = loser[1].association_id
        assert winner_association.unlinked_at is not None
        assert session.get(DocumentAssociation, loser_association_id).unlinked_at is None
        assert unlink_counts(session, organization_id, document.id) == (2, 1, 1)
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_(None),
            )
        ) == 1
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"
        assert session.get(Site, site_id).reference == "unlink-race-site"


def test_different_key_concurrent_unlink_conceals_inactive_association(test_database):
    from yarvis_api.main import app

    organization_id = create_organization(app, "DI unlink duplicate race")
    service = DocumentRegistryService(app.state.yarvis.persistence)
    document = create_document(service, organization_id, "duplicate-race-create")
    association = link(service, document.id, organization_id, "duplicate-race-link")
    command = UnlinkDocumentAssociationCommand(document.id, association.id)
    keys = ("duplicate-race-one", "duplicate-race-two")
    barrier = Barrier(2)

    def invoke(key):
        barrier.wait()
        try:
            result = DocumentRegistryService(app.state.yarvis.persistence).unlink(
                command, metadata(key), principal(organization_id, "document.association.unlink")
            )
            return "success", key, result
        except ApplicationError as error:
            return "not_found", key, error

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(invoke, keys))

    assert sorted(outcome[0] for outcome in outcomes) == ["not_found", "success"]
    winner = next(outcome for outcome in outcomes if outcome[0] == "success")
    loser = next(outcome for outcome in outcomes if outcome[0] == "not_found")
    assert loser[2].code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert loser[2].message == "document not found"
    assert service.unlink(command, metadata(winner[1]), principal(organization_id, "document.association.unlink")).id == winner[2].id
    with pytest.raises(ApplicationError) as error:
        service.unlink(command, metadata(loser[1]), principal(organization_id, "document.association.unlink"))
    assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    with app.state.yarvis.persistence.create_session() as session:
        current = session.get(DocumentAssociation, association.id)
        assert current.unlinked_at == winner[2].unlinked_at
        assert current.unlinked_by_subject_id == winner[2].unlinked_by_subject_id == "actor"
        assert session.scalar(
            select(func.count()).select_from(DocumentAssociation).where(
                DocumentAssociation.document_id == document.id,
                DocumentAssociation.unlinked_at.is_(None),
            )
        ) == 0
        assert unlink_counts(session, organization_id, document.id) == (1, 1, 1)
        assert session.get(Document, document.id).version == document.version
        assert session.get(Organization, organization_id).status == "active"

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import func, select
from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import AddDocumentVersionCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.document_registry import Document, DocumentCommandIdempotency, DocumentVersion
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.services.document_registry import DocumentRegistryService
def p(o):return AuthenticatedPrincipal("actor",str(o),(),(),"document.version.add","test",datetime.now(timezone.utc),False)
def m(k):return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=k,expected_aggregate_version=1)
def c(document_id, checksum="a" * 64):
    return AddDocumentVersionCommand(
        document_id=document_id,
        media_type="text/plain",
        checksum_algorithm="sha256",
        checksum_value=checksum,
        storage_provider="local",
        storage_key="documents/a.txt",
        external_reference=None,
        source_kind="manual",
        provenance={"source": "test"},
        original_filename="a.txt",
        byte_size=42,
        source_reference="source-1",
    )
def test_first_document_version_replays_and_conflicts(test_database):
    from yarvis_api.main import app

    oid = uuid4()
    document_id = uuid4()

    org = Organization(
        id=oid,
        legal_name="DI version",
        display_name="DI version",
    )

    document = Document(
        id=document_id,
        organization_id=oid,
        title="Document",
        classification="general",
        visibility="organization",
        created_by_subject_id="test",
    )

    with app.state.yarvis.persistence.create_session() as session:
        session.add(org)
        session.flush()

        session.add(document)
        session.commit()

    service = DocumentRegistryService(app.state.yarvis.persistence)
    meta = m("version-key")

    first = service.add(c(document_id), meta, p(oid))
    replay = service.add(c(document_id), meta, p(oid))

    assert first.id == replay.id
    assert first.sequence == 1
    assert first.supersedes_version_id is None
    assert first.storage_key == "documents/a.txt"
    assert first.provenance == {"source": "test"}

    with pytest.raises(ApplicationError) as error:
        service.add(c(document_id, "b" * 64), meta, p(oid))

    assert error.value.code == ApplicationErrorCode.CONFLICT

    with app.state.yarvis.persistence.create_session() as session:
        current = session.get(Document, document_id)

        assert current is not None
        assert current.current_version_id == first.id
        assert current.version == 2

        assert (
            session.scalar(
                select(func.count())
                .select_from(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
            )
            == 1
        )

        assert (
            session.scalar(
                select(func.count())
                .select_from(DomainEvent)
                .where(
                    DomainEvent.aggregate_id == document_id,
                    DomainEvent.event_type == "document.version_added",
                )
            )
            == 1
        )

        assert (
            session.scalar(
                select(func.count())
                .select_from(DocumentCommandIdempotency)
                .where(DocumentCommandIdempotency.aggregate_id == first.id)
            )
            == 1
        )


def test_later_version_preserves_lineage_and_replays(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI later", display_name="DI later")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first = service.add(c(document_id), m("first"), p(oid))
    second_meta = RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="second", expected_aggregate_version=2)
    second = service.add(c(document_id, "b" * 64), second_meta, p(oid))
    assert service.add(c(document_id, "b" * 64), second_meta, p(oid)).id == second.id
    with app.state.yarvis.persistence.create_session() as session:
        versions = session.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.sequence)).all()
        document = session.get(Document, document_id)
        assert [version.sequence for version in versions] == [1, 2]
        assert second.supersedes_version_id == first.id
        assert versions[0].checksum_value == "a" * 64 and versions[0].supersedes_version_id is None
        assert document.current_version_id == second.id and document.version == 3


@pytest.mark.parametrize("authority", ["", "document.read"])
def test_add_version_requires_exact_authority(test_database, authority):
    from yarvis_api.main import app
    oid = uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI version auth" + authority, display_name="DI version auth")); session.commit()
    with pytest.raises((ApplicationError, ValueError)):
        principal = AuthenticatedPrincipal("actor", str(oid), (), (), authority, "test", datetime.now(timezone.utc), False)
        DocumentRegistryService(app.state.yarvis.persistence).add(c(uuid4()), m(uuid4().hex), principal)
    with app.state.yarvis.persistence.create_session() as session:
        assert session.scalar(select(func.count()).select_from(DocumentVersion)) == 0
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type == "document.version_added")) == 0
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003")) == 0


def test_add_version_conceals_missing_and_foreign_document(test_database):
    from yarvis_api.main import app
    own, foreign = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all([Organization(id=own, legal_name="DI version own", display_name="DI version own"), Organization(id=foreign, legal_name="DI version foreign", display_name="DI version foreign")]); session.commit()
    document = Document(id=uuid4(), organization_id=foreign, title="Foreign", classification="general", visibility="organization", created_by_subject_id="test")
    document_id = document.id
    with app.state.yarvis.persistence.create_session() as session: session.add(document); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    for target_document_id, key in ((uuid4(), "missing"), (document_id, "foreign")):
        with pytest.raises(ApplicationError) as error: service.add(c(target_document_id), m(key), p(own))
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND and error.value.message == "document not found"
    with app.state.yarvis.persistence.create_session() as session:
        current = session.get(Document, document_id)
        assert current.version == 1 and current.current_version_id is None
        assert session.scalar(select(func.count()).select_from(DocumentVersion)) == 0
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type == "document.version_added")) == 0
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003")) == 0


def test_add_version_idempotency_is_organization_scoped(test_database):
    from yarvis_api.main import app
    one, two = uuid4(), uuid4(); first_id, second_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all([Organization(id=one, legal_name="DI version scope one", display_name="DI version scope one"), Organization(id=two, legal_name="DI version scope two", display_name="DI version scope two")]); session.flush()
        session.add_all([Document(id=first_id, organization_id=one, title="One", classification="general", visibility="organization", created_by_subject_id="test"), Document(id=second_id, organization_id=two, title="Two", classification="general", visibility="organization", created_by_subject_id="test")]); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence); key = "same-version-key"
    first = service.add(c(first_id), m(key), p(one)); second = service.add(c(second_id), m(key), p(two))
    assert service.add(c(first_id), m(key), p(one)).id == first.id
    assert service.add(c(second_id), m(key), p(two)).id == second.id
    with app.state.yarvis.persistence.create_session() as session:
        for organization_id, document_id, version_id in ((one, first_id, first.id), (two, second_id, second.id)):
            document = session.get(Document, document_id)
            assert document.current_version_id == version_id and document.version == 2
            assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.organization_id == organization_id)) == 1
            assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == organization_id, DomainEvent.event_type == "document.version_added")) == 1
            assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id == organization_id, DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003", DocumentCommandIdempotency.idempotency_key == key)) == 1


def test_add_version_stale_non_replay_has_no_side_effects(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI version stale", display_name="DI version stale")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first = service.add(c(document_id), m("first-stale"), p(oid))
    with pytest.raises(ApplicationError) as error:
        service.add(c(document_id, "b" * 64), m("stale-fresh"), p(oid))
    assert error.value.code == ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.current_version_id == first.id and document.version == 2
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 1
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 1
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.idempotency_key == "stale-fresh")) == 0


def test_add_version_replay_precedes_stale_validation(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI version replay stale", display_name="DI version replay stale")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first_meta = m("replay-first"); first = service.add(c(document_id), first_meta, p(oid))
    second_meta = RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="replay-second", expected_aggregate_version=2)
    second = service.add(c(document_id, "b" * 64), second_meta, p(oid))
    assert service.add(c(document_id), first_meta, p(oid)).id == first.id
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.current_version_id == second.id and document.version == 3
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 2
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 2
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003")) == 2


def test_add_version_mismatched_replay_precedes_stale_validation(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI version mismatch stale", display_name="DI version mismatch stale")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first_meta = m("mismatch-first"); service.add(c(document_id), first_meta, p(oid))
    second_meta = RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="mismatch-second", expected_aggregate_version=2)
    second = service.add(c(document_id, "b" * 64), second_meta, p(oid))
    with pytest.raises(ApplicationError) as error: service.add(c(document_id, "c" * 64), first_meta, p(oid))
    assert error.value.code == ApplicationErrorCode.CONFLICT and "idempotency key" in error.value.message
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.current_version_id == second.id and document.version == 3
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 2
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 2
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003")) == 2


def test_add_version_archived_lifecycle_and_prearchive_replay(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI version archived", display_name="DI version archived")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    version_meta = m("prearchive-version"); version = service.add(c(document_id), version_meta, p(oid))
    archive_principal = AuthenticatedPrincipal("actor", str(oid), (), (), "document.archive", "test", datetime.now(timezone.utc), False)
    archive_meta = RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="archive", expected_aggregate_version=2)
    archived = service.archive(document_id, archive_meta, archive_principal)
    with pytest.raises(ApplicationError) as fresh: service.add(c(document_id, "b" * 64), RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="fresh-archived", expected_aggregate_version=3), p(oid))
    assert fresh.value.code == ApplicationErrorCode.CONFLICT
    assert service.add(c(document_id), version_meta, p(oid)).id == version.id
    with pytest.raises(ApplicationError) as mismatch: service.add(c(document_id, "c" * 64), version_meta, p(oid))
    assert mismatch.value.code == ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.lifecycle_status == "archived" and document.archived_at == archived.archived_at and document.current_version_id == version.id and document.version == 3
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 1
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 1
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.contract_id == "IC-DOCUMENT-CMD-003")) == 1


@pytest.mark.parametrize("storage_key,external_reference,checksum_algorithm,checksum_value,byte_size", [("/tmp/a",None,"sha256","a"*64,1),(r"C:\\a",None,"sha256","a"*64,1),(r"\\\\server\\a",None,"sha256","a"*64,1),("../a",None,"sha256","a"*64,1),(None,None,"sha256","a"*64,1),("a",None,"","a",1),("a",None,"sha256","",1),("a",None,"sha256","a",-1)])
def test_add_version_rejects_invalid_storage_checksum_and_size(test_database, storage_key, external_reference, checksum_algorithm, checksum_value, byte_size):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI validation " + uuid4().hex, display_name="DI validation")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    command = AddDocumentVersionCommand(document_id, "text/plain", checksum_algorithm, checksum_value, "local", storage_key, external_reference, "manual", {}, "a.txt", byte_size, None)
    with pytest.raises(ApplicationError) as error: DocumentRegistryService(app.state.yarvis.persistence).add(command, m("invalid"), p(oid))
    assert error.value.code == ApplicationErrorCode.VALIDATION_FAILED
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.version == 1 and document.current_version_id is None
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 0
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 0
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.idempotency_key == "invalid")) == 0


def test_add_version_accepts_external_reference_only(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI external version", display_name="DI external version")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    command = AddDocumentVersionCommand(document_id, "text/plain", "sha256", "a" * 64, "external", None, "urn:example:artifact", "manual", {"source":"external"}, "a.txt", 42, "source")
    version = DocumentRegistryService(app.state.yarvis.persistence).add(command, m("external-only"), p(oid))
    assert version.storage_key is None and version.external_reference == "urn:example:artifact"
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.current_version_id == version.id and document.version == 2
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 1
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id == version.id)) == 1


@pytest.mark.parametrize("changed", ["checksum", "storage", "size"])
def test_add_version_fingerprint_is_sensitive_to_semantic_fields(test_database, changed):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI fingerprint " + changed, display_name="DI fingerprint")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence); meta = m("sensitive")
    first = service.add(c(document_id), meta, p(oid))
    values = {"checksum": c(document_id, "b" * 64), "storage": AddDocumentVersionCommand(document_id,"text/plain","sha256","a"*64,"local","documents/b.txt",None,"manual",{"source":"test"},"a.txt",42,"source-1"), "size": AddDocumentVersionCommand(document_id,"text/plain","sha256","a"*64,"local","documents/a.txt",None,"manual",{"source":"test"},"a.txt",43,"source-1")}
    with pytest.raises(ApplicationError) as error: service.add(values[changed], meta, p(oid))
    assert error.value.code == ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as session:
        document = session.get(Document, document_id)
        assert document.current_version_id == first.id and document.version == 2
        assert session.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document_id)) == 1
        assert session.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id == document_id, DomainEvent.event_type == "document.version_added")) == 1
        assert session.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id == first.id)) == 1


def test_later_versions_preserve_historical_fields(test_database):
    from yarvis_api.main import app
    oid, document_id = uuid4(), uuid4()
    with app.state.yarvis.persistence.create_session() as session:
        session.add(Organization(id=oid, legal_name="DI immutable", display_name="DI immutable")); session.flush()
        session.add(Document(id=document_id, organization_id=oid, title="Document", classification="general", visibility="organization", created_by_subject_id="test")); session.commit()
    service = DocumentRegistryService(app.state.yarvis.persistence)
    first = service.add(c(document_id), m("immutable-first"), p(oid))
    with app.state.yarvis.persistence.create_session() as session: before = session.get(DocumentVersion, first.id); snapshot = (before.checksum_value, before.storage_key, before.provenance, before.original_filename, before.byte_size, before.created_at, before.supersedes_version_id)
    second_meta = RequestMetadata(datetime.now(timezone.utc), str(uuid4()), command_id=str(uuid4()), idempotency_key="immutable-second", expected_aggregate_version=2)
    second = service.add(c(document_id, "b" * 64), second_meta, p(oid))
    with app.state.yarvis.persistence.create_session() as session:
        first_after = session.get(DocumentVersion, first.id); document = session.get(Document, document_id)
        assert (first_after.checksum_value, first_after.storage_key, first_after.provenance, first_after.original_filename, first_after.byte_size, first_after.created_at, first_after.supersedes_version_id) == snapshot
        assert second.supersedes_version_id == first.id and document.current_version_id == second.id and document.version == 3
        assert [item.sequence for item in session.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.sequence)).all()] == [1, 2]

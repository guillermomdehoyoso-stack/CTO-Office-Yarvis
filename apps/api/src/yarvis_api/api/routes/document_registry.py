"""Governed metadata-only Document Registry API."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.document_registry import AddDocumentVersionCommand, CreateDocumentCommand, DocumentAssociationCommand, UnlinkDocumentAssociationCommand, UpdateDocumentCommand
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.schemas.document_registry import AssociationRequest, DocumentArchiveRequest, DocumentAssociationRead, DocumentCreateRequest, DocumentPage, DocumentRead, DocumentUnlinkRequest, DocumentUpdateRequest, DocumentVersionRead, DocumentVersionRequest


router = APIRouter(prefix="/documents", tags=["document-registry"])


def _principal(request: Request):
    return request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))


def _command_metadata(payload, command_id: str) -> RequestMetadata:
    return RequestMetadata(utc_now(), str(payload.correlation_id), command_id=command_id, causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key, expected_aggregate_version=getattr(payload, "expected_version", None))


def _query_metadata(principal, query_id: str) -> RequestMetadata:
    return RequestMetadata(utc_now(), principal.correlation_id or str(uuid4()), query_id=query_id)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreateRequest, request: Request) -> DocumentRead:
    return request.app.state.yarvis.document_registry_service.create(CreateDocumentCommand(payload.title, payload.classification, payload.visibility, payload.media_type, payload.checksum_algorithm, payload.checksum_value, payload.storage_provider, payload.storage_key, payload.external_reference, payload.source_kind, payload.provenance, payload.original_filename, payload.byte_size, payload.source_reference), _command_metadata(payload, "create_document"), _principal(request))


@router.patch("/{document_id:uuid}", response_model=DocumentRead)
def update_document(document_id: UUID, payload: DocumentUpdateRequest, request: Request) -> DocumentRead:
    return request.app.state.yarvis.document_registry_service.update(UpdateDocumentCommand(document_id, payload.expected_version, payload.title, payload.classification, payload.visibility), _command_metadata(payload, "update_document_metadata"), _principal(request))


@router.post("/{document_id:uuid}/versions", response_model=DocumentVersionRead, status_code=status.HTTP_201_CREATED)
def add_version(document_id: UUID, payload: DocumentVersionRequest, request: Request) -> DocumentVersionRead:
    return request.app.state.yarvis.document_registry_service.add(AddDocumentVersionCommand(document_id, payload.media_type, payload.checksum_algorithm, payload.checksum_value, payload.storage_provider, payload.storage_key, payload.external_reference, payload.source_kind, payload.provenance, payload.original_filename, payload.byte_size, payload.source_reference), _command_metadata(payload, "add_document_version"), _principal(request))


@router.post("/{document_id:uuid}/archive", response_model=DocumentRead)
def archive_document(document_id: UUID, payload: DocumentArchiveRequest, request: Request) -> DocumentRead:
    return request.app.state.yarvis.document_registry_service.archive(document_id, _command_metadata(payload, "archive_document"), _principal(request))


@router.post("/{document_id:uuid}/associations", response_model=DocumentAssociationRead, status_code=status.HTTP_201_CREATED)
def link_association(document_id: UUID, payload: AssociationRequest, request: Request) -> DocumentAssociationRead:
    return request.app.state.yarvis.document_registry_service.link(DocumentAssociationCommand(document_id, payload.subject_type, payload.subject_id), _command_metadata(payload, "link_document_association"), _principal(request))


@router.post("/{document_id:uuid}/associations/{association_id:uuid}/unlink", response_model=DocumentAssociationRead)
def unlink_association(document_id: UUID, association_id: UUID, payload: DocumentUnlinkRequest, request: Request) -> DocumentAssociationRead:
    return request.app.state.yarvis.document_registry_service.unlink(UnlinkDocumentAssociationCommand(document_id, association_id), _command_metadata(payload, "unlink_document_association"), _principal(request))


@router.get("/{document_id:uuid}", response_model=DocumentRead)
def get_document(document_id: UUID, request: Request, db: Session = Depends(get_db)) -> DocumentRead:
    principal = _principal(request)
    return request.app.state.yarvis.document_registry_query_service.get(db, document_id, principal, _query_metadata(principal, "get_document"))


@router.get("/{document_id:uuid}/versions", response_model=list[DocumentVersionRead])
def get_versions(document_id: UUID, request: Request, db: Session = Depends(get_db)) -> list[DocumentVersionRead]:
    principal = _principal(request)
    return request.app.state.yarvis.document_registry_query_service.versions(db, document_id, principal, _query_metadata(principal, "get_document_versions"))


@router.get("/{document_id:uuid}/associations", response_model=list[DocumentAssociationRead])
def get_associations(document_id: UUID, request: Request, db: Session = Depends(get_db)) -> list[DocumentAssociationRead]:
    principal = _principal(request)
    return request.app.state.yarvis.document_registry_query_service.associations(db, document_id, principal, _query_metadata(principal, "get_document_associations"))


@router.get("/subjects/{subject_type}/{subject_id}", response_model=DocumentPage)
def get_documents_by_subject(subject_type: str, subject_id: UUID, request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)) -> DocumentPage:
    principal = _principal(request)
    return request.app.state.yarvis.document_registry_query_service.by_subject(db, subject_type, subject_id, principal, _query_metadata(principal, "get_documents_by_subject"), limit, offset)

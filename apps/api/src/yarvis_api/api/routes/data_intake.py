from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.config import get_settings
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.observation_engine import DocumentRecord, Observation, SourceRecord
from yarvis_api.schemas.data_intake import (
    DataIntakeConfirmRequest,
    DataIntakeDocumentRead,
    DataIntakePreviewResponse,
    DataIntakeProcessResponse,
    DataIntakeRejectRequest,
    DataIntakeReprocessRequest,
    DataIntakeUploadResponse,
)
from yarvis_api.services.data_intake import (
    DeterministicReportClassifier,
    DocumentParserRegistry,
    FileInspectionService,
    DataIntakePreviewService,
)
from yarvis_api.storage.document_repository import LocalDocumentRepository

router = APIRouter(prefix="/data-intake", tags=["data-intake"])
settings = get_settings()
repository = LocalDocumentRepository(settings.document_storage_root)
inspection_service = FileInspectionService(max_upload_size_bytes=settings.max_upload_size_bytes)
preview_service = DataIntakePreviewService(
    repository=repository,
    parser_registry=DocumentParserRegistry(preview_row_limit=settings.preview_row_limit),
    classifier=DeterministicReportClassifier(),
)


@router.post("/documents", response_model=DataIntakeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form(default="manual_upload"),
    source_name: str = Form(default="Manual Upload"),
    classification: str = Form(default="confidential"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    inspection = inspection_service.inspect(filename=file.filename or "document", content=content, content_type=file.content_type)

    source = SourceRecord(
        source_type=source_type,
        external_source_id=None,
        source_name=source_name,
        received_at=utc_now(),
        metadata_json={"upload_filename": file.filename, "byte_size": inspection.byte_size},
        classification=classification,
    )
    db.add(source)
    db.flush()

    duplicate = db.scalar(select(DocumentRecord).where(DocumentRecord.file_hash == inspection.sha256).order_by(DocumentRecord.created_at.desc()))

    storage_reference = None
    duplicate_of = None
    if duplicate is None:
        storage_reference = repository.save(filename=file.filename or "document", content=content)
    else:
        duplicate_of = duplicate.id

    document = DocumentRecord(
        source_id=source.id,
        filename=file.filename,
        original_filename=file.filename,
        media_type=inspection.media_type,
        file_hash=inspection.sha256,
        byte_size=inspection.byte_size,
        storage_reference=storage_reference,
        extraction_status="pending",
        classification=classification,
        detected_file_type=inspection.content_kind,
        duplicate_of_document_id=duplicate_of,
        review_status="pending",
        metadata_json={"content_kind": inspection.content_kind},
    )
    db.add(document)
    db.flush()

    record_event(
        db,
        event_type="data_intake.document_received",
        aggregate_type="document_record",
        aggregate_id=document.id,
        payload={"source_type": source_type, "byte_size": inspection.byte_size, "media_type": inspection.media_type},
    )
    if duplicate_of:
        record_event(
            db,
            event_type="data_intake.duplicate_detected",
            aggregate_type="document_record",
            aggregate_id=document.id,
            payload={"duplicate_of_document_id": str(duplicate_of)},
        )

    db.commit()
    return DataIntakeUploadResponse(
        document_id=document.id,
        duplicate=duplicate_of is not None,
        duplicate_of_document_id=duplicate_of,
        processing_status=document.review_status,
    )


@router.get("/documents", response_model=list[DataIntakeDocumentRead])
def list_documents(
    status: str | None = None,
    report_type: str | None = None,
    source_type: str | None = None,
    received_from: datetime | None = None,
    received_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    query = select(DocumentRecord, SourceRecord).join(SourceRecord, SourceRecord.id == DocumentRecord.source_id)
    if status:
        query = query.where(DocumentRecord.review_status == status)
    if report_type:
        query = query.where(DocumentRecord.detected_report_type == report_type)
    if source_type:
        query = query.where(SourceRecord.source_type == source_type)
    if received_from:
        query = query.where(SourceRecord.received_at >= received_from)
    if received_to:
        query = query.where(SourceRecord.received_at <= received_to)
    rows = db.execute(query.order_by(DocumentRecord.created_at.desc())).all()
    return [row[0] for row in rows]


@router.get("/documents/{document_id}", response_model=DataIntakeDocumentRead)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return document


@router.post("/documents/{document_id}/process", response_model=DataIntakeProcessResponse)
def process_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    source = db.get(SourceRecord, document.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")

    if document.duplicate_of_document_id:
        document.review_status = "preview_ready"
        document.metadata_json = {
            **(document.metadata_json or {}),
            "preview": {
                "document_metadata": {"document_id": str(document.id), "filename": document.original_filename or document.filename},
                "duplicate_status": True,
                "detected_report_type": document.detected_report_type or "unknown",
                "confidence": document.classification_confidence or 0.0,
                "parser_used": document.parser_key or "none",
                "worksheets": [],
                "original_columns": [],
                "proposed_canonical_mappings": [],
                "sample_rows": [],
                "total_rows": 0,
                "candidate_observation_count": 0,
                "detected_strong_identifiers": [],
                "conflicts": [],
                "warnings": ["duplicate_document"],
                "fields_requiring_review": [],
                "proposed_changes_summary": {"new_observations": 0, "report_type": document.detected_report_type or "unknown"},
                "operational_summary": {
                    "stores": 0,
                    "churn_candidates": 0,
                    "churn_insufficient_data": 0,
                    "critical_stores": 0,
                    "assets_without_store": 0,
                    "identity_conflicts": 0,
                    "missing_identity": 0,
                    "unavailable_fields": [],
                },
            },
        }
        db.commit()
        return DataIntakeProcessResponse(document_id=document.id, status=document.review_status, preview_ready=True)

    try:
        preview_service.process_document(db, document, source)
        record_event(
            db,
            event_type="data_intake.observations_created",
            aggregate_type="document_record",
            aggregate_id=document.id,
            payload={"observation_count": document.observation_count or 0},
        )
    except Exception as exc:
        document.review_status = "failed"
        document.processing_error = str(exc)
        record_event(
            db,
            event_type="data_intake.extraction_completed",
            aggregate_type="document_record",
            aggregate_id=document.id,
            payload={"status": "failed"},
        )
    db.commit()
    return DataIntakeProcessResponse(document_id=document.id, status=document.review_status, preview_ready=document.review_status == "preview_ready")


@router.get("/documents/{document_id}/preview", response_model=DataIntakePreviewResponse)
def get_preview(document_id: UUID, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    preview = (document.metadata_json or {}).get("preview")
    if not preview:
        raise HTTPException(status_code=404, detail="preview not available")
    return preview


@router.post("/documents/{document_id}/confirm", response_model=DataIntakeDocumentRead)
def confirm_document(document_id: UUID, payload: DataIntakeConfirmRequest, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    if document.review_status not in {"preview_ready", "pending"}:
        raise HTTPException(status_code=409, detail="document cannot be confirmed")
    document.review_status = "confirmed"
    document.confirmed_by = payload.reviewer
    document.confirmed_at = utc_now()
    candidate_observations = db.scalars(
        select(Observation).where(
            Observation.document_id == document.id,
            Observation.confirmation_status == "candidate",
        )
    ).all()
    for observation in candidate_observations:
        observation.confirmation_status = "confirmed"
        observation.confirmed_by = payload.reviewer
        observation.confirmed_at = document.confirmed_at
    record_event(
        db,
        event_type="data_intake.document_confirmed",
        aggregate_type="document_record",
        aggregate_id=document.id,
        payload={"reviewer": payload.reviewer, "confirmed_observation_count": len(candidate_observations)},
    )
    db.commit()
    db.refresh(document)
    return document


@router.post("/documents/{document_id}/reject", response_model=DataIntakeDocumentRead)
def reject_document(document_id: UUID, payload: DataIntakeRejectRequest, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    document.review_status = "rejected"
    document.confirmed_by = payload.reviewer
    document.confirmed_at = utc_now()
    document.processing_error = payload.reason
    record_event(
        db,
        event_type="data_intake.document_rejected",
        aggregate_type="document_record",
        aggregate_id=document.id,
        payload={"reviewer": payload.reviewer},
    )
    db.commit()
    db.refresh(document)
    return document


@router.post("/documents/{document_id}/reprocess", response_model=DataIntakeProcessResponse)
def reprocess_document(document_id: UUID, payload: DataIntakeReprocessRequest, db: Session = Depends(get_db)):
    document = db.get(DocumentRecord, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    source = db.get(SourceRecord, document.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")

    record_event(
        db,
        event_type="data_intake.reprocessing_requested",
        aggregate_type="document_record",
        aggregate_id=document.id,
        payload={"reviewer": payload.reviewer},
    )
    preview_service.process_document(db, document, source, force_reprocess=True)
    db.commit()
    return DataIntakeProcessResponse(document_id=document.id, status=document.review_status, preview_ready=True)


@router.get("/report-types")
def report_types():
    return DeterministicReportClassifier.REPORT_TYPES


@router.get("/parsers")
def list_parsers():
    return DocumentParserRegistry(preview_row_limit=settings.preview_row_limit).list_parsers()

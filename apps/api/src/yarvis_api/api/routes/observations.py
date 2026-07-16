from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.observation_engine import DocumentRecord, Observation, ResolutionDecision, SourceRecord
from yarvis_api.schemas.observation_engine import (
    DocumentCreate,
    DocumentRegisterResult,
    DocumentRead,
    ObservationCreate,
    ObservationRead,
    ObservationStatusChange,
    ObservationSupersede,
    ResolutionDecisionAction,
    ResolutionDecisionRead,
    ResolutionProposalCreate,
    SourceCreate,
    SourceRead,
)
from yarvis_api.services.observation_engine import (
    confirm_observation,
    confirm_resolution,
    create_observation,
    create_resolution_proposal,
    list_observations_query,
    mark_conflict,
    register_document,
    register_source,
    reject_observation,
    reject_resolution,
    supersede_observation,
)

router = APIRouter(tags=["observations", "resolutions"])


@router.post("/observations/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = register_source(db, **payload.model_dump(mode="python"))
    db.commit()
    db.refresh(source)
    return source


@router.post("/observations/documents", response_model=DocumentRegisterResult, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    if db.get(SourceRecord, payload.source_id) is None:
        raise HTTPException(status_code=404, detail="source not found")

    document, created, duplicate_by = register_document(db, **payload.model_dump(mode="python"))
    db.commit()
    db.refresh(document)
    return DocumentRegisterResult(created=created, duplicate_by=duplicate_by, document=DocumentRead.model_validate(document))


@router.get("/observations/documents", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(DocumentRecord).order_by(DocumentRecord.created_at.desc())).all()


@router.get("/observations/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    item = db.get(DocumentRecord, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="document not found")
    return item


@router.post("/observations", response_model=ObservationRead, status_code=status.HTTP_201_CREATED)
def add_observation(payload: ObservationCreate, db: Session = Depends(get_db)):
    if payload.document_id and db.get(DocumentRecord, payload.document_id) is None:
        raise HTTPException(status_code=404, detail="document not found")
    if payload.source_id and db.get(SourceRecord, payload.source_id) is None:
        raise HTTPException(status_code=404, detail="source not found")
    item = create_observation(db, **payload.model_dump(mode="python"))
    db.commit()
    db.refresh(item)
    return item


@router.get("/observations", response_model=list[ObservationRead])
def list_observations(
    domain: str | None = None,
    subject_type: str | None = None,
    subject_reference: str | None = None,
    confirmation_status: str | None = None,
    db: Session = Depends(get_db),
):
    return db.scalars(
        list_observations_query(
            domain=domain,
            subject_type=subject_type,
            subject_reference=subject_reference,
            status=confirmation_status,
        )
    ).all()


@router.get("/observations/{observation_id}", response_model=ObservationRead)
def get_observation(observation_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Observation, observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    return item


@router.post("/observations/{observation_id}/confirm", response_model=ObservationRead)
def confirm(observation_id: UUID, payload: ObservationStatusChange, db: Session = Depends(get_db)):
    item = db.get(Observation, observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    try:
        confirm_observation(db, item, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item


@router.post("/observations/{observation_id}/reject", response_model=ObservationRead)
def reject(observation_id: UUID, payload: ObservationStatusChange, db: Session = Depends(get_db)):
    item = db.get(Observation, observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    try:
        reject_observation(db, item, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item


@router.post("/observations/{observation_id}/conflict", response_model=ObservationRead)
def conflict(observation_id: UUID, payload: ObservationStatusChange, db: Session = Depends(get_db)):
    item = db.get(Observation, observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    try:
        mark_conflict(db, item, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item


@router.post("/observations/{observation_id}/supersede", response_model=ObservationRead)
def supersede(observation_id: UUID, payload: ObservationSupersede, db: Session = Depends(get_db)):
    item = db.get(Observation, observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    replacement = db.get(Observation, payload.replacement_observation_id)
    if replacement is None:
        raise HTTPException(status_code=404, detail="replacement observation not found")
    try:
        supersede_observation(db, item, payload.replacement_observation_id, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item


@router.post("/observations/{observation_id}/resolution-proposals", response_model=ResolutionDecisionRead, status_code=status.HTTP_201_CREATED)
def propose_resolution(observation_id: UUID, payload: ResolutionProposalCreate, db: Session = Depends(get_db)):
    if db.get(Observation, observation_id) is None:
        raise HTTPException(status_code=404, detail="observation not found")
    item = create_resolution_proposal(db, observation_id=observation_id, **payload.model_dump(mode="python"))
    db.commit()
    db.refresh(item)
    return item


@router.post("/resolutions/{resolution_id}/confirm", response_model=ResolutionDecisionRead)
def confirm_resolution_endpoint(resolution_id: UUID, payload: ResolutionDecisionAction, db: Session = Depends(get_db)):
    item = db.get(ResolutionDecision, resolution_id)
    if item is None:
        raise HTTPException(status_code=404, detail="resolution not found")
    confirm_resolution(db, item, payload.actor)
    db.commit()
    db.refresh(item)
    return item


@router.post("/resolutions/{resolution_id}/reject", response_model=ResolutionDecisionRead)
def reject_resolution_endpoint(resolution_id: UUID, payload: ResolutionDecisionAction, db: Session = Depends(get_db)):
    item = db.get(ResolutionDecision, resolution_id)
    if item is None:
        raise HTTPException(status_code=404, detail="resolution not found")
    reject_resolution(db, item, payload.actor)
    db.commit()
    db.refresh(item)
    return item

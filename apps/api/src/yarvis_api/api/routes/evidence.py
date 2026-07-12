from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.evidence import Evidence
from yarvis_api.models.intake import IntakeItem
from yarvis_api.schemas.evidence import EvidenceCreate, EvidenceRead
from yarvis_api.schemas.event import DomainEventRead
from yarvis_api.models.domain_event import DomainEvent

router = APIRouter(prefix="/cases", tags=["evidence", "events"])


@router.post("/{case_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def create_evidence(case_id: UUID, payload: EvidenceCreate, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if payload.intake_item_id is not None and db.get(IntakeItem, payload.intake_item_id) is None:
        raise HTTPException(status_code=404, detail="intake_item_id not found")
    evidence = Evidence(case_id=case_id, **payload.model_dump(mode="python"))
    db.add(evidence)
    db.flush()
    record_event(
        db,
        event_type="evidence.created",
        aggregate_type="evidence",
        aggregate_id=evidence.id,
        organization_id=case.owner_organization_id,
        case_id=case_id,
        payload={"evidence_type": evidence.evidence_type, "title": evidence.title},
    )
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/{case_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(case_id: UUID, db: Session = Depends(get_db)):
    if db.get(Case, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.scalars(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)).all()


@router.get("/{case_id}/events", response_model=list[DomainEventRead])
def list_case_events(case_id: UUID, db: Session = Depends(get_db)):
    if db.get(Case, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.scalars(
        select(DomainEvent)
        .where(DomainEvent.case_id == case_id)
        .order_by(DomainEvent.occurred_at, DomainEvent.recorded_at, DomainEvent.id)
    ).all()

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.schemas.intake import IntakeCreate, IntakeRead

router = APIRouter(prefix="/intake", tags=["intake"])


def validate_references(db: Session, payload: IntakeCreate) -> None:
    for model, identifier, label in (
        (Organization, payload.organization_id, "organization_id"),
        (Person, payload.person_id, "person_id"),
        (Case, payload.case_id, "case_id"),
    ):
        if identifier is not None and db.get(model, identifier) is None:
            raise HTTPException(status_code=404, detail=f"{label} not found")


@router.post("", response_model=IntakeRead, status_code=status.HTTP_201_CREATED)
def create_intake(payload: IntakeCreate, db: Session = Depends(get_db)):
    validate_references(db, payload)
    item = IntakeItem(**payload.model_dump(exclude={"received_at"}, mode="python"))
    if payload.received_at is not None:
        item.received_at = payload.received_at
    db.add(item)
    db.flush()
    record_event(
        db,
        event_type="intake.received",
        aggregate_type="intake_item",
        aggregate_id=item.id,
        organization_id=item.organization_id,
        case_id=item.case_id,
        payload={"intake_number": item.intake_number, "source_type": item.source_type},
    )
    if item.case_id is not None:
        record_event(
            db,
            event_type="intake.linked_to_case",
            aggregate_type="intake_item",
            aggregate_id=item.id,
            organization_id=item.organization_id,
            case_id=item.case_id,
            payload={"intake_number": item.intake_number},
        )
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[IntakeRead])
def list_intake(db: Session = Depends(get_db)):
    return db.scalars(select(IntakeItem).order_by(IntakeItem.received_at, IntakeItem.created_at)).all()


@router.get("/{intake_id}", response_model=IntakeRead)
def get_intake(intake_id: UUID, db: Session = Depends(get_db)):
    item = db.get(IntakeItem, intake_id)
    if item is None:
        raise HTTPException(status_code=404, detail="IntakeItem not found")
    return item


@router.post("/{intake_id}/link-case/{case_id}", response_model=IntakeRead)
def link_case(intake_id: UUID, case_id: UUID, db: Session = Depends(get_db)):
    item = db.get(IntakeItem, intake_id)
    if item is None:
        raise HTTPException(status_code=404, detail="IntakeItem not found")
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if item.case_id == case_id:
        raise HTTPException(status_code=409, detail="IntakeItem is already linked to this Case")
    item.case_id = case_id
    record_event(
        db,
        event_type="intake.linked_to_case",
        aggregate_type="intake_item",
        aggregate_id=item.id,
        organization_id=item.organization_id or case.owner_organization_id,
        case_id=case_id,
        payload={"intake_number": item.intake_number},
    )
    db.commit()
    db.refresh(item)
    return item

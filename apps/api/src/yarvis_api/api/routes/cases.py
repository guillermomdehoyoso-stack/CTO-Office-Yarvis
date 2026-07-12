from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.schemas.case import CaseCreate, CaseRead

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    if db.get(Organization, payload.owner_organization_id) is None:
        raise HTTPException(status_code=422, detail="owner_organization_id does not exist")
    if payload.primary_person_id and db.get(Person, payload.primary_person_id) is None:
        raise HTTPException(status_code=422, detail="primary_person_id does not exist")
    case = Case(**payload.model_dump(mode="json"))
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db)):
    return db.scalars(select(Case).order_by(Case.created_at)).all()


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: UUID, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

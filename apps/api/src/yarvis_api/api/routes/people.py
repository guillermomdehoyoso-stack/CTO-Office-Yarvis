from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.person import Person
from yarvis_api.schemas.person import PersonCreate, PersonRead

router = APIRouter(prefix="/people", tags=["people"])


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    person = Person(
        first_name=payload.first_name,
        last_name=payload.last_name,
        display_name=payload.resolved_display_name(),
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        status=payload.status,
    )
    db.add(person)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="email must be unique") from exc
    db.refresh(person)
    return person


@router.get("", response_model=list[PersonRead])
def list_people(db: Session = Depends(get_db)):
    return db.scalars(select(Person).order_by(Person.created_at)).all()


@router.get("/{person_id}", response_model=PersonRead)
def get_person(person_id: UUID, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

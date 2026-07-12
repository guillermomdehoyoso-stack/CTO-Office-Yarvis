from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.organization import Organization
from yarvis_api.schemas.organization import OrganizationCreate, OrganizationRead

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    organization = Organization(
        legal_name=payload.legal_name,
        display_name=payload.display_name or payload.legal_name,
        organization_type=payload.organization_type,
        status=payload.status,
    )
    db.add(organization)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="legal_name must be unique") from exc
    db.refresh(organization)
    return organization


@router.get("", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)):
    return db.scalars(select(Organization).order_by(Organization.created_at)).all()


@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(organization_id: UUID, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

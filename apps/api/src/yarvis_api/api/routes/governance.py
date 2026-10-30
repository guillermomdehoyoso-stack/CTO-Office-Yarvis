"""Bounded F-011 Membership activation and terminal revocation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.database import get_db
from yarvis_api.services.governance_authority import (
    activate_membership,
    change_membership_role_for_portfolio_read,
    revoke_membership,
)

router = APIRouter(prefix="/governance/memberships", tags=["governance"])


class MembershipActivation(BaseModel):
    principal_id: UUID
    role: str = Field(min_length=1, max_length=64)
    causation_id: UUID | None = None


class MembershipRead(BaseModel):
    id: UUID
    principal_id: UUID
    organization_id: UUID
    role: str
    status: str


class MembershipRoleTransition(BaseModel):
    expected_role: str = Field(min_length=1, max_length=64)
    target_role: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=255)
    causation_id: UUID | None = None


def _key(value: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255)) -> str:
    return value


@router.post("", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def activate(payload: MembershipActivation, response: Response, idempotency_key: str = Depends(_key), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope), db: Session = Depends(get_db)):
    membership = activate_membership(db, envelope=envelope, principal_id=payload.principal_id, role=payload.role, idempotency_key=idempotency_key, causation_id=payload.causation_id)
    db.commit()
    return membership


@router.post("/{membership_id}/revoke", response_model=MembershipRead)
def revoke(membership_id: UUID, causation_id: UUID | None = None, idempotency_key: str = Depends(_key), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope), db: Session = Depends(get_db)):
    membership = revoke_membership(db, envelope=envelope, membership_id=membership_id, idempotency_key=idempotency_key, causation_id=causation_id)
    db.commit()
    return membership


@router.post("/{membership_id}/role-transition", response_model=MembershipRead)
def change_role(
    membership_id: UUID,
    payload: MembershipRoleTransition,
    idempotency_key: str = Depends(_key),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
    db: Session = Depends(get_db),
):
    membership = change_membership_role_for_portfolio_read(
        db,
        envelope=envelope,
        membership_id=membership_id,
        expected_role=payload.expected_role,
        target_role=payload.target_role,
        reason=payload.reason,
        idempotency_key=idempotency_key,
        causation_id=payload.causation_id,
    )
    db.commit()
    return membership

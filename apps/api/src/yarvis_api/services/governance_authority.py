"""F-011 Governance QRY-001 / EVT-001 application entry points."""

from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.principal import Principal, PrincipalMembership, PrincipalMembershipCommand


def evaluate_authority(envelope: IdentityAuthorityEnvelope, *, required_permission: str, target_organization_id: UUID) -> None:
    """Implement IC-GOVERNANCE-QRY-001 v1.1.0 without mutation."""
    if envelope.organization_id != target_organization_id:
        raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "foreign_target"})
    envelope.require(required_permission)


def _correlation_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


def _fingerprint(command_type: str, membership_id: UUID, values: tuple[str, ...]) -> str:
    return sha256("|".join((command_type, str(membership_id), *values)).encode()).hexdigest()


def _replay(db: Session, *, envelope: IdentityAuthorityEnvelope, key: str, fingerprint: str) -> PrincipalMembership | None:
    command = db.scalar(select(PrincipalMembershipCommand).where(PrincipalMembershipCommand.organization_id == envelope.organization_id, PrincipalMembershipCommand.idempotency_key == key))
    if command is None:
        return None
    if command.request_fingerprint != fingerprint:
        raise ApplicationError(ApplicationErrorCode.CONFLICT, "idempotency key conflicts", {"reason": "idempotency_conflict"})
    return db.scalar(select(PrincipalMembership).where(PrincipalMembership.id == command.membership_id, PrincipalMembership.organization_id == envelope.organization_id))


def activate_membership(db: Session, *, envelope: IdentityAuthorityEnvelope, principal_id: UUID, role: str, idempotency_key: str, causation_id: UUID | None = None) -> PrincipalMembership:
    """Bounded activation command implementing EVT-001 atomically."""
    envelope.require("governance.membership.create")
    existing = db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal_id, PrincipalMembership.organization_id == envelope.organization_id))
    fingerprint = sha256(f"activate|{principal_id}|{role}".encode()).hexdigest()
    replay = _replay(db, envelope=envelope, key=idempotency_key, fingerprint=fingerprint)
    if replay is not None:
        return replay
    if existing is not None:
        raise ApplicationError(ApplicationErrorCode.CONFLICT, "membership already exists", {"reason": "membership_terminal_or_existing"})
    principal = db.scalar(select(Principal).where(Principal.id == principal_id, Principal.status == "active"))
    if principal is None:
        raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "foreign_or_inactive_principal"})
    membership = PrincipalMembership(principal_id=principal_id, organization_id=envelope.organization_id, role=role, status="active")
    db.add(membership); db.flush()
    db.add(PrincipalMembershipCommand(organization_id=envelope.organization_id, membership_id=membership.id, command_type="activate", idempotency_key=idempotency_key, request_fingerprint=fingerprint))
    record_event(db, event_type="AuthorityChanged", aggregate_type="PrincipalMembership", aggregate_id=membership.id, organization_id=membership.organization_id, correlation_id=_correlation_uuid(envelope.correlation_id), causation_id=causation_id, payload={"contract_version": "1.1.0", "transition": "activated", "membership_id": str(membership.id), "principal_id": str(principal_id), "actor_principal_id": str(envelope.principal_id)})
    return membership


def revoke_membership(db: Session, *, envelope: IdentityAuthorityEnvelope, membership_id: UUID, idempotency_key: str, causation_id: UUID | None = None) -> PrincipalMembership:
    """Implement the terminal revoke transition and safe EVT-001 append."""
    envelope.require("governance.membership.revoke")
    fingerprint = _fingerprint("revoke", membership_id, ())
    replay = _replay(db, envelope=envelope, key=idempotency_key, fingerprint=fingerprint)
    if replay is not None:
        return replay
    membership = db.scalar(select(PrincipalMembership).where(PrincipalMembership.id == membership_id, PrincipalMembership.organization_id == envelope.organization_id))
    if membership is None:
        raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "foreign_membership"})
    if membership.status == "revoked":
        raise ApplicationError(ApplicationErrorCode.CONFLICT, "membership is terminally revoked", {"reason": "membership_revoked"})
    membership.status = "revoked"
    membership.revoked_at = datetime.now(timezone.utc)
    db.add(PrincipalMembershipCommand(organization_id=envelope.organization_id, membership_id=membership.id, command_type="revoke", idempotency_key=idempotency_key, request_fingerprint=fingerprint))
    record_event(db, event_type="AuthorityChanged", aggregate_type="PrincipalMembership", aggregate_id=membership.id, organization_id=membership.organization_id, correlation_id=_correlation_uuid(envelope.correlation_id), causation_id=causation_id, payload={"contract_version": "1.1.0", "transition": "revoked", "membership_id": str(membership.id), "principal_id": str(membership.principal_id), "actor_principal_id": str(envelope.principal_id)})
    return membership

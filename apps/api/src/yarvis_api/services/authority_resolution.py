"""Persistence-resolved F-011 authority envelope construction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope, permissions_for_role
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership


class AuthorityResolutionService:
    def resolve(self, db: Session, *, external_subject: str, selector: str | UUID | None, authentication_source: str, correlation_id: str) -> IdentityAuthorityEnvelope:
        principal = db.scalar(select(Principal).where(Principal.external_subject == external_subject))
        if principal is None:
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "principal is not provisioned", {"reason": "principal_not_found"})
        if principal.status != "active":
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "principal is disabled", {"reason": "principal_disabled"})
        memberships = db.scalars(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id, PrincipalMembership.status == "active")).all()
        if not memberships:
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "no active membership", {"reason": "no_active_membership"})
        if selector is None:
            if len(memberships) != 1:
                raise ApplicationError(ApplicationErrorCode.CONFLICT, "organization selector required", {"reason": "ambiguous_organization"})
            membership = memberships[0]
        else:
            try:
                organization_id = UUID(str(selector))
            except ValueError as error:
                raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "foreign_selector"}) from error
            membership = next((item for item in memberships if item.organization_id == organization_id), None)
            if membership is None:
                raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "foreign_selector"})
        organization = db.scalar(select(Organization).where(Organization.id == membership.organization_id))
        if organization is None:
            raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "organization_not_found"})
        if organization.status != "active":
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "organization is inactive", {"reason": "organization_inactive"})
        return IdentityAuthorityEnvelope(principal.id, organization.id, permissions_for_role(membership.role), authentication_source, correlation_id)

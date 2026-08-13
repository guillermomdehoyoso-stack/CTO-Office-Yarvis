"""Trusted F-011 authority values and closed server policy."""

from dataclasses import dataclass
from uuid import UUID

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "radar_viewer": frozenset({"radar.read", "radar.activity.read"}),
    "radar_operator": frozenset({"radar.read", "radar.activity.read", "radar.merchant.create", "radar.request.create", "radar.request.update", "radar.checklist.update", "radar.request.close", "radar.request.reopen", "radar.note.create"}),
    "foundation_membership_operator": frozenset({"governance.membership.create", "governance.membership.revoke"}),
    "inbound_viewer": frozenset({"inbound.read"}),
    "inbound_operator": frozenset({"inbound.read", "inbound.intake"}),
    "inbound_context_operator": frozenset({"inbound.context.associate"}),
    "mission_inbox_viewer": frozenset({"mission.inbox.read"}),
}


def permissions_for_role(role: str) -> frozenset[str]:
    try:
        return ROLE_PERMISSIONS[role]
    except KeyError as error:
        raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "unknown persisted role", {"reason": "unknown_role"}) from error


@dataclass(frozen=True, slots=True)
class IdentityAuthorityEnvelope:
    principal_id: UUID
    organization_id: UUID
    validated_permissions: frozenset[str]
    authentication_source: str
    correlation_id: str

    def require(self, permission: str) -> None:
        if permission not in self.validated_permissions:
            raise ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "permission denied", {"reason": "missing_permission"})

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
    "document_viewer": frozenset({"document.read"}),
    "document_contributor": frozenset({
        "document.read",
        "document.create",
        "document.metadata.update",
        "document.version.add",
        "document.association.link",
        "document.association.unlink",
    }),
    "document_archivist": frozenset({"document.read", "document.archive"}),
    "mission_work_viewer": frozenset({"mission.work.read"}),
    "mission_work_operator": frozenset({"mission.work.read", "mission.work.create", "mission.work.status.change", "mission.work.priority.change"}),
    "mission_work_coordinator": frozenset({"mission.work.read", "mission.work.assign"}),
    "economics_fact_recorder": frozenset({"economics.fact.record"}),
    "economics_fact_corrector": frozenset({"economics.fact.correct"}),
    "economics_viewer": frozenset({"economics.read"}),
    "task_planner": frozenset({"task.create", "task.update"}),
    "task_assigner": frozenset({"task.assign"}),
    "task_lifecycle_operator": frozenset({"task.transition", "task.complete", "task.cancel"}),
    "task_dependency_manager": frozenset({"task.dependency.manage"}),
    "process_definition_viewer": frozenset({"process.definition.read"}),
    "process_definition_manager": frozenset({"process.definition.manage"}),
    "process_instance_viewer": frozenset({"process.instance.read"}),
    "process_instance_operator": frozenset({"process.instance.start", "process.instance.transition", "process.instance.cancel"}),
    "process_work_link_coordinator": frozenset({"process.instance.work.link", "process.instance.work.unlink"}),
    "netpay_master_viewer": frozenset({"netpay.master.read"}),
    "netpay_master_operator": frozenset({"netpay.master.read", "netpay.master.manage"}),
    "netpay_inbox_viewer": frozenset({"netpay.inbox.read"}),
    "netpay_inbox_operator": frozenset({"netpay.inbox.read", "netpay.inbox.manage"}),
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

"""Typed WS-001 contract declarations for application-layer use."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WS001CommandName(StrEnum):
    RECEIVE_INTAKE = "receive_intake"
    REGISTER_MESSAGE = "register_message"
    CAPTURE_INBOUND_OBSERVATION = "capture_inbound_observation"
    REGISTER_SOURCE_ARTIFACT = "register_source_artifact"
    VALIDATE_EVIDENCE = "validate_evidence"
    IDENTIFY_OR_REGISTER_MERCHANT_CANDIDATE = "identify_or_register_merchant_candidate"
    OPEN_NETPAY_CASE = "open_netpay_case"
    CLASSIFY_NETPAY_CHANNEL = "classify_netpay_channel"
    EVALUATE_CHECKLIST_AND_SET_PENDING_ACTION = "evaluate_checklist_and_set_pending_action"
    CREATE_PENDING_ACTION = "create_pending_action"
    ASSIGN_PENDING_ACTION = "assign_pending_action"
    RESOLVE_PENDING_ACTION = "resolve_pending_action"
    ACKNOWLEDGE_ATTENTION_ITEM = "acknowledge_attention_item"


class WS002CommandName(StrEnum):
    ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT = "associate_intake_operational_context"


class WS001QueryName(StrEnum):
    RETRIEVE_DETERMINISTIC_INTAKE_DETAIL = "retrieve_deterministic_intake_detail"
    RETRIEVE_MERCHANT_CASE = "retrieve_merchant_case"
    RETRIEVE_CHECKLIST_AND_PENDING_ACTIONS = "retrieve_checklist_and_pending_actions"
    RETRIEVE_PENDING_ACTION_STATUS = "retrieve_pending_action_status"
    RETRIEVE_CASE_ATTENTION = "retrieve_case_attention"


class WS002QueryName(StrEnum):
    RETRIEVE_INTAKE_OPERATIONAL_CONTEXT = "retrieve_intake_operational_context"


class WS003QueryName(StrEnum):
    LIST_MISSION_INBOX = "list_mission_inbox"
    RETRIEVE_MISSION_INBOX_ITEM = "retrieve_mission_inbox_item"


class WS004CommandName(StrEnum):
    CREATE_MISSION_WORK_ITEM_FROM_INBOX = "create_mission_work_item_from_inbox"
    ASSIGN_MISSION_WORK_ITEM = "assign_mission_work_item"
    CHANGE_MISSION_WORK_ITEM_STATUS = "change_mission_work_item_status"
    CHANGE_MISSION_WORK_ITEM_PRIORITY = "change_mission_work_item_priority"


class WS004QueryName(StrEnum):
    LIST_MISSION_WORK_ITEMS = "list_mission_work_items"
    RETRIEVE_MISSION_WORK_ITEM = "retrieve_mission_work_item"


class WS004EventName(StrEnum):
    MISSION_WORK_ITEM_CREATED = "mission_work_item_created"
    MISSION_WORK_ITEM_ASSIGNED = "mission_work_item_assigned"
    MISSION_WORK_ITEM_UNASSIGNED = "mission_work_item_unassigned"
    MISSION_WORK_ITEM_STATUS_CHANGED = "mission_work_item_status_changed"
    MISSION_WORK_ITEM_PRIORITY_CHANGED = "mission_work_item_priority_changed"


class WS005CommandName(StrEnum):
    ADD_MISSION_WORK_ITEM_COMMENT = "add_mission_work_item_comment"


class WS005QueryName(StrEnum):
    RETRIEVE_MISSION_WORK_TIMELINE = "retrieve_mission_work_timeline"


class WS005EventName(StrEnum):
    MISSION_WORK_ITEM_COMMENT_ADDED = "mission_work_item_comment_added"


class WS006CommandName(StrEnum):
    CREATE_PROCESS_DEFINITION = "create_process_definition"
    CREATE_PROCESS_VERSION = "create_process_version"
    ADD_PROCESS_STAGE = "add_process_stage"
    UPDATE_PROCESS_STAGE = "update_process_stage"
    DELETE_PROCESS_STAGE = "delete_process_stage"
    ADD_PROCESS_TRANSITION = "add_process_transition"
    UPDATE_PROCESS_TRANSITION = "update_process_transition"
    DELETE_PROCESS_TRANSITION = "delete_process_transition"
    PUBLISH_PROCESS_DEFINITION = "publish_process_definition"
    RETIRE_PROCESS_DEFINITION = "retire_process_definition"
    START_PROCESS_INSTANCE = "start_process_instance"
    TRANSITION_PROCESS_INSTANCE = "transition_process_instance"
    CANCEL_PROCESS_INSTANCE = "cancel_process_instance"
    LINK_PROCESS_INSTANCE_TO_MISSION_WORK = "link_process_instance_to_mission_work"
    UNLINK_PROCESS_INSTANCE_FROM_MISSION_WORK = "unlink_process_instance_from_mission_work"


class WS006QueryName(StrEnum):
    LIST_PROCESS_DEFINITIONS = "list_process_definitions"
    RETRIEVE_PROCESS_DEFINITION = "retrieve_process_definition"
    LIST_PROCESS_INSTANCES = "list_process_instances"
    RETRIEVE_PROCESS_INSTANCE = "retrieve_process_instance"
    RETRIEVE_PROCESS_INSTANCE_TIMELINE = "retrieve_process_instance_timeline"
    LIST_MISSION_WORK_PROCESS_LINKS = "list_mission_work_process_links"
    RETRIEVE_PROCESS_INSTANCE_PRIMARY_WORK_LINK = "retrieve_process_instance_primary_work_link"
    LIST_PROCESS_INSTANCE_WORK_LINK_HISTORY = "list_process_instance_work_link_history"
    RETRIEVE_OPERATIONAL_WORKSPACE = "retrieve_operational_workspace"


class WS006EventName(StrEnum):
    PROCESS_DEFINITION_CREATED = "process_definition_created"
    PROCESS_DEFINITION_VERSION_CREATED = "process_definition_version_created"
    PROCESS_DEFINITION_PUBLISHED = "process_definition_published"
    PROCESS_DEFINITION_RETIRED = "process_definition_retired"
    PROCESS_INSTANCE_STARTED = "process_instance_started"
    PROCESS_INSTANCE_TRANSITIONED = "process_instance_transitioned"
    PROCESS_INSTANCE_COMPLETED = "process_instance_completed"
    PROCESS_INSTANCE_CANCELLED = "process_instance_cancelled"
    PROCESS_INSTANCE_WORK_LINKED = "process_instance_work_linked"
    PROCESS_INSTANCE_WORK_UNLINKED = "process_instance_work_unlinked"


class OV002CommandName(StrEnum):
    RECORD_ECONOMIC_FACT = "record_economic_fact"
    CORRECT_ECONOMIC_FACT = "correct_economic_fact"

class WS007CommandName(StrEnum):
    CREATE_TASK="create_operational_task"; UPDATE_TASK="update_operational_task"; ASSIGN_TASK="assign_operational_task"; TRANSITION_TASK="transition_operational_task"; COMPLETE_TASK="complete_operational_task"; CANCEL_TASK="cancel_operational_task"; MANAGE_DEPENDENCIES="manage_operational_task_dependencies"


class WS008QueryName(StrEnum):
    RETRIEVE_OPERATIONAL_WORKSPACE_OVERVIEW = "retrieve_operational_workspace_overview"


class OV002QueryName(StrEnum):
    RETRIEVE_OPERATIONAL_ECONOMICS = "retrieve_operational_economics"
    RETRIEVE_ECONOMIC_FACT_HISTORY = "retrieve_economic_fact_history"


class OV002EventName(StrEnum):
    ECONOMIC_FACT_RECORDED = "economic_fact_recorded"
    ECONOMIC_FACT_CORRECTED = "economic_fact_corrected"


class WS001EventName(StrEnum):
    OBSERVATION_CAPTURED = "observation_captured"
    EVIDENCE_VALIDATED = "evidence_validated"
    NETPAY_CASE_OPENED = "netpay_case_opened"
    NETPAY_CASE_STATUS_CHANGED = "netpay_case_status_changed"
    PENDING_ACTION_STATE_CHANGED = "pending_action_state_changed"
    WORK_ACTIVITY_RECORDED = "work_activity_recorded"
    ATTENTION_PUBLISHED = "attention_published"


@dataclass(frozen=True, slots=True)
class ApplicationContract:
    interaction_contract_id: str
    owning_context: str
    owning_capability: str
    mutating: bool
    requires_actor: bool
    requires_authority: bool = False
    required_authority_scope: str | None = None
    requires_idempotency_key: bool = False


command_contracts: dict[WS001CommandName | WS002CommandName | WS004CommandName | WS005CommandName | WS006CommandName | OV002CommandName | WS007CommandName, ApplicationContract] = {
    WS001CommandName.RECEIVE_INTAKE: ApplicationContract(
        interaction_contract_id="IC-INBOX-CMD-001",
        owning_context="intake",
        owning_capability="receive",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
        required_authority_scope="inbound.intake",
        requires_idempotency_key=True,
    ),
    WS001CommandName.REGISTER_MESSAGE: ApplicationContract(
        interaction_contract_id="IC-INBOX-CMD-002",
        owning_context="intake",
        owning_capability="message",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
        required_authority_scope="inbound.intake",
        requires_idempotency_key=True,
    ),
    WS001CommandName.CAPTURE_INBOUND_OBSERVATION: ApplicationContract(
        interaction_contract_id="IC-EVIDENCE-CMD-001",
        owning_context="observation_evidence",
        owning_capability="observation",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.REGISTER_SOURCE_ARTIFACT: ApplicationContract(
        interaction_contract_id="IC-EVIDENCE-CMD-002",
        owning_context="observation_evidence",
        owning_capability="artifact_evidence",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.VALIDATE_EVIDENCE: ApplicationContract(
        interaction_contract_id="IC-EVIDENCE-CMD-003",
        owning_context="observation_evidence",
        owning_capability="validation",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.IDENTIFY_OR_REGISTER_MERCHANT_CANDIDATE: ApplicationContract(
        interaction_contract_id="IC-NETPAY-CMD-001",
        owning_context="netpay_merchant_operations",
        owning_capability="merchant_candidate",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
        requires_idempotency_key=True,
    ),
    WS001CommandName.OPEN_NETPAY_CASE: ApplicationContract(
        interaction_contract_id="IC-NETPAY-CMD-002",
        owning_context="netpay_merchant_operations",
        owning_capability="case",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
        requires_idempotency_key=True,
    ),
    WS001CommandName.CLASSIFY_NETPAY_CHANNEL: ApplicationContract(
        interaction_contract_id="IC-NETPAY-CMD-003",
        owning_context="netpay_merchant_operations",
        owning_capability="case_classification",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.EVALUATE_CHECKLIST_AND_SET_PENDING_ACTION: ApplicationContract(
        interaction_contract_id="IC-NETPAY-CMD-004",
        owning_context="netpay_merchant_operations",
        owning_capability="checklist",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.CREATE_PENDING_ACTION: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-CMD-001",
        owning_context="execution",
        owning_capability="work",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.ASSIGN_PENDING_ACTION: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-CMD-002",
        owning_context="execution",
        owning_capability="assignment",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.RESOLVE_PENDING_ACTION: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-CMD-003",
        owning_context="execution",
        owning_capability="work_state",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
    WS001CommandName.ACKNOWLEDGE_ATTENTION_ITEM: ApplicationContract(
        interaction_contract_id="IC-MISSION-CMD-001",
        owning_context="mission_control",
        owning_capability="acknowledgement",
        mutating=True,
        requires_actor=True,
        requires_authority=True,
    ),
}

command_contracts[WS002CommandName.ASSOCIATE_INTAKE_OPERATIONAL_CONTEXT] = ApplicationContract(
    interaction_contract_id="IC-INBOX-CMD-003",
    owning_context="intake",
    owning_capability="operational_context_association",
    mutating=True,
    requires_actor=True,
    requires_authority=True,
    required_authority_scope="inbound.context.associate",
    requires_idempotency_key=True,
)

for name, contract_id, capability, authority in (
    (WS004CommandName.CREATE_MISSION_WORK_ITEM_FROM_INBOX, "IC-MISSION-CMD-002", "work_item_creation", "mission.work.create"),
    (WS004CommandName.ASSIGN_MISSION_WORK_ITEM, "IC-MISSION-CMD-003", "work_item_assignment", "mission.work.assign"),
    (WS004CommandName.CHANGE_MISSION_WORK_ITEM_STATUS, "IC-MISSION-CMD-004", "work_item_status", "mission.work.status.change"),
    (WS004CommandName.CHANGE_MISSION_WORK_ITEM_PRIORITY, "IC-MISSION-CMD-005", "work_item_priority", "mission.work.priority.change"),
):
    command_contracts[name] = ApplicationContract(contract_id, "mission_control", capability, True, True, True, authority)

command_contracts[WS005CommandName.ADD_MISSION_WORK_ITEM_COMMENT] = ApplicationContract(
    "IC-MISSION-CMD-006", "mission_control", "work_item_comment", True, True, True, "mission.work.create"
)

for name, contract_id, capability in (
    (WS006CommandName.CREATE_PROCESS_DEFINITION, "IC-PROCESS-CMD-001", "process_definition"),
    (WS006CommandName.CREATE_PROCESS_VERSION, "IC-PROCESS-CMD-002", "process_version"),
    (WS006CommandName.ADD_PROCESS_STAGE, "IC-PROCESS-CMD-003", "process_stage"),
    (WS006CommandName.UPDATE_PROCESS_STAGE, "IC-PROCESS-CMD-004", "process_stage"),
    (WS006CommandName.DELETE_PROCESS_STAGE, "IC-PROCESS-CMD-005", "process_stage"),
    (WS006CommandName.ADD_PROCESS_TRANSITION, "IC-PROCESS-CMD-006", "process_transition"),
    (WS006CommandName.UPDATE_PROCESS_TRANSITION, "IC-PROCESS-CMD-007", "process_transition"),
    (WS006CommandName.DELETE_PROCESS_TRANSITION, "IC-PROCESS-CMD-008", "process_transition"),
    (WS006CommandName.PUBLISH_PROCESS_DEFINITION, "IC-PROCESS-CMD-009", "process_publication"),
    (WS006CommandName.RETIRE_PROCESS_DEFINITION, "IC-PROCESS-CMD-010", "process_retirement"),
):
    command_contracts[name] = ApplicationContract(contract_id, "process", capability, True, True, True, "process.definition.manage")

for name, contract_id, capability, authority in (
    (WS006CommandName.START_PROCESS_INSTANCE, "IC-PROCESS-CMD-011", "process_instance_start", "process.instance.start"),
    (WS006CommandName.TRANSITION_PROCESS_INSTANCE, "IC-PROCESS-CMD-012", "process_instance_transition", "process.instance.transition"),
    (WS006CommandName.CANCEL_PROCESS_INSTANCE, "IC-PROCESS-CMD-013", "process_instance_cancel", "process.instance.cancel"),
    (WS006CommandName.LINK_PROCESS_INSTANCE_TO_MISSION_WORK, "IC-PROCESS-CMD-014", "process_instance_work_link", "process.instance.work.link"),
    (WS006CommandName.UNLINK_PROCESS_INSTANCE_FROM_MISSION_WORK, "IC-PROCESS-CMD-015", "process_instance_work_unlink", "process.instance.work.unlink"),
):
    command_contracts[name] = ApplicationContract(contract_id, "process", capability, True, True, True, authority, True)

for name, contract_id, capability, authority in (
    (OV002CommandName.RECORD_ECONOMIC_FACT, "IC-ECONOMICS-CMD-001", "economic_fact_recording", "economics.fact.record"),
    (OV002CommandName.CORRECT_ECONOMIC_FACT, "IC-ECONOMICS-CMD-002", "economic_fact_correction", "economics.fact.correct"),
):
    command_contracts[name] = ApplicationContract(contract_id, "operational_economics", capability, True, True, True, authority, True)

for name, contract_id, capability, authority in (
    (WS007CommandName.CREATE_TASK,"IC-TASK-CMD-001","task_creation","task.create"),(WS007CommandName.UPDATE_TASK,"IC-TASK-CMD-002","task_planning","task.update"),(WS007CommandName.ASSIGN_TASK,"IC-TASK-CMD-003","task_assignment","task.assign"),(WS007CommandName.TRANSITION_TASK,"IC-TASK-CMD-004","task_transition","task.transition"),(WS007CommandName.COMPLETE_TASK,"IC-TASK-CMD-005","task_completion","task.complete"),(WS007CommandName.CANCEL_TASK,"IC-TASK-CMD-006","task_cancellation","task.cancel"),(WS007CommandName.MANAGE_DEPENDENCIES,"IC-TASK-CMD-007","task_dependencies","task.dependency.manage"),
): command_contracts[name]=ApplicationContract(contract_id,"operational_execution",capability,True,True,True,authority,True)


query_contracts: dict[WS001QueryName | WS002QueryName | WS003QueryName | WS004QueryName | WS005QueryName | WS006QueryName | WS008QueryName | OV002QueryName, ApplicationContract] = {
    WS001QueryName.RETRIEVE_DETERMINISTIC_INTAKE_DETAIL: ApplicationContract(
        interaction_contract_id="IC-INBOX-QRY-001",
        owning_context="intake",
        owning_capability="detail_retrieval",
        mutating=False,
        requires_actor=True,
        requires_authority=True,
        required_authority_scope="inbound.read",
    ),
    WS001QueryName.RETRIEVE_MERCHANT_CASE: ApplicationContract(
        interaction_contract_id="IC-NETPAY-QRY-001",
        owning_context="netpay_merchant_operations",
        owning_capability="case_view",
        mutating=False,
        requires_actor=False,
    ),
    WS001QueryName.RETRIEVE_CHECKLIST_AND_PENDING_ACTIONS: ApplicationContract(
        interaction_contract_id="IC-NETPAY-QRY-002",
        owning_context="netpay_merchant_operations",
        owning_capability="checklist_view",
        mutating=False,
        requires_actor=False,
    ),
    WS001QueryName.RETRIEVE_PENDING_ACTION_STATUS: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-QRY-001",
        owning_context="execution",
        owning_capability="work_state",
        mutating=False,
        requires_actor=False,
    ),
    WS001QueryName.RETRIEVE_CASE_ATTENTION: ApplicationContract(
        interaction_contract_id="IC-MISSION-QRY-001",
        owning_context="mission_control",
        owning_capability="attention_projection",
        mutating=False,
        requires_actor=False,
    ),
}

query_contracts[WS002QueryName.RETRIEVE_INTAKE_OPERATIONAL_CONTEXT] = ApplicationContract(
    interaction_contract_id="IC-INBOX-QRY-002",
    owning_context="intake",
    owning_capability="operational_context_association",
    mutating=False,
    requires_actor=True,
    requires_authority=True,
    required_authority_scope="inbound.read",
)

query_contracts[WS003QueryName.LIST_MISSION_INBOX] = ApplicationContract(
    interaction_contract_id="IC-MISSION-QRY-002",
    owning_context="mission_control",
    owning_capability="mission_inbox",
    mutating=False,
    requires_actor=True,
    requires_authority=True,
    required_authority_scope="mission.inbox.read",
)

query_contracts[WS003QueryName.RETRIEVE_MISSION_INBOX_ITEM] = ApplicationContract(
    interaction_contract_id="IC-MISSION-QRY-003",
    owning_context="mission_control",
    owning_capability="mission_inbox",
    mutating=False,
    requires_actor=True,
    requires_authority=True,
    required_authority_scope="mission.inbox.read",
)

query_contracts[WS004QueryName.LIST_MISSION_WORK_ITEMS] = ApplicationContract(
    "IC-MISSION-QRY-004", "mission_control", "work_item_list", False, True, True, "mission.work.read"
)
query_contracts[WS004QueryName.RETRIEVE_MISSION_WORK_ITEM] = ApplicationContract(
    "IC-MISSION-QRY-005", "mission_control", "work_item_detail", False, True, True, "mission.work.read"
)
query_contracts[WS005QueryName.RETRIEVE_MISSION_WORK_TIMELINE] = ApplicationContract(
    "IC-MISSION-QRY-006", "mission_control", "work_item_timeline", False, True, True, "mission.work.read"
)
query_contracts[WS006QueryName.LIST_PROCESS_DEFINITIONS] = ApplicationContract(
    "IC-PROCESS-QRY-001", "process", "process_definition_list", False, True, True, "process.definition.read"
)
query_contracts[WS006QueryName.RETRIEVE_PROCESS_DEFINITION] = ApplicationContract(
    "IC-PROCESS-QRY-002", "process", "process_definition_detail", False, True, True, "process.definition.read"
)
for name, contract_id, capability in (
    (WS006QueryName.LIST_PROCESS_INSTANCES, "IC-PROCESS-QRY-003", "process_instance_list"),
    (WS006QueryName.RETRIEVE_PROCESS_INSTANCE, "IC-PROCESS-QRY-004", "process_instance_detail"),
    (WS006QueryName.RETRIEVE_PROCESS_INSTANCE_TIMELINE, "IC-PROCESS-QRY-005", "process_instance_timeline"),
    (WS006QueryName.LIST_MISSION_WORK_PROCESS_LINKS, "IC-PROCESS-QRY-006", "mission_work_process_links"),
    (WS006QueryName.RETRIEVE_PROCESS_INSTANCE_PRIMARY_WORK_LINK, "IC-PROCESS-QRY-007", "process_instance_primary_work_link"),
    (WS006QueryName.LIST_PROCESS_INSTANCE_WORK_LINK_HISTORY, "IC-PROCESS-QRY-008", "process_instance_work_link_history"),
    (WS006QueryName.RETRIEVE_OPERATIONAL_WORKSPACE, "IC-MISSION-QRY-007", "operational_workspace"),
):
    authority = "mission.work.read" if name == WS006QueryName.RETRIEVE_OPERATIONAL_WORKSPACE else "process.instance.read"
    context = "mission_control" if name == WS006QueryName.RETRIEVE_OPERATIONAL_WORKSPACE else "process"
    query_contracts[name] = ApplicationContract(contract_id, context, capability, False, True, True, authority)

query_contracts[WS008QueryName.RETRIEVE_OPERATIONAL_WORKSPACE_OVERVIEW] = ApplicationContract(
    "IC-WORKSPACE-QRY-001", "mission_control", "operational_workspace_overview", False, True, True, "mission.work.read"
)

for name, contract_id, capability in (
    (OV002QueryName.RETRIEVE_OPERATIONAL_ECONOMICS, "IC-ECONOMICS-QRY-001", "economic_summary"),
    (OV002QueryName.RETRIEVE_ECONOMIC_FACT_HISTORY, "IC-ECONOMICS-QRY-002", "economic_fact_history"),
):
    query_contracts[name] = ApplicationContract(contract_id, "operational_economics", capability, False, True, True, "economics.read")


event_contracts: dict[WS001EventName | WS004EventName | WS005EventName | WS006EventName | OV002EventName, ApplicationContract] = {
    WS001EventName.OBSERVATION_CAPTURED: ApplicationContract(
        interaction_contract_id="IC-EVIDENCE-EVT-001",
        owning_context="observation_evidence",
        owning_capability="observation",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.EVIDENCE_VALIDATED: ApplicationContract(
        interaction_contract_id="IC-EVIDENCE-EVT-002",
        owning_context="observation_evidence",
        owning_capability="validation",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.NETPAY_CASE_OPENED: ApplicationContract(
        interaction_contract_id="IC-NETPAY-EVT-001",
        owning_context="netpay_merchant_operations",
        owning_capability="case",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.NETPAY_CASE_STATUS_CHANGED: ApplicationContract(
        interaction_contract_id="IC-NETPAY-EVT-002",
        owning_context="netpay_merchant_operations",
        owning_capability="case",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.PENDING_ACTION_STATE_CHANGED: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-EVT-001",
        owning_context="execution",
        owning_capability="work",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.WORK_ACTIVITY_RECORDED: ApplicationContract(
        interaction_contract_id="IC-EXECUTION-EVT-002",
        owning_context="execution",
        owning_capability="activity",
        mutating=False,
        requires_actor=False,
    ),
    WS001EventName.ATTENTION_PUBLISHED: ApplicationContract(
        interaction_contract_id="IC-MISSION-EVT-001",
        owning_context="mission_control",
        owning_capability="projection",
        mutating=False,
        requires_actor=False,
    ),
}

for name, contract_id, capability in (
    (WS004EventName.MISSION_WORK_ITEM_CREATED, "IC-MISSION-EVT-002", "work_item_creation"),
    (WS004EventName.MISSION_WORK_ITEM_ASSIGNED, "IC-MISSION-EVT-003", "work_item_assignment"),
    (WS004EventName.MISSION_WORK_ITEM_UNASSIGNED, "IC-MISSION-EVT-004", "work_item_assignment"),
    (WS004EventName.MISSION_WORK_ITEM_STATUS_CHANGED, "IC-MISSION-EVT-005", "work_item_status"),
    (WS004EventName.MISSION_WORK_ITEM_PRIORITY_CHANGED, "IC-MISSION-EVT-006", "work_item_priority"),
):
    event_contracts[name] = ApplicationContract(contract_id, "mission_control", capability, False, False)

event_contracts[WS005EventName.MISSION_WORK_ITEM_COMMENT_ADDED] = ApplicationContract(
    "IC-MISSION-EVT-007", "mission_control", "work_item_comment", False, False
)

for name, contract_id, capability in (
    (WS006EventName.PROCESS_DEFINITION_CREATED, "IC-PROCESS-EVT-001", "process_definition"),
    (WS006EventName.PROCESS_DEFINITION_VERSION_CREATED, "IC-PROCESS-EVT-002", "process_version"),
    (WS006EventName.PROCESS_DEFINITION_PUBLISHED, "IC-PROCESS-EVT-003", "process_publication"),
    (WS006EventName.PROCESS_DEFINITION_RETIRED, "IC-PROCESS-EVT-004", "process_retirement"),
):
    event_contracts[name] = ApplicationContract(contract_id, "process", capability, False, False)

for name, contract_id, capability in (
    (OV002EventName.ECONOMIC_FACT_RECORDED, "IC-ECONOMICS-EVT-001", "economic_fact_recording"),
    (OV002EventName.ECONOMIC_FACT_CORRECTED, "IC-ECONOMICS-EVT-002", "economic_fact_correction"),
):
    event_contracts[name] = ApplicationContract(contract_id, "operational_economics", capability, False, False)

for name, contract_id, capability in (
    (WS006EventName.PROCESS_INSTANCE_STARTED, "IC-PROCESS-EVT-005", "process_instance_start"),
    (WS006EventName.PROCESS_INSTANCE_TRANSITIONED, "IC-PROCESS-EVT-006", "process_instance_transition"),
    (WS006EventName.PROCESS_INSTANCE_COMPLETED, "IC-PROCESS-EVT-007", "process_instance_completion"),
    (WS006EventName.PROCESS_INSTANCE_CANCELLED, "IC-PROCESS-EVT-008", "process_instance_cancellation"),
    (WS006EventName.PROCESS_INSTANCE_WORK_LINKED, "IC-PROCESS-EVT-009", "process_instance_work_link"),
    (WS006EventName.PROCESS_INSTANCE_WORK_UNLINKED, "IC-PROCESS-EVT-010", "process_instance_work_unlink"),
):
    event_contracts[name] = ApplicationContract(contract_id, "process", capability, False, False)

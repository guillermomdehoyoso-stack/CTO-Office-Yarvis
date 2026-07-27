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


command_contracts: dict[WS001CommandName | WS002CommandName | WS004CommandName, ApplicationContract] = {
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


query_contracts: dict[WS001QueryName | WS002QueryName | WS003QueryName | WS004QueryName, ApplicationContract] = {
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


event_contracts: dict[WS001EventName | WS004EventName, ApplicationContract] = {
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

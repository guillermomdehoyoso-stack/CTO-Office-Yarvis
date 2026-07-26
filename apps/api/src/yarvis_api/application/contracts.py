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


class WS001QueryName(StrEnum):
    RETRIEVE_DETERMINISTIC_INTAKE_DETAIL = "retrieve_deterministic_intake_detail"
    RETRIEVE_MERCHANT_CASE = "retrieve_merchant_case"
    RETRIEVE_CHECKLIST_AND_PENDING_ACTIONS = "retrieve_checklist_and_pending_actions"
    RETRIEVE_PENDING_ACTION_STATUS = "retrieve_pending_action_status"
    RETRIEVE_CASE_ATTENTION = "retrieve_case_attention"


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


command_contracts: dict[WS001CommandName, ApplicationContract] = {
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


query_contracts: dict[WS001QueryName, ApplicationContract] = {
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


event_contracts: dict[WS001EventName, ApplicationContract] = {
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

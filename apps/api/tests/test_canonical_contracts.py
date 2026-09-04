from yarvis_api.canonical_contracts import canonical_contracts
from yarvis_api.canonical_modules import canonical_modules
from yarvis_api.contract_registry import (
    INTERACTION_CONTRACT_ID_PATTERN,
    SEMANTIC_VERSION_PATTERN,
    ContractCriticality,
    ContractLifecycle,
    ContractOperationalStatus,
    ContractType,
    build_contract_registry,
)
from yarvis_api.module_registry import build_module_registry

_PROPOSED_PLANNED = (ContractLifecycle.PROPOSED, ContractOperationalStatus.PLANNED)
_RATIFIED_VERIFIED = (ContractLifecycle.RATIFIED, ContractOperationalStatus.VERIFIED)
_RATIFIED_PLANNED = (ContractLifecycle.RATIFIED, ContractOperationalStatus.PLANNED)

CANONICAL_RUNTIME_BASELINE_V1 = (
    (
        "IC-PLATFORM-CMD-DISPATCH-PROBE",
        ContractType.COMMAND,
        "platform",
        "dispatch mechanics",
        *_RATIFIED_VERIFIED,
    ),
    (
        "IC-WORKSPACE-QRY-001",
        ContractType.QUERY,
        "mission_control",
        "operational workspace overview",
        *_PROPOSED_PLANNED,
    ),
    ("IC-TASK-CMD-001", ContractType.COMMAND, "operational_execution", "task creation", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-002", ContractType.COMMAND, "operational_execution", "task planning", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-003", ContractType.COMMAND, "operational_execution", "task assignment", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-004", ContractType.COMMAND, "operational_execution", "task transition", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-005", ContractType.COMMAND, "operational_execution", "task completion", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-006", ContractType.COMMAND, "operational_execution", "task cancellation", *_PROPOSED_PLANNED),
    ("IC-TASK-CMD-007", ContractType.COMMAND, "operational_execution", "task dependencies", *_PROPOSED_PLANNED),
    ("IC-IDENTITY-CMD-001", ContractType.COMMAND, "identity", "resolution", *_PROPOSED_PLANNED),
    ("IC-IDENTITY-QRY-001", ContractType.QUERY, "identity", "canonical reference", *_PROPOSED_PLANNED),
    ("IC-IDENTITY-EVT-001", ContractType.EVENT, "identity", "resolution", *_PROPOSED_PLANNED),
    ("IC-GOVERNANCE-QRY-001", ContractType.QUERY, "governance", "authority", *_PROPOSED_PLANNED),
    ("IC-GOVERNANCE-QRY-002", ContractType.QUERY, "governance", "policy/delegation", *_PROPOSED_PLANNED),
    ("IC-GOVERNANCE-EVT-001", ContractType.EVENT, "governance", "authority", *_PROPOSED_PLANNED),
    ("IC-RELATIONSHIP-CMD-001", ContractType.COMMAND, "relationship", "association", *_PROPOSED_PLANNED),
    ("IC-RELATIONSHIP-QRY-001", ContractType.QUERY, "relationship", "association", *_PROPOSED_PLANNED),
    ("IC-RELATIONSHIP-EVT-001", ContractType.EVENT, "relationship", "association", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-CMD-001", ContractType.COMMAND, "observation_evidence", "observation", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-CMD-002", ContractType.COMMAND, "observation_evidence", "artifact/evidence", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-CMD-003", ContractType.COMMAND, "observation_evidence", "validation", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-QRY-001", ContractType.QUERY, "observation_evidence", "lineage", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-EVT-001", ContractType.EVENT, "observation_evidence", "observation", *_PROPOSED_PLANNED),
    ("IC-EVIDENCE-EVT-002", ContractType.EVENT, "observation_evidence", "evidence", *_PROPOSED_PLANNED),
    ("IC-KNOWLEDGE-CMD-001", ContractType.COMMAND, "knowledge", "promotion", *_PROPOSED_PLANNED),
    ("IC-KNOWLEDGE-QRY-001", ContractType.QUERY, "knowledge", "assertion", *_PROPOSED_PLANNED),
    ("IC-KNOWLEDGE-EVT-001", ContractType.EVENT, "knowledge", "assertion", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-CMD-001", ContractType.COMMAND, "execution", "work", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-CMD-002", ContractType.COMMAND, "execution", "assignment", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-CMD-003", ContractType.COMMAND, "execution", "work state", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-QRY-001", ContractType.QUERY, "execution", "work state", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-EVT-001", ContractType.EVENT, "execution", "work", *_PROPOSED_PLANNED),
    ("IC-EXECUTION-EVT-002", ContractType.EVENT, "execution", "activity", *_PROPOSED_PLANNED),
    ("IC-MISSION-CMD-001", ContractType.COMMAND, "mission_control", "acknowledgement", *_PROPOSED_PLANNED),
    ("IC-MISSION-QRY-001", ContractType.QUERY, "mission_control", "attention projection", *_PROPOSED_PLANNED),
    ("IC-MISSION-EVT-001", ContractType.EVENT, "mission_control", "projection", *_PROPOSED_PLANNED),
    ("IC-MISSION-NTF-001", ContractType.NOTIFICATION, "mission_control", "communication", *_PROPOSED_PLANNED),
    ("IC-NETPAY-CMD-001", ContractType.COMMAND, "netpay_merchant_operations", "merchant candidate", *_PROPOSED_PLANNED),
    ("IC-NETPAY-CMD-002", ContractType.COMMAND, "netpay_merchant_operations", "case", *_PROPOSED_PLANNED),
    (
        "IC-NETPAY-CMD-003",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "case classification",
        *_PROPOSED_PLANNED,
    ),
    ("IC-NETPAY-CMD-004", ContractType.COMMAND, "netpay_merchant_operations", "checklist", *_PROPOSED_PLANNED),
    ("IC-NETPAY-QRY-001", ContractType.QUERY, "netpay_merchant_operations", "case view", *_PROPOSED_PLANNED),
    ("IC-NETPAY-QRY-002", ContractType.QUERY, "netpay_merchant_operations", "checklist view", *_PROPOSED_PLANNED),
    ("IC-NETPAY-EVT-001", ContractType.EVENT, "netpay_merchant_operations", "case", *_PROPOSED_PLANNED),
    ("IC-NETPAY-EVT-002", ContractType.EVENT, "netpay_merchant_operations", "case", *_PROPOSED_PLANNED),
    ("IC-NETPAY-NTF-001", ContractType.NOTIFICATION, "netpay_merchant_operations", "communication", *_PROPOSED_PLANNED),
    ("IC-DOCUMENT-CMD-001", ContractType.COMMAND, "document_registry", "document creation", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-CMD-002", ContractType.COMMAND, "document_registry", "metadata update", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-CMD-003", ContractType.COMMAND, "document_registry", "version creation", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-CMD-004", ContractType.COMMAND, "document_registry", "document archival", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-CMD-005", ContractType.COMMAND, "document_registry", "association link", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-CMD-006", ContractType.COMMAND, "document_registry", "association unlink", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-QRY-001", ContractType.QUERY, "document_registry", "document retrieval", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-QRY-002", ContractType.QUERY, "document_registry", "version retrieval", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-QRY-003", ContractType.QUERY, "document_registry", "association retrieval", *_RATIFIED_VERIFIED),
    ("IC-DOCUMENT-QRY-004", ContractType.QUERY, "document_registry", "subject retrieval", *_RATIFIED_VERIFIED),
    (
        "IC-NETPAY-CMD-020",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-021",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-022",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-023",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-024",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-025",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-009",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-010",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-011",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-012",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-013",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-014",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "commercial intake pre-master",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-026",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-027",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-028",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-029",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-030",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-011",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-012",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-013",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-015",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-016",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-017",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-018",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-019",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "operational data intake D1",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-009",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-010",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-011",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-012",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-013",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-014",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-015",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-005",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-QRY-006",
        ContractType.QUERY,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-003",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-004",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-005",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-EVT-006",
        ContractType.EVENT,
        "netpay_merchant_operations",
        "service inbox",
        ContractLifecycle.RATIFIED,
        ContractOperationalStatus.PLANNED,
    ),
    (
        "IC-NETPAY-CMD-005",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "tenant-owned master",
        *_RATIFIED_VERIFIED,
    ),
    (
        "IC-NETPAY-CMD-006",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "tenant-owned master",
        *_RATIFIED_VERIFIED,
    ),
    (
        "IC-NETPAY-CMD-007",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "tenant-owned master",
        *_RATIFIED_VERIFIED,
    ),
    (
        "IC-NETPAY-CMD-008",
        ContractType.COMMAND,
        "netpay_merchant_operations",
        "tenant-owned master",
        *_RATIFIED_VERIFIED,
    ),
    ("IC-NETPAY-QRY-003", ContractType.QUERY, "netpay_merchant_operations", "tenant-owned master", *_RATIFIED_VERIFIED),
    ("IC-NETPAY-QRY-004", ContractType.QUERY, "netpay_merchant_operations", "tenant-owned master", *_RATIFIED_VERIFIED),
)

AUTH_PROD_IDS = {
    "IC-IDENTITY-CMD-002",
    "IC-IDENTITY-CMD-003",
    "IC-IDENTITY-CMD-004",
    "IC-IDENTITY-CMD-005",
    "IC-IDENTITY-QRY-002",
    "IC-IDENTITY-QRY-003",
    "IC-IDENTITY-EVT-002",
    "IC-IDENTITY-EVT-003",
    "IC-IDENTITY-EVT-004",
    "IC-IDENTITY-EVT-005",
    "IC-GOVERNANCE-CMD-001",
    "IC-GOVERNANCE-CMD-002",
    "IC-GOVERNANCE-CMD-003",
    "IC-GOVERNANCE-QRY-003",
    "IC-GOVERNANCE-QRY-004",
    "IC-GOVERNANCE-EVT-002",
}

CANONICAL_CONTRACT_IDS = tuple(contract[0] for contract in CANONICAL_RUNTIME_BASELINE_V1)


def test_canonical_tier_one_projection_is_explicit_complete_and_deterministic() -> None:
    contracts = canonical_contracts()

    assert (
        tuple(
            (
                contract.interaction_contract_id,
                contract.contract_type,
                contract.owner_module_id,
                contract.owning_capability,
                contract.lifecycle,
                contract.operational_status,
            )
            for contract in contracts
            if contract.interaction_contract_id not in AUTH_PROD_IDS
        )
        == CANONICAL_RUNTIME_BASELINE_V1
    )
    assert (
        tuple(
            contract.interaction_contract_id
            for contract in contracts
            if contract.interaction_contract_id not in AUTH_PROD_IDS
        )
        == CANONICAL_CONTRACT_IDS
    )
    assert {
        contract.interaction_contract_id for contract in contracts if contract.interaction_contract_id in AUTH_PROD_IDS
    } == AUTH_PROD_IDS
    assert len(contracts) == 116
    assert len({contract.interaction_contract_id for contract in contracts}) == 116
    assert all(INTERACTION_CONTRACT_ID_PATTERN.fullmatch(contract.interaction_contract_id) for contract in contracts)
    assert all(SEMANTIC_VERSION_PATTERN.fullmatch(contract.version) for contract in contracts)
    assert all(contract.version == "1.0.0" for contract in contracts)
    assert all(
        (contract.lifecycle, contract.operational_status) == _RATIFIED_VERIFIED
        for contract in contracts
        if contract.owner_module_id == "document_registry"
    )
    assert all(
        (contract.lifecycle, contract.operational_status) == _PROPOSED_PLANNED
        for contract in contracts
        if contract.owner_module_id not in {"document_registry", "netpay_merchant_operations", "platform"}
        and contract.interaction_contract_id not in AUTH_PROD_IDS
    )
    assert all(
        (contract.lifecycle, contract.operational_status) == _RATIFIED_PLANNED
        for contract in contracts
        if contract.interaction_contract_id in AUTH_PROD_IDS
    )
    assert all(contract.architectural_steward is None for contract in contracts)
    assert all(contract.traceability_references == () for contract in contracts)


def test_canonical_tier_one_projection_has_ratified_kind_and_owner_distributions() -> None:
    contracts = canonical_contracts()

    assert {kind: sum(contract.contract_type == kind for contract in contracts) for kind in ContractType} == {
        ContractType.COMMAND: 57,
        ContractType.QUERY: 28,
        ContractType.EVENT: 29,
        ContractType.NOTIFICATION: 2,
    }
    owner_counts = {
        owner: sum(contract.owner_module_id == owner for contract in contracts)
        for owner in {contract.owner_module_id for contract in contracts}
    }
    assert owner_counts == {
        "platform": 1,
        "identity": 13,
        "governance": 9,
        "relationship": 3,
        "observation_evidence": 6,
        "knowledge": 3,
        "execution": 6,
        "mission_control": 5,
        "netpay_merchant_operations": 53,
        "operational_execution": 7,
        "document_registry": 10,
    }


def test_canonical_contracts_validate_against_canonical_modules_and_required_metadata() -> None:
    contracts = canonical_contracts()
    registry = build_contract_registry(build_module_registry(canonical_modules()), contracts)

    assert registry.is_sealed is True
    assert registry.list() == contracts
    assert all(contract.primary_consumer_or_use_case for contract in contracts)
    assert all(contract.contract_type in ContractType for contract in contracts)
    assert all(contract.criticality in ContractCriticality for contract in contracts)
    assert all(
        not hasattr(contract, forbidden_field)
        for contract in contracts
        for forbidden_field in ("message_type", "result_type", "handler", "transport", "persistence")
    )

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

CANONICAL_CONTRACT_IDS = (
    "IC-IDENTITY-CMD-001",
    "IC-IDENTITY-QRY-001",
    "IC-IDENTITY-EVT-001",
    "IC-GOVERNANCE-QRY-001",
    "IC-GOVERNANCE-QRY-002",
    "IC-GOVERNANCE-EVT-001",
    "IC-RELATIONSHIP-CMD-001",
    "IC-RELATIONSHIP-QRY-001",
    "IC-RELATIONSHIP-EVT-001",
    "IC-EVIDENCE-CMD-001",
    "IC-EVIDENCE-CMD-002",
    "IC-EVIDENCE-CMD-003",
    "IC-EVIDENCE-QRY-001",
    "IC-EVIDENCE-EVT-001",
    "IC-EVIDENCE-EVT-002",
    "IC-KNOWLEDGE-CMD-001",
    "IC-KNOWLEDGE-QRY-001",
    "IC-KNOWLEDGE-EVT-001",
    "IC-EXECUTION-CMD-001",
    "IC-EXECUTION-CMD-002",
    "IC-EXECUTION-CMD-003",
    "IC-EXECUTION-QRY-001",
    "IC-EXECUTION-EVT-001",
    "IC-EXECUTION-EVT-002",
    "IC-MISSION-CMD-001",
    "IC-MISSION-QRY-001",
    "IC-MISSION-EVT-001",
    "IC-MISSION-NTF-001",
    "IC-NETPAY-CMD-001",
    "IC-NETPAY-CMD-002",
    "IC-NETPAY-CMD-003",
    "IC-NETPAY-CMD-004",
    "IC-NETPAY-QRY-001",
    "IC-NETPAY-QRY-002",
    "IC-NETPAY-EVT-001",
    "IC-NETPAY-EVT-002",
    "IC-NETPAY-NTF-001",
)


def test_canonical_tier_one_projection_is_explicit_complete_and_deterministic() -> None:
    contracts = canonical_contracts()

    assert tuple(contract.interaction_contract_id for contract in contracts) == CANONICAL_CONTRACT_IDS
    assert len(contracts) == 37
    assert len({contract.interaction_contract_id for contract in contracts}) == 37
    assert all(INTERACTION_CONTRACT_ID_PATTERN.fullmatch(contract.interaction_contract_id) for contract in contracts)
    assert all(SEMANTIC_VERSION_PATTERN.fullmatch(contract.version) for contract in contracts)
    assert all(contract.version == "1.0.0" for contract in contracts)
    assert all(contract.lifecycle == ContractLifecycle.PROPOSED for contract in contracts)
    assert all(contract.operational_status == ContractOperationalStatus.PLANNED for contract in contracts)
    assert all(contract.architectural_steward is None for contract in contracts)
    assert all(contract.traceability_references == () for contract in contracts)


def test_canonical_tier_one_projection_has_ratified_kind_and_owner_distributions() -> None:
    contracts = canonical_contracts()

    assert {kind: sum(contract.contract_type == kind for contract in contracts) for kind in ContractType} == {
        ContractType.COMMAND: 14,
        ContractType.QUERY: 10,
        ContractType.EVENT: 11,
        ContractType.NOTIFICATION: 2,
    }
    owner_counts = {
        owner: sum(contract.owner_module_id == owner for contract in contracts)
        for owner in {contract.owner_module_id for contract in contracts}
    }
    assert owner_counts == {
        "identity": 3,
        "governance": 3,
        "relationship": 3,
        "observation_evidence": 6,
        "knowledge": 3,
        "execution": 6,
        "mission_control": 4,
        "netpay_merchant_operations": 9,
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

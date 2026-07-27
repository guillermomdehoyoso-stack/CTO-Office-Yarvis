from datetime import datetime, timezone

import pytest

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import (
    WS001CommandName,
    WS001QueryName,
    WS003QueryName,
    WS004CommandName,
    WS004EventName,
    WS004QueryName,
    WS005CommandName,
    WS005EventName,
    WS005QueryName,
    command_contracts,
    event_contracts,
    query_contracts,
)
from yarvis_api.application.errors import (
    ApplicationError,
    ApplicationErrorCode,
)
from yarvis_api.api.errors import error_to_http_status
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.service_boundary import (
    enforce_command_boundary,
    enforce_query_boundary,
)


def _command_metadata(*, idempotency_key: str | None = None) -> RequestMetadata:
    return RequestMetadata(
        requested_at=datetime.now(tz=timezone.utc),
        correlation_id="corr-1",
        command_id="cmd-1",
        idempotency_key=idempotency_key,
    )


def _query_metadata() -> RequestMetadata:
    return RequestMetadata(
        requested_at=datetime.now(tz=timezone.utc),
        correlation_id="corr-1",
        query_id="qry-1",
    )


def _principal(*, authority: str = "observation", roles: tuple[str, ...] = ()) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        actor_id="user-1",
        organization_id="org-1",
        roles=roles,
        permissions=(),
        authority=authority,
        authentication_method="test",
        authenticated_at=datetime.now(tz=timezone.utc),
        is_system_actor=False,
        correlation_id="corr-1",
    )


def test_request_metadata_rejects_command_and_query_id_coexistence() -> None:
    with pytest.raises(ValueError):
        RequestMetadata(
            requested_at=datetime.now(tz=timezone.utc),
            correlation_id="corr-1",
            command_id="cmd-1",
            query_id="qry-1",
        )


def test_request_metadata_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError):
        RequestMetadata(requested_at=datetime.now(), correlation_id="corr-1")


def test_authenticated_principal_validates_required_fields() -> None:
    with pytest.raises(ValueError):
        AuthenticatedPrincipal(
            actor_id="",
            organization_id="org-1",
            roles=(),
            permissions=(),
            authority="inbound.intake",
            authentication_method="test",
            authenticated_at=datetime.now(tz=timezone.utc),
            is_system_actor=False,
        )

    with pytest.raises(ValueError):
        AuthenticatedPrincipal(
            actor_id="user-1",
            organization_id="org-1",
            roles=(),
            permissions=(),
            authority="",
            authentication_method="test",
            authenticated_at=datetime.now(tz=timezone.utc),
            is_system_actor=False,
        )


def test_error_to_http_status_maps_stable_codes() -> None:
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "bad")) == 400
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "no")) == 403
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.PRECONDITION_FAILED, "wait")) == 412
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "missing")) == 404
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.CONFLICT, "conflict")) == 409
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.DEPENDENCY_UNAVAILABLE, "dep")) == 503
    assert error_to_http_status(ApplicationError(ApplicationErrorCode.INTERNAL_ERROR, "boom")) == 500


def test_command_boundary_requires_actor_for_mutating_commands() -> None:
    contract = command_contracts[WS001CommandName.CAPTURE_INBOUND_OBSERVATION]
    metadata = _command_metadata()

    with pytest.raises(ApplicationError) as exc:
        enforce_command_boundary(contract, metadata=metadata, principal=None)

    assert exc.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_command_boundary_requires_authority_for_mutating_commands() -> None:
    contract = command_contracts[WS001CommandName.CAPTURE_INBOUND_OBSERVATION]
    class EmptyAuthorityPrincipal:
        authority = ""

    with pytest.raises(ApplicationError) as exc:
        enforce_command_boundary(
            contract,
            metadata=_command_metadata(),
            principal=EmptyAuthorityPrincipal(),
        )

    assert exc.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_command_boundary_requires_idempotency_for_declared_contracts() -> None:
    contract = command_contracts[WS001CommandName.OPEN_NETPAY_CASE]
    principal = _principal(authority="netpay")

    with pytest.raises(ApplicationError) as exc:
        enforce_command_boundary(contract, metadata=_command_metadata(), principal=principal)

    assert exc.value.code == ApplicationErrorCode.PRECONDITION_FAILED

    enforce_command_boundary(
        contract,
        metadata=_command_metadata(idempotency_key="idem-1"),
        principal=principal,
    )


def test_command_boundary_rejects_insufficient_required_authority_scope() -> None:
    contract = command_contracts[WS001CommandName.RECEIVE_INTAKE]
    principal = _principal(authority="inbound.readonly")

    with pytest.raises(ApplicationError) as exc:
        enforce_command_boundary(
            contract,
            metadata=_command_metadata(idempotency_key="idem-1"),
            principal=principal,
        )

    assert exc.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_query_boundary_requires_query_id_and_non_mutating_contract() -> None:
    query_contract = query_contracts[WS001QueryName.RETRIEVE_MERCHANT_CASE]
    enforce_query_boundary(query_contract, metadata=_query_metadata())

    with pytest.raises(ApplicationError) as exc:
        enforce_query_boundary(query_contract, metadata=_command_metadata())

    assert exc.value.code == ApplicationErrorCode.VALIDATION_FAILED


def test_application_contract_ids_are_unique_and_mission_inbox_bindings_are_canonical() -> None:
    contracts = (*command_contracts.values(), *query_contracts.values(), *event_contracts.values())
    contract_ids = [contract.interaction_contract_id for contract in contracts]

    assert len(contract_ids) == len(set(contract_ids))
    assert query_contracts[WS001QueryName.RETRIEVE_CASE_ATTENTION].interaction_contract_id == "IC-MISSION-QRY-001"
    assert query_contracts[WS003QueryName.LIST_MISSION_INBOX].interaction_contract_id == "IC-MISSION-QRY-002"
    assert query_contracts[WS003QueryName.RETRIEVE_MISSION_INBOX_ITEM].interaction_contract_id == "IC-MISSION-QRY-003"


def test_ws004_contract_bindings_require_actor_authority_and_preserve_mutation_semantics() -> None:
    expected_commands = {
        WS004CommandName.CREATE_MISSION_WORK_ITEM_FROM_INBOX: ("IC-MISSION-CMD-002", "mission.work.create"),
        WS004CommandName.ASSIGN_MISSION_WORK_ITEM: ("IC-MISSION-CMD-003", "mission.work.assign"),
        WS004CommandName.CHANGE_MISSION_WORK_ITEM_STATUS: ("IC-MISSION-CMD-004", "mission.work.status.change"),
        WS004CommandName.CHANGE_MISSION_WORK_ITEM_PRIORITY: ("IC-MISSION-CMD-005", "mission.work.priority.change"),
    }
    expected_queries = {
        WS004QueryName.LIST_MISSION_WORK_ITEMS: "IC-MISSION-QRY-004",
        WS004QueryName.RETRIEVE_MISSION_WORK_ITEM: "IC-MISSION-QRY-005",
    }
    expected_events = {
        WS004EventName.MISSION_WORK_ITEM_CREATED: "IC-MISSION-EVT-002",
        WS004EventName.MISSION_WORK_ITEM_ASSIGNED: "IC-MISSION-EVT-003",
        WS004EventName.MISSION_WORK_ITEM_UNASSIGNED: "IC-MISSION-EVT-004",
        WS004EventName.MISSION_WORK_ITEM_STATUS_CHANGED: "IC-MISSION-EVT-005",
        WS004EventName.MISSION_WORK_ITEM_PRIORITY_CHANGED: "IC-MISSION-EVT-006",
    }
    for name, (contract_id, authority) in expected_commands.items():
        contract = command_contracts[name]
        assert (contract.interaction_contract_id, contract.required_authority_scope) == (contract_id, authority)
        assert contract.mutating is True and contract.requires_actor is True and contract.requires_authority is True
    for name, contract_id in expected_queries.items():
        contract = query_contracts[name]
        assert (contract.interaction_contract_id, contract.required_authority_scope) == (contract_id, "mission.work.read")
        assert contract.mutating is False and contract.requires_actor is True and contract.requires_authority is True
    for name, contract_id in expected_events.items():
        contract = event_contracts[name]
        assert contract.interaction_contract_id == contract_id
        assert contract.mutating is False and contract.requires_actor is False


def test_ws005_timeline_contract_bindings_are_governed_and_unique() -> None:
    command = command_contracts[WS005CommandName.ADD_MISSION_WORK_ITEM_COMMENT]
    query = query_contracts[WS005QueryName.RETRIEVE_MISSION_WORK_TIMELINE]
    event = event_contracts[WS005EventName.MISSION_WORK_ITEM_COMMENT_ADDED]

    assert (command.interaction_contract_id, command.required_authority_scope) == (
        "IC-MISSION-CMD-006",
        "mission.work.create",
    )
    assert command.mutating is True and command.requires_actor is True
    assert (query.interaction_contract_id, query.required_authority_scope) == (
        "IC-MISSION-QRY-006",
        "mission.work.read",
    )
    assert query.mutating is False and query.requires_actor is True
    assert event.interaction_contract_id == "IC-MISSION-EVT-007"
    assert event.mutating is False and event.requires_actor is False

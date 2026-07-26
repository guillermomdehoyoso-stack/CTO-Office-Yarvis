from datetime import datetime, timezone

import pytest

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import (
    WS001CommandName,
    WS001QueryName,
    command_contracts,
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

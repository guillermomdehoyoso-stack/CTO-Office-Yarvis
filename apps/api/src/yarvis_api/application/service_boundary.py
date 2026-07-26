"""Boundary guard utilities for WS-001 application contracts."""

from __future__ import annotations

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import ApplicationContract
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata


def enforce_command_boundary(
    contract: ApplicationContract,
    *,
    metadata: RequestMetadata,
    principal: AuthenticatedPrincipal | None,
) -> None:
    if not contract.mutating:
        raise ApplicationError(
            code=ApplicationErrorCode.INTERNAL_ERROR,
            message="command boundary requires mutating contract",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.requires_actor and principal is None:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="mutating command requires actor context",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.requires_authority and (principal is None or not principal.authority.strip()):
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="mutating command requires authority context",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.required_authority_scope is not None and principal is not None and principal.authority != contract.required_authority_scope:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="insufficient authority scope",
            details={
                "contract": contract.interaction_contract_id,
                "required_authority_scope": contract.required_authority_scope,
                "provided_authority_scope": principal.authority,
            },
        )

    if contract.requires_idempotency_key and metadata.idempotency_key is None:
        raise ApplicationError(
            code=ApplicationErrorCode.PRECONDITION_FAILED,
            message="idempotency key is required for this command",
            details={"contract": contract.interaction_contract_id},
        )

    if metadata.command_id is None:
        raise ApplicationError(
            code=ApplicationErrorCode.VALIDATION_FAILED,
            message="command_id is required for command processing",
            details={"contract": contract.interaction_contract_id},
        )


def enforce_query_boundary(
    contract: ApplicationContract,
    *,
    metadata: RequestMetadata,
    principal: AuthenticatedPrincipal | None = None,
) -> None:
    if contract.mutating:
        raise ApplicationError(
            code=ApplicationErrorCode.INTERNAL_ERROR,
            message="query boundary requires non-mutating contract",
            details={"contract": contract.interaction_contract_id},
        )

    if metadata.query_id is None:
        raise ApplicationError(
            code=ApplicationErrorCode.VALIDATION_FAILED,
            message="query_id is required for query processing",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.requires_actor and principal is None:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="governed query requires actor context",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.requires_authority and (principal is None or not principal.authority.strip()):
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="governed query requires authority context",
            details={"contract": contract.interaction_contract_id},
        )

    if contract.required_authority_scope is not None and principal is not None and principal.authority != contract.required_authority_scope:
        raise ApplicationError(
            code=ApplicationErrorCode.AUTHORIZATION_DENIED,
            message="insufficient authority scope",
            details={
                "contract": contract.interaction_contract_id,
                "required_authority_scope": contract.required_authority_scope,
                "provided_authority_scope": principal.authority,
            },
        )

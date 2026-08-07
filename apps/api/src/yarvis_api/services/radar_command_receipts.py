"""Shared durable command infrastructure for the future Radar F command slice.

This module deliberately has no FastAPI dependency and no Radar route imports.
Handlers supply a current authority resolver, which is called before receipt lookup.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.radar import RadarCommandReceipt


_AUTHORITY_FIELDS = frozenset(
    {
        "actor",
        "actor_id",
        "authority",
        "membership",
        "membership_id",
        "organization",
        "organization_id",
        "permission",
        "permissions",
        "principal",
        "principal_id",
        "role",
        "roles",
        "workspace",
        "workspace_id",
    }
)


@dataclass(frozen=True, slots=True)
class CommandResultReference:
    """Minimal safe reference used to reconstruct a future public response."""

    resource_type: str
    resource_id: UUID
    status_code: int

    def __post_init__(self) -> None:
        if not self.resource_type.strip() or len(self.resource_type) > 100:
            raise ValueError("result resource_type must be nonblank and at most 100 characters")
        if not 200 <= self.status_code < 300:
            raise ValueError("durable command results must have a successful HTTP status code")


@dataclass(frozen=True, slots=True)
class DurableCommandResult:
    command_id: UUID
    correlation_id: UUID
    result: CommandResultReference
    replayed: bool


@dataclass(frozen=True, slots=True)
class CommandExecutionContext:
    """Metadata a future handler passes to its atomic activity/event writes."""

    envelope: IdentityAuthorityEnvelope
    command_id: UUID
    correlation_id: UUID
    input_causation_id: UUID | None


def _normalise(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalise(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key).casefold() not in _AUTHORITY_FIELDS
        }
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError(f"unsupported functional payload value: {type(value).__name__}")


def request_fingerprint(
    *,
    command_type: str,
    contract_version: str,
    target_id: UUID | None,
    functional_payload: Mapping[str, Any],
) -> str:
    """Create the SHA-256 fingerprint without client authority claims."""

    if not command_type.strip() or not contract_version.strip():
        raise ValueError("command_type and contract_version must be nonblank")
    canonical = {
        "command_type": command_type,
        "contract_version": contract_version,
        "target_id": str(target_id) if target_id is not None else None,
        "functional_payload": _normalise(functional_payload),
    }
    encoded = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _idempotency_key(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 255:
        raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid idempotency key", {"reason": "idempotency_key"})
    return normalized


def _correlation_id(value: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return uuid4()


def _replayed(receipt: RadarCommandReceipt) -> DurableCommandResult:
    return DurableCommandResult(
        command_id=receipt.command_id,
        correlation_id=receipt.correlation_id,
        result=CommandResultReference(
            resource_type=receipt.result_resource_type,
            resource_id=receipt.result_resource_id,
            status_code=receipt.result_status_code,
        ),
        replayed=True,
    )


class RadarCommandReceiptService:
    """Reserve, execute and persist one organization-scoped Radar command."""

    def execute(
        self,
        db: Session,
        *,
        resolve_authority: Callable[[], IdentityAuthorityEnvelope],
        command_type: str,
        contract_version: str,
        idempotency_key: str,
        functional_payload: Mapping[str, Any],
        mutation: Callable[[CommandExecutionContext], CommandResultReference],
        target_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> DurableCommandResult:
        """Execute the callback and receipt in the caller's transaction.

        The authority resolver is called before receipt lookup.  The nested
        transaction makes receipt and callback effects roll back together while
        leaving the caller free to compose a wider local unit of work.
        """

        # Resolving before receipt lookup is deliberate: a revocation denies a
        # retried command before any old result can be returned.
        envelope = resolve_authority()
        key = _idempotency_key(idempotency_key)
        fingerprint = request_fingerprint(
            command_type=command_type,
            contract_version=contract_version,
            target_id=target_id,
            functional_payload=functional_payload,
        )
        existing = self._existing(db, envelope, command_type, key)
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise ApplicationError(
                    ApplicationErrorCode.CONFLICT,
                    "idempotency key conflicts with a different command",
                    {"reason": "idempotency_conflict"},
                )
            return _replayed(existing)

        command_id = uuid4()
        correlation_id = _correlation_id(envelope.correlation_id)
        context = CommandExecutionContext(
            envelope=envelope,
            command_id=command_id,
            correlation_id=correlation_id,
            input_causation_id=causation_id,
        )
        try:
            with db.begin_nested():
                result = mutation(context)
                receipt = RadarCommandReceipt(
                    command_id=command_id,
                    organization_id=envelope.organization_id,
                    command_type=command_type,
                    contract_version=contract_version,
                    idempotency_key=key,
                    request_fingerprint=fingerprint,
                    actor_principal_id=envelope.principal_id,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    result_status_code=result.status_code,
                    result_resource_type=result.resource_type,
                    result_resource_id=result.resource_id,
                    status="succeeded",
                )
                db.add(receipt)
                db.flush()
        except IntegrityError:
            # A competing committed command may have won the unique receipt
            # reservation.  Its mutation was protected by the same savepoint.
            existing = self._existing(db, envelope, command_type, key)
            if existing is None:
                raise
            if existing.request_fingerprint != fingerprint:
                raise ApplicationError(
                    ApplicationErrorCode.CONFLICT,
                    "idempotency key conflicts with a different command",
                    {"reason": "idempotency_conflict"},
                )
            return _replayed(existing)
        return DurableCommandResult(command_id=command_id, correlation_id=correlation_id, result=result, replayed=False)

    @staticmethod
    def _existing(
        db: Session,
        envelope: IdentityAuthorityEnvelope,
        command_type: str,
        key: str,
    ) -> RadarCommandReceipt | None:
        return db.scalar(
            select(RadarCommandReceipt).where(
                RadarCommandReceipt.organization_id == envelope.organization_id,
                RadarCommandReceipt.command_type == command_type,
                RadarCommandReceipt.idempotency_key == key,
            )
        )

"""Netpay Master durable receipts with authority checked before replay."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.netpay_master import NetpayMasterCommandReceipt


@dataclass(frozen=True)
class MasterResult:
    resource_type: str
    resource_id: UUID
    status_code: int
    replayed: bool = False
    command_id: UUID | None = None
    correlation_id: UUID | None = None


def fingerprint(command_type: str, target_id: UUID | None, payload: Mapping[str, Any]) -> str:
    value = {"command_type": command_type, "target_id": str(target_id) if target_id else None, "payload": payload}
    return sha256(json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class NetpayMasterReceiptService:
    def execute(self, db: Session, *, resolve_authority: Callable[[], IdentityAuthorityEnvelope], command_type: str, idempotency_key: str, payload: Mapping[str, Any], mutation: Callable[[UUID, UUID, IdentityAuthorityEnvelope], MasterResult], target_id: UUID | None = None) -> MasterResult:
        envelope = resolve_authority()
        key = idempotency_key.strip()
        if not key or len(key) > 255:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "invalid idempotency key", {"reason": "idempotency_key"})
        request_fingerprint = fingerprint(command_type, target_id, payload)
        existing = db.scalar(select(NetpayMasterCommandReceipt).where(NetpayMasterCommandReceipt.organization_id == envelope.organization_id, NetpayMasterCommandReceipt.command_type == command_type, NetpayMasterCommandReceipt.idempotency_key == key))
        if existing:
            if existing.request_fingerprint != request_fingerprint:
                raise ApplicationError(ApplicationErrorCode.CONFLICT, "idempotency key conflicts with a different command", {"reason": "idempotency_conflict"})
            return MasterResult(existing.result_resource_type, existing.result_resource_id, existing.result_status_code, True, existing.command_id, existing.correlation_id)
        command_id = uuid4()
        try:
            correlation_id = UUID(envelope.correlation_id)
        except (TypeError, ValueError):
            correlation_id = uuid4()
        with db.begin_nested():
            result = mutation(command_id, correlation_id, envelope)
            db.add(NetpayMasterCommandReceipt(command_id=command_id, organization_id=envelope.organization_id, command_type=command_type, idempotency_key=key, request_fingerprint=request_fingerprint, actor_principal_id=envelope.principal_id, correlation_id=correlation_id, result_resource_type=result.resource_type, result_resource_id=result.resource_id, result_status_code=result.status_code))
            db.flush()
        return MasterResult(result.resource_type, result.resource_id, result.status_code, False, command_id, correlation_id)

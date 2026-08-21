"""Canonical Identity CMD-002/003 application services."""

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.person import Person
from yarvis_api.models.principal import Principal
from yarvis_api.models.productive_auth import ExternalIdentityBinding, IdentityProvisioningReceipt


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _receipt(
    db: Session,
    *,
    envelope: IdentityAuthorityEnvelope,
    contract_id: str,
    idempotency_key: str,
    fingerprint: str,
):
    scope = f"{envelope.organization_id}:{envelope.principal_id}"
    item = db.scalar(
        select(IdentityProvisioningReceipt).where(
            IdentityProvisioningReceipt.contract_id == contract_id,
            IdentityProvisioningReceipt.authority_scope == scope,
            IdentityProvisioningReceipt.idempotency_key_hash == _hash(idempotency_key),
        )
    )
    if item is not None and item.request_fingerprint != fingerprint:
        raise ApplicationError(
            ApplicationErrorCode.CONFLICT,
            "idempotency key conflicts",
            {"reason": "idempotency_conflict"},
        )
    return item, scope


class IdentityProvisioningService:
    def bind_external_identity(
        self,
        db: Session,
        *,
        envelope: IdentityAuthorityEnvelope,
        principal_id,
        issuer: str,
        normalized_subject: str,
        normalization_version: str,
        provenance_receipt_hash: str,
        idempotency_key: str,
    ) -> ExternalIdentityBinding:
        envelope.require("identity.binding.manage")
        fingerprint = _hash(
            "|".join((str(principal_id), issuer, normalized_subject, normalization_version, provenance_receipt_hash))
        )
        receipt, scope = _receipt(
            db,
            envelope=envelope,
            contract_id="IC-IDENTITY-CMD-002",
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )
        if receipt is not None:
            replayed = db.get(ExternalIdentityBinding, receipt.aggregate_id)
            if replayed is None:
                raise ApplicationError(ApplicationErrorCode.CONFLICT, "receipt target missing")
            return replayed
        if not issuer.startswith("https://") or not normalized_subject or len(normalized_subject) > 512:
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "identity binding denied",
                {"reason": "invalid_provenance"},
            )
        principal = db.scalar(select(Principal).where(Principal.id == principal_id, Principal.status == "active"))
        if principal is None:
            raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "principal"})
        collision = db.scalar(
            select(ExternalIdentityBinding).where(
                ExternalIdentityBinding.issuer == issuer,
                ExternalIdentityBinding.normalized_subject == normalized_subject,
            )
        )
        if collision is not None:
            raise ApplicationError(ApplicationErrorCode.CONFLICT, "identity binding denied", {"reason": "collision"})
        binding = ExternalIdentityBinding(
            principal_id=principal.id,
            issuer=issuer,
            normalized_subject=normalized_subject,
            normalization_version=normalization_version,
            provenance_receipt_hash=provenance_receipt_hash,
            status="active",
        )
        db.add(binding)
        db.flush()
        db.add(
            IdentityProvisioningReceipt(
                contract_id="IC-IDENTITY-CMD-002",
                authority_scope=scope,
                idempotency_key_hash=_hash(idempotency_key),
                request_fingerprint=fingerprint,
                aggregate_id=binding.id,
            )
        )
        record_event(
            db,
            event_type="ExternalIdentityBound",
            aggregate_type="ExternalIdentityBinding",
            aggregate_id=binding.id,
            payload={
                "contract_id": "IC-IDENTITY-EVT-002",
                "principal_id": str(principal.id),
                "normalization_version": normalization_version,
                "provenance_receipt_hash": provenance_receipt_hash,
            },
        )
        db.flush()
        return binding

    def link_principal_to_person(
        self,
        db: Session,
        *,
        envelope: IdentityAuthorityEnvelope,
        principal_id,
        person_id,
        approval_receipt_hash: str,
        idempotency_key: str,
    ) -> Principal:
        envelope.require("identity.principal.link")
        fingerprint = _hash(f"{principal_id}|{person_id}|{approval_receipt_hash}")
        receipt, scope = _receipt(
            db,
            envelope=envelope,
            contract_id="IC-IDENTITY-CMD-003",
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )
        if receipt is not None:
            replayed = db.get(Principal, receipt.aggregate_id)
            if replayed is None:
                raise ApplicationError(ApplicationErrorCode.CONFLICT, "receipt target missing")
            return replayed
        principal = db.get(Principal, principal_id)
        person = db.get(Person, person_id)
        if principal is None or person is None:
            raise ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "not found", {"reason": "target"})
        if principal.person_id is not None and principal.person_id != person.id:
            raise ApplicationError(ApplicationErrorCode.CONFLICT, "principal link denied", {"reason": "conflict"})
        principal.person_id = person.id
        db.add(
            IdentityProvisioningReceipt(
                contract_id="IC-IDENTITY-CMD-003",
                authority_scope=scope,
                idempotency_key_hash=_hash(idempotency_key),
                request_fingerprint=fingerprint,
                aggregate_id=principal.id,
            )
        )
        record_event(
            db,
            event_type="PrincipalLinkedToPerson",
            aggregate_type="Principal",
            aggregate_id=principal.id,
            payload={
                "contract_id": "IC-IDENTITY-EVT-003",
                "person_id": str(person.id),
                "approval_receipt_hash": approval_receipt_hash,
            },
        )
        db.flush()
        return principal

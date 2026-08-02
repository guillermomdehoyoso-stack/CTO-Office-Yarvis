"""Governed DI-003 Slice 01 Opportunity commands and query."""

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from yarvis_api.application.contracts import DI003CommandName, DI003QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.opportunity import Opportunity, OpportunityCommandIdempotency
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.opportunity import OpportunityRead
from yarvis_api.services.inbound_intake import _principal_organization_id


def _error(code: ApplicationErrorCode, message: str) -> ApplicationError:
    return ApplicationError(code, message, {"resource": "opportunity"})


def _not_found() -> ApplicationError:
    return _error(ApplicationErrorCode.RESOURCE_NOT_FOUND, "opportunity not found")


def _key(metadata) -> str:
    if not metadata.idempotency_key:
        raise _error(ApplicationErrorCode.PRECONDITION_FAILED, "idempotency key is required")
    return metadata.idempotency_key


def _fingerprint(contract_id: str, organization_id: UUID, payload: dict) -> str:
    return sha256(dumps({"contract_id": contract_id, "organization_id": str(organization_id), "payload": payload}, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


@dataclass(slots=True)
class OpportunityService:
    persistence: PersistenceRuntime

    def propose(self, command, metadata, principal) -> OpportunityRead:
        contract = command_contracts[DI003CommandName.PROPOSE]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        organization_id, idempotency_key = _principal_organization_id(principal), _key(metadata)
        fingerprint = _fingerprint(contract.interaction_contract_id, organization_id, asdict(command))
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                receipt = self._receipt(session, organization_id, contract.interaction_contract_id, idempotency_key)
                if receipt:
                    return self._replay(session, receipt, fingerprint)
                opportunity = Opportunity(organization_id=organization_id, business_intent=command.business_intent.strip())
                if not opportunity.business_intent:
                    raise _error(ApplicationErrorCode.VALIDATION_FAILED, "business intent is required")
                session.add(opportunity)
                session.flush()
                self._event(session, opportunity, "opportunity.proposed", metadata, principal, {"business_intent": opportunity.business_intent})
                self._add_receipt(session, organization_id, contract.interaction_contract_id, idempotency_key, fingerprint, opportunity)
                result = OpportunityRead.model_validate(opportunity)
                unit_of_work.commit()
                return result
        except IntegrityError as exc:
            return self._recover_receipt(exc, organization_id, contract.interaction_contract_id, idempotency_key, fingerprint)

    def confirm(self, command, metadata, principal) -> OpportunityRead:
        contract = command_contracts[DI003CommandName.CONFIRM]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        organization_id, idempotency_key = _principal_organization_id(principal), _key(metadata)
        fingerprint = _fingerprint(contract.interaction_contract_id, organization_id, {"opportunity_id": str(command.opportunity_id), "expected_version": command.expected_version})
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                receipt = self._receipt(session, organization_id, contract.interaction_contract_id, idempotency_key)
                if receipt:
                    return self._replay(session, receipt, fingerprint)
                opportunity = self._opportunity(session, command.opportunity_id, organization_id, lock=True)
                receipt = self._receipt(session, organization_id, contract.interaction_contract_id, idempotency_key)
                if receipt:
                    return self._replay(session, receipt, fingerprint)
                if opportunity.aggregate_version != command.expected_version:
                    raise _error(ApplicationErrorCode.CONFLICT, "opportunity version conflict")
                if opportunity.lifecycle_status != "proposed":
                    raise _error(ApplicationErrorCode.CONFLICT, "opportunity is already confirmed")
                opportunity.lifecycle_status = "confirmed"
                opportunity.confirmed_at = utc_now()
                opportunity.confirmed_by_subject_id = principal.actor_id
                opportunity.aggregate_version += 1
                opportunity.updated_at = utc_now()
                self._event(session, opportunity, "opportunity.confirmed", metadata, principal, {"idempotency_key": idempotency_key})
                self._add_receipt(session, organization_id, contract.interaction_contract_id, idempotency_key, fingerprint, opportunity)
                result = OpportunityRead.model_validate(opportunity)
                unit_of_work.commit()
                return result
        except IntegrityError as exc:
            return self._recover_receipt(exc, organization_id, contract.interaction_contract_id, idempotency_key, fingerprint)

    def _receipt(self, session, organization_id, contract_id, idempotency_key):
        return session.scalar(select(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.organization_id == organization_id, OpportunityCommandIdempotency.contract_id == contract_id, OpportunityCommandIdempotency.idempotency_key == idempotency_key))

    def _opportunity(self, session, opportunity_id, organization_id, lock=False):
        query = select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id)
        if lock:
            query = query.with_for_update()
        opportunity = session.scalar(query)
        if opportunity is None:
            raise _not_found()
        return opportunity

    def _replay(self, session, receipt, fingerprint):
        if receipt.request_fingerprint != fingerprint:
            raise _error(ApplicationErrorCode.CONFLICT, "idempotency key was previously used for a different opportunity command")
        opportunity = self._opportunity(session, receipt.aggregate_id, receipt.organization_id)
        return OpportunityRead.model_validate(opportunity)

    def _add_receipt(self, session, organization_id, contract_id, idempotency_key, fingerprint, opportunity):
        session.add(OpportunityCommandIdempotency(organization_id=organization_id, contract_id=contract_id, idempotency_key=idempotency_key, request_fingerprint=fingerprint, aggregate_id=opportunity.id, response_kind="opportunity", response_payload={"opportunity_id": str(opportunity.id)}))

    def _recover_receipt(self, exc, organization_id, contract_id, idempotency_key, fingerprint):
        if not (isinstance(exc.orig, UniqueViolation) and exc.orig.diag.constraint_name == "uq_opportunity_command_idempotency"):
            raise exc
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            receipt = self._receipt(unit_of_work.session, organization_id, contract_id, idempotency_key)
            if receipt is None:
                raise _error(ApplicationErrorCode.CONFLICT, "idempotency receipt unavailable")
            return self._replay(unit_of_work.session, receipt, fingerprint)

    def _event(self, session, opportunity, event_type, metadata, principal, payload):
        record_event(session, event_type=event_type, aggregate_type="opportunity", aggregate_id=opportunity.id, organization_id=opportunity.organization_id, correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload={**payload, "actor_subject_id": principal.actor_id, "authority_scope": principal.authority})


@dataclass(frozen=True, slots=True)
class OpportunityQueryService:
    def get(self, session, opportunity_id, principal, metadata) -> OpportunityRead:
        enforce_query_boundary(query_contracts[DI003QueryName.GET], metadata=metadata, principal=principal)
        return OpportunityRead.model_validate(OpportunityService(None)._opportunity(session, opportunity_id, _principal_organization_id(principal)))

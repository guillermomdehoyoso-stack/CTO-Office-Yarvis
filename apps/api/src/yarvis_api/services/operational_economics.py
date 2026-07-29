"""Governed append-only Operational Economics application services."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from hashlib import sha256
from json import dumps
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import OV002CommandName, OV002EventName, OV002QueryName, command_contracts, event_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.operational_economics import CorrectEconomicFactCommand, RecordEconomicFactCommand
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.operational_context import Project
from yarvis_api.models.operational_economics import EconomicFact
from yarvis_api.models.process import ProcessInstance
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.operational_economics import EconomicFactHistory, EconomicFactRead, EconomicSummary
from yarvis_api.services.inbound_intake import _principal_organization_id


_FACT_TYPES = {
    "revenue_expected", "revenue_contracted", "cost_estimated", "cost_committed",
    "cost_incurred", "labor_cost", "cash_in", "cash_out", "cost_to_complete",
}
_SUBJECT_TYPES = {"project", "mission_work_item", "process_instance", "task"}
_IDEMPOTENCY_CONSTRAINT = "uq_economic_facts_org_idempotency"


def _not_found() -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "operational economics resource not found", {"resource": "operational_economics"})


def _conflict(message: str) -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.CONFLICT, message, {"resource": "economic_fact"})


def _read(fact: EconomicFact) -> EconomicFactRead:
    return EconomicFactRead.model_validate(fact)


def build_direct_summary(subject_type: str, subject_id: UUID, currency: str, facts: list[EconomicFact], requested_at: datetime) -> EconomicSummary:
    """Apply the canonical OV-001 direct-subject metric policy once."""
    totals = {fact_type: Decimal("0") for fact_type in _FACT_TYPES}
    for fact in facts:
        totals[fact.fact_type] += fact.amount
    revenue_basis = totals["revenue_contracted"] or totals["revenue_expected"]
    projected = totals["cost_incurred"] + totals["cost_to_complete"]
    profit = revenue_basis - projected
    return EconomicSummary(
        subject_type=subject_type, subject_id=subject_id, currency=currency,
        as_of=max((fact.created_at for fact in facts), default=requested_at),
        expected_revenue=totals["revenue_expected"], contracted_revenue=totals["revenue_contracted"],
        estimated_cost=totals["cost_estimated"], committed_cost=totals["cost_committed"],
        incurred_cost=totals["cost_incurred"], labor_cost=totals["labor_cost"],
        estimated_cost_to_complete=totals["cost_to_complete"], projected_total_cost=projected,
        cash_received=totals["cash_in"], cash_paid=totals["cash_out"],
        net_cash_position=totals["cash_in"] - totals["cash_out"], expected_final_profit=profit,
        expected_final_margin_percent=(profit * Decimal("100") / revenue_basis) if revenue_basis else None,
        input_fact_ids=[fact.id for fact in facts], availability="AVAILABLE" if facts else "UNAVAILABLE",
    )


@dataclass(slots=True)
class OperationalEconomicsService:
    persistence: PersistenceRuntime

    def record(self, command: RecordEconomicFactCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> EconomicFactRead:
        enforce_command_boundary(command_contracts[OV002CommandName.RECORD_ECONOMIC_FACT], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._key(metadata)
        fingerprint = self._fingerprint("record", command)
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                replay = self._by_key(session, organization_id, key)
                if replay is not None:
                    return self._replay(replay, fingerprint)
                self._validate_fact(command)
                self._lock_subject(session, command.subject_type, command.subject_id, organization_id)
                self._validate_current_cost_to_complete(session, command, organization_id, None)
                fact = self._new_fact(command, metadata, principal, organization_id, key, fingerprint)
                session.add(fact)
                session.flush()
                self._event(session, fact, OV002EventName.ECONOMIC_FACT_RECORDED, metadata)
                result = _read(fact)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if isinstance(error.orig, UniqueViolation) and getattr(error.orig.diag, "constraint_name", None) == _IDEMPOTENCY_CONSTRAINT:
                return self._concurrent_replay(organization_id, key, fingerprint, error)
            raise

    def correct(self, command: CorrectEconomicFactCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> EconomicFactRead:
        enforce_command_boundary(command_contracts[OV002CommandName.CORRECT_ECONOMIC_FACT], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._key(metadata)
        fingerprint = self._fingerprint("correct", command)
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                replay = self._by_key(session, organization_id, key)
                if replay is not None:
                    return self._replay(replay, fingerprint)
                previous = session.scalar(select(EconomicFact).where(EconomicFact.id == command.fact_id).where(EconomicFact.organization_id == organization_id).with_for_update())
                if previous is None:
                    raise _not_found()
                self._lock_subject(session, previous.subject_type, previous.subject_id, organization_id)
                if session.scalar(select(EconomicFact.id).where(EconomicFact.supersedes_fact_id == previous.id)) is not None:
                    raise _conflict("economic fact is already superseded")
                replacement = RecordEconomicFactCommand(
                    previous.subject_type, previous.subject_id, previous.fact_type, command.amount,
                    previous.currency, command.effective_at, command.source_type,
                    command.source_reference, command.evidence_references,
                )
                self._validate_current_cost_to_complete(session, replacement, organization_id, previous.id)
                fact = self._new_fact(replacement, metadata, principal, organization_id, key, fingerprint, supersedes_fact_id=previous.id, correction_reason=command.correction_reason)
                session.add(fact)
                session.flush()
                self._event(session, fact, OV002EventName.ECONOMIC_FACT_CORRECTED, metadata)
                result = _read(fact)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if isinstance(error.orig, UniqueViolation) and getattr(error.orig.diag, "constraint_name", None) == _IDEMPOTENCY_CONSTRAINT:
                return self._concurrent_replay(organization_id, key, fingerprint, error)
            raise

    @staticmethod
    def _key(metadata: RequestMetadata) -> str:
        if metadata.idempotency_key is None:
            raise ApplicationError(ApplicationErrorCode.PRECONDITION_FAILED, "idempotency key is required for economic facts", {"resource": "economic_fact"})
        return metadata.idempotency_key

    @staticmethod
    def _fingerprint(action: str, command: object) -> str:
        values = {key: str(value) for key, value in asdict(command).items()}
        return sha256(dumps({"action": action, "request": values}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _validate_fact(command: RecordEconomicFactCommand) -> None:
        if command.subject_type not in _SUBJECT_TYPES or command.fact_type not in _FACT_TYPES:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "unsupported economic subject or fact type", {"resource": "economic_fact"})
        if command.currency != command.currency.upper() or len(command.currency) != 3:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "currency must be uppercase ISO-4217 form", {"resource": "economic_fact"})

    @staticmethod
    def _lock_subject(session: Session, subject_type: str, subject_id: UUID, organization_id: UUID) -> None:
        model = {"project": Project, "mission_work_item": MissionWorkItem, "process_instance": ProcessInstance}.get(subject_type)
        if model is None:
            raise _not_found()
        subject = session.scalar(select(model).where(model.id == subject_id).where(model.organization_id == organization_id).with_for_update())
        if subject is None:
            raise _not_found()

    @staticmethod
    def _validate_current_cost_to_complete(session: Session, command: RecordEconomicFactCommand, organization_id: UUID, replaces_id: UUID | None) -> None:
        if command.fact_type != "cost_to_complete":
            return
        current = session.scalar(
            select(EconomicFact)
            .where(EconomicFact.organization_id == organization_id)
            .where(EconomicFact.subject_type == command.subject_type)
            .where(EconomicFact.subject_id == command.subject_id)
            .where(EconomicFact.currency == command.currency)
            .where(EconomicFact.fact_type == "cost_to_complete")
            .where(~EconomicFact.id.in_(select(EconomicFact.supersedes_fact_id).where(EconomicFact.supersedes_fact_id.is_not(None))))
            .with_for_update()
        )
        if current is not None and current.id != replaces_id:
            raise _conflict("cost to complete requires correction of the current forecast")

    @staticmethod
    def _new_fact(command: RecordEconomicFactCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal, organization_id: UUID, key: str, fingerprint: str, *, supersedes_fact_id: UUID | None = None, correction_reason: str | None = None) -> EconomicFact:
        return EconomicFact(
            organization_id=organization_id, subject_type=command.subject_type, subject_id=command.subject_id,
            fact_type=command.fact_type, amount=command.amount, currency=command.currency,
            effective_at=command.effective_at, source_type=command.source_type,
            source_reference=command.source_reference, evidence_references=list(command.evidence_references),
            actor_subject_id=principal.actor_id, authority_scope=principal.authority,
            correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None,
            idempotency_key=key, request_fingerprint=fingerprint, supersedes_fact_id=supersedes_fact_id,
            correction_reason=correction_reason,
        )

    @staticmethod
    def _event(session: Session, fact: EconomicFact, event_name: OV002EventName, metadata: RequestMetadata) -> None:
        contract = event_contracts[event_name]
        record_event(session, event_type="economic_fact.recorded" if event_name == OV002EventName.ECONOMIC_FACT_RECORDED else "economic_fact.corrected", aggregate_type="economic_fact", aggregate_id=fact.id, organization_id=fact.organization_id, correlation_id=fact.correlation_id, causation_id=fact.causation_id, payload={
            "interaction_contract_id": contract.interaction_contract_id, "economic_fact_id": str(fact.id),
            "subject_type": fact.subject_type, "subject_id": str(fact.subject_id), "fact_type": fact.fact_type,
            "amount": str(fact.amount), "currency": fact.currency, "effective_at": fact.effective_at.isoformat(),
            "source_type": fact.source_type, "source_reference": fact.source_reference,
            "actor_subject_id": fact.actor_subject_id, "authority_scope": fact.authority_scope,
            "supersedes_fact_id": str(fact.supersedes_fact_id) if fact.supersedes_fact_id else None,
            "correction_reason": fact.correction_reason,
        })

    @staticmethod
    def _by_key(session: Session, organization_id: UUID, key: str) -> EconomicFact | None:
        return session.scalar(select(EconomicFact).where(EconomicFact.organization_id == organization_id).where(EconomicFact.idempotency_key == key))

    @staticmethod
    def _replay(fact: EconomicFact, fingerprint: str) -> EconomicFactRead:
        if fact.request_fingerprint != fingerprint:
            raise _conflict("idempotency key was previously used for a different economic fact command")
        return _read(fact)

    def _concurrent_replay(self, organization_id: UUID, key: str, fingerprint: str, error: IntegrityError) -> EconomicFactRead:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            fact = self._by_key(unit_of_work.session, organization_id, key)
            if fact is None:
                raise error
            return self._replay(fact, fingerprint)


@dataclass(frozen=True, slots=True)
class OperationalEconomicsQueryService:
    def history(self, session: Session, subject_type: str, subject_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> EconomicFactHistory:
        enforce_query_boundary(query_contracts[OV002QueryName.RETRIEVE_ECONOMIC_FACT_HISTORY], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        OperationalEconomicsService._lock_subject(session, subject_type, subject_id, organization_id)
        facts = session.scalars(select(EconomicFact).where(EconomicFact.organization_id == organization_id).where(EconomicFact.subject_type == subject_type).where(EconomicFact.subject_id == subject_id).order_by(EconomicFact.created_at.asc(), EconomicFact.id.asc())).all()
        return EconomicFactHistory(items=[_read(fact) for fact in facts])

    def summary(self, session: Session, subject_type: str, subject_id: UUID, currency: str, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> EconomicSummary:
        enforce_query_boundary(query_contracts[OV002QueryName.RETRIEVE_OPERATIONAL_ECONOMICS], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        if currency != currency.upper() or len(currency) != 3:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "currency must be uppercase ISO-4217 form", {"resource": "economic_fact"})
        OperationalEconomicsService._lock_subject(session, subject_type, subject_id, organization_id)
        superseded = select(EconomicFact.supersedes_fact_id).where(EconomicFact.organization_id == organization_id).where(EconomicFact.supersedes_fact_id.is_not(None))
        facts = session.scalars(select(EconomicFact).where(EconomicFact.organization_id == organization_id).where(EconomicFact.subject_type == subject_type).where(EconomicFact.subject_id == subject_id).where(EconomicFact.currency == currency).where(~EconomicFact.id.in_(superseded)).order_by(EconomicFact.effective_at.asc(), EconomicFact.id.asc())).all()
        return build_direct_summary(subject_type, subject_id, currency, facts, metadata.requested_at)

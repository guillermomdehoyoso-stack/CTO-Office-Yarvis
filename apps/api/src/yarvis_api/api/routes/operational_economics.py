"""Governed Operational Economics API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.operational_economics_authority import economics_fact_recorder_principal_from_envelope
from yarvis_api.application.operational_economics import CorrectEconomicFactCommand, RecordEconomicFactCommand
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.schemas.operational_economics import (
    CorrectEconomicFactRequest,
    EconomicFactHistory,
    EconomicFactRead,
    EconomicSummary,
    RecordEconomicFactRequest,
)


router = APIRouter(prefix="/operational-economics", tags=["operational-economics"])


def _principal(request: Request):
    return request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))


@router.post("/facts", response_model=EconomicFactRead, status_code=status.HTTP_201_CREATED)
def record_fact(payload: RecordEconomicFactRequest, request: Request, db: Session = Depends(get_db)) -> EconomicFactRead:
    authenticated = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    envelope = AuthorityResolutionService().resolve(
        db, external_subject=authenticated.actor_id, selector=None,
        authentication_source=authenticated.authentication_method,
        correlation_id=authenticated.correlation_id or str(uuid4()),
    )
    principal = economics_fact_recorder_principal_from_envelope(envelope)
    return request.app.state.yarvis.operational_economics_service.record(
        RecordEconomicFactCommand(
            payload.subject_type, payload.subject_id, payload.fact_type, payload.amount,
            payload.currency, payload.effective_at, payload.source_type, payload.source_reference,
            tuple(payload.evidence_references),
        ),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="record_economic_fact", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )


@router.post("/facts/{fact_id}/corrections", response_model=EconomicFactRead, status_code=status.HTTP_201_CREATED)
def correct_fact(fact_id: UUID, payload: CorrectEconomicFactRequest, request: Request) -> EconomicFactRead:
    principal = _principal(request)
    return request.app.state.yarvis.operational_economics_service.correct(
        CorrectEconomicFactCommand(
            fact_id, payload.amount, payload.effective_at, payload.source_type,
            payload.source_reference, tuple(payload.evidence_references), payload.correction_reason,
        ),
        RequestMetadata(utc_now(), str(payload.correlation_id), command_id="correct_economic_fact", causation_id=str(payload.causation_id) if payload.causation_id else None, idempotency_key=payload.idempotency_key),
        principal,
    )


@router.get("/subjects/{subject_type}/{subject_id}/facts", response_model=EconomicFactHistory)
def retrieve_history(subject_type: str, subject_id: UUID, request: Request, db: Session = Depends(get_db)) -> EconomicFactHistory:
    principal = _principal(request)
    return request.app.state.yarvis.operational_economics_query_service.history(
        db, subject_type, subject_id, principal,
        RequestMetadata(utc_now(), principal.correlation_id or str(uuid4()), query_id="retrieve_economic_fact_history"),
    )


@router.get("/subjects/{subject_type}/{subject_id}/summary", response_model=EconomicSummary)
def retrieve_summary(subject_type: str, subject_id: UUID, request: Request, currency: str = Query(..., min_length=3, max_length=3), db: Session = Depends(get_db)) -> EconomicSummary:
    principal = _principal(request)
    return request.app.state.yarvis.operational_economics_query_service.summary(
        db, subject_type, subject_id, currency, principal,
        RequestMetadata(utc_now(), principal.correlation_id or str(uuid4()), query_id="retrieve_operational_economics"),
    )

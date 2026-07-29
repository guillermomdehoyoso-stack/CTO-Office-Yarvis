"""API DTOs for the Operational Economics thin slice."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecordEconomicFactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject_type: str = Field(min_length=1, max_length=50)
    subject_id: UUID
    fact_type: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    effective_at: datetime
    source_type: str = Field(min_length=1, max_length=100)
    source_reference: str = Field(min_length=1, max_length=255)
    evidence_references: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class CorrectEconomicFactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    effective_at: datetime
    source_type: str = Field(min_length=1, max_length=100)
    source_reference: str = Field(min_length=1, max_length=255)
    evidence_references: list[str] = Field(default_factory=list)
    correction_reason: str = Field(min_length=1, max_length=1000)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None


class EconomicFactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    subject_type: str
    subject_id: UUID
    fact_type: str
    amount: Decimal
    currency: str
    effective_at: datetime
    source_type: str
    source_reference: str
    evidence_references: list[str]
    actor_subject_id: str
    authority_scope: str
    correlation_id: UUID
    causation_id: UUID | None
    supersedes_fact_id: UUID | None
    correction_reason: str | None
    created_at: datetime


class EconomicFactHistory(BaseModel):
    items: list[EconomicFactRead]


class EconomicSummary(BaseModel):
    subject_type: str
    subject_id: UUID
    currency: str
    as_of: datetime
    expected_revenue: Decimal
    contracted_revenue: Decimal
    estimated_cost: Decimal
    committed_cost: Decimal
    incurred_cost: Decimal
    labor_cost: Decimal
    estimated_cost_to_complete: Decimal
    projected_total_cost: Decimal
    cash_received: Decimal
    cash_paid: Decimal
    net_cash_position: Decimal
    expected_final_profit: Decimal
    expected_final_margin_percent: Decimal | None
    input_fact_ids: list[UUID]
    availability: str

"""Transport-neutral Operational Economics commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RecordEconomicFactCommand:
    subject_type: str
    subject_id: UUID
    fact_type: str
    amount: Decimal
    currency: str
    effective_at: datetime
    source_type: str
    source_reference: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CorrectEconomicFactCommand:
    fact_id: UUID
    amount: Decimal
    effective_at: datetime
    source_type: str
    source_reference: str
    evidence_references: tuple[str, ...]
    correction_reason: str

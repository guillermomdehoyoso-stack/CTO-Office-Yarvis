"""Typed, privacy-safe contracts for historical NetPay evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class HistoricalValidationError:
    source_sheet: str
    source_row_reference: str | None
    source_field: str | None
    error_code: str
    severity: str
    message: str


@dataclass(frozen=True)
class HistoricalHeaderResult:
    original_header: str
    normalized_header: str
    canonical_field: str | None
    mapped: bool
    collision: bool


@dataclass(frozen=True)
class HistoricalSheetClassificationResult:
    classification: str | None
    matching_classifications: list[str]
    structural_conflicts: list[str]
    promotable: bool


@dataclass(frozen=True)
class HistoricalSheetInspection:
    source_sheet: str
    classification: str | None
    source_column_count: int
    candidate_row_count: int
    mapped_headers: list[HistoricalHeaderResult]
    unresolved_headers: list[HistoricalHeaderResult]
    normalized_header_collisions: list[str]
    structural_conflicts: list[str]
    reporting_periods: list[str]
    promotable: bool


@dataclass(frozen=True)
class HistoricalWorkbookInspection:
    document_fingerprint: str
    source_workbook: str
    detected_sheets: list[str]
    supported_sheets: list[str]
    ignored_sheets: list[str]
    unresolved_sheets: list[str]
    sheet_results: list[HistoricalSheetInspection]
    promotable: bool


@dataclass(frozen=True)
class HistoricalEvidenceRecord:
    evidence_type: str
    temporal_class: str
    canonical_fields: dict[str, Any]
    unresolved_source_fields: dict[str, Any]
    document_fingerprint: str
    source_workbook: str
    source_sheet: str
    source_row_reference: str
    original_headers: dict[str, str]
    reporting_period: str | None
    ingestion_timestamp: datetime
    validation_errors: list[HistoricalValidationError] = field(default_factory=list)
    identity_review_required: bool = False


@dataclass(frozen=True)
class TransactionHistoricalAggregate:
    store_id: str
    reporting_period: str
    historical_transaction_count: Decimal | None
    historical_transaction_volume: Decimal | None
    historical_income: Decimal | None
    historical_cost: Decimal | None
    historical_rate_margin: Decimal | None
    rate_margin_observations: list[Decimal]
    products_observed: list[str]
    transaction_types_observed: list[str]
    card_types_observed: list[str]
    acquiring_banks_observed: list[str]
    issuing_banks_observed: list[str]
    processors_observed: list[str]
    source_evidence_count: int
    provenance_references: list[str]
    validation_errors: list[HistoricalValidationError]


@dataclass(frozen=True)
class ProfitabilitySummary:
    store_id: str
    reporting_period: str
    canonical_fields: dict[str, Any]
    provenance_references: list[str]


@dataclass(frozen=True)
class ProfitabilityDuplicateGroup:
    store_id: str
    reporting_period: str
    duplicate_type: str
    record_count: int
    provenance_references: list[str]


@dataclass(frozen=True)
class ProfitabilityDuplicateResult:
    accepted_summaries: list[ProfitabilitySummary]
    exact_duplicate_groups: list[ProfitabilityDuplicateGroup]
    conflicting_duplicate_groups: list[ProfitabilityDuplicateGroup]
    excluded_records: list[HistoricalEvidenceRecord]

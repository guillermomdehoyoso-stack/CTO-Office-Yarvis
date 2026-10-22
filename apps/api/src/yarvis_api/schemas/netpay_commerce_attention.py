from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

EntityScope = Literal["client", "company", "branch"]
ReconciliationStatus = Literal["exact_match", "human_confirmed", "probable_match", "conflict", "unreconciled"]


class PortfolioContact(BaseModel):
    available: bool
    label: str = "Contacto registrado"
    source_scope: EntityScope | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    verification: str = "not_available"
    updated_at: datetime | None = None


class PortfolioSourceBadges(BaseModel):
    master: bool = True
    cases_available: int = 0
    linked_pre_master: int = 0
    unlinked_records: int | None = None
    d1: str = "No incorporado en P0/P1"
    terminals: str = "Sin fuente canónica autorizada"


class PortfolioP2Metrics(BaseModel):
    reporting_period: str | None = None
    currency_code: str | None = None
    monthly_sales_mxn: Decimal | None = None
    distributor_commission_mxn: Decimal | None = None
    effective_commission_on_sales_percent: Decimal | None = None
    percentage_status: Literal["calculated", "not_calculable", "unknown"] = "unknown"
    percentage_reason: str | None = None
    source_fields: dict[str, str] = Field(default_factory=dict)
    source_batch_id: UUID | None = None
    precision_classification: str | None = None
    freshness_at: datetime | None = None
    quality: str = "unknown"


class PortfolioP2Totals(BaseModel):
    monthly_sales_mxn: Decimal | None = None
    distributor_commission_mxn: Decimal | None = None
    effective_commission_on_sales_percent: Decimal | None = None
    percentage_status: Literal["calculated", "not_calculable", "unknown"] = "unknown"
    percentage_reason: str | None = None
    compatible_stores: int = 0
    excluded_stores: int = 0


class PortfolioRow(BaseModel):
    row_key: str
    entity_scope: EntityScope
    client_id: UUID
    company_id: UUID | None = None
    branch_id: UUID | None = None
    store_reference_id: UUID | None = None
    store_id: str | None = None
    store_reference_count: int = 0
    commerce_name: str
    legal_name: str | None = None
    branch_name: str | None = None
    masked_rfc: str | None = None
    contact: PortfolioContact
    reconciliation_status: ReconciliationStatus = "exact_match"
    availability_reasons: list[str] = Field(default_factory=list)
    source_badges: PortfolioSourceBadges = Field(default_factory=PortfolioSourceBadges)
    updated_at: datetime
    p2: PortfolioP2Metrics = Field(default_factory=PortfolioP2Metrics)


class PortfolioPage(BaseModel):
    items: list[PortfolioRow]
    page: int
    page_size: int
    total: int
    filtered_total: int
    pages: int
    p2_totals: PortfolioP2Totals = Field(default_factory=PortfolioP2Totals)


class PortfolioDetail(PortfolioRow):
    full_rfc: str | None = None
    mid: str = "MID no disponible"
    data_quality: list[str] = Field(default_factory=list)


class ReconciliationItem(BaseModel):
    record_type: Literal["candidate", "commercial_intake", "dossier"]
    record_id: UUID
    label_hint: str
    provenance: str
    reconciliation_status: ReconciliationStatus
    reasons: list[str] = Field(default_factory=list)
    updated_at: datetime


class ReconciliationPage(BaseModel):
    items: list[ReconciliationItem]
    total: int

from datetime import datetime
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


class PortfolioPage(BaseModel):
    items: list[PortfolioRow]
    page: int
    page_size: int
    total: int
    filtered_total: int
    pages: int


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

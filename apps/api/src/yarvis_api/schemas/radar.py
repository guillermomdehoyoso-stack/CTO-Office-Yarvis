from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Classification = Literal["alta_tpv", "alta_ecommerce", "soporte", "reposicion_terminal", "pagos_depositos", "documentacion", "otro"]
Priority = Literal["low", "normal", "high"]


class MerchantInput(BaseModel):
    trade_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    store_id: str | None = Field(default=None, max_length=100)
    contact_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    products: list[Literal["tpv", "ecommerce"]] = Field(default_factory=list)


class MerchantCreate(MerchantInput):
    actor: str = Field(default="operador", min_length=1, max_length=255)


class RequestCreate(BaseModel):
    merchant_id: UUID | None = None
    merchant: MerchantInput | None = None
    free_text: str = Field(min_length=1)
    classification: Classification
    priority: Priority = "normal"
    owner: str | None = Field(default=None, max_length=255)
    next_action: str | None = None
    due_at: datetime | None = None
    actor: str = Field(default="operador", min_length=1, max_length=255)

    @model_validator(mode="after")
    def merchant_source_is_exact(self):
        if (self.merchant_id is None) == (self.merchant is None):
            raise ValueError("provide exactly one of merchant_id or merchant")
        return self


class ChecklistUpdate(BaseModel):
    received: bool
    actor: str = Field(default="operador", min_length=1, max_length=255)


class NextActionUpdate(BaseModel):
    next_action: str | None = None
    due_at: datetime | None = None
    priority: Priority | None = None
    owner: str | None = Field(default=None, max_length=255)
    actor: str = Field(default="operador", min_length=1, max_length=255)


class NoteCreate(BaseModel):
    note: str = Field(min_length=1)
    actor: str = Field(default="operador", min_length=1, max_length=255)


class CloseRequest(BaseModel):
    incomplete_justification: str | None = None
    next_action: str | None = None
    actor: str = Field(default="operador", min_length=1, max_length=255)


class ReopenRequest(BaseModel):
    actor: str = Field(default="operador", min_length=1, max_length=255)


class ChecklistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    item_code: str
    label: str
    required: bool
    received: bool
    received_by: str | None
    received_at: datetime | None
    position: int


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    merchant_id: UUID
    free_text: str
    classification: str
    status: str
    priority: str
    owner: str | None
    next_action: str | None
    due_at: datetime | None
    closed_at: datetime | None
    close_reason: str | None
    created_at: datetime
    updated_at: datetime
    checklist: list[ChecklistRead] = Field(default_factory=list)


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    request_id: UUID | None
    event_type: str
    summary: str
    actor: str
    occurred_at: datetime


class MerchantRead(MerchantInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    pending: bool
    open_count: int
    next_action: str | None
    due_at: datetime | None
    age_days: int | None
    priority: str | None
    missing_documents: list[str] = Field(default_factory=list)
    owner: str | None


class MerchantDetail(MerchantRead):
    requests: list[RequestRead]
    activity: list[ActivityRead]


class DashboardRead(BaseModel):
    timezone: str
    summary: dict[str, int]
    merchants: list[MerchantRead]

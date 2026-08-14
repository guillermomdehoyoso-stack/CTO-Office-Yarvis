from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClientWrite(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    external_reference: str | None = Field(default=None, max_length=100)
    primary_contact_name: str | None = Field(default=None, max_length=255)
    primary_email: str | None = Field(default=None, max_length=320)
    primary_phone: str | None = Field(default=None, max_length=40)


class CompanyWrite(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    tax_identifier: str | None = Field(default=None, max_length=64)
    legal_address: str | None = None
    contact_name: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=40)


class BranchWrite(BaseModel):
    commercial_name: str = Field(min_length=1, max_length=255)
    branch_kind: str = Field(pattern="^(physical|commercial)$")
    address: str | None = None
    locality: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)
    contact_name: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=40)


class StoreReferenceWrite(BaseModel):
    store_id: str = Field(min_length=1, max_length=100)
    source_type: str = Field(min_length=1, max_length=64)
    source_reference: str | None = Field(default=None, max_length=255)
    confirmed: bool = False


class StoreReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    store_id: str
    source_type: str
    source_reference: str | None
    assigned_at: datetime
    confirmed_at: datetime | None
    active: bool


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    commercial_name: str
    branch_kind: str
    address: str | None
    locality: str | None
    state: str | None
    postal_code: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    store_reference: StoreReferenceRead | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    client_id: UUID
    legal_name: str
    tax_identifier: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    branches: list[BranchRead] = Field(default_factory=list)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str
    external_reference: str | None
    primary_contact_name: str | None
    primary_email: str | None
    primary_phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    companies: list[CompanyRead] = Field(default_factory=list)


class MasterSearchRead(BaseModel):
    items: list[ClientRead]
    offset: int
    limit: int
    total: int

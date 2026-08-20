from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OperationalDataRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source_row_number: int
    validation_status: str
    match_status: str
    store_reference_id: UUID | None
    error_codes: list[str]
    projected_action: str
    preview: dict = Field(default_factory=dict)


class OperationalDataBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    dataset_type: str
    reporting_period: str | None
    sanitized_filename: str
    selected_sheet: str
    hash_identifier: str = ""
    preview_token: str
    duplicate_upload: bool = False
    status: str
    row_counts: dict
    source_discarded: bool
    created_at: datetime
    updated_at: datetime
    rows: list[OperationalDataRowRead] = Field(default_factory=list)


class OperationalDataBatchPage(BaseModel):
    items: list[OperationalDataBatchRead]
    total: int


class OperationalRowResolution(BaseModel):
    store_reference_id: UUID


class OperationalDataAcceptance(BaseModel):
    preview_token: str = Field(min_length=64, max_length=64)

from datetime import datetime
from typing import Literal
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
    source_profile: str
    currency_code: str | None
    completeness_status: str
    received_at: datetime
    source_generated_at: datetime | None
    data_cutoff_at: datetime | None
    source_producer: str
    delivery_channel: str | None
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
    reason_code: Literal["confirm_exact_store_id"] = "confirm_exact_store_id"


class OperationalDataAcceptance(BaseModel):
    preview_token: str = Field(min_length=64, max_length=64)
    expected_predecessors: dict[str, UUID] = Field(default_factory=dict)
    correction_reason: str | None = Field(default=None, min_length=3, max_length=255)


class OperationalDataMetadataCompletion(BaseModel):
    data_cutoff_at: datetime
    reason: str = Field(min_length=3, max_length=255)

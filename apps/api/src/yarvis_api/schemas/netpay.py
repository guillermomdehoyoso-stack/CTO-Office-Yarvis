from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NetpayMovementType(str, Enum):
    outbound = "outbound"
    collection = "collection"
    unknown = "unknown"


class NetpayInvestigationStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    confirmed = "confirmed"


class NetpayDirection(str, Enum):
    outbound = "outbound"
    collection = "collection"
    unknown = "unknown"


class ConfirmationStatus(str, Enum):
    candidate = "candidate"
    confirmed = "confirmed"
    rejected = "rejected"


class ExtractedField(BaseModel):
    value: str | None = None
    confidence: float = 0.0
    provenance: str = "parser"
    source_reference: str | None = None
    confirmation_status: ConfirmationStatus = ConfirmationStatus.candidate
    extraction_method: str = "regex"
    source_type: str = "email"
    confirmed_by_user: str | None = None
    confirmed_at: datetime | None = None


class AttachmentMetadata(BaseModel):
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str | None = Field(default=None, max_length=255)
    size_bytes: int | None = None
    storage_reference: str | None = Field(default=None, max_length=1000)


class EmailImportPayload(BaseModel):
    gmail_message_id: str | None = Field(default=None, max_length=255)
    gmail_thread_id: str | None = Field(default=None, max_length=255)
    from_address: str | None = Field(default=None, max_length=320)
    to_addresses: list[str] = Field(default_factory=list)
    cc_addresses: list[str] = Field(default_factory=list)
    reply_to_addresses: list[str] = Field(default_factory=list)
    delivered_to: str | None = Field(default=None, max_length=320)
    x_original_to: str | None = Field(default=None, max_length=320)
    original_recipient: str | None = Field(default=None, max_length=320)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    attachments_metadata: list[AttachmentMetadata] = Field(default_factory=list)
    sent_at: datetime | None = None
    received_at: datetime | None = None


class DocumentImportPayload(BaseModel):
    service_case_id: UUID
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=255)
    storage_reference: str | None = Field(default=None, max_length=1000)
    extracted_text: str | None = None
    enable_ocr: bool = False


class NetpayShipmentCreate(BaseModel):
    tracking_number: str = Field(min_length=1, max_length=120)
    carrier: str | None = Field(default=None, max_length=120)
    direction: NetpayDirection = NetpayDirection.unknown
    status: str = Field(default="registered", min_length=1, max_length=30)
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None

    recipient_name: str | None = Field(default=None, max_length=255)
    receiver_company: str | None = Field(default=None, max_length=255)
    branch: str | None = Field(default=None, max_length=255)
    address_full: str | None = None
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, max_length=40)
    folio: str | None = Field(default=None, max_length=100)
    store_id: str | None = Field(default=None, max_length=100)
    device_serial: str | None = Field(default=None, max_length=100)


class NetpayShipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_case_id: UUID
    tracking_number: str
    carrier: str | None
    direction: NetpayDirection
    status: str
    shipped_at: datetime | None
    delivered_at: datetime | None

    recipient_name: str | None
    receiver_company: str | None
    branch: str | None
    address_full: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    phone: str | None
    folio: str | None
    store_id: str | None
    device_serial: str | None
    extracted_fields: dict[str, ExtractedField]

    created_at: datetime


class NetpayServiceCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    folio: str
    received_at: datetime
    case_type: str | None
    status: str
    source_email_id: str | None
    source_thread_id: str | None
    source_subject: str
    source_sender: str | None
    source_intake_item_id: UUID | None
    sent_at: datetime | None

    customer_name: str | None
    merchant_name: str | None
    address: str | None
    store_id: str | None
    device_serial: str | None
    movement_type: NetpayMovementType
    investigation_status: NetpayInvestigationStatus
    notes: str | None

    to_addresses: list[str]
    cc_addresses: list[str]
    reply_to_addresses: list[str]
    delivered_to: str | None
    x_original_to: str | None
    original_recipient: str | None
    recipient_addresses: list[str]
    operational_recipient: str | None
    recipient_resolution_source: str | None
    recipient_resolution_confidence: float
    physical_destination_resolution_source: str | None
    physical_destination_resolution_confidence: float
    body_normalized: str | None
    attachments_metadata: list[AttachmentMetadata]
    extracted_fields: dict[str, ExtractedField]
    operational_resolution: dict

    created_at: datetime
    updated_at: datetime


class NetpayServiceCaseImportResult(BaseModel):
    created: bool
    duplicate_by: str | None = None
    service_case: NetpayServiceCaseRead
    shipments: list[NetpayShipmentRead] = Field(default_factory=list)


class NetpayInvestigationUpdate(BaseModel):
    case_type: str | None = Field(default=None, max_length=50)
    customer_name: str | None = Field(default=None, max_length=255)
    merchant_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    store_id: str | None = Field(default=None, max_length=100)
    device_serial: str | None = Field(default=None, max_length=100)
    movement_type: NetpayMovementType | None = None
    notes: str | None = None
    investigation_status: NetpayInvestigationStatus | None = None

    @model_validator(mode="after")
    def validate_confirmation(self):
        if self.investigation_status == NetpayInvestigationStatus.confirmed:
            if not self.store_id and not self.device_serial:
                return self
        return self


class NetpayDeviceAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_serial: str
    store_id: str | None
    organization_id: UUID | None
    assigned_at: datetime | None
    returned_at: datetime | None
    status: str
    service_case_id: UUID | None
    created_at: datetime
    updated_at: datetime


class NetpayTimelineItem(BaseModel):
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    occurred_at: datetime
    payload: dict


class DocumentImportResult(BaseModel):
    created: bool
    duplicate_by: str | None = None
    intake_item_id: UUID
    document_summary: ExtractedField

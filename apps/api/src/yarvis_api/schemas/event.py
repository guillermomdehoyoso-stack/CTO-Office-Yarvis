from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DomainEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    organization_id: UUID | None
    case_id: UUID | None
    payload: dict
    occurred_at: datetime
    recorded_at: datetime
    correlation_id: UUID | None

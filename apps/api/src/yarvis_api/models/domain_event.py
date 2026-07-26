from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from yarvis_api.models.base import Base
from yarvis_api.clock import utc_now


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    correlation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    causation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)


def record_event(
    db: Session,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    organization_id: UUID | None = None,
    case_id: UUID | None = None,
    correlation_id: UUID | None = None,
    causation_id: UUID | None = None,
    payload: dict | None = None,
) -> DomainEvent:
    event = DomainEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        organization_id=organization_id,
        case_id=case_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload or {},
    )
    db.add(event)
    return event

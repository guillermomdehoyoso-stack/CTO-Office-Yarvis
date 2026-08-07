"""F-011 persisted identity and Governance membership records."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class Principal(TimestampedUUIDMixin, Base):
    __tablename__ = "principals"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_principals_status"),
    )

    external_subject: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    person_id: Mapped[object | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True
    )


class PrincipalMembership(TimestampedUUIDMixin, Base):
    __tablename__ = "principal_memberships"
    __table_args__ = (
        UniqueConstraint("principal_id", "organization_id", name="uq_principal_memberships_principal_organization"),
        CheckConstraint("status IN ('active', 'revoked')", name="ck_principal_memberships_status"),
        CheckConstraint(
            "(status = 'active' AND revoked_at IS NULL) OR (status = 'revoked' AND revoked_at IS NOT NULL)",
            name="ck_principal_memberships_revoked_at",
        ),
        Index("ix_principal_memberships_principal_status", "principal_id", "status"),
        Index("ix_principal_memberships_organization_status", "organization_id", "status"),
    )

    principal_id: Mapped[object] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[object] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)


class PrincipalMembershipCommand(TimestampedUUIDMixin, Base):
    """Durable replay record for the bounded Governance membership command."""

    __tablename__ = "principal_membership_commands"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_principal_membership_commands_organization_key"),
        CheckConstraint("command_type IN ('activate', 'revoke')", name="ck_principal_membership_commands_type"),
    )

    organization_id: Mapped[object] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    membership_id: Mapped[object] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("principal_memberships.id", ondelete="RESTRICT"), nullable=False, index=True)
    command_type: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

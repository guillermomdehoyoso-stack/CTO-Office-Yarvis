"""F-011 Principal and Membership structural foundation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260806_32"
down_revision = "20260806_31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "principals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_subject", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_principals_status"),
        sa.UniqueConstraint("external_subject", name="uq_principals_external_subject"),
    )
    op.create_index("ix_principals_external_subject", "principals", ["external_subject"])
    op.create_index("ix_principals_person_id", "principals", ["person_id"])
    op.create_table(
        "principal_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("principal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('active', 'revoked')", name="ck_principal_memberships_status"),
        sa.CheckConstraint("(status = 'active' AND revoked_at IS NULL) OR (status = 'revoked' AND revoked_at IS NOT NULL)", name="ck_principal_memberships_revoked_at"),
        sa.UniqueConstraint("principal_id", "organization_id", name="uq_principal_memberships_principal_organization"),
    )
    op.create_index("ix_principal_memberships_principal_status", "principal_memberships", ["principal_id", "status"])
    op.create_index("ix_principal_memberships_organization_status", "principal_memberships", ["organization_id", "status"])
    op.create_table(
        "principal_membership_commands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("principal_memberships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("command_type", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("command_type IN ('activate', 'revoke')", name="ck_principal_membership_commands_type"),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_principal_membership_commands_organization_key"),
    )
    op.create_index("ix_principal_membership_commands_organization_id", "principal_membership_commands", ["organization_id"])
    op.create_index("ix_principal_membership_commands_membership_id", "principal_membership_commands", ["membership_id"])


def downgrade():
    op.drop_table("principal_membership_commands", if_exists=True)
    op.drop_table("principal_memberships")
    op.drop_table("principals")

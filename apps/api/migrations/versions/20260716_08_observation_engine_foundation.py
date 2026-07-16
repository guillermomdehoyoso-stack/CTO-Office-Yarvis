"""observation engine and operational policies foundation

Revision ID: 20260716_08
Revises: 20260714_07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260716_08"
down_revision = "20260714_07"
branch_labels = None
depends_on = None


OBSERVATION_STATUS = ("observed", "candidate", "confirmed", "rejected", "superseded", "conflicted")
RESOLUTION_STATUS = ("proposed", "confirmed", "rejected", "conflicted")
POLICY_STATUS = ("draft", "active", "inactive")
EVALUATION_STATUS = ("matched", "not_matched", "insufficient_data", "conflict")
ATTENTION_STATUS = ("open", "in_progress", "resolved", "dismissed")


def upgrade() -> None:
    op.create_table(
        "source_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("external_source_id", sa.String(length=255), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("classification", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_records_source_type", "source_records", ["source_type"])
    op.create_index("ix_source_records_external_source_id", "source_records", ["external_source_id"])
    op.create_index("ix_source_records_classification", "source_records", ["classification"])

    op.create_table(
        "document_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=True),
        sa.Column("media_type", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("report_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("storage_reference", sa.String(length=1000), nullable=True),
        sa.Column("extraction_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("classification", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["source_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_records_source_id", "document_records", ["source_id"])
    op.create_index("ix_document_records_file_hash", "document_records", ["file_hash"])
    op.create_index("ix_document_records_classification", "document_records", ["classification"])

    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=True),
        sa.Column("subject_reference", sa.String(length=255), nullable=True),
        sa.Column("field_name", sa.String(length=150), nullable=False),
        sa.Column("observed_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("identifier_type", sa.String(length=100), nullable=True),
        sa.Column("extraction_method", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("confirmation_status", sa.String(length=20), nullable=False, server_default="observed"),
        sa.Column("source_reference", sa.String(length=500), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_by", sa.String(length=255), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["document_id"], ["document_records.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["source_records.id"]),
        sa.ForeignKeyConstraint(["supersedes_observation_id"], ["observations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("confirmation_status IN ('observed', 'candidate', 'confirmed', 'rejected', 'superseded', 'conflicted')", name="ck_observations_confirmation_status"),
    )
    op.create_index("ix_observations_document_id", "observations", ["document_id"])
    op.create_index("ix_observations_source_id", "observations", ["source_id"])
    op.create_index("ix_observations_domain", "observations", ["domain"])
    op.create_index("ix_observations_subject_type", "observations", ["subject_type"])
    op.create_index("ix_observations_subject_reference", "observations", ["subject_reference"])
    op.create_index("ix_observations_field_name", "observations", ["field_name"])
    op.create_index("ix_observations_confirmation_status", "observations", ["confirmation_status"])
    op.create_index("ix_observations_supersedes_observation_id", "observations", ["supersedes_observation_id"])

    op.create_table(
        "resolution_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_entity_type", sa.String(length=100), nullable=False),
        sa.Column("candidate_entity_id", sa.String(length=255), nullable=True),
        sa.Column("decision_status", sa.String(length=20), nullable=False, server_default="proposed"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.String(length=255), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("decision_status IN ('proposed', 'confirmed', 'rejected', 'conflicted')", name="ck_resolution_decisions_status"),
    )
    op.create_index("ix_resolution_decisions_observation_id", "resolution_decisions", ["observation_id"])
    op.create_index("ix_resolution_decisions_decision_status", "resolution_decisions", ["decision_status"])

    op.create_table(
        "operational_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_key", sa.String(length=150), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="warning"),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_key", "version", name="uq_operational_policy_key_version"),
        sa.CheckConstraint("status IN ('draft', 'active', 'inactive')", name="ck_operational_policies_status"),
    )
    op.create_index("ix_operational_policies_policy_key", "operational_policies", ["policy_key"])
    op.create_index("ix_operational_policies_domain", "operational_policies", ["domain"])
    op.create_index("ix_operational_policies_status", "operational_policies", ["status"])

    op.create_table(
        "policy_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=False),
        sa.Column("subject_id", sa.String(length=255), nullable=False),
        sa.Column("result_status", sa.String(length=30), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["policy_id"], ["operational_policies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("result_status IN ('matched', 'not_matched', 'insufficient_data', 'conflict')", name="ck_policy_evaluations_result_status"),
    )
    op.create_index("ix_policy_evaluations_policy_id", "policy_evaluations", ["policy_id"])
    op.create_index("ix_policy_evaluations_subject_type", "policy_evaluations", ["subject_type"])
    op.create_index("ix_policy_evaluations_subject_id", "policy_evaluations", ["subject_id"])
    op.create_index("ix_policy_evaluations_result_status", "policy_evaluations", ["result_status"])

    op.create_table(
        "attention_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=False),
        sa.Column("subject_id", sa.String(length=255), nullable=False),
        sa.Column("policy_key", sa.String(length=150), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.String(length=100), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('open', 'in_progress', 'resolved', 'dismissed')", name="ck_attention_items_status"),
    )
    op.create_index("ix_attention_items_subject_type", "attention_items", ["subject_type"])
    op.create_index("ix_attention_items_subject_id", "attention_items", ["subject_id"])
    op.create_index("ix_attention_items_policy_key", "attention_items", ["policy_key"])
    op.create_index("ix_attention_items_status", "attention_items", ["status"])


def downgrade() -> None:
    op.drop_index("ix_attention_items_status", table_name="attention_items")
    op.drop_index("ix_attention_items_policy_key", table_name="attention_items")
    op.drop_index("ix_attention_items_subject_id", table_name="attention_items")
    op.drop_index("ix_attention_items_subject_type", table_name="attention_items")
    op.drop_table("attention_items")

    op.drop_index("ix_policy_evaluations_result_status", table_name="policy_evaluations")
    op.drop_index("ix_policy_evaluations_subject_id", table_name="policy_evaluations")
    op.drop_index("ix_policy_evaluations_subject_type", table_name="policy_evaluations")
    op.drop_index("ix_policy_evaluations_policy_id", table_name="policy_evaluations")
    op.drop_table("policy_evaluations")

    op.drop_index("ix_operational_policies_status", table_name="operational_policies")
    op.drop_index("ix_operational_policies_domain", table_name="operational_policies")
    op.drop_index("ix_operational_policies_policy_key", table_name="operational_policies")
    op.drop_table("operational_policies")

    op.drop_index("ix_resolution_decisions_decision_status", table_name="resolution_decisions")
    op.drop_index("ix_resolution_decisions_observation_id", table_name="resolution_decisions")
    op.drop_table("resolution_decisions")

    op.drop_index("ix_observations_supersedes_observation_id", table_name="observations")
    op.drop_index("ix_observations_confirmation_status", table_name="observations")
    op.drop_index("ix_observations_field_name", table_name="observations")
    op.drop_index("ix_observations_subject_reference", table_name="observations")
    op.drop_index("ix_observations_subject_type", table_name="observations")
    op.drop_index("ix_observations_domain", table_name="observations")
    op.drop_index("ix_observations_source_id", table_name="observations")
    op.drop_index("ix_observations_document_id", table_name="observations")
    op.drop_table("observations")

    op.drop_index("ix_document_records_classification", table_name="document_records")
    op.drop_index("ix_document_records_file_hash", table_name="document_records")
    op.drop_index("ix_document_records_source_id", table_name="document_records")
    op.drop_table("document_records")

    op.drop_index("ix_source_records_classification", table_name="source_records")
    op.drop_index("ix_source_records_external_source_id", table_name="source_records")
    op.drop_index("ix_source_records_source_type", table_name="source_records")
    op.drop_table("source_records")

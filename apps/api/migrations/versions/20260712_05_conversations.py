"""conversations for mission control intake

Revision ID: 20260712_05
Revises: 20260712_04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="20260712_05"; down_revision="20260712_04"; branch_labels=None; depends_on=None
def upgrade():
    u=postgresql.UUID(as_uuid=True); t=sa.DateTime(timezone=True)
    op.create_table("conversations",sa.Column("id",u,primary_key=True),sa.Column("title",sa.String(255)),sa.Column("organization_id",u,sa.ForeignKey("organizations.id")),sa.Column("person_id",u,sa.ForeignKey("people.id")),sa.Column("case_id",u,sa.ForeignKey("cases.id")),sa.Column("created_at",t,server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",t,server_default=sa.text("now()"),nullable=False))
    op.create_index("ix_conversations_case_id","conversations",["case_id"])
    op.create_table("conversation_messages",sa.Column("id",u,primary_key=True),sa.Column("conversation_id",u,sa.ForeignKey("conversations.id"),nullable=False),sa.Column("role",sa.String(20),nullable=False),sa.Column("text_content",sa.Text),sa.Column("intake_item_id",u,sa.ForeignKey("intake_items.id")),sa.Column("created_at",t,server_default=sa.text("now()"),nullable=False),sa.CheckConstraint("role IN ('user','yarvis','system')",name="ck_conversation_role"))
    op.create_index("ix_conversation_messages_conversation_id","conversation_messages",["conversation_id"])
def downgrade(): op.drop_table("conversation_messages");op.drop_table("conversations")

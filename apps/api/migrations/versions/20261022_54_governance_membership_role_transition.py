"""Allow the bounded Governance membership role-transition receipt.

Revision ID: 20261022_54
Revises: 20261021_53
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261022_54"
down_revision: str | None = "20261021_53"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_principal_membership_commands_type", "principal_membership_commands", type_="check"
    )
    op.create_check_constraint(
        "ck_principal_membership_commands_type",
        "principal_membership_commands",
        "command_type IN ('activate', 'revoke', 'change_role')",
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM principal_membership_commands WHERE command_type = 'change_role'
          ) THEN
            RAISE EXCEPTION 'cannot downgrade while change_role receipts exist';
          END IF;
        END
        $$
        """
    )
    op.drop_constraint(
        "ck_principal_membership_commands_type", "principal_membership_commands", type_="check"
    )
    op.create_check_constraint(
        "ck_principal_membership_commands_type",
        "principal_membership_commands",
        "command_type IN ('activate', 'revoke')",
    )

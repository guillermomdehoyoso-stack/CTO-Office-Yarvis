import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership, PrincipalMembershipCommand


def test_ig014_downgrade_refuses_to_destroy_existing_role_transition_receipt():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        organization = Organization(legal_name="Migration Org", display_name="Migration Org", status="active")
        principal = Principal(external_subject="local:migration-target", status="active")
        session.add_all((organization, principal))
        session.flush()
        membership = PrincipalMembership(
            principal_id=principal.id,
            organization_id=organization.id,
            role="netpay_inbox_portfolio_reader",
            status="active",
        )
        session.add(membership)
        session.flush()
        session.add(
            PrincipalMembershipCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                command_type="change_role",
                idempotency_key="protected-receipt",
                request_fingerprint="f" * 64,
            )
        )
        session.commit()

    config = Config("alembic.ini")
    with pytest.raises(DBAPIError, match="cannot downgrade while change_role receipts exist"):
        command.downgrade(config, "20261021_53")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261022_54"
        assert connection.scalar(
            select(PrincipalMembershipCommand.id).where(
                PrincipalMembershipCommand.idempotency_key == "protected-receipt"
            )
        ) is not None

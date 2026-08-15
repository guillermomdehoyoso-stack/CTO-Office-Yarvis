from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select

from yarvis_api.application.authority import permissions_for_role
from yarvis_api.application.errors import ApplicationError
from yarvis_api.config import Settings
from yarvis_api.local_netpay_authority import (
    NETPAY_OPERATIONS_ROLE,
    LocalAuthorityProvisioningError,
    build_parser,
    provision_local_netpay_operator,
)
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.authority_resolution import AuthorityResolutionService

EXPECTED_PERMISSIONS = frozenset(
    {
        "netpay.master.read",
        "netpay.master.manage",
        "netpay.inbox.read",
        "netpay.inbox.manage",
    }
)


def _session():
    from yarvis_api.main import app

    return app.state.yarvis.persistence.create_session()


def _organization(session, name="Netpay Local"):
    organization = Organization(legal_name=name, display_name=name, status="active")
    session.add(organization)
    session.flush()
    organization_id = organization.id
    session.commit()
    return organization_id


def _provision(session, organization_id, *, environment="local", subject="local:netpay", role=NETPAY_OPERATIONS_ROLE):
    return provision_local_netpay_operator(
        session,
        settings=Settings(environment=environment),
        subject=subject,
        organization_id=organization_id,
        role=role,
    )


def test_combined_role_is_exact_and_closed():
    assert permissions_for_role(NETPAY_OPERATIONS_ROLE) == EXPECTED_PERMISSIONS
    assert permissions_for_role("netpay_master_operator") == frozenset(
        {"netpay.master.read", "netpay.master.manage"}
    )
    assert permissions_for_role("netpay_inbox_operator") == frozenset(
        {"netpay.inbox.read", "netpay.inbox.manage"}
    )
    assert all(
        not permission.startswith(
            (
                "radar.",
                "mission.",
                "inbound.",
                "document.",
                "economics.",
                "task.",
                "process.",
                "governance.",
                "workspace.",
                "opportunity.",
            )
        )
        for permission in EXPECTED_PERMISSIONS
    )


@pytest.mark.parametrize("environment", ["local", "test"])
def test_local_and_test_create_principal_and_membership_atomically(environment):
    with _session() as session:
        organization = _organization(session, f"Allowed {environment}")
        result = _provision(session, organization, environment=environment)
        assert result.status == "created"
        principal = session.scalar(select(Principal).where(Principal.external_subject == "local:netpay"))
        membership = session.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id))
        assert membership.organization_id == organization
        assert membership.role == NETPAY_OPERATIONS_ROLE
        assert membership.status == "active"


def test_production_is_denied_before_any_write():
    with _session() as session:
        organization = _organization(session)
        before = session.scalar(select(func.count()).select_from(Principal))
        with pytest.raises(LocalAuthorityProvisioningError) as denied:
            _provision(session, organization, environment="production")
        assert denied.value.code == "environment_denied"
        assert session.scalar(select(func.count()).select_from(Principal)) == before


def test_cli_requires_all_explicit_arguments_and_uuid_selector():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--subject", "local:netpay", "--organization-id", "not-a-uuid", "--role", NETPAY_OPERATIONS_ROLE]
        )


def test_missing_organization_and_other_role_fail_closed_without_creation():
    with _session() as session:
        with pytest.raises(LocalAuthorityProvisioningError) as missing:
            provision_local_netpay_operator(
                session,
                settings=Settings(environment="local"),
                subject="local:netpay",
                organization_id=uuid4(),
                role=NETPAY_OPERATIONS_ROLE,
            )
        assert missing.value.code == "organization_not_found"
        assert session.scalar(select(func.count()).select_from(Organization)) == 0
        assert session.scalar(select(func.count()).select_from(Principal)) == 0

        organization = _organization(session)
        with pytest.raises(LocalAuthorityProvisioningError) as role_denied:
            _provision(session, organization, role="netpay_inbox_operator")
        assert role_denied.value.code == "role_denied"
        assert session.scalar(select(func.count()).select_from(Principal)) == 0


def test_existing_principal_and_idempotent_membership_are_reused():
    with _session() as session:
        organization = _organization(session)
        principal = Principal(external_subject="local:netpay", status="active")
        session.add(principal)
        session.commit()
        first = _provision(session, organization)
        second = _provision(session, organization)
        assert first.status == "created"
        assert second.status == "already_provisioned"
        assert first.principal_id == second.principal_id == str(principal.id)
        assert first.membership_id == second.membership_id


def test_inactive_principal_membership_and_different_role_are_not_changed():
    with _session() as session:
        organization = _organization(session)
        disabled = Principal(external_subject="local:disabled", status="disabled")
        session.add(disabled)
        session.commit()
        with pytest.raises(LocalAuthorityProvisioningError) as principal_denied:
            _provision(session, organization, subject="local:disabled")
        assert principal_denied.value.code == "principal_inactive"
        assert disabled.status == "disabled"

        active = Principal(external_subject="local:active", status="active")
        session.add(active)
        session.flush()
        revoked = PrincipalMembership(
            principal_id=active.id,
            organization_id=organization,
            role=NETPAY_OPERATIONS_ROLE,
            status="revoked",
            revoked_at=datetime.now(timezone.utc),
        )
        session.add(revoked)
        session.commit()
        with pytest.raises(LocalAuthorityProvisioningError) as membership_denied:
            _provision(session, organization, subject="local:active")
        assert membership_denied.value.code == "membership_inactive"
        assert revoked.status == "revoked"

        other_organization = _organization(session, "Other Role Org")
        other = Principal(external_subject="local:other", status="active")
        session.add(other)
        session.flush()
        membership = PrincipalMembership(
            principal_id=other.id,
            organization_id=other_organization,
            role="netpay_inbox_operator",
            status="active",
        )
        session.add(membership)
        session.commit()
        with pytest.raises(LocalAuthorityProvisioningError) as conflict:
            _provision(session, other_organization, subject="local:other")
        assert conflict.value.code == "membership_role_conflict"
        assert membership.role == "netpay_inbox_operator"


def test_membership_insert_failure_rolls_back_new_principal():
    with _session() as session:
        organization = _organization(session)

        def fail_membership_insert(*_args):
            raise RuntimeError("simulated membership write failure")

        event.listen(PrincipalMembership, "before_insert", fail_membership_insert)
        try:
            with pytest.raises(RuntimeError, match="simulated membership write failure"):
                _provision(session, organization, subject="local:rollback")
        finally:
            event.remove(PrincipalMembership, "before_insert", fail_membership_insert)
        assert session.scalar(select(Principal).where(Principal.external_subject == "local:rollback")) is None


def test_resolved_permissions_are_exact_and_revocation_removes_all_access():
    with _session() as session:
        organization = _organization(session)
        result = _provision(session, organization)
        envelope = AuthorityResolutionService().resolve(
            session,
            external_subject="local:netpay",
            selector=organization,
            authentication_source="local-test",
            correlation_id=str(uuid4()),
        )
        assert envelope.validated_permissions == EXPECTED_PERMISSIONS
        membership = session.get(PrincipalMembership, result.membership_id)
        membership.status = "revoked"
        membership.revoked_at = datetime.now(timezone.utc)
        session.commit()
        with pytest.raises(ApplicationError):
            AuthorityResolutionService().resolve(
                session,
                external_subject="local:netpay",
                selector=organization,
                authentication_source="local-test",
                correlation_id=str(uuid4()),
            )

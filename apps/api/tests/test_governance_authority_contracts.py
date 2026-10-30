from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership, PrincipalMembershipCommand
from yarvis_api.models.productive_auth import ProductiveSession
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.services.governance_authority import (
    activate_membership,
    change_membership_role_for_portfolio_read,
    evaluate_authority,
    revoke_membership,
)


def _envelope(principal_id, organization_id):
    return IdentityAuthorityEnvelope(principal_id, organization_id, frozenset({"governance.membership.create", "governance.membership.revoke"}), "local-test", str(uuid4()))


def test_membership_activation_replay_conflict_event_and_effective_terminal_revocation():
    from yarvis_api.main import app
    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="Org", display_name="Org", status="active")
        other = Organization(legal_name="Other", display_name="Other", status="active")
        operator = Principal(external_subject="local:operator", status="active")
        target = Principal(external_subject="local:target", status="active")
        session.add_all((org, other, operator, target)); session.flush()
        envelope = _envelope(operator.id, org.id)
        membership = activate_membership(session, envelope=envelope, principal_id=target.id, role="radar_viewer", idempotency_key="activate-1", causation_id=uuid4())
        session.commit()
        replay = activate_membership(session, envelope=envelope, principal_id=target.id, role="radar_viewer", idempotency_key="activate-1")
        assert replay.id == membership.id
        with pytest.raises(ApplicationError) as conflict:
            activate_membership(session, envelope=envelope, principal_id=target.id, role="radar_operator", idempotency_key="activate-1")
        assert conflict.value.code == ApplicationErrorCode.CONFLICT
        with pytest.raises(ApplicationError) as hidden:
            evaluate_authority(envelope, required_permission="governance.membership.revoke", target_organization_id=other.id)
        assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        revoked = revoke_membership(session, envelope=envelope, membership_id=membership.id, idempotency_key="revoke-1", causation_id=uuid4())
        session.commit()
        assert revoked.status == "revoked" and revoked.revoked_at is not None
        assert revoke_membership(session, envelope=envelope, membership_id=membership.id, idempotency_key="revoke-1").id == membership.id
        with pytest.raises(ApplicationError) as denied:
            AuthorityResolutionService().resolve(session, external_subject="local:target", selector=org.id, authentication_source="local-test", correlation_id=str(uuid4()))
        assert denied.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED
        events = session.scalars(select(DomainEvent).where(DomainEvent.aggregate_id == membership.id).order_by(DomainEvent.event_sequence)).all()
        assert [event.payload["transition"] for event in events] == ["activated", "revoked"]
        assert all(event.payload["contract_version"] == "1.1.0" for event in events)
        assert all("token" not in event.payload and "email" not in event.payload for event in events)


def test_bounded_role_transition_receipt_event_and_session_invalidation():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="Role Org", display_name="Role Org", status="active")
        actor = Principal(external_subject="local:role-admin", status="active")
        target = Principal(external_subject="local:portfolio-reader", status="active")
        session.add_all((org, actor, target))
        session.flush()
        membership = PrincipalMembership(
            principal_id=target.id,
            organization_id=org.id,
            role="netpay_inbox_operator",
            status="active",
        )
        session.add(membership)
        session.flush()
        now = utc_now()
        productive_session = ProductiveSession(
            principal_id=target.id,
            organization_id=org.id,
            membership_id=membership.id,
            session_hash="a" * 64,
            csrf_hash="b" * 64,
            last_seen_at=now,
            idle_expires_at=now + timedelta(hours=1),
            absolute_expires_at=now + timedelta(hours=8),
            status="active",
        )
        session.add(productive_session)
        session.commit()
        envelope = _envelope(actor.id, org.id)

        changed = change_membership_role_for_portfolio_read(
            session,
            envelope=envelope,
            membership_id=membership.id,
            expected_role="netpay_inbox_operator",
            target_role="netpay_inbox_portfolio_reader",
            reason="authenticated portfolio validation",
            idempotency_key="role-change-1",
        )
        session.commit()
        assert changed.role == "netpay_inbox_portfolio_reader"
        assert productive_session.status == "revoked"
        assert productive_session.revoke_reason == "authority_changed"
        assert change_membership_role_for_portfolio_read(
            session,
            envelope=envelope,
            membership_id=membership.id,
            expected_role="netpay_inbox_operator",
            target_role="netpay_inbox_portfolio_reader",
            reason="authenticated portfolio validation",
            idempotency_key="role-change-1",
        ).id == membership.id
        receipt = session.scalar(
            select(PrincipalMembershipCommand).where(
                PrincipalMembershipCommand.idempotency_key == "role-change-1"
            )
        )
        assert receipt is not None and receipt.command_type == "change_role"
        events = session.scalars(
            select(DomainEvent).where(DomainEvent.aggregate_id == membership.id)
        ).all()
        authority_events = [event for event in events if event.event_type == "AuthorityChanged"]
        assert len(authority_events) == 1
        assert authority_events[0].payload["contract_version"] == "1.2.0"


def test_bounded_role_transition_denials_and_conflicts():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="Guard Org", display_name="Guard Org", status="active")
        other = Organization(legal_name="Foreign Org", display_name="Foreign Org", status="active")
        actor = Principal(external_subject="local:guard-admin", status="active")
        target = Principal(external_subject="local:guard-target", status="active")
        session.add_all((org, other, actor, target))
        session.flush()
        membership = PrincipalMembership(
            principal_id=target.id,
            organization_id=org.id,
            role="netpay_inbox_operator",
            status="active",
        )
        session.add(membership)
        session.commit()
        envelope = _envelope(actor.id, org.id)
        arguments = dict(
            db=session,
            envelope=envelope,
            membership_id=membership.id,
            expected_role="netpay_inbox_operator",
            target_role="netpay_inbox_portfolio_reader",
            reason="portfolio validation",
            idempotency_key="bounded-1",
        )
        with pytest.raises(ApplicationError) as foreign:
            change_membership_role_for_portfolio_read(
                **{**arguments, "envelope": _envelope(actor.id, other.id)}
            )
        assert foreign.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        with pytest.raises(ApplicationError) as self_escalation:
            change_membership_role_for_portfolio_read(
                **{**arguments, "envelope": _envelope(target.id, org.id)}
            )
        assert self_escalation.value.details["reason"] == "self_escalation"
        with pytest.raises(ApplicationError) as wrong_target:
            change_membership_role_for_portfolio_read(
                **{**arguments, "target_role": "netpay_master_operator"}
            )
        assert wrong_target.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED

        change_membership_role_for_portfolio_read(**arguments)
        session.commit()
        with pytest.raises(ApplicationError) as replay_conflict:
            change_membership_role_for_portfolio_read(
                **{**arguments, "reason": "different payload"}
            )
        assert replay_conflict.value.details["reason"] == "idempotency_conflict"
        with pytest.raises(ApplicationError) as expected_conflict:
            change_membership_role_for_portfolio_read(
                **{**arguments, "idempotency_key": "bounded-2"}
            )
        assert expected_conflict.value.details["reason"] == "expected_role_conflict"


def test_bounded_role_transition_equivalent_concurrent_replay():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="Concurrent Org", display_name="Concurrent Org", status="active")
        actor = Principal(external_subject="local:concurrent-admin", status="active")
        target = Principal(external_subject="local:concurrent-target", status="active")
        session.add_all((org, actor, target))
        session.flush()
        membership = PrincipalMembership(
            principal_id=target.id,
            organization_id=org.id,
            role="netpay_inbox_operator",
            status="active",
        )
        session.add(membership)
        session.commit()
        organization_id = org.id
        actor_id = actor.id
        membership_id = membership.id

    def invoke() -> str:
        with app.state.yarvis.persistence.create_session() as worker:
            result = change_membership_role_for_portfolio_read(
                worker,
                envelope=_envelope(actor_id, organization_id),
                membership_id=membership_id,
                expected_role="netpay_inbox_operator",
                target_role="netpay_inbox_portfolio_reader",
                reason="concurrent authenticated validation",
                idempotency_key="concurrent-role-change",
            )
            worker.commit()
            return str(result.id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: invoke(), range(2)))
    assert results == [str(membership_id), str(membership_id)]
    with app.state.yarvis.persistence.create_session() as session:
        receipts = session.scalars(
            select(PrincipalMembershipCommand).where(
                PrincipalMembershipCommand.idempotency_key == "concurrent-role-change"
            )
        ).all()
        events = session.scalars(
            select(DomainEvent).where(
                DomainEvent.aggregate_id == membership_id,
                DomainEvent.event_type == "AuthorityChanged",
            )
        ).all()
        assert len(receipts) == 1
        assert len(events) == 1


def test_role_transition_http_route_requires_canonical_admin_and_preserves_exact_scope():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        org = Organization(legal_name="HTTP Org", display_name="HTTP Org", status="active")
        governor = Principal(external_subject="local:http-governor", status="active")
        target = Principal(external_subject="local:http-target", status="active")
        session.add_all((org, governor, target))
        session.flush()
        governor_membership = PrincipalMembership(
            principal_id=governor.id,
            organization_id=org.id,
            role="foundation_membership_operator",
            status="active",
        )
        target_membership = PrincipalMembership(
            principal_id=target.id,
            organization_id=org.id,
            role="netpay_inbox_operator",
            status="active",
        )
        session.add_all((governor_membership, target_membership))
        session.commit()
        target_membership_id = target_membership.id

    client = TestClient(app)
    payload = {
        "expected_role": "netpay_inbox_operator",
        "target_role": "netpay_inbox_portfolio_reader",
        "reason": "synthetic authenticated portfolio validation",
    }
    common_headers = {
        "X-Yarvis-Auth-Token": "deterministic-inbound-intake",
        "Idempotency-Key": "http-role-transition",
    }
    denied = client.post(
        f"/governance/memberships/{target_membership_id}/role-transition",
        headers={**common_headers, "X-Yarvis-Subject": "local:http-target"},
        json=payload,
    )
    assert denied.status_code == 403
    changed = client.post(
        f"/governance/memberships/{target_membership_id}/role-transition",
        headers={**common_headers, "X-Yarvis-Subject": "local:http-governor"},
        json=payload,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["role"] == "netpay_inbox_portfolio_reader"

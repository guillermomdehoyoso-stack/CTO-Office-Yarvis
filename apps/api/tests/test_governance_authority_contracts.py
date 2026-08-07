from uuid import uuid4

import pytest
from sqlalchemy import select

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.authority_resolution import AuthorityResolutionService
from yarvis_api.services.governance_authority import activate_membership, evaluate_authority, revoke_membership


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

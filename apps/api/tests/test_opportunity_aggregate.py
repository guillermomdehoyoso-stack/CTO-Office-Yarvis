from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import ConfirmOpportunityCommand, ProposeOpportunityCommand
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import Opportunity, OpportunityCommandIdempotency
from yarvis_api.models.organization import Organization
from yarvis_api.services.opportunity import OpportunityQueryService, OpportunityService


class _FailingCommitRuntime:
    def __init__(self, runtime): self.runtime, self.session = runtime, None
    def create_session(self):
        session = self.runtime.create_session(); self.session = session
        def fail(): raise RuntimeError("forced commit failure")
        session.commit = fail
        return session


def _principal(organization_id, authority):
    return AuthenticatedPrincipal("opportunity:actor", str(organization_id), (), (), authority, "test", datetime.now(timezone.utc), False)


def _metadata(key, expected=None, query=False):
    return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), query_id=str(uuid4()) if query else None, command_id=None if query else str(uuid4()), idempotency_key=None if query else key, expected_aggregate_version=expected)


def _organization(runtime, name="Opportunity test"):
    organization_id = uuid4()
    organization = Organization(id=organization_id, legal_name=name, display_name=name)
    with runtime.create_session() as session: session.add(organization); session.commit()
    return organization_id


def _counts(runtime, organization_id):
    with runtime.create_session() as session:
        return tuple(session.scalar(select(func.count()).select_from(model).where(model.organization_id == organization_id)) for model in (Opportunity, DomainEvent, OpportunityCommandIdempotency))


def test_propose_replay_conflict_and_query_are_tenant_safe(test_database):
    from yarvis_api.main import app
    organization_id, other_organization_id = _organization(app.state.yarvis.persistence), _organization(app.state.yarvis.persistence, "Other opportunity")
    service = OpportunityService(app.state.yarvis.persistence)
    metadata = _metadata("propose-key")
    first = service.propose(ProposeOpportunityCommand("Acquire photovoltaic site"), metadata, _principal(organization_id, "opportunity.propose"))
    replay = service.propose(ProposeOpportunityCommand("Acquire photovoltaic site"), metadata, _principal(organization_id, "opportunity.propose"))
    assert first.id == replay.id and first.lifecycle_status == "proposed" and first.aggregate_version == 1
    with pytest.raises(ApplicationError) as conflict:
        service.propose(ProposeOpportunityCommand("Different intent"), metadata, _principal(organization_id, "opportunity.propose"))
    assert conflict.value.code == ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as session:
        found = OpportunityQueryService().get(session, first.id, _principal(organization_id, "opportunity.read"), _metadata(None, query=True))
        assert found.id == first.id and found.business_intent == "Acquire photovoltaic site"
        with pytest.raises(ApplicationError) as hidden:
            OpportunityQueryService().get(session, first.id, _principal(other_organization_id, "opportunity.read"), _metadata(None, query=True))
        assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert _counts(app.state.yarvis.persistence, organization_id) == (1, 1, 1)


@pytest.mark.parametrize("authority", ["", "opportunity.confirm"])
def test_propose_requires_exact_authority(test_database, authority):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Proposal authority")
    with pytest.raises((ApplicationError, ValueError)):
        OpportunityService(app.state.yarvis.persistence).propose(ProposeOpportunityCommand("Intent"), _metadata(uuid4().hex), _principal(organization_id, authority))
    assert _counts(app.state.yarvis.persistence, organization_id) == (0, 0, 0)


def test_confirm_lifecycle_replay_stale_and_tenant_concealment(test_database):
    from yarvis_api.main import app
    organization_id, foreign_organization_id = _organization(app.state.yarvis.persistence, "Confirm owner"), _organization(app.state.yarvis.persistence, "Confirm foreign")
    service = OpportunityService(app.state.yarvis.persistence)
    proposed = service.propose(ProposeOpportunityCommand("Confirmable"), _metadata("p"), _principal(organization_id, "opportunity.propose"))
    metadata = _metadata("c", expected=1)
    confirmed = service.confirm(ConfirmOpportunityCommand(proposed.id, 1), metadata, _principal(organization_id, "opportunity.confirm"))
    replay = service.confirm(ConfirmOpportunityCommand(proposed.id, 1), metadata, _principal(organization_id, "opportunity.confirm"))
    assert confirmed.id == replay.id and confirmed.lifecycle_status == "confirmed" and confirmed.aggregate_version == 2 and confirmed.confirmed_by_subject_id == "opportunity:actor"
    with pytest.raises(ApplicationError) as replay_conflict:
        service.confirm(ConfirmOpportunityCommand(proposed.id, 2), metadata, _principal(organization_id, "opportunity.confirm"))
    assert replay_conflict.value.code == ApplicationErrorCode.CONFLICT
    with pytest.raises(ApplicationError) as stale:
        service.confirm(ConfirmOpportunityCommand(proposed.id, 1), _metadata("fresh", expected=1), _principal(organization_id, "opportunity.confirm"))
    assert stale.value.code == ApplicationErrorCode.CONFLICT
    with pytest.raises(ApplicationError) as foreign:
        service.confirm(ConfirmOpportunityCommand(proposed.id, 1), _metadata("foreign", expected=1), _principal(foreign_organization_id, "opportunity.confirm"))
    assert foreign.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert _counts(app.state.yarvis.persistence, organization_id) == (1, 2, 2)


def test_confirm_commit_failure_rolls_back_and_retry_succeeds(test_database):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Confirm rollback")
    stable = OpportunityService(app.state.yarvis.persistence)
    proposed = stable.propose(ProposeOpportunityCommand("Intent"), _metadata("propose"), _principal(organization_id, "opportunity.propose"))
    metadata = _metadata("confirm", expected=1)
    failing = _FailingCommitRuntime(app.state.yarvis.persistence)
    with pytest.raises(RuntimeError, match="forced commit failure"):
        OpportunityService(failing).confirm(ConfirmOpportunityCommand(proposed.id, 1), metadata, _principal(organization_id, "opportunity.confirm"))
    with app.state.yarvis.persistence.create_session() as session:
        opportunity = session.get(Opportunity, proposed.id)
        assert opportunity.lifecycle_status == "proposed" and opportunity.aggregate_version == 1 and opportunity.confirmed_at is None
    assert _counts(app.state.yarvis.persistence, organization_id) == (1, 1, 1)
    assert stable.confirm(ConfirmOpportunityCommand(proposed.id, 1), metadata, _principal(organization_id, "opportunity.confirm")).lifecycle_status == "confirmed"


def test_propose_commit_failure_rolls_back_and_retry_succeeds(test_database):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Proposal rollback")
    metadata = _metadata("propose-rollback")
    failing = _FailingCommitRuntime(app.state.yarvis.persistence)
    with pytest.raises(RuntimeError, match="forced commit failure"):
        OpportunityService(failing).propose(ProposeOpportunityCommand("Intent"), metadata, _principal(organization_id, "opportunity.propose"))
    assert _counts(app.state.yarvis.persistence, organization_id) == (0, 0, 0)
    first = OpportunityService(app.state.yarvis.persistence).propose(ProposeOpportunityCommand("Intent"), metadata, _principal(organization_id, "opportunity.propose"))
    assert first.id and _counts(app.state.yarvis.persistence, organization_id) == (1, 1, 1)


def test_confirm_and_query_require_exact_authority(test_database):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Confirm authority")
    service = OpportunityService(app.state.yarvis.persistence)
    proposed = service.propose(ProposeOpportunityCommand("Intent"), _metadata("proposal"), _principal(organization_id, "opportunity.propose"))
    for authority in ("", "opportunity.propose"):
        with pytest.raises((ApplicationError, ValueError)):
            service.confirm(ConfirmOpportunityCommand(proposed.id, 1), _metadata(uuid4().hex, expected=1), _principal(organization_id, authority))
    with app.state.yarvis.persistence.create_session() as session:
        with pytest.raises((ApplicationError, ValueError)):
            OpportunityQueryService().get(session, proposed.id, _principal(organization_id, "opportunity.confirm"), _metadata(None, query=True))
    assert _counts(app.state.yarvis.persistence, organization_id) == (1, 1, 1)


def test_concurrent_matching_and_mismatched_confirmation_are_deterministic(test_database):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Confirmation race")
    service = OpportunityService(app.state.yarvis.persistence)
    proposed = service.propose(ProposeOpportunityCommand("Intent"), _metadata("propose"), _principal(organization_id, "opportunity.propose"))
    barrier, metadata = Barrier(2), _metadata("race", expected=1)
    def matching():
        barrier.wait(); return OpportunityService(app.state.yarvis.persistence).confirm(ConfirmOpportunityCommand(proposed.id, 1), metadata, _principal(organization_id, "opportunity.confirm")).id
    with ThreadPoolExecutor(max_workers=2) as pool: assert len(set(pool.map(lambda _: matching(), range(2)))) == 1
    assert _counts(app.state.yarvis.persistence, organization_id) == (1, 2, 2)
    second = service.propose(ProposeOpportunityCommand("Other"), _metadata("p2"), _principal(organization_id, "opportunity.propose"))
    barrier, metadata = Barrier(2), _metadata("mismatch", expected=1)
    def invoke(expected):
        barrier.wait()
        try: return "ok", OpportunityService(app.state.yarvis.persistence).confirm(ConfirmOpportunityCommand(second.id, expected), metadata, _principal(organization_id, "opportunity.confirm")).id
        except ApplicationError as error: return "conflict", error.code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(invoke, (1, 2)))
    assert sorted(item[0] for item in outcomes) == ["conflict", "ok"]
    assert _counts(app.state.yarvis.persistence, organization_id) == (2, 4, 4)


def test_concurrent_proposal_replay_and_conflict_are_deterministic(test_database):
    from yarvis_api.main import app
    organization_id = _organization(app.state.yarvis.persistence, "Proposal race")
    barrier, metadata = Barrier(2), _metadata("proposal-race")
    def matching():
        barrier.wait(); return OpportunityService(app.state.yarvis.persistence).propose(ProposeOpportunityCommand("Intent"), metadata, _principal(organization_id, "opportunity.propose")).id
    with ThreadPoolExecutor(max_workers=2) as pool: assert len(set(pool.map(lambda _: matching(), range(2)))) == 1
    barrier, metadata = Barrier(2), _metadata("proposal-mismatch")
    def invoke(intent):
        barrier.wait()
        try: return "ok", OpportunityService(app.state.yarvis.persistence).propose(ProposeOpportunityCommand(intent), metadata, _principal(organization_id, "opportunity.propose")).id
        except ApplicationError as error: return "conflict", error.code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(invoke, ("First", "Second")))
    assert sorted(item[0] for item in outcomes) == ["conflict", "ok"]
    assert _counts(app.state.yarvis.persistence, organization_id) == (2, 2, 2)


def test_idempotency_keys_are_independent_per_organization(test_database):
    from yarvis_api.main import app
    first_org = _organization(app.state.yarvis.persistence, "First tenant")
    second_org = _organization(app.state.yarvis.persistence, "Second tenant")
    metadata = _metadata("shared-key")
    service = OpportunityService(app.state.yarvis.persistence)
    first = service.propose(ProposeOpportunityCommand("First intent"), metadata, _principal(first_org, "opportunity.propose"))
    second = service.propose(ProposeOpportunityCommand("Second intent"), metadata, _principal(second_org, "opportunity.propose"))
    assert first.id != second.id
    assert _counts(app.state.yarvis.persistence, first_org) == (1, 1, 1)
    assert _counts(app.state.yarvis.persistence, second_org) == (1, 1, 1)

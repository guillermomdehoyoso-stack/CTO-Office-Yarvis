from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import AssignOpportunityTemplateCommand, ConfirmOpportunityCommand, ProposeOpportunityCommand
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import OpportunityCommandIdempotency, OpportunityWorkspace
from yarvis_api.models.organization import Organization
from yarvis_api.services.opportunity import OpportunityService, OpportunityWorkspaceQueryService


class _FailingRuntime:
    def __init__(self, runtime): self.runtime=runtime
    def create_session(self):
        session=self.runtime.create_session(); session.commit=lambda: (_ for _ in ()).throw(RuntimeError("forced commit failure")); return session

def _principal(org, authority): return AuthenticatedPrincipal("specialist",str(org),(),(),authority,"test",datetime.now(timezone.utc),False)
def _metadata(key): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=key)
def _query(): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),query_id=str(uuid4()))
def _workspace(runtime, name="Specialization"):
    org=Organization(id=uuid4(),legal_name=name,display_name=name); oid=org.id
    with runtime.create_session() as s:s.add(org);s.commit()
    service=OpportunityService(runtime); opportunity=service.propose(ProposeOpportunityCommand("Intent"),_metadata("p"),_principal(oid,"opportunity.propose"));service.confirm(ConfirmOpportunityCommand(opportunity.id,1),_metadata("c"),_principal(oid,"opportunity.confirm"))
    with runtime.create_session() as s:return oid,s.scalar(select(OpportunityWorkspace).where(OpportunityWorkspace.opportunity_id==opportunity.id)).id

def test_assignment_metadata_replay_conflict_and_retrieval(test_database):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence); service=OpportunityService(app.state.yarvis.persistence); command=AssignOpportunityTemplateCommand(wid,"residential_solar",1); metadata=_metadata("assign")
    first=service.assign_template(command,metadata,_principal(org,"opportunity.specialize")); replay=service.assign_template(command,metadata,_principal(org,"opportunity.specialize"))
    assert first==replay and first.template_id=="residential-solar" and first.version==1 and first.display_name=="Residential Solar"
    with pytest.raises(ApplicationError) as conflict: service.assign_template(AssignOpportunityTemplateCommand(wid,"commercial_solar",1),metadata,_principal(org,"opportunity.specialize"))
    assert conflict.value.code==ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as s:
        workspace=s.get(OpportunityWorkspace,wid); assert workspace.aggregate_version==2
        assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==wid,DomainEvent.event_type.in_(["opportunity.specialized","template.assigned"])))==2
        assert s.scalar(select(func.count()).select_from(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.contract_id=="IC-OPPORTUNITY-TEMPLATE-CMD-001"))==1
        assert OpportunityWorkspaceQueryService().template(s,wid,_principal(org,"opportunity.read"),_query())==first

@pytest.mark.parametrize("authority",["", "opportunity.confirm"])
def test_assignment_authority_and_concealment_have_no_side_effects(test_database,authority):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence); service=OpportunityService(app.state.yarvis.persistence)
    with pytest.raises((ApplicationError,ValueError)): service.assign_template(AssignOpportunityTemplateCommand(wid,"residential_solar",1),_metadata(uuid4().hex),_principal(org,authority))
    with app.state.yarvis.persistence.create_session() as s: assert s.get(OpportunityWorkspace,wid).template_id is None
    foreign=uuid4()
    with pytest.raises(ApplicationError) as missing: service.assign_template(AssignOpportunityTemplateCommand(foreign,"residential_solar",1),_metadata("missing"),_principal(org,"opportunity.specialize"))
    assert missing.value.code==ApplicationErrorCode.RESOURCE_NOT_FOUND

def test_assignment_rollback_and_retry(test_database):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence); command=AssignOpportunityTemplateCommand(wid,"residential_solar",1); metadata=_metadata("rollback")
    with pytest.raises(RuntimeError): OpportunityService(_FailingRuntime(app.state.yarvis.persistence)).assign_template(command,metadata,_principal(org,"opportunity.specialize"))
    with app.state.yarvis.persistence.create_session() as s: assert s.get(OpportunityWorkspace,wid).template_id is None and s.get(OpportunityWorkspace,wid).aggregate_version==1
    assert OpportunityService(app.state.yarvis.persistence).assign_template(command,metadata,_principal(org,"opportunity.specialize")).template_id=="residential-solar"

def test_specialization_concurrency(test_database):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence); barrier=Barrier(2); metadata=_metadata("race"); command=AssignOpportunityTemplateCommand(wid,"residential_solar",1)
    def invoke(c):
        barrier.wait()
        try:return "ok",OpportunityService(app.state.yarvis.persistence).assign_template(c,metadata,_principal(org,"opportunity.specialize")).template_id
        except ApplicationError as error:return "conflict",error.code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(invoke,(command,command)))
    assert [x[0] for x in outcomes].count("ok")==2
    with app.state.yarvis.persistence.create_session() as s: assert s.get(OpportunityWorkspace,wid).aggregate_version==2

def test_foreign_and_second_specialization_have_zero_side_effects(test_database):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence); foreign,_=_workspace(app.state.yarvis.persistence,"Foreign")
    service=OpportunityService(app.state.yarvis.persistence)
    with pytest.raises(ApplicationError) as hidden: service.assign_template(AssignOpportunityTemplateCommand(wid,"residential_solar",1),_metadata("foreign"),_principal(foreign,"opportunity.specialize"))
    assert hidden.value.code==ApplicationErrorCode.RESOURCE_NOT_FOUND
    service.assign_template(AssignOpportunityTemplateCommand(wid,"residential_solar",1),_metadata("first"),_principal(org,"opportunity.specialize"))
    with pytest.raises(ApplicationError) as second: service.assign_template(AssignOpportunityTemplateCommand(wid,"commercial_solar",2),_metadata("second"),_principal(org,"opportunity.specialize"))
    assert second.value.code==ApplicationErrorCode.CONFLICT
    with app.state.yarvis.persistence.create_session() as s:
        w=s.get(OpportunityWorkspace,wid); assert w.opportunity_type=="residential_solar" and w.aggregate_version==2
        assert s.scalar(select(func.count()).select_from(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.contract_id=="IC-OPPORTUNITY-TEMPLATE-CMD-001",OpportunityCommandIdempotency.organization_id==org))==1

@pytest.mark.parametrize("same_key",[True,False])
def test_specialization_concurrent_conflicts_leave_one_winner(test_database,same_key):
    from yarvis_api.main import app
    org,wid=_workspace(app.state.yarvis.persistence,"Race")
    barrier=Barrier(2); first=_metadata("shared" if same_key else "first"); second=_metadata("shared" if same_key else "second")
    commands=(AssignOpportunityTemplateCommand(wid,"residential_solar",1),AssignOpportunityTemplateCommand(wid,"commercial_solar",1))
    def invoke(pair):
        command,metadata=pair; barrier.wait()
        try:return "ok",OpportunityService(app.state.yarvis.persistence).assign_template(command,metadata,_principal(org,"opportunity.specialize")).template_id
        except ApplicationError as error:return "conflict",error.code
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(invoke,zip(commands,(first,second))))
    assert sorted(result[0] for result in outcomes)==["conflict","ok"]
    with app.state.yarvis.persistence.create_session() as s:
        w=s.get(OpportunityWorkspace,wid); assert w.aggregate_version==2 and w.template_id in {"residential-solar","commercial-solar"}
        assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==wid,DomainEvent.event_type.in_(["opportunity.specialized","template.assigned"])))==2
        assert s.scalar(select(func.count()).select_from(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.contract_id=="IC-OPPORTUNITY-TEMPLATE-CMD-001",OpportunityCommandIdempotency.organization_id==org))==1

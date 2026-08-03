from datetime import datetime, timezone
from uuid import uuid4
import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy import func, select
from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import AssignOpportunityTemplateCommand, ConfirmOpportunityCommand, ProposeOpportunityCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import OpportunityDossier, OpportunityWorkspace
from yarvis_api.models.organization import Organization
from yarvis_api.services.opportunity import OpportunityService, OpportunityWorkspaceQueryService

def p(org,authority): return AuthenticatedPrincipal("dossier:actor",str(org),(),(),authority,"test",datetime.now(timezone.utc),False)
def m(key): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=key)
def q(): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),query_id=str(uuid4()))
def setup(runtime,name="Dossier"):
 org=Organization(id=uuid4(),legal_name=name,display_name=name);oid=org.id
 with runtime.create_session() as s:s.add(org);s.commit()
 svc=OpportunityService(runtime);o=svc.propose(ProposeOpportunityCommand("Intent"),m("p"),p(oid,"opportunity.propose"));svc.confirm(ConfirmOpportunityCommand(o.id,1),m("c"),p(oid,"opportunity.confirm"))
 with runtime.create_session() as s:return oid,s.scalar(select(OpportunityWorkspace).where(OpportunityWorkspace.opportunity_id==o.id)).id,o.id

def test_specialization_creates_one_authoritative_dossier_and_replay_is_side_effect_free(test_database):
 from yarvis_api.main import app
 org,wid,oid=setup(app.state.yarvis.persistence);svc=OpportunityService(app.state.yarvis.persistence);command=AssignOpportunityTemplateCommand(wid,"residential_solar",1);meta=m("s")
 svc.assign_template(command,meta,p(org,"opportunity.specialize"));svc.assign_template(command,meta,p(org,"opportunity.specialize"))
 with app.state.yarvis.persistence.create_session() as s:
  dossier=s.scalar(select(OpportunityDossier).where(OpportunityDossier.workspace_id==wid));assert dossier and dossier.organization_id==org and dossier.opportunity_id==oid and dossier.template_id=="residential-solar" and dossier.lifecycle_status=="active" and dossier.aggregate_version==1
  assert OpportunityWorkspaceQueryService().dossier(s,dossier.id,p(org,"opportunity.read"),q()).id==dossier.id
  assert s.scalar(select(func.count()).select_from(OpportunityDossier).where(OpportunityDossier.workspace_id==wid))==1
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==dossier.id,DomainEvent.event_type=="dossier.created"))==1

def test_foreign_dossier_is_concealed(test_database):
 from yarvis_api.main import app
 org,wid,_=setup(app.state.yarvis.persistence);foreign,_,_=setup(app.state.yarvis.persistence,"Foreign");svc=OpportunityService(app.state.yarvis.persistence);svc.assign_template(AssignOpportunityTemplateCommand(wid,"residential_solar",1),m("s"),p(org,"opportunity.specialize"))
 with app.state.yarvis.persistence.create_session() as s:
  dossier=s.scalar(select(OpportunityDossier).where(OpportunityDossier.workspace_id==wid))
  with pytest.raises(ApplicationError) as error: OpportunityWorkspaceQueryService().dossier(s,dossier.id,p(foreign,"opportunity.read"),q())
  assert error.value.code==ApplicationErrorCode.RESOURCE_NOT_FOUND

class FailRuntime:
 def __init__(self,r):self.r=r
 def create_session(self):
  s=self.r.create_session();s.commit=lambda:(_ for _ in ()).throw(RuntimeError("forced commit failure"));return s

def test_specialization_rollback_leaves_no_dossier_and_retry_is_once(test_database):
 from yarvis_api.main import app
 org,wid,_=setup(app.state.yarvis.persistence);cmd=AssignOpportunityTemplateCommand(wid,"residential_solar",1);meta=m("rollback")
 with pytest.raises(RuntimeError):OpportunityService(FailRuntime(app.state.yarvis.persistence)).assign_template(cmd,meta,p(org,"opportunity.specialize"))
 with app.state.yarvis.persistence.create_session() as s:
  assert s.get(OpportunityWorkspace,wid).template_id is None and s.get(OpportunityWorkspace,wid).aggregate_version==1
  assert s.scalar(select(func.count()).select_from(OpportunityDossier).where(OpportunityDossier.workspace_id==wid))==0
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type=="dossier.created",DomainEvent.organization_id==org))==0
 svc=OpportunityService(app.state.yarvis.persistence);svc.assign_template(cmd,meta,p(org,"opportunity.specialize"));svc.assign_template(cmd,meta,p(org,"opportunity.specialize"))
 with app.state.yarvis.persistence.create_session() as s:assert s.scalar(select(func.count()).select_from(OpportunityDossier).where(OpportunityDossier.workspace_id==wid))==1

@pytest.mark.parametrize("same_key",[True,False])
def test_specialization_races_create_one_dossier(test_database,same_key):
 from yarvis_api.main import app
 org,wid,_=setup(app.state.yarvis.persistence,"Race");barrier=Barrier(2)
 commands=(AssignOpportunityTemplateCommand(wid,"residential_solar",1),AssignOpportunityTemplateCommand(wid,"residential_solar" if same_key else "commercial_solar",1));metas=(m("shared"),m("shared" if same_key else "other"))
 def run(pair):
  c,meta=pair;barrier.wait()
  try:return "ok",OpportunityService(app.state.yarvis.persistence).assign_template(c,meta,p(org,"opportunity.specialize")).template_id
  except ApplicationError as e:return "conflict",e.code
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,zip(commands,metas)))
 assert [x[0] for x in results].count("ok")== (2 if same_key else 1)
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(OpportunityDossier).where(OpportunityDossier.workspace_id==wid))==1
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type=="dossier.created",DomainEvent.organization_id==org))==1
  assert s.get(OpportunityWorkspace,wid).aggregate_version==2

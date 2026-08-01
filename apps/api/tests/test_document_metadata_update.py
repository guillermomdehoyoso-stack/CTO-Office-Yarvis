from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import CreateDocumentCommand, UpdateDocumentCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.document_registry import Document, DocumentCommandIdempotency
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.services.document_registry import DocumentRegistryService

class _FailingCommitRuntime:
 def __init__(self,runtime): self.runtime=runtime
 def create_session(self):
  session=self.runtime.create_session()
  def fail(): raise RuntimeError("forced commit failure")
  session.commit=fail
  return session


def _principal(org, authority): return AuthenticatedPrincipal("actor",str(org),(),(),authority,"test",datetime.now(timezone.utc),False)
def _meta(key): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=key)
def _create(): return CreateDocumentCommand("Original","general","organization","text/plain","sha256","a"*64,"external",None,"urn:test","manual",{})

def test_metadata_update_replay_conflict_and_stale(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI metadata",display_name="DI metadata"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence)
 document=service.create(_create(),_meta("create"),_principal(org_id,"document.create"))
 command=UpdateDocumentCommand(document.id,1,"Changed","technical","restricted"); metadata=_meta("update")
 first=service.update(command,metadata,_principal(org_id,"document.metadata.update")); replay=service.update(command,metadata,_principal(org_id,"document.metadata.update"))
 assert (first.id,first.title,first.classification,first.visibility,first.version)==(replay.id,"Changed","technical","restricted",2)
 with pytest.raises(ApplicationError) as conflict: service.update(UpdateDocumentCommand(document.id,1,"Other","technical","restricted"),metadata,_principal(org_id,"document.metadata.update"))
 assert conflict.value.code==ApplicationErrorCode.CONFLICT
 with pytest.raises(ApplicationError) as stale: service.update(UpdateDocumentCommand(document.id,1,"Other","technical","restricted"),_meta("stale"),_principal(org_id,"document.metadata.update"))
 assert stale.value.code==ApplicationErrorCode.CONFLICT
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==document.id,DomainEvent.event_type=="document.metadata_updated"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==document.id))==2

@pytest.mark.parametrize("authority",["", "document.read"])
def test_metadata_update_requires_exact_authority(test_database,authority):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI metadata auth"+authority,display_name="DI metadata auth"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 with pytest.raises((ApplicationError,ValueError)): DocumentRegistryService(app.state.yarvis.persistence).update(UpdateDocumentCommand(uuid4(),1,"x","general","organization"),_meta(uuid4().hex),_principal(org_id,authority))

def test_metadata_update_conceals_missing_and_foreign_documents(test_database):
 from yarvis_api.main import app
 own=Organization(id=uuid4(),legal_name="DI conceal own",display_name="DI conceal own"); foreign=Organization(id=uuid4(),legal_name="DI conceal foreign",display_name="DI conceal foreign")
 own_id,foreign_id=own.id,foreign.id
 with app.state.yarvis.persistence.create_session() as s:s.add_all([own,foreign]);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); foreign_doc=service.create(_create(),_meta("foreign-create"),_principal(foreign_id,"document.create"))
 for document_id,key in ((uuid4(),"missing"),(foreign_doc.id,"foreign")):
  with pytest.raises(ApplicationError) as error: service.update(UpdateDocumentCommand(document_id,1,"x","general","organization"),_meta(key),_principal(own_id,"document.metadata.update"))
  assert error.value.code==ApplicationErrorCode.RESOURCE_NOT_FOUND and error.value.message=="document not found"
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==own_id))==0
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==own_id,DomainEvent.event_type=="document.metadata_updated"))==0

def test_metadata_update_idempotency_is_organization_scoped(test_database):
 from yarvis_api.main import app
 one=Organization(id=uuid4(),legal_name="DI scope one",display_name="DI scope one"); two=Organization(id=uuid4(),legal_name="DI scope two",display_name="DI scope two")
 one_id,two_id=one.id,two.id
 with app.state.yarvis.persistence.create_session() as s:s.add_all([one,two]);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); first=service.create(_create(),_meta("create-one"),_principal(one_id,"document.create")); second=service.create(_create(),_meta("create-two"),_principal(two_id,"document.create"))
 key="same-update-key"; a=service.update(UpdateDocumentCommand(first.id,1,"One","technical","restricted"),_meta(key),_principal(one_id,"document.metadata.update")); b=service.update(UpdateDocumentCommand(second.id,1,"Two","financial","private"),_meta(key),_principal(two_id,"document.metadata.update"))
 assert (a.title,b.title)==("One","Two")
 with app.state.yarvis.persistence.create_session() as s:
  for org in (one_id,two_id):
   assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==org,DocumentCommandIdempotency.idempotency_key==key))==1
   assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==org,DomainEvent.event_type=="document.metadata_updated"))==1

def test_metadata_update_commit_failure_rolls_back_and_retry_succeeds(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI metadata rollback",display_name="DI metadata rollback"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); document=service.create(_create(),_meta("rollback-create"),_principal(org_id,"document.create")); command=UpdateDocumentCommand(document.id,1,"Changed","technical","restricted"); metadata=_meta("rollback-update")
 with pytest.raises(RuntimeError): DocumentRegistryService(_FailingCommitRuntime(app.state.yarvis.persistence)).update(command,metadata,_principal(org_id,"document.metadata.update"))
 with app.state.yarvis.persistence.create_session() as s:
  current=s.get(Document,document.id)
  assert (current.title,current.classification,current.visibility,current.version)==("Original","general","organization",1)
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==document.id,DomainEvent.event_type=="document.metadata_updated"))==0
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==document.id,DocumentCommandIdempotency.idempotency_key=="rollback-update"))==0
 result=service.update(command,metadata,_principal(org_id,"document.metadata.update")); assert result.version==2

def test_matching_concurrent_metadata_update_replays(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI update race",display_name="DI update race"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); document=service.create(_create(),_meta("race-create"),_principal(org_id,"document.create")); command=UpdateDocumentCommand(document.id,1,"Race","technical","restricted"); metadata=_meta("race-update"); barrier=Barrier(2)
 def invoke(): barrier.wait(); return DocumentRegistryService(app.state.yarvis.persistence).update(command,metadata,_principal(org_id,"document.metadata.update"))
 with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:invoke(),range(2)))
 assert results[0].id==results[1].id and results[0].version==results[1].version==2
 with app.state.yarvis.persistence.create_session() as s:
  assert s.get(Document,document.id).title=="Race" and s.get(Document,document.id).version==2
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==document.id,DomainEvent.event_type=="document.metadata_updated"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==document.id,DocumentCommandIdempotency.idempotency_key=="race-update"))==1

def test_mismatched_concurrent_metadata_update_conflicts(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI update conflict",display_name="DI update conflict"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); document=service.create(_create(),_meta("race-conflict-create"),_principal(org_id,"document.create")); metadata=_meta("race-conflict-update"); barrier=Barrier(2)
 commands=(UpdateDocumentCommand(document.id,1,"Winner","technical","restricted"),UpdateDocumentCommand(document.id,1,"Loser","financial","private"))
 def invoke(command):
  barrier.wait()
  try:return ("success",DocumentRegistryService(app.state.yarvis.persistence).update(command,metadata,_principal(org_id,"document.metadata.update")))
  except ApplicationError as error:return ("conflict",error.code)
 with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(invoke,commands))
 assert sorted(item[0] for item in outcomes)==["conflict","success"]
 with app.state.yarvis.persistence.create_session() as s:
  assert s.get(Document,document.id).version==2
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==document.id,DomainEvent.event_type=="document.metadata_updated"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==document.id,DocumentCommandIdempotency.idempotency_key=="race-conflict-update"))==1

from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import func, select
from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.document_registry import CreateDocumentCommand
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.models.document_registry import DocumentCommandIdempotency
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.services.document_registry import DocumentRegistryService
class _FailingCommitRuntime:
 def __init__(self,runtime):self.runtime=runtime
 def create_session(self):
  session=self.runtime.create_session();session.commit=lambda:(_ for _ in ()).throw(RuntimeError("forced commit failure"));return session
def p(o,a):return AuthenticatedPrincipal("actor",str(o),(),(),a,"test",datetime.now(timezone.utc),False)
def m(k,v=None):return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=k,expected_aggregate_version=v)
def c():return CreateDocumentCommand("Original","general","organization","text/plain","sha256","a"*64,"external",None,"urn:test","manual",{})
def test_archive_replay_conflict_and_preservation(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI archive",display_name="DI archive");oid=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence);doc=service.create(c(),m("create"),p(oid,"document.create")); meta=m("archive",1)
 first=service.archive(doc.id,meta,p(oid,"document.archive")); replay=service.archive(doc.id,meta,p(oid,"document.archive"))
 assert first.lifecycle_status==replay.lifecycle_status=="archived" and first.archived_at==replay.archived_at and first.version==replay.version==2 and first.title=="Original"
 with pytest.raises(ApplicationError) as error:service.archive(doc.id,m("fresh",2),p(oid,"document.archive"))
 assert error.value.code==ApplicationErrorCode.CONFLICT
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==doc.id,DomainEvent.event_type=="document.archived"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==doc.id,DocumentCommandIdempotency.contract_id=="IC-DOCUMENT-CMD-004"))==1

@pytest.mark.parametrize("authority",["", "document.read"])
def test_archive_requires_exact_authority(test_database,authority):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI archive auth"+authority,display_name="DI archive auth");oid=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 with pytest.raises((ApplicationError,ValueError)):DocumentRegistryService(app.state.yarvis.persistence).archive(uuid4(),m(uuid4().hex),p(oid,authority))

def test_archive_conceals_missing_and_foreign_documents(test_database):
 from yarvis_api.main import app
 one=Organization(id=uuid4(),legal_name="DI archive one",display_name="DI archive one");two=Organization(id=uuid4(),legal_name="DI archive two",display_name="DI archive two");one_id,two_id=one.id,two.id
 with app.state.yarvis.persistence.create_session() as s:s.add_all([one,two]);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); foreign=service.create(c(),m("foreign"),p(two_id,"document.create"))
 for document_id,key in ((uuid4(),"missing"),(foreign.id,"foreign-archive")):
  with pytest.raises(ApplicationError) as error:service.archive(document_id,m(key,1),p(one_id,"document.archive"))
  assert error.value.code==ApplicationErrorCode.RESOURCE_NOT_FOUND and error.value.message=="document not found"
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==one_id,DomainEvent.event_type=="document.archived"))==0
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==one_id,DocumentCommandIdempotency.contract_id=="IC-DOCUMENT-CMD-004"))==0

def test_archive_idempotency_is_organization_scoped(test_database):
 from yarvis_api.main import app
 one=Organization(id=uuid4(),legal_name="DI archive scope one",display_name="DI archive scope one");two=Organization(id=uuid4(),legal_name="DI archive scope two",display_name="DI archive scope two");one_id,two_id=one.id,two.id
 with app.state.yarvis.persistence.create_session() as s:s.add_all([one,two]);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence);first=service.create(c(),m("scope-create-one"),p(one_id,"document.create"));second=service.create(c(),m("scope-create-two"),p(two_id,"document.create"))
 key="same-archive-key";assert service.archive(first.id,m(key,1),p(one_id,"document.archive")).lifecycle_status=="archived";assert service.archive(second.id,m(key,1),p(two_id,"document.archive")).lifecycle_status=="archived"
 with app.state.yarvis.persistence.create_session() as s:
  for org in (one_id,two_id):
   assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==org,DomainEvent.event_type=="document.archived"))==1
   assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==org,DocumentCommandIdempotency.contract_id=="IC-DOCUMENT-CMD-004",DocumentCommandIdempotency.idempotency_key==key))==1

def test_archive_commit_failure_rolls_back_and_retry_succeeds(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI archive rollback",display_name="DI archive rollback");oid=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence);doc=service.create(c(),m("rollback-create"),p(oid,"document.create"));metadata=m("rollback-archive",1)
 with pytest.raises(RuntimeError):DocumentRegistryService(_FailingCommitRuntime(app.state.yarvis.persistence)).archive(doc.id,metadata,p(oid,"document.archive"))
 with app.state.yarvis.persistence.create_session() as s:
  current=s.get(__import__("yarvis_api.models.document_registry",fromlist=["Document"]).Document,doc.id)
  assert (current.lifecycle_status,current.archived_at,current.version)==("active",None,1)
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==doc.id,DomainEvent.event_type=="document.archived"))==0
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==doc.id,DocumentCommandIdempotency.idempotency_key=="rollback-archive"))==0
 assert service.archive(doc.id,metadata,p(oid,"document.archive")).version==2

def test_matching_concurrent_archive_replays_winning_receipt(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI archive race",display_name="DI archive race");oid=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence);doc=service.create(c(),m("race-create"),p(oid,"document.create"));metadata=m("race-archive",1);barrier=Barrier(2)
 def invoke():barrier.wait();return DocumentRegistryService(app.state.yarvis.persistence).archive(doc.id,metadata,p(oid,"document.archive"))
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:invoke(),range(2)))
 assert results[0].id==results[1].id and results[0].archived_at==results[1].archived_at and results[0].version==results[1].version==2
 assert service.archive(doc.id,metadata,p(oid,"document.archive")).version==2
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==doc.id,DomainEvent.event_type=="document.archived"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==doc.id,DocumentCommandIdempotency.idempotency_key=="race-archive"))==1

def test_mismatched_concurrent_archive_conflicts(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI archive conflict",display_name="DI archive conflict");oid=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence);doc=service.create(c(),m("conflict-create"),p(oid,"document.create"));barrier=Barrier(2);metas=(m("conflict-archive",None),m("conflict-archive",1))
 def invoke(metadata):
  barrier.wait()
  try:return ("success",DocumentRegistryService(app.state.yarvis.persistence).archive(doc.id,metadata,p(oid,"document.archive")))
  except ApplicationError as error:return ("conflict",error.code)
 with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(invoke,metas))
 assert sorted(item[0] for item in outcomes)==["conflict","success"]
 winner=next(item[1] for item in outcomes if item[0]=="success")
 assert service.archive(doc.id,metas[0] if outcomes[0][0]=="success" else metas[1],p(oid,"document.archive")).id==winner.id
 with app.state.yarvis.persistence.create_session() as s:
  current=s.get(__import__("yarvis_api.models.document_registry",fromlist=["Document"]).Document,doc.id)
  assert current.lifecycle_status=="archived" and current.version==2
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.aggregate_id==doc.id,DomainEvent.event_type=="document.archived"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.aggregate_id==doc.id,DocumentCommandIdempotency.idempotency_key=="conflict-archive"))==1

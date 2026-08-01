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
from yarvis_api.models.document_registry import Document, DocumentCommandIdempotency
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.services.document_registry import DocumentRegistryService


class _FailingCommitRuntime:
 def __init__(self, runtime): self.runtime=runtime; self.session=None
 def create_session(self):
  session=self.runtime.create_session(); self.session=session; original=session.commit
  def fail(): raise RuntimeError("forced commit failure")
  session.commit=fail
  return session


def _principal(org, authority="document.create"):
 return AuthenticatedPrincipal("actor",str(org),(),(),authority,"test",datetime.now(timezone.utc),False)
def _metadata(key): return RequestMetadata(datetime.now(timezone.utc),str(uuid4()),command_id=str(uuid4()),idempotency_key=key)
def _command(): return CreateDocumentCommand("Document","general","organization","text/plain","sha256","a"*64,"external",None,"urn:test","manual",{})

def test_create_document_replays_and_conflicts(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI command",display_name="DI command")
 org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 service=DocumentRegistryService(app.state.yarvis.persistence); metadata=_metadata("key")
 first=service.create(_command(),metadata,_principal(org_id)); replay=service.create(_command(),metadata,_principal(org_id))
 assert replay.id==first.id
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(Document))==1
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.event_type=="document.registered"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency))==1
 with pytest.raises(ApplicationError) as error: service.create(CreateDocumentCommand("Other","general","organization","text/plain","sha256","a"*64,"external",None,"urn:test","manual",{}),metadata,_principal(org_id))
 assert error.value.code==ApplicationErrorCode.CONFLICT

@pytest.mark.parametrize("authority",["", "document.read"])
def test_create_document_requires_exact_authority(test_database,authority):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI authority"+authority,display_name="DI authority")
 org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 with pytest.raises((ApplicationError,ValueError)): DocumentRegistryService(app.state.yarvis.persistence).create(_command(),_metadata(uuid4().hex),_principal(org_id,authority))

def test_create_commit_failure_rolls_back_everything_and_retry_succeeds(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI rollback",display_name="DI rollback"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 metadata=_metadata("rollback-key")
 failing=_FailingCommitRuntime(app.state.yarvis.persistence)
 with pytest.raises(RuntimeError,match="forced commit failure"): DocumentRegistryService(failing).create(_command(),metadata,_principal(org_id))
 assert failing.session is not None
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(Document).where(Document.organization_id==org_id))==0
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==org_id,DomainEvent.event_type=="document.registered"))==0
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==org_id,DocumentCommandIdempotency.idempotency_key=="rollback-key"))==0
 assert DocumentRegistryService(app.state.yarvis.persistence).create(_command(),metadata,_principal(org_id)).id

def test_matching_concurrent_create_replays_winning_receipt(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI race",display_name="DI race"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 barrier=Barrier(2); metadata=_metadata("race-key")
 def invoke():
  barrier.wait()
  return DocumentRegistryService(app.state.yarvis.persistence).create(_command(),metadata,_principal(org_id)).id
 with ThreadPoolExecutor(max_workers=2) as pool: ids=list(pool.map(lambda _:invoke(),range(2)))
 assert ids[0]==ids[1]
 assert DocumentRegistryService(app.state.yarvis.persistence).create(_command(),metadata,_principal(org_id)).id==ids[0]
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(Document).where(Document.organization_id==org_id))==1
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==org_id,DomainEvent.event_type=="document.registered"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==org_id,DocumentCommandIdempotency.idempotency_key=="race-key"))==1

def test_mismatched_concurrent_create_conflicts_against_winning_receipt(test_database):
 from yarvis_api.main import app
 org=Organization(id=uuid4(),legal_name="DI race conflict",display_name="DI race conflict"); org_id=org.id
 with app.state.yarvis.persistence.create_session() as s:s.add(org);s.commit()
 barrier=Barrier(2); metadata=_metadata("race-conflict-key")
 winning=_command(); losing=CreateDocumentCommand("Different","general","organization","text/plain","sha256","a"*64,"external",None,"urn:test","manual",{})
 def invoke(command):
  barrier.wait()
  try:return ("success",DocumentRegistryService(app.state.yarvis.persistence).create(command,metadata,_principal(org_id)).id)
  except ApplicationError as error:return ("conflict",error.code)
 with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(invoke,(winning,losing)))
 assert sorted(item[0] for item in outcomes)==["conflict","success"]
 winner=next(item[1] for item in outcomes if item[0]=="success")
 assert DocumentRegistryService(app.state.yarvis.persistence).create(winning if outcomes[0][0]=="success" else losing,metadata,_principal(org_id)).id==winner
 with app.state.yarvis.persistence.create_session() as s:
  assert s.scalar(select(func.count()).select_from(Document).where(Document.organization_id==org_id))==1
  assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id==org_id,DomainEvent.event_type=="document.registered"))==1
  assert s.scalar(select(func.count()).select_from(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==org_id,DocumentCommandIdempotency.idempotency_key=="race-conflict-key"))==1

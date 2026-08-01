from dataclasses import asdict,dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID
from sqlalchemy import func,select
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation
from yarvis_api.application.errors import ApplicationError,ApplicationErrorCode
from yarvis_api.application.service_boundary import enforce_command_boundary,enforce_query_boundary
from yarvis_api.application.contracts import DI002CommandName,DI002QueryName,command_contracts,query_contracts
from yarvis_api.models.document_registry import Document,DocumentVersion,DocumentAssociation,DocumentCommandIdempotency
from yarvis_api.models.domain_event import record_event
from yarvis_api.persistence import UnitOfWork,OperationScope,PersistenceRuntime
from yarvis_api.services.inbound_intake import _principal_organization_id
from yarvis_api.clock import utc_now
from yarvis_api.schemas.document_registry import DocumentRead,DocumentVersionRead,DocumentAssociationRead,DocumentPage
from yarvis_api.application.document_registry import *
from yarvis_api.models.organization import Organization
from yarvis_api.models.operational_context import Site,Project
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.operational_task import OperationalTask
from yarvis_api.models.process import ProcessInstance
_TYPES={"organization":Organization,"site":Site,"project":Project,"mission_work_item":MissionWorkItem,"operational_task":OperationalTask,"process_instance":ProcessInstance}
def err(code,msg): return ApplicationError(code,msg,{"resource":"document"})
def nf(): return err(ApplicationErrorCode.RESOURCE_NOT_FOUND,"document not found")
def fp(n,c): return sha256(dumps({"action":n,"request":asdict(c)},sort_keys=True,default=str).encode()).hexdigest()
def key(m):
 if not m.idempotency_key: raise err(ApplicationErrorCode.PRECONDITION_FAILED,"idempotency key is required")
 return m.idempotency_key
def version_read(x): return DocumentVersionRead.model_validate(x)
@dataclass(slots=True)
class DocumentRegistryService:
 persistence:PersistenceRuntime
 def create(self,c,m,p):
  contract=command_contracts[DI002CommandName.CREATE];enforce_command_boundary(contract,metadata=m,principal=p);org=_principal_organization_id(p);k=key(m);f=sha256(dumps({"contract_id":contract.interaction_contract_id,"organization_id":str(org),"payload":asdict(c)},sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
  try:
   with UnitOfWork(self.persistence,OperationScope()) as u:
    s=u.session;receipt=self._receipt(s,org,contract.interaction_contract_id,k)
    if receipt:return self._replay(s,receipt,f,k)
    d=Document(organization_id=org,title=c.title,classification=c.classification,visibility=c.visibility,created_by_subject_id=p.actor_id);s.add(d);s.flush();v=self._version(s,d,c,p,1,None);d.current_version_id=v.id;self._event(s,d,"document.registered",m,p,{"document_version_id":str(v.id)})
    s.add(DocumentCommandIdempotency(organization_id=org,contract_id=contract.interaction_contract_id,idempotency_key=k,request_fingerprint=f,aggregate_id=d.id,response_kind="document",response_payload={"document_id":str(d.id)}));r=self._read(s,d);u.commit();return r
  except IntegrityError as e:
   if not(isinstance(e.orig,UniqueViolation) and e.orig.diag.constraint_name=="uq_document_command_idempotency"):raise
   with UnitOfWork(self.persistence,OperationScope()) as u:return self._replay(u.session,self._receipt(u.session,org,contract.interaction_contract_id,k),f,k)
 def _receipt(self,s,o,c,k): return s.scalar(select(DocumentCommandIdempotency).where(DocumentCommandIdempotency.organization_id==o,DocumentCommandIdempotency.contract_id==c,DocumentCommandIdempotency.idempotency_key==k))
 def _replay(self,s,r,f,k):
  if r is None:raise err(ApplicationErrorCode.CONFLICT,"idempotency receipt unavailable")
  if r.request_fingerprint!=f:raise err(ApplicationErrorCode.CONFLICT,"idempotency key was previously used for a different document command")
  return self._read(s,self._doc(s,r.aggregate_id,r.organization_id))
 def add(self, c, m, p):
    contract = command_contracts[DI002CommandName.ADD_VERSION]
    enforce_command_boundary(contract, metadata=m, principal=p)

    org = _principal_organization_id(p)
    k = key(m)

    f = sha256(
        dumps(
            {
                "contract_id": contract.interaction_contract_id,
                "organization_id": str(org),
                "document_id": str(c.document_id),
                "expected_version": m.expected_aggregate_version,
                "payload": asdict(c),
            },
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    try:
        with UnitOfWork(self.persistence, OperationScope()) as u:
            s = u.session

            receipt = self._receipt(
                s,
                org,
                contract.interaction_contract_id,
                k,
            )

            if receipt:
                if receipt.request_fingerprint != f:
                    raise err(
                        ApplicationErrorCode.CONFLICT,
                        "idempotency key was previously used for a different document command",
                    )

                version = s.get(DocumentVersion, receipt.aggregate_id)

                if version is None:
                    raise err(
                        ApplicationErrorCode.CONFLICT,
                        "idempotency receipt result unavailable",
                    )

                return version_read(version)

            d = self._doc(s, c.document_id, org, True)

            if d.lifecycle_status != "active":
                raise err(
                    ApplicationErrorCode.CONFLICT,
                    "document is archived",
                )

            if (
                m.expected_aggregate_version is not None
                and d.version != m.expected_aggregate_version
            ):
                raise err(
                    ApplicationErrorCode.CONFLICT,
                    "document version conflict",
                )

            seq = (
                s.scalar(
                    select(func.max(DocumentVersion.sequence)).where(
                        DocumentVersion.document_id == d.id
                    )
                )
                or 0
            )

            v = self._version(
                s,
                d,
                c,
                p,
                seq + 1,
                d.current_version_id,
            )

            d.current_version_id = v.id
            d.version += 1
            d.updated_at = utc_now()

            self._event(
                s,
                d,
                "document.version_added",
                m,
                p,
                {
                    "document_version_id": str(v.id),
                    "idempotency_key": k,
                },
            )

            s.add(
                DocumentCommandIdempotency(
                    organization_id=org,
                    contract_id=contract.interaction_contract_id,
                    idempotency_key=k,
                    request_fingerprint=f,
                    aggregate_id=v.id,
                    response_kind="document_version",
                    response_payload={
                        "document_version_id": str(v.id),
                    },
                )
            )

            result = version_read(v)
            u.commit()
            return result

    except IntegrityError as exc:
        if not (
            isinstance(exc.orig, UniqueViolation)
            and exc.orig.diag.constraint_name
            == "uq_document_command_idempotency"
        ):
            raise

        with UnitOfWork(self.persistence, OperationScope()) as u:
            receipt = self._receipt(
                u.session,
                org,
                contract.interaction_contract_id,
                k,
            )

            if receipt is None or receipt.request_fingerprint != f:
                raise err(
                    ApplicationErrorCode.CONFLICT,
                    "idempotency key was previously used for a different document command",
                )

            version = u.session.get(
                DocumentVersion,
                receipt.aggregate_id,
            )

            if version is None:
                raise err(
                    ApplicationErrorCode.CONFLICT,
                    "idempotency receipt result unavailable",
                )

            return version_read(version)
 def update(self,c,m,p):
  contract=command_contracts[DI002CommandName.UPDATE];enforce_command_boundary(contract,metadata=m,principal=p);org=_principal_organization_id(p);k=key(m);f=sha256(dumps({"contract_id":contract.interaction_contract_id,"organization_id":str(org),"document_id":str(c.document_id),"payload":asdict(c)},sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
  try:
   with UnitOfWork(self.persistence,OperationScope()) as u:
    s=u.session;receipt=self._receipt(s,org,contract.interaction_contract_id,k)
    if receipt:return self._replay(s,receipt,f,k)
    d=self._doc(s,c.document_id,org,True)
    receipt=self._receipt(s,org,contract.interaction_contract_id,k)
    if receipt:return self._replay(s,receipt,f,k)
    if d.version!=c.expected_version: raise err(ApplicationErrorCode.CONFLICT,"document version conflict")
    d.title,d.classification,d.visibility=c.title,c.classification,c.visibility;d.version+=1;d.updated_at=utc_now();self._event(s,d,"document.metadata_updated",m,p,{"changed_fields":["title","classification","visibility"],"idempotency_key":k})
    s.add(DocumentCommandIdempotency(organization_id=org,contract_id=contract.interaction_contract_id,idempotency_key=k,request_fingerprint=f,aggregate_id=d.id,response_kind="document",response_payload={"document_id":str(d.id)}));r=self._read(s,d);u.commit();return r
  except IntegrityError as e:
   if not(isinstance(e.orig,UniqueViolation) and e.orig.diag.constraint_name=="uq_document_command_idempotency"):raise
   with UnitOfWork(self.persistence,OperationScope()) as u:return self._replay(u.session,self._receipt(u.session,org,contract.interaction_contract_id,k),f,k)
 def archive(self,i,m,p):
  contract=command_contracts[DI002CommandName.ARCHIVE];enforce_command_boundary(contract,metadata=m,principal=p);org=_principal_organization_id(p);k=key(m);f=sha256(dumps({"contract_id":contract.interaction_contract_id,"organization_id":str(org),"document_id":str(i),"expected_version":m.expected_aggregate_version},sort_keys=True,separators=(",",":")).encode()).hexdigest()
  try:
   with UnitOfWork(self.persistence,OperationScope()) as u:
    s=u.session;receipt=self._receipt(s,org,contract.interaction_contract_id,k)
    if receipt:return self._replay(s,receipt,f,k)
    d=self._doc(s,i,org,True)
    receipt=self._receipt(s,org,contract.interaction_contract_id,k)
    if receipt:return self._replay(s,receipt,f,k)
    if m.expected_aggregate_version is not None and d.version!=m.expected_aggregate_version:raise err(ApplicationErrorCode.CONFLICT,"document version conflict")
    if d.lifecycle_status=="archived":raise err(ApplicationErrorCode.CONFLICT,"document is already archived")
    d.lifecycle_status="archived";d.archived_at=utc_now();d.version+=1;self._event(s,d,"document.archived",m,p,{"lifecycle_status":"archived","idempotency_key":k})
    s.add(DocumentCommandIdempotency(organization_id=org,contract_id=contract.interaction_contract_id,idempotency_key=k,request_fingerprint=f,aggregate_id=d.id,response_kind="document",response_payload={"document_id":str(d.id)}));r=self._read(s,d);u.commit();return r
  except IntegrityError as e:
   if not(isinstance(e.orig,UniqueViolation) and e.orig.diag.constraint_name=="uq_document_command_idempotency"):raise
   with UnitOfWork(self.persistence,OperationScope()) as u:return self._replay(u.session,self._receipt(u.session,org,contract.interaction_contract_id,k),f,k)
 def link(self,c,m,p,unlink=False):
  n=DI002CommandName.UNLINK if unlink else DI002CommandName.LINK;enforce_command_boundary(command_contracts[n],metadata=m,principal=p);org=_principal_organization_id(p)
  with UnitOfWork(self.persistence,OperationScope()) as u:
   s=u.session;d=self._doc(s,c.document_id,org,True);self._subject(s,c.subject_type,c.subject_id,org)
   a=s.scalar(select(DocumentAssociation).where(DocumentAssociation.document_id==d.id).where(DocumentAssociation.subject_type==c.subject_type).where(DocumentAssociation.subject_id==c.subject_id).where(DocumentAssociation.unlinked_at.is_(None)).with_for_update())
   if unlink:
    if not a: raise nf()
    a.unlinked_at=utc_now();event="document.unlinked"
   else:
    if a: return DocumentAssociationRead.model_validate(a)
    a=DocumentAssociation(organization_id=org,document_id=d.id,subject_type=c.subject_type,subject_id=c.subject_id,linked_by_subject_id=p.actor_id);s.add(a);event="document.associated"
   s.flush();self._event(s,d,event,m,p,{"subject_type":c.subject_type,"subject_id":str(c.subject_id)});r=DocumentAssociationRead.model_validate(a);u.commit();return r
 def _version(self,s,d,c,p,seq,sup):
  if c.storage_key and (c.storage_key.startswith(("/","\\")) or (len(c.storage_key)>2 and c.storage_key[1]==":") or ".." in c.storage_key.replace("\\","/").split("/")): raise err(ApplicationErrorCode.VALIDATION_FAILED,"storage key must be provider-relative")
  if not c.storage_key and not c.external_reference: raise err(ApplicationErrorCode.VALIDATION_FAILED,"storage key or external reference is required")
  if not c.checksum_algorithm or not c.checksum_value: raise err(ApplicationErrorCode.VALIDATION_FAILED,"checksum algorithm and value are required")
  if c.byte_size is not None and c.byte_size<0: raise err(ApplicationErrorCode.VALIDATION_FAILED,"byte size must be non-negative")
  v=DocumentVersion(organization_id=d.organization_id,document_id=d.id,sequence=seq,media_type=c.media_type,original_filename=c.original_filename,byte_size=c.byte_size,checksum_algorithm=c.checksum_algorithm,checksum_value=c.checksum_value,storage_provider=c.storage_provider,storage_key=c.storage_key,external_reference=c.external_reference,source_kind=c.source_kind,source_reference=c.source_reference,provenance=c.provenance,created_by_subject_id=p.actor_id,supersedes_version_id=sup);s.add(v);s.flush();return v
 def _doc(self,s,i,o,lock=False):
  q=select(Document).where(Document.id==i).where(Document.organization_id==o)
  if lock:q=q.with_for_update()
  d=s.scalar(q)
  if not d:raise nf()
  return d
 def _subject(self,s,t,i,o):
  M=_TYPES.get(t)
  if not M:raise nf()
  if not s.scalar(select(M).where(M.id==i).where(M.organization_id==o)):raise nf()
 def _event(self,s,d,t,m,p,x): record_event(s,event_type=t,aggregate_type="document",aggregate_id=d.id,organization_id=d.organization_id,correlation_id=UUID(m.correlation_id),causation_id=UUID(m.causation_id) if m.causation_id else None,payload={**x,"actor_subject_id":p.actor_id,"authority_scope":p.authority})
 def _read(self,s,d): return DocumentRead.model_validate(d).model_copy(update={"active_association_count":s.scalar(select(func.count()).select_from(DocumentAssociation).where(DocumentAssociation.document_id==d.id).where(DocumentAssociation.unlinked_at.is_(None))) or 0})
@dataclass(frozen=True,slots=True)
class DocumentRegistryQueryService:
 def get(self,s,i,p,m):
  enforce_query_boundary(query_contracts[DI002QueryName.GET],metadata=m,principal=p); service=DocumentRegistryService(None); return service._read(s,service._doc(s,i,_principal_organization_id(p)))

"""Tenant-owned Netpay Inbox core. B2 operations intentionally have no route."""
from hashlib import sha256
import json
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_inbox_authority import netpay_inbox_envelope
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.netpay_inbox import NetpayCaseActivity, NetpayCaseChecklistItem, NetpayCaseDocumentReference, NetpayCaseNextAction, NetpayCaseStep, NetpayCaseType, NetpayChecklistTemplate, NetpayInboxCommandReceipt, NetpayServiceCase
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.schemas.netpay_inbox import CaseClassify, CaseCreate, CaseRead, InboxPage

router = APIRouter(prefix="/netpay/inbox", tags=["netpay-inbox"])
_CASE_TYPES = ("merchant_onboarding","branch_onboarding","tpv_activation","ecommerce_activation","bank_account_change","document_submission","legal_entity_change","franchisee_change","store_deactivation","terminal_replacement","support_incident","unclassified")

def _ensure_catalog(db, e):
    if db.scalar(select(NetpayCaseType.id).where(NetpayCaseType.organization_id == e.organization_id)):
        return
    for key in _CASE_TYPES:
        db.add(NetpayCaseType(organization_id=e.organization_id, semantic_key=key, display_name=key.replace("_", " ").title(), allowed_products=["tpv", "ecommerce", "mixed", "not_applicable"], completion_policy={"provisional_requirements": True}, created_by_principal_id=e.principal_id, updated_by_principal_id=e.principal_id))
    db.flush()

def _operator(e): return netpay_inbox_envelope(e, required_scope="netpay.inbox.manage")
def _viewer(e): return netpay_inbox_envelope(e, required_scope="netpay.inbox.read")
def _fp(command, target, payload): return sha256(json.dumps({"command":command,"target":str(target) if target else None,"payload":payload}, default=str, sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _case_read(db, item):
    actions=db.scalars(select(NetpayCaseNextAction).where(NetpayCaseNextAction.case_id==item.id).order_by(NetpayCaseNextAction.created_at)).all()
    return CaseRead.model_validate(item).model_copy(update={"requires_attention":item.state in {"information_pending","blocked"} or item.responsible_principal_id is None or not any(a.status=="open" for a in actions),"checklist":[{"id":str(x.id),"requirement_key":x.requirement_key,"status":x.status,"required":x.required} for x in db.scalars(select(NetpayCaseChecklistItem).where(NetpayCaseChecklistItem.case_id==item.id)).all()],"steps":[{"id":str(x.id),"ordinal":x.ordinal,"description":x.description,"status":x.status} for x in db.scalars(select(NetpayCaseStep).where(NetpayCaseStep.case_id==item.id).order_by(NetpayCaseStep.ordinal)).all()],"next_actions":[{"id":str(x.id),"description":x.description,"status":x.status} for x in actions],"activities":[{"id":str(x.id),"type":x.activity_type,"summary":x.safe_summary} for x in db.scalars(select(NetpayCaseActivity).where(NetpayCaseActivity.case_id==item.id).order_by(NetpayCaseActivity.created_at, NetpayCaseActivity.id)).all()],"document_references":[{"id":str(x.id),"status":x.status,"external_evidence_reference":x.external_evidence_reference} for x in db.scalars(select(NetpayCaseDocumentReference).where(NetpayCaseDocumentReference.case_id==item.id)).all()]})
def _execute(db,e,key,command,payload,mutation,target=None):
    current=_operator(e); key=key.strip(); fingerprint=_fp(command,target,payload)
    receipt=db.scalar(select(NetpayInboxCommandReceipt).where(NetpayInboxCommandReceipt.organization_id==current.organization_id,NetpayInboxCommandReceipt.command_type==command,NetpayInboxCommandReceipt.idempotency_key==key))
    if receipt:
        if receipt.request_fingerprint!=fingerprint: raise HTTPException(409,"idempotency conflict")
        return receipt.result_resource_id,receipt.result_status_code
    try: correlation=UUID(current.correlation_id)
    except ValueError: correlation=uuid4()
    resource,status_code=mutation(current,correlation)
    db.add(NetpayInboxCommandReceipt(organization_id=current.organization_id,command_type=command,idempotency_key=key,request_fingerprint=fingerprint,actor_principal_id=current.principal_id,correlation_id=correlation,result_resource_id=resource,result_status_code=status_code)); db.flush(); return resource,status_code
def _masters(db,e,p):
    client=db.scalar(select(NetpayClient).where(NetpayClient.id==p.client_id,NetpayClient.organization_id==e.organization_id)); company=db.scalar(select(NetpayCompany).where(NetpayCompany.id==p.company_id,NetpayCompany.organization_id==e.organization_id,NetpayCompany.client_id==p.client_id))
    if not client or not company: raise HTTPException(404,"not found")
    if p.branch_id and not db.scalar(select(NetpayBranch).where(NetpayBranch.id==p.branch_id,NetpayBranch.organization_id==e.organization_id,NetpayBranch.company_id==p.company_id)): raise HTTPException(404,"not found")
    if p.store_reference_id and not db.scalar(select(NetpayStoreReference).where(NetpayStoreReference.id==p.store_reference_id,NetpayStoreReference.organization_id==e.organization_id,NetpayStoreReference.active.is_(True))): raise HTTPException(404,"not found")
@router.post("/cases",response_model=CaseRead,status_code=201)
def create_case(payload:CaseCreate,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  _ensure_catalog(db,e); _masters(db,e,payload); typ=db.scalar(select(NetpayCaseType).where(NetpayCaseType.organization_id==e.organization_id,NetpayCaseType.semantic_key==payload.case_type_key,NetpayCaseType.active.is_(True)))
  if not typ: raise HTTPException(422,"unknown case type")
  folio=f"NPS-{str(uuid4())[:8].upper()}"; item=NetpayServiceCase(organization_id=e.organization_id,folio=folio,client_id=payload.client_id,company_id=payload.company_id,branch_id=payload.branch_id,store_reference_id=payload.store_reference_id,case_type_key=payload.case_type_key,original_description=payload.original_description,expected_outcome=payload.expected_outcome,product=payload.product,priority=payload.priority,source_channel=payload.source_channel,source_reference=payload.source_reference,provenance=payload.provenance,created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id); db.add(item); db.flush(); record_event(db,event_type="netpay_service_case.created",aggregate_type="netpay_service_case",aggregate_id=item.id,organization_id=e.organization_id,correlation_id=c,causation_id=c,payload={"case_id":str(item.id),"folio":folio,"actor_principal_id":str(e.principal_id)}); return item.id,201
 try: rid,code=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-009",payload.model_dump(mode="python"),mutate); db.commit()
 except IntegrityError as x: db.rollback(); raise HTTPException(409,"conflict") from x
 item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==rid,NetpayServiceCase.organization_id==envelope.organization_id)); response.status_code=code; return _case_read(db,item)
@router.put("/cases/{case_id}/classification",response_model=CaseRead)
def classify_case(case_id:UUID,payload:CaseClassify,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==case_id,NetpayServiceCase.organization_id==e.organization_id)); typ=db.scalar(select(NetpayCaseType).where(NetpayCaseType.organization_id==e.organization_id,NetpayCaseType.semantic_key==payload.case_type_key,NetpayCaseType.active.is_(True)))
  if not item or not typ: raise HTTPException(404,"not found")
  item.case_type_key,item.product,item.expected_outcome,item.priority,item.updated_by_principal_id=payload.case_type_key,payload.product,payload.expected_outcome,payload.priority,e.principal_id
  template=db.scalar(select(NetpayChecklistTemplate).where(NetpayChecklistTemplate.organization_id==e.organization_id,NetpayChecklistTemplate.case_type_key==payload.case_type_key,NetpayChecklistTemplate.active.is_(True)).order_by(NetpayChecklistTemplate.version.desc()))
  if template: item.checklist_template_version=template.version; [db.add(NetpayCaseChecklistItem(organization_id=e.organization_id,case_id=item.id,template_version=template.version,requirement_key=r["key"],required=r.get("required",True),created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id)) for r in template.requirements]
  record_event(db,event_type="netpay_service_case.classified",aggregate_type="netpay_service_case",aggregate_id=item.id,organization_id=e.organization_id,correlation_id=c,causation_id=c,payload={"case_id":str(item.id),"case_type_key":item.case_type_key,"actor_principal_id":str(e.principal_id)}); return item.id,200
 rid,code=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-010",payload.model_dump(mode="python"),mutate,case_id); db.commit(); item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==rid,NetpayServiceCase.organization_id==envelope.organization_id)); response.status_code=code; return _case_read(db,item)
@router.get("",response_model=InboxPage)
def list_inbox(query:str|None=None,state:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 e=_viewer(envelope); stmt=select(NetpayServiceCase).where(NetpayServiceCase.organization_id==e.organization_id)
 if state: stmt=stmt.where(NetpayServiceCase.state==state)
 if query: stmt=stmt.where(or_(NetpayServiceCase.folio.ilike(f"%{query}%"),NetpayServiceCase.original_description.ilike(f"%{query}%")))
 total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0; items=db.scalars(stmt.order_by(NetpayServiceCase.priority,NetpayServiceCase.created_at,NetpayServiceCase.id).offset(offset).limit(limit)).all(); return InboxPage(items=[_case_read(db,x) for x in items],offset=offset,limit=limit,total=total)
@router.get("/cases/{case_id}",response_model=CaseRead)
def detail(case_id:UUID,db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 e=_viewer(envelope); item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==case_id,NetpayServiceCase.organization_id==e.organization_id))
 if not item: raise HTTPException(404,"not found")
 return _case_read(db,item)

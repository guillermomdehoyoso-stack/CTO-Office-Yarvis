"""Tenant-owned Netpay Inbox core. B2 operations intentionally have no route."""
from hashlib import sha256
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import and_, case as sql_case, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_inbox_authority import netpay_inbox_envelope
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.netpay_inbox import NetpayCaseActivity, NetpayCaseChecklistItem, NetpayCaseDocumentReference, NetpayCaseNextAction, NetpayCaseStep, NetpayCaseType, NetpayChecklistTemplate, NetpayInboxCommandReceipt, NetpayServiceCase
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.principal import PrincipalMembership
from yarvis_api.schemas.netpay_inbox import ActivityWrite, AssignmentUpdate, CaseClassify, CaseCreate, CaseRead, ChecklistUpdate, InboxPage, NextActionUpdate, StateTransition

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
    open_actions=[action for action in actions if action.status=="open"]
    now=datetime.now(timezone.utc)
    overdue=any(action.due_date is not None and action.due_date < now for action in open_actions)
    terminal=item.state in {"completed","cancelled"}
    requires_attention=not terminal and (item.responsible_principal_id is None or not open_actions or overdue or item.state in {"information_pending","blocked"})
    return CaseRead.model_validate(item).model_copy(update={"requires_attention":requires_attention,"checklist":[{"id":str(x.id),"requirement_key":x.requirement_key,"status":x.status,"required":x.required,"safe_evidence_reference":x.safe_evidence_reference,"template_version":x.template_version} for x in db.scalars(select(NetpayCaseChecklistItem).where(NetpayCaseChecklistItem.case_id==item.id).order_by(NetpayCaseChecklistItem.created_at,NetpayCaseChecklistItem.id)).all()],"steps":[{"id":str(x.id),"ordinal":x.ordinal,"description":x.description,"status":x.status} for x in db.scalars(select(NetpayCaseStep).where(NetpayCaseStep.case_id==item.id).order_by(NetpayCaseStep.ordinal)).all()],"next_actions":[{"id":str(x.id),"description":x.description,"status":x.status,"responsible_principal_id":str(x.responsible_principal_id) if x.responsible_principal_id else None,"due_date":x.due_date.isoformat() if x.due_date else None,"origin":x.origin} for x in actions],"activities":[{"id":str(x.id),"type":x.activity_type,"summary":x.safe_summary,"created_at":x.created_at.isoformat()} for x in db.scalars(select(NetpayCaseActivity).where(NetpayCaseActivity.case_id==item.id).order_by(NetpayCaseActivity.created_at, NetpayCaseActivity.id)).all()],"document_references":[{"id":str(x.id),"status":x.status,"external_evidence_reference":x.external_evidence_reference} for x in db.scalars(select(NetpayCaseDocumentReference).where(NetpayCaseDocumentReference.case_id==item.id)).all()]})
def _execute(db,e,key,command,payload,mutation,target=None):
    current=_operator(e); key=key.strip(); fingerprint=_fp(command,target,payload)
    receipt=db.scalar(select(NetpayInboxCommandReceipt).where(NetpayInboxCommandReceipt.organization_id==current.organization_id,NetpayInboxCommandReceipt.command_type==command,NetpayInboxCommandReceipt.idempotency_key==key))
    if receipt:
        if receipt.request_fingerprint!=fingerprint: raise HTTPException(409,"idempotency conflict")
        return receipt.result_resource_id,receipt.result_status_code,receipt.result_response_body
    try: correlation=UUID(current.correlation_id)
    except ValueError: correlation=uuid4()
    resource,status_code=mutation(current,correlation)
    db.flush()
    case=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==resource,NetpayServiceCase.organization_id==current.organization_id))
    if case is None: raise HTTPException(404,"not found")
    response_body=_case_read(db,case).model_dump(mode="json")
    db.add(NetpayInboxCommandReceipt(organization_id=current.organization_id,command_type=command,idempotency_key=key,request_fingerprint=fingerprint,actor_principal_id=current.principal_id,correlation_id=correlation,result_resource_id=resource,result_status_code=status_code,result_response_body=response_body)); db.flush(); return resource,status_code,response_body
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
 try: rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-009",payload.model_dump(mode="python"),mutate); db.commit()
 except IntegrityError as x: db.rollback(); raise HTTPException(409,"conflict") from x
 response.status_code=code; return body
@router.put("/cases/{case_id}/classification",response_model=CaseRead)
def classify_case(case_id:UUID,payload:CaseClassify,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==case_id,NetpayServiceCase.organization_id==e.organization_id)); typ=db.scalar(select(NetpayCaseType).where(NetpayCaseType.organization_id==e.organization_id,NetpayCaseType.semantic_key==payload.case_type_key,NetpayCaseType.active.is_(True)))
  if not item or not typ: raise HTTPException(404,"not found")
  if item.state in {"completed","cancelled"}: raise HTTPException(409,"terminal case")
  item.case_type_key,item.product,item.expected_outcome,item.priority,item.updated_by_principal_id=payload.case_type_key,payload.product,payload.expected_outcome,payload.priority,e.principal_id
  template=db.scalar(select(NetpayChecklistTemplate).where(NetpayChecklistTemplate.organization_id==e.organization_id,NetpayChecklistTemplate.case_type_key==payload.case_type_key,NetpayChecklistTemplate.active.is_(True)).order_by(NetpayChecklistTemplate.version.desc()))
  if template: item.checklist_template_version=template.version; [db.add(NetpayCaseChecklistItem(organization_id=e.organization_id,case_id=item.id,template_version=template.version,requirement_key=r["key"],required=r.get("required",True),created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id)) for r in template.requirements]
  if payload.case_type_key=="franchisee_change" and not db.scalar(select(NetpayCaseStep.id).where(NetpayCaseStep.case_id==item.id)):
   for ordinal,description in enumerate(("Validate new franchisee","Collect evidence","Process former Store deactivation","Create or link Company and Branch","Request new Store","Confirm activation","Close integrated outcome"),start=1): db.add(NetpayCaseStep(organization_id=e.organization_id,case_id=item.id,ordinal=ordinal,description=description,status="pending",created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id))
  record_event(db,event_type="netpay_service_case.classified",aggregate_type="netpay_service_case",aggregate_id=item.id,organization_id=e.organization_id,correlation_id=c,causation_id=c,payload={"case_id":str(item.id),"case_type_key":item.case_type_key,"actor_principal_id":str(e.principal_id)}); return item.id,200
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-010",payload.model_dump(mode="python"),mutate,case_id); db.commit(); response.status_code=code; return body
@router.get("",response_model=InboxPage)
def list_inbox(query:str|None=None,state:str|None=None,product:str|None=None,case_type_key:str|None=None,responsible_principal_id:UUID|None=None,requires_attention:bool|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 e=_viewer(envelope); stmt=select(NetpayServiceCase).where(NetpayServiceCase.organization_id==e.organization_id)
 if state: stmt=stmt.where(NetpayServiceCase.state==state)
 if product: stmt=stmt.where(NetpayServiceCase.product==product)
 if case_type_key: stmt=stmt.where(NetpayServiceCase.case_type_key==case_type_key)
 if responsible_principal_id: stmt=stmt.where(NetpayServiceCase.responsible_principal_id==responsible_principal_id)
 if query:
  value=f"%{query.strip()}%"; stmt=stmt.where(or_(NetpayServiceCase.folio.ilike(value),NetpayServiceCase.original_description.ilike(value),NetpayServiceCase.client_id.in_(select(NetpayClient.id).where(NetpayClient.organization_id==e.organization_id,NetpayClient.display_name.ilike(value))),NetpayServiceCase.company_id.in_(select(NetpayCompany.id).where(NetpayCompany.organization_id==e.organization_id,NetpayCompany.legal_name.ilike(value))),NetpayServiceCase.branch_id.in_(select(NetpayBranch.id).where(NetpayBranch.organization_id==e.organization_id,NetpayBranch.commercial_name.ilike(value))),NetpayServiceCase.store_reference_id.in_(select(NetpayStoreReference.id).where(NetpayStoreReference.organization_id==e.organization_id,NetpayStoreReference.store_id.ilike(value)))))
 open_action=exists(select(NetpayCaseNextAction.id).where(NetpayCaseNextAction.case_id==NetpayServiceCase.id,NetpayCaseNextAction.status=="open"))
 overdue_action=exists(select(NetpayCaseNextAction.id).where(NetpayCaseNextAction.case_id==NetpayServiceCase.id,NetpayCaseNextAction.status=="open",NetpayCaseNextAction.due_date<datetime.now(timezone.utc)))
 attention=and_(~NetpayServiceCase.state.in_(("completed","cancelled")),or_(NetpayServiceCase.responsible_principal_id.is_(None),~open_action,overdue_action,NetpayServiceCase.state.in_(("information_pending","blocked"))))
 if requires_attention is not None: stmt=stmt.where(attention if requires_attention else ~attention)
 total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0; priority_order=sql_case((NetpayServiceCase.priority=="urgent",0),(NetpayServiceCase.priority=="high",1),(NetpayServiceCase.priority=="normal",2),else_=3); attention_order=sql_case((attention,0),else_=1); overdue_order=sql_case((overdue_action,0),else_=1); items=db.scalars(stmt.order_by(attention_order,overdue_order,priority_order,NetpayServiceCase.target_date.asc().nulls_last(),NetpayServiceCase.created_at,NetpayServiceCase.id).offset(offset).limit(limit)).all(); return InboxPage(items=[_case_read(db,x) for x in items],offset=offset,limit=limit,total=total)
@router.get("/cases/{case_id}",response_model=CaseRead)
def detail(case_id:UUID,db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 e=_viewer(envelope); item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==case_id,NetpayServiceCase.organization_id==e.organization_id))
 if not item: raise HTTPException(404,"not found")
 return _case_read(db,item)

def _target(db,e,case_id):
 item=db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.id==case_id,NetpayServiceCase.organization_id==e.organization_id))
 if not item: raise HTTPException(404,"not found")
 if item.state in {"completed","cancelled"}: raise HTTPException(409,"terminal case")
 return item
def _active_member(db,e,principal_id):
 if principal_id is None: return
 membership=db.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id==principal_id,PrincipalMembership.organization_id==e.organization_id,PrincipalMembership.status=="active"))
 if membership is None: raise HTTPException(404,"not found")
def _activity(db,e,item,c,kind,summary):
 db.add(NetpayCaseActivity(organization_id=e.organization_id,case_id=item.id,activity_type=kind,safe_summary=summary,correlation_id=c,causation_id=c,created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id))
 record_event(db,event_type="netpay_service_case.activity_recorded",aggregate_type="netpay_service_case",aggregate_id=item.id,organization_id=e.organization_id,correlation_id=c,causation_id=c,payload={"case_id":str(item.id),"activity_type":kind,"actor_principal_id":str(e.principal_id)})
@router.put("/cases/{case_id}/checklist/{item_id}",response_model=CaseRead)
def update_checklist(case_id:UUID,item_id:UUID,payload:ChecklistUpdate,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=_target(db,e,case_id); row=db.scalar(select(NetpayCaseChecklistItem).where(NetpayCaseChecklistItem.id==item_id,NetpayCaseChecklistItem.case_id==item.id,NetpayCaseChecklistItem.organization_id==e.organization_id))
  if not row: raise HTTPException(404,"not found")
  row.status,row.safe_evidence_reference,row.updated_by_principal_id=payload.status,payload.safe_evidence_reference,e.principal_id; summary=row.requirement_key if not payload.comment else f"{row.requirement_key}: {payload.comment}"; _activity(db,e,item,c,"checklist_updated",summary); return item.id,200
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-011",payload.model_dump(),mutate,case_id); db.commit(); response.status_code=code; return body
@router.put("/cases/{case_id}/assignment",response_model=CaseRead)
def assign(case_id:UUID,payload:AssignmentUpdate,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=_target(db,e,case_id); _active_member(db,e,payload.responsible_principal_id); item.responsible_principal_id=payload.responsible_principal_id; item.updated_by_principal_id=e.principal_id; _activity(db,e,item,c,"assignment",str(payload.responsible_principal_id)); return item.id,200
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-012",payload.model_dump(),mutate,case_id); db.commit(); response.status_code=code; return body
@router.put("/cases/{case_id}/next-action",response_model=CaseRead)
def next_action(case_id:UUID,payload:NextActionUpdate,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=_target(db,e,case_id); _active_member(db,e,payload.responsible_principal_id); current=db.scalar(select(NetpayCaseNextAction).where(NetpayCaseNextAction.case_id==item.id,NetpayCaseNextAction.status=="open"))
  if payload.status=="open":
   if not payload.description: raise HTTPException(422,"description required")
   if current: current.status="cancelled"; current.updated_by_principal_id=e.principal_id
   db.add(NetpayCaseNextAction(organization_id=e.organization_id,case_id=item.id,description=payload.description,responsible_principal_id=payload.responsible_principal_id,due_date=payload.due_date,status="open",origin=payload.origin,provenance={},created_by_principal_id=e.principal_id,updated_by_principal_id=e.principal_id))
  else:
   if not current: raise HTTPException(409,"no open next action")
   current.status=payload.status; current.updated_by_principal_id=e.principal_id
  _activity(db,e,item,c,"next_action",payload.status); return item.id,200
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-013",payload.model_dump(),mutate,case_id); db.commit(); response.status_code=code; return body
_TRANSITIONS={"received":{"triage","cancelled"},"triage":{"information_pending","ready","blocked","cancelled"},"information_pending":{"triage","ready","blocked","cancelled"},"ready":{"in_progress","information_pending","blocked","cancelled"},"in_progress":{"submitted","information_pending","blocked","completed","cancelled"},"submitted":{"in_progress","information_pending","blocked","completed","cancelled"},"blocked":{"triage","ready","in_progress","cancelled"}}
@router.put("/cases/{case_id}/state",response_model=CaseRead)
def transition(case_id:UUID,payload:StateTransition,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=_target(db,e,case_id)
  if payload.state not in _TRANSITIONS.get(item.state,set()) or payload.state=="cancelled" and not payload.reason: raise HTTPException(409,"invalid transition")
  if payload.state in {"cancelled","completed"} and not payload.reason: raise HTTPException(409,"reason required")
  if payload.state=="completed" and (not item.expected_outcome or any(x.required and x.status not in {"confirmed","not_applicable"} for x in db.scalars(select(NetpayCaseChecklistItem).where(NetpayCaseChecklistItem.case_id==item.id)).all()) or any(x.status!="completed" for x in db.scalars(select(NetpayCaseStep).where(NetpayCaseStep.case_id==item.id)).all())): raise HTTPException(409,"completion conditions not met")
  item.state,item.updated_by_principal_id=payload.state,e.principal_id; summary=payload.state if not payload.reason else f"{payload.state}: {payload.reason}"; _activity(db,e,item,c,"state_changed",summary); record_event(db,event_type="netpay_service_case.state_changed",aggregate_type="netpay_service_case",aggregate_id=item.id,organization_id=e.organization_id,correlation_id=c,causation_id=c,payload={"case_id":str(item.id),"state":payload.state,"actor_principal_id":str(e.principal_id)}); return item.id,200
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-014",payload.model_dump(),mutate,case_id); db.commit(); response.status_code=code; return body
@router.post("/cases/{case_id}/activities",response_model=CaseRead)
def add_activity(case_id:UUID,payload:ActivityWrite,response:Response,idempotency_key:str=Header(...,alias="Idempotency-Key"),db:Session=Depends(get_db),envelope:IdentityAuthorityEnvelope=Depends(authority_envelope)):
 def mutate(e,c):
  item=_target(db,e,case_id); summary=payload.safe_summary if not payload.external_reference else f"{payload.safe_summary} [ref:{payload.external_reference}]"; _activity(db,e,item,c,payload.activity_type,summary); return item.id,201
 rid,code,body=_execute(db,envelope,idempotency_key,"IC-NETPAY-CMD-015",payload.model_dump(),mutate,case_id); db.commit(); response.status_code=code; return body

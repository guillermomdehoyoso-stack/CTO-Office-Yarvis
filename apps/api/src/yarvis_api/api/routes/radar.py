"""Manual, synchronous Netpay operational radar API."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.radar import RadarActivity, RadarChecklistItem, RadarMerchant, RadarRequest
from yarvis_api.schemas.radar import (
    ActivityRead, ChecklistRead, ChecklistUpdate, CloseRequest, DashboardRead, MerchantCreate,
    MerchantDetail, MerchantRead, NextActionUpdate, NoteCreate, ReopenRequest, RequestCreate, RequestRead,
)

router = APIRouter(prefix="/radar", tags=["radar operativo netpay"])
DEFAULT_TIMEZONE = "America/Mexico_City"

TPV_TEMPLATE = [
    ("ine_apoderado", "INE de persona física o apoderado"),
    ("acta_constitutiva", "Acta constitutiva cuando corresponda"),
    ("estado_cuenta", "Estado de cuenta bancario"),
    ("domicilio_comercial", "Comprobante de domicilio comercial"),
    ("constancia_fiscal", "Constancia de situación fiscal"),
    ("fotos_establecimiento", "Cuatro fotos del establecimiento"),
]
ECOMMERCE_TEMPLATE = TPV_TEMPLATE + [("dominio", "Comprobante de propiedad o control del dominio")]


def workspace_id(value: str = Header(..., alias="X-Yarvis-Workspace", min_length=1, max_length=100)) -> str:
    return value.strip()


def now() -> datetime:
    return datetime.now(timezone.utc)


def activity(db: Session, merchant: RadarMerchant, request: RadarRequest | None, event_type: str, summary: str, actor: str) -> None:
    db.add(RadarActivity(workspace_id=merchant.workspace_id, merchant_id=merchant.id, request_id=request.id if request else None, event_type=event_type, summary=summary, actor=actor))


def scoped_merchant(db: Session, merchant_id: UUID, workspace: str) -> RadarMerchant:
    merchant = db.scalar(select(RadarMerchant).where(RadarMerchant.id == merchant_id, RadarMerchant.workspace_id == workspace))
    if merchant is None:
        raise HTTPException(status_code=404, detail="not found")
    return merchant


def scoped_request(db: Session, request_id: UUID, workspace: str) -> tuple[RadarRequest, RadarMerchant]:
    request = db.scalar(select(RadarRequest).where(RadarRequest.id == request_id, RadarRequest.workspace_id == workspace))
    if request is None:
        raise HTTPException(status_code=404, detail="not found")
    return request, scoped_merchant(db, request.merchant_id, workspace)


def template_for(classification: str) -> list[tuple[str, str]]:
    if classification == "alta_tpv":
        return TPV_TEMPLATE
    if classification == "alta_ecommerce":
        return ECOMMERCE_TEMPLATE
    return []


def request_read(db: Session, request: RadarRequest) -> RequestRead:
    checklist = db.scalars(select(RadarChecklistItem).where(RadarChecklistItem.request_id == request.id).order_by(RadarChecklistItem.position, RadarChecklistItem.id)).all()
    return RequestRead.model_validate(request, from_attributes=True).model_copy(update={"checklist": [ChecklistRead.model_validate(item) for item in checklist]})


def merchant_read(db: Session, merchant: RadarMerchant) -> MerchantRead:
    requests = db.scalars(select(RadarRequest).where(RadarRequest.merchant_id == merchant.id, RadarRequest.workspace_id == merchant.workspace_id).order_by(RadarRequest.created_at, RadarRequest.id)).all()
    opens = [item for item in requests if item.status == "open"]
    open_ids = [item.id for item in opens]
    items = db.scalars(select(RadarChecklistItem).where(RadarChecklistItem.request_id.in_(open_ids)).order_by(RadarChecklistItem.position, RadarChecklistItem.id)).all() if open_ids else []
    missing = [item.label for item in items if item.required and not item.received]
    ordered_open = sorted(opens, key=lambda item: (item.due_at is None, item.due_at or datetime.max.replace(tzinfo=timezone.utc), {"high": 0, "normal": 1, "low": 2}[item.priority], item.created_at, str(item.id)))
    lead = ordered_open[0] if ordered_open else None
    age_days = (now() - lead.created_at).days if lead else None
    return MerchantRead(
        id=merchant.id, trade_name=merchant.trade_name, legal_name=merchant.legal_name, store_id=merchant.store_id,
        contact_name=merchant.contact_name, email=merchant.email, phone=merchant.phone, products=merchant.products,
        pending=bool(opens), open_count=len(opens), next_action=lead.next_action if lead else None, due_at=lead.due_at if lead else None,
        age_days=age_days, priority=lead.priority if lead else None, missing_documents=missing, owner=lead.owner if lead else None,
    )


@router.post("/merchants", response_model=MerchantRead, status_code=status.HTTP_201_CREATED)
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    merchant = RadarMerchant(workspace_id=workspace, **payload.model_dump(exclude={"actor"}))
    db.add(merchant)
    db.flush()
    activity(db, merchant, None, "merchant_created", "Comercio registrado", payload.actor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="store id already exists in workspace")
    return merchant_read(db, merchant)


@router.post("/requests", response_model=RequestRead, status_code=status.HTTP_201_CREATED)
def create_request(payload: RequestCreate, response: Response, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=255), db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    if idempotency_key:
        existing = db.scalar(select(RadarRequest).where(RadarRequest.workspace_id == workspace, RadarRequest.idempotency_key == idempotency_key))
        if existing:
            response.status_code = status.HTTP_200_OK
            return request_read(db, existing)
    merchant = scoped_merchant(db, payload.merchant_id, workspace) if payload.merchant_id else RadarMerchant(workspace_id=workspace, **payload.merchant.model_dump())
    if payload.merchant:
        db.add(merchant)
        db.flush()
        activity(db, merchant, None, "merchant_created", "Comercio registrado al crear solicitud", payload.actor)
    request = RadarRequest(workspace_id=workspace, merchant_id=merchant.id, free_text=payload.free_text, classification=payload.classification, priority=payload.priority, owner=payload.owner, next_action=payload.next_action, due_at=payload.due_at, idempotency_key=idempotency_key)
    db.add(request)
    db.flush()
    for position, (code, label) in enumerate(template_for(payload.classification), 1):
        db.add(RadarChecklistItem(request_id=request.id, item_code=code, label=label, position=position))
    activity(db, merchant, request, "request_created", "Solicitud creada y clasificada como " + payload.classification, payload.actor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing = db.scalar(select(RadarRequest).where(RadarRequest.workspace_id == workspace, RadarRequest.idempotency_key == idempotency_key))
            if existing:
                response.status_code = status.HTTP_200_OK
                return request_read(db, existing)
        raise
    return request_read(db, request)


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(pending: bool | None = None, overdue: bool | None = None, product: str | None = Query(default=None, pattern="^(tpv|ecommerce)$"), merchant: str | None = None, priority: str | None = Query(default=None, pattern="^(low|normal|high)$"), db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    records = db.scalars(select(RadarMerchant).where(RadarMerchant.workspace_id == workspace).order_by(RadarMerchant.trade_name, RadarMerchant.id)).all()
    values = [merchant_read(db, item) for item in records]
    current = now()
    def accepted(item: MerchantRead) -> bool:
        return (pending is None or item.pending == pending) and (overdue is None or bool(item.due_at and item.due_at < current) == overdue) and (product is None or product in item.products) and (merchant is None or merchant.lower() in item.trade_name.lower()) and (priority is None or item.priority == priority)
    values = [item for item in values if accepted(item)]
    values.sort(key=lambda item: (not bool(item.due_at and item.due_at < current), {"high": 0, "normal": 1, "low": 2, None: 3}[item.priority], item.due_at is None, item.due_at or datetime.max.replace(tzinfo=timezone.utc), -(item.age_days or -1), item.trade_name.lower(), str(item.id)))
    all_values = [merchant_read(db, item) for item in records]
    return DashboardRead(timezone=DEFAULT_TIMEZONE, summary={"pending": sum(x.pending for x in all_values), "overdue": sum(bool(x.due_at and x.due_at < current) for x in all_values), "tpv": sum("tpv" in x.products and x.pending for x in all_values), "ecommerce": sum("ecommerce" in x.products and x.pending for x in all_values)}, merchants=values)


@router.get("/merchants/{merchant_id}", response_model=MerchantDetail)
def merchant_detail(merchant_id: UUID, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    item = scoped_merchant(db, merchant_id, workspace)
    read = merchant_read(db, item)
    requests = db.scalars(select(RadarRequest).where(RadarRequest.merchant_id == item.id).order_by(RadarRequest.created_at.desc(), RadarRequest.id)).all()
    events = db.scalars(select(RadarActivity).where(RadarActivity.merchant_id == item.id, RadarActivity.workspace_id == workspace).order_by(RadarActivity.occurred_at.desc(), RadarActivity.id.desc())).all()
    return MerchantDetail(**read.model_dump(), requests=[request_read(db, request) for request in requests], activity=[ActivityRead.model_validate(event) for event in events])


@router.patch("/requests/{request_id}/checklist/{item_id}", response_model=RequestRead)
def update_checklist(request_id: UUID, item_id: UUID, payload: ChecklistUpdate, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    request, merchant = scoped_request(db, request_id, workspace)
    item = db.scalar(select(RadarChecklistItem).where(RadarChecklistItem.id == item_id, RadarChecklistItem.request_id == request.id))
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    item.received = payload.received
    item.received_by = payload.actor if payload.received else None
    item.received_at = now() if payload.received else None
    activity(db, merchant, request, "document_received" if payload.received else "checklist_changed", ("Documento recibido: " if payload.received else "Checklist pendiente: ") + item.label, payload.actor)
    db.commit()
    return request_read(db, request)


@router.patch("/requests/{request_id}/next-action", response_model=RequestRead)
def update_next_action(request_id: UUID, payload: NextActionUpdate, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    request, merchant = scoped_request(db, request_id, workspace)
    if "next_action" in payload.model_fields_set:
        request.next_action = payload.next_action.strip() or None if payload.next_action else None
    if "due_at" in payload.model_fields_set:
        request.due_at = payload.due_at
    if "priority" in payload.model_fields_set:
        request.priority = payload.priority
    if "owner" in payload.model_fields_set:
        request.owner = payload.owner
    activity(db, merchant, request, "next_action_changed", "Siguiente acción actualizada", payload.actor)
    db.commit()
    return request_read(db, request)


@router.post("/requests/{request_id}/notes", response_model=RequestRead)
def add_note(request_id: UUID, payload: NoteCreate, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    request, merchant = scoped_request(db, request_id, workspace)
    activity(db, merchant, request, "note_added", payload.note, payload.actor)
    db.commit()
    return request_read(db, request)


@router.post("/requests/{request_id}/close", response_model=RequestRead)
def close_request(request_id: UUID, payload: CloseRequest, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    request, merchant = scoped_request(db, request_id, workspace)
    if request.status == "closed": return request_read(db, request)
    if "next_action" in payload.model_fields_set:
        request.next_action = payload.next_action.strip() or None if payload.next_action else None
    missing = db.scalars(select(RadarChecklistItem).where(RadarChecklistItem.request_id == request.id, RadarChecklistItem.required.is_(True), RadarChecklistItem.received.is_(False))).all()
    if (request.next_action and request.next_action.strip()) or missing:
        if not payload.incomplete_justification or not payload.incomplete_justification.strip():
            raise HTTPException(status_code=422, detail="next action and required checklist must be resolved or justified")
    request.status, request.closed_at, request.close_reason = "closed", now(), payload.incomplete_justification
    activity(db, merchant, request, "request_closed", "Solicitud cerrada" + (" con justificación" if payload.incomplete_justification else ""), payload.actor)
    db.commit()
    return request_read(db, request)


@router.post("/requests/{request_id}/reopen", response_model=RequestRead)
def reopen_request(request_id: UUID, payload: ReopenRequest, db: Session = Depends(get_db), workspace: str = Depends(workspace_id)):
    request, merchant = scoped_request(db, request_id, workspace)
    request.status, request.closed_at, request.close_reason = "open", None, None
    activity(db, merchant, request, "request_reopened", "Solicitud reabierta", payload.actor)
    db.commit()
    return request_read(db, request)

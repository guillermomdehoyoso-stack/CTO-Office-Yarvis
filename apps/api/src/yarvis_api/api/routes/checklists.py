from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.clock import utc_now
from yarvis_api.models.case import Case
from yarvis_api.models.checklist import CaseChecklist, CaseType, ChecklistRequirement, ChecklistTemplate, DocumentType, IntakeClassification, RequirementFulfillment
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.evidence import Evidence
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.operational import NextActionSuggestion, OperationalAlert
from yarvis_api.schemas.checklist import CaseChecklistRead, CatalogRead, ClassificationCreate, ClassificationRead, ConfirmationInput, DocumentTypeRead, FulfillmentInput, FulfillmentRead, NotesInput, RequirementRead, ReviewInput

router = APIRouter(tags=["classifications", "checklists"])


def event(db, event_type, aggregate_type, aggregate_id, case, payload):
    record_event(db, event_type=event_type, aggregate_type=aggregate_type, aggregate_id=aggregate_id, organization_id=case.owner_organization_id if case else None, case_id=case.id if case else None, payload=payload)


def checklist_read(db: Session, checklist: CaseChecklist) -> dict:
    requirements = db.scalars(select(ChecklistRequirement).where(ChecklistRequirement.checklist_template_id == checklist.checklist_template_id).order_by(ChecklistRequirement.display_order)).all()
    fulfillments = db.scalars(select(RequirementFulfillment).where(RequirementFulfillment.case_checklist_id == checklist.id)).all()
    by_requirement = {}
    for fulfillment in fulfillments:
        by_requirement.setdefault(fulfillment.checklist_requirement_id, []).append(fulfillment.status)
    required = [requirement for requirement in requirements if requirement.required]
    complete = sum(any(item in {"valid", "not_applicable"} for item in by_requirement.get(requirement.id, [])) for requirement in required)
    return {"id": checklist.id, "case_id": checklist.case_id, "checklist_template_id": checklist.checklist_template_id, "template_version": checklist.template_version, "created_at": checklist.created_at, "required_total": len(required), "required_complete": complete, "progress_percent": 100.0 if not required else round(100 * complete / len(required), 2), "requirements": [{"id": item.id, "code": item.code, "name": item.name, "required": item.required, "multiple_allowed": item.multiple_allowed, "display_order": item.display_order, "document_type_id": item.document_type_id, "fulfillment_statuses": by_requirement.get(item.id, [])} for item in requirements]}


@router.get("/case-types", response_model=list[CatalogRead])
def case_types(db: Session = Depends(get_db)):
    return db.scalars(select(CaseType).where(CaseType.active).order_by(CaseType.code)).all()


@router.get("/document-types", response_model=list[DocumentTypeRead])
def document_types(db: Session = Depends(get_db)):
    return db.scalars(select(DocumentType).where(DocumentType.active).order_by(DocumentType.code)).all()


@router.post("/intake/{intake_id}/classifications", response_model=ClassificationRead, status_code=status.HTTP_201_CREATED)
def create_classification(intake_id: UUID, payload: ClassificationCreate, db: Session = Depends(get_db)):
    intake = db.get(IntakeItem, intake_id)
    if intake is None:
        raise HTTPException(404, "IntakeItem not found")
    if payload.document_type_id and db.get(DocumentType, payload.document_type_id) is None:
        raise HTTPException(404, "DocumentType not found")
    if payload.proposed_case_type_id and db.get(CaseType, payload.proposed_case_type_id) is None:
        raise HTTPException(404, "CaseType not found")
    item = IntakeClassification(intake_item_id=intake_id, **payload.model_dump())
    db.add(item); db.flush()
    case = db.get(Case, intake.case_id) if intake.case_id else None
    event(db, "intake.classification_proposed", "intake_classification", item.id, case, {"intake_id": str(intake_id)})
    db.commit(); db.refresh(item)
    return item


@router.get("/intake/{intake_id}/classifications", response_model=list[ClassificationRead])
def classifications(intake_id: UUID, db: Session = Depends(get_db)):
    if db.get(IntakeItem, intake_id) is None:
        raise HTTPException(404, "IntakeItem not found")
    return db.scalars(select(IntakeClassification).where(IntakeClassification.intake_item_id == intake_id).order_by(IntakeClassification.created_at)).all()


def decide_classification(classification_id: UUID, approved: bool, payload: ConfirmationInput, db: Session):
    item = db.get(IntakeClassification, classification_id)
    if item is None:
        raise HTTPException(404, "IntakeClassification not found")
    if item.status != "proposed":
        raise HTTPException(409, "Classification has already been decided")
    item.status = "confirmed" if approved else "rejected"; item.confirmed_by = payload.confirmed_by; item.confirmed_at = utc_now()
    intake = db.get(IntakeItem, item.intake_item_id); case = db.get(Case, intake.case_id) if intake.case_id else None
    event(db, "intake.classification_confirmed" if approved else "intake.classification_rejected", "intake_classification", item.id, case, {"intake_id": str(intake.id)})
    db.commit(); db.refresh(item)
    return item


@router.post("/intake-classifications/{classification_id}/confirm", response_model=ClassificationRead)
def confirm_classification(classification_id: UUID, payload: ConfirmationInput = ConfirmationInput(), db: Session = Depends(get_db)):
    return decide_classification(classification_id, True, payload, db)


@router.post("/intake-classifications/{classification_id}/reject", response_model=ClassificationRead)
def reject_classification(classification_id: UUID, payload: ConfirmationInput = ConfirmationInput(), db: Session = Depends(get_db)):
    return decide_classification(classification_id, False, payload, db)


@router.post("/cases/{case_id}/checklists", response_model=CaseChecklistRead, status_code=status.HTTP_201_CREATED)
def create_checklist(case_id: UUID, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if case is None or case.case_type_id is None:
        raise HTTPException(404, "Case with configured CaseType not found")
    template = db.scalar(select(ChecklistTemplate).where(ChecklistTemplate.case_type_id == case.case_type_id, ChecklistTemplate.active).order_by(ChecklistTemplate.version.desc()))
    if template is None:
        raise HTTPException(422, "No active checklist template for CaseType")
    item = CaseChecklist(case_id=case_id, checklist_template_id=template.id, template_version=template.version)
    db.add(item)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Checklist template and version already exist for this Case") from exc
    event(db, "checklist.created", "case_checklist", item.id, case, {"template_version": item.template_version})
    db.commit(); db.refresh(item)
    return checklist_read(db, item)


@router.get("/cases/{case_id}/checklists", response_model=list[CaseChecklistRead])
def case_checklists(case_id: UUID, db: Session = Depends(get_db)):
    if db.get(Case, case_id) is None: raise HTTPException(404, "Case not found")
    return [checklist_read(db, item) for item in db.scalars(select(CaseChecklist).where(CaseChecklist.case_id == case_id)).all()]


@router.get("/case-checklists/{case_checklist_id}", response_model=CaseChecklistRead)
def get_checklist(case_checklist_id: UUID, db: Session = Depends(get_db)):
    item = db.get(CaseChecklist, case_checklist_id)
    if item is None: raise HTTPException(404, "CaseChecklist not found")
    return checklist_read(db, item)


def requirement_for(db, checklist_id, requirement_id):
    checklist = db.get(CaseChecklist, checklist_id)
    requirement = db.get(ChecklistRequirement, requirement_id)
    if checklist is None or requirement is None or requirement.checklist_template_id != checklist.checklist_template_id: raise HTTPException(404, "Checklist requirement not found")
    return checklist, requirement, db.get(Case, checklist.case_id)


@router.post("/case-checklists/{checklist_id}/requirements/{requirement_id}/fulfill", response_model=FulfillmentRead, status_code=status.HTTP_201_CREATED)
def fulfill(checklist_id: UUID, requirement_id: UUID, payload: FulfillmentInput, db: Session = Depends(get_db)):
    checklist, requirement, case = requirement_for(db, checklist_id, requirement_id)
    if payload.intake_item_id and db.get(IntakeItem, payload.intake_item_id) is None: raise HTTPException(404, "IntakeItem not found")
    evidence = db.get(Evidence, payload.evidence_id) if payload.evidence_id else None
    if payload.evidence_id and evidence is None: raise HTTPException(404, "Evidence not found")
    if evidence and evidence.case_id != case.id: raise HTTPException(422, "Evidence belongs to another Case")
    item = RequirementFulfillment(case_checklist_id=checklist.id, checklist_requirement_id=requirement.id, status="received", **payload.model_dump())
    db.add(item); db.flush(); event(db, "checklist.requirement_received", "requirement_fulfillment", item.id, case, {"requirement_code": requirement.code}); db.commit(); db.refresh(item)
    return item


def decide_fulfillment(fulfillment_id, approved, payload, db):
    item = db.get(RequirementFulfillment, fulfillment_id)
    if item is None: raise HTTPException(404, "RequirementFulfillment not found")
    checklist = db.get(CaseChecklist, item.case_checklist_id); case = db.get(Case, checklist.case_id)
    if not approved and not payload.rejection_reason: raise HTTPException(422, "rejection_reason is required")
    item.reviewed_by = payload.reviewed_by; item.reviewed_at = utc_now(); item.document_date = payload.document_date; item.valid_from = payload.valid_from
    item.status = "valid" if approved else "rejected"; item.validated_at = utc_now() if approved else None; item.rejection_reason = payload.rejection_reason
    requirement = db.get(ChecklistRequirement, item.checklist_requirement_id); document_type = db.get(DocumentType, requirement.document_type_id) if requirement.document_type_id else None
    if approved and document_type and document_type.validity_days:
        item.valid_until = (item.document_date or item.valid_from or item.created_at) + timedelta(days=document_type.validity_days)
    event(db, "fulfillment.validated" if approved else "fulfillment.rejected", "requirement_fulfillment", item.id, case, {})
    event(db, "checklist.requirement_validated" if approved else "checklist.requirement_rejected", "requirement_fulfillment", item.id, case, {})
    db.commit(); db.refresh(item); return item


@router.post("/requirement-fulfillments/{fulfillment_id}/validate", response_model=FulfillmentRead)
def validate(fulfillment_id: UUID, payload: ReviewInput = ReviewInput(), db: Session = Depends(get_db)): return decide_fulfillment(fulfillment_id, True, payload, db)

@router.get("/requirement-fulfillments/{fulfillment_id}", response_model=FulfillmentRead)
def get_fulfillment(fulfillment_id: UUID, db: Session = Depends(get_db)):
    item = db.get(RequirementFulfillment, fulfillment_id)
    if item is None: raise HTTPException(404, "RequirementFulfillment not found")
    return item


@router.post("/requirement-fulfillments/{fulfillment_id}/reject", response_model=FulfillmentRead)
def reject(fulfillment_id: UUID, payload: ReviewInput | None = None, db: Session = Depends(get_db)):
    # Preserve the previous no-body route contract; explicit review input requires a reason.
    return decide_fulfillment(fulfillment_id, False, payload or ReviewInput(rejection_reason="Rejected"), db)


@router.post("/requirement-fulfillments/{fulfillment_id}/review", response_model=FulfillmentRead)
def review(fulfillment_id: UUID, payload: ConfirmationInput = ConfirmationInput(), db: Session = Depends(get_db)):
    item = db.get(RequirementFulfillment, fulfillment_id)
    if item is None: raise HTTPException(404, "RequirementFulfillment not found")
    item.status = "under_review"; item.reviewed_by = payload.confirmed_by; item.reviewed_at = utc_now()
    checklist = db.get(CaseChecklist, item.case_checklist_id); case = db.get(Case, checklist.case_id)
    event(db, "fulfillment.reviewed", "requirement_fulfillment", item.id, case, {})
    db.commit(); db.refresh(item); return item


@router.post("/cases/{case_id}/evaluate-operational-state")
def evaluate(case_id: UUID, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if case is None: raise HTTPException(404, "Case not found")
    now = utc_now(); active = set()
    checklist = db.scalar(select(CaseChecklist).where(CaseChecklist.case_id == case_id))
    if checklist:
        requirements = db.scalars(select(ChecklistRequirement).where(ChecklistRequirement.checklist_template_id == checklist.checklist_template_id, ChecklistRequirement.required)).all()
        fulfillments = db.scalars(select(RequirementFulfillment).where(RequirementFulfillment.case_checklist_id == checklist.id)).all()
        for requirement in requirements:
            items = [x for x in fulfillments if x.checklist_requirement_id == requirement.id]
            status_value = items[-1].status if items else "missing"
            source = items[-1].id if items else requirement.id
            alert_type = None; action = None
            if status_value == "missing": alert_type, action = "missing_requirement", "request_missing_document"
            elif status_value in {"received", "under_review"}: alert_type, action = "review_required", "review_received_document"
            elif status_value == "rejected": alert_type, action = "rejected_requirement", "resolve_rejection"
            elif items and items[-1].valid_until:
                if items[-1].valid_until <= now: items[-1].status = "expired"; alert_type, action = "expired_requirement", "request_replacement_document"; event(db, "fulfillment.expired", "requirement_fulfillment", items[-1].id, case, {})
                elif items[-1].valid_until <= now + timedelta(days=30): alert_type, action = "expiring_requirement", "request_replacement_document"
            if alert_type:
                active.add((alert_type, "requirement", source))
                alert = db.scalar(select(OperationalAlert).where(OperationalAlert.case_id == case_id, OperationalAlert.alert_type == alert_type, OperationalAlert.source_entity_type == "requirement", OperationalAlert.source_entity_id == source))
                if alert is None:
                    alert = OperationalAlert(case_id=case_id, alert_type=alert_type, severity="critical" if "expired" in alert_type or "rejected" in alert_type else "warning", title=alert_type.replace("_", " "), description=f"{requirement.name}: {status_value}", source_entity_type="requirement", source_entity_id=source, due_at=items[-1].valid_until if items else None)
                    db.add(alert); db.flush(); event(db, "alert.created", "operational_alert", alert.id, case, {"alert_type": alert_type})
                if db.scalar(select(NextActionSuggestion).where(NextActionSuggestion.case_id == case_id, NextActionSuggestion.action_type == action, NextActionSuggestion.source_alert_id == alert.id)) is None:
                    suggestion = NextActionSuggestion(case_id=case_id, action_type=action, summary=alert.title, rationale=alert.description, source_alert_id=alert.id)
                    db.add(suggestion); db.flush(); event(db, "next_action.proposed", "next_action_suggestion", suggestion.id, case, {"action_type": action})
    for alert in db.scalars(select(OperationalAlert).where(OperationalAlert.case_id == case_id, OperationalAlert.status.in_(["open", "acknowledged"]))).all():
        if (alert.alert_type, alert.source_entity_type, alert.source_entity_id) not in active:
            alert.status = "resolved"; alert.resolved_at = now; alert.resolution_note = "Condition no longer applies"; event(db, "alert.resolved", "operational_alert", alert.id, case, {})
    db.commit()
    return {"case_id": str(case_id), "open_alerts": len(db.scalars(select(OperationalAlert).where(OperationalAlert.case_id == case_id, OperationalAlert.status != "resolved")).all())}


@router.get("/cases/{case_id}/alerts")
def alerts(case_id: UUID, db: Session = Depends(get_db)):
    return db.scalars(select(OperationalAlert).where(OperationalAlert.case_id == case_id).order_by(OperationalAlert.created_at)).all()


@router.get("/cases/{case_id}/next-action-suggestions")
def suggestions(case_id: UUID, db: Session = Depends(get_db)):
    return db.scalars(select(NextActionSuggestion).where(NextActionSuggestion.case_id == case_id).order_by(NextActionSuggestion.created_at)).all()


def suggestion_transition(suggestion_id: UUID, status_value: str, db: Session):
    item = db.get(NextActionSuggestion, suggestion_id)
    if item is None: raise HTTPException(404, "Suggestion not found")
    item.status = status_value; now = utc_now()
    if status_value == "dismissed": item.dismissed_at = now
    if status_value == "completed": item.completed_at = now
    case = db.get(Case, item.case_id); event(db, f"next_action.{status_value}", "next_action_suggestion", item.id, case, {})
    db.commit(); return item

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: UUID, db: Session = Depends(get_db)):
    item = db.get(OperationalAlert, alert_id)
    if item is None: raise HTTPException(404, "Alert not found")
    item.status = "acknowledged"; case = db.get(Case, item.case_id); event(db, "alert.acknowledged", "operational_alert", item.id, case, {}); db.commit(); return item
@router.post("/alerts/{alert_id}/resolve")
def resolve(alert_id: UUID, db: Session = Depends(get_db)):
    item = db.get(OperationalAlert, alert_id)
    if item is None: raise HTTPException(404, "Alert not found")
    item.status = "resolved"; item.resolved_at = utc_now(); case = db.get(Case, item.case_id); event(db, "alert.resolved", "operational_alert", item.id, case, {}); db.commit(); return item
@router.post("/next-action-suggestions/{suggestion_id}/accept")
def accept(suggestion_id: UUID, db: Session = Depends(get_db)):
    item = suggestion_transition(suggestion_id, "accepted", db)
    return {"id": str(item.id), "status": item.status}
@router.post("/next-action-suggestions/{suggestion_id}/dismiss")
def dismiss(suggestion_id: UUID, db: Session = Depends(get_db)):
    item = suggestion_transition(suggestion_id, "dismissed", db)
    return {"id": str(item.id), "status": item.status}
@router.post("/next-action-suggestions/{suggestion_id}/complete")
def complete(suggestion_id: UUID, db: Session = Depends(get_db)):
    item = suggestion_transition(suggestion_id, "completed", db)
    return {"id": str(item.id), "status": item.status}


@router.post("/case-checklists/{checklist_id}/requirements/{requirement_id}/not-applicable", response_model=FulfillmentRead, status_code=status.HTTP_201_CREATED)
def not_applicable(checklist_id: UUID, requirement_id: UUID, payload: NotesInput, db: Session = Depends(get_db)):
    checklist, requirement, case = requirement_for(db, checklist_id, requirement_id)
    item = RequirementFulfillment(case_checklist_id=checklist.id, checklist_requirement_id=requirement.id, status="not_applicable", notes=payload.notes)
    db.add(item); db.flush(); event(db, "checklist.requirement_not_applicable", "requirement_fulfillment", item.id, case, {"requirement_code": requirement.code}); db.commit(); db.refresh(item)
    return item

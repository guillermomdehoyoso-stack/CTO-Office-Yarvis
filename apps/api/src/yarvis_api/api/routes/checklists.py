from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.checklist import CaseChecklist, CaseType, ChecklistRequirement, ChecklistTemplate, DocumentType, IntakeClassification, RequirementFulfillment
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.evidence import Evidence
from yarvis_api.models.intake import IntakeItem
from yarvis_api.schemas.checklist import CaseChecklistRead, CatalogRead, ClassificationCreate, ClassificationRead, ConfirmationInput, DocumentTypeRead, FulfillmentInput, FulfillmentRead, NotesInput, RequirementRead

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
    item.status = "confirmed" if approved else "rejected"; item.confirmed_by = payload.confirmed_by; item.confirmed_at = datetime.now(timezone.utc)
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


def decide_fulfillment(fulfillment_id, approved, db):
    item = db.get(RequirementFulfillment, fulfillment_id)
    if item is None: raise HTTPException(404, "RequirementFulfillment not found")
    checklist = db.get(CaseChecklist, item.case_checklist_id); case = db.get(Case, checklist.case_id)
    item.status = "valid" if approved else "rejected"; item.validated_at = datetime.now(timezone.utc)
    event(db, "checklist.requirement_validated" if approved else "checklist.requirement_rejected", "requirement_fulfillment", item.id, case, {})
    db.commit(); db.refresh(item); return item


@router.post("/requirement-fulfillments/{fulfillment_id}/validate", response_model=FulfillmentRead)
def validate(fulfillment_id: UUID, db: Session = Depends(get_db)): return decide_fulfillment(fulfillment_id, True, db)


@router.post("/requirement-fulfillments/{fulfillment_id}/reject", response_model=FulfillmentRead)
def reject(fulfillment_id: UUID, db: Session = Depends(get_db)): return decide_fulfillment(fulfillment_id, False, db)


@router.post("/case-checklists/{checklist_id}/requirements/{requirement_id}/not-applicable", response_model=FulfillmentRead, status_code=status.HTTP_201_CREATED)
def not_applicable(checklist_id: UUID, requirement_id: UUID, payload: NotesInput, db: Session = Depends(get_db)):
    checklist, requirement, case = requirement_for(db, checklist_id, requirement_id)
    item = RequirementFulfillment(case_checklist_id=checklist.id, checklist_requirement_id=requirement.id, status="not_applicable", notes=payload.notes)
    db.add(item); db.flush(); event(db, "checklist.requirement_not_applicable", "requirement_fulfillment", item.id, case, {"requirement_code": requirement.code}); db.commit(); db.refresh(item)
    return item

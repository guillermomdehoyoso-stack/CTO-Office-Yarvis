from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.conversation import Conversation, ConversationMessage
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.operational import NextActionSuggestion, OperationalAlert
from yarvis_api.models.observation_engine import AttentionItem, DocumentRecord, Observation, PolicyEvaluation
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.schemas.conversation import (
    ConversationCreate,
    ConversationDetailRead,
    ConversationMessageCreate,
    ConversationRead,
)

router = APIRouter(tags=["mission-control", "conversations"])


def refs(db, org=None, person=None, case=None):
    for model, ident, name in ((Organization, org, "organization"), (Person, person, "person"), (Case, case, "case")):
        if ident and db.get(model, ident) is None:
            raise HTTPException(404, f"{name} not found")


@router.get("/mission-control/summary")
def summary(db: Session = Depends(get_db)):
    alerts = db.scalars(select(OperationalAlert).where(OperationalAlert.status != "resolved")).all()
    unresolved_observations = db.scalar(select(func.count()).select_from(Observation).where(Observation.confirmation_status != "confirmed")) or 0
    identity_conflicts = db.scalar(select(func.count()).select_from(Observation).where(Observation.confirmation_status == "conflicted")) or 0
    duplicate_documents = db.scalar(select(func.count()).select_from(DocumentRecord).where(DocumentRecord.processed_at.is_not(None))) or 0
    policy_matches = db.scalar(select(func.count()).select_from(PolicyEvaluation).where(PolicyEvaluation.result_status == "matched")) or 0
    insufficient_data = db.scalar(select(func.count()).select_from(PolicyEvaluation).where(PolicyEvaluation.result_status == "insufficient_data")) or 0
    pending_human_approvals = db.scalar(select(func.count()).select_from(AttentionItem).where(AttentionItem.requires_human_approval.is_(True), AttentionItem.status == "open")) or 0
    return {
        "active_cases": db.scalar(select(func.count()).select_from(Case).where(Case.status == "open")) or 0,
        "open_alerts": len(alerts),
        "critical_alerts": sum(a.severity == "critical" for a in alerts),
        "proposed_next_actions": db.scalar(select(func.count()).select_from(NextActionSuggestion).where(NextActionSuggestion.status == "proposed")) or 0,
        "expiring_requirements": sum(a.alert_type == "expiring_requirement" for a in alerts),
        "unresolved_observations": unresolved_observations,
        "identity_conflicts": identity_conflicts,
        "duplicate_documents": duplicate_documents,
        "policy_matches": policy_matches,
        "insufficient_data_evaluations": insufficient_data,
        "pending_human_approvals": pending_human_approvals,
        "recent_events": db.scalars(select(DomainEvent).order_by(DomainEvent.occurred_at.desc()).limit(10)).all(),
    }


@router.get("/mission-control/attention-items")
def attention_items(db: Session = Depends(get_db)):
    cases = db.scalars(select(Case).where(Case.status == "open")).all()
    result = []
    ranks = {"critical": 0, "expired_requirement": 1, "rejected_requirement": 2, "expiring_requirement": 3, "missing_requirement": 4}
    for case in cases:
        alerts = db.scalars(select(OperationalAlert).where(OperationalAlert.case_id == case.id, OperationalAlert.status != "resolved")).all()
        latest = db.scalar(select(DomainEvent).where(DomainEvent.case_id == case.id).order_by(DomainEvent.occurred_at.desc()))
        org = db.get(Organization, case.owner_organization_id)
        action = db.scalar(select(NextActionSuggestion).where(NextActionSuggestion.case_id == case.id, NextActionSuggestion.status == "proposed"))
        severity = "critical" if any(a.severity == "critical" for a in alerts) else "warning" if alerts else "info"
        result.append(
            {
                "case_id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "organization": org.display_name if org else None,
                "case_type": case.case_type,
                "alert_count": len(alerts),
                "highest_severity": severity,
                "next_action_summary": action.summary if action else None,
                "latest_event_at": latest.occurred_at if latest else None,
                "_rank": min([ranks.get(a.alert_type, 6) for a in alerts] or [5]),
            }
        )
    policy_items = db.scalars(select(AttentionItem).where(AttentionItem.status == "open").order_by(AttentionItem.created_at.desc()).limit(100)).all()
    for item in policy_items:
        result.append(
            {
                "case_id": None,
                "case_number": None,
                "title": f"{item.policy_key} - {item.subject_type}",
                "organization": None,
                "case_type": "policy",
                "alert_count": 1,
                "highest_severity": item.severity,
                "next_action_summary": item.recommended_action,
                "latest_event_at": item.created_at,
                "policy_key": item.policy_key,
                "subject_id": item.subject_id,
                "requires_human_approval": item.requires_human_approval,
                "_rank": 0 if item.severity == "critical" else 2,
            }
        )
    return sorted(result, key=lambda x: (x.pop("_rank"), x["latest_event_at"] is None))


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    refs(db, payload.organization_id, payload.person_id, payload.case_id)
    item = Conversation(**payload.model_dump(exclude_none=True, mode="python"))
    db.add(item)
    db.flush()
    record_event(
        db,
        event_type="conversation.created",
        aggregate_type="conversation",
        aggregate_id=item.id,
        organization_id=item.organization_id,
        case_id=item.case_id,
        payload={"title": item.title},
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/conversations", response_model=list[ConversationRead])
def conversations(db: Session = Depends(get_db)):
    return db.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailRead)
def conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Conversation, conversation_id)
    if not item:
        raise HTTPException(404, "Conversation not found")
    messages = db.scalars(select(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.created_at)).all()
    return {"conversation": item, "messages": messages}


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def message(conversation_id: UUID, payload: ConversationMessageCreate, db: Session = Depends(get_db)):
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    text = payload.text_content.strip() if payload.text_content else None
    intake = None
    if text:
        intake = IntakeItem(
            source_type="manual_text",
            content_type="text/plain",
            text_content=text,
            organization_id=convo.organization_id,
            person_id=convo.person_id,
            case_id=convo.case_id,
        )
        db.add(intake)
        db.flush()
        record_event(
            db,
            event_type="intake.received",
            aggregate_type="intake_item",
            aggregate_id=intake.id,
            organization_id=convo.organization_id,
            case_id=convo.case_id,
            payload={"source_type": "manual_text"},
        )

    item = ConversationMessage(
        conversation_id=conversation_id,
        role=payload.role or "user",
        text_content=text,
        intake_item_id=intake.id if intake else None,
    )
    db.add(item)
    db.flush()
    record_event(
        db,
        event_type="conversation.message_received",
        aggregate_type="conversation_message",
        aggregate_id=item.id,
        organization_id=convo.organization_id,
        case_id=convo.case_id,
        payload={},
    )
    db.commit()
    db.refresh(item)
    return {
        "message": item,
        "intake_item_id": intake.id if intake else None,
        "system_message": "Información recibida. Confirma el Caso y el tipo de evidencia.",
    }


@router.post("/conversations/{conversation_id}/attachments", status_code=status.HTTP_201_CREATED)
def attachment(conversation_id: UUID, payload: dict, db: Session = Depends(get_db)):
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")
    if not payload.get("original_filename"):
        raise HTTPException(422, "original_filename is required")

    item = IntakeItem(
        source_type=payload.get("source_type", "manual_upload"),
        content_type="attachment",
        original_filename=payload["original_filename"],
        mime_type=payload.get("mime_type"),
        title=payload.get("description"),
        organization_id=convo.organization_id,
        person_id=convo.person_id,
        case_id=convo.case_id,
    )
    db.add(item)
    db.flush()
    record_event(
        db,
        event_type="intake.received",
        aggregate_type="intake_item",
        aggregate_id=item.id,
        organization_id=convo.organization_id,
        case_id=convo.case_id,
        payload={"filename": item.original_filename},
    )
    db.commit()
    return {"intake_item_id": item.id, "status": "pending_context_confirmation"}

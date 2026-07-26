from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.inbound_intake import InboundIntakeSubmission
from yarvis_api.application.operational_context import AssociateIntakeOperationalContextCommand
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.models.case import Case
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person
from yarvis_api.models.evidence import Evidence
from yarvis_api.schemas.intake import (
    DeterministicInboundIntakeCreate,
    IntakeCreate,
    IntakeDetailRead,
    IntakeRead,
)
from yarvis_api.schemas.operational_context import (
    AssociateIntakeOperationalContextCreate,
    IntakeOperationalContextAssociationRead,
)

router = APIRouter(prefix="/intake", tags=["intake"])


def validate_references(db: Session, payload: IntakeCreate) -> None:
    for model, identifier, label in (
        (Organization, payload.organization_id, "organization_id"),
        (Person, payload.person_id, "person_id"),
        (Case, payload.case_id, "case_id"),
    ):
        if identifier is not None and db.get(model, identifier) is None:
            raise HTTPException(status_code=404, detail=f"{label} not found")


@router.post("", response_model=IntakeRead, status_code=status.HTTP_201_CREATED)
def create_intake(payload: IntakeCreate, db: Session = Depends(get_db)):
    validate_references(db, payload)
    item = IntakeItem(**payload.model_dump(exclude={"received_at"}, mode="python"))
    if payload.received_at is not None:
        item.received_at = payload.received_at
    db.add(item)
    db.flush()
    record_event(
        db,
        event_type="intake.received",
        aggregate_type="intake_item",
        aggregate_id=item.id,
        organization_id=item.organization_id,
        case_id=item.case_id,
        payload={"intake_number": item.intake_number, "source_type": item.source_type},
    )
    if item.case_id is not None:
        record_event(
            db,
            event_type="intake.linked_to_case",
            aggregate_type="intake_item",
            aggregate_id=item.id,
            organization_id=item.organization_id,
            case_id=item.case_id,
            payload={"intake_number": item.intake_number},
        )
    db.commit()
    db.refresh(item)
    return item


@router.post("/deterministic", response_model=IntakeDetailRead, status_code=status.HTTP_201_CREATED)
def create_deterministic_intake(
    payload: DeterministicInboundIntakeCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    adapter = request.app.state.yarvis.deterministic_inbound_adapter
    fixture = adapter.adapt(payload)
    service = request.app.state.yarvis.inbound_intake_service
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    intake_id = service.submit(
        InboundIntakeSubmission(
            fixture=fixture,
            metadata=RequestMetadata(
                requested_at=payload.received_timestamp,
                correlation_id=str(payload.correlation_id),
                command_id="receive_intake",
                causation_id=str(payload.causation_id) if payload.causation_id is not None else None,
                idempotency_key=payload.idempotency_key,
            ),
            principal=principal,
        )
    )
    request.app.state.yarvis.mission_inbox_projection_service.project_pending_events()
    return service.load_detail(db, intake_id)


@router.get("", response_model=list[IntakeRead])
def list_intake(db: Session = Depends(get_db)):
    return db.scalars(
        select(IntakeItem)
        .where(IntakeItem.organization_id.is_(None))
        .order_by(IntakeItem.received_at, IntakeItem.created_at)
    ).all()


@router.get("/deterministic/{intake_id}", response_model=IntakeDetailRead)
def get_deterministic_intake_detail(intake_id: UUID, request: Request, db: Session = Depends(get_db)):
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.inbound_intake_query_service.load_detail(
        db,
        intake_id,
        principal,
        RequestMetadata(
            requested_at=utc_now(),
            correlation_id=principal.correlation_id or str(uuid4()),
            query_id="retrieve_deterministic_intake_detail",
        ),
    )


@router.post(
    "/deterministic/{intake_id}/operational-context",
    response_model=IntakeOperationalContextAssociationRead,
    status_code=status.HTTP_201_CREATED,
)
def associate_deterministic_intake_operational_context(
    intake_id: UUID,
    payload: AssociateIntakeOperationalContextCreate,
    request: Request,
):
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    result = request.app.state.yarvis.intake_operational_context_association_service.associate(
        AssociateIntakeOperationalContextCommand(
            intake_item_id=intake_id,
            site_id=payload.site_id,
            project_id=payload.project_id,
            connector_mapping_id=payload.connector_mapping_id,
        ),
        RequestMetadata(
            requested_at=utc_now(),
            correlation_id=str(payload.correlation_id),
            command_id="associate_intake_operational_context",
            causation_id=str(payload.causation_id) if payload.causation_id is not None else None,
            idempotency_key=payload.idempotency_key,
        ),
        principal,
    )
    request.app.state.yarvis.mission_inbox_projection_service.project_pending_events()
    return result


@router.get(
    "/deterministic/{intake_id}/operational-context",
    response_model=IntakeOperationalContextAssociationRead,
)
def get_deterministic_intake_operational_context(intake_id: UUID, request: Request, db: Session = Depends(get_db)):
    principal = request.app.state.yarvis.authentication.authenticate(transport_authentication_request(request))
    return request.app.state.yarvis.intake_operational_context_query_service.retrieve(
        db,
        intake_id,
        principal,
        RequestMetadata(
            requested_at=utc_now(),
            correlation_id=principal.correlation_id or str(uuid4()),
            query_id="retrieve_intake_operational_context",
        ),
    )


@router.get("/{intake_id}", response_model=IntakeRead)
def get_intake(intake_id: UUID, db: Session = Depends(get_db)):
    item = db.scalar(
        select(IntakeItem).where(
            IntakeItem.id == intake_id,
            IntakeItem.organization_id.is_(None),
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="IntakeItem not found")
    return item


@router.post("/{intake_id}/link-case/{case_id}", response_model=IntakeRead)
def link_case(intake_id: UUID, case_id: UUID, db: Session = Depends(get_db)):
    item = db.get(IntakeItem, intake_id)
    if item is None:
        raise HTTPException(status_code=404, detail="IntakeItem not found")
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if item.case_id == case_id:
        raise HTTPException(status_code=409, detail="IntakeItem is already linked to this Case")
    item.case_id = case_id
    record_event(
        db,
        event_type="intake.linked_to_case",
        aggregate_type="intake_item",
        aggregate_id=item.id,
        organization_id=item.organization_id or case.owner_organization_id,
        case_id=case_id,
        payload={"intake_number": item.intake_number},
    )
    db.commit()
    db.refresh(item)
    return item

@router.post("/{intake_id}/confirm-context")
def confirm_context(intake_id: UUID, payload: dict, db: Session = Depends(get_db)):
    item=db.get(IntakeItem,intake_id)
    if item is None: raise HTTPException(404,"IntakeItem not found")
    for field,model in (("organization_id",Organization),("person_id",Person),("case_id",Case)):
        identifier=payload.get(field)
        if identifier and db.get(model,identifier) is None: raise HTTPException(404,f"{field} not found")
        if identifier: setattr(item,field,identifier)
    evidence=None
    if payload.get("evidence_type") and item.case_id:
        evidence=Evidence(case_id=item.case_id,intake_item_id=item.id,evidence_type=payload["evidence_type"],title=item.title or item.original_filename or "Conversation intake")
        db.add(evidence);db.flush()
    record_event(db,event_type="intake.context_confirmed",aggregate_type="intake_item",aggregate_id=item.id,organization_id=item.organization_id,case_id=item.case_id,payload={"evidence_id":str(evidence.id) if evidence else None});db.commit();db.refresh(item)
    return {"intake":item,"evidence_id":evidence.id if evidence else None,"status":"confirmed"}

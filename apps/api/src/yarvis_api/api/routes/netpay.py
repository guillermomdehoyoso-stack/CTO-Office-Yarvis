from uuid import UUID
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.netpay import NetpayDeviceAssignment, NetpayServiceCase, NetpayShipment
from yarvis_api.modules.document_intelligence import DocumentIntelligenceProvider
from yarvis_api.modules.netpay_parser import parse_email
from yarvis_api.schemas.netpay import (
    DocumentImportPayload,
    DocumentImportResult,
    EmailImportPayload,
    NetpayDeviceAssignmentRead,
    NetpayInvestigationStatus,
    NetpayInvestigationUpdate,
    NetpayServiceCaseImportResult,
    NetpayServiceCaseRead,
    NetpayShipmentCreate,
    NetpayShipmentRead,
    NetpayTimelineItem,
)

router = APIRouter(prefix="/netpay", tags=["netpay"])
doc_provider = DocumentIntelligenceProvider()


@router.post("/import-email", response_model=NetpayServiceCaseImportResult, status_code=status.HTTP_201_CREATED)
@router.post("/service-cases/import-email", response_model=NetpayServiceCaseImportResult, status_code=status.HTTP_201_CREATED)
def import_email(payload: EmailImportPayload, db: Session = Depends(get_db)):
    parsed = parse_email(payload.model_dump(mode="python"))
    if not parsed["folio"]:
        raise HTTPException(status_code=422, detail="No folio detected")

    if payload.gmail_message_id:
        existing = db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.source_email_id == payload.gmail_message_id))
        if existing:
            shipments = db.scalars(select(NetpayShipment).where(NetpayShipment.service_case_id == existing.id).order_by(NetpayShipment.created_at)).all()
            return NetpayServiceCaseImportResult(created=False, duplicate_by="message_id", service_case=existing, shipments=shipments)

    existing_by_folio = db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.folio == parsed["folio"]))
    if existing_by_folio:
        shipments = db.scalars(select(NetpayShipment).where(NetpayShipment.service_case_id == existing_by_folio.id).order_by(NetpayShipment.created_at)).all()
        return NetpayServiceCaseImportResult(created=False, duplicate_by="folio", service_case=existing_by_folio, shipments=shipments)

    intake = IntakeItem(
        source_type="email",
        content_type="message/rfc822",
        title=payload.subject,
        text_content=parsed["body_normalized"],
        received_at=payload.received_at or utc_now(),
    )
    db.add(intake)
    db.flush()

    service_case = NetpayServiceCase(
        folio=parsed["folio"],
        received_at=payload.received_at or utc_now(),
        case_type=None,
        status="detected",
        source_email_id=payload.gmail_message_id,
        source_thread_id=payload.gmail_thread_id,
        source_subject=payload.subject,
        source_sender=payload.from_address,
        source_intake_item_id=intake.id,
        sent_at=payload.sent_at,
        customer_name=None,
        merchant_name=None,
        address=None,
        store_id=parsed["store_id"],
        device_serial=parsed["device_serial"],
        movement_type=parsed["movement_type"],
        investigation_status=NetpayInvestigationStatus.pending.value,
        notes=None,
        to_addresses=parsed["to_addresses"],
        cc_addresses=parsed["cc_addresses"],
        reply_to_addresses=parsed["reply_to_addresses"],
        delivered_to=parsed["delivered_to"],
        x_original_to=parsed["x_original_to"],
        original_recipient=parsed["original_recipient"],
        recipient_addresses=parsed["recipient_addresses"],
        operational_recipient=parsed["operational_recipient"],
        recipient_resolution_source=parsed["recipient_resolution_source"],
        recipient_resolution_confidence=parsed["recipient_resolution_confidence"],
        physical_destination_resolution_source=parsed["physical_destination_resolution_source"],
        physical_destination_resolution_confidence=parsed["physical_destination_resolution_confidence"],
        body_normalized=parsed["body_normalized"],
        attachments_metadata=[item.model_dump(mode="python") for item in payload.attachments_metadata],
        extracted_fields=parsed["extracted_fields"],
        operational_resolution=parsed["operational_resolution"],
    )
    db.add(service_case)
    db.flush()

    record_event(
        db,
        event_type="netpay.case_detected",
        aggregate_type="netpay_service_case",
        aggregate_id=service_case.id,
        payload={"folio": service_case.folio, "source_email_id": service_case.source_email_id},
    )

    shipments: list[NetpayShipment] = []
    for tracking in parsed["tracking_logistics"]:
        shipment = NetpayShipment(
            service_case_id=service_case.id,
            tracking_number=tracking["tracking_number"],
            direction=tracking["direction"],
            status="detected",
            folio=tracking["folio"],
            store_id=tracking["store_id"],
            device_serial=tracking["device_serial"],
            extracted_fields=tracking.get("extracted_fields") or {},
        )
        db.add(shipment)
        db.flush()
        shipments.append(shipment)
        record_event(
            db,
            event_type="netpay.shipment_registered",
            aggregate_type="netpay_shipment",
            aggregate_id=shipment.id,
            payload={"service_case_id": str(service_case.id), "tracking_number": shipment.tracking_number},
        )

    db.commit()
    db.refresh(service_case)
    return NetpayServiceCaseImportResult(created=True, service_case=service_case, shipments=shipments)


@router.post("/import-document", response_model=DocumentImportResult, status_code=status.HTTP_201_CREATED)
def import_document(payload: DocumentImportPayload, db: Session = Depends(get_db)):
    service_case = db.get(NetpayServiceCase, payload.service_case_id)
    if service_case is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")

    fingerprint_source = f"{payload.service_case_id}:{payload.filename}:{payload.storage_reference or ''}:{payload.extracted_text or ''}"
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

    existing = db.scalar(
        select(DomainEvent)
        .where(DomainEvent.event_type == "netpay.document_imported")
        .where(DomainEvent.aggregate_id == service_case.id)
        .where(DomainEvent.payload["document_fingerprint"].astext == fingerprint)
    )
    if existing:
        return DocumentImportResult(
            created=False,
            duplicate_by="document_fingerprint",
            intake_item_id=existing.payload.get("intake_item_id"),
            document_summary={
                "value": existing.payload.get("summary"),
                "confidence": existing.payload.get("confidence", 0.0),
                "provenance": "document_intelligence",
                "source_reference": payload.filename,
                "confirmation_status": "candidate",
                "extraction_method": existing.payload.get("method", "unknown"),
                "source_type": "document",
                "confirmed_by_user": None,
                "confirmed_at": None,
            },
        )

    intelligence = doc_provider.analyze_document(
        mime_type=payload.mime_type,
        extracted_text=payload.extracted_text,
        enable_ocr=payload.enable_ocr,
        binary=None,
    )

    intake = IntakeItem(
        source_type="manual_upload",
        content_type=payload.mime_type,
        title=payload.filename,
        text_content=intelligence.text or None,
        original_filename=payload.filename,
        case_id=None,
        received_at=utc_now(),
    )
    db.add(intake)
    db.flush()

    summary = (intelligence.text[:240] + "...") if len(intelligence.text) > 240 else intelligence.text
    record_event(
        db,
        event_type="netpay.document_imported",
        aggregate_type="netpay_service_case",
        aggregate_id=service_case.id,
        payload={
            "intake_item_id": str(intake.id),
            "filename": payload.filename,
            "mime_type": payload.mime_type,
            "document_fingerprint": fingerprint,
            "provider": intelligence.provider,
            "method": intelligence.method,
            "confidence": intelligence.confidence,
            "summary": summary,
        },
    )
    db.commit()
    return DocumentImportResult(
        created=True,
        intake_item_id=intake.id,
        document_summary={
            "value": summary,
            "confidence": intelligence.confidence,
            "provenance": "document_intelligence",
            "source_reference": payload.filename,
            "confirmation_status": "candidate",
            "extraction_method": intelligence.method,
            "source_type": "document",
            "confirmed_by_user": None,
            "confirmed_at": None,
        },
    )


@router.get("/service-cases", response_model=list[NetpayServiceCaseRead])
def list_service_cases(db: Session = Depends(get_db)):
    return db.scalars(select(NetpayServiceCase).order_by(NetpayServiceCase.received_at.desc(), NetpayServiceCase.created_at.desc())).all()


@router.get("/service-cases/pending", response_model=list[NetpayServiceCaseRead])
@router.get("/pending", response_model=list[NetpayServiceCaseRead])
def list_pending_service_cases(db: Session = Depends(get_db)):
    return db.scalars(
        select(NetpayServiceCase)
        .where(NetpayServiceCase.investigation_status != NetpayInvestigationStatus.confirmed.value)
        .order_by(NetpayServiceCase.received_at.desc())
    ).all()


@router.get("/service-cases/{service_case_id}", response_model=NetpayServiceCaseRead)
def get_service_case(service_case_id: UUID, db: Session = Depends(get_db)):
    item = db.get(NetpayServiceCase, service_case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")
    return item


@router.get("/service-cases/{service_case_id}/shipments", response_model=list[NetpayShipmentRead])
def list_service_case_shipments(service_case_id: UUID, db: Session = Depends(get_db)):
    service_case = db.get(NetpayServiceCase, service_case_id)
    if service_case is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")
    return db.scalars(select(NetpayShipment).where(NetpayShipment.service_case_id == service_case_id).order_by(NetpayShipment.created_at)).all()


@router.patch("/service-cases/{service_case_id}/investigation", response_model=NetpayServiceCaseRead)
@router.patch("/investigation/{service_case_id}", response_model=NetpayServiceCaseRead)
def update_investigation(service_case_id: UUID, payload: NetpayInvestigationUpdate, db: Session = Depends(get_db)):
    item = db.get(NetpayServiceCase, service_case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")

    update_data = payload.model_dump(exclude_none=True)
    if item.investigation_status == NetpayInvestigationStatus.pending.value and update_data:
        item.investigation_status = NetpayInvestigationStatus.in_progress.value
        record_event(
            db,
            event_type="netpay.case_investigation_started",
            aggregate_type="netpay_service_case",
            aggregate_id=item.id,
            payload={"folio": item.folio},
        )

    for field, value in update_data.items():
        setattr(item, field, value)

    if item.investigation_status == NetpayInvestigationStatus.confirmed.value:
        item.status = "confirmed"
        record_event(
            db,
            event_type="netpay.case_confirmed",
            aggregate_type="netpay_service_case",
            aggregate_id=item.id,
            payload={"folio": item.folio, "store_id": item.store_id, "device_serial": item.device_serial},
        )

    if item.investigation_status == NetpayInvestigationStatus.confirmed.value and item.device_serial:
        assignment_status = "assigned"
        assignment_returned_at = None
        assignment_assigned_at = utc_now()
        event_type = "netpay.device_assigned"

        if item.movement_type == "collection":
            assignment_status = "returned"
            assignment_returned_at = utc_now()
            assignment_assigned_at = None
            event_type = "netpay.device_returned"

        assignment = NetpayDeviceAssignment(
            device_serial=item.device_serial,
            store_id=item.store_id,
            assigned_at=assignment_assigned_at,
            returned_at=assignment_returned_at,
            status=assignment_status,
            service_case_id=item.id,
        )
        db.add(assignment)
        db.flush()
        record_event(
            db,
            event_type=event_type,
            aggregate_type="netpay_device_assignment",
            aggregate_id=assignment.id,
            payload={"device_serial": assignment.device_serial, "store_id": assignment.store_id},
        )

    db.commit()
    db.refresh(item)
    return item


@router.post("/service-cases/{service_case_id}/shipments", response_model=NetpayShipmentRead, status_code=status.HTTP_201_CREATED)
@router.post("/shipment/{service_case_id}", response_model=NetpayShipmentRead, status_code=status.HTTP_201_CREATED)
def register_shipment(service_case_id: UUID, payload: NetpayShipmentCreate, db: Session = Depends(get_db)):
    service_case = db.get(NetpayServiceCase, service_case_id)
    if service_case is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")

    shipment = NetpayShipment(service_case_id=service_case_id, **payload.model_dump(mode="python"))
    db.add(shipment)
    db.flush()

    record_event(
        db,
        event_type="netpay.shipment_registered",
        aggregate_type="netpay_shipment",
        aggregate_id=shipment.id,
        payload={"service_case_id": str(service_case_id), "tracking_number": shipment.tracking_number},
    )

    if shipment.direction == "collection" and shipment.delivered_at and service_case.device_serial:
        assignment = NetpayDeviceAssignment(
            device_serial=service_case.device_serial,
            store_id=service_case.store_id,
            assigned_at=None,
            returned_at=shipment.delivered_at,
            status="returned",
            service_case_id=service_case.id,
        )
        db.add(assignment)
        db.flush()
        record_event(
            db,
            event_type="netpay.device_returned",
            aggregate_type="netpay_device_assignment",
            aggregate_id=assignment.id,
            payload={"device_serial": assignment.device_serial, "store_id": assignment.store_id},
        )

    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/devices", response_model=list[NetpayDeviceAssignmentRead])
def list_devices(db: Session = Depends(get_db)):
    return db.scalars(select(NetpayDeviceAssignment).order_by(NetpayDeviceAssignment.updated_at.desc())).all()


@router.get("/timeline/{service_case_id}", response_model=list[NetpayTimelineItem])
def timeline(service_case_id: UUID, db: Session = Depends(get_db)):
    service_case = db.get(NetpayServiceCase, service_case_id)
    if service_case is None:
        raise HTTPException(status_code=404, detail="NetPay service case not found")
    events = db.scalars(
        select(DomainEvent)
        .where(
            (DomainEvent.aggregate_id == service_case_id)
            | ((DomainEvent.payload["service_case_id"].astext == str(service_case_id)))
        )
        .order_by(DomainEvent.occurred_at)
    ).all()
    return [
        NetpayTimelineItem(
            event_type=item.event_type,
            aggregate_type=item.aggregate_type,
            aggregate_id=item.aggregate_id,
            occurred_at=item.occurred_at,
            payload=item.payload,
        )
        for item in events
    ]



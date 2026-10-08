"""Read-only Netpay Gmail Intake D1 HTTP surface."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_inbox_authority import netpay_inbox_envelope
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.netpay_gmail_intake import (
    NetpayGmailCommandReceipt,
    NetpayGmailConnection,
    NetpayGmailSourceItem,
    NetpayGmailSyncRun,
)
from yarvis_api.schemas.netpay_gmail_intake import (
    GmailConnectionCreate,
    GmailConnectionRead,
    GmailSourceItemRead,
    GmailSourcePage,
    GmailSyncPage,
    GmailSyncRead,
    GmailSyncRequest,
)
from yarvis_api.services.netpay_gmail_intake import run_manual_sync
from yarvis_api.services.netpay_gmail_provider import (
    DEFAULT_FAKE_GMAIL_PROVIDER,
    GmailProviderError,
    GmailSourceProvider,
)

router = APIRouter(prefix="/netpay/gmail", tags=["netpay-gmail-intake"])


def _operator(envelope: IdentityAuthorityEnvelope) -> IdentityAuthorityEnvelope:
    return netpay_inbox_envelope(envelope, required_scope="netpay.inbox.manage")


def _viewer(envelope: IdentityAuthorityEnvelope) -> IdentityAuthorityEnvelope:
    return netpay_inbox_envelope(envelope, required_scope="netpay.inbox.read")


def _fingerprint(command: str, target: UUID | None, payload: object) -> str:
    value = {"command": command, "target": str(target) if target else None, "payload": payload}
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _correlation(envelope: IdentityAuthorityEnvelope) -> UUID:
    try:
        return UUID(envelope.correlation_id)
    except ValueError:
        return uuid4()


def gmail_provider() -> GmailSourceProvider:
    return DEFAULT_FAKE_GMAIL_PROVIDER


def _connection(db: Session, envelope: IdentityAuthorityEnvelope, connection_id: UUID) -> NetpayGmailConnection:
    item = db.scalar(
        select(NetpayGmailConnection).where(
            NetpayGmailConnection.id == connection_id,
            NetpayGmailConnection.organization_id == envelope.organization_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return item


def _receipt(
    db: Session,
    envelope: IdentityAuthorityEnvelope,
    *,
    command: str,
    key: str,
    target: UUID | None,
    payload: object,
) -> NetpayGmailCommandReceipt | None:
    current = db.scalar(
        select(NetpayGmailCommandReceipt).where(
            NetpayGmailCommandReceipt.organization_id == envelope.organization_id,
            NetpayGmailCommandReceipt.command_type == command,
            NetpayGmailCommandReceipt.idempotency_key == key,
        )
    )
    if current is None:
        return None
    if current.request_fingerprint != _fingerprint(command, target, payload):
        raise HTTPException(status_code=409, detail="idempotency conflict")
    return current


def _store_receipt(
    db: Session,
    envelope: IdentityAuthorityEnvelope,
    *,
    command: str,
    key: str,
    target: UUID | None,
    payload: object,
    resource_id: UUID,
    status_code: int,
    response_body: dict,
) -> None:
    db.add(
        NetpayGmailCommandReceipt(
            organization_id=envelope.organization_id,
            command_type=command,
            idempotency_key=key,
            request_fingerprint=_fingerprint(command, target, payload),
            actor_principal_id=envelope.principal_id,
            correlation_id=_correlation(envelope),
            result_resource_id=resource_id,
            result_status_code=status_code,
            result_response_body=response_body,
        )
    )


@router.post("/connections", response_model=GmailConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: GmailConnectionCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> dict:
    current = _operator(envelope)
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="idempotency key required")
    replay = _receipt(db, current, command="IC-NETPAY-CMD-016", key=key, target=None, payload=payload.model_dump())
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    connection = NetpayGmailConnection(
        organization_id=current.organization_id,
        provider_account_id=payload.provider_account_id.strip(),
        credential_secret_ref=payload.credential_secret_ref.strip(),
        label_id=payload.label_id.strip(),
        query=payload.query.strip(),
        state="connected",
        created_by_principal_id=current.principal_id,
        updated_by_principal_id=current.principal_id,
    )
    db.add(connection)
    db.flush()
    correlation = _correlation(current)
    record_event(
        db,
        event_type="netpay.gmail.source_connected",
        aggregate_type="netpay_gmail_connection",
        aggregate_id=connection.id,
        organization_id=current.organization_id,
        correlation_id=correlation,
        causation_id=correlation,
        payload={"connection_id": str(connection.id), "actor_principal_id": str(current.principal_id)},
    )
    body = GmailConnectionRead.model_validate(connection).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-016",
        key=key,
        target=None,
        payload=payload.model_dump(),
        resource_id=connection.id,
        status_code=201,
        response_body=body,
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="connection already exists") from error
    response.status_code = 201
    return body


@router.get("/connections", response_model=list[GmailConnectionRead])
def list_connections(
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> list[NetpayGmailConnection]:
    current = _viewer(envelope)
    return list(
        db.scalars(
            select(NetpayGmailConnection)
            .where(NetpayGmailConnection.organization_id == current.organization_id)
            .order_by(NetpayGmailConnection.created_at, NetpayGmailConnection.id)
        ).all()
    )


@router.get("/connections/{connection_id}", response_model=GmailConnectionRead)
def get_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> NetpayGmailConnection:
    return _connection(db, _viewer(envelope), connection_id)


@router.post("/connections/{connection_id}/validate", response_model=GmailConnectionRead)
def validate_connection(
    connection_id: UUID,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
    provider: GmailSourceProvider = Depends(gmail_provider),
) -> dict:
    current = _operator(envelope)
    connection = _connection(db, current, connection_id)
    payload = {"connection_id": str(connection_id)}
    replay = _receipt(
        db,
        current,
        command="IC-NETPAY-CMD-016",
        key=idempotency_key.strip(),
        target=connection_id,
        payload=payload,
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    try:
        provider.list_messages(
            provider_account_id=connection.provider_account_id,
            label_id=connection.label_id,
            query=connection.query,
        )
    except GmailProviderError as error:
        connection.state = "failed"
        connection.last_error_code = error.code
        db.commit()
        raise HTTPException(status_code=422, detail={"code": error.code}) from error
    connection.state = "ready"
    connection.last_error_code = None
    connection.updated_by_principal_id = current.principal_id
    body = GmailConnectionRead.model_validate(connection).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-016",
        key=idempotency_key.strip(),
        target=connection_id,
        payload=payload,
        resource_id=connection.id,
        status_code=200,
        response_body=body,
    )
    db.commit()
    return body


@router.post("/connections/{connection_id}/disconnect", response_model=GmailConnectionRead)
def disconnect_connection(
    connection_id: UUID,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> dict:
    current = _operator(envelope)
    connection = _connection(db, current, connection_id)
    payload = {"connection_id": str(connection_id)}
    replay = _receipt(
        db,
        current,
        command="IC-NETPAY-CMD-016",
        key=idempotency_key.strip(),
        target=connection_id,
        payload=payload,
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    connection.state = "disconnected"
    connection.updated_by_principal_id = current.principal_id
    body = GmailConnectionRead.model_validate(connection).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-016",
        key=idempotency_key.strip(),
        target=connection_id,
        payload=payload,
        resource_id=connection.id,
        status_code=200,
        response_body=body,
    )
    record_event(
        db,
        event_type="netpay.gmail.source_disconnected",
        aggregate_type="netpay_gmail_connection",
        aggregate_id=connection.id,
        organization_id=current.organization_id,
        correlation_id=_correlation(current),
        causation_id=_correlation(current),
        payload={
            "connection_id": str(connection.id),
            "actor_principal_id": str(current.principal_id),
        },
    )
    db.commit()
    return body


@router.post("/connections/{connection_id}/sync", response_model=GmailSyncRead, status_code=status.HTTP_201_CREATED)
def sync_connection(
    connection_id: UUID,
    payload: GmailSyncRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
    provider: GmailSourceProvider = Depends(gmail_provider),
) -> dict:
    current = _operator(envelope)
    connection = _connection(db, current, connection_id)
    key = idempotency_key.strip()
    replay = _receipt(
        db,
        current,
        command="IC-NETPAY-CMD-017",
        key=key,
        target=connection_id,
        payload=payload.model_dump(),
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    if connection.state in {"disconnected", "revoked"}:
        raise HTTPException(status_code=409, detail="connection is not usable")
    result = run_manual_sync(
        db,
        connection=connection,
        provider=provider,
        actor_principal_id=current.principal_id,
        correlation_id=_correlation(current),
        backfill_days=payload.backfill_days,
    )
    record_event(
        db,
        event_type="netpay.gmail.manual_sync_started",
        aggregate_type="netpay_gmail_sync_run",
        aggregate_id=result.run.id,
        organization_id=current.organization_id,
        correlation_id=result.run.correlation_id,
        causation_id=result.run.id,
        payload={
            "sync_run_id": str(result.run.id),
            "connection_id": str(connection.id),
        },
    )
    record_event(
        db,
        event_type="netpay.gmail.manual_sync_completed",
        aggregate_type="netpay_gmail_sync_run",
        aggregate_id=result.run.id,
        organization_id=current.organization_id,
        correlation_id=result.run.correlation_id,
        causation_id=result.run.id,
        payload={
            "sync_run_id": str(result.run.id),
            "connection_id": str(connection.id),
            "captured_count": result.run.captured_count,
            "deduplicated_count": result.run.deduplicated_count,
            "conflict_count": result.run.conflict_count,
            "cursor_advanced": result.run.cursor_after is not None,
        },
    )
    body = GmailSyncRead.model_validate(result.run).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-017",
        key=key,
        target=connection_id,
        payload=payload.model_dump(),
        resource_id=result.run.id,
        status_code=201,
        response_body=body,
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="sync conflict") from error
    response.status_code = 201
    return body


@router.get("/connections/{connection_id}/sync-runs", response_model=GmailSyncPage)
def list_sync_runs(
    connection_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> GmailSyncPage:
    current = _viewer(envelope)
    _connection(db, current, connection_id)
    stmt = select(NetpayGmailSyncRun).where(
        NetpayGmailSyncRun.organization_id == current.organization_id,
        NetpayGmailSyncRun.connection_id == connection_id,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(NetpayGmailSyncRun.created_at.desc(), NetpayGmailSyncRun.id).offset(offset).limit(limit)
    ).all()
    return GmailSyncPage(
        items=[GmailSyncRead.model_validate(item) for item in items],
        offset=offset,
        limit=limit,
        total=total,
    )


@router.get("/source-items", response_model=GmailSourcePage)
def list_source_items(
    connection_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> GmailSourcePage:
    current = _viewer(envelope)
    stmt = select(NetpayGmailSourceItem).where(NetpayGmailSourceItem.organization_id == current.organization_id)
    if connection_id is not None:
        stmt = stmt.where(NetpayGmailSourceItem.connection_id == connection_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(NetpayGmailSourceItem.provider_received_at, NetpayGmailSourceItem.id).offset(offset).limit(limit)
    ).all()
    return GmailSourcePage(
        items=[GmailSourceItemRead.model_validate(item) for item in items],
        offset=offset,
        limit=limit,
        total=total,
    )


@router.get("/source-items/{source_item_id}", response_model=GmailSourceItemRead)
def get_source_item(
    source_item_id: UUID,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> NetpayGmailSourceItem:
    current = _viewer(envelope)
    item = db.scalar(
        select(NetpayGmailSourceItem).where(
            NetpayGmailSourceItem.id == source_item_id,
            NetpayGmailSourceItem.organization_id == current.organization_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return item

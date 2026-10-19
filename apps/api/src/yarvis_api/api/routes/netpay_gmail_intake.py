"""Read-only Netpay Gmail intake and D2 review HTTP surface."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from psycopg.errors import UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.api.routes.netpay_inbox import CommercialIntakeDraft, execute_create_commercial_intake
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_inbox_authority import netpay_inbox_envelope
from yarvis_api.config import get_settings
from yarvis_api.database import get_db
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.netpay_gmail_intake import (
    NetpayCandidateCommercialIntakeTrace,
    NetpayCandidateHumanFollowUp,
    NetpayCandidateOnboardingDossier,
    NetpayCandidateQualification,
    NetpayDossierEvidenceReference,
    NetpayDossierRequirementReview,
    NetpayGmailCommandReceipt,
    NetpayGmailConnection,
    NetpayGmailOAuthAttempt,
    NetpayGmailSourceItem,
    NetpayGmailSyncRun,
    NetpayIntakeCandidate,
)
from yarvis_api.models.netpay_inbox import CommercialIntakeItem, NetpayServiceCase
from yarvis_api.schemas.netpay_gmail_intake import (
    CandidateCommercialIntakeCreate,
    CandidateDossierCreate,
    CandidateDossierRequirementReviewWrite,
    CandidateHumanFollowUpCreate,
    CandidateHumanFollowUpPage,
    CandidateHumanFollowUpRead,
    CandidateQualificationRead,
    CandidateQualificationWrite,
    GmailCandidatePage,
    GmailCandidateRead,
    GmailCandidateReview,
    GmailConnectionCreate,
    GmailConnectionRead,
    GmailOAuthStartRead,
    GmailPilotManifestRead,
    GmailSourceItemRead,
    GmailSourcePage,
    GmailSyncPage,
    GmailSyncRead,
    GmailSyncRequest,
)
from yarvis_api.services.netpay_gmail_google_provider import GoogleGmailOAuthCoordinator, GoogleGmailProvider
from yarvis_api.services.netpay_gmail_intake import run_manual_sync
from yarvis_api.services.netpay_gmail_provider import (
    DEFAULT_FAKE_GMAIL_PROVIDER,
    GmailProviderError,
    GmailSourceProvider,
)
from yarvis_api.services.netpay_gmail_secret_store import (
    DEFAULT_MEMORY_GMAIL_SECRET_STORE,
    AesGcmFileSecretStore,
    GmailSecretStore,
    GmailSecretStoreError,
)
from yarvis_api.services.netpay_h2d_catalog import (
    CATALOG_EFFECTIVE_DATE,
    CATALOG_OWNER,
    CATALOG_SHA256,
    CATALOG_VERSION,
    build_catalog_snapshot,
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
    settings = get_settings()
    if settings.gmail_intake_enabled and settings.gmail_provider == "google":
        return GoogleGmailProvider(gmail_secret_store())
    return DEFAULT_FAKE_GMAIL_PROVIDER


def gmail_secret_store() -> GmailSecretStore:
    settings = get_settings()
    if settings.gmail_intake_enabled:
        assert settings.gmail_token_store_root is not None and settings.gmail_token_key_file is not None
        return AesGcmFileSecretStore(root=settings.gmail_token_store_root, key_file=settings.gmail_token_key_file)
    return DEFAULT_MEMORY_GMAIL_SECRET_STORE


def gmail_oauth_coordinator() -> GoogleGmailOAuthCoordinator:
    settings = get_settings()
    if not settings.gmail_intake_enabled:
        raise HTTPException(status_code=503, detail={"code": "gmail_pilot_disabled"})
    assert settings.gmail_oauth_client_id_file is not None and settings.gmail_oauth_client_secret_file is not None
    return GoogleGmailOAuthCoordinator(
        client_id_file=settings.gmail_oauth_client_id_file,
        client_secret_file=settings.gmail_oauth_client_secret_file,
        redirect_uri=settings.gmail_oauth_redirect_uri,
        label_name=settings.gmail_label_name,
    )


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
        provider.validate_binding(
            provider_account_id=connection.provider_account_id,
            label_id=connection.label_id,
            credential_secret_ref=connection.credential_secret_ref,
        )
    except GmailProviderError as error:
        connection.state = "failed"
        connection.last_error_code = error.code
        db.commit()
        raise HTTPException(status_code=422, detail={"code": error.code}) from error
    connection.state = "ready"
    connection.last_error_code = None
    connection.mailbox_verified_at = datetime.now(timezone.utc)
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
    store: GmailSecretStore = Depends(gmail_secret_store),
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
    if connection.provider_kind == "google":
        try:
            store.delete(connection.credential_secret_ref)
        except GmailSecretStoreError as error:
            raise HTTPException(status_code=422, detail={"code": error.code}) from error
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
    _connection(db, current, connection_id)
    connection = db.scalar(
        select(NetpayGmailConnection)
        .where(
            NetpayGmailConnection.id == connection_id,
            NetpayGmailConnection.organization_id == current.organization_id,
        )
        .with_for_update(skip_locked=True)
    )
    if connection is None or connection.state == "running":
        raise HTTPException(status_code=409, detail={"code": "gmail_sync_in_progress"})
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
    if connection.provider_kind == "google" and connection.manifest_status != "approved":
        raise HTTPException(status_code=409, detail={"code": "pilot_manifest_not_approved"})
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


@router.post("/oauth/start", response_model=GmailOAuthStartRead)
def start_oauth(
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
    store: GmailSecretStore = Depends(gmail_secret_store),
    coordinator: GoogleGmailOAuthCoordinator = Depends(gmail_oauth_coordinator),
) -> GmailOAuthStartRead:
    current = _operator(envelope)
    existing = db.scalar(
        select(NetpayGmailConnection).where(
            NetpayGmailConnection.organization_id == current.organization_id,
            NetpayGmailConnection.provider_kind == "google",
            NetpayGmailConnection.state.in_(("ready", "succeeded")),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail={"code": "gmail_connection_already_ready"})
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    attempt_id = uuid4()
    secret_ref = store.put(f"oauth-attempts/{attempt_id}", {"code_verifier": verifier})
    db.add(
        NetpayGmailOAuthAttempt(
            id=attempt_id,
            organization_id=current.organization_id,
            principal_id=current.principal_id,
            state_digest=hashlib.sha256(state.encode("utf-8")).hexdigest(),
            secret_ref=secret_ref,
            expires_at=expires_at,
        )
    )
    db.commit()
    return GmailOAuthStartRead(
        authorization_url=coordinator.authorization_url(state=state, code_verifier=verifier),
        expires_at=expires_at,
    )


@router.get("/oauth/callback", response_class=RedirectResponse)
def oauth_callback(
    state: str,
    code: str,
    db: Session = Depends(get_db),
    store: GmailSecretStore = Depends(gmail_secret_store),
    coordinator: GoogleGmailOAuthCoordinator = Depends(gmail_oauth_coordinator),
) -> RedirectResponse:
    clock = datetime.now(timezone.utc)
    attempt = db.scalar(
        select(NetpayGmailOAuthAttempt).where(
            NetpayGmailOAuthAttempt.state_digest == hashlib.sha256(state.encode("utf-8")).hexdigest()
        )
    )
    if attempt is None or attempt.consumed_at is not None or attempt.expires_at <= clock:
        raise HTTPException(status_code=409, detail={"code": "oauth_state_invalid"})
    try:
        verifier = str(store.get(attempt.secret_ref)["code_verifier"])
        result = coordinator.exchange(state=state, code=code, code_verifier=verifier)
        settings = get_settings()
        assert settings.gmail_mailbox_binding is not None
        expected = store.get(settings.gmail_mailbox_binding)
        expected_email = str(expected.get("expected_email", ""))
        if not expected_email or not hmac.compare_digest(result.email_address.casefold(), expected_email.casefold()):
            raise GmailProviderError("mailbox_mismatch")
        existing = db.scalar(
            select(NetpayGmailConnection).where(
                NetpayGmailConnection.organization_id == attempt.organization_id,
                NetpayGmailConnection.provider_account_id == result.email_address,
            )
        )
        if existing is not None:
            if existing.provider_kind != "google" or existing.state not in {"ready", "succeeded"}:
                raise GmailProviderError("gmail_connection_already_exists")
            attempt.consumed_at = clock
            db.commit()
            store.delete(attempt.secret_ref)
            return RedirectResponse(get_settings().gmail_post_connect_redirect_uri, status_code=303)
        connection_id = uuid4()
        credential_ref = store.put(f"credentials/{connection_id}", result.token_payload)
        connection = NetpayGmailConnection(
            id=connection_id,
            organization_id=attempt.organization_id,
            provider_account_id=result.email_address,
            provider_kind="google",
            credential_secret_ref=credential_ref,
            label_id=result.label_id,
            query="",
            state="ready",
            cursor=result.history_id or None,
            mailbox_verified_at=clock,
            created_by_principal_id=attempt.principal_id,
            updated_by_principal_id=attempt.principal_id,
        )
        db.add(connection)
        attempt.consumed_at = clock
        db.flush()
        record_event(
            db,
            event_type="netpay.gmail.source_connected",
            aggregate_type="netpay_gmail_connection",
            aggregate_id=connection.id,
            organization_id=attempt.organization_id,
            correlation_id=uuid4(),
            causation_id=attempt.id,
            payload={"connection_id": str(connection.id), "provider": "google"},
        )
        db.commit()
        store.delete(attempt.secret_ref)
    except (GmailProviderError, GmailSecretStoreError, KeyError) as error:
        attempt_id = attempt.id
        attempt_secret_ref = attempt.secret_ref
        db.rollback()
        failed_attempt = db.get(NetpayGmailOAuthAttempt, attempt_id)
        if failed_attempt is not None and failed_attempt.consumed_at is None:
            failed_attempt.consumed_at = clock
            db.commit()
        try:
            store.delete(attempt_secret_ref)
        except GmailSecretStoreError as cleanup_error:
            raise HTTPException(status_code=422, detail={"code": "oauth_cleanup_failed"}) from cleanup_error
        code_value = (
            error.code if isinstance(error, (GmailProviderError, GmailSecretStoreError)) else "oauth_state_invalid"
        )
        raise HTTPException(status_code=422, detail={"code": code_value}) from error
    return RedirectResponse(get_settings().gmail_post_connect_redirect_uri, status_code=303)


@router.post("/connections/{connection_id}/manifest/discover", response_model=GmailPilotManifestRead)
def discover_manifest(
    connection_id: UUID,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
    provider: GmailSourceProvider = Depends(gmail_provider),
    store: GmailSecretStore = Depends(gmail_secret_store),
) -> GmailPilotManifestRead:
    current = _operator(envelope)
    connection = _connection(db, current, connection_id)
    if connection.provider_kind != "google" or connection.state not in {"ready", "succeeded"}:
        raise HTTPException(status_code=409, detail={"code": "connection_not_ready"})
    clock = datetime.now(timezone.utc)
    metadata = provider.discover_message_metadata(
        provider_account_id=connection.provider_account_id,
        label_id=connection.label_id,
        query=connection.query,
        credential_secret_ref=connection.credential_secret_ref,
        window_start=clock - timedelta(days=30),
        window_end=clock,
        limit=10,
    )
    if len(metadata) != 10:
        raise HTTPException(status_code=409, detail={"code": "pilot_manifest_requires_exactly_10"})
    credential = store.get(connection.credential_secret_ref)
    hmac_key = secrets.token_bytes(32)
    entries = [
        {
            "handle": hmac.new(hmac_key, item.message_id.encode("utf-8"), hashlib.sha256).hexdigest(),
            "received_at": item.received_at.isoformat(),
        }
        for item in metadata
    ]
    credential["pilot_manifest_message_ids"] = [item.message_id for item in metadata]
    credential["pilot_manifest_hmac_key"] = hmac_key.hex()
    key = connection.credential_secret_ref.split("/netpay-gmail/", 1)[-1]
    store.put(key, credential)
    connection.manifest_status = "discovered"
    connection.manifest_entries = entries
    connection.manifest_approved_at = None
    db.commit()
    return GmailPilotManifestRead(
        connection_id=connection.id,
        status=connection.manifest_status,
        entries=connection.manifest_entries,
        approved_at=None,
    )


@router.post("/connections/{connection_id}/manifest/approve", response_model=GmailPilotManifestRead)
def approve_manifest(
    connection_id: UUID,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> GmailPilotManifestRead:
    current = _operator(envelope)
    connection = _connection(db, current, connection_id)
    if connection.manifest_status != "discovered" or len(connection.manifest_entries) != 10:
        raise HTTPException(status_code=409, detail={"code": "manifest_not_ready"})
    connection.manifest_status = "approved"
    connection.manifest_approved_at = datetime.now(timezone.utc)
    db.commit()
    return GmailPilotManifestRead(
        connection_id=connection.id,
        status=connection.manifest_status,
        entries=connection.manifest_entries,
        approved_at=connection.manifest_approved_at,
    )


def _candidate_read(db: Session, candidate: NetpayIntakeCandidate) -> GmailCandidateRead:
    clock = datetime.now(timezone.utc)
    received = candidate.received_at.astimezone(timezone.utc)
    age_days = max(0, (clock.date() - received.date()).days)
    related: list[UUID] = []
    if candidate.correlation_key:
        related = list(
            db.scalars(
                select(NetpayIntakeCandidate.id).where(
                    NetpayIntakeCandidate.organization_id == candidate.organization_id,
                    NetpayIntakeCandidate.correlation_key == candidate.correlation_key,
                    NetpayIntakeCandidate.id != candidate.id,
                )
            ).all()
        )
    return GmailCandidateRead.model_validate(candidate).model_copy(
        update={
            "age_days": age_days,
            "overdue": bool(candidate.follow_up_at and candidate.follow_up_at < clock and not candidate.immutable),
            "related_candidate_ids": related,
        }
    )


@router.get("/candidates", response_model=GmailCandidatePage)
def list_candidates(
    state: str | None = None,
    overdue: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> GmailCandidatePage:
    current = _viewer(envelope)
    stmt = select(NetpayIntakeCandidate).where(NetpayIntakeCandidate.organization_id == current.organization_id)
    if state:
        stmt = stmt.where(NetpayIntakeCandidate.state == state)
    if overdue is True:
        stmt = stmt.where(
            NetpayIntakeCandidate.follow_up_at < datetime.now(timezone.utc), NetpayIntakeCandidate.immutable.is_(False)
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(NetpayIntakeCandidate.priority, NetpayIntakeCandidate.received_at, NetpayIntakeCandidate.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return GmailCandidatePage(
        items=[_candidate_read(db, item) for item in items],
        offset=offset,
        limit=limit,
        total=total,
    )


@router.get("/candidates/{candidate_id}", response_model=GmailCandidateRead)
def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> GmailCandidateRead:
    current = _viewer(envelope)
    candidate = db.scalar(
        select(NetpayIntakeCandidate).where(
            NetpayIntakeCandidate.id == candidate_id,
            NetpayIntakeCandidate.organization_id == current.organization_id,
        )
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="not found")
    return _candidate_read(db, candidate)


@router.get("/candidates/{candidate_id}/follow-ups", response_model=CandidateHumanFollowUpPage)
def list_candidate_follow_ups(
    candidate_id: UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> CandidateHumanFollowUpPage:
    current = _viewer(envelope)
    candidate = db.scalar(
        select(NetpayIntakeCandidate.id).where(
            NetpayIntakeCandidate.id == candidate_id, NetpayIntakeCandidate.organization_id == current.organization_id
        )
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="not found")
    scoped = select(NetpayCandidateHumanFollowUp).where(
        NetpayCandidateHumanFollowUp.organization_id == current.organization_id,
        NetpayCandidateHumanFollowUp.candidate_id == candidate_id,
    )
    total = db.scalar(select(func.count()).select_from(scoped.subquery())) or 0
    items = db.scalars(
        scoped.order_by(NetpayCandidateHumanFollowUp.recorded_at, NetpayCandidateHumanFollowUp.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return CandidateHumanFollowUpPage(
        items=[CandidateHumanFollowUpRead.model_validate(item, from_attributes=True) for item in items],
        offset=offset,
        limit=limit,
        total=total,
    )


@router.post(
    "/candidates/{candidate_id}/follow-ups",
    response_model=CandidateHumanFollowUpRead,
    status_code=status.HTTP_201_CREATED,
)
def record_candidate_follow_up(
    candidate_id: UUID,
    payload: CandidateHumanFollowUpCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> dict:
    current = _operator(envelope)
    candidate = db.scalar(
        select(NetpayIntakeCandidate).where(
            NetpayIntakeCandidate.id == candidate_id, NetpayIntakeCandidate.organization_id == current.organization_id
        )
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="not found")
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="idempotency key required")
    command = "IC-NETPAY-CMD-037"
    request_payload = payload.model_dump()
    replay = _receipt(db, current, command=command, key=key, target=candidate_id, payload=request_payload)
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    follow_up = NetpayCandidateHumanFollowUp(
        organization_id=current.organization_id,
        candidate_id=candidate.id,
        kind=payload.kind,
        note=payload.note.strip(),
        provenance_kind="operator_reported",
        occurred_at=payload.occurred_at,
        created_by_principal_id=current.principal_id,
        correlation_id=_correlation(current),
    )
    if not follow_up.note:
        raise HTTPException(status_code=422, detail="note must not be blank")
    db.add(follow_up)
    db.flush()
    body = CandidateHumanFollowUpRead.model_validate(follow_up).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command=command,
        key=key,
        target=candidate_id,
        payload=request_payload,
        resource_id=follow_up.id,
        status_code=201,
        response_body=body,
    )
    record_event(
        db,
        event_type="netpay.candidate_human_follow_up_recorded",
        aggregate_type="netpay_intake_candidate",
        aggregate_id=candidate.id,
        organization_id=current.organization_id,
        correlation_id=follow_up.correlation_id,
        causation_id=follow_up.id,
        payload={
            "follow_up_id": str(follow_up.id),
            "candidate_id": str(candidate.id),
            "kind": follow_up.kind,
            "actor_principal_id": str(current.principal_id),
            "occurred_at_present": follow_up.occurred_at is not None,
        },
    )
    db.commit()
    return body


def _scoped_candidate(db: Session, current: IdentityAuthorityEnvelope, candidate_id: UUID) -> NetpayIntakeCandidate:
    item = db.scalar(
        select(NetpayIntakeCandidate).where(
            NetpayIntakeCandidate.id == candidate_id, NetpayIntakeCandidate.organization_id == current.organization_id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return item


@router.get("/candidates/{candidate_id}/qualifications", response_model=list[CandidateQualificationRead])
def list_candidate_qualifications(
    candidate_id: UUID, db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)
):
    current = _viewer(envelope)
    _scoped_candidate(db, current, candidate_id)
    return db.scalars(
        select(NetpayCandidateQualification)
        .where(
            NetpayCandidateQualification.organization_id == current.organization_id,
            NetpayCandidateQualification.candidate_id == candidate_id,
        )
        .order_by(NetpayCandidateQualification.sequence)
    ).all()


@router.post("/candidates/{candidate_id}/qualifications", response_model=CandidateQualificationRead, status_code=201)
def create_candidate_qualification(
    candidate_id: UUID,
    payload: CandidateQualificationWrite,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
):
    current = _operator(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    data = payload.model_dump(mode="json")
    if any(product not in {"tpv", "ecommerce"} for product in data["requested_products"]):
        raise HTTPException(422, "unsupported product")
    if len({branch["draft_key"] for branch in data["branches"]}) != len(data["branches"]):
        raise HTTPException(422, "duplicate branch draft key")
    replay = _receipt(
        db, current, command="IC-NETPAY-CMD-038", key=idempotency_key.strip(), target=candidate_id, payload=data
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    sequence = (
        db.scalar(
            select(func.max(NetpayCandidateQualification.sequence)).where(
                NetpayCandidateQualification.candidate_id == candidate_id
            )
        )
        or 0
    ) + 1
    item = NetpayCandidateQualification(
        organization_id=current.organization_id,
        candidate_id=candidate.id,
        sequence=sequence,
        payload=data,
        provenance_kind="operator_reported",
        created_by_principal_id=current.principal_id,
        correlation_id=_correlation(current),
    )
    db.add(item)
    db.flush()
    body = CandidateQualificationRead.model_validate(item).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-038",
        key=idempotency_key.strip(),
        target=candidate_id,
        payload=data,
        resource_id=item.id,
        status_code=201,
        response_body=body,
    )
    record_event(
        db,
        event_type="netpay.candidate_qualification_corrected",
        aggregate_type="netpay_intake_candidate",
        aggregate_id=candidate.id,
        organization_id=current.organization_id,
        correlation_id=item.correlation_id,
        causation_id=item.id,
        payload={
            "qualification_id": str(item.id),
            "sequence": sequence,
            "branch_count": len(data["branches"]),
            "actor_principal_id": str(current.principal_id),
        },
    )
    db.commit()
    return body


@router.get("/candidates/{candidate_id}/commercial-intake-preview")
def preview_candidate_commercial_intake(
    candidate_id: UUID, db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)
):
    current = _viewer(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    qualification = db.scalar(
        select(NetpayCandidateQualification)
        .where(
            NetpayCandidateQualification.organization_id == current.organization_id,
            NetpayCandidateQualification.candidate_id == candidate_id,
        )
        .order_by(NetpayCandidateQualification.sequence.desc())
    )
    if qualification is None:
        raise HTTPException(409, "qualification required")
    p = qualification.payload
    products = p["requested_products"]
    trace = db.scalar(
        select(NetpayCandidateCommercialIntakeTrace).where(
            NetpayCandidateCommercialIntakeTrace.organization_id == current.organization_id,
            NetpayCandidateCommercialIntakeTrace.candidate_id == candidate_id,
        )
    )
    intake = (
        db.scalar(
            select(CommercialIntakeItem).where(
                CommercialIntakeItem.id == trace.commercial_intake_id,
                CommercialIntakeItem.organization_id == current.organization_id,
            )
        )
        if trace is not None
        else None
    )

    def val(name):
        return (p.get(name) or {}).get("value")

    return {
        "candidate_id": str(candidate.id),
        "qualification_id": str(qualification.id),
        "provisional_company_name": val("brand_name") or val("legal_person_name"),
        "provisional_contact_name": val("representative_name"),
        "product_interest": "mixed" if len(products) > 1 else products[0],
        "summary": candidate.description,
        "priority": candidate.priority,
        "next_action": candidate.suggested_next_action,
        "branches": p["branches"],
        "provenance": {"source": "message_observed", "qualification": "operator_reported"},
        "unresolved": [key for key in ("legal_person_name", "brand_name") if not p.get(key)],
        "promotion_trace": (
            {
                "id": str(trace.id),
                "qualification_id": str(trace.qualification_id),
                "commercial_intake_id": str(trace.commercial_intake_id),
                "branch_drafts": trace.branch_drafts,
                "created_at": trace.created_at,
            }
            if trace is not None
            else None
        ),
        "existing_intake": (
            {
                "id": str(intake.id),
                "provisional_company_name": intake.provisional_company_name,
                "provisional_contact_name": intake.provisional_contact_name,
                "product_interest": intake.product_interest,
                "summary": intake.summary,
                "priority": intake.priority,
                "next_action": intake.next_action,
                "status": intake.status,
            }
            if intake is not None
            else None
        ),
    }


@router.post("/candidates/{candidate_id}/commercial-intake", status_code=201)
def promote_candidate(
    candidate_id: UUID,
    payload: CandidateCommercialIntakeCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
):
    current = _operator(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    data = payload.model_dump(mode="json")
    qualification = db.scalar(
        select(NetpayCandidateQualification).where(
            NetpayCandidateQualification.id == payload.qualification_id,
            NetpayCandidateQualification.candidate_id == candidate_id,
            NetpayCandidateQualification.organization_id == current.organization_id,
        )
    )
    if qualification is None:
        raise HTTPException(404, "qualification not found")
    replay = _receipt(
        db, current, command="IC-NETPAY-CMD-039", key=idempotency_key.strip(), target=candidate_id, payload=data
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    existing = db.scalar(
        select(NetpayCandidateCommercialIntakeTrace).where(
            NetpayCandidateCommercialIntakeTrace.organization_id == current.organization_id,
            NetpayCandidateCommercialIntakeTrace.candidate_id == candidate_id,
        )
    )
    if existing is not None:
        raise HTTPException(409, "candidate already promoted")
    draft = CommercialIntakeDraft(
        kind="commercial_opportunity",
        channel="email",
        received_at=candidate.received_at,
        provisional_company_name=payload.provisional_company_name,
        provisional_contact_name=payload.provisional_contact_name,
        product_interest=payload.product_interest,
        summary=payload.summary,
        priority=payload.priority,
        assignee_principal_id=None,
        assign_to_self=False,
        next_action=payload.next_action,
        due_date=None,
    )
    try:
        with db.begin_nested():
            _, owner_body = execute_create_commercial_intake(
                db, current, f"gmail-candidate:{candidate.id}", draft
            )
            trace = NetpayCandidateCommercialIntakeTrace(
                organization_id=current.organization_id,
                candidate_id=candidate.id,
                qualification_id=qualification.id,
                commercial_intake_id=UUID(owner_body["id"]),
                branch_drafts=qualification.payload["branches"],
                created_by_principal_id=current.principal_id,
                correlation_id=_correlation(current),
            )
            db.add(trace)
            db.flush()
            body = {
                "trace_id": str(trace.id),
                "candidate_id": str(candidate.id),
                "qualification_id": str(qualification.id),
                "commercial_intake_id": str(trace.commercial_intake_id),
                "branch_drafts": trace.branch_drafts,
            }
            _store_receipt(
                db, current, command="IC-NETPAY-CMD-039", key=idempotency_key.strip(),
                target=candidate_id, payload=data, resource_id=trace.id, status_code=201,
                response_body=body,
            )
            record_event(
                db,
                event_type="netpay.candidate_promoted_to_commercial_intake",
                aggregate_type="netpay_intake_candidate",
                aggregate_id=candidate.id,
                organization_id=current.organization_id,
                correlation_id=trace.correlation_id,
                causation_id=trace.id,
                payload={"trace_id": str(trace.id), "commercial_intake_id": str(trace.commercial_intake_id)},
            )
            db.flush()
    except IntegrityError as error:
        collision_constraints = {
            "uq_netpay_candidate_commercial_intake_trace",
            "uq_netpay_gmail_receipts_org_command_key",
            "uq_netpay_commercial_intake_receipts_org_command_key",
        }
        if not isinstance(error.orig, UniqueViolation) or error.orig.diag.constraint_name not in collision_constraints:
            raise
        # The savepoint has rolled back all owner and candidate effects. PostgreSQL's
        # unique check waits for the winning transaction, so a new READ COMMITTED
        # statement can now distinguish its receipt from a competing key.
        winning_receipt = db.scalar(
            select(NetpayGmailCommandReceipt).where(
                NetpayGmailCommandReceipt.organization_id == current.organization_id,
                NetpayGmailCommandReceipt.command_type == "IC-NETPAY-CMD-039",
                NetpayGmailCommandReceipt.idempotency_key == idempotency_key.strip(),
            )
        )
        if winning_receipt is not None:
            if winning_receipt.request_fingerprint != _fingerprint("IC-NETPAY-CMD-039", candidate_id, data):
                raise HTTPException(409, "idempotency conflict") from error
            response.status_code = winning_receipt.result_status_code
            return winning_receipt.result_response_body
        winning_trace = db.scalar(
            select(NetpayCandidateCommercialIntakeTrace).where(
                NetpayCandidateCommercialIntakeTrace.organization_id == current.organization_id,
                NetpayCandidateCommercialIntakeTrace.candidate_id == candidate_id,
            )
        )
        if winning_trace is None:
            raise
        raise HTTPException(409, "candidate already promoted") from error
    db.commit()
    return body


def _dossier_read(db: Session, dossier: NetpayCandidateOnboardingDossier) -> dict:
    reviews = db.scalars(
        select(NetpayDossierRequirementReview)
        .where(
            NetpayDossierRequirementReview.organization_id == dossier.organization_id,
            NetpayDossierRequirementReview.dossier_id == dossier.id,
        )
        .order_by(NetpayDossierRequirementReview.sequence, NetpayDossierRequirementReview.id)
    ).all()
    evidence_ids = {item.evidence_reference_id for item in reviews if item.evidence_reference_id is not None}
    evidence = (
        {
            item.id: item
            for item in db.scalars(
                select(NetpayDossierEvidenceReference).where(
                    NetpayDossierEvidenceReference.organization_id == dossier.organization_id,
                    NetpayDossierEvidenceReference.dossier_id == dossier.id,
                    NetpayDossierEvidenceReference.id.in_(evidence_ids),
                )
            ).all()
        }
        if evidence_ids
        else {}
    )

    def evidence_read(reference_id: UUID | None) -> dict | None:
        item = evidence.get(reference_id) if reference_id is not None else None
        if item is None:
            return None
        return {
            "id": str(item.id),
            "source_item_id": str(item.source_item_id),
            "attachment_index": item.attachment_index,
            "metadata": item.metadata_snapshot,
            "suggestion": item.suggestion,
            "verification": item.verification,
        }
    by_key: dict[str, list[NetpayDossierRequirementReview]] = {}
    for item in reviews:
        by_key.setdefault(item.requirement_snapshot_key, []).append(item)
    requirements = []
    blockers = []
    state_counts = {
        state: 0
        for state in ("pending", "attachment_detected", "under_review", "validated", "observed", "not_applicable")
    }
    for definition in dossier.requirement_snapshot["requirements"]:
        history = by_key.get(definition["snapshot_key"], [])
        state = history[-1].state if history else "pending"
        state_counts[state] += 1
        if definition.get("required", True) and state not in {"validated", "not_applicable"}:
            blockers.append({"snapshot_key": definition["snapshot_key"], "label": definition["label"], "state": state})
        requirements.append(
            {
                **definition,
                "state": state,
                "history": [
                    {
                        "id": str(review.id),
                        "sequence": review.sequence,
                        "prior_state": review.prior_state,
                        "state": review.state,
                        "review_data": review.review_data,
                        "comment": review.comment,
                        "provenance_kind": review.provenance_kind,
                        "recorded_at": review.recorded_at.isoformat(),
                        "created_by_principal_id": str(review.created_by_principal_id),
                        "evidence": evidence_read(review.evidence_reference_id),
                    }
                    for review in history
                ],
            }
        )
    return {
        "id": str(dossier.id),
        "candidate_id": str(dossier.candidate_id),
        "commercial_intake_id": str(dossier.commercial_intake_id),
        "qualification_id": str(dossier.qualification_id),
        "catalog_version": dossier.catalog_version,
        "catalog_effective_date": dossier.catalog_effective_date,
        "catalog_sha256": dossier.catalog_sha256,
        "catalog_owner": dossier.catalog_owner,
        "applicant_kind": dossier.applicant_kind,
        "products": dossier.products,
        "branches": dossier.branch_snapshot,
        "created_at": dossier.created_at.isoformat(),
        "created_by_principal_id": str(dossier.created_by_principal_id),
        "requirements": requirements,
        "state_counts": state_counts,
        "blockers": blockers,
        "complete": not blockers,
        "history_count": len(reviews),
    }


@router.get("/candidates/{candidate_id}/dossier-preview")
def preview_candidate_dossier(
    candidate_id: UUID, db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)
):
    current = _viewer(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    existing = db.scalar(
        select(NetpayCandidateOnboardingDossier).where(
            NetpayCandidateOnboardingDossier.organization_id == current.organization_id,
            NetpayCandidateOnboardingDossier.candidate_id == candidate.id,
        )
    )
    if existing is not None:
        return {"existing": True, "dossier": _dossier_read(db, existing)}
    trace = db.scalar(
        select(NetpayCandidateCommercialIntakeTrace).where(
            NetpayCandidateCommercialIntakeTrace.organization_id == current.organization_id,
            NetpayCandidateCommercialIntakeTrace.candidate_id == candidate.id,
        )
    )
    if trace is None:
        raise HTTPException(409, "promotion trace required")
    qualification = db.scalar(
        select(NetpayCandidateQualification).where(
            NetpayCandidateQualification.id == trace.qualification_id,
            NetpayCandidateQualification.organization_id == current.organization_id,
        )
    )
    intake = db.scalar(
        select(CommercialIntakeItem).where(
            CommercialIntakeItem.id == trace.commercial_intake_id,
            CommercialIntakeItem.organization_id == current.organization_id,
        )
    )
    if qualification is None or intake is None:
        raise HTTPException(409, "promotion owner readback required")
    q = qualification.payload
    try:
        snapshot = build_catalog_snapshot(
            applicant_kind=q["applicant_kind"], products=q["requested_products"], branches=trace.branch_drafts
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        "existing": False,
        "candidate_id": str(candidate.id),
        "commercial_intake_id": str(intake.id),
        "qualification_id": str(qualification.id),
        "candidate_terminal": candidate.immutable,
        "candidate_state": candidate.state,
        "catalog_version": CATALOG_VERSION,
        "catalog_effective_date": CATALOG_EFFECTIVE_DATE,
        "catalog_sha256": CATALOG_SHA256,
        "catalog_owner": CATALOG_OWNER,
        "applicant_kind": q["applicant_kind"],
        "products": snapshot["products"],
        "branches": trace.branch_drafts,
        "requirements": [{**item, "state": "pending"} for item in snapshot["requirements"]],
        "blocker_count": sum(1 for item in snapshot["requirements"] if item.get("required", True)),
        "excluded": ["ecommerce_without_physical_establishment"],
    }


@router.get("/candidates/{candidate_id}/dossier")
def get_candidate_dossier(
    candidate_id: UUID, db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)
):
    current = _viewer(envelope)
    _scoped_candidate(db, current, candidate_id)
    dossier = db.scalar(
        select(NetpayCandidateOnboardingDossier).where(
            NetpayCandidateOnboardingDossier.organization_id == current.organization_id,
            NetpayCandidateOnboardingDossier.candidate_id == candidate_id,
        )
    )
    if dossier is None:
        raise HTTPException(404, "dossier not found")
    return _dossier_read(db, dossier)


@router.post("/candidates/{candidate_id}/dossier", status_code=201)
def create_candidate_dossier(
    candidate_id: UUID,
    payload: CandidateDossierCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
):
    current = _operator(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    data = payload.model_dump(mode="json")
    replay = _receipt(
        db, current, command="IC-NETPAY-CMD-041", key=idempotency_key.strip(), target=candidate_id, payload=data
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    if not payload.confirmed or payload.catalog_sha256 != CATALOG_SHA256:
        raise HTTPException(422, "exact approved catalog confirmation required")
    trace = db.scalar(
        select(NetpayCandidateCommercialIntakeTrace).where(
            NetpayCandidateCommercialIntakeTrace.organization_id == current.organization_id,
            NetpayCandidateCommercialIntakeTrace.candidate_id == candidate.id,
        )
    )
    if trace is None or trace.qualification_id != payload.qualification_id:
        raise HTTPException(409, "matching promotion trace required")
    if (
        db.scalar(
            select(NetpayCandidateOnboardingDossier.id).where(
                NetpayCandidateOnboardingDossier.organization_id == current.organization_id,
                NetpayCandidateOnboardingDossier.candidate_id == candidate.id,
            )
        )
        is not None
    ):
        raise HTTPException(409, "candidate dossier already exists")
    qualification = db.scalar(
        select(NetpayCandidateQualification).where(
            NetpayCandidateQualification.id == trace.qualification_id,
            NetpayCandidateQualification.organization_id == current.organization_id,
            NetpayCandidateQualification.candidate_id == candidate.id,
        )
    )
    intake = db.scalar(
        select(CommercialIntakeItem).where(
            CommercialIntakeItem.id == trace.commercial_intake_id,
            CommercialIntakeItem.organization_id == current.organization_id,
        )
    )
    if qualification is None or intake is None:
        raise HTTPException(409, "promotion owner readback required")
    q = qualification.payload
    try:
        snapshot = build_catalog_snapshot(
            applicant_kind=q["applicant_kind"], products=q["requested_products"], branches=trace.branch_drafts
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    dossier = NetpayCandidateOnboardingDossier(
        organization_id=current.organization_id,
        candidate_id=candidate.id,
        commercial_intake_id=intake.id,
        qualification_id=qualification.id,
        catalog_version=CATALOG_VERSION,
        catalog_effective_date=CATALOG_EFFECTIVE_DATE,
        catalog_sha256=CATALOG_SHA256,
        catalog_owner=CATALOG_OWNER,
        applicant_kind=q["applicant_kind"],
        products=snapshot["products"],
        branch_snapshot=trace.branch_drafts,
        requirement_snapshot=snapshot,
        created_by_principal_id=current.principal_id,
        correlation_id=_correlation(current),
    )
    db.add(dossier)
    db.flush()
    body = _dossier_read(db, dossier)
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-041",
        key=idempotency_key.strip(),
        target=candidate_id,
        payload=data,
        resource_id=dossier.id,
        status_code=201,
        response_body=body,
    )
    db.commit()
    return body


@router.post("/candidates/{candidate_id}/dossier/reviews", status_code=201)
def review_candidate_dossier_requirement(
    candidate_id: UUID,
    payload: CandidateDossierRequirementReviewWrite,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
):
    current = _operator(envelope)
    candidate = _scoped_candidate(db, current, candidate_id)
    dossier = db.scalar(
        select(NetpayCandidateOnboardingDossier).where(
            NetpayCandidateOnboardingDossier.organization_id == current.organization_id,
            NetpayCandidateOnboardingDossier.candidate_id == candidate.id,
        )
    )
    if dossier is None:
        raise HTTPException(404, "dossier not found")
    data = payload.model_dump(mode="json")
    replay = _receipt(
        db, current, command="IC-NETPAY-CMD-042", key=idempotency_key.strip(), target=dossier.id, payload=data
    )
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    definitions = {item["snapshot_key"]: item for item in dossier.requirement_snapshot["requirements"]}
    if payload.requirement_snapshot_key not in definitions:
        raise HTTPException(422, "requirement not in approved snapshot")
    definition = definitions[payload.requirement_snapshot_key]
    if len(json.dumps(payload.review_data, default=str)) > 4000:
        raise HTTPException(422, "review data too large")
    if payload.state in {"observed", "validated", "not_applicable"} and not (payload.comment or "").strip():
        raise HTTPException(422, "attributed review comment required")
    if payload.state == "attachment_detected" and payload.evidence is None:
        raise HTTPException(422, "metadata evidence reference required")
    review_data = dict(payload.review_data)
    if payload.state == "validated":
        maximum_age_days = definition.get("maximum_age_days")
        if maximum_age_days is not None:
            try:
                document_date = date.fromisoformat(str(review_data["document_date"]))
            except (KeyError, ValueError) as exc:
                raise HTTPException(422, "document date required for validity review") from exc
            review_date = datetime.now(timezone.utc).date()
            age_days = (review_date - document_date).days
            if age_days < 0 or age_days > maximum_age_days:
                raise HTTPException(422, "document outside approved 60-day window")
            review_data.update({"review_date": review_date.isoformat(), "age_days": age_days})
        key = definition["key"]
        if (
            key in {"receiving_account_bank_statement", "tax_status_certificate"}
            and not str(review_data.get("holder") or "").strip()
        ):
            raise HTTPException(422, "reviewed holder required")
        if key == "tax_status_certificate" and review_data.get("holder_correspondence") != "matches":
            raise HTTPException(422, "holder correspondence must be explicitly confirmed")
        if key == "branch_premises_photos":
            try:
                photo_counts = (int(review_data.get("interior_count") or 0), int(review_data.get("facade_count") or 0))
            except (TypeError, ValueError) as exc:
                raise HTTPException(422, "numeric photo counts required") from exc
            if min(photo_counts) < 2:
                raise HTTPException(422, "two interior and two facade photos required per branch")
        if key == "branch_manager_contact":
            shared_review_id = review_data.get("shared_contact_review_id")
            if shared_review_id:
                try:
                    shared_review_uuid = UUID(str(shared_review_id))
                except ValueError as exc:
                    raise HTTPException(422, "invalid shared contact review reference") from exc
                shared_review = db.scalar(
                    select(NetpayDossierRequirementReview).where(
                        NetpayDossierRequirementReview.id == shared_review_uuid,
                        NetpayDossierRequirementReview.organization_id == current.organization_id,
                        NetpayDossierRequirementReview.dossier_id == dossier.id,
                        NetpayDossierRequirementReview.state == "validated",
                    )
                )
                if shared_review is None:
                    raise HTTPException(422, "shared contact review not found in dossier")
                shared_definition = definitions.get(shared_review.requirement_snapshot_key)
                if shared_definition is None or shared_definition.get("key") != "branch_manager_contact":
                    raise HTTPException(422, "shared contact review not found in dossier")
                if any(
                    not str((shared_review.review_data or {}).get(field) or "").strip()
                    for field in ("name", "phone", "email")
                ):
                    raise HTTPException(422, "shared contact review has no reusable contact")
                review_data = {"shared_contact_review_id": str(shared_review.id)}
            elif any(not str(review_data.get(field) or "").strip() for field in ("name", "phone", "email")):
                raise HTTPException(422, "branch manager name, phone and email required")
    evidence_reference = None
    if payload.evidence is not None:
        if payload.evidence.source_item_id != candidate.source_item_id:
            raise HTTPException(404, "source item not found")
        source = db.scalar(
            select(NetpayGmailSourceItem).where(
                NetpayGmailSourceItem.id == payload.evidence.source_item_id,
                NetpayGmailSourceItem.organization_id == current.organization_id,
            )
        )
        if source is None or payload.evidence.attachment_index >= len(source.attachment_metadata):
            raise HTTPException(404, "attachment metadata not found")
        evidence_reference = db.scalar(
            select(NetpayDossierEvidenceReference).where(
                NetpayDossierEvidenceReference.dossier_id == dossier.id,
                NetpayDossierEvidenceReference.source_item_id == source.id,
                NetpayDossierEvidenceReference.attachment_index == payload.evidence.attachment_index,
            )
        )
        if evidence_reference is None:
            raw = source.attachment_metadata[payload.evidence.attachment_index]
            evidence_reference = NetpayDossierEvidenceReference(
                organization_id=current.organization_id,
                dossier_id=dossier.id,
                source_item_id=source.id,
                attachment_index=payload.evidence.attachment_index,
                metadata_snapshot={
                    "filename": raw.get("filename") or raw.get("name"),
                    "mime_type": raw.get("mime_type") or raw.get("type"),
                    "size": raw.get("size"),
                },
                suggestion=payload.evidence.suggestion,
                verification="unverified",
                created_by_principal_id=current.principal_id,
            )
            db.add(evidence_reference)
            db.flush()
    prior = db.scalar(
        select(NetpayDossierRequirementReview)
        .where(
            NetpayDossierRequirementReview.dossier_id == dossier.id,
            NetpayDossierRequirementReview.requirement_snapshot_key == payload.requirement_snapshot_key,
        )
        .order_by(NetpayDossierRequirementReview.sequence.desc())
    )
    sequence = (
        db.scalar(
            select(func.max(NetpayDossierRequirementReview.sequence)).where(
                NetpayDossierRequirementReview.dossier_id == dossier.id
            )
        )
        or 0
    ) + 1
    review = NetpayDossierRequirementReview(
        organization_id=current.organization_id,
        dossier_id=dossier.id,
        sequence=sequence,
        requirement_snapshot_key=payload.requirement_snapshot_key,
        prior_state=prior.state if prior else "pending",
        state=payload.state,
        evidence_reference_id=evidence_reference.id if evidence_reference else None,
        review_data=review_data,
        comment=(payload.comment or "").strip() or None,
        provenance_kind="operator_reported",
        created_by_principal_id=current.principal_id,
        correlation_id=_correlation(current),
    )
    db.add(review)
    db.flush()
    body = _dossier_read(db, dossier)
    _store_receipt(
        db,
        current,
        command="IC-NETPAY-CMD-042",
        key=idempotency_key.strip(),
        target=dossier.id,
        payload=data,
        resource_id=review.id,
        status_code=201,
        response_body=body,
    )
    record_event(
        db,
        event_type="netpay.candidate_dossier_requirement_reviewed",
        aggregate_type="netpay_candidate_onboarding_dossier",
        aggregate_id=dossier.id,
        organization_id=current.organization_id,
        correlation_id=review.correlation_id,
        causation_id=review.id,
        payload={
            "review_id": str(review.id),
            "requirement_snapshot_key": review.requirement_snapshot_key,
            "prior_state": review.prior_state,
            "state": review.state,
            "actor_principal_id": str(current.principal_id),
            "evidence_reference_present": review.evidence_reference_id is not None,
        },
    )
    db.commit()
    return body


@router.post("/candidates/{candidate_id}/review", response_model=GmailCandidateRead)
def review_candidate(
    candidate_id: UUID,
    payload: GmailCandidateReview,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> dict:
    current = _operator(envelope)
    candidate = db.scalar(
        select(NetpayIntakeCandidate).where(
            NetpayIntakeCandidate.id == candidate_id,
            NetpayIntakeCandidate.organization_id == current.organization_id,
        )
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="not found")
    command = {
        "edit": "IC-NETPAY-CMD-018",
        "accept": "IC-NETPAY-CMD-032",
        "reject": "IC-NETPAY-CMD-033",
        "duplicate": "IC-NETPAY-CMD-034",
        "link": "IC-NETPAY-CMD-035",
    }[payload.action]
    key = idempotency_key.strip()
    replay = _receipt(db, current, command=command, key=key, target=candidate_id, payload=payload.model_dump())
    if replay is not None:
        response.status_code = replay.result_status_code
        return replay.result_response_body
    if candidate.immutable:
        raise HTTPException(status_code=409, detail="candidate disposition is immutable")
    if payload.action == "edit":
        if payload.request_type:
            candidate.request_type = payload.request_type
        if payload.priority:
            candidate.priority = payload.priority
        if payload.suggested_next_action is not None:
            candidate.suggested_next_action = payload.suggested_next_action
        if payload.follow_up_at is not None:
            candidate.follow_up_at = payload.follow_up_at
        candidate.state = "needs_review"
    else:
        if payload.action in {"accept", "link"}:
            if payload.owner_type is None or payload.owner_id is None:
                raise HTTPException(status_code=422, detail="owner target required")
            owner = (
                db.scalar(
                    select(NetpayServiceCase).where(
                        NetpayServiceCase.id == payload.owner_id,
                        NetpayServiceCase.organization_id == current.organization_id,
                    )
                )
                if payload.owner_type == "case"
                else db.scalar(
                    select(CommercialIntakeItem).where(
                        CommercialIntakeItem.id == payload.owner_id,
                        CommercialIntakeItem.organization_id == current.organization_id,
                    )
                )
            )
            if owner is None:
                raise HTTPException(status_code=404, detail="owner target not found")
            candidate.owner_type = payload.owner_type
            candidate.owner_id = payload.owner_id
        candidate.state = {"accept": "accepted", "reject": "rejected", "duplicate": "duplicate", "link": "linked"}[
            payload.action
        ]
        candidate.reviewed_by_principal_id = current.principal_id
        candidate.reviewed_at = datetime.now(timezone.utc)
        candidate.disposition_reason = payload.reason
        candidate.immutable = True
    db.flush()
    body = _candidate_read(db, candidate).model_dump(mode="json")
    _store_receipt(
        db,
        current,
        command=command,
        key=key,
        target=candidate_id,
        payload=payload.model_dump(),
        resource_id=candidate.id,
        status_code=200,
        response_body=body,
    )
    record_event(
        db,
        event_type="netpay.gmail.intake_candidate_reviewed",
        aggregate_type="netpay_intake_candidate",
        aggregate_id=candidate.id,
        organization_id=current.organization_id,
        correlation_id=_correlation(current),
        causation_id=candidate.source_item_id,
        payload={"candidate_id": str(candidate.id), "decision": payload.action},
    )
    db.commit()
    return body

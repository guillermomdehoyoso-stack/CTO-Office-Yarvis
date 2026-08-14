"""Tenant-scoped Netpay master APIs; no legacy Netpay case aggregate is reused."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_master_authority import netpay_master_principal_from_envelope
from yarvis_api.database import get_db
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.schemas.netpay_master import BranchRead, BranchWrite, ClientRead, ClientWrite, CompanyRead, CompanyWrite, MasterSearchRead, StoreReferenceRead, StoreReferenceWrite
from yarvis_api.services.netpay_master_receipts import MasterResult, NetpayMasterReceiptService

router = APIRouter(prefix="/netpay/master", tags=["netpay-master"])


def _norm(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold())


def _active_store(db: Session, branch_id: UUID, organization_id: UUID) -> NetpayStoreReference | None:
    return db.scalar(select(NetpayStoreReference).where(NetpayStoreReference.branch_id == branch_id, NetpayStoreReference.organization_id == organization_id, NetpayStoreReference.active.is_(True)))


def _branch_read(db: Session, branch: NetpayBranch) -> BranchRead:
    return BranchRead.model_validate(branch).model_copy(update={"store_reference": _active_store(db, branch.id, branch.organization_id)})


def _company_read(db: Session, company: NetpayCompany, *, detail: bool) -> CompanyRead:
    branches = db.scalars(select(NetpayBranch).where(NetpayBranch.company_id == company.id, NetpayBranch.organization_id == company.organization_id).order_by(NetpayBranch.commercial_name, NetpayBranch.id)).all() if detail else []
    return CompanyRead.model_validate(company).model_copy(update={"branches": [_branch_read(db, branch) for branch in branches]})


def _client_read(db: Session, client: NetpayClient, *, detail: bool) -> ClientRead:
    companies = db.scalars(select(NetpayCompany).where(NetpayCompany.client_id == client.id, NetpayCompany.organization_id == client.organization_id).order_by(NetpayCompany.legal_name, NetpayCompany.id)).all() if detail else []
    return ClientRead.model_validate(client).model_copy(update={"companies": [_company_read(db, item, detail=True) for item in companies]})


def _operator(envelope: IdentityAuthorityEnvelope) -> None:
    netpay_master_principal_from_envelope(envelope, required_scope="netpay.master.manage")


def _viewer(envelope: IdentityAuthorityEnvelope) -> None:
    netpay_master_principal_from_envelope(envelope, required_scope="netpay.master.read")


def _execute(db: Session, envelope: IdentityAuthorityEnvelope, key: str, command: str, payload: dict, mutation, *, target_id: UUID | None = None) -> MasterResult:
    try:
        result = NetpayMasterReceiptService().execute(db, resolve_authority=lambda: _operator(envelope) or envelope, command_type=command, idempotency_key=key, payload=payload, mutation=mutation, target_id=target_id)
        db.commit()
        return result
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="conflict") from error


@router.post("/clients", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientWrite, response: Response, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    functional = payload.model_dump(mode="python")
    def mutation(command_id, correlation_id, current):
        normal = _norm(payload.display_name)
        duplicate = db.scalar(select(NetpayClient).where(NetpayClient.organization_id == current.organization_id, NetpayClient.normalized_name == normal, NetpayClient.primary_email == payload.primary_email, NetpayClient.primary_phone == payload.primary_phone))
        if duplicate: raise HTTPException(status_code=409, detail="duplicate client")
        client = NetpayClient(organization_id=current.organization_id, display_name=payload.display_name.strip(), normalized_name=normal, external_reference=payload.external_reference, primary_contact_name=payload.primary_contact_name, primary_email=payload.primary_email, primary_phone=payload.primary_phone, created_by_principal_id=current.principal_id, updated_by_principal_id=current.principal_id)
        db.add(client); db.flush()
        return MasterResult("netpay_client", client.id, status.HTTP_201_CREATED)
    result = _execute(db, envelope, idempotency_key, "IC-NETPAY-CMD-005", functional, mutation)
    client = db.scalar(select(NetpayClient).where(NetpayClient.id == result.resource_id, NetpayClient.organization_id == envelope.organization_id))
    if not client: raise HTTPException(status_code=404, detail="not found")
    response.status_code = result.status_code
    return _client_read(db, client, detail=False)


@router.post("/clients/{client_id}/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(client_id: UUID, payload: CompanyWrite, response: Response, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    def mutation(command_id, correlation_id, current):
        client = db.scalar(select(NetpayClient).where(NetpayClient.id == client_id, NetpayClient.organization_id == current.organization_id))
        if not client: raise HTTPException(status_code=404, detail="not found")
        tax = _norm(payload.tax_identifier) or None
        if tax and db.scalar(select(NetpayCompany).where(NetpayCompany.organization_id == current.organization_id, NetpayCompany.tax_identifier == tax)):
            raise HTTPException(status_code=409, detail="duplicate tax identifier")
        company = NetpayCompany(organization_id=current.organization_id, client_id=client.id, legal_name=payload.legal_name.strip(), normalized_legal_name=_norm(payload.legal_name), tax_identifier=tax, legal_address=payload.legal_address, contact_name=payload.contact_name, contact_email=payload.contact_email, contact_phone=payload.contact_phone, created_by_principal_id=current.principal_id, updated_by_principal_id=current.principal_id)
        db.add(company); db.flush()
        return MasterResult("netpay_company", company.id, status.HTTP_201_CREATED)
    result = _execute(db, envelope, idempotency_key, "IC-NETPAY-CMD-006", payload.model_dump(mode="python"), mutation, target_id=client_id)
    company = db.scalar(select(NetpayCompany).where(NetpayCompany.id == result.resource_id, NetpayCompany.organization_id == envelope.organization_id))
    if not company: raise HTTPException(status_code=404, detail="not found")
    response.status_code = result.status_code
    return _company_read(db, company, detail=False)


@router.post("/companies/{company_id}/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(company_id: UUID, payload: BranchWrite, response: Response, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    def mutation(command_id, correlation_id, current):
        company = db.scalar(select(NetpayCompany).where(NetpayCompany.id == company_id, NetpayCompany.organization_id == current.organization_id))
        if not company: raise HTTPException(status_code=404, detail="not found")
        key = "|".join((_norm(payload.commercial_name), _norm(payload.address), _norm(payload.locality), _norm(payload.postal_code)))
        if db.scalar(select(NetpayBranch).where(NetpayBranch.organization_id == current.organization_id, NetpayBranch.company_id == company.id, NetpayBranch.branch_match_key == key)):
            raise HTTPException(status_code=409, detail="duplicate branch")
        branch = NetpayBranch(organization_id=current.organization_id, company_id=company.id, commercial_name=payload.commercial_name.strip(), normalized_commercial_name=_norm(payload.commercial_name), branch_match_key=key, branch_kind=payload.branch_kind, address=payload.address, locality=payload.locality, state=payload.state, postal_code=payload.postal_code, contact_name=payload.contact_name, contact_email=payload.contact_email, contact_phone=payload.contact_phone, created_by_principal_id=current.principal_id, updated_by_principal_id=current.principal_id)
        db.add(branch); db.flush()
        return MasterResult("netpay_branch", branch.id, status.HTTP_201_CREATED)
    result = _execute(db, envelope, idempotency_key, "IC-NETPAY-CMD-007", payload.model_dump(mode="python"), mutation, target_id=company_id)
    branch = db.scalar(select(NetpayBranch).where(NetpayBranch.id == result.resource_id, NetpayBranch.organization_id == envelope.organization_id))
    if not branch: raise HTTPException(status_code=404, detail="not found")
    response.status_code = result.status_code
    return _branch_read(db, branch)


@router.put("/branches/{branch_id}/store-reference", response_model=StoreReferenceRead, status_code=status.HTTP_201_CREATED)
def assign_or_correct_store_reference(branch_id: UUID, payload: StoreReferenceWrite, response: Response, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    def mutation(command_id, correlation_id, current):
        branch = db.scalar(select(NetpayBranch).where(NetpayBranch.id == branch_id, NetpayBranch.organization_id == current.organization_id))
        if not branch: raise HTTPException(status_code=404, detail="not found")
        normal = _norm(payload.store_id)
        other = db.scalar(select(NetpayStoreReference).where(NetpayStoreReference.organization_id == current.organization_id, NetpayStoreReference.normalized_store_id == normal, NetpayStoreReference.active.is_(True), NetpayStoreReference.branch_id != branch.id))
        if other: raise HTTPException(status_code=409, detail="store id already assigned")
        reference = _active_store(db, branch.id, current.organization_id)
        now = datetime.now(timezone.utc)
        if reference is None:
            reference = NetpayStoreReference(organization_id=current.organization_id, branch_id=branch.id, store_id=payload.store_id.strip(), normalized_store_id=normal, source_type=payload.source_type.strip(), source_reference=payload.source_reference, confirmed_at=now if payload.confirmed else None, confirmed_by_principal_id=current.principal_id if payload.confirmed else None, created_by_principal_id=current.principal_id, updated_by_principal_id=current.principal_id)
            db.add(reference)
        else:
            reference.store_id, reference.normalized_store_id, reference.source_type, reference.source_reference, reference.updated_by_principal_id = payload.store_id.strip(), normal, payload.source_type.strip(), payload.source_reference, current.principal_id
            if payload.confirmed: reference.confirmed_at, reference.confirmed_by_principal_id = now, current.principal_id
        db.flush()
        return MasterResult("netpay_store_reference", reference.id, status.HTTP_201_CREATED)
    result = _execute(db, envelope, idempotency_key, "IC-NETPAY-CMD-008", payload.model_dump(mode="python"), mutation, target_id=branch_id)
    reference = db.scalar(select(NetpayStoreReference).where(NetpayStoreReference.id == result.resource_id, NetpayStoreReference.organization_id == envelope.organization_id))
    if not reference: raise HTTPException(status_code=404, detail="not found")
    response.status_code = result.status_code
    return StoreReferenceRead.model_validate(reference)


@router.delete("/branches/{branch_id}/store-reference", status_code=status.HTTP_204_NO_CONTENT)
def remove_store_reference(branch_id: UUID, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    def mutation(command_id, correlation_id, current):
        branch = db.scalar(select(NetpayBranch).where(NetpayBranch.id == branch_id, NetpayBranch.organization_id == current.organization_id))
        if not branch: raise HTTPException(status_code=404, detail="not found")
        reference = _active_store(db, branch.id, current.organization_id)
        if not reference: raise HTTPException(status_code=404, detail="not found")
        reference.active, reference.removed_at, reference.updated_by_principal_id = False, datetime.now(timezone.utc), current.principal_id
        return MasterResult("netpay_branch", branch.id, status.HTTP_204_NO_CONTENT)
    _execute(db, envelope, idempotency_key, "IC-NETPAY-CMD-008", {"operation": "remove"}, mutation, target_id=branch_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=MasterSearchRead)
def list_search_master(query: str | None = Query(default=None, max_length=255), offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    _viewer(envelope)
    statement = select(NetpayClient).where(NetpayClient.organization_id == envelope.organization_id)
    if query:
        value = f"%{query.strip()}%"
        statement = statement.where(or_(NetpayClient.display_name.ilike(value), NetpayClient.external_reference.ilike(value)))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    clients = db.scalars(statement.order_by(NetpayClient.display_name, NetpayClient.id).offset(offset).limit(limit)).all()
    return MasterSearchRead(items=[_client_read(db, item, detail=False) for item in clients], offset=offset, limit=limit, total=total)


@router.get("/branches/{branch_id}", response_model=ClientRead)
def retrieve_master_detail(branch_id: UUID, db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)):
    _viewer(envelope)
    branch = db.scalar(select(NetpayBranch).where(NetpayBranch.id == branch_id, NetpayBranch.organization_id == envelope.organization_id))
    if not branch: raise HTTPException(status_code=404, detail="not found")
    company = db.scalar(select(NetpayCompany).where(NetpayCompany.id == branch.company_id, NetpayCompany.organization_id == envelope.organization_id))
    client = db.scalar(select(NetpayClient).where(NetpayClient.id == company.client_id, NetpayClient.organization_id == envelope.organization_id)) if company else None
    if not client: raise HTTPException(status_code=404, detail="not found")
    return _client_read(db, client, detail=True)

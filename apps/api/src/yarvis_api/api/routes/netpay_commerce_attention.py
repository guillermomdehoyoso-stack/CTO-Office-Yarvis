"""Read-only HTTP boundary for QRY-023 and QRY-024."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from yarvis_api.api.dependencies.authority import authority_envelope
from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.netpay_portfolio_authority import (
    PORTFOLIO_READ,
    PORTFOLIO_RECONCILIATION_READ,
    PORTFOLIO_SENSITIVE_READ,
    netpay_portfolio_envelope,
)
from yarvis_api.database import get_db
from yarvis_api.schemas.netpay_commerce_attention import PortfolioDetail, PortfolioPage, ReconciliationPage
from yarvis_api.services.netpay_commerce_attention import NetpayCommerceAttentionService, PortfolioFilters

router = APIRouter(prefix="/netpay/commerce-attention", tags=["netpay-commerce-attention"])


@router.get("", response_model=PortfolioPage)
def list_portfolio(
    reporting_period: str | None = Query(None, pattern=r"^20\d{2}-(0[1-9]|1[0-2])$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=255),
    entity_scopes: list[Literal["client", "company", "branch"]] = Query(default=[]),
    reconciliation_statuses: list[
        Literal["exact_match", "human_confirmed", "probable_match", "conflict", "unreconciled"]
    ] = Query(default=[]),
    has_company: bool | None = None,
    has_branch: bool | None = None,
    has_store_reference: bool | None = None,
    has_contact: bool | None = None,
    sort_field: Literal[
        "commerce", "legal_name", "branch_name", "store_id", "reconciliation_status", "updated_at"
    ] = "commerce",
    sort_direction: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> PortfolioPage:
    current = netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_READ)
    return NetpayCommerceAttentionService(db, current.organization_id, reporting_period).list(
        PortfolioFilters(
            search,
            tuple(entity_scopes),
            tuple(reconciliation_statuses),
            has_company,
            has_branch,
            has_store_reference,
            has_contact,
            sort_field,
            sort_direction,
            page,
            page_size,
        ),
        include_reconciliation_count=PORTFOLIO_RECONCILIATION_READ in current.validated_permissions,
    )


@router.get("/reconciliation", response_model=ReconciliationPage)
def list_reconciliation(
    db: Session = Depends(get_db), envelope: IdentityAuthorityEnvelope = Depends(authority_envelope)
) -> ReconciliationPage:
    current = netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_RECONCILIATION_READ)
    return NetpayCommerceAttentionService(db, current.organization_id).reconciliation()


@router.get("/settlements")
def list_settlements(
    reporting_period: str | None = Query(None, pattern=r"^20\d{2}-(0[1-9]|1[0-2])$"),
    include_details: bool = False,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
):
    from yarvis_api.services.netpay_commission_reconciliation import settlements

    current = netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_READ)
    if include_details:
        netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_RECONCILIATION_READ)
    return settlements(db, current.organization_id, reporting_period, include_details=include_details)


@router.get("/{row_key}", response_model=PortfolioDetail)
def get_portfolio_detail(
    row_key: str,
    reporting_period: str | None = Query(None, pattern=r"^20\d{2}-(0[1-9]|1[0-2])$"),
    include_sensitive: bool = False,
    db: Session = Depends(get_db),
    envelope: IdentityAuthorityEnvelope = Depends(authority_envelope),
) -> PortfolioDetail:
    current = netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_READ)
    if include_sensitive:
        netpay_portfolio_envelope(envelope, required_scope=PORTFOLIO_SENSITIVE_READ)
    detail = NetpayCommerceAttentionService(db, current.organization_id, reporting_period).detail(
        row_key, sensitive=include_sensitive
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="not found")
    return detail

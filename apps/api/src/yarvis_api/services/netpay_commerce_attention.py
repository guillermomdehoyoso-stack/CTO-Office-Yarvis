"""Read-only tenant-scoped projection for the reported Netpay portfolio."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.models.netpay_gmail_intake import NetpayCandidateOnboardingDossier, NetpayIntakeCandidate
from yarvis_api.models.netpay_inbox import CommercialIntakeItem
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.netpay_operational_data import OperationalDataBatch, StoreProfitabilityFact
from yarvis_api.schemas.netpay_commerce_attention import (
    EntityScope,
    PortfolioContact,
    PortfolioDetail,
    PortfolioP2Metrics,
    PortfolioP2Totals,
    PortfolioPage,
    PortfolioRow,
    PortfolioSourceBadges,
    ReconciliationItem,
    ReconciliationPage,
)

_SORT_FIELDS = {
    "commerce": lambda row: row.commerce_name.casefold(),
    "legal_name": lambda row: (row.legal_name or "").casefold(),
    "branch_name": lambda row: (row.branch_name or "").casefold(),
    "store_id": lambda row: (row.store_id or "").casefold(),
    "reconciliation_status": lambda row: row.reconciliation_status,
    "updated_at": lambda row: row.updated_at,
}


def _normalized(value: str | None) -> str:
    return re.sub(
        r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()
    )


def _mask_rfc(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    if len(normalized) <= 4:
        return "*" * len(normalized)
    return f"{'*' * (len(normalized) - 4)}{normalized[-4:]}"


def _masked_contact(
    name: str | None, email: str | None, phone: str | None, scope: EntityScope, updated_at: datetime
) -> PortfolioContact:
    return PortfolioContact(
        available=bool(name or email or phone),
        source_scope=scope if name or email or phone else None,
        name=name if name else None,
        email="Disponible" if email else None,
        phone="Disponible" if phone else None,
        updated_at=updated_at if name or email or phone else None,
    )


def _full_contact(
    name: str | None, email: str | None, phone: str | None, scope: EntityScope, updated_at: datetime
) -> PortfolioContact:
    return PortfolioContact(
        available=bool(name or email or phone),
        source_scope=scope if name or email or phone else None,
        name=name,
        email=email,
        phone=phone,
        updated_at=updated_at if name or email or phone else None,
    )


@dataclass(frozen=True)
class PortfolioFilters:
    search: str | None = None
    entity_scopes: tuple[str, ...] = ()
    reconciliation_statuses: tuple[str, ...] = ()
    has_company: bool | None = None
    has_branch: bool | None = None
    has_store_reference: bool | None = None
    has_contact: bool | None = None
    sort_field: str = "commerce"
    sort_direction: str = "asc"
    page: int = 1
    page_size: int = 50


class NetpayCommerceAttentionService:
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id

    def _rows(self, *, sensitive: bool = False) -> list[PortfolioRow]:
        clients = self.db.scalars(
            select(NetpayClient).where(
                NetpayClient.organization_id == self.organization_id, NetpayClient.status == "active"
            )
        ).all()
        companies = self.db.scalars(
            select(NetpayCompany).where(
                NetpayCompany.organization_id == self.organization_id, NetpayCompany.status == "active"
            )
        ).all()
        branches = self.db.scalars(
            select(NetpayBranch).where(
                NetpayBranch.organization_id == self.organization_id, NetpayBranch.status == "active"
            )
        ).all()
        references = self.db.scalars(
            select(NetpayStoreReference).where(
                NetpayStoreReference.organization_id == self.organization_id, NetpayStoreReference.active.is_(True)
            )
        ).all()
        companies_by_client: dict[UUID, list[NetpayCompany]] = {}
        branches_by_company: dict[UUID, list[NetpayBranch]] = {}
        refs_by_branch: dict[UUID, list[NetpayStoreReference]] = {}
        for item in companies:
            companies_by_client.setdefault(item.client_id, []).append(item)
        for item in branches:
            branches_by_company.setdefault(item.company_id, []).append(item)
        for item in references:
            refs_by_branch.setdefault(item.branch_id, []).append(item)
        rows: list[PortfolioRow] = []
        for client in clients:
            client_companies = sorted(
                companies_by_client.get(client.id, []), key=lambda item: (item.normalized_legal_name, str(item.id))
            )
            if not client_companies:
                contact = (_full_contact if sensitive else _masked_contact)(
                    client.primary_contact_name, client.primary_email, client.primary_phone, "client", client.updated_at
                )
                rows.append(self._row("client", client, None, None, [], contact))
                continue
            for company in client_companies:
                company_branches = sorted(
                    branches_by_company.get(company.id, []),
                    key=lambda item: (item.normalized_commercial_name, str(item.id)),
                )
                if not company_branches:
                    contact = (_full_contact if sensitive else _masked_contact)(
                        company.contact_name,
                        company.contact_email,
                        company.contact_phone,
                        "company",
                        company.updated_at,
                    )
                    rows.append(self._row("company", client, company, None, [], contact))
                    continue
                for branch in company_branches:
                    branch_refs = sorted(
                        refs_by_branch.get(branch.id, []), key=lambda item: (item.normalized_store_id, str(item.id))
                    )
                    contact = (_full_contact if sensitive else _masked_contact)(
                        branch.contact_name, branch.contact_email, branch.contact_phone, "branch", branch.updated_at
                    )
                    rows.append(self._row("branch", client, company, branch, branch_refs, contact))
        return rows

    def _row(
        self,
        scope: EntityScope,
        client: NetpayClient,
        company: NetpayCompany | None,
        branch: NetpayBranch | None,
        references: list[NetpayStoreReference],
        contact: PortfolioContact,
    ) -> PortfolioRow:
        identity = branch.id if branch else company.id if company else client.id
        reference = references[0] if references else None
        reasons = []
        if company is None:
            reasons.append("Sin razón social registrada")
        if branch is None:
            reasons.append("Sin sucursal registrada")
        if reference is None:
            reasons.append("Sin StoreReference")
        if not contact.available:
            reasons.append("Contacto no disponible")
        if len(references) > 1:
            reasons.append(f"{len(references)} StoreReferences activas; se muestra la primera en orden determinista")
        updated = max(
            item
            for item in (
                client.updated_at,
                company.updated_at if company else None,
                branch.updated_at if branch else None,
                reference.updated_at if reference else None,
            )
            if item is not None
        )
        return PortfolioRow(
            row_key=f"{scope}:{identity}",
            entity_scope=scope,
            client_id=client.id,
            company_id=company.id if company else None,
            branch_id=branch.id if branch else None,
            store_reference_id=reference.id if reference else None,
            store_id=reference.store_id if reference else None,
            store_reference_count=len(references),
            commerce_name=client.display_name,
            legal_name=company.legal_name if company else None,
            branch_name=branch.commercial_name if branch else None,
            masked_rfc=_mask_rfc(company.tax_identifier if company else None),
            contact=contact,
            availability_reasons=reasons,
            source_badges=PortfolioSourceBadges(),
            updated_at=updated,
            p2=self._p2(reference),
        )

    def _p2(self, reference: NetpayStoreReference | None) -> PortfolioP2Metrics:
        if reference is None:
            return PortfolioP2Metrics(percentage_status="unknown", percentage_reason="store_reference_missing")
        fact = self.db.scalar(
            select(StoreProfitabilityFact)
            .join(OperationalDataBatch, OperationalDataBatch.id == StoreProfitabilityFact.batch_id)
            .where(
                StoreProfitabilityFact.organization_id == self.organization_id,
                StoreProfitabilityFact.store_reference_id == reference.id,
                StoreProfitabilityFact.effective_status == "effective",
                OperationalDataBatch.organization_id == self.organization_id,
                OperationalDataBatch.status == "accepted",
                OperationalDataBatch.currency_code == "MXN",
            )
            .order_by(StoreProfitabilityFact.reporting_period.desc(), StoreProfitabilityFact.effective_at.desc())
        )
        if fact is None or fact.precision_classification != "exact_decimal_source":
            return PortfolioP2Metrics(percentage_status="unknown", percentage_reason="exact_fact_missing")
        batch = self.db.get(OperationalDataBatch, fact.batch_id)
        sales, commission = fact.volume_exact, fact.distributor_commission_exact
        if sales is None:
            status, reason, percentage = "not_calculable", "volume_missing", None
        elif sales == 0:
            status, reason, percentage = "not_calculable", "volume_zero", None
        elif commission is None:
            status, reason, percentage = "not_calculable", "commission_missing", None
        else:
            status, reason = "calculated", None
            percentage = ((commission / sales) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        return PortfolioP2Metrics(
            reporting_period=fact.reporting_period,
            currency_code=batch.currency_code if batch else None,
            monthly_sales_mxn=sales,
            distributor_commission_mxn=commission,
            effective_commission_on_sales_percent=percentage,
            percentage_status=status,
            percentage_reason=reason,
            source_fields={"monthly_sales_mxn": "Volumen", "distributor_commission_mxn": "Rentabilidad"},
            source_batch_id=fact.batch_id,
            precision_classification=fact.precision_classification,
            freshness_at=fact.effective_at,
            quality="qualified",
        )

    @staticmethod
    def _p2_totals(rows: list[PortfolioRow]) -> PortfolioP2Totals:
        compatible: list[tuple[Decimal, Decimal]] = []
        for row in rows:
            sales = row.p2.monthly_sales_mxn
            commission = row.p2.distributor_commission_mxn
            if sales is not None and sales != 0 and commission is not None:
                compatible.append((sales, commission))
        if not compatible:
            return PortfolioP2Totals(
                percentage_status="not_calculable",
                percentage_reason="no_compatible_stores",
                excluded_stores=len(rows),
            )
        sales = sum((item[0] for item in compatible), Decimal("0"))
        commission = sum((item[1] for item in compatible), Decimal("0"))
        percentage = (
            None
            if sales == 0
            else ((commission / sales) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )
        return PortfolioP2Totals(
            monthly_sales_mxn=sales,
            distributor_commission_mxn=commission,
            effective_commission_on_sales_percent=percentage,
            percentage_status="not_calculable" if percentage is None else "calculated",
            percentage_reason="aggregate_volume_zero" if percentage is None else None,
            compatible_stores=len(compatible),
            excluded_stores=len(rows) - len(compatible),
        )

    def list(self, filters: PortfolioFilters, *, include_reconciliation_count: bool = False) -> PortfolioPage:
        rows = self._rows()
        if include_reconciliation_count:
            unlinked = self.reconciliation().total
            rows = [
                row.model_copy(
                    update={
                        "source_badges": row.source_badges.model_copy(update={"unlinked_records": unlinked})
                    }
                )
                for row in rows
            ]
        total = len(rows)
        search = _normalized(filters.search)
        if search:
            rows = [
                row
                for row in rows
                if search
                in _normalized(
                    " ".join(filter(None, (row.commerce_name, row.legal_name, row.branch_name, row.store_id)))
                )
            ]
        if filters.entity_scopes:
            rows = [row for row in rows if row.entity_scope in filters.entity_scopes]
        if filters.reconciliation_statuses:
            rows = [row for row in rows if row.reconciliation_status in filters.reconciliation_statuses]
        predicates = (
            (filters.has_company, lambda row: row.company_id is not None),
            (filters.has_branch, lambda row: row.branch_id is not None),
            (filters.has_store_reference, lambda row: row.store_reference_id is not None),
            (filters.has_contact, lambda row: row.contact.available),
        )
        for expected, predicate in predicates:
            if expected is not None:
                rows = [row for row in rows if predicate(row) is expected]
        key = _SORT_FIELDS[filters.sort_field]
        rows.sort(key=lambda row: (key(row), row.row_key), reverse=filters.sort_direction == "desc")
        filtered_total = len(rows)
        p2_totals = self._p2_totals(rows)
        start = (filters.page - 1) * filters.page_size
        return PortfolioPage(
            items=rows[start : start + filters.page_size],
            page=filters.page,
            page_size=filters.page_size,
            total=total,
            filtered_total=filtered_total,
            pages=max(1, (filtered_total + filters.page_size - 1) // filters.page_size),
            p2_totals=p2_totals,
        )

    def detail(self, row_key: str, *, sensitive: bool) -> PortfolioDetail | None:
        match = re.fullmatch(r"(client|company|branch):([0-9a-fA-F-]{36})", row_key)
        if not match:
            return None
        try:
            UUID(match.group(2))
        except ValueError:
            return None
        row = next((item for item in self._rows(sensitive=sensitive) if item.row_key == row_key), None)
        if row is None:
            return None
        full_rfc = None
        if sensitive and row.company_id:
            company = self.db.scalar(
                select(NetpayCompany).where(
                    NetpayCompany.id == row.company_id, NetpayCompany.organization_id == self.organization_id
                )
            )
            full_rfc = company.tax_identifier if company else None
        return PortfolioDetail(**row.model_dump(), full_rfc=full_rfc, data_quality=list(row.availability_reasons))

    def reconciliation(self) -> ReconciliationPage:
        items: list[ReconciliationItem] = []
        candidates = self.db.scalars(
            select(NetpayIntakeCandidate).where(
                NetpayIntakeCandidate.organization_id == self.organization_id, NetpayIntakeCandidate.client_id.is_(None)
            )
        ).all()
        for item in candidates:
            hint = next(
                (str(value) for value in item.commerce_hints if isinstance(value, str)), "Registro sin etiqueta"
            )
            status = "conflict" if item.contradictions else "probable_match" if item.commerce_hints else "unreconciled"
            items.append(
                ReconciliationItem(
                    record_type="candidate",
                    record_id=item.id,
                    label_hint=hint[:120],
                    provenance="Netpay Intake Candidate",
                    reconciliation_status=status,
                    reasons=["Sin Client canónico confirmado"],
                    updated_at=item.updated_at,
                )
            )
        intakes = self.db.scalars(
            select(CommercialIntakeItem).where(
                CommercialIntakeItem.organization_id == self.organization_id,
                CommercialIntakeItem.converted_case_id.is_(None),
            )
        ).all()
        for item in intakes:
            items.append(
                ReconciliationItem(
                    record_type="commercial_intake",
                    record_id=item.id,
                    label_hint=(item.provisional_company_name or "Ingreso sin empresa")[:120],
                    provenance="Commercial Intake",
                    reconciliation_status="unreconciled",
                    reasons=["Sin vínculo Master confirmado"],
                    updated_at=item.updated_at,
                )
            )
        dossiers = self.db.scalars(
            select(NetpayCandidateOnboardingDossier)
            .join(
                NetpayIntakeCandidate,
                NetpayIntakeCandidate.id == NetpayCandidateOnboardingDossier.candidate_id,
            )
            .where(
                NetpayCandidateOnboardingDossier.organization_id == self.organization_id,
                NetpayIntakeCandidate.organization_id == self.organization_id,
                NetpayIntakeCandidate.client_id.is_(None),
            )
        ).all()
        for item in dossiers:
            items.append(
                ReconciliationItem(
                    record_type="dossier",
                    record_id=item.id,
                    label_hint="Expediente pre-Master",
                    provenance="Candidate Dossier",
                    reconciliation_status="unreconciled",
                    reasons=["Sin Client Master confirmado"],
                    updated_at=item.created_at,
                )
            )
        items.sort(key=lambda item: (item.updated_at, str(item.record_id)), reverse=True)
        return ReconciliationPage(items=items, total=len(items))

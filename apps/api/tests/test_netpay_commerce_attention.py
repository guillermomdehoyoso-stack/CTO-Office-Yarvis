from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from yarvis_api.main import app
from yarvis_api.models.netpay_inbox import CommercialIntakeItem
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.netpay_operational_data import OperationalDataBatch, StoreProfitabilityFact
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.schemas.netpay_commerce_attention import PortfolioContact, PortfolioP2Metrics, PortfolioRow
from yarvis_api.services.netpay_commerce_attention import NetpayCommerceAttentionService

client = TestClient(app)


def _totals_row(sales: str | None, commission: str | None, suffix: str) -> PortfolioRow:
    return PortfolioRow(
        row_key=f"client:00000000-0000-0000-0000-0000000000{suffix}",
        entity_scope="client",
        client_id=UUID(f"00000000-0000-0000-0000-0000000000{suffix}"),
        commerce_name=f"Synthetic {suffix}",
        contact=PortfolioContact(available=False),
        updated_at=datetime.now(timezone.utc),
        p2=PortfolioP2Metrics(
            monthly_sales_mxn=Decimal(sales) if sales is not None else None,
            distributor_commission_mxn=Decimal(commission) if commission is not None else None,
            percentage_status="calculated" if sales not in (None, "0") and commission is not None else "not_calculable",
        ),
    )


def test_p2_totals_use_ratio_of_sums_and_report_zero_aggregate_denominator() -> None:
    weighted = NetpayCommerceAttentionService._p2_totals(
        [_totals_row("100", "10", "01"), _totals_row("300", "15", "02"), _totals_row(None, "9", "03")]
    )
    assert weighted.effective_commission_on_sales_percent == Decimal("6.25")
    assert weighted.compatible_stores == 2 and weighted.excluded_stores == 1

    zero = NetpayCommerceAttentionService._p2_totals(
        [_totals_row("100", "10", "04"), _totals_row("-100", "-5", "05")]
    )
    assert zero.effective_commission_on_sales_percent is None
    assert zero.percentage_status == "not_calculable" and zero.percentage_reason == "aggregate_volume_zero"


def _headers(subject: str) -> dict[str, str]:
    return {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake"}


def _setup() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    with app.state.yarvis.persistence.create_session() as db:
        org = Organization(legal_name="Portfolio Org", display_name="Portfolio Org", status="active")
        foreign_org = Organization(legal_name="Foreign Org", display_name="Foreign Org", status="active")
        viewer = Principal(external_subject="portfolio:viewer", status="active")
        operator = Principal(external_subject="portfolio:operator", status="active")
        inbox = Principal(external_subject="portfolio:inbox", status="active")
        foreign = Principal(external_subject="portfolio:foreign", status="active")
        db.add_all((org, foreign_org, viewer, operator, inbox, foreign))
        db.flush()
        db.add_all(
            (
                PrincipalMembership(principal_id=viewer.id, organization_id=org.id, role="netpay_master_viewer"),
                PrincipalMembership(
                    principal_id=operator.id, organization_id=org.id, role="netpay_operations_operator"
                ),
                PrincipalMembership(principal_id=inbox.id, organization_id=org.id, role="netpay_inbox_viewer"),
                PrincipalMembership(
                    principal_id=foreign.id, organization_id=foreign_org.id, role="netpay_master_viewer"
                ),
            )
        )
        client_only = NetpayClient(
            organization_id=org.id,
            display_name="Cliente Solo",
            normalized_name="clientesolo",
            primary_contact_name="Ana",
            primary_email="ana@example.test",
            primary_phone="5550000001",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        client_company = NetpayClient(
            organization_id=org.id,
            display_name="Grupo Dos",
            normalized_name="grupodos",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        foreign_client = NetpayClient(
            organization_id=foreign_org.id,
            display_name="Foreign Secret",
            normalized_name="foreignsecret",
            created_by_principal_id=foreign.id,
            updated_by_principal_id=foreign.id,
        )
        db.add_all((client_only, client_company, foreign_client))
        db.flush()
        company_only = NetpayCompany(
            organization_id=org.id,
            client_id=client_company.id,
            legal_name="Razón Sin Sucursal SA",
            normalized_legal_name="razonsinsucursalsa",
            tax_identifier="RFC123456ABC",
            contact_email="legal@example.test",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        company_branch = NetpayCompany(
            organization_id=org.id,
            client_id=client_company.id,
            legal_name="Razón Con Sucursal SA",
            normalized_legal_name="razonconsucursalsa",
            tax_identifier="RFC987654XYZ",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add_all((company_only, company_branch))
        db.flush()
        branch = NetpayBranch(
            organization_id=org.id,
            company_id=company_branch.id,
            commercial_name="Sucursal Centro",
            normalized_commercial_name="sucursalcentro",
            branch_match_key="centro",
            branch_kind="physical",
            contact_name="Encargado",
            contact_phone="5550000002",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(branch)
        db.flush()
        active_ref = NetpayStoreReference(
            organization_id=org.id,
            branch_id=branch.id,
            store_id="STORE-002",
            normalized_store_id="store002",
            source_type="synthetic",
            active=True,
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        inactive_ref = NetpayStoreReference(
            organization_id=org.id,
            branch_id=branch.id,
            store_id="STORE-001",
            normalized_store_id="store001",
            source_type="synthetic",
            active=False,
            removed_at=now,
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        intake = CommercialIntakeItem(
            organization_id=org.id,
            kind="initial_contact",
            channel="manual",
            received_at=now,
            provisional_company_name="Comercio por conciliar",
            product_interest="tpv",
            summary="Dato sintético",
            status="new",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add_all((active_ref, inactive_ref, intake))
        db.flush()
        batch = OperationalDataBatch(
            organization_id=org.id,
            dataset_type="monthly_store_profitability",
            reporting_period="2026-09",
            selected_sheet="Synthetic",
            sanitized_filename="synthetic.csv",
            source_hash="a" * 64,
            preview_token="b" * 64,
            store_state_hash="c" * 64,
            status="accepted",
            source_profile="netpay_monthly_store_v1",
            currency_code="MXN",
            completeness_status="partial",
            row_counts={},
            uploaded_by_principal_id=operator.id,
        )
        db.add(batch)
        db.flush()
        db.add(
            StoreProfitabilityFact(
                organization_id=org.id,
                batch_id=batch.id,
                store_reference_id=active_ref.id,
                reporting_period="2026-09",
                volume=1000.0,
                profitability=-25.0,
                volume_exact=Decimal("1000.00"),
                distributor_commission_exact=Decimal("-25.00"),
                source_scale=2,
                precision_classification="exact_decimal_source",
                effective_status="effective",
                row_fingerprint="d" * 64,
            )
        )
        db.commit()
        return {"branch_key": f"branch:{branch.id}", "foreign_key": f"client:{foreign_client.id}"}


def test_portfolio_permissions_redaction_granularity_filters_and_stable_pagination() -> None:
    keys = _setup()
    denied = client.get("/netpay/commerce-attention", headers=_headers("portfolio:inbox"))
    assert denied.status_code == 403

    response = client.get(
        "/netpay/commerce-attention?page_size=2&sort_field=commerce", headers=_headers("portfolio:viewer")
    )
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 3 and page["filtered_total"] == 3 and len(page["items"]) == 2
    assert page["p2_totals"] == {
        "monthly_sales_mxn": "1000.00000000",
        "distributor_commission_mxn": "-25.00000000",
        "effective_commission_on_sales_percent": "-2.50",
        "percentage_status": "calculated",
        "percentage_reason": None,
        "compatible_stores": 1,
        "excluded_stores": 2,
    }
    second = client.get(
        "/netpay/commerce-attention?page=2&page_size=2&sort_field=commerce", headers=_headers("portfolio:viewer")
    ).json()
    assert len({item["row_key"] for item in page["items"] + second["items"]}) == 3

    branch = client.get(f"/netpay/commerce-attention/{keys['branch_key']}", headers=_headers("portfolio:viewer"))
    assert branch.status_code == 200
    payload = branch.json()
    assert payload["entity_scope"] == "branch"
    assert payload["store_id"] == "STORE-002" and payload["store_reference_count"] == 1
    assert payload["full_rfc"] is None
    assert payload["contact"]["phone"] == "Disponible"
    assert payload["p2"]["monthly_sales_mxn"] == "1000.00000000"
    assert payload["p2"]["distributor_commission_mxn"] == "-25.00000000"
    assert payload["p2"]["effective_commission_on_sales_percent"] == "-2.50"
    assert payload["p2"]["source_fields"] == {
        "monthly_sales_mxn": "Volumen",
        "distributor_commission_mxn": "Rentabilidad",
    }
    assert payload["p2"]["currency_code"] == "MXN" and payload["p2"]["reporting_period"] == "2026-09"
    assert "RFC987654XYZ" not in branch.text and "5550000002" not in branch.text

    sensitive = client.get(
        f"/netpay/commerce-attention/{keys['branch_key']}?include_sensitive=true",
        headers=_headers("portfolio:operator"),
    )
    assert sensitive.status_code == 200
    assert sensitive.json()["full_rfc"] == "RFC987654XYZ"
    assert sensitive.json()["contact"]["phone"] == "5550000002"
    operator_list = client.get("/netpay/commerce-attention", headers=_headers("portfolio:operator"))
    assert "RFC987654XYZ" not in operator_list.text and "5550000002" not in operator_list.text
    assert (
        client.get(
            f"/netpay/commerce-attention/{keys['branch_key']}?include_sensitive=true",
            headers=_headers("portfolio:viewer"),
        ).status_code
        == 403
    )

    filtered = client.get(
        "/netpay/commerce-attention?entity_scopes=client&entity_scopes=company&has_branch=false",
        headers=_headers("portfolio:viewer"),
    ).json()
    assert {item["entity_scope"] for item in filtered["items"]} == {"client", "company"}
    assert (
        client.get("/netpay/commerce-attention?page_size=101", headers=_headers("portfolio:viewer")).status_code == 422
    )


def test_portfolio_conceals_foreign_rows_validates_keys_and_separates_reconciliation() -> None:
    keys = _setup()
    assert (
        client.get(
            f"/netpay/commerce-attention/{keys['foreign_key']}", headers=_headers("portfolio:viewer")
        ).status_code
        == 404
    )
    assert (
        client.get("/netpay/commerce-attention/not-a-row-key", headers=_headers("portfolio:viewer")).status_code == 404
    )
    assert (
        client.get("/netpay/commerce-attention/reconciliation", headers=_headers("portfolio:viewer")).status_code == 403
    )
    queue = client.get("/netpay/commerce-attention/reconciliation", headers=_headers("portfolio:operator"))
    assert queue.status_code == 200
    assert queue.json()["total"] == 1
    assert queue.json()["items"][0]["label_hint"] == "Comercio por conciliar"
    assert "Dato sintético" not in queue.text
    viewer_list = client.get("/netpay/commerce-attention", headers=_headers("portfolio:viewer")).json()
    operator_list = client.get("/netpay/commerce-attention", headers=_headers("portfolio:operator")).json()
    assert all(item["source_badges"]["unlinked_records"] is None for item in viewer_list["items"])
    assert all(item["source_badges"]["unlinked_records"] == 1 for item in operator_list["items"])

    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(func.count()).select_from(CommercialIntakeItem)) == 1
        assert db.scalar(select(func.count()).select_from(NetpayClient)) == 3


def test_portfolio_query_validation_normalized_search_and_empty_pages() -> None:
    _setup()
    headers = _headers("portfolio:viewer")
    assert client.get("/netpay/commerce-attention?page=0", headers=headers).status_code == 422
    assert client.get("/netpay/commerce-attention?page_size=0", headers=headers).status_code == 422
    assert client.get("/netpay/commerce-attention?page_size=101", headers=headers).status_code == 422
    assert client.get("/netpay/commerce-attention?sort_field=raw_sql", headers=headers).status_code == 422
    default_page = client.get("/netpay/commerce-attention", headers=headers).json()
    assert default_page["page"] == 1 and default_page["page_size"] == 50
    normalized = client.get("/netpay/commerce-attention?search=RAZON%20SIN%20SUCURSAL", headers=headers).json()
    assert normalized["filtered_total"] == 1 and normalized["items"][0]["entity_scope"] == "company"
    pii_search = client.get("/netpay/commerce-attention?search=legal%40example.test", headers=headers).json()
    assert pii_search["filtered_total"] == 0
    empty = client.get("/netpay/commerce-attention?page=99", headers=headers).json()
    assert empty["items"] == [] and empty["total"] == 3

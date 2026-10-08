"""Reset and seed the isolated PostgreSQL database for the D1 browser run."""

from yarvis_api.main import app
from yarvis_api.models import Base
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from sqlalchemy import text


def main() -> None:
    with app.state.yarvis.persistence.create_session() as db:
        tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
        db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
        org = Organization(legal_name="Synthetic Data Org", display_name="Synthetic Data Org", status="active")
        foreign_org = Organization(legal_name="Other Data Org", display_name="Other Data Org", status="active")
        operator = Principal(external_subject="data:operator", status="active")
        foreign = Principal(external_subject="data:foreign", status="active")
        db.add_all((org, foreign_org, operator, foreign))
        db.flush()
        db.add_all(
            (
                PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_inbox_operator"),
                PrincipalMembership(principal_id=foreign.id, organization_id=foreign_org.id, role="netpay_inbox_operator"),
            )
        )
        client = NetpayClient(
            organization_id=org.id,
            display_name="Synthetic Data Client",
            normalized_name="syntheticdataclient",
            external_reference="SYN-CLIENT",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(client)
        db.flush()
        company = NetpayCompany(
            organization_id=org.id,
            client_id=client.id,
            legal_name="Synthetic Data Co",
            normalized_legal_name="syntheticdataco",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(company)
        db.flush()
        branch = NetpayBranch(
            organization_id=org.id,
            company_id=company.id,
            commercial_name="Synthetic Data Branch",
            normalized_commercial_name="syntheticdatabranch",
            branch_match_key="synthetic-data",
            branch_kind="physical",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(branch)
        db.flush()
        db.add(
            NetpayStoreReference(
                organization_id=org.id,
                branch_id=branch.id,
                store_id="SYN-STORE-001",
                normalized_store_id="synstore001",
                source_type="synthetic",
                created_by_principal_id=operator.id,
                updated_by_principal_id=operator.id,
            )
        )
        db.commit()
        print(f"seeded organization={org.id} store=SYN-STORE-001")


if __name__ == "__main__":
    main()

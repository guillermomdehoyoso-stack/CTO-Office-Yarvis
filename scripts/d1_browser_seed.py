"""Reset and seed the isolated PostgreSQL database for the D1 browser run."""

from datetime import datetime, timedelta, timezone

from yarvis_api.main import app
from yarvis_api.models import Base
from yarvis_api.models.netpay_gmail_intake import (
    NetpayGmailConnection,
    NetpayGmailSourceItem,
    NetpayIntakeCandidate,
)
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
        connection = NetpayGmailConnection(
            organization_id=org.id,
            provider_account_id="pilot@example.invalid",
            provider_kind="fake",
            credential_secret_ref="memory://netpay-gmail/synthetic-browser",
            label_id="LABEL_SYNTHETIC_NETPAY",
            state="succeeded",
            last_sync_at=datetime.now(timezone.utc),
            mailbox_verified_at=datetime.now(timezone.utc),
            manifest_status="approved",
            manifest_entries=[],
            manifest_approved_at=datetime.now(timezone.utc),
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(connection)
        db.flush()
        source = NetpayGmailSourceItem(
            organization_id=org.id,
            connection_id=connection.id,
            provider_account_id="pilot@example.invalid",
            gmail_message_id="synthetic-browser-message-001",
            gmail_thread_id="synthetic-browser-thread-001",
            provider_received_at=datetime.now(timezone.utc) - timedelta(days=2),
            sender="synthetic.sender@example.invalid",
            recipient="pilot@example.invalid",
            subject="Detalle de Envío - Caso 00199130",
            plain_excerpt=(
                "Producto: Rollo Individual 18 mts Netpay; Cantidad: 18; Paquetería: FedEx; "
                "Guía: 878325984682; Estado: Esperando recolección; Número de serie: vacío"
            ),
            source_fingerprint="0" * 64,
            attachment_metadata=[],
            provenance={"provider": "fake", "label_id": "LABEL_SYNTHETIC_NETPAY"},
        )
        db.add(source)
        db.flush()
        db.add(
            NetpayIntakeCandidate(
                organization_id=org.id,
                source_item_id=source.id,
                connection_id=connection.id,
                source_fingerprint=source.source_fingerprint,
                received_at=source.provider_received_at,
                state="pending_link",
                request_type="consumable_shipment",
                product="not_applicable",
                description=source.plain_excerpt,
                ticket_references=["00199130"],
                commerce_hints=[],
                terminal_serials=[],
                shipment_facts={
                    "carrier": "FedEx",
                    "tracking_number": "878325984682",
                    "reported_state": "Esperando recolección",
                },
                facts=[{"field": "ticket", "value": "00199130", "source": "message_text"}],
                inferences=[
                    {
                        "field": "shipment_interpretation",
                        "value": "reported_state_only; delivery, activation and return remain unconfirmed",
                        "basis": "non_inference_guardrail",
                    }
                ],
                contradictions=[],
                missing_data=["verified_commerce_identifier", "terminal_serial"],
                correlation_key="ticket:00199130",
                priority="normal",
                suggested_next_action="Vincular el comercio con un identificador verificable",
                follow_up_at=datetime.now(timezone.utc) - timedelta(days=1),
                extraction_method="deterministic",
                extraction_version="d2-rules-v1",
                confidence=0.75,
                extraction_reasons=["shipment_evidence"],
            )
        )
        db.commit()
        print(f"seeded organization={org.id} store=SYN-STORE-001")


if __name__ == "__main__":
    main()

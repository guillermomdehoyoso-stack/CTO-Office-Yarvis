import json
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from yarvis_api.main import app
from yarvis_api.models.mission_inbox import MissionInboxItem
from yarvis_api.models.netpay import NetpayDeviceAssignment, NetpayShipment
from yarvis_api.models.netpay_inbox import CommercialIntakeItem, NetpayCaseNextAction, NetpayServiceCase
from yarvis_api.models.netpay_master import NetpayBranch, NetpayClient, NetpayCompany, NetpayStoreReference
from yarvis_api.models.netpay_operational_data import (
    NoUsageCampaignEntry,
    OperationalDataBatch,
    OperationalDataRow,
    StoreProfitabilityFact,
)
from yarvis_api.models.operational_task import OperationalTask
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

client = TestClient(app)


def setup_data():
    with app.state.yarvis.persistence.create_session() as db:
        org, foreign_org = (
            Organization(legal_name="Synthetic Data Org", display_name="Synthetic Data Org", status="active"),
            Organization(legal_name="Other Data Org", display_name="Other Data Org", status="active"),
        )
        operator, foreign = (
            Principal(external_subject="data:operator", status="active"),
            Principal(external_subject="data:foreign", status="active"),
        )
        db.add_all((org, foreign_org, operator, foreign))
        db.flush()
        db.add_all(
            (
                PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_inbox_operator"),
                PrincipalMembership(
                    principal_id=foreign.id, organization_id=foreign_org.id, role="netpay_inbox_operator"
                ),
            )
        )
        master = NetpayClient(
            organization_id=org.id,
            display_name="Synthetic Data Client",
            normalized_name="syntheticdataclient",
            external_reference="SYN-CLIENT",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(master)
        db.flush()
        company = NetpayCompany(
            organization_id=org.id,
            client_id=master.id,
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
        store = NetpayStoreReference(
            organization_id=org.id,
            branch_id=branch.id,
            store_id="SYN-STORE-001",
            normalized_store_id="synstore001",
            source_type="synthetic",
            created_by_principal_id=operator.id,
            updated_by_principal_id=operator.id,
        )
        db.add(store)
        db.commit()
        return store.id


def headers(subject="data:operator", key="data-key"):
    return {"X-Yarvis-Subject": subject, "X-Yarvis-Auth-Token": "deterministic-inbound-intake", "Idempotency-Key": key}


def upload(name, data, dataset, key, rfc=None):
    form = {"dataset_type": dataset}
    if rfc:
        form["rfc_filter"] = rfc
    return client.post(
        "/netpay/data/datasets", headers=headers(key=key), data=form, files={"file": (name, data, "text/csv")}
    )


def test_profitability_preview_accept_replay_and_tenant_isolation():
    setup_data()
    content = (
        b"Store ID,Client ID,Mes,Producto,Volumen,Transacciones,Rentabilidad\n"
        b"SYN-STORE-001,SYN-CLIENT,2026-08,TPV,1200,8,55\n"
    )
    created = upload("synthetic-profitability.csv", content, "monthly_store_profitability", "profitability-upload")
    replay = upload("synthetic-profitability.csv", content, "monthly_store_profitability", "profitability-upload")
    assert created.status_code == 201 and replay.status_code == 200
    assert created.json()["id"] == replay.json()["id"] and replay.json()["duplicate_upload"] is True
    batch = created.json()
    assert batch["status"] == "needs_review"
    assert {
        key: batch["row_counts"][key]
        for key in ("received", "authorized", "valid", "invalid", "matched", "unmatched", "ambiguous")
    } == {"received": 1, "authorized": 1, "valid": 1, "invalid": 0, "matched": 1, "unmatched": 0, "ambiguous": 0}
    accepted = client.post(
        f"/netpay/data/datasets/{batch['id']}/accept",
        headers=headers(key="profitability-accept"),
        json={"preview_token": batch["preview_token"]},
    )
    assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"
    assert (
        len(
            client.get(
                f"/netpay/data/datasets/{batch['id']}/results", headers=headers("data:operator", "result")
            ).json()
        )
        == 1
    )
    assert (
        client.get(f"/netpay/data/datasets/{batch['id']}", headers=headers("data:foreign", "foreign")).status_code
        == 404
    )


def test_no_usage_rfc_filter_is_ephemeral_and_fail_closed():
    setup_data()
    content = (
        b"RFC,Store ID,Periodo,Meses sin uso,Estatus,Alerta\n"
        b"RFC-SYN-ALLOW,SYN-STORE-001,2026-08,2,active,watch\n"
        b"RFC-SYN-OTHER,OTHER-001,2026-08,9,blocked,alert\n"
    )
    missing = upload("synthetic-no-usage.csv", content, "no_usage_campaign", "missing")
    assert missing.status_code == 422
    created = upload("synthetic-no-usage.csv", content, "no_usage_campaign", "no-usage", "RFC-SYN-ALLOW")
    assert created.status_code == 201
    payload = created.json()
    assert payload["row_counts"]["received"] == 2 and payload["row_counts"]["authorized"] == 1
    assert "RFC-SYN" not in str(payload)
    accepted = client.post(
        f"/netpay/data/datasets/{payload['id']}/accept",
        headers=headers(key="no-usage-accept"),
        json={"preview_token": payload["preview_token"]},
    )
    assert accepted.status_code == 200
    assert (
        len(
            client.get(f"/netpay/data/datasets/{payload['id']}/results", headers=headers(key="no-usage-results")).json()
        )
        == 1
    )
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(NetpayServiceCase).count() == 0
        assert db.query(CommercialIntakeItem).count() == 0
        assert db.query(NetpayCaseNextAction).count() == 0
        assert db.query(MissionInboxItem).count() == 0
        assert db.query(OperationalTask).count() == 0
        assert db.query(NetpayShipment).count() == 0
        assert db.query(NetpayDeviceAssignment).count() == 0


def test_xlsx_and_formula_rejection():
    setup_data()
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Store ID", "Client ID", "Mes", "Rentabilidad"])
    sheet.append(["SYN-STORE-001", "SYN-CLIENT", "2026-08", 12])
    stream = BytesIO()
    workbook.save(stream)
    response = upload("synthetic.xlsx", stream.getvalue(), "monthly_store_profitability", "xlsx")
    assert response.status_code == 201
    formula = Workbook()
    sheet = formula.active
    sheet.append(["Store ID", "Client ID", "Mes", "Rentabilidad"])
    sheet.append(["SYN-STORE-001", "SYN-CLIENT", "2026-08", "=1+1"])
    stream = BytesIO()
    formula.save(stream)
    assert upload("formula.xlsx", stream.getvalue(), "monthly_store_profitability", "formula").status_code == 422


def test_invalid_files_headers_and_internal_duplicates_fail_closed():
    setup_data()
    assert upload("synthetic.txt", b"not a workbook", "monthly_store_profitability", "extension").status_code == 422
    assert upload("corrupt.xlsx", b"PK-corrupt", "monthly_store_profitability", "corrupt").status_code == 422
    missing = b"Store ID,Mes\nSYN-STORE-001,2026-08\n"
    assert upload("missing.csv", missing, "monthly_store_profitability", "missing-header").status_code == 422
    duplicate = b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-08,1\nSYN-STORE-001,2026-08,1\n"
    preview = upload("duplicate.csv", duplicate, "monthly_store_profitability", "duplicate-row").json()
    assert preview["row_counts"]["duplicates"] == 2 and preview["row_counts"]["invalid"] == 2


def test_preview_is_staging_only_and_confirmation_requires_exact_token():
    setup_data()
    preview = upload(
        "preview.csv",
        b"Store ID,Mes,Rentabilidad\nSYN-STORE-001,2026-09,10\n",
        "monthly_store_profitability",
        "preview-only",
    ).json()
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(StoreProfitabilityFact).count() == 0
    stale = client.post(
        f"/netpay/data/datasets/{preview['id']}/accept", headers=headers(key="stale"), json={"preview_token": "0" * 64}
    )
    assert stale.status_code == 409
    accepted = client.post(
        f"/netpay/data/datasets/{preview['id']}/accept",
        headers=headers(key="exact"),
        json={"preview_token": preview["preview_token"]},
    )
    replay = client.post(
        f"/netpay/data/datasets/{preview['id']}/accept",
        headers=headers(key="exact"),
        json={"preview_token": preview["preview_token"]},
    )
    assert accepted.status_code == replay.status_code == 200 and accepted.json() == replay.json()
    with app.state.yarvis.persistence.create_session() as db:
        assert db.query(StoreProfitabilityFact).count() == 1


def test_rfc_is_filtered_before_staging_and_never_persisted_or_returned():
    setup_data()
    content = (
        b"RFC,Store ID,Periodo,Meses sin uso\n"
        b"RFC-SYN-ALLOW,SYN-STORE-001,2026-10,2\n"
        b"RFC-SYN-OTHER,OTHER-001,2026-10,9\n"
    )
    response = upload("privacy.csv", content, "no_usage_campaign", "privacy", "RFC-SYN-ALLOW")
    assert response.status_code == 201 and response.json()["row_counts"]["authorized"] == 1
    assert "RFC-SYN" not in response.text
    with app.state.yarvis.persistence.create_session() as db:
        batch = db.query(OperationalDataBatch).one()
        rows = db.query(OperationalDataRow).filter(OperationalDataRow.batch_id == batch.id).all()
        assert len(rows) == 1 and "rfc" not in json.dumps(rows[0].controlled_payload).lower()
        assert db.query(NoUsageCampaignEntry).count() == 0


def test_operational_data_migration_round_trip():
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script_head = ScriptDirectory.from_config(config).get_current_head()

    def current_revision():
        with app.state.yarvis.persistence.create_session() as session:
            return MigrationContext.configure(session.connection()).get_current_revision()

    initial_head = current_revision()
    assert initial_head == script_head
    try:
        command.downgrade(config, "20260819_40")
        command.upgrade(config, "20260819_41")
        assert current_revision() == "20260819_41"
    finally:
        command.upgrade(config, initial_head)
        assert current_revision() == initial_head

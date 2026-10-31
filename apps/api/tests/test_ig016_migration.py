from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from yarvis_api.main import app


def test_ig016_migration_roundtrip_and_single_head():
    config = Config("alembic.ini")
    command.downgrade(config, "20261028_55")
    command.upgrade(config, "20261030_56")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261030_56"
        tables = set(inspect(connection).get_table_names())
        assert {
            "netpay_equipment_identities",
            "netpay_equipment_evidence",
            "netpay_store_equipment_links",
            "netpay_equipment_identity_decisions",
            "netpay_equipment_identity_receipts",
        } <= tables
    command.downgrade(config, "20261028_55")
    command.upgrade(config, "head")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261030_56"

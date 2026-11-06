from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from yarvis_api.main import app


def test_ig016a_c4_migration_roundtrip_and_single_head():
    config = Config("alembic.ini")
    command.downgrade(config, "20261102_58")
    command.upgrade(config, "20261105_59")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261105_59"
        tables = set(inspect(connection).get_table_names())
        assert {
            "netpay_protection_outcome_evidence",
            "netpay_protection_outcome_assessments",
            "netpay_protection_financial_snapshots",
            "netpay_protection_outcome_receipts",
        } <= tables
    command.downgrade(config, "20261102_58")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261102_58"
        assert "netpay_protection_outcome_evidence" not in inspect(connection).get_table_names()
    command.upgrade(config, "head")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261105_59"

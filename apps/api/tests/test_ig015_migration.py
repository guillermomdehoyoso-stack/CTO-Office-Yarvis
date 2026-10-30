"""Round-trip only in the disposable test DB created by conftest."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from test_ig015_commissions import accept, core
from test_netpay_operational_data import setup_data

from yarvis_api.main import app


def test_ig015_empty_roundtrip_and_evidence_guard():
    config = Config("alembic.ini")
    command.downgrade(config, "20261022_54")
    command.upgrade(config, "head")
    setup_data()
    batch = core().json()
    assert accept(batch).status_code == 200
    with pytest.raises(RuntimeError, match="would discard evidence"):
        command.downgrade(config, "20261022_54")
    with app.state.yarvis.persistence.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20261028_55"
        assert connection.scalar(text("SELECT commission_v2_exact FROM netpay_store_profitability_facts")) == 100

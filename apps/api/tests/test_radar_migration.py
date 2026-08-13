from alembic import command
from alembic.config import Config


def test_radar_migration_round_trip():
    config = Config("alembic.ini")
    command.downgrade(config, "20260805_30")
    command.upgrade(config, "20260806_31")
    command.current(config)
    command.upgrade(config, "head")

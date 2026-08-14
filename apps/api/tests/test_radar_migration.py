from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from yarvis_api.config import Settings


def test_radar_migration_round_trip():
    config = Config("alembic.ini")
    command.downgrade(config, "20260805_30")
    command.upgrade(config, "20260806_31")
    command.current(config)
    command.upgrade(config, "head")


def test_radar_workspace_compatibility_migration_round_trip_preserves_legacy_values():
    config = Config("alembic.ini")
    engine = create_engine(Settings().database_url.replace("postgresql://", "postgresql+psycopg://", 1))
    command.downgrade(config, "20260813_36")
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO radar_merchants (id, workspace_id, trade_name, products) VALUES (gen_random_uuid(), 'legacy-workspace', 'Legacy', '[]'::jsonb)")
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        workspace_column = next(column for column in inspect(connection).get_columns("radar_merchants") if column["name"] == "workspace_id")
        assert workspace_column["nullable"] is True
        assert connection.execute(text("SELECT workspace_id FROM radar_merchants")).scalar_one() == "legacy-workspace"
    command.downgrade(config, "20260813_36")
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT workspace_id FROM radar_merchants")).scalar_one() == "legacy-workspace"

import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yarvis_api.config import get_settings

settings = get_settings()


def sqlalchemy_url(database_url: str) -> str:
    """Use psycopg 3 for SQLAlchemy while retaining the standard DATABASE_URL."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


engine = create_engine(sqlalchemy_url(settings.database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def check_database_connection(database_url: str) -> None:
    with psycopg.connect(database_url, connect_timeout=3) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


def get_db():
    with SessionLocal() as session:
        yield session

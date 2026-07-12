from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str = "Yarvis API"
    app_version: str = "0.1.0"
    database_url: str = field(
        default_factory=lambda: getenv(
            "DATABASE_URL",
            "postgresql://yarvis:yarvis@localhost:5432/yarvis",
        )
    )


def get_settings() -> Settings:
    return Settings()

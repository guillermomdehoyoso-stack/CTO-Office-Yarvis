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
    document_storage_root: str = field(default_factory=lambda: getenv("DOCUMENT_STORAGE_ROOT", "/data/yarvis"))
    max_upload_size_bytes: int = field(default_factory=lambda: int(getenv("MAX_UPLOAD_SIZE_BYTES", "5242880")))
    preview_row_limit: int = field(default_factory=lambda: int(getenv("PREVIEW_ROW_LIMIT", "200")))


def get_settings() -> Settings:
    return Settings()

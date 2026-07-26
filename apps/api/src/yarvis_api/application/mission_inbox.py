"""Application DTOs for the Mission Inbox read model."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MissionInboxFilters:
    status: str | None = None
    priority: str | None = None
    site_id: UUID | None = None
    project_id: UUID | None = None
    source_type: str | None = None
    sort: str = "last_activity_at"
    limit: int = 50
    offset: int = 0

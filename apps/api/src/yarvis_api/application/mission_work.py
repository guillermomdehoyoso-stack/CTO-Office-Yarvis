"""Transport-neutral Mission Work commands and query filters."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateMissionWorkItemFromInboxCommand:
    inbox_item_id: UUID


@dataclass(frozen=True, slots=True)
class AssignMissionWorkItemCommand:
    work_item_id: UUID
    assignee_subject_id: str | None


@dataclass(frozen=True, slots=True)
class ChangeMissionWorkItemStatusCommand:
    work_item_id: UUID
    status: str


@dataclass(frozen=True, slots=True)
class ChangeMissionWorkItemPriorityCommand:
    work_item_id: UUID
    priority: str


@dataclass(frozen=True, slots=True)
class MissionWorkItemFilters:
    status: str | None = None
    priority: str | None = None
    assignee_subject_id: str | None = None
    inbox_item_id: UUID | None = None
    source_type: str | None = None
    source_id: UUID | None = None
    sort: str = "updated_at"
    limit: int = 50
    offset: int = 0

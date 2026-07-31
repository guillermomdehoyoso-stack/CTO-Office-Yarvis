from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True, slots=True)
class CreateOperationalTaskCommand:
    mission_work_item_id: UUID; title: str; description: str | None = None; priority: str = "normal"; process_instance_id: UUID | None = None; process_stage_id: UUID | None = None; planned_start_at: datetime | None = None; due_at: datetime | None = None
@dataclass(frozen=True, slots=True)
class UpdateOperationalTaskCommand:
    task_id: UUID; expected_version: int; title: str; description: str | None; priority: str; process_instance_id: UUID | None; process_stage_id: UUID | None; planned_start_at: datetime | None; due_at: datetime | None
@dataclass(frozen=True, slots=True)
class AssignOperationalTaskCommand:
    task_id: UUID; expected_version: int; assignee_subject_id: str | None
@dataclass(frozen=True, slots=True)
class TaskTransitionCommand:
    task_id: UUID; expected_version: int; status: str
@dataclass(frozen=True, slots=True)
class CompleteOperationalTaskCommand:
    task_id: UUID; expected_version: int; completion_note: str | None
@dataclass(frozen=True, slots=True)
class CancelOperationalTaskCommand:
    task_id: UUID; expected_version: int; reason: str
@dataclass(frozen=True, slots=True)
class ManageTaskDependencyCommand:
    successor_task_id: UUID; predecessor_task_id: UUID; remove: bool = False

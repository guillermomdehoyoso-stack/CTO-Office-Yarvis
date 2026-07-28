"""Transport-neutral commands for versioned operational process definitions."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateProcessDefinitionCommand:
    name: str
    description: str | None


@dataclass(frozen=True, slots=True)
class CreateProcessVersionCommand:
    process_definition_id: UUID


@dataclass(frozen=True, slots=True)
class AddProcessStageCommand:
    process_definition_id: UUID
    stage_key: str
    name: str
    description: str | None
    stage_type: str
    display_order: int
    metadata_json: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class UpdateProcessStageCommand:
    process_definition_id: UUID
    stage_id: UUID
    stage_key: str
    name: str
    description: str | None
    stage_type: str
    display_order: int
    metadata_json: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class DeleteProcessStageCommand:
    process_definition_id: UUID
    stage_id: UUID


@dataclass(frozen=True, slots=True)
class AddProcessTransitionCommand:
    process_definition_id: UUID
    from_stage_id: UUID
    to_stage_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class UpdateProcessTransitionCommand:
    process_definition_id: UUID
    transition_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class DeleteProcessTransitionCommand:
    process_definition_id: UUID
    transition_id: UUID


@dataclass(frozen=True, slots=True)
class ProcessLifecycleCommand:
    process_definition_id: UUID


@dataclass(frozen=True, slots=True)
class StartProcessInstanceCommand:
    process_definition_id: UUID


@dataclass(frozen=True, slots=True)
class TransitionProcessInstanceCommand:
    process_instance_id: UUID
    transition_id: UUID
    expected_version: int


@dataclass(frozen=True, slots=True)
class CancelProcessInstanceCommand:
    process_instance_id: UUID
    expected_version: int
    reason: str

"""Transactional Operational Task owner; Timeline remains a Mission projection.

Timeline projection runs synchronously after Task commit. A projection failure leaves
the committed Task and DomainEvent records durable and is returned to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS007CommandName, command_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.operational_task import (
    AssignOperationalTaskCommand,
    CancelOperationalTaskCommand,
    CompleteOperationalTaskCommand,
    CreateOperationalTaskCommand,
    ManageTaskDependencyCommand,
    TaskTransitionCommand,
    UpdateOperationalTaskCommand,
)
from yarvis_api.application.service_boundary import enforce_command_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.operational_task import OperationalTask, OperationalTaskEvent, TaskDependency
from yarvis_api.models.process import ProcessInstance, ProcessStage
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.operational_task import TaskPage, TaskRead
from yarvis_api.services.inbound_intake import _principal_organization_id

_STATUSES = {"planned", "ready", "in_progress", "completed", "cancelled"}
_PRIORITIES = {"low", "normal", "high", "urgent"}
_CREATE_IDEMPOTENCY_CONSTRAINT = "uq_operational_tasks_create_idempotency"


def _error(code: ApplicationErrorCode, message: str) -> ApplicationError:
    return ApplicationError(code, message, {"resource": "operational_task"})


def _not_found() -> ApplicationError:
    return _error(ApplicationErrorCode.RESOURCE_NOT_FOUND, "operational task not found")


def _conflict(message: str) -> ApplicationError:
    return _error(ApplicationErrorCode.CONFLICT, message)


@dataclass(slots=True)
class OperationalTaskService:
    persistence: PersistenceRuntime
    timeline_projector: TaskMissionWorkTimelineProjector

    def create(self, command: CreateOperationalTaskCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.CREATE_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._idempotency_key(metadata)
        fingerprint = self._fingerprint(contract.interaction_contract_id, {
            "mission_work_item_id": str(command.mission_work_item_id), "title": command.title,
            "description": command.description, "priority": command.priority,
            "process_instance_id": str(command.process_instance_id) if command.process_instance_id else None,
            "process_stage_id": str(command.process_stage_id) if command.process_stage_id else None,
            "planned_start_at": command.planned_start_at, "due_at": command.due_at,
        })
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                existing = session.scalar(select(OperationalTask).where(
                    OperationalTask.organization_id == organization_id,
                    OperationalTask.create_idempotency_key == key,
                ))
                if existing is not None:
                    return self._create_replay(existing, fingerprint)
                self._work(session, command.mission_work_item_id, organization_id)
                self._process(session, command.process_instance_id, command.process_stage_id, organization_id)
                if command.priority not in _PRIORITIES:
                    raise _error(ApplicationErrorCode.VALIDATION_FAILED, "unsupported task priority")
                task = OperationalTask(
                    organization_id=organization_id, mission_work_item_id=command.mission_work_item_id,
                    title=command.title, description=command.description, priority=command.priority,
                    process_instance_id=command.process_instance_id, process_stage_id=command.process_stage_id,
                    planned_start_at=command.planned_start_at, due_at=command.due_at,
                    create_idempotency_key=key, create_request_fingerprint=fingerprint,
                )
                session.add(task)
                session.flush()
                self._event(session, task, "operational_task.created", principal, metadata, key, fingerprint, {
                    "title": task.title, "status": task.status,
                })
                result = TaskRead.model_validate(task)
                unit_of_work.commit()
        except IntegrityError as error:
            if not self._is_create_idempotency_violation(error):
                raise
            return self._resolve_create_replay(organization_id, key, fingerprint, error)
        self.timeline_projector.project_task(result.id)
        return result

    def update(self, command: UpdateOperationalTaskCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.UPDATE_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        return self._mutate(command.task_id, command.expected_version, metadata, principal, contract, "operational_task.updated", {
            "title": command.title, "description": command.description, "priority": command.priority,
            "process_instance_id": str(command.process_instance_id) if command.process_instance_id else None,
            "process_stage_id": str(command.process_stage_id) if command.process_stage_id else None,
            "planned_start_at": command.planned_start_at, "due_at": command.due_at,
            "expected_version": command.expected_version,
        }, lambda session, task: self._plan(session, task, command))

    def assign(self, command: AssignOperationalTaskCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.ASSIGN_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        return self._mutate(command.task_id, command.expected_version, metadata, principal, contract, "operational_task.assigned", {
            "assignee_subject_id": command.assignee_subject_id, "expected_version": command.expected_version,
        }, lambda _session, task: setattr(task, "assignee_subject_id", command.assignee_subject_id))

    def transition(self, command: TaskTransitionCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.TRANSITION_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)

        def change(session: Session, task: OperationalTask) -> None:
            if command.status not in _STATUSES or command.status in {"completed", "cancelled"}:
                raise _error(ApplicationErrorCode.VALIDATION_FAILED, "use explicit completion or cancellation")
            if command.status == "ready" and not self._ready(session, task):
                raise _conflict("task prerequisites are not completed")
            if command.status == "in_progress" and task.status != "ready":
                raise _conflict("task cannot start unless ready")
            if task.status in {"completed", "cancelled"}:
                raise _conflict("task is terminal")
            task.status = command.status

        event = "operational_task.started" if command.status == "in_progress" else "operational_task.ready"
        return self._mutate(command.task_id, command.expected_version, metadata, principal, contract, event, {
            "status": command.status, "expected_version": command.expected_version,
        }, change)

    def complete(self, command: CompleteOperationalTaskCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.COMPLETE_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)

        def change(_session: Session, task: OperationalTask) -> None:
            if task.status != "in_progress":
                raise _conflict("task can only be completed from in_progress")
            task.status = "completed"
            task.completed_at = utc_now()
            task.completed_by_subject_id = principal.actor_id
            task.completion_note = command.completion_note

        return self._mutate(command.task_id, command.expected_version, metadata, principal, contract, "operational_task.completed", {
            "completion_note": command.completion_note, "expected_version": command.expected_version,
        }, change)

    def cancel(self, command: CancelOperationalTaskCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> TaskRead:
        contract = command_contracts[WS007CommandName.CANCEL_TASK]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        if not command.reason.strip():
            raise _error(ApplicationErrorCode.VALIDATION_FAILED, "cancellation reason is required")

        def change(_session: Session, task: OperationalTask) -> None:
            if task.status in {"completed", "cancelled"}:
                raise _conflict("task is terminal")
            task.status = "cancelled"
            task.cancelled_at = utc_now()
            task.cancelled_by_subject_id = principal.actor_id
            task.cancellation_reason = command.reason

        return self._mutate(command.task_id, command.expected_version, metadata, principal, contract, "operational_task.cancelled", {
            "reason": command.reason, "expected_version": command.expected_version,
        }, change)

    def dependency(self, command: ManageTaskDependencyCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> None:
        contract = command_contracts[WS007CommandName.MANAGE_DEPENDENCIES]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        key = self._idempotency_key(metadata)
        fingerprint = self._fingerprint(contract.interaction_contract_id, {
            "successor_task_id": str(command.successor_task_id),
            "predecessor_task_id": str(command.predecessor_task_id), "operation": "remove" if command.remove else "add",
        })
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            successor = self._task(session, command.successor_task_id, organization_id, True)
            if self._event_replay(session, successor, key, fingerprint):
                return
            predecessor = self._task(session, command.predecessor_task_id, organization_id, True)
            if predecessor.id == successor.id or predecessor.mission_work_item_id != successor.mission_work_item_id:
                raise _error(ApplicationErrorCode.VALIDATION_FAILED, "dependencies must be distinct tasks in the same Mission Work")
            edge = session.scalar(select(TaskDependency).where(
                TaskDependency.organization_id == organization_id,
                TaskDependency.predecessor_task_id == predecessor.id,
                TaskDependency.successor_task_id == successor.id,
                TaskDependency.closed_at.is_(None),
            ))
            if command.remove:
                if edge is None:
                    raise _not_found()
                edge.closed_at = utc_now()
                event_type = "operational_task.dependency_closed"
            else:
                if edge is not None:
                    raise _conflict("task dependency already exists")
                if self._reachable(session, successor.id, predecessor.id, organization_id):
                    raise _conflict("task dependency would create a cycle")
                session.add(TaskDependency(organization_id=organization_id, predecessor_task_id=predecessor.id, successor_task_id=successor.id))
                event_type = "operational_task.dependency_added"
            self._event(session, successor, event_type, principal, metadata, key, fingerprint, {
                "predecessor_task_id": str(predecessor.id), "operation": "remove" if command.remove else "add",
            })
            successor_id = successor.id
            unit_of_work.commit()
        self.timeline_projector.project_task(successor_id)

    def _mutate(self, task_id: UUID, expected_version: int, metadata: RequestMetadata, principal: AuthenticatedPrincipal, contract, event_type: str, request: dict[str, object], change) -> TaskRead:
        organization_id = _principal_organization_id(principal)
        key = self._idempotency_key(metadata)
        fingerprint = self._fingerprint(contract.interaction_contract_id, request)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            task = self._task(session, task_id, organization_id, True)
            if self._event_replay(session, task, key, fingerprint):
                return TaskRead.model_validate(task)
            if task.version != expected_version:
                raise _conflict("task version conflict")
            previous_status = task.status
            change(session, task)
            task.version += 1
            task.updated_at = utc_now()
            self._event(session, task, event_type, principal, metadata, key, fingerprint, {
                **request, "previous_status": previous_status, "resulting_status": task.status,
            })
            result = TaskRead.model_validate(task)
            unit_of_work.commit()
        self.timeline_projector.project_task(result.id)
        return result

    @staticmethod
    def _idempotency_key(metadata: RequestMetadata) -> str:
        if metadata.idempotency_key is None:
            raise ApplicationError(ApplicationErrorCode.PRECONDITION_FAILED, "idempotency key is required for operational task commands", {"resource": "operational_task"})
        return metadata.idempotency_key

    @staticmethod
    def _fingerprint(contract_id: str, request: dict[str, object]) -> str:
        return sha256(dumps({"contract": contract_id, "request": request}, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

    @staticmethod
    def _create_replay(task: OperationalTask, fingerprint: str) -> TaskRead:
        if task.create_request_fingerprint != fingerprint:
            raise _conflict("idempotency key was previously used for a different operational task create command")
        return TaskRead.model_validate(task)

    def _resolve_create_replay(self, organization_id: UUID, key: str, fingerprint: str, original_error: IntegrityError) -> TaskRead:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            task = unit_of_work.session.scalar(select(OperationalTask).where(
                OperationalTask.organization_id == organization_id,
                OperationalTask.create_idempotency_key == key,
            ))
            if task is None:
                raise original_error
            return self._create_replay(task, fingerprint)

    @staticmethod
    def _is_create_idempotency_violation(error: IntegrityError) -> bool:
        return isinstance(error.orig, UniqueViolation) and error.orig.diag.constraint_name == _CREATE_IDEMPOTENCY_CONSTRAINT

    @staticmethod
    def _event_replay(session: Session, task: OperationalTask, key: str, fingerprint: str) -> bool:
        replay = session.scalar(select(OperationalTaskEvent).where(
            OperationalTaskEvent.organization_id == task.organization_id,
            OperationalTaskEvent.task_id == task.id,
            OperationalTaskEvent.idempotency_key == key,
        ))
        if replay is None:
            return False
        if replay.request_fingerprint != fingerprint:
            raise _conflict("idempotency key was previously used for a different operational task command")
        return True

    def _plan(self, session: Session, task: OperationalTask, command: UpdateOperationalTaskCommand) -> None:
        if task.status != "planned":
            raise _conflict("planning fields can only change while planned")
        if command.priority not in _PRIORITIES:
            raise _error(ApplicationErrorCode.VALIDATION_FAILED, "unsupported task priority")
        self._process(session, command.process_instance_id, command.process_stage_id, task.organization_id)
        task.title = command.title
        task.description = command.description
        task.priority = command.priority
        task.process_instance_id = command.process_instance_id
        task.process_stage_id = command.process_stage_id
        task.planned_start_at = command.planned_start_at
        task.due_at = command.due_at

    @staticmethod
    def _event(session: Session, task: OperationalTask, event_type: str, principal: AuthenticatedPrincipal, metadata: RequestMetadata, key: str, fingerprint: str, payload: dict[str, object]) -> None:
        sequence = (session.scalar(select(func.coalesce(func.max(OperationalTaskEvent.sequence_number), 0)).where(
            OperationalTaskEvent.organization_id == task.organization_id,
            OperationalTaskEvent.task_id == task.id,
        )) or 0) + 1
        envelope = {**payload, "actor_subject_id": principal.actor_id, "mission_work_item_id": str(task.mission_work_item_id)}
        session.add(OperationalTaskEvent(
            organization_id=task.organization_id, task_id=task.id, event_type=event_type,
            payload_json=envelope, sequence_number=sequence, idempotency_key=key,
            request_fingerprint=fingerprint,
        ))
        record_event(session, event_type=event_type, aggregate_type="operational_task", aggregate_id=task.id,
            organization_id=task.organization_id, correlation_id=UUID(metadata.correlation_id),
            causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload=envelope)

    @staticmethod
    def _work(session: Session, work_id: UUID, organization_id: UUID) -> None:
        if session.scalar(select(MissionWorkItem.id).where(MissionWorkItem.id == work_id, MissionWorkItem.organization_id == organization_id)) is None:
            raise _not_found()

    @staticmethod
    def _task(session: Session, task_id: UUID, organization_id: UUID, lock: bool = False) -> OperationalTask:
        query = select(OperationalTask).where(OperationalTask.id == task_id, OperationalTask.organization_id == organization_id)
        if lock:
            query = query.with_for_update()
        task = session.scalar(query)
        if task is None:
            raise _not_found()
        return task

    @staticmethod
    def _process(session: Session, process_instance_id: UUID | None, process_stage_id: UUID | None, organization_id: UUID) -> None:
        if process_instance_id is None:
            if process_stage_id is not None:
                raise _error(ApplicationErrorCode.VALIDATION_FAILED, "stage requires process instance")
            return
        instance = session.scalar(select(ProcessInstance).where(ProcessInstance.id == process_instance_id, ProcessInstance.organization_id == organization_id))
        if instance is None:
            raise _not_found()
        if process_stage_id is not None and session.scalar(select(ProcessStage.id).where(
            ProcessStage.id == process_stage_id, ProcessStage.process_definition_id == instance.process_definition_id,
            ProcessStage.organization_id == organization_id,
        )) is None:
            raise _not_found()

    @staticmethod
    def _reachable(session: Session, start: UUID, target: UUID, organization_id: UUID) -> bool:
        frontier, seen = [start], set()
        while frontier:
            node = frontier.pop()
            if node == target:
                return True
            if node in seen:
                continue
            seen.add(node)
            frontier.extend(session.scalars(select(TaskDependency.successor_task_id).where(
                TaskDependency.organization_id == organization_id, TaskDependency.predecessor_task_id == node,
                TaskDependency.closed_at.is_(None),
            )))
        return False

    def _ready(self, session: Session, task: OperationalTask) -> bool:
        predecessors = session.scalars(select(OperationalTask).join(TaskDependency, TaskDependency.predecessor_task_id == OperationalTask.id).where(
            TaskDependency.successor_task_id == task.id, TaskDependency.organization_id == task.organization_id,
            TaskDependency.closed_at.is_(None),
        )).all()
        return all(item.status == "completed" for item in predecessors)


class OperationalTaskQueryService:
    def retrieve(self, session: Session, task_id: UUID, principal: AuthenticatedPrincipal) -> TaskRead:
        return TaskRead.model_validate(OperationalTaskService._task(session, task_id, _principal_organization_id(principal)))

    def list(self, session: Session, work_id: UUID, principal: AuthenticatedPrincipal, limit: int = 50, offset: int = 0) -> TaskPage:
        organization_id = _principal_organization_id(principal)
        OperationalTaskService._work(session, work_id, organization_id)
        query = select(OperationalTask).where(OperationalTask.organization_id == organization_id, OperationalTask.mission_work_item_id == work_id).order_by(OperationalTask.created_at.asc(), OperationalTask.id.asc())
        return TaskPage(items=[TaskRead.model_validate(item) for item in session.scalars(query.limit(limit).offset(offset))], total=session.scalar(select(func.count()).select_from(OperationalTask).where(OperationalTask.organization_id == organization_id, OperationalTask.mission_work_item_id == work_id)) or 0, limit=limit, offset=offset)


@dataclass(slots=True)
class TaskMissionWorkTimelineProjector:
    persistence: PersistenceRuntime

    def project_task(self, task_id: UUID) -> None:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            task = OperationalTaskService._task(session, task_id, self._organization(session, task_id), True)
            sources = session.scalars(select(DomainEvent).where(DomainEvent.aggregate_type == "operational_task", DomainEvent.aggregate_id == task.id).order_by(DomainEvent.event_sequence)).all()
            for source in sources:
                if session.scalar(select(MissionWorkEvent.id).where(MissionWorkEvent.organization_id == task.organization_id, MissionWorkEvent.work_item_id == task.mission_work_item_id, MissionWorkEvent.source_domain_event_id == source.id)):
                    continue
                sequence = (session.scalar(select(func.coalesce(func.max(MissionWorkEvent.sequence_number), 0)).where(MissionWorkEvent.organization_id == task.organization_id, MissionWorkEvent.work_item_id == task.mission_work_item_id)) or 0) + 1
                session.add(MissionWorkEvent(organization_id=task.organization_id, work_item_id=task.mission_work_item_id, event_type=source.event_type.replace("operational_task.", "task."), actor_subject_id=source.payload.get("actor_subject_id"), payload_json=source.payload, sequence_number=sequence, source_domain_event_id=source.id))
            unit_of_work.commit()

    @staticmethod
    def _organization(session: Session, task_id: UUID) -> UUID:
        return session.scalar(select(OperationalTask.organization_id).where(OperationalTask.id == task_id))

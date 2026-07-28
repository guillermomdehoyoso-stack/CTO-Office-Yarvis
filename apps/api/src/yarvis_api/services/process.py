"""Governed application services for versioned operational processes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import (
    WS006CommandName,
    WS006QueryName,
    command_contracts,
    query_contracts,
)
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.process import (
    AddProcessStageCommand,
    AddProcessTransitionCommand,
    CreateProcessDefinitionCommand,
    CreateProcessVersionCommand,
    DeleteProcessStageCommand,
    DeleteProcessTransitionCommand,
    ProcessLifecycleCommand,
    CancelProcessInstanceCommand,
    StartProcessInstanceCommand,
    TransitionProcessInstanceCommand,
    UpdateProcessStageCommand,
    UpdateProcessTransitionCommand,
)
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceEvent, ProcessStage, ProcessTransition
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.process import (
    ProcessDefinitionListItem,
    ProcessDefinitionRead,
    ProcessInstanceEventRead,
    ProcessInstancePage,
    ProcessInstanceRead,
    ProcessInstanceTimeline,
    ProcessStageRead,
    ProcessTransitionRead,
)
from yarvis_api.services.inbound_intake import _principal_organization_id


_DRAFT = "draft"
_PUBLISHED = "published"
_RETIRED = "retired"
_STAGE_TYPES = {"start", "work", "wait", "decision", "terminal"}


def _not_found() -> ApplicationError:
    return ApplicationError(
        ApplicationErrorCode.RESOURCE_NOT_FOUND,
        "process definition not found",
        {"resource": "process_definition"},
    )


def _conflict(reason: str) -> ApplicationError:
    return ApplicationError(
        ApplicationErrorCode.CONFLICT,
        reason,
        {"resource": "process_definition"},
    )


def _validation(reason: str) -> ApplicationError:
    return ApplicationError(
        ApplicationErrorCode.VALIDATION_FAILED,
        reason,
        {"resource": "process_definition"},
    )


def _definition_read(session: Session, definition: ProcessDefinition) -> ProcessDefinitionRead:
    stages = session.scalars(
        select(ProcessStage)
        .where(ProcessStage.process_definition_id == definition.id)
        .order_by(ProcessStage.display_order.asc(), ProcessStage.stage_key.asc())
    ).all()
    transitions = session.scalars(
        select(ProcessTransition)
        .where(ProcessTransition.process_definition_id == definition.id)
        .order_by(ProcessTransition.name.asc(), ProcessTransition.id.asc())
    ).all()
    return ProcessDefinitionRead(
        id=definition.id,
        name=definition.name,
        description=definition.description,
        version=definition.version,
        lifecycle=definition.lifecycle,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
        published_at=definition.published_at,
        retired_at=definition.retired_at,
        stages=[ProcessStageRead.model_validate(stage) for stage in stages],
        transitions=[ProcessTransitionRead.model_validate(transition) for transition in transitions],
    )


@dataclass(slots=True)
class ProcessDefinitionService:
    """Owns draft mutation, lifecycle transitions, versioning, and event recording."""

    persistence: PersistenceRuntime

    def create(
        self,
        command: CreateProcessDefinitionCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.CREATE_PROCESS_DEFINITION], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            existing = session.scalar(
                select(ProcessDefinition.id)
                .where(ProcessDefinition.organization_id == organization_id)
                .where(ProcessDefinition.name == command.name)
            )
            if existing is not None:
                raise _conflict("a process definition with this name already exists; create a version from it instead")
            definition = ProcessDefinition(
                organization_id=organization_id,
                name=command.name,
                description=command.description,
                version=1,
                lifecycle=_DRAFT,
            )
            session.add(definition)
            session.flush()
            self._record(
                session,
                definition,
                "process_definition.created",
                {"name": definition.name, "version": definition.version, "lifecycle": definition.lifecycle},
                metadata,
            )
            result = _definition_read(session, definition)
            unit_of_work.commit()
            return result

    def create_version(
        self,
        command: CreateProcessVersionCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.CREATE_PROCESS_VERSION], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            source = self._definition(session, command.process_definition_id, organization_id, lock=True)
            if source.lifecycle == _DRAFT:
                raise _conflict("a new version can only be created from a published or retired definition")
            latest_version = session.scalar(
                select(func.max(ProcessDefinition.version))
                .where(ProcessDefinition.organization_id == organization_id)
                .where(ProcessDefinition.name == source.name)
            ) or source.version
            version = ProcessDefinition(
                organization_id=organization_id,
                name=source.name,
                description=source.description,
                version=latest_version + 1,
                lifecycle=_DRAFT,
            )
            session.add(version)
            session.flush()
            stage_map: dict[UUID, UUID] = {}
            source_stages = session.scalars(
                select(ProcessStage)
                .where(ProcessStage.process_definition_id == source.id)
                .order_by(ProcessStage.display_order.asc(), ProcessStage.stage_key.asc())
            ).all()
            for stage in source_stages:
                clone = ProcessStage(
                    organization_id=organization_id,
                    process_definition_id=version.id,
                    stage_key=stage.stage_key,
                    name=stage.name,
                    description=stage.description,
                    stage_type=stage.stage_type,
                    display_order=stage.display_order,
                    metadata_json=stage.metadata_json,
                )
                session.add(clone)
                session.flush()
                stage_map[stage.id] = clone.id
            source_transitions = session.scalars(
                select(ProcessTransition)
                .where(ProcessTransition.process_definition_id == source.id)
                .order_by(ProcessTransition.name.asc(), ProcessTransition.id.asc())
            ).all()
            for transition in source_transitions:
                session.add(
                    ProcessTransition(
                        organization_id=organization_id,
                        process_definition_id=version.id,
                        from_stage_id=stage_map[transition.from_stage_id],
                        to_stage_id=stage_map[transition.to_stage_id],
                        name=transition.name,
                    )
                )
            session.flush()
            self._record(
                session,
                version,
                "process_definition.version_created",
                {"source_process_definition_id": str(source.id), "source_version": source.version, "version": version.version},
                metadata,
            )
            result = _definition_read(session, version)
            unit_of_work.commit()
            return result

    def add_stage(self, command: AddProcessStageCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.ADD_PROCESS_STAGE], metadata=metadata, principal=principal)
        return self._change_stage(command.process_definition_id, metadata, principal, lambda session, definition: self._add_stage(session, definition, command))

    def update_stage(self, command: UpdateProcessStageCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.UPDATE_PROCESS_STAGE], metadata=metadata, principal=principal)
        return self._change_stage(command.process_definition_id, metadata, principal, lambda session, definition: self._update_stage(session, definition, command))

    def delete_stage(self, command: DeleteProcessStageCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.DELETE_PROCESS_STAGE], metadata=metadata, principal=principal)
        return self._change_stage(command.process_definition_id, metadata, principal, lambda session, definition: self._delete_stage(session, definition, command.stage_id))

    def add_transition(self, command: AddProcessTransitionCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.ADD_PROCESS_TRANSITION], metadata=metadata, principal=principal)
        return self._change_transition(command.process_definition_id, metadata, principal, lambda session, definition: self._add_transition(session, definition, command))

    def update_transition(self, command: UpdateProcessTransitionCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.UPDATE_PROCESS_TRANSITION], metadata=metadata, principal=principal)
        return self._change_transition(command.process_definition_id, metadata, principal, lambda session, definition: self._update_transition(session, definition, command))

    def delete_transition(self, command: DeleteProcessTransitionCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.DELETE_PROCESS_TRANSITION], metadata=metadata, principal=principal)
        return self._change_transition(command.process_definition_id, metadata, principal, lambda session, definition: self._delete_transition(session, definition, command.transition_id))

    def publish(self, command: ProcessLifecycleCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.PUBLISH_PROCESS_DEFINITION], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            definition = self._draft_definition(session, command.process_definition_id, organization_id)
            stages = session.scalars(select(ProcessStage).where(ProcessStage.process_definition_id == definition.id)).all()
            start_count = sum(stage.stage_type == "start" for stage in stages)
            terminal_count = sum(stage.stage_type == "terminal" for stage in stages)
            if start_count != 1:
                raise _validation("a published process definition requires exactly one start stage")
            if terminal_count < 1:
                raise _validation("a published process definition requires at least one terminal stage")
            definition.lifecycle = _PUBLISHED
            definition.published_at = utc_now()
            definition.updated_at = definition.published_at
            self._record(
                session,
                definition,
                "process_definition.published",
                {"version": definition.version, "stage_count": len(stages)},
                metadata,
            )
            result = _definition_read(session, definition)
            unit_of_work.commit()
            return result

    def retire(self, command: ProcessLifecycleCommand, metadata: RequestMetadata, principal: AuthenticatedPrincipal) -> ProcessDefinitionRead:
        enforce_command_boundary(command_contracts[WS006CommandName.RETIRE_PROCESS_DEFINITION], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            definition = self._definition(session, command.process_definition_id, organization_id, lock=True)
            if definition.lifecycle != _PUBLISHED:
                raise _conflict("only a published process definition can be retired")
            definition.lifecycle = _RETIRED
            definition.retired_at = utc_now()
            definition.updated_at = definition.retired_at
            self._record(
                session,
                definition,
                "process_definition.retired",
                {"version": definition.version},
                metadata,
            )
            result = _definition_read(session, definition)
            unit_of_work.commit()
            return result

    def _change_stage(self, definition_id: UUID, metadata: RequestMetadata, principal: AuthenticatedPrincipal, change) -> ProcessDefinitionRead:
        organization_id = _principal_organization_id(principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            definition = self._draft_definition(session, definition_id, organization_id)
            change(session, definition)
            definition.updated_at = utc_now()
            result = _definition_read(session, definition)
            unit_of_work.commit()
            return result

    def _change_transition(self, definition_id: UUID, metadata: RequestMetadata, principal: AuthenticatedPrincipal, change) -> ProcessDefinitionRead:
        return self._change_stage(definition_id, metadata, principal, change)

    @staticmethod
    def _definition(session: Session, definition_id: UUID, organization_id: UUID, *, lock: bool = False) -> ProcessDefinition:
        statement = (
            select(ProcessDefinition)
            .where(ProcessDefinition.id == definition_id)
            .where(ProcessDefinition.organization_id == organization_id)
        )
        if lock:
            statement = statement.with_for_update()
        definition = session.scalar(statement)
        if definition is None:
            raise _not_found()
        return definition

    def _draft_definition(self, session: Session, definition_id: UUID, organization_id: UUID) -> ProcessDefinition:
        definition = self._definition(session, definition_id, organization_id, lock=True)
        if definition.lifecycle != _DRAFT:
            raise _conflict("published and retired process definitions are immutable; create a new version")
        return definition

    @staticmethod
    def _valid_stage_type(stage_type: str) -> None:
        if stage_type not in _STAGE_TYPES:
            raise _validation("unsupported process stage type")

    def _add_stage(self, session: Session, definition: ProcessDefinition, command: AddProcessStageCommand) -> None:
        self._valid_stage_type(command.stage_type)
        duplicate = session.scalar(
            select(ProcessStage.id)
            .where(ProcessStage.process_definition_id == definition.id)
            .where(or_(ProcessStage.stage_key == command.stage_key, ProcessStage.display_order == command.display_order))
        )
        if duplicate is not None:
            raise _conflict("process stage key and display order must be unique within a process version")
        session.add(
            ProcessStage(
                organization_id=definition.organization_id,
                process_definition_id=definition.id,
                stage_key=command.stage_key,
                name=command.name,
                description=command.description,
                stage_type=command.stage_type,
                display_order=command.display_order,
                metadata_json=command.metadata_json,
            )
        )
        session.flush()

    def _update_stage(self, session: Session, definition: ProcessDefinition, command: UpdateProcessStageCommand) -> None:
        self._valid_stage_type(command.stage_type)
        stage = session.scalar(
            select(ProcessStage)
            .where(ProcessStage.id == command.stage_id)
            .where(ProcessStage.process_definition_id == definition.id)
            .where(ProcessStage.organization_id == definition.organization_id)
        )
        if stage is None:
            raise _not_found()
        duplicate = session.scalar(
            select(ProcessStage.id)
            .where(ProcessStage.process_definition_id == definition.id)
            .where(ProcessStage.id != stage.id)
            .where(or_(ProcessStage.stage_key == command.stage_key, ProcessStage.display_order == command.display_order))
        )
        if duplicate is not None:
            raise _conflict("process stage key and display order must be unique within a process version")
        stage.stage_key = command.stage_key
        stage.name = command.name
        stage.description = command.description
        stage.stage_type = command.stage_type
        stage.display_order = command.display_order
        stage.metadata_json = command.metadata_json
        session.flush()

    @staticmethod
    def _delete_stage(session: Session, definition: ProcessDefinition, stage_id: UUID) -> None:
        stage = session.scalar(
            select(ProcessStage)
            .where(ProcessStage.id == stage_id)
            .where(ProcessStage.process_definition_id == definition.id)
            .where(ProcessStage.organization_id == definition.organization_id)
        )
        if stage is None:
            raise _not_found()
        transitions = session.scalars(
            select(ProcessTransition).where(
                ProcessTransition.process_definition_id == definition.id,
                or_(ProcessTransition.from_stage_id == stage.id, ProcessTransition.to_stage_id == stage.id),
            )
        ).all()
        for transition in transitions:
            session.delete(transition)
        session.delete(stage)
        session.flush()

    def _add_transition(self, session: Session, definition: ProcessDefinition, command: AddProcessTransitionCommand) -> None:
        stages = session.scalars(
            select(ProcessStage)
            .where(ProcessStage.process_definition_id == definition.id)
            .where(ProcessStage.organization_id == definition.organization_id)
            .where(ProcessStage.id.in_((command.from_stage_id, command.to_stage_id)))
        ).all()
        if {stage.id for stage in stages} != {command.from_stage_id, command.to_stage_id}:
            raise _validation("a process transition cannot reference a stage outside its process version")
        duplicate = session.scalar(
            select(ProcessTransition.id)
            .where(ProcessTransition.process_definition_id == definition.id)
            .where(ProcessTransition.from_stage_id == command.from_stage_id)
            .where(ProcessTransition.to_stage_id == command.to_stage_id)
        )
        if duplicate is not None:
            raise _conflict("this process transition already exists")
        session.add(
            ProcessTransition(
                organization_id=definition.organization_id,
                process_definition_id=definition.id,
                from_stage_id=command.from_stage_id,
                to_stage_id=command.to_stage_id,
                name=command.name,
            )
        )
        session.flush()

    @staticmethod
    def _update_transition(session: Session, definition: ProcessDefinition, command: UpdateProcessTransitionCommand) -> None:
        transition = session.scalar(
            select(ProcessTransition)
            .where(ProcessTransition.id == command.transition_id)
            .where(ProcessTransition.process_definition_id == definition.id)
            .where(ProcessTransition.organization_id == definition.organization_id)
        )
        if transition is None:
            raise _not_found()
        transition.name = command.name
        session.flush()

    @staticmethod
    def _delete_transition(session: Session, definition: ProcessDefinition, transition_id: UUID) -> None:
        transition = session.scalar(
            select(ProcessTransition)
            .where(ProcessTransition.id == transition_id)
            .where(ProcessTransition.process_definition_id == definition.id)
            .where(ProcessTransition.organization_id == definition.organization_id)
        )
        if transition is None:
            raise _not_found()
        session.delete(transition)
        session.flush()

    @staticmethod
    def _record(session: Session, definition: ProcessDefinition, event_type: str, payload: dict[str, object], metadata: RequestMetadata) -> None:
        record_event(
            session,
            event_type=event_type,
            aggregate_type="process_definition",
            aggregate_id=definition.id,
            organization_id=definition.organization_id,
            correlation_id=UUID(metadata.correlation_id),
            causation_id=UUID(metadata.causation_id) if metadata.causation_id else None,
            payload=payload,
        )


@dataclass(frozen=True, slots=True)
class ProcessDefinitionQueryService:
    """Owns governed, tenant-scoped reads of process definitions."""

    def list(self, session: Session, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> list[ProcessDefinitionListItem]:
        enforce_query_boundary(query_contracts[WS006QueryName.LIST_PROCESS_DEFINITIONS], metadata=metadata, principal=principal)
        definitions = session.scalars(
            select(ProcessDefinition)
            .where(ProcessDefinition.organization_id == _principal_organization_id(principal))
            .order_by(ProcessDefinition.name.asc(), ProcessDefinition.version.desc())
        ).all()
        return [ProcessDefinitionListItem.model_validate(definition) for definition in definitions]

    def retrieve(self, session: Session, definition_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessDefinitionRead:
        enforce_query_boundary(query_contracts[WS006QueryName.RETRIEVE_PROCESS_DEFINITION], metadata=metadata, principal=principal)
        definition = session.scalar(
            select(ProcessDefinition)
            .where(ProcessDefinition.id == definition_id)
            .where(ProcessDefinition.organization_id == _principal_organization_id(principal))
        )
        if definition is None:
            raise _not_found()
        return _definition_read(session, definition)


def _instance_not_found() -> ApplicationError:
    return ApplicationError(
        ApplicationErrorCode.RESOURCE_NOT_FOUND,
        "process instance not found",
        {"resource": "process_instance"},
    )


def _instance_conflict(reason: str) -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.CONFLICT, reason, {"resource": "process_instance"})


def _instance_read(instance: ProcessInstance) -> ProcessInstanceRead:
    return ProcessInstanceRead.model_validate(instance)


@dataclass(slots=True)
class ProcessRuntimeService:
    """Own Process Instance state transitions and their atomic evidence."""

    persistence: PersistenceRuntime

    def start(
        self,
        command: StartProcessInstanceCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> ProcessInstanceRead:
        enforce_command_boundary(command_contracts[WS006CommandName.START_PROCESS_INSTANCE], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        idempotency_key = self._idempotency_key(metadata)
        fingerprint = self._fingerprint("start", {"process_definition_id": str(command.process_definition_id)})
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
                session = unit_of_work.session
                existing = session.scalar(
                    select(ProcessInstance)
                    .where(ProcessInstance.organization_id == organization_id)
                    .where(ProcessInstance.start_idempotency_key == idempotency_key)
                )
                if existing is not None:
                    return self._start_replay(existing, fingerprint)
                definition = session.scalar(
                    select(ProcessDefinition)
                    .where(ProcessDefinition.id == command.process_definition_id)
                    .where(ProcessDefinition.organization_id == organization_id)
                    .with_for_update()
                )
                if definition is None:
                    raise _not_found()
                if definition.lifecycle != _PUBLISHED:
                    raise _instance_conflict("process instances can start only from a published process definition")
                start_stage = session.scalar(
                    select(ProcessStage)
                    .where(ProcessStage.process_definition_id == definition.id)
                    .where(ProcessStage.organization_id == organization_id)
                    .where(ProcessStage.stage_type == "start")
                )
                if start_stage is None:
                    raise _instance_conflict("published process definition has no start stage")
                instance = ProcessInstance(
                    organization_id=organization_id,
                    process_definition_id=definition.id,
                    process_definition_version=definition.version,
                    current_stage_id=start_stage.id,
                    lifecycle="active",
                    created_by_subject_id=principal.actor_id,
                    start_idempotency_key=idempotency_key,
                    start_request_fingerprint=fingerprint,
                )
                session.add(instance)
                session.flush()
                payload = {
                    "process_instance_id": str(instance.id),
                    "process_definition_id": str(definition.id),
                    "process_definition_version": definition.version,
                    "current_stage_id": str(start_stage.id),
                    "current_stage_key": start_stage.stage_key,
                    "lifecycle": instance.lifecycle,
                    "version": instance.version,
                }
                self._append_event(session, instance, "process_instance.started", payload, principal, idempotency_key, fingerprint)
                self._record_domain_event(session, instance, "process_instance.started", payload, metadata)
                result = _instance_read(instance)
                unit_of_work.commit()
                return result
        except IntegrityError as error:
            if not self._is_start_idempotency_violation(error):
                raise
            return self._resolve_start_replay(organization_id, idempotency_key, fingerprint)

    def transition(
        self,
        command: TransitionProcessInstanceCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> ProcessInstanceRead:
        enforce_command_boundary(command_contracts[WS006CommandName.TRANSITION_PROCESS_INSTANCE], metadata=metadata, principal=principal)
        return self._mutate(
            command.process_instance_id,
            command.expected_version,
            metadata,
            principal,
            "transition",
            {"transition_id": str(command.transition_id), "expected_version": command.expected_version},
            lambda session, instance, idempotency_key, fingerprint: self._transition(
                session,
                instance,
                command.transition_id,
                metadata,
                principal,
                idempotency_key,
                fingerprint,
            ),
        )

    def cancel(
        self,
        command: CancelProcessInstanceCommand,
        metadata: RequestMetadata,
        principal: AuthenticatedPrincipal,
    ) -> ProcessInstanceRead:
        enforce_command_boundary(command_contracts[WS006CommandName.CANCEL_PROCESS_INSTANCE], metadata=metadata, principal=principal)
        return self._mutate(
            command.process_instance_id,
            command.expected_version,
            metadata,
            principal,
            "cancel",
            {"expected_version": command.expected_version, "reason": command.reason},
            lambda session, instance, idempotency_key, fingerprint: self._cancel(
                session,
                instance,
                command.reason,
                metadata,
                principal,
                idempotency_key,
                fingerprint,
            ),
        )

    def _mutate(self, instance_id: UUID, expected_version: int, metadata: RequestMetadata, principal: AuthenticatedPrincipal, command_type: str, request: dict[str, object], mutation) -> ProcessInstanceRead:
        organization_id = _principal_organization_id(principal)
        idempotency_key = self._idempotency_key(metadata)
        fingerprint = self._fingerprint(command_type, request)
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            session = unit_of_work.session
            instance = session.scalar(
                select(ProcessInstance)
                .where(ProcessInstance.id == instance_id)
                .where(ProcessInstance.organization_id == organization_id)
                .with_for_update()
            )
            if instance is None:
                raise _instance_not_found()
            replay = session.scalar(
                select(ProcessInstanceEvent)
                .where(ProcessInstanceEvent.organization_id == organization_id)
                .where(ProcessInstanceEvent.process_instance_id == instance.id)
                .where(ProcessInstanceEvent.idempotency_key == idempotency_key)
            )
            if replay is not None:
                if replay.request_fingerprint != fingerprint:
                    raise _instance_conflict("idempotency key was previously used for a different process instance command")
                return _instance_read(instance)
            if instance.version != expected_version:
                raise _instance_conflict("process instance version does not match expected version")
            mutation(session, instance, idempotency_key, fingerprint)
            result = _instance_read(instance)
            unit_of_work.commit()
            return result

    def _transition(self, session: Session, instance: ProcessInstance, transition_id: UUID, metadata: RequestMetadata, principal: AuthenticatedPrincipal, idempotency_key: str, fingerprint: str) -> None:
        if instance.lifecycle != "active":
            raise _instance_conflict("completed and cancelled process instances cannot transition")
        transition = session.scalar(
            select(ProcessTransition)
            .where(ProcessTransition.id == transition_id)
            .where(ProcessTransition.process_definition_id == instance.process_definition_id)
            .where(ProcessTransition.organization_id == instance.organization_id)
        )
        if transition is None or transition.from_stage_id != instance.current_stage_id:
            raise _instance_conflict("transition is not valid from the current process stage")
        previous_stage = session.get(ProcessStage, instance.current_stage_id)
        target_stage = session.scalar(
            select(ProcessStage)
            .where(ProcessStage.id == transition.to_stage_id)
            .where(ProcessStage.process_definition_id == instance.process_definition_id)
            .where(ProcessStage.organization_id == instance.organization_id)
        )
        if previous_stage is None or target_stage is None:
            raise _instance_conflict("process transition references an unavailable process stage")
        previous_lifecycle = instance.lifecycle
        instance.current_stage_id = target_stage.id
        instance.version += 1
        instance.updated_at = utc_now()
        payload = {
            "process_instance_id": str(instance.id),
            "transition_id": str(transition.id),
            "transition_name": transition.name,
            "previous_stage_id": str(previous_stage.id),
            "previous_stage_key": previous_stage.stage_key,
            "current_stage_id": str(target_stage.id),
            "current_stage_key": target_stage.stage_key,
            "previous_lifecycle": previous_lifecycle,
            "lifecycle": instance.lifecycle,
            "version": instance.version,
        }
        self._append_event(session, instance, "process_instance.transitioned", payload, principal, idempotency_key, fingerprint)
        self._record_domain_event(session, instance, "process_instance.transitioned", payload, metadata)
        if target_stage.stage_type == "terminal":
            instance.lifecycle = "completed"
            instance.completed_at = utc_now()
            instance.updated_at = instance.completed_at
            completion = {
                **payload,
                "previous_lifecycle": "active",
                "lifecycle": "completed",
                "version": instance.version,
            }
            self._append_event(session, instance, "process_instance.completed", completion, principal, None, None)
            self._record_domain_event(session, instance, "process_instance.completed", completion, metadata)

    def _cancel(self, session: Session, instance: ProcessInstance, reason: str, metadata: RequestMetadata, principal: AuthenticatedPrincipal, idempotency_key: str, fingerprint: str) -> None:
        if instance.lifecycle != "active":
            raise _instance_conflict("completed and cancelled process instances cannot be cancelled")
        stage = session.get(ProcessStage, instance.current_stage_id)
        if stage is None:
            raise _instance_conflict("process instance current stage is unavailable")
        instance.lifecycle = "cancelled"
        instance.cancelled_at = utc_now()
        instance.cancellation_reason = reason
        instance.version += 1
        instance.updated_at = instance.cancelled_at
        payload = {
            "process_instance_id": str(instance.id),
            "current_stage_id": str(stage.id),
            "current_stage_key": stage.stage_key,
            "previous_lifecycle": "active",
            "lifecycle": "cancelled",
            "reason": reason,
            "version": instance.version,
        }
        self._append_event(session, instance, "process_instance.cancelled", payload, principal, idempotency_key, fingerprint)
        self._record_domain_event(session, instance, "process_instance.cancelled", payload, metadata)

    @staticmethod
    def _idempotency_key(metadata: RequestMetadata) -> str:
        if metadata.idempotency_key is None:
            raise ApplicationError(ApplicationErrorCode.PRECONDITION_FAILED, "idempotency key is required for process runtime commands", {"resource": "process_instance"})
        return metadata.idempotency_key

    @staticmethod
    def _fingerprint(command_type: str, request: dict[str, object]) -> str:
        return sha256(dumps({"command": command_type, "request": request}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _start_replay(instance: ProcessInstance, fingerprint: str) -> ProcessInstanceRead:
        if instance.start_request_fingerprint != fingerprint:
            raise _instance_conflict("idempotency key was previously used for a different process instance command")
        return _instance_read(instance)

    def _resolve_start_replay(self, organization_id: UUID, idempotency_key: str, fingerprint: str) -> ProcessInstanceRead:
        with UnitOfWork(self.persistence, OperationScope()) as unit_of_work:
            instance = unit_of_work.session.scalar(
                select(ProcessInstance)
                .where(ProcessInstance.organization_id == organization_id)
                .where(ProcessInstance.start_idempotency_key == idempotency_key)
            )
            if instance is None:
                raise _instance_conflict("process instance start could not be replayed")
            return self._start_replay(instance, fingerprint)

    @staticmethod
    def _is_start_idempotency_violation(error: IntegrityError) -> bool:
        return isinstance(error.orig, UniqueViolation) and error.orig.diag.constraint_name == "uq_process_instances_start_idempotency"

    @staticmethod
    def _append_event(session: Session, instance: ProcessInstance, event_type: str, payload: dict[str, object], principal: AuthenticatedPrincipal, idempotency_key: str | None, fingerprint: str | None) -> ProcessInstanceEvent:
        sequence_number = (session.scalar(
            select(func.coalesce(func.max(ProcessInstanceEvent.sequence_number), 0))
            .where(ProcessInstanceEvent.organization_id == instance.organization_id)
            .where(ProcessInstanceEvent.process_instance_id == instance.id)
        ) or 0) + 1
        event = ProcessInstanceEvent(
            organization_id=instance.organization_id,
            process_instance_id=instance.id,
            occurred_at=utc_now(),
            event_type=event_type,
            actor_subject_id=principal.actor_id,
            payload_json=payload,
            sequence_number=sequence_number,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def _record_domain_event(session: Session, instance: ProcessInstance, event_type: str, payload: dict[str, object], metadata: RequestMetadata) -> None:
        record_event(
            session,
            event_type=event_type,
            aggregate_type="process_instance",
            aggregate_id=instance.id,
            organization_id=instance.organization_id,
            correlation_id=UUID(metadata.correlation_id),
            causation_id=UUID(metadata.causation_id) if metadata.causation_id else None,
            payload=payload,
        )


@dataclass(frozen=True, slots=True)
class ProcessRuntimeQueryService:
    """Owns governed, tenant-scoped Process Instance reads."""

    def list(self, session: Session, principal: AuthenticatedPrincipal, metadata: RequestMetadata, limit: int, offset: int) -> ProcessInstancePage:
        enforce_query_boundary(query_contracts[WS006QueryName.LIST_PROCESS_INSTANCES], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        statement = select(ProcessInstance).where(ProcessInstance.organization_id == organization_id)
        total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        instances = session.scalars(statement.order_by(ProcessInstance.updated_at.desc(), ProcessInstance.id.desc()).offset(offset).limit(limit)).all()
        return ProcessInstancePage(items=[_instance_read(instance) for instance in instances], total=total, limit=limit, offset=offset)

    def retrieve(self, session: Session, instance_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessInstanceRead:
        enforce_query_boundary(query_contracts[WS006QueryName.RETRIEVE_PROCESS_INSTANCE], metadata=metadata, principal=principal)
        instance = session.scalar(select(ProcessInstance).where(ProcessInstance.id == instance_id).where(ProcessInstance.organization_id == _principal_organization_id(principal)))
        if instance is None:
            raise _instance_not_found()
        return _instance_read(instance)

    def timeline(self, session: Session, instance_id: UUID, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> ProcessInstanceTimeline:
        enforce_query_boundary(query_contracts[WS006QueryName.RETRIEVE_PROCESS_INSTANCE_TIMELINE], metadata=metadata, principal=principal)
        organization_id = _principal_organization_id(principal)
        instance = session.scalar(select(ProcessInstance).where(ProcessInstance.id == instance_id).where(ProcessInstance.organization_id == organization_id))
        if instance is None:
            raise _instance_not_found()
        events = session.scalars(
            select(ProcessInstanceEvent)
            .where(ProcessInstanceEvent.organization_id == organization_id)
            .where(ProcessInstanceEvent.process_instance_id == instance.id)
            .order_by(ProcessInstanceEvent.sequence_number.asc())
        ).all()
        return ProcessInstanceTimeline(items=[ProcessInstanceEventRead.model_validate(event) for event in events])

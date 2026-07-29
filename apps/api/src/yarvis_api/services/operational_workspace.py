"""Read-only, bounded Mission Work workspace composition."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.contracts import WS006QueryName, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.service_boundary import enforce_query_boundary
from yarvis_api.models.mission_work import MissionWorkItem
from yarvis_api.models.mission_work_event import MissionWorkEvent
from yarvis_api.models.operational_economics import EconomicFact
from yarvis_api.models.process import ProcessDefinition, ProcessInstance, ProcessInstanceEvent, ProcessInstanceWorkLink, ProcessStage
from yarvis_api.schemas.mission_work import MissionWorkEventRead, MissionWorkItemRead, MissionWorkTimeline
from yarvis_api.schemas.operational_economics import EconomicSummary
from yarvis_api.schemas.operational_workspace import OperationalWorkspaceProcessInstance, OperationalWorkspaceProcessLink, OperationalWorkspaceRead
from yarvis_api.services.inbound_intake import _principal_organization_id
from yarvis_api.services.operational_economics import build_direct_summary


def _not_found() -> ApplicationError:
    return ApplicationError(ApplicationErrorCode.RESOURCE_NOT_FOUND, "mission work item not found", {"resource": "mission_work_item"})


@dataclass(frozen=True, slots=True)
class OperationalWorkspaceQueryService:
    """Composes owner read models without persisting a second workspace model."""

    def retrieve(self, session: Session, work_item_id: UUID, currency: str, principal: AuthenticatedPrincipal, metadata: RequestMetadata) -> OperationalWorkspaceRead:
        enforce_query_boundary(query_contracts[WS006QueryName.RETRIEVE_OPERATIONAL_WORKSPACE], metadata=metadata, principal=principal)
        if currency != currency.upper() or len(currency) != 3:
            raise ApplicationError(ApplicationErrorCode.VALIDATION_FAILED, "currency must be uppercase ISO-4217 form", {"resource": "operational_workspace"})
        organization_id = _principal_organization_id(principal)
        work = session.scalar(select(MissionWorkItem).where(MissionWorkItem.id == work_item_id).where(MissionWorkItem.organization_id == organization_id))
        if work is None:
            raise _not_found()
        timeline_items = session.scalars(select(MissionWorkEvent).where(MissionWorkEvent.organization_id == organization_id).where(MissionWorkEvent.work_item_id == work.id).order_by(MissionWorkEvent.sequence_number.asc())).all()
        last_transition_sequence = (
            select(func.max(ProcessInstanceEvent.sequence_number))
            .where(ProcessInstanceEvent.organization_id == organization_id)
            .where(ProcessInstanceEvent.process_instance_id == ProcessInstance.id)
            .where(ProcessInstanceEvent.event_type == "process_instance.transitioned")
            .correlate(ProcessInstance).scalar_subquery()
        )
        rows = session.execute(
            select(ProcessInstanceWorkLink, ProcessInstance, ProcessDefinition, ProcessStage, ProcessInstanceEvent)
            .join(ProcessInstance, and_(ProcessInstance.id == ProcessInstanceWorkLink.process_instance_id, ProcessInstance.organization_id == ProcessInstanceWorkLink.organization_id))
            .join(ProcessDefinition, and_(ProcessDefinition.id == ProcessInstance.process_definition_id, ProcessDefinition.organization_id == ProcessInstance.organization_id))
            .join(ProcessStage, and_(ProcessStage.id == ProcessInstance.current_stage_id, ProcessStage.process_definition_id == ProcessInstance.process_definition_id, ProcessStage.organization_id == ProcessInstance.organization_id))
            .outerjoin(ProcessInstanceEvent, and_(ProcessInstanceEvent.organization_id == organization_id, ProcessInstanceEvent.process_instance_id == ProcessInstance.id, ProcessInstanceEvent.sequence_number == last_transition_sequence))
            .where(ProcessInstanceWorkLink.organization_id == organization_id)
            .where(ProcessInstanceWorkLink.mission_work_item_id == work.id)
            .order_by(ProcessInstanceWorkLink.unlinked_at.is_not(None).asc(), ProcessInstanceWorkLink.linked_at.desc(), ProcessInstance.id.asc())
        ).all()
        instance_ids = [instance.id for _, instance, _, _, _ in rows]
        superseded = select(EconomicFact.supersedes_fact_id).where(EconomicFact.organization_id == organization_id).where(EconomicFact.supersedes_fact_id.is_not(None))
        facts = session.scalars(
            select(EconomicFact).where(EconomicFact.organization_id == organization_id).where(EconomicFact.currency == currency).where(~EconomicFact.id.in_(superseded)).where(
                or_(
                    and_(EconomicFact.subject_type == "mission_work_item", EconomicFact.subject_id == work.id),
                    and_(EconomicFact.subject_type == "process_instance", EconomicFact.subject_id.in_(instance_ids or [UUID(int=0)])),
                )
            ).order_by(EconomicFact.effective_at.asc(), EconomicFact.id.asc())
        ).all()
        facts_by_subject: dict[tuple[str, UUID], list[EconomicFact]] = defaultdict(list)
        for fact in facts:
            facts_by_subject[(fact.subject_type, fact.subject_id)].append(fact)
        grouped: dict[UUID, OperationalWorkspaceProcessInstance] = {}
        for link, instance, definition, stage, last_transition in rows:
            existing = grouped.get(instance.id)
            link_read = OperationalWorkspaceProcessLink(id=link.id, relationship_type=link.relationship_type, linked_at=link.linked_at, unlinked_at=link.unlinked_at)
            if existing is not None:
                existing.links.append(link_read)
                continue
            grouped[instance.id] = OperationalWorkspaceProcessInstance(
                id=instance.id, lifecycle=instance.lifecycle, process_definition_id=definition.id,
                process_definition_name=definition.name, process_definition_version=instance.process_definition_version,
                current_stage_id=stage.id, current_stage_key=stage.stage_key, current_stage_name=stage.name,
                current_stage_type=stage.stage_type, created_at=instance.created_at, updated_at=instance.updated_at,
                completed_at=instance.completed_at, cancelled_at=instance.cancelled_at, cancellation_reason=instance.cancellation_reason,
                last_transition=MissionWorkEventRead.model_validate(last_transition) if last_transition else None,
                links=[link_read], economic_summary=build_direct_summary("process_instance", instance.id, currency, facts_by_subject[("process_instance", instance.id)], metadata.requested_at),
            )
        processes = list(grouped.values())
        participants = sorted({value for value in [work.created_by_subject_id, work.assignee_subject_id, *(event.actor_subject_id for event in timeline_items)] if value})
        activity_times = [work.updated_at, *(event.occurred_at for event in timeline_items), *(process.updated_at for process in processes)]
        return OperationalWorkspaceRead(
            work_item=MissionWorkItemRead.model_validate(work), participants=participants, process_instances=processes,
            timeline=MissionWorkTimeline(items=[MissionWorkEventRead.model_validate(event) for event in timeline_items]),
            economic_summary=build_direct_summary("mission_work_item", work.id, currency, facts_by_subject[("mission_work_item", work.id)], metadata.requested_at),
            active_process_instance_count=sum(any(link.unlinked_at is None for link in process.links) for process in processes),
            historical_process_instance_count=sum(all(link.unlinked_at is not None for link in process.links) for process in processes),
            last_activity_at=max(activity_times),
        )

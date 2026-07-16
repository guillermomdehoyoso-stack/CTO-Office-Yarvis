import hashlib
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from yarvis_api.clock import utc_now
from yarvis_api.models.observation_engine import (
    DocumentRecord,
    Observation,
    ResolutionDecision,
    SourceRecord,
)


STATUS_TERMINAL = {"rejected", "superseded"}


def compute_hash(file_hash: str | None, file_content: str | None) -> str:
    if file_hash:
        return file_hash
    if file_content is None:
        raise ValueError("file_hash or file_content is required")
    return hashlib.sha256(file_content.encode("utf-8")).hexdigest()


def register_source(
    db: Session,
    *,
    source_type: str,
    source_name: str,
    received_at,
    metadata: dict,
    classification: str | None,
    external_source_id: str | None,
) -> SourceRecord:
    source = SourceRecord(
        source_type=source_type,
        source_name=source_name,
        received_at=received_at or utc_now(),
        metadata_json=metadata or {},
        classification=classification,
        external_source_id=external_source_id,
    )
    db.add(source)
    db.flush()
    return source


def register_document(
    db: Session,
    *,
    source_id: UUID,
    filename: str | None,
    media_type: str,
    file_hash: str | None,
    file_content: str | None,
    byte_size: int | None,
    report_date,
    storage_reference: str | None,
    extraction_status: str,
    classification: str | None,
    metadata: dict,
    allow_reprocess: bool,
) -> tuple[DocumentRecord, bool, str | None]:
    digest = compute_hash(file_hash, file_content)
    existing = db.scalar(select(DocumentRecord).where(DocumentRecord.file_hash == digest).order_by(DocumentRecord.created_at.desc()))
    if existing and not allow_reprocess:
        return existing, False, "file_hash"

    record = DocumentRecord(
        source_id=source_id,
        filename=filename,
        media_type=media_type,
        file_hash=digest,
        byte_size=byte_size,
        report_date=report_date,
        storage_reference=storage_reference,
        extraction_status=extraction_status,
        classification=classification,
        metadata_json=metadata or {},
        processed_at=utc_now() if allow_reprocess else None,
    )
    db.add(record)
    db.flush()
    return record, True, None


def create_observation(db: Session, **kwargs) -> Observation:
    observation = Observation(observed_at=kwargs.pop("observed_at", None) or utc_now(), **kwargs)
    db.add(observation)
    db.flush()
    return observation


def list_observations_query(*, domain: str | None, subject_type: str | None, subject_reference: str | None, status: str | None) -> Select:
    query = select(Observation)
    if domain:
        query = query.where(Observation.domain == domain)
    if subject_type:
        query = query.where(Observation.subject_type == subject_type)
    if subject_reference:
        query = query.where(Observation.subject_reference == subject_reference)
    if status:
        query = query.where(Observation.confirmation_status == status)
    return query.order_by(Observation.observed_at.desc(), Observation.created_at.desc())


def _ensure_mutable(observation: Observation) -> None:
    if observation.confirmation_status in STATUS_TERMINAL:
        raise ValueError("observation is immutable in terminal status")


def confirm_observation(db: Session, observation: Observation, actor: str) -> Observation:
    _ensure_mutable(observation)
    observation.confirmation_status = "confirmed"
    observation.confirmed_by = actor
    observation.confirmed_at = utc_now()
    db.flush()
    return observation


def reject_observation(db: Session, observation: Observation, actor: str) -> Observation:
    _ensure_mutable(observation)
    observation.confirmation_status = "rejected"
    observation.confirmed_by = actor
    observation.confirmed_at = utc_now()
    db.flush()
    return observation


def mark_conflict(db: Session, observation: Observation, actor: str) -> Observation:
    _ensure_mutable(observation)
    observation.confirmation_status = "conflicted"
    observation.confirmed_by = actor
    observation.confirmed_at = utc_now()
    db.flush()
    return observation


def supersede_observation(db: Session, observation: Observation, replacement_observation_id: UUID, actor: str) -> Observation:
    _ensure_mutable(observation)
    observation.confirmation_status = "superseded"
    observation.supersedes_observation_id = replacement_observation_id
    observation.confirmed_by = actor
    observation.confirmed_at = utc_now()
    db.flush()
    return observation


def create_resolution_proposal(
    db: Session,
    *,
    observation_id: UUID,
    candidate_entity_type: str,
    candidate_entity_id: str | None,
    confidence: float,
    explanation: str,
) -> ResolutionDecision:
    decision = ResolutionDecision(
        observation_id=observation_id,
        candidate_entity_type=candidate_entity_type,
        candidate_entity_id=candidate_entity_id,
        confidence=confidence,
        explanation=explanation,
        decision_status="proposed",
    )
    db.add(decision)
    db.flush()
    return decision


def confirm_resolution(db: Session, decision: ResolutionDecision, actor: str) -> ResolutionDecision:
    decision.decision_status = "confirmed"
    decision.decided_by = actor
    decision.decided_at = utc_now()
    db.flush()
    return decision


def reject_resolution(db: Session, decision: ResolutionDecision, actor: str) -> ResolutionDecision:
    decision.decision_status = "rejected"
    decision.decided_by = actor
    decision.decided_at = utc_now()
    db.flush()
    return decision

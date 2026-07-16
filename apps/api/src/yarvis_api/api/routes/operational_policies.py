from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.database import get_db
from yarvis_api.models.observation_engine import OperationalPolicy, PolicyEvaluation
from yarvis_api.schemas.observation_engine import (
    OperationalPolicyCreate,
    OperationalPolicyRead,
    PolicyEvaluateRequest,
    PolicyEvaluationRead,
)
from yarvis_api.services.policy_engine import evaluate_policy, get_active_policy, validate_policy_configuration

router = APIRouter(tags=["operational-policies"])


@router.get("/operational-policies", response_model=list[OperationalPolicyRead])
def list_policies(db: Session = Depends(get_db)):
    return db.scalars(select(OperationalPolicy).order_by(OperationalPolicy.policy_key, OperationalPolicy.version.desc())).all()


@router.post("/operational-policies", response_model=OperationalPolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(payload: OperationalPolicyCreate, db: Session = Depends(get_db)):
    try:
        validate_policy_configuration(payload.configuration)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = db.scalar(
        select(OperationalPolicy).where(
            OperationalPolicy.policy_key == payload.policy_key,
            OperationalPolicy.version == payload.version,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="policy_key + version already exists")

    item = OperationalPolicy(**payload.model_dump(mode="python"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/operational-policies/evaluate", response_model=PolicyEvaluationRead)
def evaluate(payload: PolicyEvaluateRequest, db: Session = Depends(get_db)):
    policy = get_active_policy(db, payload.policy_key)
    if policy is None:
        raise HTTPException(status_code=404, detail="active policy not found")

    item = evaluate_policy(
        db,
        policy=policy,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        facts=payload.facts,
        evidence_references=payload.evidence_references,
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/policy-evaluations", response_model=list[PolicyEvaluationRead])
def list_evaluations(db: Session = Depends(get_db)):
    return db.scalars(select(PolicyEvaluation).order_by(PolicyEvaluation.evaluated_at.desc())).all()

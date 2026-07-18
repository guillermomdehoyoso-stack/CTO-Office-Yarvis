from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from yarvis_api.database import get_db
from yarvis_api.schemas.store_analytics import StoreAnalyticsFilters
from yarvis_api.schemas.store_intelligence import HumanDecisionInput, RecoveryQueueFilters
from yarvis_api.schemas.store_intelligence_api import StoreProfilePage
from yarvis_api.services.store_intelligence_runtime import StoreIntelligenceRuntime

router=APIRouter(prefix="/api/store-intelligence",tags=["store-intelligence"])
def runtime(db): return StoreIntelligenceRuntime(db)

@router.get("/profiles",response_model=StoreProfilePage)
def profiles(store_id:str|None=None,client_id:str|None=None,evidence_completeness:str|None=None,pending_only:bool=False,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    items=runtime(db).profiles(); items=[p for p in items if (store_id is None or p.store_id==store_id) and (client_id is None or p.confirmed_client_id==client_id) and (evidence_completeness is None or p.evidence_completeness==evidence_completeness) and (not pending_only or (p.requires_human_review and p.latest_human_decision not in {"resolved","no_action"}))]
    return StoreProfilePage(items[offset:offset+limit],len(items),limit,offset)
@router.get("/profiles/{store_id}")
def profile(store_id:str,db:Session=Depends(get_db)):
    item=runtime(db).profile(store_id)
    if not item: raise HTTPException(404,"store not found")
    return item
@router.get("/recovery-queue")
def recovery_queue(recommended_action:str|None=None,action_priority:str|None=None,minimum_months_no_use:int|None=None,operational_block:bool|None=None,activation_failure:bool|None=None,has_historical_value_evidence:bool|None=None,pending_action:bool|None=None,client_id:str|None=None,db:Session=Depends(get_db)):
    return runtime(db).recovery_queue(RecoveryQueueFilters(recommended_action,action_priority,minimum_months_no_use,operational_block,activation_failure,has_historical_value_evidence,pending_action,client_id))
@router.get("/analytics")
def analytics(analytical_segment:str|None=None,attention_level:str|None=None,minimum_months_no_use:int|None=None,has_historical_value_evidence:bool|None=None,operational_block:bool|None=None,activation_failure:bool|None=None,terminal_recovery_candidate:bool|None=None,pending_action:bool|None=None,evidence_completeness:str|None=None,client_id:str|None=None,db:Session=Depends(get_db)):
    return runtime(db).analytics(StoreAnalyticsFilters(analytical_segment,attention_level,minimum_months_no_use,has_historical_value_evidence,operational_block,activation_failure,terminal_recovery_candidate,pending_action,evidence_completeness,client_id))
@router.post("/decisions",status_code=status.HTTP_201_CREATED)
def decision(payload:HumanDecisionInput,db:Session=Depends(get_db)):
    try: event=runtime(db).decision(payload); db.commit(); return event
    except ValueError as exc: raise HTTPException(404 if str(exc)=="unknown store" else 422,str(exc)) from exc
@router.get("/summary")
def summary(db:Session=Depends(get_db)): return runtime(db).summary()

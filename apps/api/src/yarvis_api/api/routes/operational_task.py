from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from yarvis_api.api.authentication import transport_authentication_request
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.operational_task import *
from yarvis_api.clock import utc_now
from yarvis_api.database import get_db
from yarvis_api.schemas.operational_task import TaskAssignmentRequest, TaskCancellationRequest, TaskCompletionRequest, TaskCreateRequest, TaskDependencyRequest, TaskPage, TaskRead, TaskTransitionRequest, TaskUpdateRequest
router=APIRouter(prefix="/mission/tasks",tags=["operational-tasks"])
def _p(r): return r.app.state.yarvis.authentication.authenticate(transport_authentication_request(r))
def _m(p, command_id, key=None, version=None): return RequestMetadata(utc_now(),p.correlation_id or str(uuid4()),command_id=command_id,idempotency_key=key,expected_aggregate_version=version)
@router.post("",response_model=TaskRead,status_code=status.HTTP_201_CREATED)
def create(x:TaskCreateRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.create(CreateOperationalTaskCommand(x.mission_work_item_id,x.title,x.description,x.priority,x.process_instance_id,x.process_stage_id,x.planned_start_at,x.due_at),_m(p,"create_operational_task",x.idempotency_key),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.get("/{task_id}",response_model=TaskRead)
def get(task_id:UUID,request:Request,db:Session=Depends(get_db)): return request.app.state.yarvis.operational_task_query_service.retrieve(db,task_id,_p(request))
@router.get("/work/{work_id}",response_model=TaskPage)
def list_(work_id:UUID,request:Request,limit:int=50,offset:int=0,db:Session=Depends(get_db)): return request.app.state.yarvis.operational_task_query_service.list(db,work_id,_p(request),limit,offset)
@router.put("/{task_id}",response_model=TaskRead)
def update(task_id:UUID,x:TaskUpdateRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.update(UpdateOperationalTaskCommand(task_id,x.expected_version,x.title,x.description,x.priority,x.process_instance_id,x.process_stage_id,x.planned_start_at,x.due_at),_m(p,"update_operational_task",x.idempotency_key,x.expected_version),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.post("/{task_id}/assignment",response_model=TaskRead)
def assign(task_id:UUID,x:TaskAssignmentRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.assign(AssignOperationalTaskCommand(task_id,x.expected_version,x.assignee_subject_id),_m(p,"assign_operational_task",x.idempotency_key,x.expected_version),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.post("/{task_id}/transition",response_model=TaskRead)
def transition(task_id:UUID,x:TaskTransitionRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.transition(TaskTransitionCommand(task_id,x.expected_version,x.status),_m(p,"transition_operational_task",x.idempotency_key,x.expected_version),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.post("/{task_id}/complete",response_model=TaskRead)
def complete(task_id:UUID,x:TaskCompletionRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.complete(CompleteOperationalTaskCommand(task_id,x.expected_version,x.completion_note),_m(p,"complete_operational_task",x.idempotency_key,x.expected_version),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.post("/{task_id}/cancel",response_model=TaskRead)
def cancel(task_id:UUID,x:TaskCancellationRequest,request:Request):
 p=_p(request);r=request.app.state.yarvis.operational_task_service.cancel(CancelOperationalTaskCommand(task_id,x.expected_version,x.reason),_m(p,"cancel_operational_task",x.idempotency_key,x.expected_version),p);request.app.state.yarvis.task_mission_work_timeline_projector.project_task(r.id);return r
@router.post("/{task_id}/dependencies",status_code=status.HTTP_204_NO_CONTENT)
def add_dependency(task_id:UUID,x:TaskDependencyRequest,request:Request):
 p=_p(request);request.app.state.yarvis.operational_task_service.dependency(ManageTaskDependencyCommand(task_id,x.predecessor_task_id),_m(p,"manage_operational_task_dependencies",x.idempotency_key),p)
@router.delete("/{task_id}/dependencies/{predecessor_task_id}",status_code=status.HTTP_204_NO_CONTENT)
def remove_dependency(task_id:UUID,predecessor_task_id:UUID,idempotency_key:str,request:Request):
 p=_p(request);request.app.state.yarvis.operational_task_service.dependency(ManageTaskDependencyCommand(task_id,predecessor_task_id,True),_m(p,"manage_operational_task_dependencies",idempotency_key),p)

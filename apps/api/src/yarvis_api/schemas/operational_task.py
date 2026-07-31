from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class TaskCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    mission_work_item_id: UUID; title: str = Field(min_length=1,max_length=255); description: str|None=None; priority: str="normal"; process_instance_id: UUID|None=None; process_stage_id: UUID|None=None; planned_start_at: datetime|None=None; due_at: datetime|None=None; idempotency_key: str=Field(min_length=1,max_length=255); correlation_id: UUID
class TaskRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID; mission_work_item_id: UUID; process_instance_id: UUID|None; process_stage_id: UUID|None; title:str; description:str|None; status:str; priority:str; assignee_subject_id:str|None; planned_start_at:datetime|None; due_at:datetime|None; created_at:datetime; updated_at:datetime; completed_at:datetime|None; completed_by_subject_id:str|None; completion_note:str|None; cancelled_at:datetime|None; cancelled_by_subject_id:str|None; cancellation_reason:str|None; version:int
class TaskPage(BaseModel): items:list[TaskRead]; total:int; limit:int; offset:int
class TaskUpdateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    title:str=Field(min_length=1,max_length=255); description:str|None=None; priority:str="normal"; process_instance_id:UUID|None=None; process_stage_id:UUID|None=None; planned_start_at:datetime|None=None; due_at:datetime|None=None; expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID
class TaskAssignmentRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    assignee_subject_id:str|None=None; expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID
class TaskTransitionRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status:str; expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID
class TaskCompletionRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    completion_note:str|None=None; expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID
class TaskCancellationRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    reason:str=Field(min_length=1); expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID
class TaskDependencyRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    predecessor_task_id:UUID; idempotency_key:str=Field(min_length=1); correlation_id:UUID

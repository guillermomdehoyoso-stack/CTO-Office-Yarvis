from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field
class VersionInput(BaseModel):
 model_config=ConfigDict(extra="forbid"); media_type:str=Field(min_length=1); checksum_algorithm:str=Field(min_length=1); checksum_value:str=Field(min_length=1); storage_provider:str=Field(min_length=1); storage_key:str|None=None; external_reference:str|None=None; source_kind:str=Field(min_length=1); provenance:dict=Field(default_factory=dict); original_filename:str|None=None; byte_size:int|None=Field(default=None,ge=0); source_reference:str|None=None
class DocumentCreateRequest(VersionInput):
 title:str=Field(min_length=1,max_length=255); classification:str="general"; visibility:str="organization"; idempotency_key:str=Field(min_length=1); correlation_id:UUID; causation_id:UUID|None=None
class DocumentUpdateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); title:str=Field(min_length=1,max_length=255); classification:str; visibility:str; expected_version:int=Field(ge=1); idempotency_key:str=Field(min_length=1); correlation_id:UUID; causation_id:UUID|None=None
class DocumentVersionRequest(VersionInput):
 idempotency_key:str=Field(min_length=1); correlation_id:UUID; causation_id:UUID|None=None
class AssociationRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); subject_type:str; subject_id:UUID; idempotency_key:str=Field(min_length=1); correlation_id:UUID; causation_id:UUID|None=None
class DocumentRead(BaseModel):
 model_config=ConfigDict(from_attributes=True); id:UUID; title:str; classification:str; lifecycle_status:str; visibility:str; current_version_id:UUID|None; created_at:datetime; updated_at:datetime; archived_at:datetime|None; version:int; active_association_count:int=0
class DocumentVersionRead(BaseModel):
 model_config=ConfigDict(from_attributes=True); id:UUID; document_id:UUID; sequence:int; media_type:str; original_filename:str|None; byte_size:int|None; checksum_algorithm:str; checksum_value:str; storage_provider:str; storage_key:str|None; external_reference:str|None; source_kind:str; source_reference:str|None; provenance:dict; created_at:datetime; supersedes_version_id:UUID|None
class DocumentAssociationRead(BaseModel):
 model_config=ConfigDict(from_attributes=True); id:UUID; document_id:UUID; subject_type:str; subject_id:UUID; linked_at:datetime; unlinked_at:datetime|None
class DocumentPage(BaseModel): items:list[DocumentRead]; total:int; limit:int; offset:int

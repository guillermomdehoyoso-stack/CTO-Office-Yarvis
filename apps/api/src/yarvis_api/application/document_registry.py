from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True,slots=True)
class CreateDocumentCommand:
 title:str; classification:str; visibility:str; media_type:str; checksum_algorithm:str; checksum_value:str; storage_provider:str; storage_key:str|None; external_reference:str|None; source_kind:str; provenance:dict; original_filename:str|None=None; byte_size:int|None=None; source_reference:str|None=None
@dataclass(frozen=True,slots=True)
class UpdateDocumentCommand: document_id:UUID; expected_version:int; title:str; classification:str; visibility:str
@dataclass(frozen=True,slots=True)
class AddDocumentVersionCommand:
 document_id:UUID; media_type:str; checksum_algorithm:str; checksum_value:str; storage_provider:str; storage_key:str|None; external_reference:str|None; source_kind:str; provenance:dict; original_filename:str|None=None; byte_size:int|None=None; source_reference:str|None=None
@dataclass(frozen=True,slots=True)
class DocumentAssociationCommand: document_id:UUID; subject_type:str; subject_id:UUID
@dataclass(frozen=True,slots=True)
class ArchiveDocumentCommand: document_id:UUID
@dataclass(frozen=True,slots=True)
class UnlinkDocumentAssociationCommand: document_id:UUID; association_id:UUID

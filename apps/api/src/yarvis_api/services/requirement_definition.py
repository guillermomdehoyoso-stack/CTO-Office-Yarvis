"""Governed C06 Requirement Definition registration."""
from dataclasses import asdict
from uuid import UUID
from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from yarvis_api.application.contracts import DI003CommandName, DI003QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.opportunity import DossierTemplateVersion, OpportunityCommandIdempotency, RequirementDefinition, RequirementDefinitionDependency
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.opportunity import RequirementDefinitionRead
from yarvis_api.services.inbound_intake import _principal_organization_id
from yarvis_api.services.opportunity import _fingerprint, _key

_SUBJECTS={"identity","evidence","business_data","derived_knowledge","human_decision"}; _MODES={"provided","derived","verified","confirmed"}; _CLASSES={"required","optional"}
def _error(code,msg): return ApplicationError(code,msg,{"resource":"requirement definition"})

class RequirementDefinitionService:
 def __init__(self,persistence:PersistenceRuntime): self.persistence=persistence
 def register(self,command,metadata,principal):
  contract=command_contracts[DI003CommandName.REGISTER_REQUIREMENT_DEFINITION];enforce_command_boundary(contract,metadata=metadata,principal=principal)
  org,key=_principal_organization_id(principal),_key(metadata);deps=tuple(sorted(set(command.dependency_ids),key=str));payload={**asdict(command),"dependency_ids":[str(x) for x in deps]};fp=_fingerprint(contract.interaction_contract_id,org,payload)
  try:
   with UnitOfWork(self.persistence,OperationScope()) as u:
    s=u.session;receipt=self._receipt(s,org,contract.interaction_contract_id,key)
    if receipt:return self._replay(s,receipt,fp)
    if command.semantic_subject not in _SUBJECTS or command.fulfillment_mode not in _MODES or command.classification not in _CLASSES:raise _error(ApplicationErrorCode.VALIDATION_FAILED,"unsupported requirement semantics")
    template=s.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.id==command.dossier_template_version_id,DossierTemplateVersion.organization_id==org))
    if not template:raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND,"dossier template version not found")
    if template.status!="published":raise _error(ApplicationErrorCode.CONFLICT,"dossier template version is not published")
    if not command.semantic_key or not command.title or not command.purpose or not command.provenance:raise _error(ApplicationErrorCode.VALIDATION_FAILED,"requirement definition fields are required")
    existing=s.scalar(select(RequirementDefinition).where(RequirementDefinition.organization_id==org,RequirementDefinition.dossier_template_version_id==template.id,RequirementDefinition.semantic_key==command.semantic_key))
    if existing:raise _error(ApplicationErrorCode.CONFLICT,"requirement semantic key already exists")
    prerequisites=list(s.scalars(select(RequirementDefinition).where(RequirementDefinition.id.in_(deps))).all()) if deps else []
    if len(prerequisites)!=len(deps) or any(x.organization_id!=org or x.dossier_template_version_id!=template.id for x in prerequisites):raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND,"requirement dependency not found")
    definition=RequirementDefinition(organization_id=org,dossier_template_version_id=template.id,semantic_key=command.semantic_key,title=command.title,purpose=command.purpose,semantic_subject=command.semantic_subject,fulfillment_mode=command.fulfillment_mode,classification=command.classification,provenance=command.provenance);s.add(definition);s.flush()
    for dep in deps:s.add(RequirementDefinitionDependency(requirement_definition_id=definition.id,depends_on_definition_id=dep))
    record_event(s,event_type="requirement_definition.registered",aggregate_type="requirement_definition",aggregate_id=definition.id,organization_id=org,correlation_id=UUID(metadata.correlation_id),causation_id=UUID(metadata.causation_id) if metadata.causation_id else None,payload={"actor_subject_id":principal.actor_id,"template_version_id":str(template.id)})
    s.add(OpportunityCommandIdempotency(organization_id=org,contract_id=contract.interaction_contract_id,idempotency_key=key,request_fingerprint=fp,aggregate_id=definition.id,response_kind="requirement_definition",response_payload={"requirement_definition_id":str(definition.id)}));result=RequirementDefinitionRead.model_validate(definition);u.commit();return result
  except IntegrityError as exc:
   if not isinstance(exc.orig,UniqueViolation):raise
   with UnitOfWork(self.persistence,OperationScope()) as u:
    receipt=self._receipt(u.session,org,contract.interaction_contract_id,key)
    if receipt:return self._replay(u.session,receipt,fp)
    raise _error(ApplicationErrorCode.CONFLICT,"requirement semantic key already exists")
 def _receipt(self,s,org,c,k):return s.scalar(select(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.organization_id==org,OpportunityCommandIdempotency.contract_id==c,OpportunityCommandIdempotency.idempotency_key==k))
 def _replay(self,s,r,fp):
  if r.request_fingerprint!=fp:raise _error(ApplicationErrorCode.CONFLICT,"idempotency key was previously used for a different requirement command")
  d=s.scalar(select(RequirementDefinition).where(RequirementDefinition.id==r.aggregate_id,RequirementDefinition.organization_id==r.organization_id))
  if not d:raise _error(ApplicationErrorCode.CONFLICT,"idempotency receipt result unavailable")
  return RequirementDefinitionRead.model_validate(d)
 def get(self,definition_id,metadata,principal):
  enforce_query_boundary(query_contracts[DI003QueryName.GET_REQUIREMENT_DEFINITION],metadata=metadata,principal=principal)
  with UnitOfWork(self.persistence,OperationScope()) as u:
   d=u.session.scalar(select(RequirementDefinition).where(RequirementDefinition.id==definition_id,RequirementDefinition.organization_id==_principal_organization_id(principal)))
   if not d:raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND,"requirement definition not found")
   return self._read(u.session,d)
 def get_by_key(self,template_id,semantic_key,metadata,principal):
  enforce_query_boundary(query_contracts[DI003QueryName.GET_REQUIREMENT_DEFINITION_BY_KEY],metadata=metadata,principal=principal)
  with UnitOfWork(self.persistence,OperationScope()) as u:
   d=u.session.scalar(select(RequirementDefinition).where(RequirementDefinition.organization_id==_principal_organization_id(principal),RequirementDefinition.dossier_template_version_id==template_id,RequirementDefinition.semantic_key==semantic_key))
   if not d:raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND,"requirement definition not found")
   return self._read(u.session,d)
 def _read(self,s,d):
  deps=tuple(s.scalars(select(RequirementDefinitionDependency.depends_on_definition_id).where(RequirementDefinitionDependency.requirement_definition_id==d.id).order_by(RequirementDefinitionDependency.depends_on_definition_id)).all())
  return RequirementDefinitionRead.model_validate(d).model_copy(update={"dependency_ids":deps})

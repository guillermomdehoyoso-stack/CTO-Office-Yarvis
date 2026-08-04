"""Governed C05 published Dossier Template Version catalog."""

from dataclasses import asdict
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from yarvis_api.application.contracts import DI003CommandName, DI003QueryName, command_contracts, query_contracts
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.service_boundary import enforce_command_boundary, enforce_query_boundary
from yarvis_api.clock import utc_now
from yarvis_api.models.domain_event import record_event
from yarvis_api.models.opportunity import DossierTemplateVersion, OpportunityCommandIdempotency
from yarvis_api.persistence import OperationScope, PersistenceRuntime, UnitOfWork
from yarvis_api.schemas.opportunity import DossierTemplateVersionRead
from yarvis_api.services.inbound_intake import _principal_organization_id
from yarvis_api.services.opportunity import _fingerprint, _key


def _error(code, message):
    return ApplicationError(code, message, {"resource": "dossier template version"})


class DossierTemplateService:
    def __init__(self, persistence: PersistenceRuntime): self.persistence = persistence

    def publish(self, command, metadata, principal):
        contract = command_contracts[DI003CommandName.PUBLISH_DOSSIER_TEMPLATE]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        org, key = _principal_organization_id(principal), _key(metadata)
        payload = asdict(command); fingerprint = _fingerprint(contract.interaction_contract_id, org, payload)
        try:
            with UnitOfWork(self.persistence, OperationScope()) as unit:
                s = unit.session; receipt = self._receipt(s, org, contract.interaction_contract_id, key)
                if receipt: return self._replay(s, receipt, fingerprint)
                if not command.stable_key or not command.business_type or not command.display_name or command.business_version <= 0:
                    raise _error(ApplicationErrorCode.VALIDATION_FAILED, "valid template identity and business version are required")
                existing = s.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.organization_id == org, DossierTemplateVersion.stable_key == command.stable_key, DossierTemplateVersion.business_version == command.business_version))
                if existing: raise _error(ApplicationErrorCode.CONFLICT, "dossier template version already exists")
                template = DossierTemplateVersion(organization_id=org, stable_key=command.stable_key, business_type=command.business_type, business_version=command.business_version, display_name=command.display_name)
                s.add(template); s.flush(); self._event(s, template, "dossier_template.published", metadata, principal)
                self._receipt_add(s, org, contract.interaction_contract_id, key, fingerprint, template); result = DossierTemplateVersionRead.model_validate(template); unit.commit(); return result
        except IntegrityError as exc:
            if not isinstance(exc.orig, UniqueViolation): raise
            with UnitOfWork(self.persistence, OperationScope()) as unit:
                receipt = self._receipt(unit.session, org, contract.interaction_contract_id, key)
                if receipt is None: raise _error(ApplicationErrorCode.CONFLICT, "dossier template version already exists")
                return self._replay(unit.session, receipt, fingerprint)

    def retire(self, command, metadata, principal):
        contract = command_contracts[DI003CommandName.RETIRE_DOSSIER_TEMPLATE]
        enforce_command_boundary(contract, metadata=metadata, principal=principal)
        org, key = _principal_organization_id(principal), _key(metadata)
        fingerprint = _fingerprint(contract.interaction_contract_id, org, asdict(command))
        with UnitOfWork(self.persistence, OperationScope()) as unit:
            s = unit.session; receipt = self._receipt(s, org, contract.interaction_contract_id, key)
            if receipt: return self._replay(s, receipt, fingerprint)
            template = s.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.id == command.template_id, DossierTemplateVersion.organization_id == org).with_for_update())
            if not template: raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND, "dossier template version not found")
            receipt = self._receipt(s, org, contract.interaction_contract_id, key)
            if receipt: return self._replay(s, receipt, fingerprint)
            if template.aggregate_version != command.expected_version or template.status != "published": raise _error(ApplicationErrorCode.CONFLICT, "dossier template version cannot be retired")
            template.status = "retired"; template.retired_at = utc_now(); template.aggregate_version += 1
            self._event(s, template, "dossier_template.retired", metadata, principal); self._receipt_add(s, org, contract.interaction_contract_id, key, fingerprint, template)
            result = DossierTemplateVersionRead.model_validate(template); unit.commit(); return result

    def get(self, template_id, metadata, principal):
        enforce_query_boundary(query_contracts[DI003QueryName.GET_DOSSIER_TEMPLATE], metadata=metadata, principal=principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit:
            template = unit.session.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.id == template_id, DossierTemplateVersion.organization_id == _principal_organization_id(principal)))
            if not template: raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND, "dossier template version not found")
            return DossierTemplateVersionRead.model_validate(template)

    def get_published(self, stable_key, business_version, metadata, principal):
        enforce_query_boundary(query_contracts[DI003QueryName.GET_PUBLISHED_DOSSIER_TEMPLATE], metadata=metadata, principal=principal)
        with UnitOfWork(self.persistence, OperationScope()) as unit:
            template = unit.session.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.organization_id == _principal_organization_id(principal), DossierTemplateVersion.stable_key == stable_key, DossierTemplateVersion.business_version == business_version, DossierTemplateVersion.status == "published"))
            if not template: raise _error(ApplicationErrorCode.RESOURCE_NOT_FOUND, "dossier template version not found")
            return DossierTemplateVersionRead.model_validate(template)

    def _receipt(self, s, org, contract, key): return s.scalar(select(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.organization_id == org, OpportunityCommandIdempotency.contract_id == contract, OpportunityCommandIdempotency.idempotency_key == key))
    def _replay(self, s, receipt, fingerprint):
        if receipt.request_fingerprint != fingerprint: raise _error(ApplicationErrorCode.CONFLICT, "idempotency key was previously used for a different dossier template command")
        template = s.scalar(select(DossierTemplateVersion).where(DossierTemplateVersion.id == receipt.aggregate_id, DossierTemplateVersion.organization_id == receipt.organization_id))
        if not template: raise _error(ApplicationErrorCode.CONFLICT, "idempotency receipt result unavailable")
        return DossierTemplateVersionRead.model_validate(template)
    def _receipt_add(self, s, org, contract, key, fingerprint, template): s.add(OpportunityCommandIdempotency(organization_id=org, contract_id=contract, idempotency_key=key, request_fingerprint=fingerprint, aggregate_id=template.id, response_kind="dossier_template", response_payload={"template_id": str(template.id)}))
    def _event(self, s, template, event, metadata, principal): record_event(s, event_type=event, aggregate_type="dossier_template_version", aggregate_id=template.id, organization_id=template.organization_id, correlation_id=UUID(metadata.correlation_id), causation_id=UUID(metadata.causation_id) if metadata.causation_id else None, payload={"actor_subject_id": principal.actor_id, "authority_scope": principal.authority, "stable_key": template.stable_key, "business_version": template.business_version})

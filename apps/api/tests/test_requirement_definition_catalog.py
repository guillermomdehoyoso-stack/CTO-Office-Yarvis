from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import pytest
from sqlalchemy import func, select, text
from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import PublishDossierTemplateVersionCommand, RegisterRequirementDefinitionCommand, RetireDossierTemplateVersionCommand
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import DossierTemplateVersion, OpportunityCommandIdempotency, RequirementDefinition, RequirementDefinitionDependency
from yarvis_api.models.organization import Organization
from yarvis_api.services.dossier_template import DossierTemplateService
from yarvis_api.services.requirement_definition import RequirementDefinitionService

def _p(org, authority): return AuthenticatedPrincipal("requirement:actor",str(org),(),(),authority,"test",datetime.now(timezone.utc),False)
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import (
  PublishDossierTemplateVersionCommand,
  RegisterRequirementDefinitionCommand,
  RetireDossierTemplateVersionCommand,
)
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import (
  DossierTemplateVersion,
  OpportunityCommandIdempotency,
  RequirementDefinition,
  RequirementDefinitionDependency,
)
from yarvis_api.models.organization import Organization
from yarvis_api.services.dossier_template import DossierTemplateService
from yarvis_api.services.requirement_definition import RequirementDefinitionService


def _p(org, authority):
  return AuthenticatedPrincipal(
    "requirement:actor",
    str(org),
    (),
    (),
    authority,
    "test",
    datetime.now(timezone.utc),
    False,
  )


def _m(key):
  return RequestMetadata(
    datetime.now(timezone.utc),
    str(uuid4()),
    command_id=str(uuid4()),
    idempotency_key=key,
  )


def _q():
  return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), query_id=str(uuid4()))


def _org(runtime):
  oid = uuid4()
  name = f"Requirement {oid}"
  with runtime.create_session() as s:
    s.add(Organization(id=oid, legal_name=name, display_name=name))
    s.commit()
  return oid


def _counts(runtime, org):
  with runtime.create_session() as s:
    return tuple(
      s.scalar(select(func.count()).select_from(model).where(model.organization_id == org))
      if hasattr(model, "organization_id")
      else s.scalar(select(func.count()).select_from(model))
      for model in (
        RequirementDefinition,
        RequirementDefinitionDependency,
        DomainEvent,
        OpportunityCommandIdempotency,
      )
    )


class _FailingRuntime:
  def __init__(self, runtime):
    self.runtime = runtime

  def create_session(self):
    session = self.runtime.create_session()

    def fail():
      raise RuntimeError("forced commit failure")

    session.commit = fail
    return session


def _definition_snapshot(runtime, definition_id, org):
  with runtime.create_session() as s:
    row = s.get(RequirementDefinition, definition_id)
    deps = tuple(
      s.scalars(
        select(RequirementDefinitionDependency.depends_on_definition_id)
        .where(RequirementDefinitionDependency.requirement_definition_id == definition_id)
        .order_by(RequirementDefinitionDependency.depends_on_definition_id)
      ).all()
    )
  return (
    (
      row.organization_id,
      row.dossier_template_version_id,
      row.semantic_key,
      row.title,
      row.purpose,
      row.semantic_subject,
      row.fulfillment_mode,
      row.classification,
      row.provenance,
      row.created_at,
      row.aggregate_version,
    ),
    deps,
    _counts(runtime, org),
  )


def test_register_requirement_definition_persists_replays_and_conflicts(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "Solar v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  service = RequirementDefinitionService(runtime)
  command = RegisterRequirementDefinitionCommand(
    template.id,
    "customer_identity",
    "Customer identity",
    "Identify customer",
    "identity",
    "verified",
    "required",
    "template",
  )
  first = service.register(command, _m("register"), _p(org, "requirement.definition.register"))
  replay = service.register(command, _m("register"), _p(org, "requirement.definition.register"))

  assert first.id == replay.id
  assert first.organization_id == org
  assert first.dossier_template_version_id == template.id
  assert first.aggregate_version == 1
  assert _counts(runtime, org) == (1, 0, 2, 2)

  with pytest.raises(ApplicationError) as conflict:
    service.register(
      RegisterRequirementDefinitionCommand(
        template.id,
        "customer_identity",
        "Changed",
        "Changed",
        "identity",
        "verified",
        "required",
        "template",
      ),
      _m("other"),
      _p(org, "requirement.definition.register"),
    )

  assert conflict.value.code == ApplicationErrorCode.CONFLICT
  assert _counts(runtime, org) == (1, 0, 2, 2)


@pytest.mark.parametrize(
  "subject,mode,classification",
  [
    ("identity", "verified", "required"),
    ("evidence", "provided", "optional"),
    ("business_data", "provided", "required"),
    ("derived_knowledge", "derived", "required"),
    ("human_decision", "confirmed", "optional"),
  ],
)
def test_requirement_semantics_and_dependency_normalization(test_database, subject, mode, classification):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("netpay", "NetPay", 1, "NetPay v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  service = RequirementDefinitionService(runtime)
  prerequisite = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "prerequisite",
      "Prerequisite",
      "Purpose",
      "identity",
      "provided",
      "required",
      "template",
    ),
    _m("pre"),
    _p(org, "requirement.definition.register"),
  )
  definition = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      f"{subject}_{mode}",
      "Title",
      "Purpose",
      subject,
      mode,
      classification,
      "template",
      (prerequisite.id, prerequisite.id),
    ),
    _m("definition"),
    _p(org, "requirement.definition.register"),
  )

  with runtime.create_session() as s:
    row = s.get(RequirementDefinition, definition.id)
    deps = list(
      s.scalars(
        select(RequirementDefinitionDependency).where(
          RequirementDefinitionDependency.requirement_definition_id == definition.id
        )
      )
    )
    assert (row.semantic_subject, row.fulfillment_mode, row.classification, row.aggregate_version) == (
      subject,
      mode,
      classification,
      1,
    )
    assert len(deps) == 1
    assert deps[0].depends_on_definition_id == prerequisite.id
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 2
    )


@pytest.mark.parametrize(
  "field,value",
  [
    ("semantic_subject", "unsupported"),
    ("fulfillment_mode", "unsupported"),
    ("classification", "unsupported"),
  ],
)
def test_invalid_requirement_semantics_have_zero_side_effects(test_database, field, value):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("invalid", "Invalid", 1, "Invalid v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  data = dict(semantic_subject="identity", fulfillment_mode="provided", classification="required")
  data[field] = value

  with pytest.raises(ApplicationError):
    RequirementDefinitionService(runtime).register(
      RegisterRequirementDefinitionCommand(
        template.id,
        "invalid",
        "Title",
        "Purpose",
        data["semantic_subject"],
        data["fulfillment_mode"],
        data["classification"],
        "template",
      ),
      _m("invalid"),
      _p(org, "requirement.definition.register"),
    )

  assert _counts(runtime, org) == (0, 0, 1, 1)


def test_multiple_dependencies_normalize_and_replay_in_any_order(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("energy", "Energy", 1, "Energy v1"),
    _m("t"),
    _p(org, "dossier.template.publish"),
  )
  service = RequirementDefinitionService(runtime)
  first = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "bill",
      "Bill",
      "Purpose",
      "evidence",
      "provided",
      "required",
      "template",
    ),
    _m("a"),
    _p(org, "requirement.definition.register"),
  )
  second = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "site",
      "Site",
      "Purpose",
      "business_data",
      "provided",
      "required",
      "template",
    ),
    _m("b"),
    _p(org, "requirement.definition.register"),
  )
  created = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "demand",
      "Demand",
      "Purpose",
      "derived_knowledge",
      "derived",
      "required",
      "template",
      (second.id, first.id, second.id),
    ),
    _m("deps"),
    _p(org, "requirement.definition.register"),
  )
  replay = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "demand",
      "Demand",
      "Purpose",
      "derived_knowledge",
      "derived",
      "required",
      "template",
      (first.id, second.id),
    ),
    _m("deps"),
    _p(org, "requirement.definition.register"),
  )

  with runtime.create_session() as s:
    deps = list(
      s.scalars(
        select(RequirementDefinitionDependency)
        .where(RequirementDefinitionDependency.requirement_definition_id == created.id)
        .order_by(RequirementDefinitionDependency.depends_on_definition_id)
      )
    )
    assert replay.id == created.id
    assert [d.depends_on_definition_id for d in deps] == sorted((first.id, second.id), key=str)
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org)
      )
      == 3
    )
    assert len(deps) == 2


def test_dependency_boundary_rejections_have_zero_side_effects(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org, foreign = _org(runtime), _org(runtime)
  service = RequirementDefinitionService(runtime)
  template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("one", "One", 1, "One"),
    _m("t1"),
    _p(org, "dossier.template.publish"),
  )
  other = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("two", "Two", 1, "Two"),
    _m("t2"),
    _p(org, "dossier.template.publish"),
  )
  foreign_template = DossierTemplateService(runtime).publish(
    PublishDossierTemplateVersionCommand("foreign", "Foreign", 1, "Foreign"),
    _m("tf"),
    _p(foreign, "dossier.template.publish"),
  )
  service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "local",
      "Local",
      "Purpose",
      "identity",
      "provided",
      "required",
      "template",
    ),
    _m("local"),
    _p(org, "requirement.definition.register"),
  )
  foreign_definition = service.register(
    RegisterRequirementDefinitionCommand(
      foreign_template.id,
      "foreign",
      "Foreign",
      "Purpose",
      "identity",
      "provided",
      "required",
      "template",
    ),
    _m("foreign"),
    _p(foreign, "requirement.definition.register"),
  )
  cross = service.register(
    RegisterRequirementDefinitionCommand(
      other.id,
      "cross",
      "Cross",
      "Purpose",
      "identity",
      "provided",
      "required",
      "template",
    ),
    _m("cross"),
    _p(org, "requirement.definition.register"),
  )
  baseline = _counts(runtime, org)

  for dependency in (uuid4(), foreign_definition.id, cross.id):
    with pytest.raises(ApplicationError):
      service.register(
        RegisterRequirementDefinitionCommand(
          template.id,
          f"bad_{dependency}",
          "Bad",
          "Purpose",
          "identity",
          "provided",
          "required",
          "template",
          (dependency,),
        ),
        _m(str(dependency)),
        _p(org, "requirement.definition.register"),
      )
    assert _counts(runtime, org) == baseline


def test_registration_authority_template_eligibility_tenant_scope_and_c05_preservation(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  owner, foreign = _org(runtime), _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("scope", "Scope", 1, "Scope v1"),
    _m("template"),
    _p(owner, "dossier.template.publish"),
  )
  foreign_template = catalog.publish(
    PublishDossierTemplateVersionCommand("scope", "Scope", 1, "Scope v1"),
    _m("template"),
    _p(foreign, "dossier.template.publish"),
  )

  def snapshot(org, template_id):
    with runtime.create_session() as s:
      row = s.get(DossierTemplateVersion, template_id)
      return (
        row.status,
        row.published_at,
        row.retired_at,
        row.aggregate_version,
        row.stable_key,
        row.business_type,
        row.business_version,
        row.display_name,
        s.scalar(
          select(func.count())
          .select_from(DomainEvent)
          .where(DomainEvent.organization_id == org, DomainEvent.event_type.like("dossier_template.%"))
        ),
        s.scalar(
          select(func.count())
          .select_from(OpportunityCommandIdempotency)
          .where(
            OpportunityCommandIdempotency.organization_id == org,
            OpportunityCommandIdempotency.contract_id.like("IC-DOSSIER-TEMPLATE-%"),
          )
        ),
      )

  before = snapshot(owner, template.id)
  command = RegisterRequirementDefinitionCommand(
    template.id,
    "identity",
    "Identity",
    "Purpose",
    "identity",
    "provided",
    "required",
    "template",
  )
  for authority in ("", "dossier.template.publish"):
    with pytest.raises((ApplicationError, ValueError)):
      service.register(command, _m(uuid4().hex), _p(owner, authority))
    assert _counts(runtime, owner) == (0, 0, 1, 1)
    assert snapshot(owner, template.id) == before

  created = service.register(command, _m("shared"), _p(owner, "requirement.definition.register"))
  other = service.register(
    RegisterRequirementDefinitionCommand(
      foreign_template.id,
      "identity",
      "Identity",
      "Purpose",
      "identity",
      "provided",
      "required",
      "template",
    ),
    _m("shared"),
    _p(foreign, "requirement.definition.register"),
  )
  assert created.id != other.id
  assert _counts(runtime, owner) == (1, 0, 2, 2)
  assert _counts(runtime, foreign) == (1, 0, 2, 2)
  assert snapshot(owner, template.id) == before

  for template_id in (uuid4(), foreign_template.id):
    with pytest.raises(ApplicationError) as hidden:
      service.register(
        RegisterRequirementDefinitionCommand(
          template_id,
          "hidden",
          "Hidden",
          "Purpose",
          "identity",
          "provided",
          "required",
          "template",
        ),
        _m(uuid4().hex),
        _p(owner, "requirement.definition.register"),
      )
    assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert snapshot(owner, template.id) == before


def test_retired_template_rejects_registration_without_side_effects(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("retired", "Retired", 1, "Retired v1"),
    _m("publish"),
    _p(org, "dossier.template.publish"),
  )
  catalog.retire(RetireDossierTemplateVersionCommand(template.id, 1), _m("retire"), _p(org, "dossier.template.retire"))
  with runtime.create_session() as s:
    before = s.get(DossierTemplateVersion, template.id)
    snapshot = (
      before.status,
      before.retired_at,
      before.aggregate_version,
      before.stable_key,
      before.business_type,
      before.business_version,
      before.display_name,
      s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)),
      s.scalar(
        select(func.count()).select_from(OpportunityCommandIdempotency).where(
          OpportunityCommandIdempotency.organization_id == org
        )
      ),
    )

  with pytest.raises(ApplicationError) as rejected:
    service.register(
      RegisterRequirementDefinitionCommand(
        template.id,
        "blocked",
        "Blocked",
        "Purpose",
        "identity",
        "provided",
        "required",
        "template",
      ),
      _m("register"),
      _p(org, "requirement.definition.register"),
    )

  assert rejected.value.code == ApplicationErrorCode.CONFLICT
  assert _counts(runtime, org) == (0, 0, 2, 2)
  with runtime.create_session() as s:
    after = s.get(DossierTemplateVersion, template.id)
    assert (
      after.status,
      after.retired_at,
      after.aggregate_version,
      after.stable_key,
      after.business_type,
      after.business_version,
      after.display_name,
      s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)),
      s.scalar(
        select(func.count()).select_from(OpportunityCommandIdempotency).where(
          OpportunityCommandIdempotency.organization_id == org
        )
      ),
    ) == snapshot


def test_requirement_definition_queries_are_authoritative_concealed_and_side_effect_free(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org, foreign = _org(runtime), _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("query", "Query", 1, "Query v1"),
    _m("t"),
    _p(org, "dossier.template.publish"),
  )
  a = service.register(
    RegisterRequirementDefinitionCommand(template.id, "a", "A", "P", "identity", "provided", "required", "p"),
    _m("a"),
    _p(org, "requirement.definition.register"),
  )
  b = service.register(
    RegisterRequirementDefinitionCommand(template.id, "b", "B", "P", "evidence", "provided", "required", "p"),
    _m("b"),
    _p(org, "requirement.definition.register"),
  )
  d = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "target",
      "Target",
      "Purpose",
      "derived_knowledge",
      "derived",
      "optional",
      "p",
      (b.id, a.id),
    ),
    _m("d"),
    _p(org, "requirement.definition.register"),
  )
  before = _counts(runtime, org)
  by_id = service.get(d.id, _q(), _p(org, "requirement.definition.read"))
  by_key = service.get_by_key(template.id, "target", _q(), _p(org, "requirement.definition.read"))
  assert by_id == by_key
  assert by_id.dependency_ids == tuple(sorted((a.id, b.id), key=str))
  assert by_id.created_at == d.created_at

  for call in (
    lambda: service.get(uuid4(), _q(), _p(org, "requirement.definition.read")),
    lambda: service.get(d.id, _q(), _p(foreign, "requirement.definition.read")),
    lambda: service.get_by_key(uuid4(), "target", _q(), _p(org, "requirement.definition.read")),
  ):
    with pytest.raises(ApplicationError) as hidden:
      call()
    assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    assert _counts(runtime, org) == before

  for call in (
    lambda: service.get(d.id, _q(), _p(org, "wrong")),
    lambda: service.get_by_key(template.id, "target", _q(), _p(org, "")),
  ):
    with pytest.raises((ApplicationError, ValueError)):
      call()
    assert _counts(runtime, org) == before


def test_requirement_definition_immutability_guards_block_direct_updates_and_dependency_mutation(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("immutability", "Immutability", 1, "Immutability v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  prerequisite = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "pre",
      "Pre",
      "Purpose",
      "identity",
      "provided",
      "required",
      "test",
    ),
    _m("pre"),
    _p(org, "requirement.definition.register"),
  )
  definition = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "target",
      "Target",
      "Purpose",
      "evidence",
      "verified",
      "optional",
      "test",
      (prerequisite.id,),
    ),
    _m("target"),
    _p(org, "requirement.definition.register"),
  )
  baseline = _definition_snapshot(runtime, definition.id, org)

  immutable_updates = (
    "UPDATE requirement_definitions SET organization_id=:v WHERE id=:id",
    "UPDATE requirement_definitions SET dossier_template_version_id=:v WHERE id=:id",
    "UPDATE requirement_definitions SET semantic_key=:v WHERE id=:id",
    "UPDATE requirement_definitions SET title=:v WHERE id=:id",
    "UPDATE requirement_definitions SET purpose=:v WHERE id=:id",
    "UPDATE requirement_definitions SET semantic_subject=:v WHERE id=:id",
    "UPDATE requirement_definitions SET fulfillment_mode=:v WHERE id=:id",
    "UPDATE requirement_definitions SET classification=:v WHERE id=:id",
    "UPDATE requirement_definitions SET provenance=:v WHERE id=:id",
    "UPDATE requirement_definitions SET created_at=:v WHERE id=:id",
    "UPDATE requirement_definitions SET aggregate_version=:v WHERE id=:id",
  )
  for statement, value in (
    (immutable_updates[0], uuid4()),
    (immutable_updates[1], uuid4()),
    (immutable_updates[2], "changed"),
    (immutable_updates[3], "changed"),
    (immutable_updates[4], "changed"),
    (immutable_updates[5], "identity"),
    (immutable_updates[6], "derived"),
    (immutable_updates[7], "required"),
    (immutable_updates[8], "changed"),
    (immutable_updates[9], datetime.now(timezone.utc)),
    (immutable_updates[10], 2),
  ):
    with runtime.create_session() as s:
      with pytest.raises(Exception):
        s.execute(text(statement), {"id": definition.id, "v": value})
        s.commit()
      s.rollback()
    assert _definition_snapshot(runtime, definition.id, org) == baseline

  with runtime.create_session() as s:
    dep = s.scalar(
      select(RequirementDefinitionDependency).where(
        RequirementDefinitionDependency.requirement_definition_id == definition.id
      )
    )
    dependency_row_id = dep.id

  with runtime.create_session() as s:
    with pytest.raises(Exception):
      s.execute(
        text("UPDATE requirement_definition_dependencies SET depends_on_definition_id=:v WHERE id=:id"),
        {"id": dependency_row_id, "v": definition.id},
      )
      s.commit()
    s.rollback()
  assert _definition_snapshot(runtime, definition.id, org) == baseline

  new_dependency = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "extra",
      "Extra",
      "Purpose",
      "business_data",
      "provided",
      "required",
      "test",
    ),
    _m("extra"),
    _p(org, "requirement.definition.register"),
  )
  post_extra = (
    baseline[0],
    baseline[1],
    (baseline[2][0] + 1, baseline[2][1], baseline[2][2] + 1, baseline[2][3] + 1),
  )
  with runtime.create_session() as s:
    with pytest.raises(Exception):
      s.execute(
        text(
          "INSERT INTO requirement_definition_dependencies (id, requirement_definition_id, depends_on_definition_id) VALUES (:id, :requirement_definition_id, :depends_on_definition_id)"
        ),
        {
          "id": uuid4(),
          "requirement_definition_id": definition.id,
          "depends_on_definition_id": new_dependency.id,
        },
      )
      s.commit()
    s.rollback()
  assert _definition_snapshot(runtime, definition.id, org) == post_extra

  with runtime.create_session() as s:
    with pytest.raises(Exception):
      s.execute(text("DELETE FROM requirement_definition_dependencies WHERE id=:id"), {"id": dependency_row_id})
      s.commit()
    s.rollback()
  assert _definition_snapshot(runtime, definition.id, org) == post_extra

  reread = service.get(definition.id, _q(), _p(org, "requirement.definition.read"))
  assert reread.id == definition.id
  assert reread.dependency_ids == (prerequisite.id,)


def test_registration_rollback_leaves_no_partial_definition_and_retry_is_once(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("rollback", "Rollback", 1, "Rollback v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  prerequisite = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "pre",
      "Pre",
      "Purpose",
      "identity",
      "provided",
      "required",
      "test",
    ),
    _m("pre"),
    _p(org, "requirement.definition.register"),
  )
  baseline = _counts(runtime, org)
  command = RegisterRequirementDefinitionCommand(
    template.id,
    "rollback_target",
    "Rollback Target",
    "Purpose",
    "evidence",
    "verified",
    "required",
    "test",
    (prerequisite.id,),
  )
  metadata = _m("rollback-register")

  with pytest.raises(RuntimeError):
    RequirementDefinitionService(_FailingRuntime(runtime)).register(
      command,
      metadata,
      _p(org, "requirement.definition.register"),
    )

  with runtime.create_session() as s:
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "rollback_target")
      )
      == 0
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinitionDependency)
        .join(
          RequirementDefinition,
          RequirementDefinitionDependency.requirement_definition_id == RequirementDefinition.id,
        )
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "rollback_target")
      )
      == 0
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(OpportunityCommandIdempotency)
        .where(
          OpportunityCommandIdempotency.organization_id == org,
          OpportunityCommandIdempotency.idempotency_key == "rollback-register",
        )
      )
      == 0
    )
  assert _counts(runtime, org) == baseline

  created = service.register(command, metadata, _p(org, "requirement.definition.register"))
  replay = service.register(command, metadata, _p(org, "requirement.definition.register"))
  assert replay.id == created.id

  with runtime.create_session() as s:
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "rollback_target")
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinitionDependency)
        .where(RequirementDefinitionDependency.requirement_definition_id == created.id)
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.aggregate_id == created.id,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(OpportunityCommandIdempotency)
        .where(
          OpportunityCommandIdempotency.organization_id == org,
          OpportunityCommandIdempotency.idempotency_key == "rollback-register",
        )
      )
      == 1
    )


def test_registration_concurrency_receipt_and_business_identity_recovery(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  catalog = DossierTemplateService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand("race", "Race", 1, "Race v1"),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  prerequisite = RequirementDefinitionService(runtime).register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "pre",
      "Pre",
      "Purpose",
      "identity",
      "provided",
      "required",
      "test",
    ),
    _m("pre"),
    _p(org, "requirement.definition.register"),
  )

  def race(commands, metas):
    barrier = Barrier(2)

    def invoke(pair):
      command, metadata = pair
      barrier.wait()
      try:
        return (
          "ok",
          RequirementDefinitionService(runtime).register(
            command,
            metadata,
            _p(org, "requirement.definition.register"),
          ).id,
        )
      except ApplicationError as error:
        return "conflict", error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
      return list(pool.map(invoke, zip(commands, metas)))

  matching = RegisterRequirementDefinitionCommand(
    template.id,
    "match",
    "Match",
    "Purpose",
    "evidence",
    "verified",
    "required",
    "test",
    (prerequisite.id,),
  )
  matching_results = race((matching, matching), (_m("shared"), _m("shared")))
  assert len({value for state, value in matching_results if state == "ok"}) == 1

  with runtime.create_session() as s:
    target = s.scalar(
      select(RequirementDefinition).where(
        RequirementDefinition.organization_id == org,
        RequirementDefinition.semantic_key == "match",
      )
    )
    assert target is not None
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "match")
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinitionDependency)
        .where(RequirementDefinitionDependency.requirement_definition_id == target.id)
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.aggregate_id == target.id,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(OpportunityCommandIdempotency)
        .where(
          OpportunityCommandIdempotency.organization_id == org,
          OpportunityCommandIdempotency.idempotency_key == "shared",
        )
      )
      == 1
    )

  mismatch_commands = (
    RegisterRequirementDefinitionCommand(
      template.id,
      "mismatch",
      "Winner",
      "Purpose",
      "derived_knowledge",
      "derived",
      "required",
      "test",
      (prerequisite.id,),
    ),
    RegisterRequirementDefinitionCommand(
      template.id,
      "mismatch",
      "Loser",
      "Purpose",
      "derived_knowledge",
      "derived",
      "required",
      "test",
      (prerequisite.id,),
    ),
  )
  mismatch_results = race(mismatch_commands, (_m("mismatch"), _m("mismatch")))
  assert sorted(state for state, _ in mismatch_results) == ["conflict", "ok"]

  with runtime.create_session() as s:
    target = s.scalar(
      select(RequirementDefinition).where(
        RequirementDefinition.organization_id == org,
        RequirementDefinition.semantic_key == "mismatch",
      )
    )
    assert target is not None
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "mismatch")
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.aggregate_id == target.id,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(OpportunityCommandIdempotency)
        .where(
          OpportunityCommandIdempotency.organization_id == org,
          OpportunityCommandIdempotency.idempotency_key == "mismatch",
        )
      )
      == 1
    )

  different_commands = (
    RegisterRequirementDefinitionCommand(
      template.id,
      "unique_conflict",
      "First",
      "Purpose",
      "business_data",
      "provided",
      "required",
      "test",
      (prerequisite.id,),
    ),
    RegisterRequirementDefinitionCommand(
      template.id,
      "unique_conflict",
      "Second",
      "Purpose",
      "business_data",
      "provided",
      "required",
      "test",
      (prerequisite.id,),
    ),
  )
  different_results = race(different_commands, (_m("first-key"), _m("second-key")))
  assert sorted(state for state, _ in different_results) == ["conflict", "ok"]

  with runtime.create_session() as s:
    target = s.scalar(
      select(RequirementDefinition).where(
        RequirementDefinition.organization_id == org,
        RequirementDefinition.semantic_key == "unique_conflict",
      )
    )
    assert target is not None
    assert (
      s.scalar(
        select(func.count())
        .select_from(RequirementDefinition)
        .where(RequirementDefinition.organization_id == org, RequirementDefinition.semantic_key == "unique_conflict")
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(DomainEvent)
        .where(
          DomainEvent.organization_id == org,
          DomainEvent.aggregate_id == target.id,
          DomainEvent.event_type == "requirement_definition.registered",
        )
      )
      == 1
    )
    assert (
      s.scalar(
        select(func.count())
        .select_from(OpportunityCommandIdempotency)
        .where(
          OpportunityCommandIdempotency.organization_id == org,
          OpportunityCommandIdempotency.idempotency_key.in_(("first-key", "second-key")),
        )
      )
      == 1
    )


def test_immutability_concurrency_rejects_late_dependency_inserts_without_state_change(test_database):
  from yarvis_api.main import app

  runtime = app.state.yarvis.persistence
  org = _org(runtime)
  catalog = DossierTemplateService(runtime)
  service = RequirementDefinitionService(runtime)
  template = catalog.publish(
    PublishDossierTemplateVersionCommand(
      "immutability_race",
      "Immutability Race",
      1,
      "Immutability Race v1",
    ),
    _m("template"),
    _p(org, "dossier.template.publish"),
  )
  prerequisite = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "pre",
      "Pre",
      "Purpose",
      "identity",
      "provided",
      "required",
      "test",
    ),
    _m("pre"),
    _p(org, "requirement.definition.register"),
  )
  target = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "target",
      "Target",
      "Purpose",
      "evidence",
      "verified",
      "required",
      "test",
      (prerequisite.id,),
    ),
    _m("target"),
    _p(org, "requirement.definition.register"),
  )
  extra = service.register(
    RegisterRequirementDefinitionCommand(
      template.id,
      "extra",
      "Extra",
      "Purpose",
      "business_data",
      "provided",
      "required",
      "test",
    ),
    _m("extra"),
    _p(org, "requirement.definition.register"),
  )
  baseline = _definition_snapshot(runtime, target.id, org)
  barrier = Barrier(2)

  def attempt(_: int):
    with runtime.create_session() as s:
      barrier.wait()
      try:
        s.execute(
          text(
            "INSERT INTO requirement_definition_dependencies (id, requirement_definition_id, depends_on_definition_id) VALUES (:id, :requirement_definition_id, :depends_on_definition_id)"
          ),
          {
            "id": uuid4(),
            "requirement_definition_id": target.id,
            "depends_on_definition_id": extra.id,
          },
        )
        s.commit()
        return "ok"
      except Exception:
        s.rollback()
        return "rejected"

  with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(attempt, range(2)))

  assert results == ["rejected", "rejected"]
  assert _definition_snapshot(runtime, target.id, org) == baseline

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from yarvis_api.application.authentication import AuthenticatedPrincipal
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.application.metadata import RequestMetadata
from yarvis_api.application.opportunity import AssignOpportunityTemplateCommand, ConfirmOpportunityCommand, ProposeOpportunityCommand, PublishDossierTemplateVersionCommand, RetireDossierTemplateVersionCommand
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.opportunity import DossierTemplateVersion, Opportunity, OpportunityCommandIdempotency, OpportunityDossier, OpportunityWorkspace
from yarvis_api.models.organization import Organization
from yarvis_api.services.dossier_template import DossierTemplateService
from yarvis_api.services.opportunity import OpportunityService


def _principal(org, authority): return AuthenticatedPrincipal("template:actor", str(org), (), (), authority, "test", datetime.now(timezone.utc), False)
def _metadata(key, query=False): return RequestMetadata(datetime.now(timezone.utc), str(uuid4()), query_id=str(uuid4()) if query else None, command_id=None if query else str(uuid4()), idempotency_key=None if query else key)
def _org(runtime):
    organization_id = uuid4(); name = f"Template Org {organization_id}"; org = Organization(id=organization_id, legal_name=name, display_name=name)
    with runtime.create_session() as s: s.add(org); s.commit()
    return organization_id

class _FailingRuntime:
    def __init__(self, runtime): self.runtime = runtime
    def create_session(self):
        session = self.runtime.create_session()
        def fail(): raise RuntimeError("forced commit failure")
        session.commit = fail
        return session

def _counts(runtime, org):
    with runtime.create_session() as s:
        return (s.scalar(select(func.count()).select_from(DossierTemplateVersion).where(DossierTemplateVersion.organization_id == org)), s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)), s.scalar(select(func.count()).select_from(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.organization_id == org)))


def test_publish_retrieve_replay_conflict_and_retire_are_governed(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence)
    service = DossierTemplateService(runtime); command = PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "Residential Solar v1")
    published = service.publish(command, _metadata("publish"), _principal(org, "dossier.template.publish"))
    replay = service.publish(command, _metadata("publish"), _principal(org, "dossier.template.publish"))
    assert published.id == replay.id and published.status == "published" and published.aggregate_version == 1
    assert service.get(published.id, _metadata(None, query=True), _principal(org, "dossier.template.read")).id == published.id
    assert service.get_published("residential_solar", 1, _metadata(None, query=True), _principal(org, "dossier.template.read")).id == published.id
    with pytest.raises(ApplicationError) as conflict:
        service.publish(PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "Changed"), _metadata("publish"), _principal(org, "dossier.template.publish"))
    assert conflict.value.code == ApplicationErrorCode.CONFLICT
    retired = service.retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata("retire"), _principal(org, "dossier.template.retire"))
    assert retired.status == "retired" and retired.aggregate_version == 2 and retired.retired_at
    assert service.retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata("retire"), _principal(org, "dossier.template.retire")).retired_at == retired.retired_at
    with pytest.raises(ApplicationError) as hidden: service.get_published("residential_solar", 1, _metadata(None, query=True), _principal(org, "dossier.template.read"))
    assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    with runtime.create_session() as s:
        assert s.scalar(select(func.count()).select_from(DossierTemplateVersion).where(DossierTemplateVersion.organization_id == org)) == 1
        assert s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)) == 2
        assert s.scalar(select(func.count()).select_from(OpportunityCommandIdempotency).where(OpportunityCommandIdempotency.organization_id == org)) == 2


def test_authority_concealment_and_tenant_local_identity(test_database):
    from yarvis_api.main import app
    runtime, first, second = app.state.yarvis.persistence, _org(app.state.yarvis.persistence), _org(app.state.yarvis.persistence)
    service = DossierTemplateService(runtime); cmd = PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "v1")
    for authority in ("", "dossier.template.retire"):
        with pytest.raises((ApplicationError, ValueError)): service.publish(cmd, _metadata(uuid4().hex), _principal(first, authority))
    assert _counts(runtime, first) == (0, 0, 0)
    one = service.publish(cmd, _metadata("shared"), _principal(first, "dossier.template.publish")); two = service.publish(cmd, _metadata("shared"), _principal(second, "dossier.template.publish"))
    assert one.id != two.id and _counts(runtime, first) == (1, 1, 1) and _counts(runtime, second) == (1, 1, 1)
    for target in (uuid4(), one.id):
        with pytest.raises(ApplicationError) as hidden: service.get(target, _metadata(None, query=True), _principal(second, "dossier.template.read"))
        assert hidden.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
    with pytest.raises(ApplicationError): service.get(one.id, _metadata(None, query=True), _principal(first, "wrong"))
    assert _counts(runtime, first) == (1, 1, 1)


def test_trigger_and_rollbacks_preserve_catalog_history(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence); service = DossierTemplateService(runtime)
    cmd = PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "v1")
    with pytest.raises(RuntimeError): DossierTemplateService(_FailingRuntime(runtime)).publish(cmd, _metadata("rollback-p"), _principal(org, "dossier.template.publish"))
    assert _counts(runtime, org) == (0, 0, 0)
    published = service.publish(cmd, _metadata("rollback-p"), _principal(org, "dossier.template.publish")); other_org = _org(runtime)
    immutable = (published.organization_id, published.stable_key, published.business_type, published.business_version, published.display_name, published.created_at, published.published_at)
    baseline = _counts(runtime, org)
    for field, value in (("organization_id", other_org), ("stable_key", "changed"), ("business_type", "Changed"), ("business_version", "2"), ("display_name", "Changed"), ("created_at", "now()"), ("published_at", "now()")):
        with runtime.create_session() as s:
            with pytest.raises(Exception): s.execute(text(f"UPDATE dossier_template_versions SET {field} = {value if value == 'now()' else ':value'} WHERE id = :id"), {"id": published.id, "value": value}); s.commit()
            s.rollback()
        with runtime.create_session() as s:
            row = s.get(DossierTemplateVersion, published.id)
            assert (row.organization_id, row.stable_key, row.business_type, row.business_version, row.display_name, row.created_at, row.published_at) == immutable
            assert row.status == "published" and row.aggregate_version == 1
        assert _counts(runtime, org) == baseline
    with pytest.raises(RuntimeError): DossierTemplateService(_FailingRuntime(runtime)).retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata("rollback-r"), _principal(org, "dossier.template.retire"))
    with runtime.create_session() as s: assert s.get(DossierTemplateVersion, published.id).status == "published"
    retired = service.retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata("rollback-r"), _principal(org, "dossier.template.retire"))
    assert retired.status == "retired" and _counts(runtime, org) == (1, 2, 2)


def test_retire_and_query_authorities_have_no_rejected_side_effects(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence)
    service = DossierTemplateService(runtime)
    published = service.publish(PublishDossierTemplateVersionCommand("ev_charging", "EV Charging", 1, "EV v1"), _metadata("publish"), _principal(org, "dossier.template.publish"))
    baseline = _counts(runtime, org)
    for authority in ("", "dossier.template.publish"):
        with pytest.raises((ApplicationError, ValueError)):
            service.retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata(uuid4().hex), _principal(org, authority))
        with runtime.create_session() as s:
            row = s.get(DossierTemplateVersion, published.id)
            assert row.status == "published" and row.retired_at is None and row.aggregate_version == 1
        assert _counts(runtime, org) == baseline
    for query in (lambda p: service.get(published.id, _metadata(None, query=True), p), lambda p: service.get_published("ev_charging", 1, _metadata(None, query=True), p)):
        assert query(_principal(org, "dossier.template.read")).id == published.id
        for authority in ("", "dossier.template.publish"):
            with pytest.raises((ApplicationError, ValueError)):
                query(_principal(org, authority))
            with runtime.create_session() as s:
                row = s.get(DossierTemplateVersion, published.id)
                assert row.status == "published" and row.retired_at is None and row.aggregate_version == 1
            assert _counts(runtime, org) == baseline
    retired = service.retire(RetireDossierTemplateVersionCommand(published.id, 1), _metadata("retire"), _principal(org, "dossier.template.retire"))
    assert retired.status == "retired" and retired.aggregate_version == 2 and _counts(runtime, org) == (1, 2, 2)


def test_query_concealment_and_tenant_scope_have_zero_side_effects(test_database):
    from yarvis_api.main import app
    runtime, owner, foreign = app.state.yarvis.persistence, _org(app.state.yarvis.persistence), _org(app.state.yarvis.persistence)
    service = DossierTemplateService(runtime); command = PublishDossierTemplateVersionCommand("commercial_solar", "Commercial Solar", 1, "Commercial v1")
    owned = service.publish(command, _metadata("same-key"), _principal(owner, "dossier.template.publish"))
    foreign_template = service.publish(command, _metadata("same-key"), _principal(foreign, "dossier.template.publish"))
    foreign_only = service.publish(PublishDossierTemplateVersionCommand("engineering_services", "Engineering Services", 1, "Engineering v1"), _metadata("foreign-only"), _principal(foreign, "dossier.template.publish"))
    assert owned.id != foreign_template.id and _counts(runtime, owner) == (1, 1, 1) and _counts(runtime, foreign) == (2, 2, 2)
    with runtime.create_session() as s:
        before = s.get(DossierTemplateVersion, owned.id)
        immutable = (before.aggregate_version, before.created_at, before.published_at, before.retired_at)
    def concealed(call):
        with pytest.raises(ApplicationError) as error: call()
        assert error.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        return (error.value.code, error.value.message, error.value.details)
    by_id_missing = concealed(lambda: service.get(uuid4(), _metadata(None, query=True), _principal(owner, "dossier.template.read")))
    by_id_foreign = concealed(lambda: service.get(foreign_template.id, _metadata(None, query=True), _principal(owner, "dossier.template.read")))
    exact_missing = concealed(lambda: service.get_published("commercial_solar", 2, _metadata(None, query=True), _principal(owner, "dossier.template.read")))
    exact_foreign = concealed(lambda: service.get_published("engineering_services", 1, _metadata(None, query=True), _principal(owner, "dossier.template.read")))
    assert by_id_missing == by_id_foreign and exact_missing == exact_foreign
    service.retire(RetireDossierTemplateVersionCommand(owned.id, 1), _metadata("retire"), _principal(owner, "dossier.template.retire"))
    assert concealed(lambda: service.get_published("commercial_solar", 1, _metadata(None, query=True), _principal(owner, "dossier.template.read"))) == exact_missing
    historical = service.get(owned.id, _metadata(None, query=True), _principal(owner, "dossier.template.read"))
    assert historical.status == "retired"
    with runtime.create_session() as s:
        row = s.get(DossierTemplateVersion, owned.id)
        assert row.aggregate_version == 2 and (row.created_at, row.published_at) == immutable[1:3]
    assert _counts(runtime, owner) == (1, 2, 2) and _counts(runtime, foreign) == (2, 2, 2)


def test_catalog_operations_do_not_bind_or_mutate_foundation_chain(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence); opportunity_service = OpportunityService(runtime)
    proposed = opportunity_service.propose(ProposeOpportunityCommand("Foundation compatibility"), _metadata("op"), _principal(org, "opportunity.propose"))
    opportunity_service.confirm(ConfirmOpportunityCommand(proposed.id, 1), _metadata("confirm"), _principal(org, "opportunity.confirm"))
    with runtime.create_session() as s: workspace = s.scalar(select(OpportunityWorkspace).where(OpportunityWorkspace.opportunity_id == proposed.id))
    opportunity_service.assign_template(AssignOpportunityTemplateCommand(workspace.id, "residential_solar", 1), _metadata("specialize"), _principal(org, "opportunity.specialize"))
    with runtime.create_session() as s:
        opportunity, workspace, dossier = s.get(Opportunity, proposed.id), s.get(OpportunityWorkspace, workspace.id), s.scalar(select(OpportunityDossier).where(OpportunityDossier.workspace_id == workspace.id))
        before = (opportunity.lifecycle_status, opportunity.aggregate_version, workspace.aggregate_version, workspace.template_id, workspace.template_version, dossier.template_id, dossier.aggregate_version, s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)))
    catalog = DossierTemplateService(runtime); template = catalog.publish(PublishDossierTemplateVersionCommand("residential_solar", "Residential Solar", 1, "Catalog v1"), _metadata("catalog-p"), _principal(org, "dossier.template.publish")); catalog.retire(RetireDossierTemplateVersionCommand(template.id, 1), _metadata("catalog-r"), _principal(org, "dossier.template.retire"))
    with runtime.create_session() as s:
        opportunity, after_workspace, after_dossier = s.get(Opportunity, proposed.id), s.get(OpportunityWorkspace, workspace.id), s.get(OpportunityDossier, dossier.id)
        after = (opportunity.lifecycle_status, opportunity.aggregate_version, after_workspace.aggregate_version, after_workspace.template_id, after_workspace.template_version, after_dossier.template_id, after_dossier.aggregate_version, s.scalar(select(func.count()).select_from(DomainEvent).where(DomainEvent.organization_id == org)) - 2)
    assert after == before


def test_publication_concurrency_receipt_and_business_identity_recovery(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence)
    def race(items):
        barrier = Barrier(2)
        def invoke(item):
            command, key = item
            barrier.wait()
            try: return "ok", DossierTemplateService(runtime).publish(command, _metadata(key), _principal(org, "dossier.template.publish")).id
            except ApplicationError as error: return "conflict", error.code
        with ThreadPoolExecutor(max_workers=2) as pool: return list(pool.map(invoke, items))
    matching = PublishDossierTemplateVersionCommand("battery_storage", "Battery Storage", 1, "Battery v1")
    assert len({value for state, value in race(((matching, "match"), (matching, "match"))) if state == "ok"}) == 1 and _counts(runtime, org) == (1, 1, 1)
    mismatch = race(((PublishDossierTemplateVersionCommand("ev_charging", "EV Charging", 1, "EV A"), "mismatch"), (PublishDossierTemplateVersionCommand("ev_charging", "EV Charging", 1, "EV B"), "mismatch")))
    assert sorted(state for state, _ in mismatch) == ["conflict", "ok"] and _counts(runtime, org) == (2, 2, 2)
    different = race(((PublishDossierTemplateVersionCommand("engineering_services", "Engineering Services", 1, "A"), "first"), (PublishDossierTemplateVersionCommand("engineering_services", "Engineering Services", 1, "B"), "second")))
    assert sorted(state for state, _ in different) == ["conflict", "ok"] and _counts(runtime, org) == (3, 3, 3)


def test_retirement_concurrency_replay_conflict_and_different_key(test_database):
    from yarvis_api.main import app
    runtime, org = app.state.yarvis.persistence, _org(app.state.yarvis.persistence); service = DossierTemplateService(runtime)
    def published(key, version): return service.publish(PublishDossierTemplateVersionCommand(f"retire_{version}", "Retire Test", 1, f"v{version}"), _metadata(key), _principal(org, "dossier.template.publish"))
    def race(template, items):
        barrier = Barrier(2)
        def invoke(item):
            expected, key = item; barrier.wait()
            try: return "ok", DossierTemplateService(runtime).retire(RetireDossierTemplateVersionCommand(template.id, expected), _metadata(key), _principal(org, "dossier.template.retire")).id
            except ApplicationError as error: return "conflict", error.code
        with ThreadPoolExecutor(max_workers=2) as pool: return list(pool.map(invoke, items))
    first = published("p1", 1); assert len({v for state, v in race(first, ((1, "match"), (1, "match"))) if state == "ok"}) == 1
    second = published("p2", 2); assert sorted(state for state, _ in race(second, ((1, "mismatch"), (2, "mismatch")))) == ["conflict", "ok"]
    third = published("p3", 3); assert sorted(state for state, _ in race(third, ((1, "first"), (1, "second")))) == ["conflict", "ok"]

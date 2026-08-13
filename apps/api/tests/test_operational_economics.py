"""Focused conformance coverage for OV-002 Operational Economics."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.operational_context import Project, Site
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


def _headers(authority: str, organization_id: UUID = ORGANIZATION_ID) -> dict[str, str]:
    subject = "economics:recorder" if authority == "economics.fact.record" else "economics:unmapped"
    if organization_id == OTHER_ORGANIZATION_ID:
        subject += "-other"
    return {
        "x-yarvis-subject": subject,
        "x-yarvis-actor": "forged-economics-actor",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


@pytest.fixture(autouse=True)
def economic_subject(clean_database) -> UUID:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all((
            Organization(id=ORGANIZATION_ID, legal_name="Economics", display_name="Economics"),
            Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other economics", display_name="Other economics"),
        ))
        session.flush()
        for organization_id, subject in ((ORGANIZATION_ID, "economics:recorder"), (OTHER_ORGANIZATION_ID, "economics:recorder-other")):
            principal = Principal(external_subject=subject, status="active")
            session.add(principal)
            session.flush()
            session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role="economics_fact_recorder"))
        site = Site(organization_id=ORGANIZATION_ID, reference="economics-site")
        session.add(site)
        session.flush()
        project = Project(organization_id=ORGANIZATION_ID, site_id=site.id, reference="economics-project")
        session.add(project)
        session.commit()
        return project.id


def _record(project_id: UUID, fact_type: str, amount: str, *, key: str | None = None) -> dict:
    response = client.post(
        "/operational-economics/facts",
        json={
            "subject_type": "project", "subject_id": str(project_id), "fact_type": fact_type,
            "amount": amount, "currency": "MXN", "effective_at": "2026-07-29T00:00:00+00:00",
            "source_type": "operator_assertion", "source_reference": f"source-{fact_type}",
            "evidence_references": ["evidence:test"], "idempotency_key": key or uuid4().hex,
            "correlation_id": str(uuid4()),
        },
        headers=_headers("economics.fact.record"),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_facts_are_idempotent_append_only_and_emit_domain_events(economic_subject: UUID) -> None:
    key = uuid4().hex
    fact = _record(economic_subject, "revenue_expected", "1000.00", key=key)
    replay = _record(economic_subject, "revenue_expected", "1000.00", key=key)
    assert replay["id"] == fact["id"]
    with app.state.yarvis.persistence.create_session() as session:
        events = session.scalars(select(DomainEvent).where(DomainEvent.aggregate_id == UUID(fact["id"]))).all()
    assert [event.event_type for event in events] == ["economic_fact.recorded"]
    with app.state.yarvis.persistence.create_session() as session, pytest.raises(DBAPIError):
        session.execute(
            text("UPDATE economic_facts SET source_reference = 'mutated' WHERE id = :fact_id"),
            {"fact_id": fact["id"]},
        )
        session.commit()


def test_correction_replaces_current_value_and_summary_is_direct_only(economic_subject: UUID) -> None:
    fact = _record(economic_subject, "revenue_expected", "1000.00")
    corrected = client.post(
        f"/operational-economics/facts/{fact['id']}/corrections",
        json={
            "amount": "1200.00", "effective_at": "2026-07-29T01:00:00+00:00",
            "source_type": "operator_correction", "source_reference": "source-correction",
            "evidence_references": ["evidence:corrected"], "correction_reason": "Updated approved estimate",
            "idempotency_key": uuid4().hex, "correlation_id": str(uuid4()),
        }, headers=_headers("economics.fact.correct"),
    )
    assert corrected.status_code == 201, corrected.text
    summary = client.get(
        f"/operational-economics/subjects/project/{economic_subject}/summary?currency=MXN",
        headers=_headers("economics.read"),
    )
    assert summary.status_code == 200, summary.text
    assert Decimal(summary.json()["expected_revenue"]) == Decimal("1200.00")
    assert summary.json()["input_fact_ids"] == [corrected.json()["id"]]
    with app.state.yarvis.persistence.create_session() as session:
        event = session.scalar(select(DomainEvent).where(DomainEvent.aggregate_id == UUID(corrected.json()["id"])))
    assert event is not None
    assert event.event_type == "economic_fact.corrected"
    assert event.payload["supersedes_fact_id"] == fact["id"]
    assert event.payload["correction_reason"] == "Updated approved estimate"


def test_cross_tenant_subject_is_concealed(economic_subject: UUID) -> None:
    response = client.get(
        f"/operational-economics/subjects/project/{economic_subject}/facts",
        headers=_headers("economics.read", OTHER_ORGANIZATION_ID),
    )
    assert response.status_code == 404

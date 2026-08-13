from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session as SASession

from yarvis_api.application.contracts import WS001CommandName, command_contracts
from yarvis_api.main import app
from yarvis_api.models.case import Case
from yarvis_api.models.conversation import ConversationMessage
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.evidence import Evidence
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.message import Message
from yarvis_api.models.observation_engine import Observation
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

client = TestClient(app)
NO_SERVER_RAISE_CLIENT = TestClient(app, raise_server_exceptions=False)


CANONICAL_ORGANIZATION_ID = uuid4()
PRIMARY_PRINCIPAL_ID = uuid4()
PRIMARY_SUBJECT = "connector:mailbox-01"

TRUSTED_HEADERS = {
    "x-yarvis-actor": PRIMARY_SUBJECT,
    "x-yarvis-organization": str(uuid4()),
    "x-yarvis-authority": "inbound.intake",
    "x-yarvis-auth-token": "deterministic-inbound-intake",
    "x-yarvis-roles": "connector",
    "x-yarvis-permissions": "intake:receive,intake:message",
}


def _read_headers(**overrides: str) -> dict[str, str]:
    return {**TRUSTED_HEADERS, "x-yarvis-authority": "inbound.read", **overrides}


def _headers_for_subject(subject: str, **overrides: str) -> dict[str, str]:
    return {**TRUSTED_HEADERS, "x-yarvis-actor": subject, "x-yarvis-organization": str(uuid4()), **overrides}


def _add_membership(subject: str, organization_id: UUID, role: str) -> dict[str, str]:
    with app.state.yarvis.persistence.create_session() as session:
        principal = Principal(external_subject=subject, status="active")
        session.add(principal)
        session.flush()
        session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role=role))
        session.commit()
    return _headers_for_subject(subject)


def _create_organization(subject: str, role: str) -> dict[str, str]:
    with app.state.yarvis.persistence.create_session() as session:
        organization = Organization(
            legal_name=f"Deterministic Intake {uuid4().hex}",
            display_name="Deterministic Intake",
        )
        session.add(organization)
        session.flush()
        organization_id = organization.id
        session.commit()
    return _add_membership(subject, organization_id, role)


def _set_primary_role(role: str) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        membership = session.scalar(
            select(PrincipalMembership).where(PrincipalMembership.principal_id == PRIMARY_PRINCIPAL_ID)
        )
        assert membership is not None
        membership.role = role
        session.commit()


@pytest.fixture(autouse=True)
def trusted_organization(clean_database) -> None:
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all(
            (
                Organization(
                    id=CANONICAL_ORGANIZATION_ID,
                    legal_name="Deterministic Intake Tenant",
                    display_name="Deterministic Intake Tenant",
                ),
                Principal(id=PRIMARY_PRINCIPAL_ID, external_subject=PRIMARY_SUBJECT, status="active"),
            )
        )
        session.flush()
        session.add(PrincipalMembership(principal_id=PRIMARY_PRINCIPAL_ID, organization_id=CANONICAL_ORGANIZATION_ID, role="inbound_operator"))
        session.commit()


def _payload(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "external_source": "email",
        "external_message_id": uuid4().hex,
        "connector_delivery_id": "deliv-001",
        "sender": "sender@example.com",
        "recipients": ["ops@example.com"],
        "subject": "Inbound receipt",
        "text_body": "Inbound message body",
        "html_body": "<p>Inbound message body</p>",
        "content_type": "message/rfc822",
        "source_timestamp": now.isoformat(),
        "received_timestamp": now.isoformat(),
        "headers": {"message-id": uuid4().hex},
        "correlation_id": str(uuid4()),
        "causation_id": None,
        "idempotency_key": "deterministic-intake-001",
    }
    payload.update(overrides)
    return payload


def _count(session: SASession, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def _assert_truncated_graph(session: SASession) -> None:
    assert _count(session, IntakeItem) == 1
    assert _count(session, Message) == 1
    assert _count(session, DomainEvent) == 2
    assert _count(session, Evidence) == 0
    assert _count(session, Observation) == 0
    assert _count(session, ConversationMessage) == 0
    assert _count(session, Case) == 0


def test_deterministic_inbound_intake_creates_intake_message_and_events() -> None:
    response = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS)

    assert response.status_code == 201, response.text
    body = response.json()

    assert body["message"]["external_source"] == "email"
    assert body["message"]["external_message_id"] == body["source_metadata"]["external_message_id"]
    assert body["message"]["recipients"] == ["ops@example.com"]
    assert body["message"]["text_body"] == "Inbound message body"
    assert body["message"]["trace_metadata"]["principal"]["authority"] == "inbound.intake"
    assert body["message"]["trace_metadata"]["principal"]["actor_id"] == str(PRIMARY_PRINCIPAL_ID)
    assert body["trace_metadata"]["correlation_id"] == body["message"]["trace_metadata"]["correlation_id"]
    assert [event["event_type"] for event in body["events"]] == ["intake.received", "message.registered"]
    assert body["events"][0]["correlation_id"] == body["trace_metadata"]["correlation_id"]
    assert body["events"][1]["payload"]["message_id"] == body["message"]["id"]

    with app.state.yarvis.persistence.create_session() as session:
        _assert_truncated_graph(session)
        intake = session.scalar(select(IntakeItem))
        message = session.scalar(select(Message))
        assert intake is not None
        assert message is not None
        assert str(message.intake_item_id) == str(intake.id)
        assert intake.source_metadata["external_message_id"] == body["source_metadata"]["external_message_id"]
        assert str(intake.organization_id) == str(CANONICAL_ORGANIZATION_ID)
        assert intake.trace_metadata["principal"]["authority"] == "inbound.intake"
        assert message.trace_metadata["principal"]["actor_id"] == str(PRIMARY_PRINCIPAL_ID)

    query_response = client.get(f"/intake/deterministic/{body['id']}", headers=_read_headers())
    assert query_response.status_code == 200, query_response.text
    assert query_response.json()["message"]["id"] == body["message"]["id"]
    assert query_response.json()["events"][0]["event_type"] == "intake.received"


def test_deterministic_inbound_intake_replays_an_equivalent_idempotency_key() -> None:
    payload = _payload(idempotency_key="deterministic-intake-replay")

    first_response = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    second_response = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)

    assert first_response.status_code == 201, first_response.text
    assert second_response.status_code == 201, second_response.text
    assert second_response.json()["id"] == first_response.json()["id"]
    with app.state.yarvis.persistence.create_session() as session:
        _assert_truncated_graph(session)


def test_deterministic_inbound_intake_rejects_conflicting_idempotency_key_reuse() -> None:
    payload = _payload(idempotency_key="deterministic-intake-conflict")

    first_response = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    conflict_response = client.post(
        "/intake/deterministic",
        json={**payload, "subject": "Different inbound receipt"},
        headers=TRUSTED_HEADERS,
    )

    assert first_response.status_code == 201, first_response.text
    assert conflict_response.status_code == 409, conflict_response.text
    assert conflict_response.json()["code"] == "CONFLICT"
    with app.state.yarvis.persistence.create_session() as session:
        _assert_truncated_graph(session)


def test_deterministic_inbound_intake_rejects_missing_actor() -> None:
    response = client.post(
        "/intake/deterministic",
        json=_payload(),
        headers={k: v for k, v in TRUSTED_HEADERS.items() if k != "x-yarvis-actor"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"


def test_deterministic_inbound_intake_ignores_forged_authority_header() -> None:
    response = client.post(
        "/intake/deterministic",
        json=_payload(),
        headers={k: v for k, v in TRUSTED_HEADERS.items() if k != "x-yarvis-authority"},
    )

    assert response.status_code == 201, response.text


def test_deterministic_inbound_intake_rejects_role_without_intake_permission() -> None:
    _set_primary_role("radar_viewer")
    response = client.post(
        "/intake/deterministic",
        json=_payload(),
        headers={**TRUSTED_HEADERS, "x-yarvis-authority": "inbound.intake"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"


def test_transport_payload_cannot_escalate_authority() -> None:
    response = client.post(
        "/intake/deterministic",
        json={
            **_payload(),
            "actor": {"actor_id": "attacker", "actor_type": "human"},
            "authority": {"authority_scope": "unrestricted"},
            "organization_id": str(uuid4()),
        },
        headers=TRUSTED_HEADERS,
    )

    assert response.status_code == 422
    assert "extra inputs" in response.text.lower()


def test_deterministic_inbound_intake_rejects_unsupported_source() -> None:
    response = client.post(
        "/intake/deterministic",
        json=_payload(external_source="fax"),
        headers=TRUSTED_HEADERS,
    )

    assert response.status_code == 422


def test_deterministic_inbound_intake_is_queryable_without_orm_exposure() -> None:
    created = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS).json()
    response = client.get(f"/intake/deterministic/{created['id']}", headers=_read_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == created["id"]
    assert body["message"]["id"] == created["message"]["id"]
    assert isinstance(body["message"], dict)
    assert isinstance(body["events"], list)


def test_message_flush_failure_rolls_back_entire_use_case() -> None:
    def fail_on_message_flush(session, flush_context, instances):
        if any(isinstance(obj, Message) for obj in session.new):
            raise RuntimeError("message flush failed")

    event.listen(SASession, "before_flush", fail_on_message_flush)
    try:
        response = NO_SERVER_RAISE_CLIENT.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS)
    finally:
        event.remove(SASession, "before_flush", fail_on_message_flush)

    assert response.status_code == 500
    with app.state.yarvis.persistence.create_session() as session:
        assert _count(session, IntakeItem) == 0
        assert _count(session, Message) == 0
        assert _count(session, DomainEvent) == 0


def test_event_flush_failure_rolls_back_entire_use_case() -> None:
    def fail_on_event_flush(session, flush_context, instances):
        if any(isinstance(obj, DomainEvent) for obj in session.new):
            raise RuntimeError("event flush failed")

    event.listen(SASession, "before_flush", fail_on_event_flush)
    try:
        response = NO_SERVER_RAISE_CLIENT.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS)
    finally:
        event.remove(SASession, "before_flush", fail_on_event_flush)

    assert response.status_code == 500
    with app.state.yarvis.persistence.create_session() as session:
        assert _count(session, IntakeItem) == 0
        assert _count(session, Message) == 0
        assert _count(session, DomainEvent) == 0


def test_command_contracts_include_f002_intake_commands() -> None:
    assert command_contracts[WS001CommandName.RECEIVE_INTAKE].requires_authority is True
    assert command_contracts[WS001CommandName.REGISTER_MESSAGE].requires_idempotency_key is True


def test_deterministic_inbound_intake_uses_persisted_organization_without_header() -> None:
    response = client.post(
        "/intake/deterministic",
        json=_payload(),
        headers={key: value for key, value in TRUSTED_HEADERS.items() if key != "x-yarvis-organization"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["organization_id"] == str(CANONICAL_ORGANIZATION_ID)


def test_deterministic_inbound_intake_uses_organization_scoped_idempotency() -> None:
    payload = _payload(idempotency_key="organization-scoped-key")
    first_response = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    other_organization_headers = _create_organization("connector:mailbox-03", "inbound_operator")
    second_response = client.post("/intake/deterministic", json=payload, headers=other_organization_headers)

    assert first_response.status_code == 201, first_response.text
    assert second_response.status_code == 201, second_response.text
    assert second_response.json()["id"] != first_response.json()["id"]
    with app.state.yarvis.persistence.create_session() as session:
        assert _count(session, IntakeItem) == 2
        assert _count(session, Message) == 2
        assert _count(session, DomainEvent) == 4


def test_deterministic_inbound_intake_replays_for_a_different_actor_in_the_same_organization() -> None:
    payload = _payload(idempotency_key="same-organization-different-actor")
    first_response = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    replay_response = client.post(
        "/intake/deterministic",
        json=payload,
        headers=_add_membership("connector:mailbox-02", CANONICAL_ORGANIZATION_ID, "inbound_operator"),
    )

    assert first_response.status_code == 201, first_response.text
    assert replay_response.status_code == 201, replay_response.text
    assert replay_response.json()["id"] == first_response.json()["id"]
    with app.state.yarvis.persistence.create_session() as session:
        _assert_truncated_graph(session)


def test_intake_detail_requires_governed_same_organization_access() -> None:
    created = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS).json()
    other_organization_headers = _create_organization("connector:mailbox-04", "inbound_viewer")

    unauthorized = client.get(f"/intake/deterministic/{created['id']}", headers=other_organization_headers)

    assert unauthorized.status_code == 404
    assert unauthorized.json()["code"] == "RESOURCE_NOT_FOUND"
    assert "Inbound message body" not in unauthorized.text
    assert "message-id" not in unauthorized.text
    assert "intake.received" not in unauthorized.text
    assert "trace_metadata" not in unauthorized.text


def test_legacy_intake_routes_conceal_tenant_owned_records() -> None:
    with app.state.yarvis.persistence.create_session() as session:
        legacy = IntakeItem(
            source_type="manual_text",
            content_type="text/plain",
            title="Legacy intake",
            text_content="legacy body",
        )
        session.add(legacy)
        session.commit()
        legacy_id = legacy.id

    governed = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS).json()

    legacy_list = client.get("/intake")
    legacy_detail = client.get(f"/intake/{legacy_id}")
    governed_through_legacy = client.get(f"/intake/{governed['id']}")
    missing = client.get(f"/intake/{uuid4()}")
    governed_detail = client.get(f"/intake/deterministic/{governed['id']}", headers=_read_headers())

    assert legacy_list.status_code == 200
    assert [item["id"] for item in legacy_list.json()] == [str(legacy_id)]
    assert "Inbound message body" not in legacy_list.text
    assert legacy_detail.status_code == 200
    assert legacy_detail.json()["id"] == str(legacy_id)
    assert governed_through_legacy.status_code == 404
    assert governed_through_legacy.json() == missing.json()
    assert "Inbound message body" not in governed_through_legacy.text
    assert "message-id" not in governed_through_legacy.text
    assert "intake.received" not in governed_through_legacy.text
    assert "trace_metadata" not in governed_through_legacy.text
    assert governed_detail.status_code == 200


def test_intake_detail_rejects_missing_actor() -> None:
    created = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS).json()

    response = client.get(
        f"/intake/deterministic/{created['id']}",
        headers={key: value for key, value in _read_headers().items() if key != "x-yarvis-actor"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"


def test_inbound_viewer_can_read_but_cannot_create() -> None:
    viewer_headers = _add_membership("connector:viewer", CANONICAL_ORGANIZATION_ID, "inbound_viewer")
    denied = client.post("/intake/deterministic", json=_payload(), headers=viewer_headers)
    assert denied.status_code == 403
    created = client.post("/intake/deterministic", json=_payload(), headers=TRUSTED_HEADERS).json()
    read = client.get(f"/intake/deterministic/{created['id']}", headers=viewer_headers)
    assert read.status_code == 200


def test_revoked_membership_is_denied_before_replay() -> None:
    payload = _payload(idempotency_key="revoked-replay")
    created = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    assert created.status_code == 201
    with app.state.yarvis.persistence.create_session() as session:
        membership = session.scalar(select(PrincipalMembership).where(PrincipalMembership.principal_id == PRIMARY_PRINCIPAL_ID))
        assert membership is not None
        membership.status = "revoked"
        membership.revoked_at = datetime.now(timezone.utc)
        session.commit()
    denied = client.post("/intake/deterministic", json=payload, headers=TRUSTED_HEADERS)
    assert denied.status_code == 403
    assert denied.json()["code"] == "AUTHORIZATION_DENIED"


def test_intake_detail_conceals_legacy_and_nonexistent_intakes() -> None:
    with app.state.yarvis.persistence.create_session() as session:
        legacy = IntakeItem(
            source_type="manual_text",
            content_type="text/plain",
            title="Legacy intake",
            text_content="legacy body",
        )
        session.add(legacy)
        session.commit()
        legacy_id = legacy.id

    legacy_response = client.get(f"/intake/deterministic/{legacy_id}", headers=_read_headers())
    missing_response = client.get(f"/intake/deterministic/{uuid4()}", headers=_read_headers())

    assert legacy_response.status_code == 404
    assert missing_response.status_code == 404

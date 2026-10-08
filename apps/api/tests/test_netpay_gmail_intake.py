from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.netpay_gmail_intake import (
    NetpayGmailCommandReceipt,
    NetpayGmailConnection,
    NetpayGmailSourceItem,
    NetpayGmailSyncRun,
)
from yarvis_api.models.netpay_inbox import CommercialIntakeItem, NetpayServiceCase
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.netpay_gmail_provider import DEFAULT_FAKE_GMAIL_PROVIDER, GmailSourceMessage

client = TestClient(app)


def _headers(subject: str, key: str) -> dict[str, str]:
    return {
        "X-Yarvis-Subject": subject,
        "X-Yarvis-Auth-Token": "deterministic-inbound-intake",
        "Idempotency-Key": key,
    }


def _setup() -> tuple[object, object, object, object]:
    with app.state.yarvis.persistence.create_session() as db:
        db.execute(delete(NetpayGmailCommandReceipt))
        db.execute(delete(NetpayGmailSourceItem))
        db.execute(delete(NetpayGmailSyncRun))
        db.execute(delete(NetpayGmailConnection))
        db.commit()
        org = Organization(legal_name="Synthetic Stores Org", display_name="Synthetic Stores Org", status="active")
        other = Organization(legal_name="Synthetic Other Org", display_name="Synthetic Other Org", status="active")
        operator = Principal(external_subject="gmail:d1:operator", status="active")
        foreign = Principal(external_subject="gmail:d1:foreign", status="active")
        db.add_all((org, other, operator, foreign))
        db.flush()
        db.add_all(
            (
                PrincipalMembership(principal_id=operator.id, organization_id=org.id, role="netpay_inbox_operator"),
                PrincipalMembership(principal_id=foreign.id, organization_id=other.id, role="netpay_inbox_operator"),
            )
        )
        db.commit()
        return org.id, other.id, operator.id, foreign.id


def _fixture(now: datetime) -> list[GmailSourceMessage]:
    return [
        GmailSourceMessage(
            message_id="synthetic-message-001",
            thread_id="synthetic-thread-stores",
            received_at=now - timedelta(days=1),
            sender="synthetic.sender@example.invalid",
            recipient="netpay@example.invalid",
            subject="Alta de e-commerce Stores para nuevas sucursales",
            body="<p>Solicitud sintética para Stores.</p><script>alert('ignored')</script>",
            label_ids=frozenset({"LABEL_STORES"}),
            attachments=({"name": "alta.pdf", "mime_type": "application/pdf", "size": 128},),
        ),
        GmailSourceMessage(
            message_id="synthetic-message-002",
            thread_id="synthetic-thread-stores",
            received_at=now - timedelta(days=2),
            sender="synthetic.sender@example.invalid",
            recipient="netpay@example.invalid",
            subject="Re: Alta de e-commerce Stores",
            body="Falta confirmar el cliente sintético.",
            label_ids=frozenset({"LABEL_STORES"}),
        ),
        GmailSourceMessage(
            message_id="synthetic-message-old",
            thread_id="synthetic-thread-old",
            received_at=now - timedelta(days=31),
            subject="Fuera de ventana",
            body="No debe entrar en el backfill.",
            label_ids=frozenset({"LABEL_STORES"}),
        ),
    ]


def test_d1_gmail_entry_processing_persistence_query_and_idempotency() -> None:
    org_id, other_id, _, _ = _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-stores-account", _fixture(now))
    headers = _headers("gmail:d1:operator", "gmail-connect-1")

    created = client.post(
        "/netpay/gmail/connections",
        headers=headers,
        json={
            "provider_account_id": "synthetic-stores-account",
            "label_id": "LABEL_STORES",
            "query": "newer_than:30d",
            "credential_secret_ref": "synthetic-ref-stores",
        },
    )
    assert created.status_code == 201
    connection_id = created.json()["id"]
    assert "credential_secret_ref" not in created.json()

    validated = client.post(
        f"/netpay/gmail/connections/{connection_id}/validate",
        headers=_headers("gmail:d1:operator", "gmail-validate-1"),
    )
    assert validated.status_code == 200
    assert validated.json()["state"] == "ready"

    synced = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-1"),
        json={"backfill_days": 30},
    )
    assert synced.status_code == 201
    assert synced.json()["status"] == "succeeded"
    assert synced.json()["captured_count"] == 2
    assert synced.json()["deduplicated_count"] == 0
    assert synced.json()["cursor_after"]
    assert (
        client.post(
            f"/netpay/gmail/connections/{connection_id}/sync",
            headers=_headers("gmail:d1:operator", "gmail-sync-too-wide"),
            json={"backfill_days": 31},
        ).status_code
        == 422
    )

    replay = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-1"),
        json={"backfill_days": 30},
    )
    assert replay.status_code == 201
    assert replay.json() == synced.json()

    second_run = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "gmail-sync-2"),
        json={"backfill_days": 30},
    )
    assert second_run.status_code == 201
    assert second_run.json()["captured_count"] == 0
    assert second_run.json()["deduplicated_count"] == 2
    assert second_run.json()["cursor_after"] == synced.json()["cursor_after"]

    page = client.get("/netpay/gmail/source-items", headers=_headers("gmail:d1:operator", "gmail-read-1"))
    assert page.status_code == 200
    assert page.json()["total"] == 2
    first = next(item for item in page.json()["items"] if item["gmail_message_id"] == "synthetic-message-001")
    assert first["gmail_thread_id"] == "synthetic-thread-stores"
    assert first["plain_excerpt"]
    assert "alert" not in first["plain_excerpt"]
    assert first["attachment_metadata"] == [{"name": "alta.pdf", "mime_type": "application/pdf", "size": 128}]
    assert first["provenance"]["label_id"] == "LABEL_STORES"

    detail = client.get(
        f"/netpay/gmail/source-items/{first['id']}", headers=_headers("gmail:d1:operator", "gmail-read-2")
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == first["id"]
    assert (
        client.get(
            f"/netpay/gmail/source-items/{first['id']}",
            headers={**_headers("gmail:d1:operator", "gmail-foreign"), "X-Yarvis-Organization-Selector": str(other_id)},
        ).status_code
        == 404
    )

    with app.state.yarvis.persistence.create_session() as db:
        assert (
            db.scalar(select(NetpayGmailSourceItem).where(NetpayGmailSourceItem.organization_id == org_id)) is not None
        )
        assert db.scalar(select(NetpayGmailConnection).where(NetpayGmailConnection.id == connection_id)).cursor
        event_types = {
            event.event_type
            for event in db.scalars(select(DomainEvent).where(DomainEvent.organization_id == org_id)).all()
        }
        assert {
            "netpay.gmail.source_connected",
            "netpay.gmail.manual_sync_started",
            "netpay.gmail.manual_sync_completed",
            "netpay.gmail.source_item_captured",
            "netpay.gmail.source_item_deduplicated",
        } <= event_types
        assert db.scalar(select(CommercialIntakeItem).where(CommercialIntakeItem.organization_id == org_id)) is None
        assert db.scalar(select(NetpayServiceCase).where(NetpayServiceCase.organization_id == org_id)) is None


def test_d1_changed_replay_is_quarantined_and_cursor_does_not_advance() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-conflict-account", _fixture(now)[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "conflict-connect"),
        json={
            "provider_account_id": "synthetic-conflict-account",
            "label_id": "LABEL_STORES",
            "credential_secret_ref": "synthetic-ref",
        },
    ).json()
    connection_id = connection["id"]
    first = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "conflict-sync-1"),
        json={},
    )
    assert first.status_code == 201
    cursor = first.json()["cursor_after"]
    DEFAULT_FAKE_GMAIL_PROVIDER.seed(
        "synthetic-conflict-account",
        [replace(_fixture(now)[0], body="changed synthetic body")],
    )
    conflict = client.post(
        f"/netpay/gmail/connections/{connection_id}/sync",
        headers=_headers("gmail:d1:operator", "conflict-sync-2"),
        json={},
    )
    assert conflict.status_code == 201
    assert conflict.json()["status"] == "partially_failed"
    assert conflict.json()["conflict_count"] == 1
    assert conflict.json()["cursor_after"] is None
    with app.state.yarvis.persistence.create_session() as db:
        item = db.scalar(
            select(NetpayGmailSourceItem).where(NetpayGmailSourceItem.gmail_message_id == "synthetic-message-001")
        )
        assert item is not None
        assert item.plain_excerpt != "changed synthetic body"
        assert item.conflict_fingerprint is not None
        assert (
            db.scalar(select(NetpayGmailConnection).where(NetpayGmailConnection.id == connection_id)).cursor == cursor
        )


def test_d1_label_validation_fails_closed() -> None:
    _setup()
    now = datetime.now(timezone.utc)
    DEFAULT_FAKE_GMAIL_PROVIDER.clear()
    DEFAULT_FAKE_GMAIL_PROVIDER.seed("synthetic-label-account", _fixture(now)[:1])
    connection = client.post(
        "/netpay/gmail/connections",
        headers=_headers("gmail:d1:operator", "label-connect"),
        json={
            "provider_account_id": "synthetic-label-account",
            "label_id": "WRONG_LABEL",
            "credential_secret_ref": "synthetic-ref",
        },
    ).json()
    validation = client.post(
        f"/netpay/gmail/connections/{connection['id']}/validate",
        headers=_headers("gmail:d1:operator", "label-validate"),
    )
    assert validation.status_code == 422
    assert validation.json()["detail"]["code"] == "label_not_found"
    with app.state.yarvis.persistence.create_session() as db:
        assert db.scalar(select(NetpayGmailSourceItem)) is None

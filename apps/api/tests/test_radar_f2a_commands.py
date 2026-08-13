from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

from yarvis_api.api.routes import radar as radar_routes
from yarvis_api.main import app
from yarvis_api.models.domain_event import DomainEvent
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.models.radar import RadarActivity, RadarCommandReceipt, RadarMerchant, RadarRequest


client = TestClient(app)


def _context(*, operator_role: str = "radar_operator"):
    with app.state.yarvis.persistence.create_session() as db:
        organization = Organization(legal_name="F2A primary", display_name="F2A primary", status="active")
        foreign_organization = Organization(legal_name="F2A foreign", display_name="F2A foreign", status="active")
        operator = Principal(external_subject="f2a:operator", status="active")
        viewer = Principal(external_subject="f2a:viewer", status="active")
        foreign_operator = Principal(external_subject="f2a:foreign", status="active")
        db.add_all((organization, foreign_organization, operator, viewer, foreign_operator))
        db.flush()
        membership = PrincipalMembership(principal_id=operator.id, organization_id=organization.id, role=operator_role)
        db.add_all((membership, PrincipalMembership(principal_id=viewer.id, organization_id=organization.id, role="radar_viewer"), PrincipalMembership(principal_id=foreign_operator.id, organization_id=foreign_organization.id, role="radar_operator")))
        db.commit()
        return organization.id, foreign_organization.id, membership.id


def _headers(subject: str, key: str, **extra: str) -> dict[str, str]:
    return {
        "X-Yarvis-Subject": subject,
        "X-Yarvis-Auth-Token": "deterministic-inbound-intake",
        "X-Yarvis-Workspace": "f2a-workspace",
        "Idempotency-Key": key,
        **extra,
    }


def _counts(organization_id: UUID):
    with app.state.yarvis.persistence.create_session() as db:
        return tuple(
            db.scalar(select(func.count()).select_from(model).where(model.organization_id == organization_id))
            for model in (RadarMerchant, RadarRequest, RadarCommandReceipt, RadarActivity, DomainEvent)
        )


def test_create_merchant_requires_key_replays_conflicts_and_is_organization_scoped():
    organization_id, foreign_organization_id, _ = _context()
    payload = {"trade_name": "Merchant F2A", "store_id": "f2a-store", "products": ["tpv"]}
    missing = client.post("/radar/merchants", headers={key: value for key, value in _headers("f2a:operator", "unused").items() if key != "Idempotency-Key"}, json=payload)
    assert missing.status_code == 422
    first = client.post("/radar/merchants", headers=_headers("f2a:operator", "merchant-key", **{"X-Yarvis-Authority": "admin", "X-Yarvis-Organization": str(foreign_organization_id)}), json=payload)
    replay = client.post("/radar/merchants", headers=_headers("f2a:operator", "merchant-key"), json=payload)
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    assert _counts(organization_id) == (1, 0, 1, 1, 1)
    conflict = client.post("/radar/merchants", headers=_headers("f2a:operator", "merchant-key"), json={**payload, "trade_name": "different"})
    assert conflict.status_code == 409
    assert _counts(organization_id) == (1, 0, 1, 1, 1)
    foreign = client.post("/radar/merchants", headers=_headers("f2a:foreign", "merchant-key"), json=payload)
    assert foreign.status_code == 201
    assert _counts(foreign_organization_id) == (1, 0, 1, 1, 1)


def test_create_request_requires_key_replays_conflicts_and_conceals_foreign_merchant():
    organization_id, foreign_organization_id, _ = _context()
    merchant = client.post("/radar/merchants", headers=_headers("f2a:operator", "merchant"), json={"trade_name": "Existing", "products": []}).json()
    payload = {"merchant_id": merchant["id"], "free_text": "create request", "classification": "alta_tpv"}
    missing = client.post("/radar/requests", headers={key: value for key, value in _headers("f2a:operator", "unused").items() if key != "Idempotency-Key"}, json=payload)
    assert missing.status_code == 422
    first = client.post("/radar/requests", headers=_headers("f2a:operator", "request-key"), json=payload)
    replay = client.post("/radar/requests", headers=_headers("f2a:operator", "request-key"), json=payload)
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    assert _counts(organization_id) == (1, 1, 2, 2, 2)
    conflict = client.post("/radar/requests", headers=_headers("f2a:operator", "request-key"), json={**payload, "classification": "soporte"})
    assert conflict.status_code == 409
    assert _counts(organization_id) == (1, 1, 2, 2, 2)
    foreign = client.post("/radar/requests", headers=_headers("f2a:foreign", "foreign-request"), json=payload)
    assert foreign.status_code == 404
    assert _counts(foreign_organization_id) == (0, 0, 0, 0, 0)


def test_f2a_commands_deny_viewers_and_revoked_memberships_before_replay():
    organization_id, _, membership_id = _context()
    merchant_payload = {"trade_name": "Protected merchant", "products": []}
    request_payload = {"merchant": {"trade_name": "Protected request merchant", "products": []}, "free_text": "protected", "classification": "soporte"}
    assert client.post("/radar/merchants", headers=_headers("f2a:viewer", "viewer-merchant"), json=merchant_payload).status_code == 403
    assert client.post("/radar/requests", headers=_headers("f2a:viewer", "viewer-request"), json=request_payload).status_code == 403
    created = client.post("/radar/merchants", headers=_headers("f2a:operator", "revoked-merchant"), json=merchant_payload)
    assert created.status_code == 201
    created_request = client.post("/radar/requests", headers=_headers("f2a:operator", "revoked-request"), json=request_payload)
    assert created_request.status_code == 201
    with app.state.yarvis.persistence.create_session() as db:
        membership = db.get(PrincipalMembership, membership_id)
        assert membership is not None
        membership.status = "revoked"
        from yarvis_api.clock import utc_now
        membership.revoked_at = utc_now()
        db.commit()
    denied_replay = client.post("/radar/merchants", headers=_headers("f2a:operator", "revoked-merchant"), json=merchant_payload)
    denied_request_replay = client.post("/radar/requests", headers=_headers("f2a:operator", "revoked-request"), json=request_payload)
    assert denied_replay.status_code == 403
    assert denied_request_replay.status_code == 403
    assert _counts(organization_id) == (2, 1, 2, 3, 2)


def test_same_key_is_separated_by_command_type():
    organization_id, _, _ = _context()
    merchant = client.post("/radar/merchants", headers=_headers("f2a:operator", "shared-command-key"), json={"trade_name": "Shared key", "products": []})
    assert merchant.status_code == 201
    request = client.post("/radar/requests", headers=_headers("f2a:operator", "shared-command-key"), json={"merchant_id": merchant.json()["id"], "free_text": "same key, other command", "classification": "soporte"})
    assert request.status_code == 201
    assert _counts(organization_id) == (1, 1, 2, 2, 2)


def test_f2a_rollback_leaves_no_effects_and_retry_succeeds(monkeypatch):
    organization_id, _, _ = _context()
    payload = {"merchant": {"trade_name": "Atomic", "products": ["ecommerce"]}, "free_text": "atomic request", "classification": "alta_ecommerce"}
    original = radar_routes.record_event

    def fail_event(*args, **kwargs):
        raise RuntimeError("controlled derived-effect failure")

    monkeypatch.setattr(radar_routes, "record_event", fail_event)
    with pytest.raises(RuntimeError, match="controlled derived-effect failure"):
        client.post("/radar/requests", headers=_headers("f2a:operator", "atomic-key"), json=payload)
    assert _counts(organization_id) == (0, 0, 0, 0, 0)
    monkeypatch.setattr(radar_routes, "record_event", original)
    retried = client.post("/radar/requests", headers=_headers("f2a:operator", "atomic-key"), json=payload)
    assert retried.status_code == 201
    assert _counts(organization_id) == (1, 1, 1, 2, 1)
    with app.state.yarvis.persistence.create_session() as db:
        receipt = db.scalar(select(RadarCommandReceipt).where(RadarCommandReceipt.organization_id == organization_id))
        event = db.scalar(select(DomainEvent).where(DomainEvent.organization_id == organization_id))
        assert receipt is not None and event is not None
        assert receipt.correlation_id == event.correlation_id
        assert receipt.command_id == event.causation_id
        assert event.payload["command_id"] == str(receipt.command_id)


def test_create_merchant_rollback_leaves_no_effects_and_retry_succeeds(monkeypatch):
    organization_id, _, _ = _context()
    payload = {"trade_name": "Atomic merchant", "products": ["tpv"]}
    original = radar_routes.record_event

    def fail_event(*args, **kwargs):
        raise RuntimeError("controlled merchant event failure")

    monkeypatch.setattr(radar_routes, "record_event", fail_event)
    with pytest.raises(RuntimeError, match="controlled merchant event failure"):
        client.post("/radar/merchants", headers=_headers("f2a:operator", "atomic-merchant-key"), json=payload)
    assert _counts(organization_id) == (0, 0, 0, 0, 0)
    monkeypatch.setattr(radar_routes, "record_event", original)
    retried = client.post("/radar/merchants", headers=_headers("f2a:operator", "atomic-merchant-key"), json=payload)
    assert retried.status_code == 201
    assert _counts(organization_id) == (1, 0, 1, 1, 1)

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from yarvis_api.application.authority import IdentityAuthorityEnvelope
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal
from yarvis_api.models.radar import RadarCommandReceipt, RadarMerchant
from yarvis_api.services.radar_command_receipts import (
    CommandResultReference,
    RadarCommandReceiptService,
    request_fingerprint,
)


def _setup(session, *, subject: str, organization: Organization | None = None, correlation_id: str | None = None):
    organization = organization or Organization(legal_name=f"{subject} org", display_name=f"{subject} org", status="active")
    principal = Principal(external_subject=subject, status="active")
    session.add_all((organization, principal))
    session.flush()
    return IdentityAuthorityEnvelope(
        principal.id,
        organization.id,
        frozenset({"radar.request.create"}),
        "local-test",
        correlation_id or str(uuid4()),
    )


def _create_marker(session, envelope, *, value: str, status_code: int = 201):
    def mutation(context):
        assert context.envelope == envelope
        marker = RadarMerchant(
            workspace_id="f1-infrastructure-test",
            organization_id=envelope.organization_id,
            trade_name=value,
            products=[],
        )
        session.add(marker)
        session.flush()
        return CommandResultReference("radar_merchant", marker.id, status_code)

    return mutation


def test_first_execution_replay_conflict_and_safe_durable_reference():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        envelope = _setup(session, subject="local:f1-primary")
        service = RadarCommandReceiptService()
        first = service.execute(
            session,
            resolve_authority=lambda: envelope,
            command_type="radar.request.create",
            contract_version="1.0.0",
            idempotency_key="f1-key",
            functional_payload={"classification": "alta_tpv", "authority": "forged", "organization_id": str(uuid4())},
            mutation=_create_marker(session, envelope, value="first"),
        )
        session.commit()
        replay = service.execute(
            session,
            resolve_authority=lambda: envelope,
            command_type="radar.request.create",
            contract_version="1.0.0",
            idempotency_key="f1-key",
            functional_payload={"organization_id": str(uuid4()), "authority": "different-forgery", "classification": "alta_tpv"},
            mutation=lambda _: pytest.fail("equal replay must not invoke mutation"),
        )
        assert not first.replayed and replay.replayed
        assert replay.command_id == first.command_id
        assert replay.correlation_id == first.correlation_id
        assert len(session.scalars(select(RadarMerchant).where(RadarMerchant.organization_id == envelope.organization_id)).all()) == 1
        receipt = session.scalar(select(RadarCommandReceipt).where(RadarCommandReceipt.command_id == first.command_id))
        assert receipt is not None and receipt.status == "succeeded"
        assert receipt.result_resource_type == "radar_merchant"
        assert not hasattr(receipt, "payload")
        with pytest.raises(ApplicationError) as conflict:
            service.execute(
                session,
                resolve_authority=lambda: envelope,
                command_type="radar.request.create",
                contract_version="1.0.0",
                idempotency_key="f1-key",
                functional_payload={"classification": "alta_ecommerce"},
                mutation=_create_marker(session, envelope, value="conflict"),
            )
        assert conflict.value.code == ApplicationErrorCode.CONFLICT
        assert len(session.scalars(select(RadarMerchant).where(RadarMerchant.organization_id == envelope.organization_id)).all()) == 1


def test_scope_fingerprint_correlation_and_revocation_gate():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        first = _setup(session, subject="local:f1-one", correlation_id="not-a-uuid")
        second = _setup(session, subject="local:f1-two")
        service = RadarCommandReceiptService()
        primary = service.execute(
            session,
            resolve_authority=lambda: first,
            command_type="radar.request.create",
            contract_version="1.0.0",
            idempotency_key="shared-key",
            functional_payload={"b": 2, "a": {"d": 4, "c": 3}},
            mutation=_create_marker(session, first, value="one"),
        )
        other_command = service.execute(
            session,
            resolve_authority=lambda: first,
            command_type="radar.request.close",
            contract_version="1.0.0",
            idempotency_key="shared-key",
            functional_payload={"a": {"c": 3, "d": 4}, "b": 2},
            mutation=_create_marker(session, first, value="different-command"),
        )
        other_organization = service.execute(
            session,
            resolve_authority=lambda: second,
            command_type="radar.request.create",
            contract_version="1.0.0",
            idempotency_key="shared-key",
            functional_payload={"a": {"c": 3, "d": 4}, "b": 2},
            mutation=_create_marker(session, second, value="other-org"),
        )
        session.commit()
        assert primary.command_id != other_command.command_id != other_organization.command_id
        assert isinstance(primary.correlation_id, UUID)
        assert request_fingerprint(
            command_type="radar.request.create", contract_version="1.0.0", target_id=None, functional_payload={"a": 1, "b": 2}
        ) == request_fingerprint(
            command_type="radar.request.create", contract_version="1.0.0", target_id=None, functional_payload={"b": 2, "a": 1}
        )
        assert request_fingerprint(
            command_type="radar.request.create", contract_version="1.0.0", target_id=None, functional_payload={"a": 1}
        ) != request_fingerprint(
            command_type="radar.request.create", contract_version="1.0.0", target_id=None, functional_payload={"a": 2}
        )
        denied = object()
        with pytest.raises(ApplicationError) as blocked:
            service.execute(
                session,
                resolve_authority=lambda: (_ for _ in ()).throw(ApplicationError(ApplicationErrorCode.AUTHORIZATION_DENIED, "revoked", {"reason": "revoked"})),
                command_type="radar.request.create",
                contract_version="1.0.0",
                idempotency_key="shared-key",
                functional_payload={"a": 1},
                mutation=lambda _: denied,
            )
        assert blocked.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_failed_mutation_rolls_back_receipt_and_effects_and_unique_constraint_is_real():
    from yarvis_api.main import app

    with app.state.yarvis.persistence.create_session() as session:
        envelope = _setup(session, subject="local:f1-rollback")
        service = RadarCommandReceiptService()

        def failing_mutation(_):
            session.add(
                RadarMerchant(
                    workspace_id="f1-infrastructure-test",
                    organization_id=envelope.organization_id,
                    trade_name="rolled back",
                    products=[],
                )
            )
            session.flush()
            raise RuntimeError("controlled failure")

        with pytest.raises(RuntimeError):
            service.execute(
                session,
                resolve_authority=lambda: envelope,
                command_type="radar.request.create",
                contract_version="1.0.0",
                idempotency_key="rollback-key",
                functional_payload={"classification": "alta_tpv"},
                mutation=failing_mutation,
            )
        session.commit()
        assert not session.scalars(select(RadarCommandReceipt)).all()
        assert not session.scalars(select(RadarMerchant).where(RadarMerchant.organization_id == envelope.organization_id)).all()
        receipt = RadarCommandReceipt(
            command_id=uuid4(), organization_id=envelope.organization_id, command_type="radar.request.create",
            contract_version="1.0.0", idempotency_key="duplicate-key", request_fingerprint="0" * 64,
            actor_principal_id=envelope.principal_id, correlation_id=uuid4(), result_status_code=201,
            result_resource_type="radar_merchant", result_resource_id=uuid4(), status="succeeded",
        )
        duplicate = RadarCommandReceipt(
            command_id=uuid4(), organization_id=envelope.organization_id, command_type="radar.request.create",
            contract_version="1.0.0", idempotency_key="duplicate-key", request_fingerprint="1" * 64,
            actor_principal_id=envelope.principal_id, correlation_id=uuid4(), result_status_code=201,
            result_resource_type="radar_merchant", result_resource_id=uuid4(), status="succeeded",
        )
        session.add_all((receipt, duplicate))
        with pytest.raises(IntegrityError):
            session.commit()

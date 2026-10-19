from datetime import datetime, timezone
from uuid import uuid4

from yarvis_api.models.netpay_gmail_intake import NetpayGmailSourceItem, NetpayIntakeCandidate
from yarvis_api.services.netpay_gmail_classification import (
    extract_candidate,
    readable_message_text,
    reprocess_unreviewed_candidate_from_source,
)


def _source(subject: str, plain_excerpt: str, provider_received_at: datetime) -> NetpayGmailSourceItem:
    return NetpayGmailSourceItem(
        id=uuid4(),
        organization_id=uuid4(),
        connection_id=uuid4(),
        provider_account_id="synthetic@example.invalid",
        gmail_message_id="synthetic-message",
        gmail_thread_id="synthetic-thread",
        subject=subject,
        plain_excerpt=plain_excerpt,
        provider_received_at=provider_received_at,
        source_fingerprint="synthetic-fingerprint",
        attachment_metadata=[],
        provenance={"provider": "fake"},
    )


def test_ecommerce_rejection_review_is_support_with_attributed_observations() -> None:
    repeated = (
        "Hola, ¿me ayudan con una revisión de los rechazos de este ecommerce? "
        "Decision Manager concentra el 36% de los rechazos. "
        "Se reportan 297 Order IDs y 230 de ellos no se recuperaron."
    )
    source = _source(
        subject="Solicitud de revisión de rechazos de Ecommerce Rock N' Wok ID 1272162",
        plain_excerpt=f"{repeated} {repeated}",
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    result = extract_candidate(source)

    assert result.request_type == "support_or_incident"
    assert result.product == "ecommerce"
    assert result.priority == "normal"
    assert result.ticket_references == []
    assert result.correlation_key is None
    assert {item["kind"] for item in result.commerce_hints} == {"unverified_name", "unverified_identifier"}
    assert any(item["field"] == "commerce_name" and item["value"] == "Rock N' Wok" for item in result.facts)
    identifier = next(item for item in result.facts if item["field"] == "external_identifier")
    assert identifier == {
        "field": "external_identifier",
        "value": "1272162",
        "source": "message_subject",
        "identifier_type": "unspecified",
        "verification": "unverified",
    }
    assert any(item["field"] == "requested_action" for item in result.facts)
    assert all(
        item.get("attribution") == "reported_by_message" for item in result.facts if item["field"] == "reported_claim"
    )
    assert "canalizar la revisión de rechazos" in result.next_action
    assert readable_message_text(source.plain_excerpt) == repeated


def test_ecommerce_activation_still_requires_activation_language() -> None:
    source = _source(
        subject="Alta de ecommerce para comercio existente",
        plain_excerpt="Solicito activar el canal ecommerce.",
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    assert extract_candidate(source).request_type == "ecommerce_activation"


def test_new_branches_extracts_generic_repeated_merchant_and_each_branch() -> None:
    source = _source(
        subject="Solicitud para sucursales nuevas",
        plain_excerpt=(
            "Solicito terminal y alta en Ecommerce para la nueva sucursal: "
            "Marca Demo Centro Marca Demo Norte Marca Demo Aeropuerto. "
            "Adjunto información para el proceso."
        ),
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    result = extract_candidate(source)

    assert result.request_type == "new_branch"
    assert result.product == "mixed"
    assert any(
        item["field"] == "commerce_name" and item["value"] == "Marca Demo" for item in result.facts
    )
    assert [item["value"] for item in result.facts if item["field"] == "branch_name"] == [
        "Marca Demo Centro",
        "Marca Demo Norte",
        "Marca Demo Aeropuerto",
    ]
    assert any(
        item["field"] == "requested_action"
        and item["value"] == "new_branch_onboarding"
        and item["attribution"] == "reported_by_message"
        for item in result.facts
    )
    assert result.commerce_hints == [{"kind": "unverified_name", "value": "Marca Demo"}]


def test_reply_for_five_branch_onboardings_remains_new_branch() -> None:
    source = _source(
        subject="RE: Solicitud de alta - 5 sucursales",
        plain_excerpt=(
            "Solicito el alta de 5 sucursales: Información para las tiendas. "
            "Marca Demo Centro Dirección. Calle sintética 1. "
            "Marca Demo Norte Dirección. Calle sintética 2. "
            "Marca Demo Sur Dirección. Calle sintética 3. "
            "Marca Demo Oriente Dirección. Calle sintética 4. "
            "Marca Demo Poniente Dirección. Calle sintética 5."
        ),
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    result = extract_candidate(source)
    assert result.request_type == "new_branch"
    assert [item["value"] for item in result.facts if item["field"] == "branch_name"] == [
        "Marca Demo Centro",
        "Marca Demo Norte",
        "Marca Demo Sur",
        "Marca Demo Oriente",
        "Marca Demo Poniente",
    ]


def test_support_message_with_ecommerce_does_not_become_activation() -> None:
    source = _source(
        subject="Soporte ecommerce por rechazos",
        plain_excerpt="Solicito revisión de rechazos en Decision Manager; no es un alta nueva.",
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    assert extract_candidate(source).request_type == "support_or_incident"


def test_local_reprocessing_preserves_source_identity_and_rejects_human_decisions() -> None:
    source = _source(
        subject="Solicitud de revisión de rechazos de Ecommerce Rock N' Wok ID 1272162",
        plain_excerpt="Solicito revisión de rechazos de Decision Manager.",
        provider_received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    candidate = NetpayIntakeCandidate(
        organization_id=source.organization_id,
        source_item_id=source.id,
        connection_id=source.connection_id,
        source_fingerprint=source.source_fingerprint,
        received_at=source.provider_received_at,
        immutable=False,
        reviewed_at=None,
        reviewed_by_principal_id=None,
        owner_type=None,
        owner_id=None,
        state="pending_link",
    )

    reprocess_unreviewed_candidate_from_source(candidate, source)

    assert candidate.source_item_id == source.id
    assert candidate.source_fingerprint == source.source_fingerprint
    assert candidate.request_type == "support_or_incident"
    assert candidate.extraction_version == "d2-rules-v2"
    assert "local_source_reprocessed_after_rule_fix" in candidate.extraction_reasons

    candidate.reviewed_at = datetime.now(timezone.utc)
    try:
        reprocess_unreviewed_candidate_from_source(candidate, source)
    except ValueError as error:
        assert str(error) == "candidate_human_decision_present"
    else:
        raise AssertionError("reviewed candidates must not be reprocessed")

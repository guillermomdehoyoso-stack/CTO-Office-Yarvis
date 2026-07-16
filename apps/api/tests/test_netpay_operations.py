from datetime import datetime, timezone

from fastapi.testclient import TestClient

from yarvis_api.main import app

client = TestClient(app)


def sample_email_payload(message_id: str = "gmail-message-1", body_extra: str = ""):
    return {
        "gmail_message_id": message_id,
        "gmail_thread_id": "gmail-thread-1",
        "from_address": "operaciones@netpay.mx",
        "to_addresses": ["inbox.netpay@cto.local"],
        "cc_addresses": ["ops.team@cto.local"],
        "reply_to_addresses": ["responder@netpay.mx"],
        "delivered_to": "netpay.ops@cto.local",
        "x_original_to": "netpay.alias@cto.local",
        "original_recipient": "rfc822;netpay.original@cto.local",
        "subject": "Folio NP-2026-001 Guia 999988887777 envio",
        "body": "Folio NetPay: NP-2026-001\nGuia: 999988887777\nStore ID: STO-100\nSerie TPV: TPV-ABC-01\nCliente: Cliente Demo\nComercio: Comercio Demo\nSucursal: Centro\nDestinatario: Juan Perez\nDomicilio: Calle Uno 123\nCiudad: Monterrey\nEstado: Nuevo Leon\nCP: 64000\nTelefono: 8181818181\n" + body_extra,
        "attachments_metadata": [
            {"filename": "guia.pdf", "mime_type": "application/pdf", "size_bytes": 1024, "storage_reference": "local://guides/guia.pdf"}
        ],
        "sent_at": datetime(2026, 7, 10, tzinfo=timezone.utc).isoformat(),
        "received_at": datetime(2026, 7, 11, tzinfo=timezone.utc).isoformat(),
    }


def test_import_email_detects_folio_tracking_and_provenance():
    response = client.post("/netpay/import-email", json=sample_email_payload())
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["created"] is True
    assert payload["service_case"]["folio"] == "NP-2026-001"
    assert payload["shipments"][0]["tracking_number"] == "999988887777"
    assert payload["service_case"]["extracted_fields"]["customer"]["value"] == "CLIENTE DEMO"
    assert payload["service_case"]["extracted_fields"]["customer"]["confirmation_status"] == "candidate"
    assert payload["service_case"]["attachments_metadata"][0]["filename"] == "guia.pdf"


def test_operational_recipient_uses_delivered_to_priority():
    response = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-recipient"))
    assert response.status_code == 201
    case_data = response.json()["service_case"]
    assert case_data["operational_recipient"] == "netpay.ops@cto.local"
    assert case_data["recipient_resolution_source"] == "delivered_to"


def test_idempotency_by_message_id_and_folio():
    first = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-dup"))
    assert first.status_code == 201

    duplicate_message = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-dup"))
    assert duplicate_message.status_code == 201
    assert duplicate_message.json()["created"] is False
    assert duplicate_message.json()["duplicate_by"] == "message_id"

    duplicate_folio = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-other"))
    assert duplicate_folio.status_code == 201
    assert duplicate_folio.json()["created"] is False
    assert duplicate_folio.json()["duplicate_by"] == "folio"


def test_patch_investigation_confirms_case_and_assigns_device():
    imported = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-confirm")).json()
    case_id = imported["service_case"]["id"]

    response = client.patch(
        f"/netpay/investigation/{case_id}",
        json={
            "case_type": "installation",
            "customer_name": "Cliente Demo",
            "merchant_name": "Comercio Demo",
            "address": "Calle Uno 123",
            "store_id": "STO-100",
            "device_serial": "TPV-ABC-01",
            "movement_type": "outbound",
            "notes": "confirmado por operador",
            "investigation_status": "confirmed",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["investigation_status"] == "confirmed"

    devices = client.get("/netpay/devices")
    assert devices.status_code == 200
    assert any(item["device_serial"] == "TPV-ABC-01" for item in devices.json())


def test_register_shipment_and_timeline():
    imported = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-ship")).json()
    case_id = imported["service_case"]["id"]

    shipment = client.post(
        f"/netpay/shipment/{case_id}",
        json={"tracking_number": "TRK-001", "carrier": "DHL", "direction": "outbound", "status": "registered"},
    )
    assert shipment.status_code == 201

    timeline = client.get(f"/netpay/timeline/{case_id}")
    assert timeline.status_code == 200
    event_types = [item["event_type"] for item in timeline.json()]
    assert "netpay.case_detected" in event_types
    assert "netpay.shipment_registered" in event_types


def test_import_document_ocr_fallback_and_idempotency():
    imported = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-doc")).json()
    case_id = imported["service_case"]["id"]

    first = client.post(
        "/netpay/import-document",
        json={
            "service_case_id": case_id,
            "filename": "ticket.png",
            "mime_type": "image/png",
            "storage_reference": "local://docs/ticket.png",
            "extracted_text": "",
            "enable_ocr": True,
        },
    )
    assert first.status_code == 201, first.text
    assert first.json()["created"] is True
    assert first.json()["document_summary"]["extraction_method"] in {"ocr_unavailable", "ocr_attempted"}

    second = client.post(
        "/netpay/import-document",
        json={
            "service_case_id": case_id,
            "filename": "ticket.png",
            "mime_type": "image/png",
            "storage_reference": "local://docs/ticket.png",
            "extracted_text": "",
            "enable_ocr": True,
        },
    )
    assert second.status_code == 201
    assert second.json()["created"] is False
    assert second.json()["duplicate_by"] == "document_fingerprint"


def test_multiple_recipients_are_preserved():
    payload = sample_email_payload("gmail-message-multi")
    payload["to_addresses"] = ["a@cto.local", "b@cto.local"]
    payload["cc_addresses"] = ["c@cto.local", "d@cto.local"]
    response = client.post("/netpay/import-email", json=payload)
    assert response.status_code == 201
    service_case = response.json()["service_case"]
    assert set(service_case["recipient_addresses"]) >= {"a@cto.local", "b@cto.local", "c@cto.local", "d@cto.local"}


def test_netpay_import_creates_observations_with_provenance():
    response = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-observations"))
    assert response.status_code == 201, response.text
    service_case = response.json()["service_case"]

    observations = client.get("/observations", params={"domain": "netpay", "subject_reference": service_case["folio"]})
    assert observations.status_code == 200
    items = observations.json()
    assert any(item["field_name"] == "folio" for item in items)
    assert any(item["field_name"] == "tracking_number" for item in items)
    assert all("processor" in item["provenance"] for item in items)


def test_netpay_reimport_is_idempotent_for_observations():
    first = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-idempotent-obs"))
    assert first.status_code == 201
    folio = first.json()["service_case"]["folio"]

    before = client.get("/observations", params={"domain": "netpay", "subject_reference": folio})
    assert before.status_code == 200
    before_count = len(before.json())

    second = client.post("/netpay/import-email", json=sample_email_payload("gmail-message-idempotent-obs"))
    assert second.status_code == 201
    assert second.json()["created"] is False

    after = client.get("/observations", params={"domain": "netpay", "subject_reference": folio})
    assert after.status_code == 200
    assert len(after.json()) == before_count

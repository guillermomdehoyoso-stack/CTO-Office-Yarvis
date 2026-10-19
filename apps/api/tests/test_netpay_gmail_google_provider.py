import base64
import json
from datetime import datetime, timedelta, timezone

from yarvis_api.services import netpay_gmail_google_provider as provider_module
from yarvis_api.services.netpay_gmail_google_provider import GoogleGmailProvider
from yarvis_api.services.netpay_gmail_secret_store import InMemoryGmailSecretStore


class _Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class _Messages:
    def __init__(self):
        self.fetched: list[str] = []

    def list(self, **_kwargs):
        return _Request({"messages": [{"id": "allowed-1"}, {"id": "blocked-1"}]})

    def get(self, *, id: str, **_kwargs):
        self.fetched.append(id)
        return _Request(
            {
                "id": id,
                "threadId": "thread-1",
                "historyId": "history-2",
                "internalDate": "1760000000000",
                "labelIds": ["Label_1"],
                "payload": {
                    "headers": [
                        {"name": "From", "value": "synthetic.sender@example.invalid"},
                        {"name": "Subject", "value": "Caso sintético 00199130"},
                    ],
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": base64.urlsafe_b64encode(b"synthetic body").decode()},
                        },
                        {
                            "filename": "synthetic.pdf",
                            "mimeType": "application/pdf",
                            "body": {"attachmentId": "never-fetched", "size": 123},
                        },
                    ],
                },
            }
        )


class _Users:
    def __init__(self):
        self.message_resource = _Messages()

    def getProfile(self, **_kwargs):
        return _Request({"emailAddress": "pilot@example.invalid"})

    def labels(self):
        return self

    def get(self, **_kwargs):
        return _Request({"id": "Label_1"})

    def messages(self):
        return self.message_resource


class _Service:
    def __init__(self):
        self.user_resource = _Users()

    def users(self):
        return self.user_resource


class _Credentials:
    def to_json(self) -> str:
        return json.dumps({"token": "synthetic-token"})


def test_google_provider_fetches_only_manifest_content_and_never_attachment_bytes(monkeypatch) -> None:
    store = InMemoryGmailSecretStore()
    reference = store.put(
        "credentials/synthetic",
        {"pilot_manifest_message_ids": ["allowed-1", *[f"not-listed-{index}" for index in range(2, 11)]]},
    )
    service = _Service()
    monkeypatch.setattr(provider_module, "build", lambda *_args, **_kwargs: service)
    provider = GoogleGmailProvider(store)
    monkeypatch.setattr(provider, "_credentials", lambda _reference: _Credentials())

    messages = provider.list_messages(
        provider_account_id="pilot@example.invalid",
        label_id="Label_1",
        query="",
        credential_secret_ref=reference,
        window_start=datetime.now(timezone.utc) - timedelta(days=30),
        window_end=datetime.now(timezone.utc),
    )

    assert service.user_resource.message_resource.fetched == ["allowed-1"]
    assert len(messages) == 1
    assert messages[0].message_id == "allowed-1"
    assert messages[0].body == "synthetic body"
    assert messages[0].attachments == ({"name": "synthetic.pdf", "mime_type": "application/pdf", "size": 123},)


def test_google_provider_fails_closed_without_an_exact_ten_message_manifest(monkeypatch) -> None:
    store = InMemoryGmailSecretStore()
    reference = store.put("credentials/synthetic", {"pilot_manifest_message_ids": ["allowed-1"]})
    service = _Service()
    monkeypatch.setattr(provider_module, "build", lambda *_args, **_kwargs: service)
    provider = GoogleGmailProvider(store)
    monkeypatch.setattr(provider, "_credentials", lambda _reference: _Credentials())

    try:
        provider.list_messages(
            provider_account_id="pilot@example.invalid",
            label_id="Label_1",
            query="",
            credential_secret_ref=reference,
            window_start=datetime.now(timezone.utc) - timedelta(days=30),
            window_end=datetime.now(timezone.utc),
        )
    except provider_module.GmailProviderError as error:
        assert error.code == "pilot_manifest_invalid"
    else:
        raise AssertionError("an invalid pilot manifest must fail closed")

    assert service.user_resource.message_resource.fetched == []


def test_mime_alternative_prefers_plain_text_and_keeps_attachment_metadata_only() -> None:
    plain = base64.urlsafe_b64encode(b"Readable plain message").decode()
    html = base64.urlsafe_b64encode(b"<p>Readable plain message</p>").decode()
    body, attachments = GoogleGmailProvider._content(
        {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": plain}},
                {"mimeType": "text/html", "body": {"data": html}},
                {
                    "filename": "report.xlsx",
                    "mimeType": "application/vnd.ms-excel",
                    "body": {"attachmentId": "not-read", "size": 42},
                },
            ],
        }
    )

    assert body == "Readable plain message"
    assert attachments == ({"name": "report.xlsx", "mime_type": "application/vnd.ms-excel", "size": 42},)


def test_mime_single_representation_supports_plain_or_html() -> None:
    plain = base64.urlsafe_b64encode(b"Plain only").decode()
    html = base64.urlsafe_b64encode(b"<p>HTML only</p>").decode()

    plain_body, _ = GoogleGmailProvider._content({"mimeType": "text/plain", "body": {"data": plain}})
    html_body, _ = GoogleGmailProvider._content({"mimeType": "text/html", "body": {"data": html}})

    assert plain_body == "Plain only"
    assert html_body == "<p>HTML only</p>"

"""Official Gmail API adapter for the ratified restricted local pilot."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from yarvis_api.services.netpay_gmail_provider import GmailMessageMetadata, GmailProviderError, GmailSourceMessage
from yarvis_api.services.netpay_gmail_secret_store import GmailSecretStore, GmailSecretStoreError

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


@dataclass(frozen=True, slots=True)
class GoogleOAuthResult:
    token_payload: dict[str, object]
    email_address: str
    history_id: str
    label_id: str


class GoogleGmailOAuthCoordinator:
    def __init__(
        self,
        *,
        client_id_file: Path,
        client_secret_file: Path,
        redirect_uri: str,
        label_name: str,
    ) -> None:
        self.client_id_file = client_id_file
        self.client_secret_file = client_secret_file
        self.redirect_uri = redirect_uri
        self.label_name = label_name

    def _flow(self, *, state: str | None = None, code_verifier: str | None = None) -> Flow:
        try:
            client_id = self.client_id_file.read_text(encoding="utf-8").strip()
            client_secret = self.client_secret_file.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise GmailProviderError("oauth_client_unavailable") from error
        if not client_id or not client_secret:
            raise GmailProviderError("oauth_client_invalid")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[GMAIL_READONLY_SCOPE],
            state=state,
        )
        flow.redirect_uri = self.redirect_uri
        flow.code_verifier = code_verifier
        return flow

    def authorization_url(self, *, state: str, code_verifier: str) -> str:
        flow = self._flow(state=state, code_verifier=code_verifier)
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="false",
            prompt="consent",
            code_challenge_method="S256",
        )
        return str(url)

    def exchange(self, *, state: str, code: str, code_verifier: str) -> GoogleOAuthResult:
        flow = self._flow(state=state, code_verifier=code_verifier)
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
            profile = service.users().getProfile(userId="me").execute()
            labels = service.users().labels().list(userId="me").execute().get("labels", [])
        except (HttpError, OSError, ValueError) as error:
            raise GmailProviderError("oauth_exchange_failed") from error
        label = next((item for item in labels if item.get("name") == self.label_name), None)
        if label is None or not label.get("id"):
            raise GmailProviderError("label_not_found")
        payload = json.loads(credentials.to_json())
        payload["scopes"] = [GMAIL_READONLY_SCOPE]
        return GoogleOAuthResult(
            token_payload=payload,
            email_address=str(profile.get("emailAddress", "")),
            history_id=str(profile.get("historyId", "")),
            label_id=str(label["id"]),
        )


class GoogleGmailProvider:
    provider_kind = "google"

    def __init__(self, secret_store: GmailSecretStore) -> None:
        self.secret_store = secret_store

    def _credentials(self, reference: str | None) -> Credentials:
        if not reference:
            raise GmailProviderError("credential_state_invalid")
        try:
            payload = self.secret_store.get(reference)
            credentials = Credentials.from_authorized_user_info(payload, scopes=[GMAIL_READONLY_SCOPE])
        except (GmailSecretStoreError, ValueError, TypeError) as error:
            raise GmailProviderError("credential_state_invalid") from error
        if credentials.expired and not credentials.refresh_token:
            raise GmailProviderError("credential_state_invalid")
        return credentials

    def validate_binding(
        self, *, provider_account_id: str, label_id: str, credential_secret_ref: str | None = None
    ) -> None:
        credentials = self._credentials(credential_secret_ref)
        try:
            service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
            profile = service.users().getProfile(userId="me").execute()
            if str(profile.get("emailAddress", "")).casefold() != provider_account_id.casefold():
                raise GmailProviderError("mailbox_mismatch")
            label = service.users().labels().get(userId="me", id=label_id).execute()
            if str(label.get("id", "")) != label_id:
                raise GmailProviderError("label_mismatch")
        except GmailProviderError:
            raise
        except HttpError as error:
            raise GmailProviderError("gmail_provider_unavailable") from error

    def discover_message_metadata(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None,
        window_start: datetime,
        window_end: datetime,
        limit: int,
    ) -> list[GmailMessageMetadata]:
        credentials = self._credentials(credential_secret_ref)
        try:
            service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
            profile = service.users().getProfile(userId="me").execute()
            if str(profile.get("emailAddress", "")).casefold() != provider_account_id.casefold():
                raise GmailProviderError("mailbox_mismatch")
            bounded_query = (
                f"{query.strip()} after:{int(window_start.timestamp())} before:{int(window_end.timestamp()) + 1}"
            ).strip()
            response = (
                service.users()
                .messages()
                .list(userId="me", labelIds=[label_id], q=bounded_query, maxResults=min(limit, 10))
                .execute()
            )
            result: list[GmailMessageMetadata] = []
            for item in response.get("messages", []):
                metadata = (
                    service.users()
                    .messages()
                    .get(userId="me", id=item["id"], format="metadata", metadataHeaders=[])
                    .execute()
                )
                received = datetime.fromtimestamp(int(metadata.get("internalDate", "0")) / 1000, tz=timezone.utc)
                result.append(GmailMessageMetadata(str(item["id"]), received))
            return result
        except GmailProviderError:
            raise
        except HttpError as error:
            raise GmailProviderError("gmail_provider_unavailable") from error

    @staticmethod
    def _decode(data: str | None) -> str:
        if not data:
            return ""
        try:
            return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
        except (ValueError, UnicodeError):
            return ""

    @classmethod
    def _content(cls, payload: dict[str, Any]) -> tuple[str, tuple[dict[str, str | int], ...]]:
        plain_texts: list[str] = []
        html_texts: list[str] = []
        attachments: list[dict[str, str | int]] = []

        def visit(part: dict[str, Any]) -> None:
            filename = str(part.get("filename", ""))
            mime = str(part.get("mimeType", "application/octet-stream"))
            body = part.get("body") or {}
            if filename:
                attachments.append({"name": filename, "mime_type": mime, "size": int(body.get("size", 0) or 0)})
            elif mime == "text/plain" and body.get("data"):
                plain_texts.append(cls._decode(str(body["data"])))
            elif mime == "text/html" and body.get("data"):
                html_texts.append(cls._decode(str(body["data"])))
            for child in part.get("parts") or []:
                visit(child)

        visit(payload)
        return "\n".join(plain_texts or html_texts), tuple(attachments)

    @classmethod
    def _message(cls, item: dict[str, Any], label_id: str) -> GmailSourceMessage:
        headers = {
            str(header.get("name", "")).lower(): str(header.get("value", ""))
            for header in item.get("payload", {}).get("headers", [])
        }
        body, attachments = cls._content(item.get("payload") or {})
        received_at = datetime.fromtimestamp(int(item.get("internalDate", "0")) / 1000, tz=timezone.utc)
        return GmailSourceMessage(
            message_id=str(item.get("id", "")),
            thread_id=str(item.get("threadId", "")),
            received_at=received_at,
            sender=headers.get("from"),
            recipient=headers.get("to"),
            subject=headers.get("subject"),
            body=body,
            label_ids=frozenset(str(value) for value in item.get("labelIds", []) if value),
            attachments=attachments,
            provider_cursor=str(item.get("historyId", "")) or None,
        )

    def list_messages(
        self,
        *,
        provider_account_id: str,
        label_id: str,
        query: str,
        credential_secret_ref: str | None = None,
        cursor: str | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> list[GmailSourceMessage]:
        credentials = self._credentials(credential_secret_ref)
        try:
            service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
            profile = service.users().getProfile(userId="me").execute()
            if str(profile.get("emailAddress", "")).casefold() != provider_account_id.casefold():
                raise GmailProviderError("mailbox_mismatch")
            label = service.users().labels().get(userId="me", id=label_id).execute()
            if str(label.get("id", "")) != label_id:
                raise GmailProviderError("label_mismatch")
            message_ids: list[str] = []
            if cursor:
                page_token: str | None = None
                while True:
                    response = (
                        service.users()
                        .history()
                        .list(
                            userId="me",
                            startHistoryId=cursor,
                            labelId=label_id,
                            historyTypes=["messageAdded"],
                            pageToken=page_token,
                        )
                        .execute()
                    )
                    for history in response.get("history", []):
                        for added in history.get("messagesAdded", []):
                            message = added.get("message") or {}
                            if message.get("id"):
                                message_ids.append(str(message["id"]))
                    page_token = response.get("nextPageToken")
                    if not page_token:
                        break
            else:
                bounded_query = query.strip()
                if window_start is not None:
                    bounded_query = f"{bounded_query} after:{int(window_start.timestamp())}".strip()
                if window_end is not None:
                    bounded_query = f"{bounded_query} before:{int(window_end.timestamp()) + 1}".strip()
                page_token = None
                while True:
                    response = (
                        service.users()
                        .messages()
                        .list(userId="me", labelIds=[label_id], q=bounded_query, maxResults=100, pageToken=page_token)
                        .execute()
                    )
                    message_ids.extend(str(item["id"]) for item in response.get("messages", []) if item.get("id"))
                    page_token = response.get("nextPageToken")
                    if not page_token:
                        break
            stored: dict[str, object] = {}
            if credential_secret_ref:
                stored = self.secret_store.get(credential_secret_ref)
                manifest_ids = stored.get("pilot_manifest_message_ids")
                if not isinstance(manifest_ids, list):
                    raise GmailProviderError("pilot_manifest_invalid")
                allowed = {str(value) for value in manifest_ids if value}
                if len(manifest_ids) != 10 or len(allowed) != 10:
                    raise GmailProviderError("pilot_manifest_invalid")
                message_ids = [message_id for message_id in message_ids if message_id in allowed]
            messages = [
                self._message(
                    service.users().messages().get(userId="me", id=message_id, format="full").execute(),
                    label_id,
                )
                for message_id in dict.fromkeys(message_ids)
            ]
            if credential_secret_ref:
                refreshed = json.loads(credentials.to_json())
                refreshed.update(
                    {
                        key: value
                        for key, value in stored.items()
                        if key.startswith("pilot_manifest_") or key == "expected_email"
                    }
                )
                key = credential_secret_ref.split("/netpay-gmail/", 1)[-1]
                self.secret_store.put(key, refreshed)
            return [message for message in messages if label_id in message.label_ids]
        except GmailProviderError:
            raise
        except HttpError as error:
            code = (
                "history_cursor_invalid"
                if getattr(error.resp, "status", None) == 404 and cursor
                else "gmail_provider_unavailable"
            )
            raise GmailProviderError(code) from error
        except (OSError, ValueError, GmailSecretStoreError) as error:
            raise GmailProviderError("gmail_provider_unavailable") from error

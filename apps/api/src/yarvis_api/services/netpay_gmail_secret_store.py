"""Encrypted credential-reference storage for the restricted local Gmail pilot."""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_REF = re.compile(r"^(?:file-aesgcm|memory)://netpay-gmail/([a-zA-Z0-9._/-]{1,180})$")


class GmailSecretStoreError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class GmailSecretStore(Protocol):
    def put(self, key: str, value: dict[str, object]) -> str: ...
    def get(self, reference: str) -> dict[str, object]: ...
    def delete(self, reference: str) -> None: ...


class AesGcmFileSecretStore:
    def __init__(self, *, root: Path, key_file: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            raw = key_file.read_bytes().strip()
        except OSError as error:
            raise GmailSecretStoreError("secret_store_key_unavailable") from error
        try:
            key = base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4))
        except ValueError:
            key = raw
        if len(key) != 32:
            raise GmailSecretStoreError("secret_store_key_invalid")
        self._cipher = AESGCM(key)

    def _path(self, key: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9._/-]{1,180}", key) or ".." in key.split("/"):
            raise GmailSecretStoreError("secret_reference_invalid")
        target = (self.root / f"{key}.enc").resolve()
        if self.root not in target.parents:
            raise GmailSecretStoreError("secret_reference_invalid")
        return target

    def put(self, key: str, value: dict[str, object]) -> str:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        nonce = os.urandom(12)
        plaintext = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload = base64.urlsafe_b64encode(nonce + self._cipher.encrypt(nonce, plaintext, key.encode("utf-8")))
        descriptor, temporary_name = tempfile.mkstemp(prefix=".gmail-", dir=target.parent)
        try:
            os.write(descriptor, payload)
            os.close(descriptor)
            descriptor = -1
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, target)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        return f"file-aesgcm://netpay-gmail/{key}"

    def get(self, reference: str) -> dict[str, object]:
        match = _REF.fullmatch(reference)
        if match is None or not reference.startswith("file-aesgcm://"):
            raise GmailSecretStoreError("secret_reference_invalid")
        key = match.group(1)
        try:
            encrypted = base64.urlsafe_b64decode(self._path(key).read_bytes())
            value = self._cipher.decrypt(encrypted[:12], encrypted[12:], key.encode("utf-8"))
            result = json.loads(value)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise GmailSecretStoreError("secret_unavailable") from error
        if not isinstance(result, dict):
            raise GmailSecretStoreError("secret_payload_invalid")
        return result

    def delete(self, reference: str) -> None:
        match = _REF.fullmatch(reference)
        if match is None or not reference.startswith("file-aesgcm://"):
            raise GmailSecretStoreError("secret_reference_invalid")
        try:
            self._path(match.group(1)).unlink(missing_ok=True)
        except OSError as error:
            raise GmailSecretStoreError("secret_delete_failed") from error


class InMemoryGmailSecretStore:
    """Test-only store with the same opaque-reference behavior."""

    def __init__(self) -> None:
        self.values: dict[str, dict[str, object]] = {}

    def put(self, key: str, value: dict[str, object]) -> str:
        reference = f"memory://netpay-gmail/{key}"
        self.values[reference] = json.loads(json.dumps(value))
        return reference

    def get(self, reference: str) -> dict[str, object]:
        if reference not in self.values:
            raise GmailSecretStoreError("secret_unavailable")
        return json.loads(json.dumps(self.values[reference]))

    def delete(self, reference: str) -> None:
        self.values.pop(reference, None)


DEFAULT_MEMORY_GMAIL_SECRET_STORE = InMemoryGmailSecretStore()

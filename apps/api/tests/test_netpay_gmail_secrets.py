import base64
from pathlib import Path

import pytest

from yarvis_api.services.netpay_gmail_secret_store import (
    AesGcmFileSecretStore,
    GmailSecretStoreError,
)


def test_aes_secret_store_keeps_tokens_out_of_plaintext(tmp_path: Path) -> None:
    key_file = tmp_path / "gmail.key"
    key_file.write_bytes(base64.urlsafe_b64encode(b"k" * 32))
    root = tmp_path / "tokens"
    store = AesGcmFileSecretStore(root=root, key_file=key_file)
    secret = {"refresh_token": "synthetic-refresh-secret", "scopes": ["gmail.readonly"]}

    reference = store.put("credentials/synthetic", secret)

    assert reference == "file-aesgcm://netpay-gmail/credentials/synthetic"
    ciphertext = (root / "credentials" / "synthetic.enc").read_bytes()
    assert b"synthetic-refresh-secret" not in ciphertext
    assert store.get(reference) == secret
    rotated = {"refresh_token": "rotated-synthetic-secret", "scopes": ["gmail.readonly"]}
    assert store.put("credentials/synthetic", rotated) == reference
    rotated_ciphertext = (root / "credentials" / "synthetic.enc").read_bytes()
    assert rotated_ciphertext != ciphertext
    assert b"rotated-synthetic-secret" not in rotated_ciphertext
    assert store.get(reference) == rotated
    store.delete(reference)
    with pytest.raises(GmailSecretStoreError, match="secret_unavailable"):
        store.get(reference)


def test_aes_secret_store_rejects_path_escape(tmp_path: Path) -> None:
    key_file = tmp_path / "gmail.key"
    key_file.write_bytes(base64.urlsafe_b64encode(b"k" * 32))
    store = AesGcmFileSecretStore(root=tmp_path / "tokens", key_file=key_file)

    with pytest.raises(GmailSecretStoreError, match="secret_reference_invalid"):
        store.put("../outside", {"token": "synthetic"})

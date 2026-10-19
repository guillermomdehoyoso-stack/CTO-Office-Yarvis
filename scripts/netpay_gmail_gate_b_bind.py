"""Create the encrypted expected-mailbox binding without exposing its value."""

from __future__ import annotations

import argparse
import getpass
import re
from pathlib import Path

from yarvis_api.services.netpay_gmail_secret_store import AesGcmFileSecretStore

_MAILBOX_PATTERN = re.compile(
    r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?"
)


def normalize_mailbox(value: str) -> str:
    email = value.strip().casefold()
    if not email.isascii() or not _MAILBOX_PATTERN.fullmatch(email):
        raise ValueError("invalid mailbox")
    return email


def read_mailbox() -> str:
    email = normalize_mailbox(getpass.getpass("Authorized Gmail address (input hidden): "))
    confirmation = normalize_mailbox(getpass.getpass("Repeat authorized Gmail address (input hidden): "))
    if email != confirmation:
        raise ValueError("mailbox entries do not match")
    return email


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="replace an existing binding")
    args = parser.parse_args()
    root = Path("/run/secrets/netpay-gmail")
    binding_path = root / "tokens" / "binding.enc"
    if binding_path.exists() and not args.replace:
        raise SystemExit("Mailbox binding already exists; refusing overwrite.")
    try:
        email = read_mailbox()
    except ValueError as error:
        raise SystemExit(f"{error}; binding was not changed.") from error
    store = AesGcmFileSecretStore(root=root / "tokens", key_file=root / "token-key.txt")
    reference = store.put("binding", {"expected_email": email})
    if reference != "file-aesgcm://netpay-gmail/binding":
        raise SystemExit("Unexpected binding reference.")
    print("Encrypted mailbox binding stored; address was not displayed.")


if __name__ == "__main__":
    main()

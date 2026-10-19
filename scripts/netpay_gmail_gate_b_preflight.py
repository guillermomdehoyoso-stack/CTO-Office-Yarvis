"""Non-secret Gate B local runtime preflight; performs no Google access."""

from __future__ import annotations

import re

from yarvis_api.config import Settings
from yarvis_api.services.netpay_gmail_google_provider import GMAIL_READONLY_SCOPE
from yarvis_api.services.netpay_gmail_secret_store import AesGcmFileSecretStore


def main() -> None:
    settings = Settings()
    checks = {
        "enabled": settings.gmail_intake_enabled,
        "provider_google": settings.gmail_provider == "google",
        "project_exact": settings.gmail_google_project_id == "yarvis-pilot",
        "scope_exact": settings.gmail_oauth_scopes == GMAIL_READONLY_SCOPE,
        "callback_exact": settings.gmail_oauth_redirect_uri
        == "http://127.0.0.1:8000/netpay/gmail/oauth/callback",
        "backfill_30": settings.gmail_backfill_days == 30,
        "label_exact": settings.gmail_label_name == "Yarvis/Netpay-Intake",
        "scheduler_disabled": not settings.scheduler_enabled,
        "worker_disabled": not settings.worker_enabled,
    }
    assert settings.gmail_token_store_root is not None
    assert settings.gmail_token_key_file is not None
    assert settings.gmail_mailbox_binding is not None
    store = AesGcmFileSecretStore(
        root=settings.gmail_token_store_root,
        key_file=settings.gmail_token_key_file,
    )
    try:
        binding = store.get(settings.gmail_mailbox_binding)
        expected_email = str(binding.get("expected_email", ""))
        checks["mailbox_binding_present"] = bool(expected_email)
        normalized = expected_email.strip().casefold()
        checks["mailbox_binding_valid"] = bool(
            normalized.isascii()
            and re.fullmatch(
                r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?",
                normalized,
            )
        )
    except Exception:
        checks["mailbox_binding_present"] = False
        checks["mailbox_binding_valid"] = False
    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{name}={'PASS' if passed else 'PENDING'}")
    if failed:
        raise SystemExit("Gate B preflight pending: " + ", ".join(failed))


if __name__ == "__main__":
    main()

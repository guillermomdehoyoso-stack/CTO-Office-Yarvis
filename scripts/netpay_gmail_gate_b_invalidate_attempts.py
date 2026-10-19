"""Consume pending local OAuth attempts and remove their PKCE verifiers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from yarvis_api.config import Settings
from yarvis_api.main import app
from yarvis_api.models.netpay_gmail_intake import NetpayGmailConnection, NetpayGmailOAuthAttempt
from yarvis_api.services.netpay_gmail_secret_store import AesGcmFileSecretStore


def main() -> None:
    settings = Settings()
    assert settings.gmail_token_store_root is not None
    assert settings.gmail_token_key_file is not None
    store = AesGcmFileSecretStore(
        root=settings.gmail_token_store_root,
        key_file=settings.gmail_token_key_file,
    )
    with app.state.yarvis.persistence.create_session() as db:
        attempts = list(
            db.scalars(
                select(NetpayGmailOAuthAttempt).where(NetpayGmailOAuthAttempt.consumed_at.is_(None))
            ).all()
        )
        references = [item.secret_ref for item in attempts]
        clock = datetime.now(timezone.utc)
        for attempt in attempts:
            attempt.consumed_at = clock
        referenced_credentials = set(
            db.scalars(
                select(NetpayGmailConnection.credential_secret_ref).where(
                    NetpayGmailConnection.provider_kind == "google"
                )
            ).all()
        )
        db.commit()
    for reference in references:
        store.delete(reference)
    credential_root = settings.gmail_token_store_root / "credentials"
    orphan_references = [
        f"file-aesgcm://netpay-gmail/credentials/{path.stem}"
        for path in credential_root.glob("*.enc")
        if f"file-aesgcm://netpay-gmail/credentials/{path.stem}" not in referenced_credentials
    ]
    for reference in orphan_references:
        store.delete(reference)
    print(
        f"Invalidated local OAuth attempts: {len(references)}; PKCE verifiers removed; "
        f"orphan credentials removed: {len(orphan_references)}."
    )


if __name__ == "__main__":
    main()

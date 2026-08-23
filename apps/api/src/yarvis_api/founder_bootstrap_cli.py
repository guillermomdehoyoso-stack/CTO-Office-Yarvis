"""Non-HTTP founder authorization verifier; it never performs enrollment."""

import argparse
from pathlib import Path

from yarvis_api.bootstrap import create_app
from yarvis_api.services.founder_bootstrap import FounderBootstrapAuthorizationService


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or prepare one signed founder-bootstrap authorization.")
    parser.add_argument("operation", choices=("verify", "consume"))
    parser.add_argument("--authorization-file", required=True, type=Path)
    args = parser.parse_args()
    payload = args.authorization_file.read_bytes()
    app = create_app()
    if args.operation == "consume" and app.state.yarvis.settings.environment != "test":
        parser.error("consume is available only in the synthetic test environment")
    with app.state.yarvis.persistence.create_session() as db:
        receipt = FounderBootstrapAuthorizationService().prepare(
            db, authorization=payload, settings=app.state.yarvis.settings
        )
        if args.operation == "consume":
            FounderBootstrapAuthorizationService().consume(db, receipt=receipt)
            db.commit()
        else:
            db.rollback()
    print(
        "founder_bootstrap_authorization_verified"
        if args.operation == "verify"
        else "founder_bootstrap_authorization_prepared"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

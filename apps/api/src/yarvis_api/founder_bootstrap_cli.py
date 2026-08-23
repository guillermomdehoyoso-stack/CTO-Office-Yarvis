"""Non-HTTP, signed founder-bootstrap administrative command."""

import argparse
import sys
from pathlib import Path

from yarvis_api.application.errors import ApplicationError
from yarvis_api.bootstrap import create_app
from yarvis_api.services.founder_bootstrap import FounderBootstrapAuthorizationService


def _authorization_bytes(args: argparse.Namespace, parser: argparse.ArgumentParser) -> bytes:
    if args.authorization_file is not None:
        return args.authorization_file.read_bytes()
    if args.authorization_stdin:
        return sys.stdin.buffer.read()
    parser.error("exactly one authorization input is required")
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Administer one signed founder-bootstrap authorization.")
    parser.add_argument("operation", choices=("verify", "consume", "enroll", "select-handoff"))
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--authorization-file", type=Path)
    input_group.add_argument("--authorization-stdin", action="store_true")
    args = parser.parse_args()
    app = create_app()
    settings = app.state.yarvis.settings
    if args.operation != "select-handoff" and args.authorization_file is None and not args.authorization_stdin:
        parser.error("exactly one authorization input is required")
    if args.operation == "consume" and app.state.yarvis.settings.environment != "test":
        parser.error("consume is available only in the synthetic test environment")
    if args.operation in {"enroll", "select-handoff"} and settings.environment != "production":
        parser.error(f"{args.operation} requires the production environment")
    with app.state.yarvis.persistence.create_session() as db:
        service = FounderBootstrapAuthorizationService()
        try:
            if args.operation == "select-handoff":
                handoff = service.select_eligible_handoff(db, settings=settings)
                db.rollback()
                print(f"founder_bootstrap_handoff_id={handoff.id}")
                return 0
            payload = _authorization_bytes(args, parser)
            if args.operation == "enroll":
                receipt = service.enroll(db, authorization=payload, settings=settings)
            else:
                receipt = service.prepare(db, authorization=payload, settings=settings)
            if args.operation == "consume":
                receipt = service.consume(db, receipt=receipt)
            if args.operation in {"consume", "enroll"}:
                db.commit()
            else:
                db.rollback()
        except ApplicationError as error:
            db.rollback()
            print(f"founder_bootstrap_failed code={error.code}", file=sys.stderr)
            return 2
    if args.operation == "enroll":
        assert receipt.outcome == "enrolled"
        print("founder_bootstrap_enrollment_completed status=enrolled")
    elif args.operation == "verify":
        print("founder_bootstrap_authorization_verified")
    else:
        print("founder_bootstrap_authorization_prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

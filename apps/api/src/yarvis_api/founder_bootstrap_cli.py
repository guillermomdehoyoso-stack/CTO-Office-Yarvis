"""Non-HTTP, signed founder-bootstrap administrative command."""

import argparse
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yarvis_api.application.errors import ApplicationError
from yarvis_api.bootstrap import create_app
from yarvis_api.config import FounderFirstOrganizationSettings, FounderHandoffSelectorSettings
from yarvis_api.persistence import sqlalchemy_url
from yarvis_api.services.first_organization import FirstOrganizationAuthorizationService
from yarvis_api.services.founder_bootstrap import FounderBootstrapAuthorizationService


def _authorization_bytes(args: argparse.Namespace, parser: argparse.ArgumentParser) -> bytes:
    if args.authorization_file is not None:
        return args.authorization_file.read_bytes()
    if args.authorization_stdin:
        return sys.stdin.buffer.read()
    parser.error("exactly one authorization input is required")
    raise AssertionError("unreachable")


@contextmanager
def _selector_session(settings: FounderHandoffSelectorSettings | FounderFirstOrganizationSettings) -> Iterator[Session]:
    engine = create_engine(sqlalchemy_url(settings.database_url), pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        with session_factory() as db:
            yield db
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Administer one signed founder-bootstrap authorization.")
    parser.add_argument(
        "operation",
        choices=("verify", "consume", "enroll", "select-handoff", "select-organization", "create-first-organization"),
    )
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--authorization-file", type=Path)
    input_group.add_argument("--authorization-stdin", action="store_true")
    args = parser.parse_args()
    if args.operation in {"select-handoff", "select-organization"}:
        output_key = (
            "founder_bootstrap_handoff_id"
            if args.operation == "select-handoff"
            else "founder_bootstrap_organization_id"
        )
        selected_id = ""
        try:
            selector_settings = FounderHandoffSelectorSettings()
            with _selector_session(selector_settings) as db:
                service = FounderBootstrapAuthorizationService()
                try:
                    if args.operation == "select-handoff":
                        selected_id = str(service.select_eligible_handoff(db, settings=selector_settings).id)
                    else:
                        selected_id = str(service.select_active_organization(db).id)
                finally:
                    db.rollback()
        except ApplicationError as error:
            print(f"founder_bootstrap_failed code={error.code}", file=sys.stderr)
            return 2
        print(f"{output_key}={selected_id}")
        return 0
    if args.operation == "create-first-organization":
        try:
            settings = FounderFirstOrganizationSettings()
            authorization = _authorization_bytes(args, parser)
            with _selector_session(settings) as db:
                result = FirstOrganizationAuthorizationService().create(
                    db, authorization=authorization, settings=settings
                )
                db.commit()
        except ApplicationError as error:
            try:
                db.rollback()
            except UnboundLocalError:
                pass
            print(f"founder_bootstrap_failed code={error.code}", file=sys.stderr)
            return 2
        status = "replayed" if result.replayed else "created"
        print(f"founder_bootstrap_first_organization_created status={status}")
        return 0
    app = create_app()
    settings = app.state.yarvis.settings
    if (
        args.operation not in {"select-handoff", "select-organization"}
        and args.authorization_file is None
        and not args.authorization_stdin
    ):
        parser.error("exactly one authorization input is required")
    if args.operation == "consume" and app.state.yarvis.settings.environment != "test":
        parser.error("consume is available only in the synthetic test environment")
    if args.operation == "enroll" and settings.environment != "production":
        parser.error(f"{args.operation} requires the production environment")
    with app.state.yarvis.persistence.create_session() as db:
        service = FounderBootstrapAuthorizationService()
        try:
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

"""Fail-closed local/test provisioning for the Netpay operations role."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yarvis_api.config import Settings, get_settings
from yarvis_api.database import legacy_session
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

NETPAY_OPERATIONS_ROLE = "netpay_operations_operator"
ALLOWED_ENVIRONMENTS = frozenset({"local", "test"})


class LocalAuthorityProvisioningError(RuntimeError):
    """A safe, operator-facing failure that makes no partial change."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ProvisioningResult:
    status: str
    principal_id: str
    organization_id: str
    membership_id: str
    role: str


def _validate_request(*, settings: Settings, subject: str, role: str) -> str:
    if settings.environment not in ALLOWED_ENVIRONMENTS:
        raise LocalAuthorityProvisioningError(
            "environment_denied",
            "local authority provisioning is disabled in this environment",
        )
    normalized_subject = subject.strip()
    if not normalized_subject:
        raise LocalAuthorityProvisioningError("subject_required", "subject is required")
    if role != NETPAY_OPERATIONS_ROLE:
        raise LocalAuthorityProvisioningError("role_denied", "requested role is not allowed")
    return normalized_subject


def provision_local_netpay_operator(
    db: Session,
    *,
    settings: Settings,
    subject: str,
    organization_id: UUID,
    role: str,
) -> ProvisioningResult:
    """Provision exactly one persisted local/test Principal and Membership."""

    normalized_subject = _validate_request(settings=settings, subject=subject, role=role)
    try:
        with db.begin():
            organization = db.scalar(
                select(Organization).where(
                    Organization.id == organization_id,
                    Organization.status == "active",
                )
            )
            if organization is None:
                raise LocalAuthorityProvisioningError(
                    "organization_not_found",
                    "active organization was not found",
                )

            principal = db.scalar(select(Principal).where(Principal.external_subject == normalized_subject))
            if principal is None:
                principal = Principal(external_subject=normalized_subject, status="active")
                db.add(principal)
                db.flush()
            elif principal.status != "active":
                raise LocalAuthorityProvisioningError(
                    "principal_inactive",
                    "principal is not active and was not changed",
                )

            membership = db.scalar(
                select(PrincipalMembership).where(
                    PrincipalMembership.principal_id == principal.id,
                    PrincipalMembership.organization_id == organization.id,
                )
            )
            if membership is not None:
                if membership.status != "active":
                    raise LocalAuthorityProvisioningError(
                        "membership_inactive",
                        "membership is not active and was not changed",
                    )
                if membership.role != role:
                    raise LocalAuthorityProvisioningError(
                        "membership_role_conflict",
                        "membership already has a different role and was not changed",
                    )
                return ProvisioningResult(
                    status="already_provisioned",
                    principal_id=str(principal.id),
                    organization_id=str(organization.id),
                    membership_id=str(membership.id),
                    role=membership.role,
                )

            membership = PrincipalMembership(
                principal_id=principal.id,
                organization_id=organization.id,
                role=role,
                status="active",
            )
            db.add(membership)
            db.flush()
            return ProvisioningResult(
                status="created",
                principal_id=str(principal.id),
                organization_id=str(organization.id),
                membership_id=str(membership.id),
                role=membership.role,
            )
    except IntegrityError as error:
        raise LocalAuthorityProvisioningError(
            "persistence_conflict",
            "provisioning conflicted with persisted authority state",
        ) from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision the ratified Netpay operations role in local/test only."
    )
    parser.add_argument("--subject", required=True)
    parser.add_argument("--organization-id", required=True, type=UUID)
    parser.add_argument("--role", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    try:
        _validate_request(settings=settings, subject=args.subject, role=args.role)
        with legacy_session() as db:
            result = provision_local_netpay_operator(
                db,
                settings=settings,
                subject=args.subject,
                organization_id=args.organization_id,
                role=args.role,
            )
    except LocalAuthorityProvisioningError as error:
        print(json.dumps({"status": "error", "code": error.code, "message": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

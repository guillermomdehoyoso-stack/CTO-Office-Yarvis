"""Create the bounded local authority used by the Gate B pilot runtime."""

from __future__ import annotations

from sqlalchemy import select

from yarvis_api.main import app
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership

ORGANIZATION_NAME = "Netpay Gmail Pilot"
SUBJECT = "netpay-gmail:operator"
ROLE = "netpay_inbox_operator"


def main() -> None:
    with app.state.yarvis.persistence.create_session() as db:
        organization = db.scalar(select(Organization).where(Organization.display_name == ORGANIZATION_NAME))
        if organization is None:
            organization = Organization(
                legal_name=ORGANIZATION_NAME,
                display_name=ORGANIZATION_NAME,
                status="active",
            )
            db.add(organization)
            db.flush()
        elif organization.status != "active":
            raise SystemExit("Gate B organization exists but is not active.")

        principal = db.scalar(select(Principal).where(Principal.external_subject == SUBJECT))
        if principal is None:
            principal = Principal(external_subject=SUBJECT, status="active")
            db.add(principal)
            db.flush()
        elif principal.status != "active":
            raise SystemExit("Gate B principal exists but is not active.")

        memberships = list(
            db.scalars(select(PrincipalMembership).where(PrincipalMembership.principal_id == principal.id)).all()
        )
        matching = [item for item in memberships if item.organization_id == organization.id]
        if len(memberships) > 1 or len(matching) != len(memberships):
            raise SystemExit("Gate B principal has an unexpected organization membership.")
        if not matching:
            db.add(
                PrincipalMembership(
                    principal_id=principal.id,
                    organization_id=organization.id,
                    role=ROLE,
                    status="active",
                )
            )
        else:
            membership = matching[0]
            if membership.status != "active" or membership.role != ROLE:
                raise SystemExit("Gate B membership does not match the bounded role.")
        db.commit()
        print("Gate B local Principal, Organization and bounded Membership are ready.")


if __name__ == "__main__":
    main()

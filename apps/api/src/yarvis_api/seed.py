"""Optional development seed; run with `python -m yarvis_api.seed`."""
from sqlalchemy import select

from yarvis_api.database import SessionLocal
from yarvis_api.models.case import Case
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person


def main() -> None:
    with SessionLocal() as db:
        organization = db.scalar(select(Organization).where(Organization.legal_name == "Energía Fotónica"))
        if organization is None:
            organization = Organization(legal_name="Energía Fotónica", display_name="Energía Fotónica", organization_type="business")
            db.add(organization)
            db.flush()
        person = db.scalar(select(Person).where(Person.display_name == "Juan Manuel"))
        if person is None:
            person = Person(first_name="Juan", last_name="Manuel", display_name="Juan Manuel")
            db.add(person)
            db.flush()
        title = "Cambio de alcance — preparación bifásica y redistribución eléctrica"
        if db.scalar(select(Case).where(Case.title == title)) is None:
            db.add(Case(title=title, case_type="cfe", owner_organization_id=organization.id, primary_person_id=person.id))
        db.commit()
    print("Seed completed")


if __name__ == "__main__":
    main()

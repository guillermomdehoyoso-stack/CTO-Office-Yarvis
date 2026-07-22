"""Optional development seed; run with `python -m yarvis_api.seed`."""
from sqlalchemy import select

from yarvis_api.database import legacy_session
from yarvis_api.models.case import Case
from yarvis_api.models.domain_event import DomainEvent, record_event
from yarvis_api.models.evidence import Evidence
from yarvis_api.models.intake import IntakeItem
from yarvis_api.models.organization import Organization
from yarvis_api.models.person import Person


def main() -> None:
    with legacy_session() as db:
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
        case = db.scalar(select(Case).where(Case.title == title))
        if case is None:
            case = Case(title=title, case_type="cfe", owner_organization_id=organization.id, primary_person_id=person.id)
            db.add(case)
            db.flush()
        if db.scalar(select(DomainEvent).where(DomainEvent.event_type == "case.created", DomainEvent.case_id == case.id)) is None:
            record_event(db, event_type="case.created", aggregate_type="case", aggregate_id=case.id, organization_id=organization.id, case_id=case.id, payload={"case_number": case.case_number})
        text = "Cliente solicitó cambio de servicio monofásico a bifásico"
        intake = db.scalar(select(IntakeItem).where(IntakeItem.text_content == text))
        if intake is None:
            intake = IntakeItem(source_type="manual_text", content_type="text/plain", text_content=text, organization_id=organization.id, person_id=person.id)
            db.add(intake)
            db.flush()
            record_event(db, event_type="intake.received", aggregate_type="intake_item", aggregate_id=intake.id, organization_id=organization.id, payload={"intake_number": intake.intake_number, "source_type": intake.source_type})
        if intake.case_id != case.id:
            intake.case_id = case.id
            record_event(db, event_type="intake.linked_to_case", aggregate_type="intake_item", aggregate_id=intake.id, organization_id=organization.id, case_id=case.id, payload={"intake_number": intake.intake_number})
        evidence_title = "Fotografías de preparación de nueva base de medidor"
        if db.scalar(select(Evidence).where(Evidence.case_id == case.id, Evidence.title == evidence_title)) is None:
            evidence = Evidence(case_id=case.id, intake_item_id=intake.id, evidence_type="photo", title=evidence_title)
            db.add(evidence)
            db.flush()
            record_event(db, event_type="evidence.created", aggregate_type="evidence", aggregate_id=evidence.id, organization_id=organization.id, case_id=case.id, payload={"evidence_type": evidence.evidence_type, "title": evidence.title})
        db.commit()
    print("Seed completed")


if __name__ == "__main__":
    main()

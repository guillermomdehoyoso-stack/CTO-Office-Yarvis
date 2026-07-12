from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.models.checklist import CaseType, ChecklistRequirement, ChecklistTemplate, DocumentType

DOCUMENT_TYPES = [
    ("cfe_bill", "Recibo CFE"), ("government_id", "Identificación oficial"), ("power_of_attorney", "Carta poder"),
    ("tax_certificate", "Constancia fiscal"), ("bank_statement", "Estado de cuenta bancario"), ("address_proof", "Comprobante de domicilio"),
    ("incorporation_document", "Acta constitutiva"), ("premises_photos", "Fotografías del local"), ("domain_ownership_proof", "Comprobante de dominio"),
    ("single_line_diagram", "Diagrama unifilar"), ("equipment_datasheet", "Ficha técnica de equipo"), ("equipment_certificate", "Certificado de equipo"), ("other", "Otro"),
]
TEMPLATES = {
    "cfe_residential_interconnection": [
        ("cfe_bill", "Recibo CFE", "cfe_bill", True), ("client_id", "INE del cliente", "government_id", True),
        ("power_of_attorney", "Carta poder", "power_of_attorney", True), ("manager_id", "INE del gestor", "government_id", True),
        ("annex_2", "Anexo 2 CFE", None, True), ("site_sketch", "Croquis", None, True),
        ("premises_photos", "Fotografías de instalación y medidor", "premises_photos", True), ("single_line_diagram", "Diagrama unifilar", "single_line_diagram", True),
        ("equipment_docs", "Fichas y certificados de equipos", "equipment_datasheet", True),
    ],
    "netpay_merchant_onboarding": [
        ("government_id", "Identificación de persona física o apoderado", "government_id", True), ("incorporation", "Acta constitutiva", "incorporation_document", False),
        ("bank_statement", "Estado de cuenta bancario reciente", "bank_statement", True), ("address_proof", "Comprobante de domicilio reciente", "address_proof", True),
        ("tax_certificate", "Constancia fiscal reciente", "tax_certificate", True), ("premises_photos", "Cuatro fotografías del local", "premises_photos", True),
        ("domain_ownership", "Comprobante de propiedad de dominio", "domain_ownership_proof", False),
    ],
}


def load_catalogs(db: Session) -> None:
    case_types = {}
    for code, name in (("cfe_residential_interconnection", "Interconexión residencial CFE"), ("netpay_merchant_onboarding", "Alta de comercio NetPay")):
        item = db.scalar(select(CaseType).where(CaseType.code == code))
        if item is None:
            item = CaseType(code=code, name=name)
            db.add(item)
            db.flush()
        case_types[code] = item
    document_types = {}
    for code, name in DOCUMENT_TYPES:
        item = db.scalar(select(DocumentType).where(DocumentType.code == code))
        if item is None:
            item = DocumentType(code=code, name=name)
            db.add(item)
            db.flush()
        document_types[code] = item
    # Operational defaults, not universal legal validity rules.
    for code, validity_days in {"tax_certificate": 30, "bank_statement": 90, "address_proof": 90, "cfe_bill": 90}.items():
        document_types[code].validity_days = validity_days
    for case_code, requirements in TEMPLATES.items():
        template = db.scalar(select(ChecklistTemplate).where(ChecklistTemplate.case_type_id == case_types[case_code].id, ChecklistTemplate.version == 1))
        if template is None:
            template = ChecklistTemplate(case_type_id=case_types[case_code].id, name=f"Checklist {case_types[case_code].name}", version=1)
            db.add(template)
            db.flush()
        for order, (code, name, document_code, required) in enumerate(requirements, start=1):
            if db.scalar(select(ChecklistRequirement).where(ChecklistRequirement.checklist_template_id == template.id, ChecklistRequirement.code == code)) is None:
                db.add(ChecklistRequirement(checklist_template_id=template.id, code=code, name=name, document_type_id=document_types[document_code].id if document_code else None, required=required, multiple_allowed=False, display_order=order))


def main() -> None:
    from yarvis_api.database import SessionLocal
    with SessionLocal() as db:
        load_catalogs(db)
        db.commit()
    print("Catalogs loaded")


if __name__ == "__main__":
    main()

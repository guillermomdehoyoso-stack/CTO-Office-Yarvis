from sqlalchemy import select
from sqlalchemy.orm import Session

from yarvis_api.models.checklist import CaseType, ChecklistRequirement, ChecklistTemplate, DocumentType
from yarvis_api.models.observation_engine import OperationalPolicy

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

OPERATIONAL_POLICIES = [
    {
        "policy_key": "netpay.store.watch_inactivity",
        "domain": "netpay",
        "version": 1,
        "status": "active",
        "description": "Watch stores that reached inactivity threshold.",
        "severity": "warning",
        "requires_human_approval": True,
        "configuration": {
            "conditions": [
                {"field": "inactive_days", "operator": "greater_than_or_equal", "value": 30},
            ],
            "output": "watch",
        },
    },
    {
        "policy_key": "netpay.store.churn_candidate",
        "domain": "netpay",
        "version": 1,
        "status": "active",
        "description": "Flag churn candidate stores, never automatic cancellation.",
        "severity": "critical",
        "requires_human_approval": True,
        "configuration": {
            "conditions": [
                {"field": "inactive_days", "operator": "greater_than_or_equal", "value": 60},
                {"field": "open_service_case", "operator": "equals", "value": False},
                {"field": "open_replacement", "operator": "equals", "value": False},
            ],
            "output": "churn_candidate",
            "cancellation": "manual_only",
        },
    },
    {
        "policy_key": "netpay.store.critical_sales_drop",
        "domain": "netpay",
        "version": 1,
        "status": "active",
        "description": "Identify critical sales deterioration before churn window.",
        "severity": "critical",
        "requires_human_approval": True,
        "configuration": {
            "conditions": [
                {"field": "historical_volume", "operator": "greater_than", "value": 1000},
                {"field": "sales_drop_percentage", "operator": "greater_than_or_equal", "value": 35},
            ],
            "output": "critical_store_review",
        },
    },
    {
        "policy_key": "netpay.asset.recovery_review",
        "domain": "netpay",
        "version": 1,
        "status": "active",
        "description": "Recommend asset recovery review for churn candidate stores.",
        "severity": "critical",
        "requires_human_approval": True,
        "configuration": {
            "conditions": [
                {"field": "is_churn_candidate", "operator": "equals", "value": True},
                {"field": "asset_assigned", "operator": "equals", "value": True},
                {"field": "active_shipment_or_replacement", "operator": "equals", "value": False},
            ],
            "output": "asset_recovery_review",
        },
    },
]


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

    for policy_data in OPERATIONAL_POLICIES:
        existing = db.scalar(
            select(OperationalPolicy).where(
                OperationalPolicy.policy_key == policy_data["policy_key"],
                OperationalPolicy.version == policy_data["version"],
            )
        )
        if existing is None:
            db.add(OperationalPolicy(**policy_data))


def main() -> None:
    from yarvis_api.config import get_settings
    from yarvis_api.persistence import build_persistence_runtime

    runtime = build_persistence_runtime(get_settings())
    owner_token = object()
    runtime.transfer_ownership(owner_token)
    try:
        with runtime.create_session() as db:
            load_catalogs(db)
            db.commit()
    finally:
        runtime.dispose(owner_token)
    print("Catalogs loaded")


if __name__ == "__main__":
    main()

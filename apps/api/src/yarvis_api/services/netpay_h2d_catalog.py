"""Approved H2-D pilot catalog projection and immutable snapshot builder."""

from __future__ import annotations

from copy import deepcopy

CATALOG_VERSION = "1.0.0"
CATALOG_EFFECTIVE_DATE = "2026-10-14"
CATALOG_SHA256 = "4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b"
CATALOG_OWNER = "Guillermo De Hoyos"
CATALOG_PROVENANCE = "operator_reported"

_COMMON = {"required": True, "provenance_kind": CATALOG_PROVENANCE}
_BASE_REQUIREMENTS = [
    {
        **_COMMON,
        "key": "applicant_or_representative_government_id",
        "label": "INE del titular o del representante legal",
        "scope": "representative",
    },
    {
        **_COMMON,
        "key": "receiving_account_bank_statement",
        "label": "Estado de cuenta bancario",
        "scope": "client",
        "maximum_age_days": 60,
        "shareable": True,
    },
    {
        **_COMMON,
        "key": "tax_status_certificate",
        "label": "Constancia de Situación Fiscal",
        "scope": "client",
        "maximum_age_days": 60,
        "holder_must_match": "receiving_account_bank_statement",
    },
    {
        **_COMMON,
        "key": "applicant_or_representative_rfc",
        "label": "RFC del titular o del representante legal",
        "scope": "representative",
    },
    {
        **_COMMON,
        "key": "applicant_or_representative_mobile",
        "label": "Celular del titular o del representante legal",
        "scope": "representative",
        "kind": "data",
    },
    {
        **_COMMON,
        "key": "applicant_or_representative_email",
        "label": "Correo electrónico del titular o del representante legal",
        "scope": "representative",
        "kind": "data",
    },
]
_MORAL_REQUIREMENTS = [
    {**_COMMON, "key": "incorporation_instrument", "label": "Acta constitutiva", "scope": "client"},
    {
        **_COMMON,
        "key": "legal_representative_authority",
        "label": "Poder del representante legal",
        "scope": "representative",
    },
]
_BRANCH_REQUIREMENTS = [
    {
        **_COMMON,
        "key": "branch_address_proof",
        "label": "Comprobante de domicilio del local comercial",
        "scope": "branch",
        "maximum_age_days": 60,
    },
    {
        **_COMMON,
        "key": "branch_premises_photos",
        "label": "Cuatro fotos: dos del interior y dos de la fachada",
        "scope": "branch",
        "expected_count": 4,
    },
    {
        **_COMMON,
        "key": "branch_manager_contact",
        "label": "Nombre, teléfono y correo del encargado del comercio",
        "scope": "branch",
        "kind": "data",
        "shareable": True,
    },
]
_ECOMMERCE_REQUIREMENTS = [
    {**_COMMON, "key": "ecommerce_domain_ownership", "label": "Comprobante de propiedad del dominio", "scope": "client"}
]


def build_catalog_snapshot(*, applicant_kind: str, products: list[str], branches: list[dict]) -> dict:
    if applicant_kind not in {"persona_fisica", "persona_moral"}:
        raise ValueError("resolved applicant kind required")
    normalized_products = sorted(set(products))
    if not normalized_products or any(item not in {"tpv", "ecommerce"} for item in normalized_products):
        raise ValueError("supported product required")
    if not branches:
        raise ValueError("physical branch required")
    requirements = deepcopy(_BASE_REQUIREMENTS)
    if applicant_kind == "persona_moral":
        requirements.extend(deepcopy(_MORAL_REQUIREMENTS))
    if "ecommerce" in normalized_products:
        requirements.extend(deepcopy(_ECOMMERCE_REQUIREMENTS))
    for branch in branches:
        draft_key = str(branch.get("draft_key") or "").strip()
        name = str(branch.get("name") or "").strip()
        if not draft_key or not name:
            raise ValueError("branch key and name required")
        for definition in _BRANCH_REQUIREMENTS:
            item = deepcopy(definition)
            item["scope_key"] = f"branch:{draft_key}"
            item["branch_draft_key"] = draft_key
            item["branch_name"] = name
            requirements.append(item)
    for position, requirement in enumerate(requirements, start=1):
        requirement.setdefault("scope_key", requirement["scope"])
        requirement["snapshot_key"] = f"{requirement['scope_key']}:{requirement['key']}"
        requirement["position"] = position
    return {
        "catalog_version": CATALOG_VERSION,
        "catalog_effective_date": CATALOG_EFFECTIVE_DATE,
        "catalog_sha256": CATALOG_SHA256,
        "catalog_owner": CATALOG_OWNER,
        "catalog_provenance": CATALOG_PROVENANCE,
        "applicant_kind": applicant_kind,
        "products": normalized_products,
        "physical_location_scope": True,
        "requirements": requirements,
    }

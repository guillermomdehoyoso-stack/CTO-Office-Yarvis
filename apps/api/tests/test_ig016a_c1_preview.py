import hashlib
import io
import json
import zipfile

import pytest
from openpyxl import Workbook

from yarvis_api.services.netpay_no_usage_recovery_preview import (
    PROFILES,
    PreviewSourceError,
    SourceBytes,
    _identity,
    _ticket_client_identity,
    preview_no_usage_recovery_sources,
)


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """C1 proves it has no database dependency, including during test setup."""
    yield


@pytest.fixture(autouse=True)
def clean_database():
    """Override the repository DB fixture: this package must remain pure C1."""
    yield


def _book(
    profile: str,
    *,
    bad_header=False,
    bad_type=False,
    formula=False,
    ticket_header_overrides: dict[int, str] | None = None,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    if profile == "netpay_no_usage_oct26_v1":
        sheet.append(
            [
                "wrong" if bad_header else "#",
                "Store ID",
                "Store Name",
                "Master Name",
                "Distributor Name",
                "Estatus",
                "Meses No Uso",
                "Alertas",
                "Motivo del no uso",
                None,
                None,
                "Fecha",
                "Renta",
                "Cancelar",
                "Comentarios",
            ]
        )
        sheet.merge_cells("I1:K1")
        sheet.append(["bad" if bad_type else 1, "S1", "name", "master", "distributor", "Activo", 3, "alert"])
        sheet.append([2])
        sheet.cell(1001, 15, " ")
    elif profile == "netpay_global_equipment_oct26_v1":
        sheet.append([None] * 17)
        sheet.append(
            [
                None,
                "wrong" if bad_header else "Serial TPV",
                "Estatus de producto",
                "Numero de comercio",
                "Nombre del comercio",
                "Numero de terminal",
                "Folio",
                "Producto",
                "Fecha de creacion",
                "Client ID",
                "Rep Legal",
                "Correo Rep Legal",
                "Tel Rep Legal",
                "RFC",
                "Razon Social",
                "Domicilio comercial",
                "Tel Local Comercial",
            ]
        )
        sheet.merge_cells("J1:M1")
        sheet.merge_cells("N1:O1")
        sheet.merge_cells("P1:Q1")
        sheet.append([None, "SER1", "Activo", "S1", "commerce", "T1", "F1", "TPV", "date"])
        sheet.cell(347, 17, " ")
    else:
        ticket_headers = {
            12: "Correo Rep Legal",
            13: "Tel Rep Legal",
            16: "Razon Social",
            **(ticket_header_overrides or {}),
        }
        sheet.append([None] * 25)
        sheet.append(
            [
                None,
                "Serial TPV",
                "Estatus de producto",
                "Numero de comercio",
                "Nombre del comercio",
                "Numero de terminal",
                "Folio",
                "Producto",
                "Fecha de creacion",
                "Client ID",
                "Rep Legal",
                ticket_headers[12],
                ticket_headers[13],
                "Company Id",
                "RFC",
                ticket_headers[16],
                "Branch Id",
                "Domicilio",
            ]
            + [None] * 7
        )
        sheet.append(
            [None] * 17 + ["ESTADO", "CIUDAD", "CP", "COLONIA", "CALLE", "NO EXTERIOR", "NO INTERIOR", "Tel Local"]
        )
        for merged in PROFILES[profile].merged:
            sheet.merge_cells(merged)
        sheet.append(
            [
                None,
                "SER1",
                "Activo",
                "S1",
                "commerce",
                "T1",
                "F1",
                "TPV",
                "date",
                "C1",
                "person",
                "private@example.test",
                "555",
                "CO1",
                "RFC",
                "company",
                "B1",
            ]
        )
        sheet.cell(348, 25, " ")
    if formula:
        sheet.cell(sheet.max_row, sheet.max_column, "=1+1")
    target = io.BytesIO()
    workbook.save(target)
    workbook.close()
    return target.getvalue()


def _sources(**options):
    sources = []
    for profile in PROFILES:
        content = _book(profile, **options)
        sources.append(SourceBytes(profile, content, hashlib.sha256(content).hexdigest()))
    return tuple(sources)


def test_canonical_profiles_are_deterministic_minimized_and_side_effect_free():
    sources = _sources()
    first = preview_no_usage_recovery_sources("org-a", sources, enforce_allowlist=False)
    second = preview_no_usage_recovery_sources("org-a", sources, enforce_allowlist=False)
    assert first == second
    assert first["matching"] == {
        "exact_evidenced": 1,
        "resolution_status": "pending",
        "resolution_reason": "pending_temporality",
        "missing_equipment_match": 0,
        "equipment_with_client": 1,
        "missing_store_and_client": 0,
        "ambiguous": 0,
        "contradictory": 0,
        "period_cutoff": "unknown",
    }
    assert first["effects"] == {"database_writes": 0, "events_emitted": 0, "cache_writes": 0}
    serialized = json.dumps(first)
    assert "private@example" not in serialized and "person" not in serialized and "C1" not in serialized


def test_organization_scope_is_isolated():
    sources = _sources()
    assert (
        preview_no_usage_recovery_sources("org-a", sources, enforce_allowlist=False)["preview_digest"]
        != preview_no_usage_recovery_sources("org-b", sources, enforce_allowlist=False)["preview_digest"]
    )


@pytest.mark.parametrize("value", [0, 0.0, "0", " 0 ", "\t0\n", None, ""])
def test_ticket_client_zero_and_blank_are_missing(value):
    assert _ticket_client_identity(value) is None


@pytest.mark.parametrize("value,expected", [("C1", "C1"), ("00", "00"), ("0.0", "0.0"), (-1, "-1")])
def test_ticket_client_non_placeholder_values_are_not_coerced(value, expected):
    assert _ticket_client_identity(value) == expected


def test_ticket_client_rule_does_not_change_other_identity_spaces():
    sources = list(_sources())
    ticket = sources[2]
    # The synthetic Ticket keeps Store, terminal and serial values that are independently parsed.
    preview = preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)
    assert preview["matching"]["exact_evidenced"] == 1
    assert ticket.profile == "netpay_ticket97580_equipment_client_oct26_v1"
    assert _identity(0) == "0"


@pytest.mark.parametrize(
    "overrides",
    [
        {12: "Correo"},
        {13: "Tel"},
        {16: "Razon"},
        {12: "Correo Rep Legal", 13: "Tel", 16: "Razon Social"},
    ],
)
def test_ticket_abbreviated_or_mixed_headers_are_rejected(overrides):
    sources = list(_sources())
    profile = "netpay_ticket97580_equipment_client_oct26_v1"
    content = _book(profile, ticket_header_overrides=overrides)
    sources[2] = SourceBytes(profile, content, hashlib.sha256(content).hexdigest())
    with pytest.raises(PreviewSourceError, match="^incompatible_xlsx_header$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)


@pytest.mark.parametrize(
    "option,code",
    [
        ({"bad_header": True}, "incompatible_xlsx_header"),
        ({"bad_type": True}, "incompatible_xlsx_value_type"),
        ({"formula": True}, "xlsx_formula_not_allowed"),
    ],
)
def test_incompatible_content_is_rejected(option, code):
    with pytest.raises(PreviewSourceError, match=f"^{code}$"):
        preview_no_usage_recovery_sources("org", _sources(**option), enforce_allowlist=False)


def test_hash_mismatch_and_real_allowlist_are_controlled():
    sources = list(_sources())
    sources[0] = SourceBytes(sources[0].profile, sources[0].content, "0" * 64)
    with pytest.raises(PreviewSourceError, match="^source_hash_mismatch$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)
    with pytest.raises(PreviewSourceError, match="^source_hash_not_allowlisted$"):
        preview_no_usage_recovery_sources("org", _sources(), enforce_allowlist=True)


def test_wrong_sheet_and_merged_signature_are_rejected():
    workbook = Workbook()
    workbook.active.title = "Other"
    target = io.BytesIO()
    workbook.save(target)
    bad = target.getvalue()
    sources = list(_sources())
    sources[0] = SourceBytes(sources[0].profile, bad, hashlib.sha256(bad).hexdigest())
    with pytest.raises(PreviewSourceError, match="^incompatible_xlsx_sheet$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(
        ["#", "Store ID", "Store Name", "Master Name", "Distributor Name", "Estatus", "Meses No Uso", "Alertas"]
    )
    sheet.cell(1001, 15, " ")
    target = io.BytesIO()
    workbook.save(target)
    bad = target.getvalue()
    sources[0] = SourceBytes(sources[0].profile, bad, hashlib.sha256(bad).hexdigest())
    with pytest.raises(PreviewSourceError, match="^incompatible_xlsx_merges$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)


def test_truncated_and_unsafe_zip_are_rejected():
    sources = list(_sources())
    bad = b"PK\x03\x04broken"
    sources[0] = SourceBytes(sources[0].profile, bad, hashlib.sha256(bad).hexdigest())
    with pytest.raises(PreviewSourceError, match="^invalid_xlsx_package$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("../escape", b"x")
    bad = target.getvalue()
    sources[0] = SourceBytes(sources[0].profile, bad, hashlib.sha256(bad).hexdigest())
    with pytest.raises(PreviewSourceError, match="^unsafe_xlsx_path$"):
        preview_no_usage_recovery_sources("org", tuple(sources), enforce_allowlist=False)


def test_request_requires_each_profile_exactly_once():
    with pytest.raises(PreviewSourceError, match="^invalid_preview_request$"):
        preview_no_usage_recovery_sources("org", _sources()[:2], enforce_allowlist=False)

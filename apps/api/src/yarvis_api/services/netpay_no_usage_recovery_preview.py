"""IG-016A C1 read-only XLSX preview; deliberately has no persistence surface."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from xml.etree import ElementTree as ET

from openpyxl import load_workbook

MAX_ENTRIES = 600
MAX_ENTRY_BYTES = 12_000_000
MAX_EXPANDED_BYTES = 40_000_000
MAX_RATIO = 200
WORKBOOK_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"


class PreviewSourceError(ValueError):
    """Safe error whose text never includes workbook values or paths."""


@dataclass(frozen=True)
class SourceBytes:
    profile: str
    content: bytes
    expected_sha256: str


@dataclass(frozen=True)
class _Profile:
    version: str
    allowed_hash: str
    rows: int
    columns: int
    header_rows: int
    merged: tuple[str, ...]


PROFILES = {
    "netpay_no_usage_oct26_v1": _Profile(
        "1", "2f93cb0589219642c129c764ce29328974400a1a942b068f7b09b466e1899d0c", 1001, 15, 1, ("I1:K1",)
    ),
    "netpay_global_equipment_oct26_v1": _Profile(
        "1",
        "58bb41ec0d273122820822362953565e3aa82c092b75b5377c98c7c06f49c6d7",
        347,
        17,
        2,
        ("J1:M1", "N1:O1", "P1:Q1"),
    ),
    "netpay_ticket97580_equipment_client_oct26_v1": _Profile(
        "1",
        "b22849379cfa03a70edda41744ae0956a5667ccbb8e92b596fcf4e5a84f896da",
        348,
        25,
        3,
        (
            "B2:B3",
            "C2:C3",
            "D2:D3",
            "E2:E3",
            "F2:F3",
            "G2:G3",
            "H2:H3",
            "I2:I3",
            "J2:J3",
            "K2:K3",
            "L2:L3",
            "M2:M3",
            "N2:N3",
            "O2:O3",
            "P2:P3",
            "Q2:Q3",
            "R2:X2",
            "Y2:Y3",
        ),
    ),
}


def _fail(code: str) -> None:
    raise PreviewSourceError(code)


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def _identity(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            _fail("incompatible_identifier_type")
        value = int(value)
    result = str(value).replace("\xa0", " ").strip()
    if not result or result.casefold() == "na":
        return None
    return result


def _ticket_client_identity(value: Any) -> str | None:
    """Treat only the Ticket producer's exact Client ID zero placeholder as missing."""
    if not isinstance(value, bool) and ((isinstance(value, (int, float)) and value == 0) or value == "0"):
        return None
    if isinstance(value, str) and value.strip() == "0":
        return None
    return _identity(value)


def _safe_package(content: bytes) -> bytes:
    try:
        archive = zipfile.ZipFile(BytesIO(content))
    except (zipfile.BadZipFile, ValueError):
        _fail("invalid_xlsx_package")
    with archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ENTRIES:
            _fail("xlsx_package_limit")
        names: set[str] = set()
        folded: set[str] = set()
        expanded = 0
        payloads: dict[str, bytes] = {}
        for entry in entries:
            name = entry.filename.replace("\\", "/")
            parts = name.split("/")
            if (
                not name
                or name.startswith("/")
                or re.match(r"^[a-zA-Z]:", name)
                or any(part in ("", ".", "..") for part in parts)
            ):
                _fail("unsafe_xlsx_path")
            if entry.is_dir() or entry.flag_bits & 1:
                _fail("unsafe_xlsx_entry")
            if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                _fail("unsafe_xlsx_compression")
            if name in names or name.casefold() in folded:
                _fail("xlsx_entry_collision")
            names.add(name)
            folded.add(name.casefold())
            expanded += entry.file_size
            if entry.file_size > MAX_ENTRY_BYTES or expanded > MAX_EXPANDED_BYTES:
                _fail("xlsx_package_limit")
            if entry.file_size and (not entry.compress_size or entry.file_size / entry.compress_size > MAX_RATIO):
                _fail("xlsx_compression_ratio")
            try:
                payloads[name] = archive.read(entry)
            except (OSError, RuntimeError, zipfile.BadZipFile):
                _fail("invalid_xlsx_package")
        if {"[Content_Types].xml", "xl/workbook.xml"} - names:
            _fail("invalid_xlsx_package")
        if any(n.startswith("xl/externalLinks/") or n.casefold().endswith("vbaproject.bin") for n in names):
            _fail("unsafe_xlsx_content")
        try:
            types = ET.fromstring(payloads["[Content_Types].xml"])
            workbook_types = [
                node.attrib.get("ContentType") for node in types if node.attrib.get("PartName") == "/xl/workbook.xml"
            ]
            if workbook_types != [WORKBOOK_TYPE]:
                _fail("unsupported_xlsx_type")
            for name, payload in payloads.items():
                if name.endswith(".rels"):
                    relationships = ET.fromstring(payload)
                    if any(node.attrib.get("TargetMode", "").casefold() == "external" for node in relationships):
                        _fail("external_xlsx_relationship")
        except ET.ParseError:
            _fail("invalid_xlsx_xml")
    return content


def _headers(profile: str, ws: Any) -> None:
    if profile == "netpay_no_usage_oct26_v1":
        expected = ["", "storeid", "storename", "mastername", "distributorname", "estatus", "mesesnouso", "alertas"]
        actual = [_normalized(ws.cell(1, column).value) for column in range(1, 9)]
    else:
        expected = [
            "",
            "serialtpv",
            "estatusdeproducto",
            "numerodecomercio",
            "nombredelcomercio",
            "numerodeterminal",
            "folio",
            "producto",
            "fechadecreacion",
        ]
        row = 2
        actual = [_normalized(ws.cell(row, column).value) for column in range(1, 10)]
    if actual != expected:
        _fail("incompatible_xlsx_header")
    if profile.endswith("client_oct26_v1"):
        expected_tail = [
            "clientid",
            "replegal",
            "correoreplegal",
            "telreplegal",
            "companyid",
            "rfc",
            "razonsocial",
            "branchid",
        ]
        actual_tail = [_normalized(ws.cell(2, column).value) for column in range(10, 18)]
        if actual_tail != expected_tail:
            _fail("incompatible_xlsx_header")


def _parse(source: SourceBytes, *, enforce_allowlist: bool) -> dict[str, Any]:
    spec = PROFILES.get(source.profile)
    if spec is None:
        _fail("unknown_source_profile")
    digest = hashlib.sha256(source.content).hexdigest()
    if digest != source.expected_sha256:
        _fail("source_hash_mismatch")
    if enforce_allowlist and digest != spec.allowed_hash:
        _fail("source_hash_not_allowlisted")
    content = _safe_package(source.content)
    try:
        workbook = load_workbook(BytesIO(content), read_only=False, data_only=False, keep_links=False)
    except Exception as exc:  # openpyxl exposes several producer-specific parse exceptions
        raise PreviewSourceError("invalid_xlsx_workbook") from exc
    try:
        if workbook.sheetnames != ["Sheet1"] or workbook["Sheet1"].sheet_state != "visible":
            _fail("incompatible_xlsx_sheet")
        ws = workbook["Sheet1"]
        if ws.max_row != spec.rows or ws.max_column != spec.columns:
            _fail("incompatible_xlsx_dimensions")
        if tuple(sorted(map(str, ws.merged_cells.ranges))) != tuple(sorted(spec.merged)):
            _fail("incompatible_xlsx_merges")
        _headers(source.profile, ws)
        for row in ws.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    _fail("xlsx_formula_not_allowed")
                if cell.data_type == "e" and not (source.profile.endswith("client_oct26_v1") and cell.column == 18):
                    _fail("unexpected_xlsx_cell_error")
        signature = hashlib.sha256(
            json.dumps(
                {
                    "profile": source.profile,
                    "sheet": "Sheet1",
                    "rows": ws.max_row,
                    "columns": ws.max_column,
                    "header_rows": spec.header_rows,
                    "merged": sorted(spec.merged),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        if source.profile == "netpay_no_usage_oct26_v1":
            business: list[dict[str, Any]] = []
            templates = 0
            for row_number in range(2, ws.max_row + 1):
                number = ws.cell(row_number, 1).value
                store = _identity(ws.cell(row_number, 2).value)
                if number is not None and not isinstance(number, int):
                    _fail("incompatible_xlsx_value_type")
                if store is None:
                    templates += 1
                else:
                    business.append({"store": store, "source_row": row_number})
            return {
                "profile": source.profile,
                "version": spec.version,
                "sha256": digest,
                "signature": signature,
                "business_rows": len(business),
                "template_rows": templates,
                "unique_stores": len({r["store"] for r in business}),
                "rows": business,
            }
        data_start = 4 if source.profile.endswith("client_oct26_v1") else 3
        rows: list[dict[str, Any]] = []
        placeholders = errors = 0
        for row_number in range(data_start, ws.max_row + 1):
            serial = _identity(ws.cell(row_number, 2).value)
            store = _identity(ws.cell(row_number, 4).value)
            terminal = _identity(ws.cell(row_number, 6).value)
            if serial is None and _normalized(ws.cell(row_number, 2).value) == "na":
                placeholders += 1
            client = (
                _ticket_client_identity(ws.cell(row_number, 10).value)
                if source.profile.endswith("client_oct26_v1")
                else None
            )
            contact = False
            if source.profile.endswith("client_oct26_v1"):
                contact = any(_identity(ws.cell(row_number, column).value) for column in (11, 12, 13, 16, 25))
                errors += sum(ws.cell(row_number, column).data_type == "e" for column in range(18, 25))
            rows.append(
                {
                    "store": store,
                    "serial": serial,
                    "terminal": terminal,
                    "client": client,
                    "contact_available": bool(contact),
                    "source_row": row_number,
                }
            )
        distinguishable = [row for row in rows if row["serial"] and row["terminal"]]
        return {
            "profile": source.profile,
            "version": spec.version,
            "sha256": digest,
            "signature": signature,
            "observations": len(rows),
            "placeholders": placeholders,
            "distinguishable_equipment": len(distinguishable),
            "terminals": len({r["terminal"] for r in distinguishable}),
            "serials": len({r["serial"] for r in distinguishable}),
            "explicit_mid_tid": 0,
            "cell_errors": errors,
            "rows": rows,
        }
    finally:
        workbook.close()


def preview_no_usage_recovery_sources(
    organization_id: str, sources: tuple[SourceBytes, ...], *, enforce_allowlist: bool = True
) -> dict[str, Any]:
    """Return a deterministic, aggregate-only C1 preview without side effects."""
    if not organization_id or len(sources) != 3 or {s.profile for s in sources} != set(PROFILES):
        _fail("invalid_preview_request")
    parsed = {source.profile: _parse(source, enforce_allowlist=enforce_allowlist) for source in sources}
    no_usage = parsed["netpay_no_usage_oct26_v1"]
    global_data = parsed["netpay_global_equipment_oct26_v1"]
    ticket = parsed["netpay_ticket97580_equipment_client_oct26_v1"]
    global_relations = {(r["store"], r["terminal"], r["serial"]) for r in global_data["rows"] if r["serial"]}
    ticket_relations = {(r["store"], r["terminal"], r["serial"]) for r in ticket["rows"] if r["serial"]}
    contradictions = len(global_relations ^ ticket_relations)
    by_store: dict[str, list[dict[str, Any]]] = {}
    for row in ticket["rows"]:
        if row["store"] and row["serial"] and row["terminal"]:
            by_store.setdefault(row["store"], []).append(row)
    exact = sum(store in by_store for store in {row["store"] for row in no_usage["rows"]})
    ambiguous = sum(len({(r["serial"], r["terminal"]) for r in rows}) > 1 for rows in by_store.values())
    ticket_equipment = [r for r in ticket["rows"] if r["serial"] and r["terminal"]]
    with_client = sum(bool(r["client"]) for r in ticket_equipment)
    without_store_client = sum(not r["store"] and not r["client"] for r in ticket_equipment)
    public_sources = [{key: value for key, value in parsed[name].items() if key != "rows"} for name in sorted(parsed)]
    result: dict[str, Any] = {
        "query": "PreviewNoUsageRecoverySources",
        "organization_scope": hashlib.sha256(organization_id.encode()).hexdigest(),
        "sources": public_sources,
        "matching": {
            "exact_evidenced": exact,
            "resolution_status": "pending",
            "resolution_reason": "pending_temporality",
            "missing_equipment_match": no_usage["unique_stores"] - exact,
            "equipment_with_client": with_client,
            "missing_store_and_client": without_store_client,
            "ambiguous": ambiguous,
            "contradictory": contradictions,
            "period_cutoff": "unknown",
        },
        "privacy": {"pii_values_returned": False, "contact_availability_only": True},
        "effects": {"database_writes": 0, "events_emitted": 0, "cache_writes": 0},
    }
    result["preview_digest"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result

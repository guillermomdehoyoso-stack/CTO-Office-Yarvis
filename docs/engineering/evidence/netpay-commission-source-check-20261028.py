"""Read-only source audit; no application imports, DB access or workbook writes.

Usage: python this_file.py SETTLEMENT.xlsx CORE.xlsx
Prints minimized aggregates only. Source amounts come from XLSX XML Decimal
tokens, not a binary-float conversion. This is not an implementation gate PASS.
"""
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree as ET

N = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet(path, title):
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheet = next(s for s in wb.find("s:sheets", N) if s.attrib["name"] == title)
        target = rels[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        result = {}
        for row in ET.fromstring(z.read(target)).findall("s:sheetData/s:row", N):
            cells = {}
            for c in row:
                assert c.find("s:f", N) is None, "Formula requires a separate reviewed profile"
                col = "".join(x for x in c.attrib["r"] if x.isalpha())
                v = c.find("s:v", N)
                t = c.attrib.get("t")
                if t == "inlineStr":
                    value = "".join(c.find("s:is", N).itertext())
                elif v is None or v.text is None:
                    value = None
                elif t == "s":
                    value = strings[int(v.text)]
                elif t in (None, "n"):
                    value = Decimal(v.text)
                else:
                    value = v.text
                cells[col] = value
            result[int(row.attrib["r"])] = cells
        return result


def audit(settlement, core):
    rows = read_sheet(settlement, "sheet1")
    headers = [n for n, r in rows.items() if r.get("A") == "Entidad"]
    assert headers == [7, 152, 161]
    expected = {"A": "Entidad", "B": "NOMBRE", "C": "Mes", "D": "Store", "E": "Comercio", "F": "CONCEPTO", "G": "Total Comisiones", "H": "CORREO"}
    assert all(rows[n] == expected for n in headers)
    moves = [(n, r) for n, r in rows.items() if n > 7 and isinstance(r.get("G"), Decimal)]
    assert len(moves) == 291
    assert all(r.get("C") == "Septiembre" and r.get("F") and r.get("A") for _, r in moves)
    positive = sum((r["G"] for _, r in moves if r["G"] > 0), Decimal(0))
    negative = sum((r["G"] for _, r in moves if r["G"] < 0), Decimal(0))
    assert (positive, negative) == (Decimal("25668.64"), Decimal("-8187.85"))
    assert positive + negative == rows[2]["E"] == Decimal("17480.79")
    assert "Septiembre 2026" in rows[5]["A"]
    assert "15 de Octubre" in rows[2]["H"] and "Septiembre 2026" in rows[2]["H"]
    groups = defaultdict(lambda: [0, Decimal(0)])
    for _, r in moves:
        concept = r["F"].split("COMERCIO:")[0].strip()
        key = (r["A"], concept)
        groups[key][0] += 1
        groups[key][1] += r["G"]
    cr = read_sheet(core, "BD Rentabilidad")
    expected_core = {"AP": "Bono de Activación", "AQ": "Comisión - Referenciador", "AR": "Total Comisiones (sin Activación ni Referenciador)", "AS": "Rentabilidad"}
    assert all(cr[1][k] == v for k, v in expected_core.items())
    facts = [r for n, r in cr.items() if n > 1 and r.get("A") is not None]
    assert len(facts) == 348 and len({r["A"] for r in facts}) == 348
    totals = {k: sum((r[k] for r in facts), Decimal(0)) for k in ("S", "AP", "AQ", "AR", "AS")}
    assert all(isinstance(r.get(k), Decimal) for r in facts for k in ("S", "AP", "AQ", "AR", "AS"))
    core_stores = {str(r["A"]) for r in facts}
    matched = [(n, r) for n, r in moves if str(r.get("D")) in core_stores]
    q = lambda x: str(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {
        "scope": "Offline source audit only; not canonical reconciliation or runtime conformance",
        "settlement_sha256": hashlib.sha256(Path(settlement).read_bytes()).hexdigest(),
        "core_sha256": hashlib.sha256(Path(core).read_bytes()).hexdigest(),
        "settlement_bytes": Path(settlement).stat().st_size, "core_bytes": Path(core).stat().st_size,
        "period": "2026-09", "announced_payment_date": "2026-10-15", "currency": "MXN (user-confirmed)",
        "movement_count": len(moves), "header_rows": headers,
        "positive": q(positive), "negative": q(negative), "net": q(positive + negative),
        "entities": dict(Counter(r["A"] for _, r in moves)),
        "missing_store_movements": sum(not r.get("D") for _, r in moves),
        "exact_core_store_matches": len(matched), "unmatched_including_missing": len(moves)-len(matched),
        "groups": [{"entity": e, "concept_family": c, "count": count, "amount": q(amount)} for (e, c), (count, amount) in sorted(groups.items())],
        "core_headers": expected_core, "core_rows": len(facts),
        "core_totals_raw_decimal": {k: str(v) for k, v in totals.items()},
        "core_commission_sum_display": q(totals["AP"] + totals["AQ"] + totals["AR"]),
        "core_zero_sales": sum(r["S"] == 0 for r in facts),
        "core_negative_commissions": sum(r["AP"] + r["AQ"] + r["AR"] < 0 for r in facts),
        "checks": "PASS: headers, 291 movements, signed controls, header net, dates, Core fields and uniqueness",
    }


if __name__ == "__main__":
    print(json.dumps(audit(*sys.argv[1:]), ensure_ascii=True, indent=2))

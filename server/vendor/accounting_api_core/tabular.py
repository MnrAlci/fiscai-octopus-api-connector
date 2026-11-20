"""Generieke tabelschrijvers (CSV, JSON, xlsx zonder extra pakketten) en SHA-256, voor overdrachtspakketten en exports."""
from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def columns(rows: list[dict]) -> list[str]:
    out: list[str] = []
    for r in rows:
        for k in r:
            if k not in out:
                out.append(k)
    return out


def cell(v: Any) -> Any:
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return "" if v is None else v


def write_csv(p: Path, rows: list[dict]) -> None:
    cols = columns(rows) or ["leeg"]
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([cell(r.get(c)) for c in cols])


def write_json(p: Path, rows: list[dict], meta: dict | None = None) -> None:
    p.write_text(json.dumps({**(meta or {}), "rows": rows}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _ref(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def write_xlsx(p: Path, rows: list[dict], sheet: str = "Data") -> None:
    """Minimale xlsx (inline strings). Alles als tekst: exact zoals de bron het gaf; deterministisch (vaste zip-datum)."""
    cols = columns(rows) or ["leeg"]
    data = [cols] + [[cell(r.get(c)) for c in cols] for r in rows]
    body = "".join(f'<row r="{ri}">' + "".join(f'<c r="{_ref(ci)}{ri}" t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'
                                               for ci, v in enumerate(row)) + "</row>" for ri, row in enumerate(data, 1))
    parts = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="{escape(sheet[:31])}" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{body}</sheetData></worksheet>',
    }
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        for n, t in parts.items():
            z.writestr(zipfile.ZipInfo(n, (2026, 1, 1, 0, 0, 0)), t)


WRITERS = {"csv": write_csv, "json": write_json, "xlsx": write_xlsx}

"""Bouwt server/octopus_mcp/spec_endpoints.py en spec/endpoints.json uit de officiële Octopus REST OpenAPI-spec.

Gebruik: python scripts/build_endpoints.py PAD_NAAR/openapi.json
De officiële spec staat op https://service.inaras.be/octopus-rest-api/v1/openapi.json (publiek, zonder login).
Het script leest alleen feiten uit de spec: methode, pad, samenvatting, parameters en 'Maximum allowed calls per day'.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READ_POST = re.compile(r"^/dossiers/\{dossierId\}/reports/(accounts|clients|suppliers|costcentres)/(open|history)$")


def limits(desc: str) -> dict:
    txt = re.sub(r"<[^>]+>", " ", desc or "")
    out = {}
    m = re.search(r"without search parameters\s*:\s*(\d+)\s*with search parameters\s*:\s*(\d+)", txt)
    if m:
        return {"default": int(m.group(1)), "search": int(m.group(2))}
    m = re.search(r"Maximum allowed calls per day\s*:?\s*(\d+)", txt)
    if m:
        out["default"] = int(m.group(1))
    return out


def classify(method: str, path: str) -> str:
    if path == "/authentication":
        return "auth"
    if path == "/dossiers" and method == "post":
        return "auth"
    if method == "get":
        return "read"
    if method == "post" and READ_POST.match(path):
        return "read"
    return "write"


def main(spec_path: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    ops = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            params = [{"name": p["name"], "in": p["in"], "required": bool(p.get("required")), "type": (p.get("schema") or {}).get("type", "string")}
                      for p in op.get("parameters", [])]
            body = None
            for c in (op.get("requestBody") or {}).get("content", {}).values():
                body = (c.get("schema") or {}).get("$ref", "").split("/")[-1] or (c.get("schema") or {}).get("type")
            ops.append({"method": method.upper(), "path": path, "summary": (op.get("summary") or "").split("<")[0].strip(),
                        "kind": classify(method, path), "limits": limits(op.get("description", "")), "params": params, "body": body})
    meta = {"title": spec["info"]["title"], "version": spec["info"]["version"], "server": spec["servers"][0]["url"],
            "paths": len(spec["paths"]), "operations": len(ops), "source": "https://service.inaras.be/octopus-rest-api/v1/openapi.json"}
    (ROOT / "spec").mkdir(exist_ok=True)
    (ROOT / "spec" / "endpoints.json").write_text(json.dumps({"meta": meta, "operations": ops}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    py = ('"""GEGENEREERD door scripts/build_endpoints.py uit de officiële Octopus REST OpenAPI-spec. Niet met de hand wijzigen."""\n'
          f"META = {json.dumps(meta, ensure_ascii=False)!r}\n"
          f"OPERATIONS = {json.dumps(ops, ensure_ascii=False)!r}\n")
    (ROOT / "server" / "octopus_mcp" / "spec_endpoints.py").write_text(py, encoding="utf-8")
    print(f"{meta['paths']} paden, {meta['operations']} operaties, "
          f"{sum(1 for o in ops if o['kind'] == 'read')} lezen, {sum(1 for o in ops if o['kind'] == 'write')} schrijven")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Gebruik: python scripts/build_endpoints.py PAD/octopus-rest-api.openapi.json\n"
                         "Download de officiële spec eerst via https://service.inaras.be/octopus-rest-api/v1/openapi.json (zie spec/README.md).")
    main(sys.argv[1])

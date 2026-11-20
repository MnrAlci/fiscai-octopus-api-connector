"""Bouwt de Postman-collectie (v2.1) en -omgeving uit spec/endpoints.json (officiële Octopus REST-spec).

Alleen aanmelden, dossiertoken en LEES-operaties; geen schrijf-, verwijder-, Management- of file-import-calls.
Geen geheimen: alle waarden zijn plaatshouders die u in uw eigen Postman-omgeving invult.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "FISCAi Octopus API Connector"
ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"
NS = uuid.UUID("6f1d3b8e-0c1e-4d0a-9b8a-0c7c0c1f0a01")

EXAMPLES = {"bookyearId": "{{bookyearId}}", "journalTypeId": "-1", "modifiedTimeStamp": "{{modifiedTimeStamp}}", "localeId": "{{localeId}}",
            "dossierId": "{{dossierId}}", "errorCode": "1"}
BODIES = {
    "OpenAccountQueryData": {"fromBookyearKey": {"id": "{{bookyearId}}"}, "toBookyearKey": {"id": "{{bookyearId}}"}, "fromBookyearPeriodNr": 1, "toBookyearPeriodNr": 12},
    "OpenRelationQueryData": {"fromBookyearKey": {"id": "{{bookyearId}}"}, "toBookyearKey": {"id": "{{bookyearId}}"}, "fromBookyearPeriodNr": 1, "toBookyearPeriodNr": 12},
}


def uid(s: str) -> str:
    return str(uuid.uuid5(NS, s))


def folder_of(path: str) -> str:
    parts = [p for p in path.split("/") if p and not p.startswith("{")]
    if parts[:1] == ["dossiers"] and len(parts) > 1:
        return parts[1]
    return parts[0] if parts else "root"


def pm_url(path: str, params: list[dict]) -> dict:
    raw_path = re.sub(r"\{(\w+)\}", r":\1", path)
    q = [{"key": p["name"], "value": EXAMPLES.get(p["name"], ""), "disabled": not p["required"]} for p in params if p["in"] == "query"]
    var = [{"key": p["name"], "value": EXAMPLES.get(p["name"], "{{" + p["name"] + "}}")} for p in params if p["in"] == "path"]
    url = {"raw": "{{baseUrl}}" + raw_path + ("?" + "&".join(f"{x['key']}={x['value']}" for x in q if not x["disabled"]) if any(not x["disabled"] for x in q) else ""),
           "host": ["{{baseUrl}}"], "path": [s for s in raw_path.split("/") if s]}
    if q:
        url["query"] = q
    if var:
        url["variable"] = var
    return url


def request(op: dict) -> dict:
    hdr = [{"key": "Accept", "value": "application/json"}]
    for p in op["params"]:
        if p["in"] == "header":
            hdr.append({"key": p["name"], "value": {"dossierToken": "{{dossierToken}}", "Token": "{{token}}", "softwareHouseUuid": "{{softwareHouseUuid}}"}.get(p["name"], "")})
    lim = op["limits"].get("default")
    desc = f"{op['summary']}. Daglimiet volgens de officiële spec: {lim if lim else 'niet vermeld'} per dag" + (
        f" ({op['limits']['search']} met zoekparameters)" if op["limits"].get("search") else "") + ". Lees-operatie."
    req = {"method": op["method"], "header": hdr, "url": pm_url(op["path"], op["params"]), "description": desc}
    if op["method"] == "POST" and op["body"]:
        hdr.append({"key": "Content-Type", "value": "application/json"})
        req["body"] = {"mode": "raw", "raw": json.dumps(BODIES.get(op["body"], {}), indent=2), "options": {"raw": {"language": "json"}}}
    return {"id": uid(op["method"] + op["path"]), "name": f"{op['method']} {op['path']}", "request": req}


def main() -> None:
    spec = json.loads((ROOT / "spec" / "endpoints.json").read_text(encoding="utf-8"))
    ops = spec["operations"]
    auth = {"id": uid("auth"), "name": "0. Aanmelden (token, 10 min geldig)", "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": [
        "const j = pm.response.json();", "if (j.token) { pm.collectionVariables.set('token', j.token); }"]}}],
        "request": {"method": "POST", "header": [{"key": "softwareHouseUuid", "value": "{{softwareHouseUuid}}"}, {"key": "Content-Type", "value": "application/json"},
                                                  {"key": "Accept", "value": "application/json"}],
                    "body": {"mode": "raw", "raw": json.dumps({"user": "{{user}}", "password": "{{password}}"}, indent=2), "options": {"raw": {"language": "json"}}},
                    "url": {"raw": "{{baseUrl}}/authentication", "host": ["{{baseUrl}}"], "path": ["authentication"]},
                    "description": "POST /authentication met header softwareHouseUuid en body {user, password}. Antwoord {token}, 10 minuten geldig."}}
    dtok = {"id": uid("dossiertoken"), "name": "1. Dossiertoken (10 min geldig)", "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": [
        "const j = pm.response.json();", "if (j.Dossiertoken) { pm.collectionVariables.set('dossierToken', j.Dossiertoken); }"]}}],
        "request": {"method": "POST", "header": [{"key": "Token", "value": "{{token}}"}, {"key": "Accept", "value": "application/json"}],
                    "url": {"raw": "{{baseUrl}}/dossiers?dossierId={{dossierId}}&localeId={{localeId}}", "host": ["{{baseUrl}}"], "path": ["dossiers"],
                            "query": [{"key": "dossierId", "value": "{{dossierId}}"}, {"key": "localeId", "value": "{{localeId}}"}]},
                    "description": "POST /dossiers?dossierId=&localeId= met header Token. Antwoord {Dossiertoken}; daarna header dossierToken. Daglimiet 150."}}
    folders: dict[str, list] = {}
    for op in ops:
        if op["kind"] != "read":
            continue
        folders.setdefault(folder_of(op["path"]), []).append(request(op))
    items = [auth, dtok] + [{"id": uid("f:" + f), "name": f, "item": sorted(v, key=lambda x: x["name"])} for f, v in sorted(folders.items())]
    n = sum(len(v) for v in folders.values())
    col = {"info": {"_postman_id": uid("collection"), "name": NAME,
                    "description": (f"Alleen-lezen Postman-collectie voor de Octopus REST API, gegenereerd uit de officiële OpenAPI-spec "
                                    f"({spec['meta']['source']}, versie {spec['meta']['version']}). {n} lees-operaties plus aanmelden en dossiertoken. "
                                    "Let op: zeer lage daglimieten per endpoint (bv. 2 per dag voor rekeningen en btw-codes). Geen sandbox: gebruik het demodossier. "
                                    "Geen schrijf-, Management- of file-import-calls. Bedoeld voor Belgische boekhouders; buiten België: verifieer zelf de lokale regels. " + ATTR),
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
           "item": items,
           "variable": [{"key": k, "value": v} for k, v in (("baseUrl", spec["meta"]["server"]), ("token", ""), ("dossierToken", ""))]}
    env = {"id": uid("env"), "name": f"{NAME} (plaatshouders)", "values": [
        {"key": "baseUrl", "value": spec["meta"]["server"], "enabled": True},
        {"key": "softwareHouseUuid", "value": "", "type": "secret", "enabled": True},
        {"key": "user", "value": "", "type": "secret", "enabled": True},
        {"key": "password", "value": "", "type": "secret", "enabled": True},
        {"key": "dossierId", "value": "", "enabled": True},
        {"key": "localeId", "value": "1", "enabled": True},
        {"key": "bookyearId", "value": "", "enabled": True},
        {"key": "modifiedTimeStamp", "value": "1980-01-01 00:00:00.000", "enabled": True}], "_postman_variable_scope": "environment"}
    out = ROOT / "postman"
    out.mkdir(exist_ok=True)
    (out / "FISCAi-Octopus-API-Connector.postman_collection.json").write_text(json.dumps(col, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "FISCAi-Octopus-API-Connector.postman_environment.json").write_text(json.dumps(env, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Postman: {n} lees-operaties in {len(folders)} mappen")


if __name__ == "__main__":
    main()

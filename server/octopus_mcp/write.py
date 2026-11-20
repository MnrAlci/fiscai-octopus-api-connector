"""Schrijven naar Octopus: standaard UIT. Alleen actief met OCTOPUS_WRITE_ENABLED=true, en dan nog in twee stappen:

1. ``octopus_schrijf_voorstel``: controleert en toont exact wat er verstuurd zou worden (geen call), met een bevestigingscode (10 min geldig).
2. ``octopus_schrijf_bevestigen``: verstuurt pas met die code; maximaal OCTOPUS_WRITE_MAX_PER_DAY per dag.

Toegelaten (officiële spec, BEVESTIGD): relatie bijwerken/aanmaken, aankoop/verkoop- en financiële/diverse boekingen aanmaken of bijwerken,
afpunting toevoegen. Nooit: verwijderen, boekjaren afsluiten, CODA/SODA-import, facturen versturen, Management API of file import.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time

from .endpoints import BY_ID
from .errors import OctopusRefused, parse_error

ALLOWED = {
    "relatie_bijwerken": ("PUT", "/dossiers/{dossierId}/relations"),
    "aankoop_verkoop_aanmaken": ("POST", "/dossiers/{dossierId}/buysellbookings"),
    "aankoop_verkoop_bijwerken": ("PUT", "/dossiers/{dossierId}/buysellbookings"),
    "financieel_divers_aanmaken": ("POST", "/dossiers/{dossierId}/financialdiversbookings"),
    "financieel_divers_bijwerken": ("PUT", "/dossiers/{dossierId}/financialdiversbookings"),
    "afpunting_toevoegen": ("POST", "/dossiers/{dossierId}/balancings"),
}
TTL = 600


def register_write(t) -> None:
    pending: dict[str, dict] = {}
    done_today: dict[str, int] = {}

    def voorstel(a: dict) -> dict:
        actie = a["actie"]
        method, path = ALLOWED[actie]
        if f"{method} {path}" not in BY_ID or BY_ID[f"{method} {path}"]["kind"] != "write":
            raise OctopusRefused("Actie niet gevonden in de officiële spec.")
        d = int(a["dossier_id"])
        t.client.check_dossier(d)
        body = a["gegevens"]
        digest = hashlib.sha256(json.dumps([actie, d, body], sort_keys=True).encode()).hexdigest()[:16]
        code = secrets.token_hex(4)
        pending[code] = {"actie": actie, "dossier_id": d, "body": body, "digest": digest, "t": time.time()}
        return {"status": "voorstel", "actie": actie, "endpoint": f"{method} {path}", "dossier_id": d, "gegevens": body, "controle": digest,
                "bevestigingscode": code, "geldig_seconden": TTL, "waarschuwing": "Er is nog NIETS verstuurd. Controleer de gegevens en bevestig met de code."}

    def bevestigen(a: dict) -> dict:
        p = pending.pop(a["bevestigingscode"], None)
        if not p or time.time() - p["t"] > TTL:
            raise OctopusRefused("Onbekende of verlopen bevestigingscode; maak een nieuw voorstel.")
        day = time.strftime("%Y-%m-%d")
        if done_today.get(day, 0) >= t.client.s.write_max_per_day:
            raise OctopusRefused("Maximum aantal schrijfacties voor vandaag bereikt (OCTOPUS_WRITE_MAX_PER_DAY).")
        method, path = ALLOWED[p["actie"]]
        op = f"{method} {path}"
        lim = (BY_ID[op].get("limits") or {}).get("default")
        if lim:
            t.client.quota.limits.setdefault(op, lim)
        t.client.quota.check(op)
        t.client.quota.record(op)
        r = t.client.rest.request(method, path.replace("{dossierId}", str(p["dossier_id"])), json=p["body"],
                                  headers={"dossierToken": t.client._dossier_token(p["dossier_id"]), "Content-Type": "application/json"})
        t.client.calls.append(f"{method} {path}")
        if r.status_code >= 400:
            raise parse_error(r.status_code, f"{method} {path}", r.content)
        done_today[day] = done_today.get(day, 0) + 1
        return {"status": "verstuurd", "actie": p["actie"], "http_status": r.status_code, "controle": p["digest"],
                "antwoord": r.json() if r.content[:1] in (b"{", b"[") else None}

    W = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    t.add("octopus_schrijf_voorstel", "Schrijfvoorstel (stap 1)", "Bereidt een schrijfactie voor en toont exact wat er verstuurd zou worden. Verstuurt niets.",
          {"type": "object", "properties": {"actie": {"type": "string", "enum": sorted(ALLOWED)}, "dossier_id": {"type": "integer"},
                                            "gegevens": {"type": "object", "description": "JSON-body volgens de officiële spec"}},
           "required": ["actie", "dossier_id", "gegevens"], "additionalProperties": False}, voorstel, {**W, "readOnlyHint": True, "openWorldHint": False})
    t.add("octopus_schrijf_bevestigen", "Schrijfactie bevestigen (stap 2)", "Verstuurt een eerder voorstel naar Octopus met de bevestigingscode.",
          {"type": "object", "properties": {"bevestigingscode": {"type": "string"}}, "required": ["bevestigingscode"], "additionalProperties": False}, bevestigen,
          {**W, "destructiveHint": True})

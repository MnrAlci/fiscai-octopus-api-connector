"""Register van de Octopus REST-endpoints die de connector gebruikt, met daglimieten uit de officiële spec.

* Daglimieten komen uit ``spec_endpoints.py`` (gegenereerd uit de OpenAPI-spec, 'Maximum allowed calls per day').
* Cache-vervaltijd volgt de daglimiet: hoe lager de limiet, hoe langer de cache (stamdata met 2 calls/dag: 12 uur).
* Alleen-lezen: GET-endpoints en de POST-rapporten (open posten, historiek). Schrijfendpoints staan in ``write.py`` (standaard uit).
* De Management API, de file import API en betaalde modules worden nooit gebruikt.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from .spec_endpoints import META as _META_JSON, OPERATIONS as _OPS_JSON

META = json.loads(_META_JSON)
OPERATIONS = json.loads(_OPS_JSON)
BY_ID = {f"{o['method']} {o['path']}": o for o in OPERATIONS}


@dataclass(frozen=True)
class Endpoint:
    key: str
    method: str
    path: str
    title: str

    @property
    def op_id(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def spec(self) -> dict:
        return BY_ID[self.op_id]

    def limit(self, search: bool = False) -> Optional[int]:
        lim = self.spec.get("limits") or {}
        return lim.get("search") if search and "search" in lim else lim.get("default")

    def quota_key(self, search: bool = False) -> str:
        return self.op_id + (" [search]" if search and "search" in (self.spec.get("limits") or {}) else "")

    def cache_ttl(self, search: bool = False) -> int:
        return ttl_for(self.limit(search))


def ttl_for(limit: Optional[int]) -> int:
    if limit is None:
        return 300
    if limit <= 2:
        return 12 * 3600
    if limit <= 10:
        return 6 * 3600
    if limit <= 24:
        return 3600
    if limit <= 48:
        return 1800
    if limit <= 150:
        return 600
    return 300


D = "/dossiers/{dossierId}"
_E = [
    ("version", "GET", "/about/version", "API-versie"),
    ("whoami", "GET", "/authentication", "Aangemelde gebruiker"),
    ("authenticate", "POST", "/authentication", "Aanmelden (token, 10 min)"),
    ("dossiers", "GET", "/dossiers", "Dossiers"),
    ("dossier_token", "POST", "/dossiers", "Dossiertoken (10 min)"),
    ("bookyears", "GET", f"{D}/bookyears", "Boekjaren"),
    ("bookyear", "GET", f"{D}/bookyears/{{bookyearId}}", "Boekjaar (detail)"),
    ("journals", "GET", f"{D}/bookyears/{{bookyearId}}/journals", "Dagboeken"),
    ("journal_A", "GET", f"{D}/bookyears/{{bookyearId}}/journals/A/{{sequenceNumber}}", "Aankoopdagboek"),
    ("journal_V", "GET", f"{D}/bookyears/{{bookyearId}}/journals/V/{{sequenceNumber}}", "Verkoopdagboek"),
    ("journal_F", "GET", f"{D}/bookyears/{{bookyearId}}/journals/F/{{sequenceNumber}}", "Financieel dagboek"),
    ("journal_D", "GET", f"{D}/bookyears/{{bookyearId}}/journals/D/{{sequenceNumber}}", "Diverse verrichtingen"),
    ("journal_L", "GET", f"{D}/bookyears/{{bookyearId}}/journals/L/{{sequenceNumber}}", "Leveringsdagboek"),
    ("journal_balance", "GET", f"{D}/bookyears/{{bookyearId}}/journals/{{journalKey}}", "Saldo financieel dagboek"),
    ("journals_modified", "GET", f"{D}/journals/modified", "Gewijzigde dagboeken"),
    ("bookings_modified", "GET", f"{D}/bookyears/{{bookyearId}}/bookings/modified", "Gewijzigde boekingslijnen"),
    ("buysell", "GET", f"{D}/buysellbookings", "Aankoop/verkoop-boeking"),
    ("buysell_modified", "GET", f"{D}/buysellbookings/modified", "Gewijzigde aankoop/verkoop-boekingen"),
    ("findiv", "GET", f"{D}/financialdiversbookings", "Financiële/diverse boeking"),
    ("findiv_modified", "GET", f"{D}/financialdiversbookings/modified", "Gewijzigde financiële/diverse boekingen"),
    ("accounts", "GET", f"{D}/accounts", "Grootboekrekeningen"),
    ("accounts_modified", "GET", f"{D}/accounts/modified", "Gewijzigde rekeningen"),
    ("amounts_modified", "GET", f"{D}/accounts/amounts/modified", "Saldi per rekening per periode"),
    ("history_accounts", "POST", f"{D}/reports/accounts/history", "Rekeninghistoriek"),
    ("history_clients", "POST", f"{D}/reports/clients/history", "Klantenhistoriek"),
    ("history_suppliers", "POST", f"{D}/reports/suppliers/history", "Leveranciershistoriek"),
    ("history_costcentres", "POST", f"{D}/reports/costcentres/history", "Kostenplaatshistoriek"),
    ("open_accounts", "POST", f"{D}/reports/accounts/open", "Openstaande posten per rekening"),
    ("open_clients", "POST", f"{D}/reports/clients/open", "Openstaande posten klanten"),
    ("open_suppliers", "POST", f"{D}/reports/suppliers/open", "Openstaande posten leveranciers"),
    ("bank_invoices", "GET", f"{D}/bank/invoices", "Onafgepunte facturen"),
    ("balancings_modified", "GET", f"{D}/balancings/modified", "Gewijzigde afpuntingen"),
    ("relations", "GET", f"{D}/relations", "Relaties"),
    ("relations_modified", "GET", f"{D}/relations/modified", "Gewijzigde relaties"),
    ("vatcodes", "GET", f"{D}/vatcodes", "Btw-codes"),
    ("currencies", "GET", f"{D}/currencies", "Munten"),
    ("costcentres", "GET", f"{D}/costcentres", "Kostenplaatsen"),
    ("costcentres_active", "GET", f"{D}/costcentres/active", "Actieve kostenplaatsen"),
    ("customfields", "GET", f"{D}/customfields", "Vrije velden"),
    ("products", "GET", f"{D}/products", "Producten"),
    ("productgroups", "GET", f"{D}/productgroups", "Productgroepen"),
    ("paymentlist", "GET", f"{D}/bank/paymentlist", "Betaallijst"),
    ("envelopes", "GET", f"{D}/bank/enveloppes", "Betalingsenveloppes"),
    ("envelope", "GET", f"{D}/bank/enveloppes/{{enveloppeKeyId}}", "Betalingsenveloppe (detail)"),
    ("invoices_modified", "GET", f"{D}/invoices/modified", "Gewijzigde facturen (factuurmodule)"),
    ("invoice", "GET", f"{D}/invoices", "Factuur (factuurmodule)"),
    ("deliverynotes_modified", "GET", f"{D}/deliverynotes/modified", "Gewijzigde leveringsbonnen"),
    ("rappels", "GET", f"{D}/rappels", "Rappels"),
    ("error_sample", "GET", "/error", "Voorbeeld-foutobject voor een foutcode"),
]
ENDPOINTS = {k: Endpoint(k, m, p, t) for k, m, p, t in _E}


def get(key: str) -> Endpoint:
    return ENDPOINTS[key]


def is_read_only(ep: Endpoint) -> bool:
    return ep.spec["kind"] in ("read", "auth")


def quota_limits() -> dict[str, int]:
    out = {}
    for ep in ENDPOINTS.values():
        lim = ep.spec.get("limits") or {}
        if "default" in lim:
            out[ep.quota_key(False)] = lim["default"]
        if "search" in lim:
            out[ep.quota_key(True)] = lim["search"]
    return out

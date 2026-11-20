"""MCP-tools van de FISCAi Octopus API Connector. Alles alleen lezen, tenzij OCTOPUS_WRITE_ENABLED bewust aan staat (zie write.py).

Elke tool zegt in zijn beschrijving welke Octopus-endpoint(s) hij gebruikt en wat de daglimiet is. Lijsten worden afgekapt op
``max_rijen`` (standaard 200) om de context klein te houden; exports schrijven altijd alles naar bestanden.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Callable, Optional

from accounting_api_core import analytics, trial_balance

from . import normalize as N
from .client import OctopusClient
from .errors import OctopusApiError
from .sync import OctopusSync

SOURCE = "Octopus (alleen lezen)"
RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
LOCAL = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

# ------------------------------------------------------------------ schema-bouwstenen
S_DOSSIER = {"type": "integer", "description": "Octopus dossier-id (zie octopus_dossiers)"}
S_BY = {"type": "integer", "description": "Boekjaar-id (bookyearKey.id, zie octopus_boekjaren). Leeg = recentste boekjaar of zie 'jaar'."}
S_JAAR = {"type": "integer", "description": "Kalenderjaar waarin het boekjaar eindigt (alternatief voor boekjaar_id)"}
S_VERS = {"type": "boolean", "description": "Cache overslaan en opnieuw ophalen (kost een call van de daglimiet)"}
S_MAX = {"type": "integer", "minimum": 1, "maximum": 5000, "description": "Maximum aantal rijen in het antwoord (standaard 200)"}
S_TS = {"type": "string", "description": "Gewijzigd sinds: JJJJ-MM-DD of JJJJ-MM-DD UU:MM:SS (tijdzone van de server: verifieer actuele regel)"}
S_DAGBOEK = {"type": "string", "description": "Dagboekcode (journalKey)"}
S_DOCNR = {"type": "integer", "description": "Documentnummer (documentSequenceNr)"}


def obj(props: dict, required: tuple = ()) -> dict:
    return {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}


def ts(v: Optional[str]) -> Optional[str]:
    """Zet een datum/tijd om naar het formaat uit de spec: 'JJJJ-MM-DD UU:MM:SS.000'."""
    if v in (None, ""):
        return None
    s = str(v).strip().replace("T", " ")
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2})(?::(\d{2}))?(?:\.(\d{1,3}))?)?", s)
    if not m:
        raise ValueError("Tijdstempel als JJJJ-MM-DD of JJJJ-MM-DD UU:MM:SS.")
    d, hm, sec, ms = m.groups()
    date.fromisoformat(d)
    return f"{d} {hm or '00:00'}:{sec or '00'}.{(ms or '000').ljust(3, '0')}"


def cap(rows: list, n: Optional[int]) -> dict:
    n = int(n or 200)
    return {"aantal": len(rows), "getoond": min(n, len(rows)), "afgekapt": len(rows) > n, "rijen": rows[:n]}


class Tools:
    def __init__(self, client: Optional[OctopusClient] = None, today: Optional[Callable[[], date]] = None) -> None:
        self._client = client
        self._sync: Optional[OctopusSync] = None
        self.today = today or date.today
        self.defs: dict[str, dict] = {}
        self.handlers: dict[str, Callable[[dict], Any]] = {}
        self._register()

    # ------------------------------------------------------------------ infrastructuur
    @property
    def client(self) -> OctopusClient:
        if self._client is None:
            self._client = OctopusClient()
        return self._client

    @property
    def sync(self) -> OctopusSync:
        if self._sync is None:
            self._sync = OctopusSync(self.client)
        return self._sync

    def add(self, name: str, title: str, desc: str, schema: dict, fn: Callable[[dict], Any], ann: dict = RO) -> None:
        self.defs[name] = {"name": name, "title": title, "description": desc, "inputSchema": schema, "annotations": dict(ann)}
        self.handlers[name] = fn

    def list(self) -> list[dict]:
        return list(self.defs.values())

    def call(self, name: str, args: Optional[dict]) -> Any:
        if name not in self.handlers:
            raise KeyError(f"Onbekende tool: {name}")
        args = dict(args or {})
        from accounting_api_core.cli_base import validate_args
        problems = validate_args(self.defs[name]["inputSchema"], args)
        if problems:
            raise ValueError("; ".join(problems))
        return self.handlers[name](args)

    # ------------------------------------------------------------------ hulpfuncties
    def bookyears(self, d: int, fresh: bool = False) -> list[dict]:
        return [N.bookyear(b) for b in (self.client.call("bookyears", dossier_id=d, fresh=fresh) or [])]

    def resolve_by(self, d: int, a: dict) -> dict:
        bys = self.bookyears(d)
        if not bys:
            raise ValueError("Geen boekjaren gevonden voor dit dossier.")
        if a.get("boekjaar_id") is not None:
            for b in bys:
                if b["boekjaar_id"] == int(a["boekjaar_id"]):
                    return b
            raise ValueError("Boekjaar-id niet gevonden in dit dossier.")
        if a.get("jaar") is not None:
            for b in bys:
                if str(b.get("einde") or "")[:4] == str(a["jaar"]):
                    return b
            raise ValueError(f"Geen boekjaar dat eindigt in {a['jaar']}.")
        return sorted(bys, key=lambda b: str(b.get("start") or ""))[-1]

    @staticmethod
    def period_range(by: dict) -> tuple[int, int]:
        ps = [p["periode"] for p in by.get("perioden") or [] if p.get("periode") is not None]
        return (min(ps), max(ps)) if ps else (1, 12)    # zonder periodelijst: 1-12 (verifieer actuele regel)

    def client_settings_write_enabled(self) -> bool:
        """Schrijftools alleen registreren als OCTOPUS_WRITE_ENABLED aan staat (zonder netwerk, zonder client te bouwen)."""
        if self._client is not None:
            return self._client.s.write_enabled
        from .config import TRUE
        import os
        return str(os.environ.get("OCTOPUS_WRITE_ENABLED", "")).strip().lower() in TRUE

    def _out(self, data: dict) -> dict:
        return {"bron": SOURCE, **data}

    def _names(self, d: int) -> dict:
        """Relatienamen uit de lokale synchronisatie (kost geen call)."""
        recs = self.sync.state.records(f"{d}:relations")
        return {N.relation(r)["relatie_id"]: N.relation(r)["naam"] for r in recs.values()}

    # ------------------------------------------------------------------ samengestelde lezingen
    def tb(self, a: dict) -> dict:
        d = int(a["dossier_id"])
        by = self.resolve_by(d, a)
        accs = self.sync.accounts(d, by["boekjaar_id"], refresh=bool(a.get("vers")))
        amts = [x for x in self.sync.amounts(d, refresh=bool(a.get("vers"))) if x["boekjaar_id"] == by["boekjaar_id"]]
        res = trial_balance.build(accs, amts, up_to_period=a.get("tot_periode"), from_period=a.get("vanaf_periode"),
                                  mode=self.client.s.amounts_mode, include_zero=bool(a.get("inclusief_nul")))
        return {"dossier_id": d, "boekjaar": {k: by[k] for k in ("boekjaar_id", "omschrijving", "start", "einde", "afgesloten")}, **res,
                "_verifieer": "Proefbalans samengesteld uit saldi per rekening per periode (geen eigen endpoint bij Octopus); "
                              f"modus '{self.client.s.amounts_mode}' en tekenconventie: verifieer actuele regel."}

    def open_items(self, d: int, soort: str, a: dict) -> tuple[list[dict], dict]:
        bys = sorted(self.bookyears(d), key=lambda b: str(b.get("start") or ""))
        if not bys:
            raise ValueError("Geen boekjaren gevonden voor dit dossier.")
        first = bys[0] if a.get("van_boekjaar_id") is None else next(b for b in bys if b["boekjaar_id"] == int(a["van_boekjaar_id"]))
        last = bys[-1] if a.get("tot_boekjaar_id") is None else next(b for b in bys if b["boekjaar_id"] == int(a["tot_boekjaar_id"]))
        body = {"fromBookyearKey": {"id": first["boekjaar_id"]}, "toBookyearKey": {"id": last["boekjaar_id"]},
                "fromBookyearPeriodNr": self.period_range(first)[0], "toBookyearPeriodNr": self.period_range(last)[1]}
        if a.get("relatie_id") is not None:
            body["relationId"] = int(a["relatie_id"])
        key = {"debiteuren": "open_clients", "crediteuren": "open_suppliers"}[soort]
        raw = self.client.call(key, dossier_id=d, body=body, fresh=bool(a.get("vers"))) or []
        peil = a.get("peildatum") or self.today().isoformat()
        names = self._names(d)
        rows = []
        for o in raw:
            r = N.open_item(o, soort, peil)
            if not r["open_bedrag"]:
                continue        # volledig afgepunt (open bedrag 0): geen openstaande post
            r["relatie"] = names.get(r["relatie_id"])
            rows.append(r)
        return rows, body

    def kpis(self, a: dict) -> dict:
        d = int(a["dossier_id"])
        args = {k: a[k] for k in ("dossier_id", "boekjaar_id", "jaar", "vers") if k in a}
        per = a.get("periode")
        if per not in (None, "", "jaar"):
            month = None
            if (m := re.fullmatch(r"(\d{4})-(\d{2})", str(per))):          # 'JJJJ-MM'
                if "boekjaar_id" not in args:
                    args["jaar"] = int(m.group(1))
                month = int(m.group(2))
            elif (m := re.fullmatch(r"maand:(\d{1,2})", str(per))):         # automatisering
                month = int(m.group(1))
            elif (m := re.fullmatch(r"kwartaal:([1-4])", str(per))):
                month = 3 * int(m.group(1))
            if month is not None:                   # periode van het boekjaar die in die kalendermaand start (zonder datums: maandnummer)
                by = self.resolve_by(d, args)
                hit = [p["periode"] for p in by.get("perioden") or [] if str(p.get("start") or "")[5:7] == f"{month:02d}"]
                args["tot_periode"] = hit[0] if hit else month
            elif str(per).isdigit():
                args["tot_periode"] = int(per)
            else:
                raise ValueError("periode is 'jaar', 'JJJJ-MM', 'maand:M', 'kwartaal:K' of een periodenummer van het boekjaar.")
        tb = self.tb(args)
        out = {"dossier_id": d, "boekjaar": tb["boekjaar"], "periode": per or "jaar", **analytics.kpis(tb["rows"]),
               "proefbalans_in_evenwicht": tb["in_evenwicht"]}
        if a.get("inclusief_open_posten", True):
            for soort, label in (("debiteuren", "open_debiteuren"), ("crediteuren", "open_crediteuren")):
                try:
                    rows, _ = self.open_items(d, soort, {"vers": a.get("vers")})
                    ag = analytics.aging(rows, date.fromisoformat(self.today().isoformat()))
                    out[label] = {"totaal": ag["totaal_positief"], "vervallen": ag["vervallen_totaal"], "aantal": len(rows)}
                except OctopusApiError as exc:
                    out[label] = {"totaal": None, "vervallen": None, "fout": exc.as_dict()}
        if a.get("vergelijk_vorige_periode") and tb["boekjaar"].get("start"):
            bys = sorted(self.bookyears(d), key=lambda b: str(b.get("start") or ""))
            idx = [b["boekjaar_id"] for b in bys].index(tb["boekjaar"]["boekjaar_id"])
            if idx > 0:
                prev = self.tb({"dossier_id": d, "boekjaar_id": bys[idx - 1]["boekjaar_id"], **({"tot_periode": args["tot_periode"]} if "tot_periode" in args else {})})
                pk = analytics.kpis(prev["rows"])
                out["vorige_periode"] = {k: pk[k] for k in ("omzet", "kosten", "resultaat", "liquide_middelen", "bruto_marge")}
        return self._out(out)

    # ------------------------------------------------------------------ registratie
    def _register(self) -> None:
        from .tooldefs import register_all
        register_all(self)

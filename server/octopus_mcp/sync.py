"""Lokale synchronisatie van stamdata en boekingen, zuinig met de daglimieten van Octopus.

Strategie (officiële spec, 'Get modified bookings'):
* Boekingen: eerste keer per boekjaar x dagboektype 1-4 met modifiedTimeStamp = 1980-01-01 00:00:00.000;
  daarna één call met bookyearId = -1, journalTypeId = -1 en het watermerk van de laatste synchronisatie.
* Rekeningen: eerste keer GET /accounts per boekjaar (2 per dag!), daarna /accounts/modified (48 per dag).
* Relaties: eerste keer GET /relations (2 per dag), daarna /relations/modified (48 per dag).
* Saldi per rekening per periode: /accounts/amounts/modified met watermerk (48 per dag).
Gegevens staan versleuteld op schijf als OCTOPUS_CACHE_KEY is ingesteld, anders alleen in het geheugen van dit proces.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from accounting_api_core.syncstate import SyncState

from . import normalize as N
from .client import OctopusClient

INITIAL = "1980-01-01 00:00:00.000"


def _brussels_now() -> datetime:
    """Watermerk in Belgische tijd (tijdzone van de Octopus-server niet gedocumenteerd: verifieer actuele regel)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Brussels")).replace(tzinfo=None)
    except Exception:  # noqa: BLE001 - geen tijdzonedata (bv. Windows zonder tzdata): lokale tijd
        return datetime.now()


class OctopusSync:
    def __init__(self, client: OctopusClient, state: Optional[SyncState] = None) -> None:
        self.c = client
        self.state = state or SyncState(client.store, INITIAL, now=_brussels_now)

    # ------------------------------------------------------------------ rekeningen
    def accounts(self, dossier: int, bookyear: int, refresh: bool = False) -> list[dict]:
        scope = f"{dossier}:accounts"
        cur = self.state.load(scope)
        loaded = set(cur["meta"].get("bookyears", []))
        if bookyear not in loaded:
            marker = self.state.start_marker()
            data = self.c.call("accounts", dossier_id=dossier, query={"bookyearId": bookyear}, use_cache=False) or []
            recs = cur["records"]
            for a in data:
                recs[N.account_key(a)] = a
            loaded.add(bookyear)
            self.state.save(scope, recs, cur["watermark"] or marker, {**cur["meta"], "bookyears": sorted(loaded)})
        elif refresh:
            self._accounts_modified(dossier)
        return [N.account(a, self.c.s.language) for k, a in self.state.records(scope).items() if k.startswith(f"{bookyear}|")]

    def _accounts_modified(self, dossier: int) -> dict:
        scope = f"{dossier}:accounts"
        marker = self.state.start_marker()
        res = self.c.call("accounts_modified", dossier_id=dossier, query={"modifiedTimeStamp": self.state.watermark(scope)}, use_cache=False) or {}
        return self.state.apply(scope, res.get("modified") or [], res.get("deleted") or [], N.account_key, marker)

    # ------------------------------------------------------------------ saldi
    def amounts(self, dossier: int, refresh: bool = False) -> list[dict]:
        scope = f"{dossier}:amounts"
        if refresh or self.state.is_initial(scope):
            marker = self.state.start_marker()
            res = self.c.call("amounts_modified", dossier_id=dossier, query={"modifiedTimeStamp": self.state.watermark(scope)}, use_cache=False) or {}
            self.state.apply(scope, res.get("modified") or [], res.get("deleted") or [], N.amount_key, marker)
        return [N.amount(x) for x in self.state.records(scope).values()]

    # ------------------------------------------------------------------ relaties
    def relations(self, dossier: int, refresh: bool = False) -> list[dict]:
        scope = f"{dossier}:relations"
        if self.state.is_initial(scope):
            marker = self.state.start_marker()
            data = self.c.call("relations", dossier_id=dossier, use_cache=False) or []
            self.state.apply(scope, data, [], N.relation_key, marker, {"initial": "GET /relations (alleen actieve relaties)"})
        elif refresh:
            marker = self.state.start_marker()
            res = self.c.call("relations_modified", dossier_id=dossier, query={"modifiedTimeStamp": self.state.watermark(scope)}, use_cache=False) or {}
            self.state.apply(scope, res.get("modified") or [], res.get("deleted") or [], N.relation_key, marker)
        return [N.relation(r) for r in self.state.records(scope).values()]

    # ------------------------------------------------------------------ boekingen
    def bookings(self, dossier: int, bookyear: int, refresh: bool = False) -> list[dict]:
        scope = f"{dossier}:bookings"
        cur = self.state.load(scope)
        loaded = set(cur["meta"].get("bookyears", []))
        recs = cur["records"]
        wm = cur["watermark"]
        if bookyear not in loaded:
            marker = self.state.start_marker()
            for jt in (1, 2, 3, 4):
                res = self.c.call("bookings_modified", dossier_id=dossier, path_params={"bookyearId": bookyear},
                                  query={"journalTypeId": jt, "modifiedTimeStamp": INITIAL}, use_cache=False) or {}
                self._merge_bookings(recs, res)
            loaded.add(bookyear)
            self.state.save(scope, recs, wm or marker, {**cur["meta"], "bookyears": sorted(loaded)})
        elif refresh:
            marker = self.state.start_marker()
            res = self.c.call("bookings_modified", dossier_id=dossier, path_params={"bookyearId": -1},
                              query={"journalTypeId": -1, "modifiedTimeStamp": wm or INITIAL}, use_cache=False) or {}
            self._merge_bookings(recs, res)
            self.state.save(scope, recs, marker, cur["meta"])
        rows = [N.booking_line(b) for k, b in self.state.records(scope).items() if k.startswith(f"{bookyear}|")]
        return sorted(rows, key=lambda r: (str(r["dagboektype"]), r["dagboek_nr"] or 0, r["document_nr"] or 0, r["lijn_nr"] or 0))

    @staticmethod
    def _merge_bookings(recs: dict, res: dict) -> None:
        for dk in res.get("deletedBookings") or []:
            pref = N.document_prefix(dk)
            for k in [k for k in recs if k.startswith(pref)]:
                del recs[k]
        for b in res.get("modifiedBookings") or []:
            recs[N.booking_key(b)] = b

    # ------------------------------------------------------------------ status
    def status(self, dossier: int) -> dict:
        return {s: self.state.info(f"{dossier}:{s}") for s in ("accounts", "amounts", "relations", "bookings")}

    def reset(self, dossier: int, what: Optional[list] = None) -> list[str]:
        out = []
        for s in what or ("accounts", "amounts", "relations", "bookings"):
            self.state.reset(f"{dossier}:{s}")
            out.append(s)
        return out

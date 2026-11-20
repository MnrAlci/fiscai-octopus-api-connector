"""Incrementele synchronisatie via 'gewijzigd sinds'-endpoints: watermerken, meta-gegevens en samenvoegen van records.

Gebruik: eerste keer een volledige ophaling (of een oude tijdstempel), daarna alleen de wijzigingen sinds het laatste watermerk.
Het watermerk is het tijdstip VÓÓR de call, met een kleine overlap tegen klokverschil (zo mis je geen wijzigingen tijdens de call);
dubbele records worden op sleutel samengevoegd. Alles staat in een SecureStore (versleuteld op schijf of alleen in het geheugen).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Optional

from .securestore import SecureStore


class SyncState:
    def __init__(self, store: SecureStore, initial: str, fmt: str = "%Y-%m-%d %H:%M:%S.000",
                 now: Callable[[], datetime] = datetime.now, overlap_seconds: int = 120) -> None:
        self.store, self.initial, self.fmt, self.now, self.overlap = store, initial, fmt, now, overlap_seconds

    @staticmethod
    def _k(scope: str) -> str:
        return "sync:" + scope

    def load(self, scope: str) -> dict:
        rec = self.store.get(self._k(scope)) or {}
        return {"watermark": rec.get("watermark"), "records": rec.get("records", {}), "meta": rec.get("meta", {}), "updated": rec.get("updated")}

    def save(self, scope: str, records: dict, watermark: Optional[str], meta: Optional[dict] = None) -> None:
        self.store.put(self._k(scope), {"watermark": watermark, "records": records, "meta": meta or {},
                                        "updated": self.now().isoformat(timespec="seconds")})

    def watermark(self, scope: str) -> str:
        return self.load(scope)["watermark"] or self.initial

    def is_initial(self, scope: str) -> bool:
        return not self.load(scope)["watermark"]

    def start_marker(self) -> str:
        """Tijdstempel om na een geslaagde call op te slaan (tijdstip vóór de call min de overlap)."""
        return (self.now() - timedelta(seconds=self.overlap)).strftime(self.fmt)

    def records(self, scope: str) -> dict:
        return self.load(scope)["records"]

    def apply(self, scope: str, modified: Iterable[dict], deleted: Iterable[Any], key: Callable[[Any], str], marker: str,
              meta: Optional[dict] = None) -> dict:
        cur = self.load(scope)
        data: dict = cur["records"]
        n_mod = n_del = 0
        for r in modified or []:
            data[key(r)] = r
            n_mod += 1
        for r in deleted or []:
            if data.pop(key(r), None) is not None:
                n_del += 1
        self.save(scope, data, marker, {**cur["meta"], **(meta or {})})
        return {"scope": scope, "modified": n_mod, "deleted": n_del, "total": len(data), "watermark": marker}

    def reset(self, scope: str) -> None:
        self.store.delete(self._k(scope))

    def info(self, scope: str) -> dict:
        cur = self.load(scope)
        return {"scope": scope, "watermark": cur["watermark"], "records": len(cur["records"]), "updated": cur["updated"], "meta": cur["meta"]}

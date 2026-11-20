"""Daglimieten per endpoint (bv. 'Maximum allowed calls per day' uit een OpenAPI-spec).

De teller staat per kalenderdag (tijdzone instelbaar, standaard Europe/Brussels) in een JSON-bestand (rechten 0600).
De teller bevat alleen endpointsleutels en aantallen: geen dossiernummers, geen parameters, geen geheimen.
Een call wordt geweigerd VÓÓR hij vertrekt als de limiet (min de reserve) bereikt is.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


class QuotaExceeded(RuntimeError):
    def __init__(self, key: str, limit: int, used: int) -> None:
        super().__init__(f"Daglimiet bereikt voor '{key}': {used}/{limit} vandaag. Gebruik de cache of de gewijzigd-sinds-endpoints, of probeer morgen opnieuw.")
        self.key, self.limit, self.used = key, limit, used


def _today(tz: str) -> str:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz)).date().isoformat()
    except Exception:  # noqa: BLE001 - zonder tz-database: lokale datum
        return datetime.now().date().isoformat()


class EndpointQuota:
    def __init__(self, path: Optional[Path], limits: dict[str, int], reserve: int = 0, tz: str = "Europe/Brussels",
                 today: Optional[Callable[[], str]] = None) -> None:
        self.path = Path(path).expanduser() if path else None
        self.limits = dict(limits)
        self.reserve = max(0, int(reserve))
        self._today = today or (lambda: _today(tz))
        self._lock = threading.Lock()
        self._state = {"date": self._today(), "counts": {}}
        if self.path and self.path.is_file():
            try:
                st = json.loads(self.path.read_text(encoding="utf-8"))
                if st.get("date") == self._state["date"]:
                    self._state = {"date": st["date"], "counts": {k: int(v) for k, v in st.get("counts", {}).items()}}
            except (ValueError, OSError):
                pass

    def _roll(self) -> None:
        d = self._today()
        if self._state["date"] != d:
            self._state = {"date": d, "counts": {}}

    def limit(self, key: str) -> Optional[int]:
        return self.limits.get(key)

    def effective(self, key: str) -> Optional[int]:
        lim = self.limits.get(key)
        if lim is None:
            return None
        return max(1, lim - self.reserve) if lim > self.reserve else lim

    def used(self, key: str) -> int:
        with self._lock:
            self._roll()
            return int(self._state["counts"].get(key, 0))

    def remaining(self, key: str) -> Optional[int]:
        eff = self.effective(key)
        return None if eff is None else max(0, eff - self.used(key))

    def check(self, key: str) -> None:
        eff = self.effective(key)
        if eff is not None and self.used(key) >= eff:
            raise QuotaExceeded(key, eff, self.used(key))

    def record(self, key: str) -> None:
        with self._lock:
            self._roll()
            self._state["counts"][key] = int(self._state["counts"].get(key, 0)) + 1
            self._save()

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, indent=0), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(self.path)

    def snapshot(self) -> dict:
        with self._lock:
            self._roll()
            counts = dict(self._state["counts"])
        return {"date": self._state["date"], "reserve": self.reserve,
                "endpoints": {k: {"limit": v, "used": counts.get(k, 0), "remaining": max(0, (self.effective(k) or 0) - counts.get(k, 0))}
                              for k, v in sorted(self.limits.items())}}

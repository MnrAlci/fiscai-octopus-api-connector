"""Antwoordcache met vervaltijd per endpoint, bovenop SecureStore. Spaart de (lage) daglimieten van boekhoud-API's."""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .securestore import SecureStore


class ResponseCache:
    def __init__(self, store: SecureStore, clock: Callable[[], float] = time.time) -> None:
        self.store, self.clock = store, clock
        self.hits = self.misses = 0

    def get(self, key: str, max_age_seconds: float) -> Optional[Any]:
        if max_age_seconds <= 0:
            return None
        rec = self.store.get("cache:" + key)
        if not rec or self.clock() - float(rec.get("t", 0)) > max_age_seconds:
            self.misses += 1
            return None
        self.hits += 1
        return rec.get("v")

    def age(self, key: str) -> Optional[float]:
        rec = self.store.get("cache:" + key)
        return None if not rec else self.clock() - float(rec.get("t", 0))

    def put(self, key: str, value: Any) -> None:
        self.store.put("cache:" + key, {"t": self.clock(), "v": value})

    def invalidate(self, key: str) -> None:
        self.store.delete("cache:" + key)

"""Tokens met beperkte geldigheid (bv. 10 minuten) en automatische vernieuwing, met een veiligheidsmarge."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Hashable, Optional


@dataclass
class TimedToken:
    value: str
    issued_at: float
    ttl_seconds: float

    def valid(self, now: float, margin: float) -> bool:
        return bool(self.value) and now < self.issued_at + self.ttl_seconds - margin


class TokenCache:
    """Houdt tokens per sleutel bij (bv. 'auth' of ('dossier', 123)). Vraagt een nieuw token aan als het (bijna) verlopen is.

    Tokens leven alleen in het geheugen; ze worden nooit gelogd of op schijf gezet.
    """

    def __init__(self, ttl_seconds: float = 600, margin_seconds: float = 60, clock: Callable[[], float] = time.monotonic) -> None:
        if margin_seconds >= ttl_seconds:
            raise ValueError("De veiligheidsmarge moet kleiner zijn dan de geldigheid van het token.")
        self.ttl, self.margin, self.clock = float(ttl_seconds), float(margin_seconds), clock
        self._tokens: dict[Hashable, TimedToken] = {}
        self._lock = threading.RLock()  # herintredend: een dossiertoken vraagt binnen get() eerst een aanmeldtoken
        self.issued = 0

    def get(self, key: Hashable, fetch: Callable[[], str]) -> str:
        with self._lock:
            now = self.clock()
            tok = self._tokens.get(key)
            if tok and tok.valid(now, self.margin):
                return tok.value
            value = fetch()
            if not value:
                raise RuntimeError("Lege token-waarde ontvangen.")
            self._tokens[key] = TimedToken(value, now, self.ttl)  # conservatief: geldigheid telt vanaf de aanvraag
            self.issued += 1
            return value

    def invalidate(self, key: Optional[Hashable] = None) -> None:
        with self._lock:
            if key is None:
                self._tokens.clear()
            else:
                self._tokens.pop(key, None)

    def peek(self, key: Hashable) -> Optional[TimedToken]:
        return self._tokens.get(key)

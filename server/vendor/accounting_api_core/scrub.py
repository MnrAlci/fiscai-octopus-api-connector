"""Geheimen-scrubber: verwijdert geheime waarden uit alles wat het proces verlaat (antwoorden, logs, hooks)."""
from __future__ import annotations

import os
import re
from typing import Any

from .profile import get_profile

GENERIC_PATTERNS = (
    (re.compile(r"(?i)(<(?:accessKey|sessionID|sessionId|clientSecret|password|token)>).*?(</)"), r"\1[GEHEIM]\2"),
    (re.compile(r"(?i)(\"(?:password|token|dossierToken|access_token|refresh_token|softwareHouseUuid)\"\s*:\s*\")[^\"]*(\")"), r"\1[GEHEIM]\2"),
    (re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[GEHEIM]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "[GEHEIM]"),   # JWT
)


def secret_values(extra: tuple = ()) -> list[str]:
    names = tuple(get_profile().secret_env) + tuple(extra)
    vals = [os.environ.get(n, "") for n in names]
    return sorted({v for v in vals if len(v) >= 6}, key=len, reverse=True)


def scrub(value: Any, extra_secrets: tuple = ()) -> Any:
    """Vervang bekende geheime waarden en geheim-achtige patronen door [GEHEIM]. Werkt recursief op dict/list/str."""
    secrets = secret_values() + [s for s in extra_secrets if s and len(s) >= 6]

    def _s(x: Any) -> Any:
        if isinstance(x, str):
            for sec in secrets:
                x = x.replace(sec, "[GEHEIM]")
            for rx, rep in GENERIC_PATTERNS:
                x = rx.sub(rep, x)
            return x
        if isinstance(x, dict):
            return {k: _s(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [_s(v) for v in x]
        return x
    return _s(value)

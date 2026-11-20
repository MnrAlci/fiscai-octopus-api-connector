"""Offline controle van een Belgisch ondernemings-/btw-nummer (modulo 97). Geen netwerk.

Regel: 10 cijfers; de laatste twee = 97 - (eerste acht cijfers mod 97). Verifieer actuele regel (KBO / FOD Economie).
"""
from __future__ import annotations

import re


def normalize(nr: str) -> str:
    s = re.sub(r"[^0-9A-Za-z]", "", str(nr or "")).upper()
    if s.startswith("BE"):
        s = s[2:]
    if len(s) == 9 and s.isdigit():
        s = "0" + s
    return s


def check(nr: str) -> dict:
    s = normalize(nr)
    if not (len(s) == 10 and s.isdigit()):
        return {"nummer": s, "geldig_formaat": False, "controlegetal_ok": False, "reden": "verwacht 10 cijfers (eventueel met BE-prefix)"}
    ok = 97 - int(s[:8]) % 97 == int(s[8:])
    return {"nummer": f"BE{s}", "geldig_formaat": s[0] in "01", "controlegetal_ok": ok,
            "reden": None if ok else "controlegetal (mod 97) klopt niet", "_verifieer": "offline controle; bestaan en btw-plicht via VIES/KBO"}

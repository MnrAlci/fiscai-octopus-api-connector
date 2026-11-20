"""Gemeenschappelijk datamodel en Belgische rekeningstelsel-hulpjes (MAR/PCMN).

De indeling in klassen volgt het Belgische minimumindelingsschema (MAR): klasse 1-5 balans, 6 kosten, 7 opbrengsten,
0 rechten en verplichtingen buiten balans. Verifieer actuele regel bij de officiële bron (FOD Economie / KB uitvoering WVV).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

CLASS_NAMES = {
    0: "Rechten en verplichtingen buiten balans", 1: "Eigen vermogen, voorzieningen en schulden > 1 jaar", 2: "Oprichtingskosten, vaste activa en vorderingen > 1 jaar",
    3: "Voorraden en bestellingen in uitvoering", 4: "Vorderingen en schulden op ten hoogste 1 jaar", 5: "Geldbeleggingen en liquide middelen",
    6: "Kosten", 7: "Opbrengsten",
}


def D(v: Any) -> Decimal:
    try:
        return Decimal(str(v)) if v not in (None, "") else Decimal(0)
    except InvalidOperation:
        return Decimal(0)


def money(v: Any) -> float:
    return float(D(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def account_class(code: Any) -> int | None:
    s = str(code or "").strip()
    return int(s[0]) if s[:1].isdigit() else None


def account_kind(code: Any) -> str:
    c = account_class(code)
    if c is None:
        return "onbekend"
    if c == 0:
        return "buiten_balans"
    if c <= 5:
        return "balans"
    return "kosten" if c == 6 else "opbrengsten"


def starts(code: Any, *prefixes: str) -> bool:
    s = str(code or "")
    return any(s.startswith(p) for p in prefixes)


def pick_lang(obj: Any, lang: str = "nl") -> str:
    """Kies een omschrijving uit een meertalig object (bv. description_NL/FR/EN/DE), met terugval."""
    if isinstance(obj, str) or obj is None:
        return obj or ""
    if isinstance(obj, dict):
        order = [lang.upper(), "NL", "FR", "EN", "DE"]
        for L in order:
            for k in (f"description_{L}", L, L.lower()):
                if obj.get(k):
                    return str(obj[k])
    return ""

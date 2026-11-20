"""Deterministische analyses op genormaliseerde data: ouderdom van open posten en kerncijfers uit een proefbalans.

Geen netwerk, geen verzonnen cijfers. De PCMN-indeling van de kerncijfers volgt het Belgische MAR (verifieer actuele regel).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from .model import D, money, starts

BUCKETS = ("niet_vervallen", "0-30", "31-60", "61-90", ">90", "zonder_datum", "negatief")

# Kerncijfers uit de proefbalans (saldo = debet - credit). Prefixen volgens het MAR.
KPI_PREFIXES = {
    "omzet": ("70",),
    "bedrijfsopbrengsten": ("70", "71", "72", "74"),
    "handelsgoederen_grondstoffen": ("60",),
    "diensten_diverse_goederen": ("61",),
    "bezoldigingen": ("62",),
    "afschrijvingen_waardeverminderingen": ("63",),
    "andere_bedrijfskosten": ("64",),
    "financiele_kosten": ("65",),
    "financiele_opbrengsten": ("75",),
    "liquide_middelen": ("55", "56", "57"),
    "handelsvorderingen": ("40",),
    "handelsschulden": ("44",),
    "btw_terug_te_vorderen": ("411",),
    "btw_te_betalen": ("451",),
}


def _parse(d) -> Optional[date]:
    if not d:
        return None
    if isinstance(d, date):
        return d
    try:
        return date.fromisoformat(str(d)[:10])
    except ValueError:
        return None


def bucket(due: Optional[date], amount: Decimal, as_of: date) -> str:
    if amount < 0:
        return "negatief"
    if due is None:
        return "zonder_datum"
    days = (as_of - due).days
    if days <= 0:
        return "niet_vervallen"
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return ">90"


def aging(items: Iterable[dict], as_of: date, amount_key: str = "open_bedrag", due_key: str = "vervaldatum") -> dict:
    """items: genormaliseerde open posten. Positief = te ontvangen (klanten) of te betalen (leveranciers), in de eenheid van de bron."""
    tot = {b: Decimal(0) for b in BUCKETS}
    cnt = {b: 0 for b in BUCKETS}
    rows = []
    for it in items:
        a = D(it.get(amount_key))
        b = bucket(_parse(it.get(due_key)), a, as_of)
        tot[b] += a
        cnt[b] += 1
        rows.append({**it, "ouderdom_bucket": b})
    pos = sum((v for k, v in tot.items() if k != "negatief"), Decimal(0))
    overdue = sum((tot[k] for k in ("0-30", "31-60", "61-90", ">90")), Decimal(0))
    return {"peildatum": as_of.isoformat(), "totaal_positief": money(pos), "vervallen_totaal": money(overdue),
            "buckets": {b: {"bedrag": money(tot[b]), "aantal": cnt[b]} for b in BUCKETS},
            "negatieve_posten": {"aantal": cnt["negatief"], "bedrag": money(tot["negatief"])}, "rijen": rows}


def kpis(tb_rows: Iterable[dict]) -> dict:
    """Kerncijfers uit proefbalansrijen (rekening_code, saldo). Opbrengsten en schulden worden positief getoond."""
    rows = list(tb_rows)

    def s(prefixes) -> Decimal:
        return sum((D(r.get("saldo")) for r in rows if starts(r.get("rekening_code"), *prefixes)), Decimal(0))
    out: dict = {}
    for k, pf in KPI_PREFIXES.items():
        v = s(pf)
        out[k] = money(-v if k in ("omzet", "bedrijfsopbrengsten", "financiele_opbrengsten", "handelsschulden", "btw_te_betalen") else v)
    kosten = s(("60", "61", "62", "63", "64", "65", "66", "67", "68", "69"))
    opbr = -s(("70", "71", "72", "73", "74", "75", "76", "77", "78", "79"))
    out["kosten"] = money(kosten)
    out["opbrengsten"] = money(opbr)
    out["resultaat"] = money(opbr - kosten)
    out["bruto_marge"] = money(-s(("70",)) - s(("60",)))
    out["btw_indicatie"] = money(s(("411",)) + s(("451",)))   # >0: terug te vorderen, <0: te betalen (indicatie)
    out["_verifieer"] = "Indeling volgens het Belgische MAR; verifieer actuele regel en de rekeningindeling van het dossier."
    return out

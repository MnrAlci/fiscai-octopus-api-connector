"""Proefbalans samenstellen uit saldi per rekening per periode (voor API's zonder eigen proefbalans-endpoint).

Invoer:
* ``accounts``: [{"account_code", "account_name"}]
* ``amounts``: [{"account_code", "fiscal_period", "amount"}] (één rij per rekening per periode)
* ``mode``: "movement" (bedrag = beweging van de periode; cumulatief optellen) of "cumulative" (bedrag = saldo op einde periode).
  Welke van de twee een API levert, moet per API geverifieerd worden (verifieer actuele regel).
Tekenconventie van de uitvoer: saldo = debet - credit (positief = debet). ``sign`` = -1 draait het teken van de bron om.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Optional

from .model import D, account_class, account_kind, money


def build(accounts: Iterable[dict], amounts: Iterable[dict], up_to_period: Optional[int] = None, from_period: Optional[int] = None,
          mode: str = "movement", sign: int = 1, include_zero: bool = False) -> dict:
    if mode not in ("movement", "cumulative"):
        raise ValueError("mode moet 'movement' of 'cumulative' zijn.")
    if sign not in (1, -1):
        raise ValueError("sign moet 1 of -1 zijn.")
    names = {str(a.get("account_code")): a.get("account_name") or "" for a in accounts}
    per: dict[str, dict[int, Decimal]] = defaultdict(dict)
    for r in amounts:
        code = str(r.get("account_code"))
        p = int(r.get("fiscal_period") or 0)
        per[code][p] = per[code].get(p, Decimal(0)) + D(r.get("amount")) * sign
    rows = []
    unknown = []
    for code in sorted(set(per) | (set(names) if include_zero else set()), key=lambda c: (not c.isdigit(), c)):
        periods = per.get(code, {})
        sel = {p: v for p, v in periods.items() if (up_to_period is None or p <= up_to_period)}
        if mode == "movement":
            start = from_period
            saldo = sum((v for p, v in sel.items() if start is None or p >= start), Decimal(0))
        else:
            saldo = sel[max(sel)] if sel else Decimal(0)
        if saldo == 0 and not include_zero:
            continue
        if code not in names:
            unknown.append(code)
        rows.append({"rekening_code": code, "rekening_naam": names.get(code, ""), "klasse": account_class(code), "soort": account_kind(code),
                     "debet": money(saldo) if saldo > 0 else 0.0, "credit": money(-saldo) if saldo < 0 else 0.0, "saldo": money(saldo)})
    tot_d = sum(D(r["debet"]) for r in rows)
    tot_c = sum(D(r["credit"]) for r in rows)
    by_class = defaultdict(Decimal)
    for r in rows:
        by_class[str(r["klasse"])] += D(r["saldo"])
    return {"rows": rows, "totals": {"debet": money(tot_d), "credit": money(tot_c), "verschil": money(tot_d - tot_c)},
            "in_evenwicht": tot_d == tot_c, "per_klasse": {k: money(v) for k, v in sorted(by_class.items())},
            "rekeningen_zonder_naam": unknown, "mode": mode, "tot_periode": up_to_period, "vanaf_periode": from_period,
            "tekenconventie": "saldo = debet - credit"}

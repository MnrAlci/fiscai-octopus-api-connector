"""Optionele hulp: euro-referentiekoersen van de ECB (gratis, geen sleutel). Alleen ter informatie.

ECB Data Portal (SDMX): https://data-api.ecb.europa.eu/service/data/EXR/D.<MUNT>.EUR.SP00.A?format=jsondata
Er gaat alleen een muntcode en datum naar de ECB; geen boekhouddata.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

BASE = "https://data-api.ecb.europa.eu/service/data/EXR"
HttpGet = Callable[[str, float], dict]


def _default_get(url: str, timeout: float) -> dict:
    import httpx
    r = httpx.get(url, timeout=timeout, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def rate(currency: str, on: Optional[str] = None, http_get: Optional[HttpGet] = None, timeout: float = 15.0) -> dict:
    cur = str(currency or "").upper()
    if not re.fullmatch(r"[A-Z]{3}", cur) or cur == "EUR":
        raise ValueError("Geef een ISO-muntcode van drie letters (niet EUR), bv. USD.")
    q = "format=jsondata&lastNObservations=1" if not on else f"format=jsondata&endPeriod={on}&lastNObservations=1"
    if on and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", on):
        raise ValueError("Datum als JJJJ-MM-DD.")
    data = (http_get or _default_get)(f"{BASE}/D.{cur}.EUR.SP00.A?{q}", timeout)
    try:
        series = next(iter(data["dataSets"][0]["series"].values()))
        idx, obs = sorted(series["observations"].items(), key=lambda kv: int(kv[0]))[-1]
        dates = data["structure"]["dimensions"]["observation"][0]["values"]
        return {"munt": cur, "koers_per_eur": float(obs[0]), "datum": dates[int(idx)]["id"], "bron": "ECB-referentiekoers (ter informatie)"}
    except (KeyError, IndexError, StopIteration, TypeError, ValueError) as exc:
        raise ValueError("Onverwacht antwoord van de ECB; geen koers gevonden voor die datum.") from exc

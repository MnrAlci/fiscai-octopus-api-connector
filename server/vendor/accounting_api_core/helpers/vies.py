"""Optionele hulp: EU-btw-nummer controleren via VIES (Europese Commissie). Gratis, geen sleutel.

REST: POST https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number met {countryCode, vatNumber}.
Alleen het gevraagde btw-nummer gaat naar VIES; geen boekhouddata. Fair-use/throttling: verifieer actuele regel.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

BASE = "https://ec.europa.eu/taxation_customs/vies/rest-api"
EU = ("AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
      "SE", "SI", "SK", "XI")

HttpPost = Callable[[str, dict, float], dict]


def _default_post(url: str, body: dict, timeout: float) -> dict:
    import httpx
    r = httpx.post(url, json=body, timeout=timeout, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def split(vat: str) -> tuple[str, str]:
    s = re.sub(r"[^0-9A-Za-z]", "", str(vat or "")).upper()
    cc, nr = s[:2], s[2:]
    if cc == "GR":
        cc = "EL"
    if cc not in EU or not nr:
        raise ValueError("Geef een btw-nummer met landcode, bv. BE0123456789 ([Voorbeeld]).")
    return cc, nr


def check(vat: str, http_post: Optional[HttpPost] = None, timeout: float = 15.0) -> dict:
    cc, nr = split(vat)
    data = (http_post or _default_post)(f"{BASE}/check-vat-number", {"countryCode": cc, "vatNumber": nr}, timeout)
    err = data.get("userError")
    return {"land": cc, "nummer": nr, "geldig": bool(data.get("valid", data.get("isValid"))),
            "naam": None if data.get("name") in (None, "---") else data.get("name"),
            "adres": None if data.get("address") in (None, "---") else data.get("address"),
            "aanvraagdatum": data.get("requestDate"), "melding": None if err in (None, "VALID", "INVALID") else err,
            "bron": "VIES (Europese Commissie)"}

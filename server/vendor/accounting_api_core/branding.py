"""Huisstijl en vaste teksten (minimalistisch): alleen logo/zegel, FISCALCI, 'Accounting & Tax' en drie kleuren."""
from __future__ import annotations

from .attribution import ATTRIBUTION

BRAND = "FISCALCI"
TAGLINE = "Accounting & Tax"
COLORS = {"navy": "#092B47", "blue": "#016BFC", "cyan": "#01D0FD"}
BE_NOTICE = {
    "nl": "Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). "
          "Gebruik buiten België: verifieer zelf de lokale regels.",
    "en": "Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). "
          "Use outside Belgium: verify the local rules yourself.",
}
VERIFY = {"nl": "verifieer actuele regel", "en": "verify current rule"}


def footer(lang: str = "nl") -> str:
    """Vaste voettekst: attributie + Belgische scope."""
    return f"{ATTRIBUTION}\n\n{BE_NOTICE.get(lang, BE_NOTICE['nl'])}"

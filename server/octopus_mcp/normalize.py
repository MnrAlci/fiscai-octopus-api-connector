"""Octopus-velden (uit de OpenAPI-spec) naar het gemeenschappelijke FISCAi-datamodel (Nederlandse kolomnamen, zoals de Yuki-connector).

Altijd meegegeven: bron = "octopus". Interpretaties die niet in de officiële bron staan, zijn gemarkeerd met 'verifieer actuele regel'
en staan in docs/OPEN-QUESTIONS.md (bv. of accountKey.id het PCMN-rekeningnummer is, en de tekenconventie van bedragen).
"""
from __future__ import annotations

from typing import Any, Optional

from accounting_api_core.model import D, account_class, money, pick_lang

JOURNAL_TYPES = {1: "AANKOOP", 2: "VERKOOP", 3: "FINANCIEEL", 4: "DIVERSEN"}
JOURNAL_LETTERS = {"A": "AANKOOP", "V": "VERKOOP", "F": "FINANCIEEL", "D": "DIVERSEN", "L": "LEVERING"}


def _id(obj: Any) -> Optional[int]:
    if isinstance(obj, dict):
        v = obj.get("id")
        return int(v) if isinstance(v, (int, float)) or (isinstance(v, str) and v.lstrip("-").isdigit()) else v
    return obj


def dossier(d: dict) -> dict:
    return {"dossier_id": _id(d.get("dossierKey")), "naam": d.get("dossierDescription"), "btw_nummer": d.get("vatNr"),
            "adres": d.get("streetAndNr"), "postcode": d.get("postalCode"), "gemeente": d.get("city"), "land": d.get("country"),
            "taal": d.get("languageCode")}


def bookyear(b: dict) -> dict:
    return {"boekjaar_id": _id(b.get("bookyearKey")), "omschrijving": b.get("bookyearDescription"), "start": b.get("startDate"),
            "einde": b.get("endDate"), "afgesloten": b.get("closed"),
            "perioden": [{"periode": p.get("bookyearPeriod"), "start": p.get("startDate"), "einde": p.get("endDate")} for p in b.get("periods") or []]}


def account(a: dict, lang: str = "nl") -> dict:
    k = a.get("accountKey") or {}
    code = k.get("id")
    return {"boekjaar_id": _id(k.get("bookyearKey")), "account_code": str(code) if code is not None else "", "account_name": pick_lang(a.get("description"), lang),
            "klasse": account_class(code), "btw_code_aankoop": a.get("purchaseVatCode"), "btw_code_verkoop": a.get("salesVatCode"),
            "btw_aftrek_pct": a.get("vatRecupPercentage"), "beroeps_pct": a.get("fiscProfessionalPercentage"), "fiscaal_aftrek_pct": a.get("fiscRecupPercentage"),
            "kostenplaats_type": a.get("costCentreType"), "standaard_kostenplaats": _id(a.get("defaultCostCentreKey")),
            "account_number_key": _id(k.get("accountNumberKey"))}


def account_key(a: dict) -> str:
    k = a.get("accountKey") or {}
    return f"{_id(k.get('bookyearKey'))}|{k.get('id')}"


def amount(x: dict) -> dict:
    k = x.get("accountAmountKey") or {}
    pk = k.get("bookyearPeriodKey") or {}
    ak = k.get("accountKey") or {}
    return {"boekjaar_id": _id(pk.get("bookyearKey")) if pk.get("bookyearKey") is not None else _id(ak.get("bookyearKey")),
            "fiscal_period": pk.get("bookyearPeriodNr"), "account_code": str(ak.get("id")), "amount": x.get("balance")}


def amount_key(x: dict) -> str:
    n = amount(x)
    return f"{n['boekjaar_id']}|{n['fiscal_period']}|{n['account_code']}"


def booking_line(b: dict) -> dict:
    jt = b.get("journalType")
    return {"boekjaar_id": _id(b.get("bookyearKey")), "dagboektype": JOURNAL_TYPES.get(jt, jt), "dagboek_nr": b.get("journalNr"),
            "document_nr": b.get("documentSequenceNr"), "lijn_nr": b.get("lineSequenceNr"), "periode": b.get("bookyearPeriodeNr"),
            "documentdatum": b.get("documentDate"), "vervaldatum": b.get("expiryDate"), "rekening_code": str(b.get("accountKey")),
            "relatie_id": _id(b.get("relationKey")), "bedrag": b.get("bookingAmount"), "bedrag_munt": b.get("documentAmount"),
            "munt": b.get("currencyCode"), "wisselkoers": b.get("exchangeRate"), "btw_rubriek": b.get("vatSectionCode"),
            "btw_aftrek_pct": b.get("vatRecuperationPercentage"), "kostenplaats": _id(b.get("costCentreKey")),
            "omschrijving": b.get("comment"), "referentie": b.get("reference")}


def booking_key(b: dict) -> str:
    return f"{_id(b.get('bookyearKey'))}|{b.get('journalType')}|{b.get('journalNr')}|{b.get('documentSequenceNr')}|{b.get('lineSequenceNr')}"


def document_prefix(dk: dict) -> str:
    """DocumentKey (verwijderde boekingen) -> prefix van de lijnsleutels. journalSequenceNr = journalNr: verifieer actuele regel."""
    return f"{_id(dk.get('bookyearKey'))}|{dk.get('journalType')}|{dk.get('journalSequenceNr')}|{dk.get('documentSequenceNr')}|"


def relation(r: dict) -> dict:
    rid = r.get("relationIdentificationServiceData") or {}
    return {"relatie_id": _id(rid.get("relationKey")), "extern_id": rid.get("externalRelationId"), "naam": " ".join(x for x in (r.get("firstName"), r.get("name")) if x),
            "klant": r.get("client"), "leverancier": r.get("supplier"), "btw_nummer": r.get("vatNr"), "adres": r.get("streetAndNr"),
            "postcode": r.get("postalCode"), "gemeente": r.get("city"), "land": r.get("country"), "email": r.get("email"),
            "iban": r.get("ibanAccountNr"), "bic": r.get("bicCode"), "munt": r.get("currencyCode"), "actief": r.get("active"),
            "standaard_rekening_klant": r.get("defaultBookingAccountClient"), "standaard_rekening_leverancier": r.get("defaultBookingAccountSupplier")}


def relation_key(r: dict) -> str:
    rid = r.get("relationIdentificationServiceData") or {}
    return str(_id(rid.get("relationKey")))


def open_item(o: dict, soort: str, as_of: Optional[str] = None) -> dict:
    deb, cre = D(o.get("debetBookingAmount")), D(o.get("creditBookingAmount"))
    orig = deb - cre if soort == "debiteuren" else cre - deb
    opn = D(o.get("openBookingAmount"))
    status = "OPEN" if abs(opn) >= abs(orig) else "PARTIAL"
    return {"soort": soort, "peildatum": as_of, "relatie_id": _id(o.get("relationKey")), "relatie": None, "extern_id": o.get("externalRelationId"),
            "referentie": o.get("reference"), "omschrijving": o.get("comment"), "factuurdatum": o.get("documentDate"), "vervaldatum": o.get("expirationDate"),
            "origineel_bedrag": money(orig), "open_bedrag": money(opn), "open_bedrag_munt": o.get("openDocAmount"), "munt": o.get("currencyCode"),
            "boekjaar_id": _id(o.get("bookyearKey")), "dagboek": o.get("journalKey"), "document_nr": o.get("documentSequenceNr"),
            "lijn_nr": o.get("lineSequenceNr"), "periode": o.get("bookyearPeriodNr"), "status": status}


def vatcode(v: dict) -> dict:
    return {"code": v.get("code"), "omschrijving": v.get("description"), "type": v.get("type"), "percentage": v.get("basePercentage"),
            "standaard_verkooprekening": v.get("defaultSellBookingAccountNr")}


def journal(j: dict) -> dict:
    return {"boekjaar_id": _id(j.get("bookyearKey")), "dagboek": j.get("journalKey"), "naam": j.get("name"), "afgesloten": j.get("closed"),
            "munt": j.get("currencyCode"), "laatste_documentnr": j.get("lastBookedDocumentNr"), "beschermd_tot_periode": j.get("protectedPeriod"),
            "afgesloten_periode": j.get("closedPeriod")}

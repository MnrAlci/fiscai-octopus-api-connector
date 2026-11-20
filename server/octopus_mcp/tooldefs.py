"""Definities van alle tools (naam, titel, beschrijving, invoerschema, handler)."""
from __future__ import annotations

from datetime import date
from typing import Any

from accounting_api_core import analytics
from accounting_api_core.attribution import ATTRIBUTION
from accounting_api_core.branding import BE_NOTICE
from accounting_api_core.helpers import be_vat, ecb, vies

from . import __version__, edition
from . import normalize as N
from .endpoints import META, get
from .errors import OctopusApiError
from .tools import (LOCAL, RO, S_BY, S_DAGBOEK, S_DOCNR, S_DOSSIER, S_JAAR, S_MAX, S_TS, S_VERS, Tools, cap, obj, ts)


def lim(key: str, search: bool = False) -> str:
    n = get(key).limit(search)
    return f"{get(key).op_id}; daglimiet {n}" if n else get(key).op_id


# Eenvoudige doorgeef-tools: (tool, endpoint, titel, beschrijving, params, normalizer, lijst?)
# param: (argnaam, plaats q|p|b, api-naam, schema, verplicht)
PASS = [
    ("octopus_boekjaar_detail", "bookyear", "Boekjaar (detail)", "Details van één boekjaar.",
     [("boekjaar_id", "p", "bookyearId", {"type": "integer"}, True)], None, False),
    ("octopus_dagboeken", "journals", "Dagboeken", "Dagboeken van een boekjaar.",
     [("boekjaar_id", "p", "bookyearId", {"type": "integer"}, True)], N.journal, True),
    ("octopus_dagboeksaldo", "journal_balance", "Saldo financieel dagboek", "Saldo van een (financieel) dagboek.",
     [("boekjaar_id", "p", "bookyearId", {"type": "integer"}, True), ("dagboek", "p", "journalKey", S_DAGBOEK, True)], None, False),
    ("octopus_dagboeken_gewijzigd", "journals_modified", "Gewijzigde dagboeken", "Dagboeken gewijzigd sinds een tijdstip.",
     [("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, False),
    ("octopus_boekingen_gewijzigd", "bookings_modified", "Gewijzigde boekingslijnen (ruw)",
     "Ruwe sync-call: boekingslijnen gewijzigd sinds een tijdstip. Eerste keer per boekjaar en dagboektype 1-4; daarna boekjaar -1 en type -1. "
     "Gebruik bij voorkeur octopus_sync of octopus_boekingslijnen.",
     [("boekjaar_id", "p", "bookyearId", {"type": "integer", "description": "boekjaar-id of -1"}, True),
      ("dagboektype_id", "q", "journalTypeId", {"type": "integer", "enum": [-1, 1, 2, 3, 4], "description": "1 aankoop, 2 verkoop, 3 financieel, 4 diversen, -1 alle"}, True),
      ("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True), ("gewijzigd_tot", "q", "modifiedTimeStampTo", S_TS, False)], None, False),
    ("octopus_aankoop_verkoop_boeking", "buysell", "Aankoop/verkoop-boeking", "Eén aankoop- of verkoopdocument met lijnen.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, True), ("documentnummer", "q", "documentSeqNr", S_DOCNR, True)], None, False),
    ("octopus_aankoop_verkoop_gewijzigd", "buysell_modified", "Gewijzigde aankoop/verkoop-boekingen", "Aankoop/verkoop-documenten gewijzigd sinds een tijdstip.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer", "description": "boekjaar-id of -1"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, False),
      ("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, True),
    ("octopus_financieel_divers_boeking", "findiv", "Financiële/diverse boeking", "Eén financieel of divers document met lijnen.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, True), ("documentnummer", "q", "documentSeqNr", S_DOCNR, True)], None, False),
    ("octopus_financieel_divers_gewijzigd", "findiv_modified", "Gewijzigde financiële/diverse boekingen", "Financiële/diverse documenten gewijzigd sinds een tijdstip.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer", "description": "boekjaar-id of -1"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, False),
      ("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, True),
    ("octopus_onafgepunte_facturen", "bank_invoices", "Onafgepunte facturen", "Facturen die nog niet afgepunt zijn.", [], None, True),
    ("octopus_afpuntingen_gewijzigd", "balancings_modified", "Gewijzigde afpuntingen", "Afpuntingen gewijzigd sinds een tijdstip.",
     [("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, False),
    ("octopus_btw_codes", "vatcodes", "Btw-codes", "Btw-codes van het dossier (stamdata: 2 calls per dag, 12 uur gecachet).", [], N.vatcode, True),
    ("octopus_munten", "currencies", "Munten", "Muntcodes van het dossier (stamdata).", [], None, True),
    ("octopus_vrije_velden", "customfields", "Vrije velden", "Vrije velden (custom fields) van het dossier (stamdata).", [], None, True),
    ("octopus_producten", "products", "Producten", "Producten (stamdata).", [], None, True),
    ("octopus_productgroepen", "productgroups", "Productgroepen", "Productgroepen (stamdata).", [], None, True),
    ("octopus_betaallijst", "paymentlist", "Betaallijst", "Inhoud van de betaallijst (alleen lezen).", [], None, True),
    ("octopus_facturen_gewijzigd", "invoices_modified", "Gewijzigde facturen", "Facturen uit de factuurmodule, gewijzigd sinds een tijdstip (module moet actief zijn).",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, False), ("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, True),
    ("octopus_factuur", "invoice", "Factuur", "Eén factuur uit de factuurmodule.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, True), ("documentnummer", "q", "documentSeqNr", S_DOCNR, True)], None, False),
    ("octopus_leveringsbonnen_gewijzigd", "deliverynotes_modified", "Gewijzigde leveringsbonnen", "Leveringsbonnen gewijzigd sinds een tijdstip.",
     [("boekjaar_id", "q", "bookyearId", {"type": "integer"}, True), ("dagboek", "q", "journalKey", S_DAGBOEK, False), ("gewijzigd_sinds", "q", "modifiedTimeStamp", S_TS, True)], None, True),
    ("octopus_rappels", "rappels", "Rappels", "Rappelinformatie tot een vervaldatum.",
     [("vervaldatum", "q", "expirationDate", {"type": "string", "description": "JJJJ-MM-DD"}, True)], None, True),
]


def _pass(t: Tools, ep_key: str, params: list, norm, is_list: bool):
    def fn(a: dict) -> Any:
        d = int(a["dossier_id"])
        pp, q, body = {}, {}, None
        for arg, where, api, _, _ in params:
            if arg not in a:
                continue
            v = ts(a[arg]) if arg.startswith("gewijzigd_") else a[arg]
            (pp if where == "p" else q)[api] = v
        data = t.client.call(ep_key, dossier_id=d, path_params=pp, query=q, body=body, fresh=bool(a.get("vers")))
        if is_list and isinstance(data, list):
            rows = [norm(x) for x in data] if norm else data
            return t._out({"dossier_id": d, **cap(rows, a.get("max_rijen"))})
        return t._out({"dossier_id": d, "gegevens": data})
    return fn


def register_all(t: Tools) -> None:
    # ---------------------------------------------------------------- status en sessie (geen of weinig calls)
    def status(a):
        s = t.client.status()
        return {"connector": edition.DISPLAY_NAME, "versie": __version__, "editie": edition.EDITION, "attributie": ATTRIBUTION, "scope": BE_NOTICE["nl"],
                "octopus_spec": META, "alleen_lezen": not t.client.s.write_enabled, **s,
                "tools": len(t.defs), "netwerk": False}
    t.add("octopus_status", "Status", "Configuratie (zonder geheimen), daglimieten, cache en versie. Doet geen call naar Octopus.", obj({}), status, LOCAL)
    t.add("octopus_quota", "Daglimieten", "Gebruik en resterende calls per Octopus-endpoint vandaag (Europe/Brussels). Doet geen call.",
          obj({}), lambda a: {"bron": "lokale teller", **t.client.quota.snapshot(),
                              "uitleg": "Octopus legt per endpoint een daglimiet op (officiële spec). Bij overschrijding volgt een e-mail van Octopus; de connector weigert vooraf."}, LOCAL)
    t.add("octopus_api_versie", "API-versie", f"Versie van de Octopus REST API ({lim('version')}).", obj({}),
          lambda a: t._out({"versie": t.client.call("version")}))
    t.add("octopus_whoami", "Aangemelde gebruiker", f"Informatie over de aangemelde Octopus-gebruiker ({lim('whoami')}).", obj({}),
          lambda a: t._out({"gebruiker": t.client.call("whoami")}))
    t.add("octopus_dossiers", "Dossiers", f"Dossiers waartoe de gebruiker toegang heeft ({lim('dossiers')}).", obj({"max_rijen": S_MAX, "vers": S_VERS}),
          lambda a: t._out(cap([N.dossier(x) for x in (t.client.call("dossiers", fresh=bool(a.get("vers"))) or [])
                                if not t.client.s.allowed_dossiers or N.dossier(x)["dossier_id"] in t.client.s.allowed_dossiers], a.get("max_rijen"))))
    t.add("octopus_boekjaren", "Boekjaren", f"Boekjaren met perioden ({lim('bookyears')}).", obj({"dossier_id": S_DOSSIER, "vers": S_VERS}, ("dossier_id",)),
          lambda a: t._out({"dossier_id": a["dossier_id"], "boekjaren": t.bookyears(int(a["dossier_id"]), bool(a.get("vers")))}))

    def by_status(a):
        d = int(a["dossier_id"])
        by = t.resolve_by(d, a)
        js = [N.journal(j) for j in (t.client.call("journals", dossier_id=d, path_params={"bookyearId": by["boekjaar_id"]}) or [])]
        return t._out({"dossier_id": d, "boekjaar": by, "dagboeken": js, "open_dagboeken": sum(1 for j in js if not j.get("afgesloten")),
                       "synchronisatie": t.sync.status(d)})
    t.add("octopus_boekjaar_status", "Boekjaarstatus", f"Status van een boekjaar: afgesloten, dagboeken, beschermde/afgesloten perioden en synchronisatie ({lim('bookyears')}, {lim('journals')}).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR}, ("dossier_id",)), by_status)

    def journal_detail(a):
        d = int(a["dossier_id"])
        return t._out({"dossier_id": d, "gegevens": t.client.call(f"journal_{a['type']}", dossier_id=d,
                                                                  path_params={"bookyearId": a["boekjaar_id"], "sequenceNumber": a["volgnummer"]})})
    t.add("octopus_dagboek_detail", "Dagboek (detail)", f"Detail van één dagboek per type A/V/F/D/L ({lim('journal_A')}).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": {"type": "integer"}, "type": {"type": "string", "enum": ["A", "V", "F", "D", "L"]},
               "volgnummer": {"type": "integer"}}, ("dossier_id", "boekjaar_id", "type", "volgnummer")), journal_detail)

    for name, ep, title, desc, params, norm, is_list in PASS:
        props = {"dossier_id": S_DOSSIER, **{p[0]: p[3] for p in params}, "vers": S_VERS}
        if is_list:
            props["max_rijen"] = S_MAX
        t.add(name, title, f"{desc.rstrip('.')} ({lim(ep)}).", obj(props, ("dossier_id",) + tuple(p[0] for p in params if p[4])), _pass(t, ep, params, norm, is_list))

    # ---------------------------------------------------------------- stamdata via synchronisatie
    def accounts(a):
        d = int(a["dossier_id"])
        by = t.resolve_by(d, a)
        rows = t.sync.accounts(d, by["boekjaar_id"], refresh=bool(a.get("vers")))
        return t._out({"dossier_id": d, "boekjaar_id": by["boekjaar_id"], **cap(sorted(rows, key=lambda r: r["account_code"]), a.get("max_rijen")),
                       "_verifieer": "account_code = accountKey.id (PCMN-rekeningnummer): verifieer actuele regel."})
    t.add("octopus_rekeningschema", "Rekeningschema", f"Grootboekrekeningen van een boekjaar via lokale synchronisatie ({lim('accounts')}, daarna {lim('accounts_modified')}).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id",)), accounts)

    def amounts(a):
        d = int(a["dossier_id"])
        by = t.resolve_by(d, a)
        rows = [x for x in t.sync.amounts(d, refresh=bool(a.get("vers"))) if x["boekjaar_id"] == by["boekjaar_id"]
                and (a.get("rekening") is None or x["account_code"] == str(a["rekening"]))]
        return t._out({"dossier_id": d, "boekjaar_id": by["boekjaar_id"], **cap(sorted(rows, key=lambda r: (r["account_code"], r["fiscal_period"] or 0)), a.get("max_rijen"))})
    t.add("octopus_rekeningsaldi", "Saldi per rekening per periode", f"Saldi per rekening per periode via synchronisatie ({lim('amounts_modified')}).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "rekening": {"type": "string"}, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id",)), amounts)

    t.add("octopus_proefbalans", "Proefbalans", "Proefbalans samengesteld uit rekeningen en saldi per periode (Octopus heeft geen proefbalans-endpoint). "
          "Saldo = debet - credit; controle op evenwicht en per klasse (MAR).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "tot_periode": {"type": "integer"}, "vanaf_periode": {"type": "integer"},
               "inclusief_nul": {"type": "boolean"}, "vers": S_VERS}, ("dossier_id",)), lambda a: t._out(t.tb(a)))

    def lines(a):
        d = int(a["dossier_id"])
        by = t.resolve_by(d, a)
        rows = t.sync.bookings(d, by["boekjaar_id"], refresh=bool(a.get("vers")))
        if a.get("rekening"):
            rows = [r for r in rows if r["rekening_code"] == str(a["rekening"])]
        if a.get("dagboektype"):
            rows = [r for r in rows if r["dagboektype"] == a["dagboektype"]]
        if a.get("periode") is not None:
            rows = [r for r in rows if r["periode"] == int(a["periode"])]
        return t._out({"dossier_id": d, "boekjaar_id": by["boekjaar_id"], **cap(rows, a.get("max_rijen"))})
    t.add("octopus_boekingslijnen", "Boekingslijnen", f"Boekingslijnen van een boekjaar via synchronisatie (eerste keer 4 calls per boekjaar, daarna 1; {lim('bookings_modified')}).",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "rekening": {"type": "string"},
               "dagboektype": {"type": "string", "enum": ["AANKOOP", "VERKOOP", "FINANCIEEL", "DIVERSEN"]}, "periode": {"type": "integer"},
               "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id",)), lines)

    def relations(a):
        d = int(a["dossier_id"])
        search = {k: a[k] for k in ("relatie_id", "extern_id", "naam", "btw_nummer") if a.get(k) not in (None, "")}
        if search:
            q = {"relationId": search.get("relatie_id"), "extRelationId": search.get("extern_id"), "name": search.get("naam"), "vatNr": search.get("btw_nummer")}
            data = t.client.call("relations", dossier_id=d, query=q, search=True, fresh=bool(a.get("vers"))) or []
            rows = [N.relation(r) for r in data]
        else:
            rows = t.sync.relations(d, refresh=bool(a.get("vers")))
        return t._out({"dossier_id": d, "zoeken": bool(search), **cap(sorted(rows, key=lambda r: str(r.get("naam") or "")), a.get("max_rijen"))})
    t.add("octopus_relaties", "Relaties", f"Klanten en leveranciers. Zonder zoekterm via synchronisatie ({lim('relations')}, daarna {lim('relations_modified')}); "
          f"met zoekterm rechtstreeks ({lim('relations', True)}).",
          obj({"dossier_id": S_DOSSIER, "relatie_id": {"type": "integer"}, "extern_id": {"type": "integer"}, "naam": {"type": "string"},
               "btw_nummer": {"type": "string"}, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id",)), relations)

    def costcentres(a):
        d = int(a["dossier_id"])
        data = t.client.call("costcentres_active" if a.get("alleen_actief") else "costcentres", dossier_id=d, fresh=bool(a.get("vers"))) or []
        return t._out({"dossier_id": d, **cap(data, a.get("max_rijen"))})
    t.add("octopus_kostenplaatsen", "Kostenplaatsen", f"Kostenplaatsen, optioneel alleen actieve ({lim('costcentres')}).",
          obj({"dossier_id": S_DOSSIER, "alleen_actief": {"type": "boolean"}, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id",)), costcentres)

    def envelopes(a):
        d = int(a["dossier_id"])
        if a.get("enveloppe_id") is not None:
            return t._out({"dossier_id": d, "gegevens": t.client.call("envelope", dossier_id=d, path_params={"enveloppeKeyId": a["enveloppe_id"]})})
        return t._out({"dossier_id": d, **cap(t.client.call("envelopes", dossier_id=d) or [], a.get("max_rijen"))})
    t.add("octopus_enveloppes", "Betalingsenveloppes", f"Betalingsenveloppes of de inhoud van één enveloppe (alleen lezen; {lim('envelopes')}).",
          obj({"dossier_id": S_DOSSIER, "enveloppe_id": {"type": "integer"}, "max_rijen": S_MAX}, ("dossier_id",)), envelopes)

    # ---------------------------------------------------------------- rapporten
    def history(a):
        d = int(a["dossier_id"])
        by_from = t.resolve_by(d, {"boekjaar_id": a.get("van_boekjaar_id")}) if a.get("van_boekjaar_id") is not None else t.resolve_by(d, a)
        by_to = t.resolve_by(d, {"boekjaar_id": a.get("tot_boekjaar_id")}) if a.get("tot_boekjaar_id") is not None else by_from
        body = {"fromBookyearKey": {"id": by_from["boekjaar_id"]}, "toBookyearKey": {"id": by_to["boekjaar_id"]},
                "fromBookyearPeriodNr": a.get("van_periode", t.period_range(by_from)[0]), "toBookyearPeriodNr": a.get("tot_periode", t.period_range(by_to)[1])}
        soort = a["soort"]
        if soort == "rekening":
            body["accountNr"] = int(a["rekening"])
            key = "history_accounts"
        elif soort in ("klant", "leverancier"):
            if a.get("relatie_id") is None and a.get("extern_id") is None:
                raise ValueError("relatie_id of extern_id is verplicht voor klant/leverancier.")
            body.update({k2: int(a[k1]) for k1, k2 in (("relatie_id", "relationId"), ("extern_id", "externalRelationId")) if a.get(k1) is not None})
            key = "history_clients" if soort == "klant" else "history_suppliers"
        else:
            body.update({"fromAccountNr": int(a.get("van_rekening", 0)), "toAccountNr": int(a.get("tot_rekening", 999999999)),
                         "showActiveCostCentres": True, "showInactiveCostCentres": bool(a.get("inactieve")), "showEmptyCostcentres": False})
            key = "history_costcentres"
        data = t.client.call(key, dossier_id=d, body=body, fresh=bool(a.get("vers"))) or []
        return t._out({"dossier_id": d, "query": body, **cap(data, a.get("max_rijen"))})
    t.add("octopus_historiek", "Historiek (rekening, klant, leverancier, kostenplaats)",
          f"Historiekrapport per rekening, klant, leverancier of kostenplaats over een boekjaar- en periodebereik ({lim('history_accounts')}).",
          obj({"dossier_id": S_DOSSIER, "soort": {"type": "string", "enum": ["rekening", "klant", "leverancier", "kostenplaats"]},
               "rekening": {"type": "integer"}, "relatie_id": {"type": "integer"}, "extern_id": {"type": "integer"},
               "boekjaar_id": S_BY, "jaar": S_JAAR, "van_boekjaar_id": {"type": "integer"}, "tot_boekjaar_id": {"type": "integer"},
               "van_periode": {"type": "integer"}, "tot_periode": {"type": "integer"}, "van_rekening": {"type": "integer"}, "tot_rekening": {"type": "integer"},
               "inactieve": {"type": "boolean"}, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id", "soort")), history)

    def open_items(a):
        d = int(a["dossier_id"])
        if a["soort"] == "rekening":
            by = t.resolve_by(d, a)
            body = {"fromBookyearKey": {"id": by["boekjaar_id"]}, "toBookyearKey": {"id": by["boekjaar_id"]},
                    "fromBookyearPeriodNr": t.period_range(by)[0], "toBookyearPeriodNr": t.period_range(by)[1], "accountNr": int(a["rekening"])}
            data = t.client.call("open_accounts", dossier_id=d, body=body, fresh=bool(a.get("vers"))) or []
            rows = [N.open_item(o, "rekening", a.get("peildatum") or t.today().isoformat()) for o in data]
        else:
            rows, body = t.open_items(d, a["soort"], a)
        return t._out({"dossier_id": d, "query": body, **cap(rows, a.get("max_rijen")),
                       "_verifieer": "Tekenconventie van openBookingAmount en de betekenis van het periodebereik: verifieer actuele regel."})
    t.add("octopus_openstaande_posten", "Openstaande posten", f"Openstaande posten van klanten (debiteuren), leveranciers (crediteuren) of één rekening ({lim('open_clients')}).",
          obj({"dossier_id": S_DOSSIER, "soort": {"type": "string", "enum": ["debiteuren", "crediteuren", "rekening"]}, "rekening": {"type": "integer"},
               "relatie_id": {"type": "integer"}, "boekjaar_id": S_BY, "jaar": S_JAAR, "van_boekjaar_id": {"type": "integer"}, "tot_boekjaar_id": {"type": "integer"},
               "peildatum": {"type": "string"}, "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id", "soort")), open_items)

    def aging(a):
        d = int(a["dossier_id"])
        rows, body = t.open_items(d, a["soort"], a)
        peil = date.fromisoformat(a.get("peildatum") or t.today().isoformat())
        res = analytics.aging(rows, peil)
        rij = res.pop("rijen")
        return t._out({"dossier_id": d, "soort": a["soort"], **res, **{"top": sorted(rij, key=lambda r: -(r["open_bedrag"] or 0))[: int(a.get("max_rijen") or 20)]}})
    t.add("octopus_ouderdom_openstaande_posten", "Ouderdom openstaande posten", f"Ouderdomsanalyse (niet vervallen, 0-30, 31-60, 61-90, >90 dagen, zonder datum, negatief) ({lim('open_clients')}).",
          obj({"dossier_id": S_DOSSIER, "soort": {"type": "string", "enum": ["debiteuren", "crediteuren"]}, "peildatum": {"type": "string"},
               "vers": S_VERS, "max_rijen": S_MAX}, ("dossier_id", "soort")), aging)

    t.add("octopus_dashboard_kpis", "Kerncijfers", "Kerncijfers uit de samengestelde proefbalans (omzet, kosten, resultaat, liquide middelen, btw-indicatie) "
          "plus open debiteuren/crediteuren. Indeling volgens het Belgische MAR.",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "periode": {"type": ["string", "integer"], "description": "'jaar' of periodenummer"},
               "vergelijk_vorige_periode": {"type": "boolean"}, "inclusief_open_posten": {"type": "boolean"}, "vers": S_VERS}, ("dossier_id",)), t.kpis)

    def error_sample(a):
        try:
            t.client.call("error_sample", query={"errorCode": int(a["foutcode"]), "localeId": a.get("taal_id", t.client.s.locale_id)}, use_cache=False)
            return {"bron": SOURCE_ERR, "foutobject": None}
        except OctopusApiError as exc:
            return {"bron": SOURCE_ERR, "foutobject": exc.as_dict(), "uitleg": "Octopus geeft voor dit endpoint altijd HTTP 400 met een voorbeeld-foutobject."}
    t.add("octopus_foutcode_uitleg", "Foutcode uitleggen", f"Vraagt het voorbeeld-foutobject voor een Octopus-foutcode op ({lim('error_sample')}).",
          obj({"foutcode": {"type": "integer"}, "taal_id": {"type": "integer", "enum": [0, 1, 2, 3, 4]}}, ("foutcode",)), error_sample)

    # ---------------------------------------------------------------- synchronisatie
    def do_sync(a):
        d = int(a["dossier_id"])
        parts = a.get("onderdelen") or ["rekeningen", "saldi", "relaties", "boekingen"]
        out: dict = {}
        by = t.resolve_by(d, a) if any(p in parts for p in ("rekeningen", "boekingen")) else None
        before = len(t.client.calls)
        if "rekeningen" in parts:
            out["rekeningen"] = len(t.sync.accounts(d, by["boekjaar_id"], refresh=True))
        if "saldi" in parts:
            out["saldi"] = len(t.sync.amounts(d, refresh=True))
        if "relaties" in parts:
            out["relaties"] = len(t.sync.relations(d, refresh=True))
        if "boekingen" in parts:
            out["boekingslijnen"] = len(t.sync.bookings(d, by["boekjaar_id"], refresh=True))
        return t._out({"dossier_id": d, "boekjaar_id": by["boekjaar_id"] if by else None, "aantallen": out, "calls": len(t.client.calls) - before,
                       "opslag": t.client.store.describe(), "status": t.sync.status(d)})
    t.add("octopus_sync", "Synchroniseren", "Haalt rekeningen, saldi, relaties en boekingen op en houdt ze lokaal bij via de gewijzigd-sinds-endpoints "
          "(eerste keer volledig, daarna alleen wijzigingen). Versleuteld op schijf met OCTOPUS_CACHE_KEY, anders alleen in het geheugen.",
          obj({"dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR,
               "onderdelen": {"type": "array", "items": {"type": "string", "enum": ["rekeningen", "saldi", "relaties", "boekingen"]}}}, ("dossier_id",)), do_sync)
    t.add("octopus_sync_status", "Synchronisatiestatus", "Watermerken en aantallen van de lokale synchronisatie. Doet geen call.",
          obj({"dossier_id": S_DOSSIER}, ("dossier_id",)), lambda a: {"bron": "lokale opslag", "dossier_id": a["dossier_id"],
                                                                      "status": t.sync.status(int(a["dossier_id"])), "opslag": t.client.store.describe()}, LOCAL)

    # ---------------------------------------------------------------- export en overdracht
    from .exporting import export_dataset, export_schema
    from .transfer import ESTIMATE_SCHEMA, TRANSFER_SCHEMA, estimate_tool, transfer_tool
    t.add("octopus_export_dataset", "Dataset exporteren", "Schrijft een dataset (kpis, saldi, proefbalans, openstaande_posten, boekingslijnen, rekeningschema, relaties) "
          "naar CSV, JSON, Excel of Parquet in een lokale map. Schrijft nooit naar Octopus.",
          obj({"dataset": {"type": "string", "enum": ["kpis", "saldi", "proefbalans", "openstaande_posten", "boekingslijnen", "rekeningschema", "relaties"]},
               "dossier_id": S_DOSSIER, "boekjaar_id": S_BY, "jaar": S_JAAR, "periode": {"type": ["string", "integer"]}, "soort": {"type": "string", "enum": ["debiteuren", "crediteuren"]},
               "formaten": {"type": "array", "items": {"type": "string", "enum": ["csv", "json", "xlsx", "parquet"]}}, "export_map": {"type": "string"}},
              ("dataset", "dossier_id", "export_map")), lambda a: export_dataset(t, a), {**LOCAL, "openWorldHint": True})
    t.add("octopus_export_schema", "Exportschema", "Kolommen en types van de exportdatasets (voor Power BI, Excel, databanken). Doet geen call.",
          obj({"dataset": {"type": "string"}}), lambda a: export_schema(a.get("dataset")), LOCAL)
    t.add("octopus_dossier_transfer_schatting", "Dossieroverdracht: schatting", "Schat het aantal calls per endpoint voor een overdracht per boekjaar en vergelijkt met de resterende daglimieten.",
          ESTIMATE_SCHEMA, lambda a: estimate_tool(t, a), RO)
    t.add("octopus_dossier_transfer_export", "Dossieroverdracht per boekjaar", "Volledig overdrachtspakket per boekjaar voor de volgende boekhouder: rekeningschema, proefbalans, "
          "boekingslijnen, openstaande posten, relaties, btw-codes, dagboeken, CONTROL.md, MANIFEST.json (SHA-256) en README. Alleen lezen; hervatbaar.",
          TRANSFER_SCHEMA, lambda a: transfer_tool(t, a), {**RO, "idempotentHint": False})

    # ---------------------------------------------------------------- gratis officiële hulpdiensten
    def vat(a):
        res = {"offline": be_vat.check(a["btw_nummer"]) if a["btw_nummer"].upper().replace(" ", "").startswith(("BE", "0", "1")) else None}
        if a.get("vies"):
            res["vies"] = vies.check(a["btw_nummer"])
        return {"bron": "offline controle" + (" + VIES (Europese Commissie, gratis)" if a.get("vies") else ""), **res}
    t.add("octopus_btw_nummer_controle", "Btw-nummer controleren", "Offline controle van een Belgisch btw-nummer (modulo 97) en optioneel een VIES-check bij de Europese Commissie "
          "(gratis, geen sleutel; alleen het nummer wordt verstuurd).",
          obj({"btw_nummer": {"type": "string"}, "vies": {"type": "boolean"}}, ("btw_nummer",)), vat, {**LOCAL, "openWorldHint": True})
    t.add("octopus_wisselkoers_ecb", "ECB-wisselkoers", "Euro-referentiekoers van de ECB voor een munt (gratis, ter informatie).",
          obj({"munt": {"type": "string"}, "datum": {"type": "string"}}, ("munt",)), lambda a: ecb.rate(a["munt"], a.get("datum")), {**LOCAL, "openWorldHint": True})

    # ---------------------------------------------------------------- schrijven (standaard UIT)
    if t.client_settings_write_enabled():
        from .write import register_write
        register_write(t)


SOURCE_ERR = "Octopus /error (voorbeeld-foutobject)"

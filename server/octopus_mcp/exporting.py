"""Exportlaag: vaste, gedocumenteerde datasets via de neutrale kern (accounting_api_core.export). Alleen lokale bestanden."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from accounting_api_core import analytics, export as X
from accounting_api_core.attribution import ATTRIBUTION, ensure
from accounting_api_core.branding import BE_NOTICE

X.register("proefbalans", [("administratie", "text", "Dossier (id)"), ("boekjaar_id", "text", "Boekjaar-id"), ("rekening_code", "text", "Grootboekrekening (PCMN)"),
                           ("rekening_naam", "text", "Naam van de rekening"), ("klasse", "text", "Klasse 0-7 (MAR)"), ("debet", "number", "Debetsaldo"),
                           ("credit", "number", "Creditsaldo"), ("saldo", "number", "Saldo = debet - credit")])
X.register("boekingslijnen", [("administratie", "text", "Dossier (id)"), ("boekjaar_id", "text", "Boekjaar-id"), ("dagboektype", "text", "AANKOOP, VERKOOP, FINANCIEEL of DIVERSEN"),
                              ("dagboek_nr", "text", "Dagboeknummer"), ("document_nr", "text", "Documentnummer"), ("lijn_nr", "text", "Lijnnummer"), ("periode", "text", "Periode"),
                              ("documentdatum", "date", "Documentdatum"), ("vervaldatum", "date", "Vervaldatum"), ("rekening_code", "text", "Rekening"),
                              ("relatie_id", "text", "Relatie-id"), ("bedrag", "number", "Bedrag in EUR (teken volgens Octopus)"), ("munt", "text", "Munt"),
                              ("btw_rubriek", "text", "Btw-rubriek"), ("omschrijving", "text", "Omschrijving"), ("referentie", "text", "Referentie")])
X.register("rekeningschema", [("administratie", "text", "Dossier (id)"), ("boekjaar_id", "text", "Boekjaar-id"), ("account_code", "text", "Rekeningnummer"),
                              ("account_name", "text", "Naam"), ("klasse", "text", "Klasse 0-7"), ("btw_code_aankoop", "text", "Standaard btw-code aankoop"),
                              ("btw_code_verkoop", "text", "Standaard btw-code verkoop")])
X.register("relaties", [("administratie", "text", "Dossier (id)"), ("relatie_id", "text", "Relatie-id"), ("naam", "text", "Naam"), ("klant", "text", "Klant (true/false)"),
                        ("leverancier", "text", "Leverancier (true/false)"), ("btw_nummer", "text", "Btw-nummer"), ("postcode", "text", "Postcode"),
                        ("gemeente", "text", "Gemeente"), ("land", "text", "Land"), ("actief", "text", "Actief")])

UNITS = {"liquide_middelen": "EUR", "_verifieer": "tekst"}


def export_schema(dataset: str | None) -> dict:
    if dataset:
        if dataset not in X.SCHEMAS:
            raise ValueError(f"Onbekende dataset. Kies uit {', '.join(sorted(X.SCHEMAS))}.")
        return {"dataset": dataset, "kolommen": X.schema_doc(dataset)}
    return {"datasets": {k: X.schema_doc(k) for k in sorted(X.SCHEMAS)}, "formaten": list(X.FORMATS)}


def rows_for(t, a: dict) -> tuple[list[dict], dict]:
    ds, d = a["dataset"], int(a["dossier_id"])
    adm = str(d)
    if ds == "kpis":
        k = t.kpis({x: a[x] for x in ("dossier_id", "boekjaar_id", "jaar", "periode") if x in a})
        by = k["boekjaar"]
        rows = []
        for name, v in k.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and name != "dossier_id":
                rows.append({"administratie": adm, "periode_van": by.get("start"), "periode_tot": by.get("einde"), "peildatum": date.today().isoformat(),
                             "kpi": name, "waarde": v, "eenheid": "EUR"})
            elif isinstance(v, dict) and name.startswith("open_"):
                for sub in ("totaal", "vervallen"):
                    if isinstance(v.get(sub), (int, float)):
                        rows.append({"administratie": adm, "periode_van": by.get("start"), "periode_tot": by.get("einde"), "peildatum": date.today().isoformat(),
                                     "kpi": f"{name}_{sub}", "waarde": v[sub], "eenheid": "EUR"})
        return rows, {"boekjaar": by}
    if ds in ("saldi", "proefbalans"):
        tb = t.tb({x: a[x] for x in ("dossier_id", "boekjaar_id", "jaar") if x in a})
        by = tb["boekjaar"]
        if ds == "saldi":
            return [{"administratie": adm, "peildatum": by.get("einde"), "rekening_code": r["rekening_code"], "rekening_naam": r["rekening_naam"], "saldo": r["saldo"]}
                    for r in tb["rows"]], {"boekjaar": by, "in_evenwicht": tb["in_evenwicht"]}
        return [{"administratie": adm, "boekjaar_id": by["boekjaar_id"], **{k: r[k] for k in ("rekening_code", "rekening_naam", "klasse", "debet", "credit", "saldo")}}
                for r in tb["rows"]], {"boekjaar": by, "in_evenwicht": tb["in_evenwicht"]}
    if ds == "openstaande_posten":
        soort = a.get("soort") or "debiteuren"
        rows, _ = t.open_items(d, soort, a)
        peil = date.fromisoformat(t.today().isoformat())
        ag = analytics.aging(rows, peil)
        return [{"administratie": adm, **r} for r in ag["rijen"]], {"soort": soort}
    if ds == "boekingslijnen":
        by = t.resolve_by(d, a)
        return [{"administratie": adm, **r} for r in t.sync.bookings(d, by["boekjaar_id"])], {"boekjaar_id": by["boekjaar_id"]}
    if ds == "rekeningschema":
        by = t.resolve_by(d, a)
        return [{"administratie": adm, **r} for r in t.sync.accounts(d, by["boekjaar_id"])], {"boekjaar_id": by["boekjaar_id"]}
    if ds == "relaties":
        return [{"administratie": adm, **r} for r in t.sync.relations(d)], {}
    raise ValueError("Onbekende dataset.")


def export_dataset(t, a: dict) -> dict:
    fmts = a.get("formaten") or ["csv"]
    rows, extra = rows_for(t, a)
    meta = {"bron": "Octopus (alleen lezen)", "attributie": ATTRIBUTION, "scope": BE_NOTICE["nl"], "dossier_id": a["dossier_id"], **extra}
    ensure(meta["attributie"], True)                     # weigert de export als de verplichte vermelding gewijzigd is
    files = X.write_all(Path(a["export_map"]).expanduser(), a["dataset"], rows, fmts, meta)
    return {"dataset": a["dataset"], "rijen": len(rows), "bestanden": files, "formaten": fmts, "attributie": ATTRIBUTION}

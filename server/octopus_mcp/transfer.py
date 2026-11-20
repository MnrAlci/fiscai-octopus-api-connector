"""Dossieroverdracht per boekjaar (voor de volgende boekhouder/confrater). Alleen lezen in Octopus; schrijft lokale bestanden.

Per boekjaar een map met boekjaar, dagboeken, rekeningschema, proefbalans (samengesteld), boekingslijnen en openstaande posten
(klanten/leveranciers) op het einde van het boekjaar; op dossierniveau relaties, btw-codes en kostenplaatsen. Daarbij CONTROL.md,
MANIFEST.json (rijen + SHA-256) en README.md voor de ontvanger. Een onderbroken export (bv. daglimiet bereikt) hervat via een checkpoint.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from accounting_api_core import trial_balance
from accounting_api_core.attribution import ensure
from accounting_api_core.branding import BE_NOTICE
from accounting_api_core.model import D, money
from accounting_api_core.quota import QuotaExceeded
from accounting_api_core.transfer import TransferPackage, estimate

from . import __version__, edition
from . import normalize as N
from .endpoints import get

S_YEARS = {"type": "array", "items": {"type": "integer"}, "description": "Boekjaar-id's; leeg = alle boekjaren"}
ESTIMATE_SCHEMA = {"type": "object", "properties": {"dossier_id": {"type": "integer"}, "boekjaren": S_YEARS}, "required": ["dossier_id"], "additionalProperties": False}
TRANSFER_SCHEMA = {"type": "object", "properties": {
    "dossier_id": {"type": "integer"}, "boekjaren": S_YEARS, "export_map": {"type": "string"},
    "formaten": {"type": "array", "items": {"type": "string", "enum": ["csv", "json", "xlsx"]}},
    "inclusief_boekingslijnen": {"type": "boolean"}, "zip": {"type": "boolean"},
    "bevestig": {"type": "boolean", "description": "true na het bekijken van de schatting (aantal calls per endpoint)"}},
    "required": ["dossier_id", "export_map"], "additionalProperties": False}


def _years(t, d: int, a: dict) -> list[dict]:
    bys = sorted(t.bookyears(d), key=lambda b: str(b.get("start") or ""))
    want = a.get("boekjaren")
    if want:
        sel = [b for b in bys if b["boekjaar_id"] in set(int(x) for x in want)]
        if len(sel) != len(set(want)):
            raise ValueError("Niet alle gevraagde boekjaren bestaan in dit dossier.")
        return sel
    return bys


def plan(t, d: int, years: list[dict], with_lines: bool = True) -> dict:
    st = t.sync.state
    acc_loaded = set(st.load(f"{d}:accounts")["meta"].get("bookyears", []))
    bk_loaded = set(st.load(f"{d}:bookings")["meta"].get("bookyears", []))
    n = len(years)
    p = {get("bookyear").quota_key(): n, get("journals").quota_key(): n,
         get("accounts").quota_key(): sum(1 for y in years if y["boekjaar_id"] not in acc_loaded),
         get("amounts_modified").quota_key(): 1 if st.is_initial(f"{d}:amounts") else 0,
         get("open_clients").quota_key(): n, get("open_suppliers").quota_key(): n,
         get("relations").quota_key(): 1 if st.is_initial(f"{d}:relations") else 0,
         get("vatcodes").quota_key(): 1, get("costcentres").quota_key(): 1, get("dossier_token").quota_key(): 3}
    if with_lines:
        p[get("bookings_modified").quota_key()] = 4 * sum(1 for y in years if y["boekjaar_id"] not in bk_loaded)
    return {k: v for k, v in p.items() if v}


def estimate_tool(t, a: dict) -> dict:
    d = int(a["dossier_id"])
    years = _years(t, d, a)
    p = plan(t, d, years)
    est = estimate(p, {k: t.client.quota.remaining(k) for k in p})
    return {"bron": "Octopus (alleen lezen)", "dossier_id": d, "boekjaren": [y["boekjaar_id"] for y in years], **est,
            "uitleg": "Stamdata (rekeningen per boekjaar, relaties, btw-codes) mogen 2 keer per dag. Past het niet vandaag, dan hervat de export morgen via het checkpoint."}


def _controls(tb: dict, lines: list[dict] | None, open_c: list[dict], open_s: list[dict], mode: str) -> list[dict]:
    checks = [{"controle": "Proefbalans in evenwicht (debet = credit)", "ok": tb["in_evenwicht"], "detail": f"verschil {tb['totals']['verschil']}"}]
    if lines is not None and mode == "movement":
        per = defaultdict(Decimal)
        for r in lines:
            per[r["rekening_code"]] += D(r["bedrag"])
        tbm = {r["rekening_code"]: D(r["saldo"]) for r in tb["rows"]}
        diff = [c for c in set(per) | set(tbm) if money(per.get(c, 0)) != money(tbm.get(c, 0))]
        checks.append({"controle": "Som boekingslijnen per rekening = saldo proefbalans", "ok": not diff,
                       "detail": "alle rekeningen sluiten aan" if not diff else f"{len(diff)} rekening(en) wijken af (beginbalans, modus of teken: verifieer actuele regel)"})
    else:
        checks.append({"controle": "Som boekingslijnen per rekening = saldo proefbalans", "ok": None, "detail": "niet uitgevoerd (zonder boekingslijnen of modus cumulative)"})
    for label, rows, pref in (("klanten", open_c, "40"), ("leveranciers", open_s, "44")):
        tot = sum((D(r["open_bedrag"]) for r in rows), Decimal(0))
        bal = sum((D(r["saldo"]) for r in tb["rows"] if r["rekening_code"].startswith(pref)), Decimal(0))
        bal = -bal if pref == "44" else bal
        checks.append({"controle": f"Openstaande {label} t.o.v. saldo rekeningen {pref}*", "ok": True if money(tot) == money(bal) else None,
                       "detail": f"open posten {money(tot)}; saldo {pref}* {money(bal)} (indicatie: andere rekeningen of tekenconventie mogelijk)"})
    res = -sum((D(r["saldo"]) for r in tb["rows"] if r["klasse"] in (6, 7)), Decimal(0))
    checks.append({"controle": "Resultaat van het boekjaar (opbrengsten - kosten)", "ok": None, "detail": f"{money(res)} (informatief)"})
    return checks


def transfer_tool(t, a: dict) -> dict:
    d = int(a["dossier_id"])
    t.client.check_dossier(d)
    years = _years(t, d, a)
    with_lines = a.get("inclusief_boekingslijnen", True)
    p = plan(t, d, years, with_lines)
    est = estimate(p, {k: t.client.quota.remaining(k) for k in p})
    if not a.get("bevestig"):
        return {"status": "bevestiging_nodig", "schatting": est, "boekjaren": [y["boekjaar_id"] for y in years],
                "uitleg": "Bekijk de schatting en roep opnieuw aan met bevestig=true. Er werd nog niets geëxporteerd."}
    pkg = TransferPackage(Path(a["export_map"]), "Octopus", a.get("formaten") or ["csv", "json"])
    status = "klaar"
    stop_reason = None
    try:
        if not pkg.done("dossier"):
            root = pkg.out / "dossier"
            root.mkdir(exist_ok=True)
            pkg.write(root, "relaties", t.sync.relations(d))
            pkg.write(root, "btw-codes", [N.vatcode(v) for v in (t.client.call("vatcodes", dossier_id=d) or [])])
            pkg.write(root, "kostenplaatsen", t.client.call("costcentres", dossier_id=d) or [])
            pkg.write(root, "boekjaren", [{k: v for k, v in y.items() if k != "perioden"} | {"perioden": len(y.get("perioden") or [])} for y in years])
            pkg.mark("dossier")
        for y in years:
            by = y["boekjaar_id"]
            step = f"jaar:{by}"
            if pkg.done(step):
                continue
            folder = pkg.year_dir(f"{by}-{str(y.get('einde') or '')[:4]}")
            pkg.write(folder, "boekjaar", [t.client.call("bookyear", dossier_id=d, path_params={"bookyearId": by}) or {}])
            pkg.write(folder, "dagboeken", [N.journal(j) for j in (t.client.call("journals", dossier_id=d, path_params={"bookyearId": by}) or [])])
            accs = t.sync.accounts(d, by)
            pkg.write(folder, "rekeningschema", accs)
            amts = [x for x in t.sync.amounts(d) if x["boekjaar_id"] == by]
            tb = trial_balance.build(accs, amts, mode=t.client.s.amounts_mode)
            pkg.write(folder, "proefbalans-einde", tb["rows"], {"in_evenwicht": tb["in_evenwicht"], "totals": tb["totals"]})
            lines = None
            if with_lines:
                lines = t.sync.bookings(d, by)
                pkg.write(folder, "boekingslijnen", lines)
            first = years[0]
            oc, _ = t.open_items(d, "debiteuren", {"van_boekjaar_id": first["boekjaar_id"], "tot_boekjaar_id": by, "peildatum": y.get("einde")})
            os_, _ = t.open_items(d, "crediteuren", {"van_boekjaar_id": first["boekjaar_id"], "tot_boekjaar_id": by, "peildatum": y.get("einde")})
            pkg.write(folder, "openstaande-klanten-einde", oc)
            pkg.write(folder, "openstaande-leveranciers-einde", os_)
            pkg.control(f"Boekjaar {by} ({y.get('start')} - {y.get('einde')})", _controls(tb, lines, oc, os_, t.client.s.amounts_mode))
            pkg.mark(step)
    except QuotaExceeded as exc:
        status, stop_reason = "onderbroken", str(exc)
    pkg.write_control_md("Controles dossieroverdracht")
    pkg.write_readme(ensure(readme([y["boekjaar_id"] for y in years], pkg.formats, with_lines), True))
    man = pkg.write_manifest({"connector": edition.DISPLAY_NAME, "versie": __version__, "dossier_id": d, "boekjaren": [y["boekjaar_id"] for y in years],
                              "status": status, "modus_saldi": t.client.s.amounts_mode})
    out = {"status": status, "export_map": str(pkg.out), "manifest": str(man), "bestanden": len(pkg.cp["files"]), "reden": stop_reason}
    if status == "klaar":
        pkg.finish()
        if a.get("zip"):
            out["zip"] = str(pkg.zip())
    else:
        out["hervatten"] = "Voer dezelfde opdracht later opnieuw uit (bv. morgen); reeds geëxporteerde onderdelen worden overgeslagen."
    return out


def readme(years: list, formats: list, with_lines: bool) -> str:
    return f"""# Dossieroverdracht (Octopus): pakket per boekjaar

{BE_NOTICE['nl']}

## Voor de ontvangende boekhouder
Dit pakket is automatisch samengesteld met alleen-lezen toegang tot Octopus. Boekjaren (id): {', '.join(map(str, years))}.

| Bestand | Inhoud |
|---|---|
| `dossier/relaties` | Klanten en leveranciers (eerste synchronisatie: actieve relaties; daarna ook wijzigingen) |
| `dossier/btw-codes`, `dossier/kostenplaatsen`, `dossier/boekjaren` | Stamdata van het dossier |
| `boekjaar-*/boekjaar`, `dagboeken` | Gegevens van het boekjaar en de dagboeken |
| `boekjaar-*/rekeningschema` | Grootboekrekeningen zoals Octopus ze geeft (Belgisch MAR/PCMN; niet hernummerd) |
| `boekjaar-*/proefbalans-einde` | Proefbalans samengesteld uit saldi per rekening per periode (Octopus heeft geen proefbalans-endpoint; saldo = debet - credit) |
| `boekjaar-*/boekingslijnen` | {'Alle boekingslijnen van het boekjaar' if with_lines else 'Niet opgenomen (op vraag van de afzender)'} |
| `boekjaar-*/openstaande-klanten-einde`, `-leveranciers-einde` | Openstaande posten tot en met de laatste periode van het boekjaar |
| `CONTROL.md` | Afstemmingen (evenwicht, boekingen = saldi, open posten t.o.v. 40/44) |
| `MANIFEST.json` | Bestanden met rijen en SHA-256 om de integriteit te controleren |

Formaten: {', '.join(formats)}. CSV is UTF-8 met komma als scheidingsteken en punt als decimaalteken. JSON bevat `rows`.

## Beperkingen (verifieer actuele regel)
- Geen proefbalans-endpoint: de proefbalans is samengesteld; de betekenis van de periodesaldi (beweging of cumulatief) en de tekenconventie zijn te verifiëren.
- Geen activaregister of afschrijvingstabellen via de gebruikte endpoints; geen bijlagen (file sync API niet gebruikt).
- Daglimieten per endpoint: een onderbroken export wordt later hervat.

## Professionele en wettelijke punten
Dit pakket is een technische hulp, geen juridisch advies en geen vervanging van de overdracht tussen beroepsbeoefenaars.
- **Deontologie**: volg de regels van uw beroepsinstituut voor de overdracht van een dossier en de communicatie met de confrater. Verifieer de actuele regels bij het instituut.
- **Klant en toestemming**: zorg dat de klant op de hoogte is en dat u een rechtsgrond heeft; de klant blijft eigenaar van zijn gegevens.
- **GDPR**: het pakket bevat persoonsgegevens. Beperk de verspreiding, bewaar het versleuteld en verwijder kopieën die u niet meer nodig heeft. Zie https://www.gegevensbeschermingsautoriteit.be
- **Veilig overmaken**: gebruik een versleutelde zip of een beveiligd platform, deel het wachtwoord via een ander kanaal en deel de SHA-256 uit `MANIFEST.json` apart.
- **Bewaartermijnen**: de wettelijke bewaartermijn voor boekhoudkundige stukken blijft gelden; verifieer de actuele regel bij https://financien.belgium.be/nl

Powered by FISCALCI Accounting & Tax (Askin Alci)
"""

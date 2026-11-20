"""Dossieroverdracht per boekjaar en export: schatting, bevestiging, controles, MANIFEST (SHA-256), hervatten, attributie."""
import csv
import hashlib
import json

from conftest import DOS

ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"


def test_schatting_zonder_calls_naar_data(tools, fake):
    r = tools.call("octopus_dossier_transfer_schatting", {"dossier_id": DOS, "boekjaren": [2]})
    assert r["schatting"] if "schatting" in r else r
    flat = json.dumps(r)
    assert "GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified" in flat
    assert all(not p["path"].endswith(("/accounts", "/bookings/modified")) for p in fake.requests)


def test_overdracht_vraagt_bevestiging(tools, tmp_path):
    r = tools.call("octopus_dossier_transfer_export", {"dossier_id": DOS, "boekjaren": [2], "export_map": str(tmp_path / "o")})
    assert r["status"] == "bevestiging_nodig" and not (tmp_path / "o").exists()


def test_volledige_overdracht(tools, tmp_path):
    out = tmp_path / "o"
    r = tools.call("octopus_dossier_transfer_export", {"dossier_id": DOS, "boekjaren": [2], "export_map": str(out), "bevestig": True, "zip": True})
    assert r["status"] == "klaar", r
    man = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    files = man["bestanden"]
    assert files and man["attributie"] == ATTR and man["controles_ok"] is True and man["status"] == "klaar"
    for name, f in files.items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == f["sha256"]
    names = set(files)
    assert any("proefbalans-einde.csv" in n for n in names) and any("boekingslijnen.csv" in n for n in names)
    assert any("openstaande-klanten-einde" in n for n in names) and any(n.startswith("dossier/relaties") for n in names)
    control = (out / "CONTROL.md").read_text(encoding="utf-8")
    assert "AFWIJKING" not in control and control.count("| OK |") >= 4
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert ATTR in readme and ("België" in readme or "Belgi" in readme)
    assert r["zip"].endswith(".zip")
    rows = list(csv.DictReader(open(next(out.rglob("proefbalans-einde.csv")), encoding="utf-8")))
    assert len(rows) == 8


def test_overdracht_onderbroken_en_hervat(tools, fake, tmp_path):
    from accounting_api_core.quota import QuotaExceeded
    out = tmp_path / "o"
    real = tools.client.call
    state = {"block": True}

    def flaky(key, **kw):
        if key == "open_suppliers" and state["block"]:
            raise QuotaExceeded("POST /dossiers/{dossierId}/reports/suppliers/open", 24, 24)
        return real(key, **kw)
    tools.client.call = flaky
    r = tools.call("octopus_dossier_transfer_export", {"dossier_id": DOS, "boekjaren": [2], "export_map": str(out), "bevestig": True})
    assert r["status"] == "onderbroken" and "hervatten" in r
    state["block"] = False
    n_before = fake.count("GET", "/vatcodes")
    r = tools.call("octopus_dossier_transfer_export", {"dossier_id": DOS, "boekjaren": [2], "export_map": str(out), "bevestig": True})
    assert r["status"] == "klaar" and fake.count("GET", "/vatcodes") == n_before   # dossierdeel niet opnieuw


def test_controle_detecteert_onevenwicht(tools, fake, tmp_path):
    fake.data["amounts"].append({"accountAmountKey": {"bookyearPeriodKey": {"bookyearKey": {"id": 2}, "bookyearPeriodNr": 6},
                                                      "accountKey": {"bookyearKey": {"id": 2}, "id": 700000}}, "balance": -1.0})
    out = tmp_path / "o"
    tools.call("octopus_dossier_transfer_export", {"dossier_id": DOS, "boekjaren": [2], "export_map": str(out), "bevestig": True})
    c = (out / "CONTROL.md").read_text(encoding="utf-8")
    assert "| Proefbalans in evenwicht (debet = credit) | AFWIJKING |" in c
    assert json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))["controles_ok"] is False


def test_export_dataset_formaten_en_attributie(tools, tmp_path):
    r = tools.call("octopus_export_dataset", {"dataset": "proefbalans", "dossier_id": DOS, "jaar": 2026, "export_map": str(tmp_path), "formaten": ["csv", "json", "xlsx"]})
    assert r["rijen"] == 8 and len(r["bestanden"]) == 3 and r["attributie"] == ATTR
    js = json.loads(open([f for f in r["bestanden"] if f.endswith(".json")][0], encoding="utf-8").read())
    assert ATTR in json.dumps(js)


def test_export_schema(tools, fake):
    s = tools.call("octopus_export_schema", {"dataset": "proefbalans"})
    assert "rekening_code" in json.dumps(s) and fake.requests == []

"""Synchronisatie via de gewijzigd-sinds-endpoints: eerste lading, daarna alleen wijzigingen, verwijderingen, opslag."""
import pytest

from conftest import DOS, FAKE_CACHE


def _bk(q):
    return [r for r in q if r["path"].endswith("/bookings/modified")]


def test_eerste_lading_per_dagboektype_en_daarna_min1(tools, fake):
    tools.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026, "onderdelen": ["boekingen"]})
    first = _bk(fake.requests)
    assert [r["query"]["journalTypeId"] for r in first] == ["1", "2", "3", "4"]
    assert all(r["path"] == "/dossiers/101/bookyears/2/bookings/modified" and r["query"]["modifiedTimeStamp"] == "1980-01-01 00:00:00.000" for r in first)
    tools.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026, "onderdelen": ["boekingen"]})
    nxt = _bk(fake.requests)[4:]
    assert len(nxt) == 1 and nxt[0]["path"] == "/dossiers/101/bookyears/-1/bookings/modified" and nxt[0]["query"]["journalTypeId"] == "-1"
    assert nxt[0]["query"]["modifiedTimeStamp"] != "1980-01-01 00:00:00.000"


def test_wijziging_en_verwijdering_samengevoegd(tools, fake):
    tools.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026, "onderdelen": ["boekingen"]})
    mod = dict(fake.data["bookings"][0], bookingAmount=550.0, comment="[Voorbeeld] gewijzigd")
    last = fake.data["bookings"][-1]
    deleted = {"bookyearKey": last["bookyearKey"], "journalType": last["journalType"], "journalSequenceNr": last["journalNr"],
               "documentSequenceNr": last["documentSequenceNr"]}   # DocumentKey volgens de spec
    fake.modified[("bookings", -1, -1)] = {"modifiedBookings": [mod], "deletedBookings": [deleted]}
    r = tools.call("octopus_boekingslijnen", {"dossier_id": DOS, "jaar": 2026, "vers": True})
    assert r["aantal"] == 8          # document 1 van type 3 (2 lijnen) verwijderd
    assert any(x["bedrag"] == 550.0 and x["omschrijving"] == "[Voorbeeld] gewijzigd" for x in r["rijen"])


def test_rekeningen_eerst_volledig_dan_gewijzigd(tools, fake):
    tools.call("octopus_rekeningschema", {"dossier_id": DOS, "jaar": 2026})
    assert fake.count("GET", "/accounts") == 1
    new = dict(fake.data["accounts"][-1], description={"description_NL": "Omzet [Voorbeeld] nieuw"})
    fake.modified["accounts"] = {"modified": [new], "deleted": []}
    r = tools.call("octopus_rekeningschema", {"dossier_id": DOS, "jaar": 2026, "vers": True})
    assert fake.count("GET", "/accounts") == 1 and fake.count("GET", "/accounts/modified") == 1
    assert {x["account_code"]: x["account_name"] for x in r["rijen"]}["700000"] == "Omzet [Voorbeeld] nieuw"


def test_saldi_gewijzigd_vervangt_per_sleutel(tools, fake):
    tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026})
    k = next(a["accountAmountKey"] for a in fake.data["amounts"] if a["accountAmountKey"]["accountKey"]["id"] == 550000
             and a["accountAmountKey"]["bookyearPeriodKey"]["bookyearPeriodNr"] == 1 and a["accountAmountKey"]["bookyearPeriodKey"]["bookyearKey"]["id"] == 2)
    fake.modified["amounts"] = {"modified": [{"accountAmountKey": k, "balance": 6000.0}], "deleted": []}
    r = tools.call("octopus_rekeningsaldi", {"dossier_id": DOS, "jaar": 2026, "rekening": "550000", "vers": True})
    assert [x["amount"] for x in r["rijen"] if x["fiscal_period"] == 1] == [6000.0]


def test_sync_status_en_reset_via_cli_cache_clear(tools):
    tools.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026})
    st = tools.call("octopus_sync_status", {"dossier_id": DOS})
    assert st["status"]["bookings"]["records"] == 10 and st["status"]["accounts"]["meta"]["bookyears"] == [2]
    assert st["opslag"]["persistent"] is False   # zonder OCTOPUS_CACHE_KEY alleen in het geheugen


def test_versleutelde_opslag_met_sleutel(make_client, env):
    from datetime import date
    from octopus_mcp.tools import Tools
    t = Tools(make_client(OCTOPUS_CACHE_KEY=FAKE_CACHE), today=lambda: date(2026, 11, 20))
    t.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026})
    files = [p for p in (env / "data").rglob("*") if p.is_file()]
    assert files
    blob = b"".join(p.read_bytes() for p in files)
    assert b"Voorbeeld" not in blob and b"Handelsdebiteuren" not in blob and FAKE_CACHE.encode() not in blob
    t2 = Tools(make_client(OCTOPUS_CACHE_KEY=FAKE_CACHE), today=lambda: date(2026, 11, 20))
    assert t2.call("octopus_sync_status", {"dossier_id": DOS})["status"]["bookings"]["records"] == 10


def test_te_korte_sleutel_geen_opslag(make_client, env):
    c = make_client(OCTOPUS_CACHE_KEY="kort")
    assert c.store.describe()["persistent"] is False


def test_tijdstempel_formaat():
    from octopus_mcp.tools import ts
    assert ts("2026-01-01") == "2026-01-01 00:00:00.000" and ts("2026-01-01T10:15") == "2026-01-01 10:15:00.000"
    with pytest.raises(ValueError):
        ts("1-1-2026")

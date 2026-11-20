"""Tools: register, annotaties, proefbalans (samengesteld), openstaande posten, ouderdom, kerncijfers."""
import pytest

from conftest import DOS


def test_registry_en_annotaties(tools):
    defs = tools.list()
    names = [d["name"] for d in defs]
    assert len(names) == len(set(names)) == 49 and all(n.startswith("octopus_") for n in names)
    for d in defs:
        assert d["inputSchema"]["type"] == "object" and d["description"] and d["title"]
        assert d["annotations"]["readOnlyHint"] is True and d["annotations"]["destructiveHint"] is False
    assert not [n for n in names if "schrijf" in n]


def test_onbekende_parameter_geweigerd(tools):
    with pytest.raises(ValueError):
        tools.call("octopus_proefbalans", {"dossier_id": DOS, "onbekend": 1})


def test_proefbalans_uit_rekeningen_en_saldi(tools, fake):
    r = tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026})
    rows = {x["rekening_code"]: x for x in r["rows"]}
    assert r["in_evenwicht"] and r["totals"]["debet"] == r["totals"]["credit"] == 6815.0
    assert rows["400000"]["saldo"] == 1000.0 and rows["700000"]["saldo"] == -1000.0 and rows["550000"]["debet"] == 5210.0
    assert rows["700000"]["rekening_naam"] == "Omzet" and rows["604000"]["soort"] == "kosten"
    assert r["per_klasse"]["1"] == -5000.0 and "verifieer actuele regel" in r["_verifieer"]
    assert fake.count("GET", "/accounts") == 1 and fake.count("GET", "/accounts/amounts/modified") == 1
    assert not any(p.endswith("trialbalance") for p in fake.ops())


def test_proefbalans_tot_periode_en_cumulatief(tools, make_client):
    r = tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026, "tot_periode": 3})
    rows = {x["rekening_code"]: x["saldo"] for x in r["rows"]}
    assert rows == {"100000": -5000.0, "400000": 1210.0, "451000": -210.0, "550000": 5000.0, "700000": -1000.0} and r["in_evenwicht"]
    r2 = tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026, "vanaf_periode": 4})
    assert {x["rekening_code"] for x in r2["rows"]} == {"400000", "411000", "440000", "550000", "604000"}


def test_proefbalans_tweede_keer_uit_cache(tools, fake):
    tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026})
    n = len(fake.requests)
    tools.call("octopus_proefbalans", {"dossier_id": DOS, "jaar": 2026})
    tools.call("octopus_dashboard_kpis", {"dossier_id": DOS, "jaar": 2026, "inclusief_open_posten": False})
    assert len(fake.requests) == n


def test_openstaande_posten_en_nulposten(tools):
    r = tools.call("octopus_openstaande_posten", {"dossier_id": DOS, "soort": "debiteuren"})
    assert r["aantal"] == 1 and r["rijen"][0]["open_bedrag"] == 1000.0 and r["rijen"][0]["status"] == "PARTIAL"
    assert r["query"]["fromBookyearKey"] == {"id": 1} and r["query"]["toBookyearPeriodNr"] == 12
    s = tools.call("octopus_openstaande_posten", {"dossier_id": DOS, "soort": "crediteuren"})
    assert s["rijen"][0]["open_bedrag"] == 605.0 and s["rijen"][0]["status"] == "OPEN"


def test_relatienaam_na_synchronisatie(tools):
    tools.call("octopus_sync", {"dossier_id": DOS, "jaar": 2026, "onderdelen": ["relaties"]})
    r = tools.call("octopus_openstaande_posten", {"dossier_id": DOS, "soort": "debiteuren", "vers": True})
    assert r["rijen"][0]["relatie"] == "[Voorbeeld] Klant"


def test_ouderdom(tools):
    r = tools.call("octopus_ouderdom_openstaande_posten", {"dossier_id": DOS, "soort": "debiteuren", "peildatum": "2026-05-20"})
    assert r["totaal_positief"] == 1000.0 and r["vervallen_totaal"] == 1000.0
    assert r["buckets"]["31-60"] == {"bedrag": 1000.0, "aantal": 1} and r["negatieve_posten"]["aantal"] == 0
    r = tools.call("octopus_ouderdom_openstaande_posten", {"dossier_id": DOS, "soort": "debiteuren", "peildatum": "2026-04-01"})
    assert r["vervallen_totaal"] == 0.0


def test_kerncijfers_mar(tools):
    r = tools.call("octopus_dashboard_kpis", {"dossier_id": DOS, "jaar": 2026})
    assert r["omzet"] == 1000.0 and r["kosten"] == 500.0 and r["resultaat"] == 500.0
    assert r["liquide_middelen"] == 5210.0 and r["handelsvorderingen"] == 1000.0 and r["handelsschulden"] == 605.0
    assert r["btw_indicatie"] == -105.0 and r["proefbalans_in_evenwicht"]
    assert r["open_debiteuren"]["totaal"] == 1000.0 and r["open_crediteuren"]["aantal"] == 1


def test_boekjaar_zoeken(tools):
    assert tools.resolve_by(DOS, {})["boekjaar_id"] == 2
    assert tools.resolve_by(DOS, {"jaar": 2025})["boekjaar_id"] == 1
    with pytest.raises(ValueError):
        tools.resolve_by(DOS, {"jaar": 1999})


def test_doorgeeftool_en_maximum_rijen(tools, fake):
    r = tools.call("octopus_btw_codes", {"dossier_id": DOS})
    assert r["rijen"][0]["code"] == "21"
    r = tools.call("octopus_boekingslijnen", {"dossier_id": DOS, "jaar": 2026, "max_rijen": 3})
    assert r["aantal"] == 10 and r["getoond"] == 3 and r["afgekapt"] is True


def test_foutcode_uitleg_en_btw(tools):
    r = tools.call("octopus_foutcode_uitleg", {"foutcode": 12})
    assert r["foutobject"]["foutcode"] == 12 and r["foutobject"]["variant"] == "spec"
    assert tools.call("octopus_btw_nummer_controle", {"btw_nummer": "BE0000000097"})["offline"]["controlegetal_ok"]
    assert not tools.call("octopus_btw_nummer_controle", {"btw_nummer": "BE0000000098"})["offline"]["controlegetal_ok"]


def test_status_en_quota_zonder_calls(tools, fake):
    s = tools.call("octopus_status", {})
    q = tools.call("octopus_quota", {})
    assert fake.requests == [] and s["alleen_lezen"] and s["attributie"] == "Powered by FISCALCI Accounting & Tax (Askin Alci)"
    assert "buiten België" in s["scope"] or "outside Belgium" in s["scope"]
    assert q["endpoints"]["GET /dossiers/{dossierId}/accounts"]["limit"] == 2


def test_dossierlijst_respecteert_allowlist(make_client):
    from datetime import date
    from octopus_mcp.tools import Tools
    t = Tools(make_client(OCTOPUS_ALLOWED_DOSSIERS="101"), today=lambda: date(2026, 11, 20))
    assert [r["dossier_id"] for r in t.call("octopus_dossiers", {})["rijen"]] == [101]


@pytest.mark.parametrize("per,omzet", [("3", 1000.0), ("2026-02", 0.0), ("maand:3", 1000.0), ("kwartaal:1", 1000.0), ("jaar", 1000.0)])
def test_kerncijfers_periodevormen(tools, per, omzet):
    r = tools.call("octopus_dashboard_kpis", {"dossier_id": DOS, "jaar": 2026, "periode": per, "inclusief_open_posten": False})
    assert r["omzet"] == omzet


def test_kerncijfers_ongeldige_periode(tools):
    with pytest.raises(ValueError):
        tools.call("octopus_dashboard_kpis", {"dossier_id": DOS, "periode": "Q1"})

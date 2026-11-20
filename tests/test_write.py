"""Schrijven: standaard uit; met OCTOPUS_WRITE_ENABLED=true in twee stappen, met dagmaximum."""
from datetime import date

import pytest

from conftest import DOS
from octopus_mcp.errors import OctopusRefused


@pytest.fixture
def wtools(make_client):
    from octopus_mcp.tools import Tools
    return Tools(make_client(OCTOPUS_WRITE_ENABLED="true", OCTOPUS_WRITE_MAX_PER_DAY="1"), today=lambda: date(2026, 11, 20))


def test_standaard_geen_schrijftools(tools):
    assert not [d for d in tools.list() if not d["annotations"]["readOnlyHint"]]


def test_voorstel_verstuurt_niets(wtools, fake):
    r = wtools.call("octopus_schrijf_voorstel", {"actie": "relatie_bijwerken", "dossier_id": DOS, "gegevens": {"name": "[Voorbeeld]"}})
    assert r["status"] == "voorstel" and r["endpoint"] == "PUT /dossiers/{dossierId}/relations"
    assert [x for x in fake.requests if x["method"] in ("PUT", "DELETE")] == []


def test_bevestigen_verstuurt_en_dagmaximum(wtools, fake):
    code = wtools.call("octopus_schrijf_voorstel", {"actie": "relatie_bijwerken", "dossier_id": DOS, "gegevens": {"name": "[Voorbeeld]"}})["bevestigingscode"]
    r = wtools.call("octopus_schrijf_bevestigen", {"bevestigingscode": code})
    assert r["status"] == "verstuurd" and fake.count("PUT", "/dossiers/101/relations") == 1
    with pytest.raises(OctopusRefused):
        wtools.call("octopus_schrijf_bevestigen", {"bevestigingscode": code})        # code eenmalig
    code2 = wtools.call("octopus_schrijf_voorstel", {"actie": "afpunting_toevoegen", "dossier_id": DOS, "gegevens": {}})["bevestigingscode"]
    with pytest.raises(OctopusRefused):
        wtools.call("octopus_schrijf_bevestigen", {"bevestigingscode": code2})       # dagmaximum 1


def test_geen_verwijderacties(wtools):
    from octopus_mcp.write import ALLOWED
    assert all(m in ("POST", "PUT") for m, _ in ALLOWED.values())
    with pytest.raises(ValueError):
        wtools.call("octopus_schrijf_voorstel", {"actie": "boekjaar_verwijderen", "dossier_id": DOS, "gegevens": {}})


def test_cli_voert_schrijftool_niet_uit(wtools, monkeypatch, capsys):
    from octopus_mcp import cli
    monkeypatch.setattr(cli, "_tools", lambda: wtools)
    assert cli.main(["call", "octopus_schrijf_voorstel", "actie=relatie_bijwerken", f"dossier_id={DOS}", "gegevens={}"]) == 6

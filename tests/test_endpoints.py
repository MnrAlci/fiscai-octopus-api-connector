"""Register en daglimieten tegen de officiële spec (spec/endpoints.json, gegenereerd uit openapi.json)."""
import json
from pathlib import Path

from octopus_mcp import endpoints as E

ROOT = Path(__file__).resolve().parent.parent


def test_spec_aantallen_en_bron():
    assert E.META["paths"] == 78 and E.META["server"] == "https://service.inaras.be/octopus-rest-api/v1"
    sj = json.loads((ROOT / "spec" / "endpoints.json").read_text(encoding="utf-8"))
    assert sj["meta"] == E.META and len(sj["operations"]) == E.META["operations"]


def test_daglimieten_uit_de_spec():
    assert E.get("accounts").limit() == 2
    assert E.get("vatcodes").limit() == 2 and E.get("currencies").limit() == 2 and E.get("costcentres").limit() == 2
    assert E.get("relations").limit() == 2 and E.get("relations").limit(search=True) == 400
    assert E.get("buysell").limit() == 10 and E.get("findiv").limit() == 10
    assert E.get("bookings_modified").limit() == 48 and E.get("open_clients").limit() == 24 and E.get("history_accounts").limit() == 24
    assert E.get("dossiers").limit() == 150 and E.get("dossier_token").limit() == 150
    assert E.get("authenticate").limit() is None


def test_quota_sleutels_bevatten_geen_dossierdata():
    for k in E.quota_limits():
        assert "{dossierId}" in k or k.startswith(("GET /", "POST /"))
        assert "101" not in k


def test_alle_geregistreerde_endpoints_zijn_lezen_of_auth():
    for k, ep in E.ENDPOINTS.items():
        assert ep.spec["kind"] in ("read", "auth"), k
        assert E.is_read_only(ep)


def test_cache_vervaltijd_volgt_limiet():
    assert E.get("accounts").cache_ttl() == 12 * 3600
    assert E.get("buysell").cache_ttl() == 6 * 3600
    assert E.get("open_clients").cache_ttl() == 3600
    assert E.get("bookings_modified").cache_ttl() == 1800
    assert E.get("relations").cache_ttl(search=True) == 300


def test_geen_management_of_file_import_api():
    for ep in E.ENDPOINTS.values():
        assert "management" not in ep.path and "file" not in ep.path
    src = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "server" / "octopus_mcp").glob("*.py") if p.name != "spec_endpoints.py")
    assert "octopus-management-api" not in src and "octopus-file-import-api" not in src

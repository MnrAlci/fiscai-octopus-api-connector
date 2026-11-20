"""Client: aanmelden, tokens (10 min), automatische vernieuwing, 401, daglimieten, cache, foutvarianten, veiligheid."""
import json

import httpx
import pytest

from conftest import DOS, FAKE_PASS, FAKE_SHU, FAKE_USER
from octopus_mcp.errors import OctopusApiError, OctopusAuthError, OctopusConfigError, OctopusRefused, QuotaExceeded, parse_error


def test_aanmelden_en_dossiertoken_headers(make_client, fake):
    c = make_client()
    c.call("bookyears", dossier_id=DOS)
    auth, tok, by = fake.requests
    assert auth["method"] == "POST" and auth["path"] == "/authentication"
    assert auth["headers"]["softwarehouseuuid"] == FAKE_SHU and auth["body"] == {"user": FAKE_USER, "password": FAKE_PASS}
    assert tok["method"] == "POST" and tok["path"] == "/dossiers" and tok["query"] == {"dossierId": "101", "localeId": "1"}
    assert tok["headers"]["token"].startswith("auth-")
    assert by["headers"]["dossiertoken"].startswith("dos-")


def test_tokens_worden_hergebruikt_binnen_10_minuten(make_client, fake, clock):
    c = make_client()
    c.call("bookyears", dossier_id=DOS)
    clock.advance(300)
    c.call("journals", dossier_id=DOS, path_params={"bookyearId": 2})
    assert fake.count("POST", "/authentication") == 1 and fake.count("POST", "/dossiers") == 1


def test_tokens_vernieuwen_voor_ze_verlopen(make_client, fake, clock):
    c = make_client()
    c.call("bookyears", dossier_id=DOS)
    clock.advance(541)                       # 10 min - 1 min marge = 540 s
    c.call("journals", dossier_id=DOS, path_params={"bookyearId": 2})
    assert fake.count("POST", "/authentication") == 2 and fake.count("POST", "/dossiers") == 2


def test_401_eenmaal_nieuw_token_en_opnieuw(make_client, fake):
    c = make_client()
    c.call("bookyears", dossier_id=DOS)
    fake.expire_all()                        # server trekt de tokens in (verlopen aan serverkant)
    res = c.call("journals", dossier_id=DOS, path_params={"bookyearId": 2})
    assert res and fake.count("POST", "/authentication") == 2 and fake.count("POST", "/dossiers") == 2


def test_tweede_401_geeft_autherror(make_client, fake):
    c = make_client()
    fake.fail[("GET", "/bookyears")] = [(401, {"errorCode": 1, "errorMessage": "x", "technicalInfo": ""})] * 2
    with pytest.raises(OctopusAuthError):
        c.call("bookyears", dossier_id=DOS)


def test_verkeerde_gegevens_handleidingvariant(make_client, fake, monkeypatch):
    c = make_client(OCTOPUS_PASSWORD="fout-wachtwoord-123")
    with pytest.raises(OctopusAuthError) as e:
        c.call("bookyears", dossier_id=DOS)
    assert e.value.variant == "manual" and "fout-wachtwoord-123" not in str(e.value)


def test_daglimiet_weigert_voor_de_call(make_client, fake):
    c = make_client()
    c.call("accounts", dossier_id=DOS, query={"bookyearId": 1}, use_cache=False)
    c.call("accounts", dossier_id=DOS, query={"bookyearId": 2}, use_cache=False)
    before = len(fake.requests)
    with pytest.raises(QuotaExceeded):
        c.call("accounts", dossier_id=DOS, query={"bookyearId": 1}, use_cache=False)
    assert len(fake.requests) == before      # niets verstuurd


def test_reserve_op_daglimiet(make_client, fake):
    c = make_client(OCTOPUS_QUOTA_RESERVE="1")
    c.call("accounts", dossier_id=DOS, query={"bookyearId": 1}, use_cache=False)
    with pytest.raises(QuotaExceeded):
        c.call("accounts", dossier_id=DOS, query={"bookyearId": 2}, use_cache=False)


def test_zoeken_in_relaties_heeft_eigen_limiet(make_client, fake):
    c = make_client()
    for _ in range(2):
        c.call("relations", dossier_id=DOS, use_cache=False)
    c.call("relations", dossier_id=DOS, query={"name": "klant"}, search=True, use_cache=False)
    snap = c.quota.snapshot()["endpoints"]
    assert snap["GET /dossiers/{dossierId}/relations"]["remaining"] == 0
    assert snap["GET /dossiers/{dossierId}/relations [search]"]["used"] == 1


def test_cache_spaart_calls_en_vers_slaat_over(make_client, fake):
    c = make_client()
    c.call("vatcodes", dossier_id=DOS)
    c.call("vatcodes", dossier_id=DOS)
    assert fake.count("GET", "/vatcodes") == 1 and c.cache.hits == 1
    c.call("vatcodes", dossier_id=DOS, fresh=True)
    assert fake.count("GET", "/vatcodes") == 2


def test_cache_vervalt(make_client, fake, clock):
    c = make_client()
    c.call("bookyears", dossier_id=DOS)
    clock.advance(3601)
    c.call("bookyears", dossier_id=DOS)
    assert fake.count("GET", "/bookyears") == 2


def test_teller_overleeft_herstart_en_bevat_geen_dossiers(make_client, fake, env):
    c = make_client()
    c.call("vatcodes", dossier_id=DOS)
    q = (env / "data" / "quota.json").read_text()
    assert "101" not in q and "auth-" not in q and FAKE_SHU not in q
    c2 = make_client()
    assert c2.quota.used("GET /dossiers/{dossierId}/vatcodes") == 1


def test_foutvariant_spec_en_handleiding_en_tekst():
    a = parse_error(400, "GET x", json.dumps({"errorCode": 7, "errorMessage": "Ongeldig", "technicalInfo": "t"}).encode())
    b = parse_error(500, "GET x", json.dumps({"octopusErrorCode": 8, "description": "Fout", "technicalDescription": "td"}).encode())
    c = parse_error(500, "GET x", b"Internal error")
    assert (a.variant, a.code, a.message, a.technical) == ("spec", 7, "Ongeldig", "t")
    assert (b.variant, b.code, b.message, b.technical) == ("manual", 8, "Fout", "td")
    assert c.variant == "none" and "Internal error" in c.message
    assert isinstance(parse_error(401, "x", b"{}"), OctopusAuthError)


def test_foutobject_bij_500_rapport(make_client, fake):
    c = make_client()
    fake.fail[("POST", "/reports/clients/open")] = [(500, {"octopusErrorCode": 12, "description": "Invalid Open Query Data", "technicalDescription": ""})]
    with pytest.raises(OctopusApiError) as e:
        c.call("open_clients", dossier_id=DOS, body={"fromBookyearKey": {"id": 2}})
    assert e.value.status == 500 and e.value.code == 12 and "ongeldige querygegevens" in str(e.value)


def test_geen_gegevens_geen_call(make_client, fake, monkeypatch):
    monkeypatch.delenv("OCTOPUS_PASSWORD")
    from octopus_mcp.client import OctopusClient
    from octopus_mcp.config import load
    c = OctopusClient(load(), httpx.MockTransport(fake.handler))
    with pytest.raises(OctopusConfigError):
        c.call("bookyears", dossier_id=DOS)
    assert fake.requests == []


@pytest.mark.parametrize("url", ["http://service.inaras.be/octopus-rest-api/v1", "https://example.org/octopus-rest-api/v1",
                                 "https://service.inaras.be/octopus-management-api/v1"])
def test_basis_url_beperkt(url, env, monkeypatch):
    from octopus_mcp.config import load
    monkeypatch.setenv("OCTOPUS_BASE_URL", url)
    with pytest.raises(OctopusConfigError):
        load()


def test_allowlist_dossiers(make_client, fake):
    c = make_client(OCTOPUS_ALLOWED_DOSSIERS="202")
    with pytest.raises(OctopusRefused):
        c.call("bookyears", dossier_id=DOS)
    assert fake.requests == []


def test_schrijfendpoints_geweigerd_in_client(make_client):
    c = make_client()
    with pytest.raises(OctopusRefused):
        c.call("authenticate")


def test_status_zonder_geheimen(make_client):
    c = make_client(OCTOPUS_CACHE_KEY="x" * 20)
    s = json.dumps(c.status())
    assert FAKE_PASS not in s and FAKE_SHU not in s and "x" * 20 not in s


def test_unresolved_placeholders_count_as_unset(monkeypatch):
    """MCP-clients die ${VAR} niet invullen: de letterlijke plaatshouder telt als niet ingesteld (schrijven blijft uit)."""
    from octopus_mcp import config
    env = {"OCTOPUS_WRITE_ENABLED": "${OCTOPUS_WRITE_ENABLED}", "OCTOPUS_AMOUNTS_MODE": "${OCTOPUS_AMOUNTS_MODE}",
           "OCTOPUS_LOCALE_ID": "${OCTOPUS_LOCALE_ID}", "OCTOPUS_USER": "${OCTOPUS_USER}", "OTHER": "${OTHER}"}
    s = config.load(env)
    assert s.write_enabled is False and s.amounts_mode == "movement" and s.locale_id == 1 and s.user == ""
    weg = config.drop_unresolved_placeholders(env)
    assert sorted(weg) == ["OCTOPUS_AMOUNTS_MODE", "OCTOPUS_LOCALE_ID", "OCTOPUS_USER", "OCTOPUS_WRITE_ENABLED"] and env == {"OTHER": "${OTHER}"}

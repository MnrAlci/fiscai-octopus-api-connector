"""MCP-server (stdio) en opdrachtregel."""
import io
import json

import pytest

from conftest import DOS

ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"


def rpc(srv, method, params=None, i=1):
    return srv.handle({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}})


def test_mcp_initialize_list_call(tools):
    from octopus_mcp.server import build
    srv = build(tools)
    init = rpc(srv, "initialize")["result"]
    assert init["serverInfo"]["name"] == "fiscai-octopus-api-connector" and ATTR in init["instructions"]
    assert len(rpc(srv, "tools/list")["result"]["tools"]) == 49
    res = rpc(srv, "tools/call", {"name": "octopus_proefbalans", "arguments": {"dossier_id": DOS, "jaar": 2026}})["result"]
    assert res["isError"] is False and res["structuredContent"]["in_evenwicht"] is True
    err = rpc(srv, "tools/call", {"name": "octopus_onbekend", "arguments": {}})["result"]
    assert err["isError"] is True
    assert rpc(srv, "bestaat/niet")["error"]["code"] == -32601


def test_mcp_fout_zonder_geheimen(tools, fake):
    from conftest import FAKE_PASS
    from octopus_mcp.server import build
    fake.fail[("GET", "/bookyears")] = [(500, {"errorCode": 5, "errorMessage": f"echo {FAKE_PASS}", "technicalInfo": ""})]
    res = rpc(build(tools), "tools/call", {"name": "octopus_boekjaren", "arguments": {"dossier_id": DOS}})["result"]
    assert res["isError"] and FAKE_PASS not in res["content"][0]["text"]


def test_stdio_loop(tools):
    from accounting_api_core.mcp import serve_stdio
    from octopus_mcp.server import build
    inp = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n" + json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    out = io.StringIO()
    serve_stdio(build(tools), inp, out)
    lines = [json.loads(x) for x in out.getvalue().splitlines() if x.strip()]
    assert lines == [{"jsonrpc": "2.0", "id": 1, "result": {}}]


def test_attributie_manipulatie_stopt_server(tools, monkeypatch):
    from accounting_api_core import attribution
    monkeypatch.setattr(attribution, "ATTRIBUTION", "Powered by iemand anders")
    from octopus_mcp.server import build
    with pytest.raises(Exception):
        build(tools)


@pytest.fixture
def cli(tools, monkeypatch):
    from octopus_mcp import cli as c
    monkeypatch.setattr(c, "_tools", lambda: tools)
    return c


def test_cli_tools_json(cli, capsys):
    assert cli.main(["tools", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 49


def test_cli_call_en_dry_run(cli, capsys, fake):
    assert cli.main(["call", "octopus_proefbalans", f"dossier_id={DOS}", "jaar=2026", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["in_evenwicht"] is True
    n = len(fake.requests)
    assert cli.main(["call", "octopus_proefbalans", f"dossier_id={DOS}", "--dry-run"]) == 0
    assert len(fake.requests) == n


def test_cli_validatie(cli, capsys):
    assert cli.main(["call", "octopus_proefbalans"]) == 2
    assert cli.main(["call", "octopus_bestaat_niet"]) == 2


def test_cli_doctor_quota_version_completion(cli, capsys):
    assert cli.main(["doctor"]) in (0, 3)
    out = capsys.readouterr().out
    assert "naamsvermelding" in out and "test-password" not in out
    assert cli.main(["quota", "--json"]) == 0
    assert "GET /dossiers/{dossierId}/accounts" in capsys.readouterr().out
    assert cli.main(["version"]) == 0 and "1.0.0" in capsys.readouterr().out
    assert cli.main(["completion", "bash"]) == 0 and "octopus-api-connector" in capsys.readouterr().out


def test_cli_config_init_plaatshouders(cli, tmp_path, capsys):
    p = tmp_path / ".env"
    assert cli.main(["config", "init", "--path", str(p)]) == 0
    t = p.read_text(encoding="utf-8")
    assert "OCTOPUS_SOFTWARE_HOUSE_UUID=" in t and "OCTOPUS_WRITE_ENABLED=false" in t
    assert cli.main(["config", "init", "--path", str(p)]) != 0          # niet overschrijven zonder --force


def test_cli_export_en_transfer(cli, tmp_path, capsys):
    assert cli.main(["export", "proefbalans", "--dossier", str(DOS), "--out", str(tmp_path / "e"), "--format", "csv"]) == 0
    assert (tmp_path / "e" / "octopus-proefbalans.csv").exists()
    assert cli.main(["transfer", "--dossier", str(DOS), "--bookyear", "2", "--out", str(tmp_path / "t")]) == 0   # alleen schatting
    assert not (tmp_path / "t" / "MANIFEST.json").exists()
    assert cli.main(["transfer", "--dossier", str(DOS), "--bookyear", "2", "--out", str(tmp_path / "t"), "--yes"]) == 0
    assert (tmp_path / "t" / "MANIFEST.json").exists()


def test_cli_sync_en_cache(cli, capsys):
    assert cli.main(["sync", "--dossier", str(DOS), "--bookyear", "2"]) == 0
    assert cli.main(["cache", "status"]) == 0
    assert cli.main(["cache", "clear"]) != 0                            # vraagt --yes
    assert cli.main(["cache", "clear", "--yes"]) == 0

"""Automatisering (kern-engine met het Octopus-profiel): alleen-lezen tools, concepten, geen verzending standaard."""
import json

from accounting_api_core.automation import engine


def test_toegelaten_tools_zijn_octopus_en_alleen_lezen(tools):
    allowed = set(engine.ALLOWED_TOOLS)
    assert allowed and all(n.startswith("octopus_") for n in allowed)
    defs = {d["name"]: d for d in tools.list()}
    assert all(defs[n]["annotations"]["readOnlyHint"] for n in allowed)
    cfg = engine.EXAMPLE_CONFIG
    assert "dossier_id = 1  # [Voorbeeld]" in cfg and "octopus-api-connector" in cfg and "OCTOPUS_WF_ICS_URL" in cfg and "YUKI" not in cfg


def test_init_plan_run(tools, tmp_path, monkeypatch, capsys):
    from octopus_mcp import cli
    monkeypatch.setattr(cli, "_tools", lambda: tools)
    wf = tmp_path / "workflows.toml"
    assert cli.main(["workflows", "init", "--path", str(wf)]) == 0
    assert cli.main(["workflows", "list", "-w", str(wf), "--json"]) == 0
    capsys.readouterr()
    assert cli.main(["workflows", "plan", "-w", str(wf), "--today", "2026-11-20", "--days", "60", "--only", "obligations", "--json"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan
    wf.write_text(wf.read_text(encoding="utf-8").replace("dossier_id = 1  #", "dossier_id = 101  #"), encoding="utf-8")
    out = tmp_path / "out"
    rc = cli.main(["workflows", "run", "-w", str(wf), "--today", "2026-11-20", "--days", "60", "--only", "obligations", "--out", str(out)])
    assert rc == 0
    files = list(out.rglob("*.md"))
    assert files and all("Powered by FISCALCI Accounting & Tax (Askin Alci)" in f.read_text(encoding="utf-8") for f in files)

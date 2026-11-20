"""Opdrachtregel 'octopus-api-connector': serve, doctor, tools, call, sync, quota, export, transfer, workflows, cache, config init, version, completion.

Alleen lezen. Voorrang: CLI-opties > omgeving > .env-bestand. Geheimen worden nooit afgedrukt.
Exitcodes: 0 ok, 1 algemene fout, 2 gebruik, 3 configuratie, 4 tool- of Octopus-fout, 5 netwerk, 6 geweigerd.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from accounting_api_core.cli_base import Out, apply_env_file, common_parser, completion_script, parse_kv
from accounting_api_core.exitcodes import EXIT_CONFIG, EXIT_ERR, EXIT_OK, EXIT_REFUSED, EXIT_TOOL, EXIT_USAGE
from accounting_api_core.logsetup import setup as setup_logging
from accounting_api_core.scrub import scrub

from . import __version__, _tools_factory, edition
from .config import ENV_TEMPLATE
from .errors import OctopusConfigError, OctopusRefused, QuotaExceeded

PROG = edition.PROG
COMMANDS = ["serve", "doctor", "tools", "call", "sync", "quota", "export", "transfer", "workflows", "cache", "config", "version", "completion"]
OPTS = "--json --quiet --verbose --log-level --log-format --env-file --hooks --dry-run --data-dir --help"


def build_parser() -> argparse.ArgumentParser:
    c = common_parser("Octopus")
    ap = argparse.ArgumentParser(prog=PROG, parents=[c], description=f"{edition.DISPLAY_NAME}: alleen-lezen Octopus-koppeling (MCP-server en opdrachtregel).",
                                 epilog="Voor Belgische boekhouders/accountants (MAR, Belgisch btw-stelsel). Buiten België: verifieer zelf de lokale regels. "
                                        "Powered by FISCALCI Accounting & Tax (Askin Alci)")
    sub = ap.add_subparsers(dest="cmd", metavar="opdracht")
    sub.add_parser("serve", parents=[c], help="start de MCP-server (stdio)")
    sub.add_parser("doctor", parents=[c], help="controleer Python, afhankelijkheden en configuratie (zonder geheimen, zonder calls)")
    sub.add_parser("tools", parents=[c], help="lijst van de tools")
    ca = sub.add_parser("call", parents=[c], help="roep één alleen-lezen tool aan")
    ca.add_argument("tool")
    ca.add_argument("args", nargs="*", help="naam=waarde (JSON-waarden toegestaan)")
    sy = sub.add_parser("sync", parents=[c], help="synchroniseer rekeningen, saldi, relaties en boekingen van een dossier")
    sy.add_argument("--dossier", type=int, required=True)
    sy.add_argument("--bookyear", type=int)
    sub.add_parser("quota", parents=[c], help="daglimieten per endpoint (geen calls)")
    ex = sub.add_parser("export", parents=[c], help="exporteer een dataset (csv, json, xlsx, parquet)")
    ex.add_argument("dataset", choices=["kpis", "saldi", "proefbalans", "openstaande_posten", "boekingslijnen", "rekeningschema", "relaties"])
    ex.add_argument("--dossier", type=int, required=True)
    ex.add_argument("--bookyear", type=int)
    ex.add_argument("--kind", choices=["debiteuren", "crediteuren"])
    ex.add_argument("--format", action="append", choices=["csv", "json", "xlsx", "parquet"])
    ex.add_argument("--out", required=True)
    tr = sub.add_parser("transfer", parents=[c], help="dossieroverdracht per boekjaar (met schatting, bevestiging, checkpoint, MANIFEST en CONTROL)")
    tr.add_argument("--dossier", type=int, required=True)
    tr.add_argument("--bookyear", type=int, action="append", help="boekjaar-id (herhaalbaar); leeg = alle")
    tr.add_argument("--out", required=True)
    tr.add_argument("--format", action="append", choices=["csv", "json", "xlsx"])
    tr.add_argument("--no-lines", action="store_true", help="zonder boekingslijnen")
    tr.add_argument("--zip", action="store_true")
    tr.add_argument("--yes", action="store_true", help="bevestig na het tonen van de schatting")
    wf = sub.add_parser("workflows", parents=[c], help="automatisering: vergaderingvoorbereiding en terugkerende verplichtingen (alleen lezen, concepten)")
    ws = wf.add_subparsers(dest="wf_cmd", metavar="actie")
    wc = argparse.ArgumentParser(add_help=False)
    wc.add_argument("-w", "--workflows-file", default="workflows.toml")
    wc.add_argument("--today")
    wc.add_argument("--days", type=int)
    wc.add_argument("--only", choices=["meetings", "obligations"])
    ws.add_parser("plan", parents=[c, wc], help="toon wat voorbereid moet worden (geen Octopus-calls)")
    ws.add_parser("list", parents=[c, wc], help="toon klanten en verplichtingen")
    wr = ws.add_parser("run", parents=[c, wc], help="maak overzichten en conceptmails (verstuurt niets standaard)")
    wr.add_argument("--out")
    wr.add_argument("--send", action="store_true")
    wr.add_argument("--confirm-send", action="store_true")
    wr.add_argument("--force", action="store_true")
    wi = ws.add_parser("init", parents=[c], help="schrijf een voorbeeld-workflows.toml")
    wi.add_argument("--path", default="workflows.toml")
    wi.add_argument("--force", action="store_true")
    cc = sub.add_parser("cache", parents=[c], help="lokale cache en synchronisatie")
    ccs = cc.add_subparsers(dest="cache_cmd", metavar="actie")
    ccs.add_parser("status", parents=[c])
    cl = ccs.add_parser("clear", parents=[c], help="wis de lokale cache en synchronisatie (niet de daglimiet-teller)")
    cl.add_argument("--yes", action="store_true")
    cf = sub.add_parser("config", parents=[c], help="configuratie")
    cfs = cf.add_subparsers(dest="config_cmd", metavar="actie")
    ci = cfs.add_parser("init", parents=[c], help="schrijf een voorbeeld-.env met plaatshouders")
    ci.add_argument("--path", default=".env")
    ci.add_argument("--force", action="store_true")
    sub.add_parser("version", parents=[c], help="toon de versie")
    co = sub.add_parser("completion", parents=[c], help="shell-aanvulling")
    co.add_argument("shell", choices=["bash", "zsh", "powershell"])
    return ap


def _bootstrap(a) -> None:
    if getattr(a, "data_dir", None):
        os.environ["OCTOPUS_DATA_DIR"] = a.data_dir
    if getattr(a, "hooks", None):
        os.environ["OCTOPUS_HOOKS_FILE"] = a.hooks
    if getattr(a, "env_file", None):
        apply_env_file(Path(a.env_file))
    setup_logging(getattr(a, "log_level", None), getattr(a, "log_format", None), getattr(a, "quiet", False), getattr(a, "verbose", False))


def _tools():
    from .tools import Tools
    return Tools()


def run_tool(a, out: Out, name: str, args: dict, tools=None) -> int:
    from accounting_api_core.cli_base import validate_args
    from accounting_api_core.hooks import Hooks, guarded_call
    tools = tools or _tools()
    d = tools.defs.get(name)
    if d is None:
        sys.stderr.write(f"Onbekende tool: {name}. Zie '{PROG} tools'.\n")
        return EXIT_USAGE
    if not d["annotations"].get("readOnlyHint") or name.startswith("octopus_schrijf_"):
        sys.stderr.write(f"{name} is niet alleen-lezen en wordt via de opdrachtregel niet uitgevoerd.\n")
        return EXIT_REFUSED
    problems = validate_args(d["inputSchema"], args)
    if problems:
        sys.stderr.write("; ".join(problems) + "\n")
        return EXIT_USAGE
    if getattr(a, "dry_run", False):
        out.emit({"dry_run": True, "tool": name, "args": args, "network": False}, f"[dry-run] zou {name} aanroepen met {json.dumps(args, ensure_ascii=False)}; geen Octopus-calls.")
        return EXIT_OK
    try:
        res = guarded_call(Hooks.from_env(), tools.call, name, args)
    except OctopusConfigError as exc:
        sys.stderr.write(scrub(str(exc)) + "\n")
        return EXIT_CONFIG
    except (OctopusRefused, QuotaExceeded) as exc:
        sys.stderr.write(scrub(str(exc)) + "\n")
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(scrub(f"{type(exc).__name__}: {exc}") + "\n")
        return EXIT_TOOL
    out.emit(res)
    return EXIT_OK


def cmd_doctor(a, out: Out) -> int:
    rows, rc = [], EXIT_OK

    def add(name, ok, detail, level="error"):
        nonlocal rc
        rows.append({"check": name, "ok": ok, "detail": detail})
        if not ok and level == "error":
            rc = EXIT_CONFIG
    add("python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0])
    for mod in ("httpx", "cryptography"):
        try:
            __import__(mod)
            add(mod, True, "geïnstalleerd")
        except ImportError:
            add(mod, False, "ontbreekt: pip install " + mod, "error" if mod == "httpx" else "warning")
    try:
        from .config import load
        s = load()
        add("configuratie", True, "geladen")
        add("Octopus-gegevens", s.has_credentials, "ingesteld" if s.has_credentials else "OCTOPUS_SOFTWARE_HOUSE_UUID, OCTOPUS_USER, OCTOPUS_PASSWORD ontbreken", "warning")
        add("versleutelde cache (OCTOPUS_CACHE_KEY)", len(s.cache_key) >= 16, "aan" if len(s.cache_key) >= 16 else "uit: cache en synchronisatie alleen in het geheugen", "warning")
        add("schrijven", not s.write_enabled, "uit (alleen lezen)" if not s.write_enabled else "AAN: OCTOPUS_WRITE_ENABLED=true", "warning")
    except OctopusConfigError as exc:
        add("configuratie", False, str(exc))
    from accounting_api_core.attribution import constant_intact
    add("naamsvermelding", constant_intact(), "intact")
    out.emit({"checks": rows, "network": False}, "\n".join(f"[{'OK' if r['ok'] else '!!'}] {r['check']}: {r['detail']}" for r in rows))
    return rc


def cmd_transfer(a, out: Out) -> int:
    args = {"dossier_id": a.dossier, "export_map": a.out, "inclusief_boekingslijnen": not a.no_lines, "zip": a.zip}
    if a.bookyear:
        args["boekjaren"] = a.bookyear
    if a.format:
        args["formaten"] = a.format
    tools = _tools()
    est = tools.call("octopus_dossier_transfer_schatting", {k: args[k] for k in ("dossier_id", "boekjaren") if k in args})
    if not a.yes:
        out.emit({"schatting": est, "bevestigd": False}, json.dumps(est, ensure_ascii=False, indent=2) + "\nVoer opnieuw uit met --yes om te exporteren.")
        return EXIT_OK
    res = tools.call("octopus_dossier_transfer_export", {**args, "bevestig": True})
    out.emit(res)
    return EXIT_OK if res.get("status") == "klaar" else EXIT_TOOL


def main(argv: Optional[list[str]] = None) -> int:
    from .config import drop_unresolved_placeholders
    drop_unresolved_placeholders()
    ap = build_parser()
    a = ap.parse_args(argv)
    out = Out(getattr(a, "json", False), getattr(a, "quiet", False))
    try:
        _bootstrap(a)
    except (OctopusConfigError, FileNotFoundError, ValueError) as exc:
        sys.stderr.write(f"Configuratiefout: {exc}\n")
        return EXIT_CONFIG
    cmd = a.cmd
    try:
        if cmd in (None, "serve"):
            from .server import main as serve
            return serve()
        if cmd == "version":
            out.emit({"version": __version__, "name": edition.DISPLAY_NAME}, f"{edition.DISPLAY_NAME} {__version__}")
            return EXIT_OK
        if cmd == "completion":
            sys.stdout.write(completion_script(a.shell, PROG, COMMANDS, OPTS))
            return EXIT_OK
        if cmd == "doctor":
            return cmd_doctor(a, out)
        if cmd == "tools":
            t = _tools()
            out.emit([{"name": d["name"], "title": d["title"], "read_only": d["annotations"]["readOnlyHint"]} for d in t.list()],
                     "\n".join(f"{d['name']:42} {d['title']}" for d in t.list()))
            return EXIT_OK
        if cmd == "call":
            return run_tool(a, out, a.tool, parse_kv(a.args))
        if cmd == "quota":
            return run_tool(a, out, "octopus_quota", {})
        if cmd == "sync":
            return run_tool(a, out, "octopus_sync", {"dossier_id": a.dossier, **({"boekjaar_id": a.bookyear} if a.bookyear else {})})
        if cmd == "export":
            args = {"dataset": a.dataset, "dossier_id": a.dossier, "export_map": a.out, "formaten": a.format or ["csv"]}
            if a.bookyear:
                args["boekjaar_id"] = a.bookyear
            if a.kind:
                args["soort"] = a.kind
            return run_tool(a, out, "octopus_export_dataset", args)
        if cmd == "transfer":
            return cmd_transfer(a, out)
        if cmd == "workflows":
            from accounting_api_core.automation.engine import cmd_workflows
            return cmd_workflows(a, out, tools_factory=lambda: _tools_factory(_tools()))
        if cmd == "cache":
            t = _tools()
            if a.cache_cmd == "clear":
                if not a.yes:
                    sys.stderr.write("Gebruik --yes om de lokale cache en synchronisatie te wissen.\n")
                    return EXIT_USAGE
                out.emit({"gewist": t.client.store.clear()})
                return EXIT_OK
            out.emit(t.client.store.describe())
            return EXIT_OK
        if cmd == "config":
            if a.config_cmd != "init":
                ap.print_help()
                return EXIT_USAGE
            p = Path(a.path)
            if p.exists() and not a.force:
                sys.stderr.write(f"{p} bestaat al; gebruik --force.\n")
                return EXIT_CONFIG
            p.write_text(ENV_TEMPLATE, encoding="utf-8")
            out.emit({"written": str(p)}, f"Voorbeeld-.env geschreven naar {p} (alleen plaatshouders).")
            return EXIT_OK
    except OctopusConfigError as exc:
        sys.stderr.write(scrub(str(exc)) + "\n")
        return EXIT_CONFIG
    except (OctopusRefused, QuotaExceeded) as exc:
        sys.stderr.write(scrub(str(exc)) + "\n")
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(scrub(f"{type(exc).__name__}: {exc}") + "\n")
        return EXIT_ERR
    ap.print_help()
    return EXIT_USAGE

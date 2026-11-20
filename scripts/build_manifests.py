"""Genereert mcp.json, plugin.json, .cursor-plugin/plugin.json, .claude-plugin/plugin.json en server.json uit één lijst.

Gebruik: python scripts/build_manifests.py   (tests/test_repo_hygiene.py controleert dat de bestanden overeenkomen)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG, NAME = "fiscai-octopus-api-connector", "FISCAi Octopus API Connector"
VERSION = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
DESC = ("Plugin for Grok Bot (also works with Copilot, Claude, Cursor, Windsurf and other MCP clients): read-only access to the Octopus accounting "
        "REST API for Belgian accountants, with daily-limit protection, local sync, trial balance, export and dossier transfer per fiscal year. "
        "Powered by FISCALCI Accounting & Tax (Askin Alci)")
REPO = f"https://github.com/MnrAlci/{SLUG}"
KEYWORDS = ["octopus", "boekhouding", "accounting", "belgie", "mcp", "proefbalans", "debiteuren", "crediteuren", "dossieroverdracht"]

# (naam, titel, beschrijving, geheim, verplicht, standaard)
VARS = [
    ("OCTOPUS_SOFTWARE_HOUSE_UUID", "Software house UUID", "UUID die Octopus aan uw software toekent (header softwareHouseUuid). Geheim.", True, True, None),
    ("OCTOPUS_USER", "Octopus-gebruiker", "Gebruikersnaam (e-mail) van de Octopus-gebruiker met API-toegang. Geheim.", True, True, None),
    ("OCTOPUS_PASSWORD", "Octopus-wachtwoord", "Wachtwoord van die gebruiker. Alleen in het geheugen; nooit gelogd. Geheim.", True, True, None),
    ("OCTOPUS_CACHE_KEY", "Cachesleutel", "Optioneel, minstens 16 tekens: versleutelt de lokale cache en synchronisatie op schijf. Zonder sleutel alleen in het geheugen. Geheim.",
     True, False, None),
    ("OCTOPUS_LOCALE_ID", "Taal-id", "localeId voor het dossiertoken (0-4, standaard 1; verifieer actuele regel).", False, False, "1"),
    ("OCTOPUS_ALLOWED_DOSSIERS", "Toegelaten dossiers", "Optioneel: komma-gescheiden dossier-id's; andere dossiers worden geweigerd.", False, False, None),
    ("OCTOPUS_QUOTA_RESERVE", "Reserve op daglimiet", "Aantal calls per endpoint dat de connector vrijhoudt (standaard 0).", False, False, "0"),
    ("OCTOPUS_AMOUNTS_MODE", "Modus saldi", "movement (beweging per periode, standaard) of cumulative. Verifieer actuele regel met de controle in de dossieroverdracht.",
     False, False, "movement"),
    ("OCTOPUS_WRITE_ENABLED", "Schrijven toestaan", "Standaard uit. Alleen true zet de tweestaps-schrijftools aan.", False, False, "false"),
    ("OCTOPUS_WRITE_MAX_PER_DAY", "Maximum schrijfacties per dag", "1 tot 200, standaard 20.", False, False, "20"),
]


def env_map(fmt) -> dict:
    return {n: fmt(n) for n, *_ in VARS}


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    dump(ROOT / "mcp.json", {"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json", "mcpServers": {SLUG: {
        "type": "stdio", "command": "python3", "args": ["./server/run_server.py"], "env": env_map(lambda n: "${" + n + "}")}}})
    base = {"name": SLUG, "version": VERSION, "description": DESC, "author": {"name": "Askin Alci"}, "license": "Apache-2.0",
            "homepage": f"{REPO}#readme", "repository": REPO, "keywords": KEYWORDS}
    dump(ROOT / "plugin.json", {**base, "logo": "assets/logo.png", "skills": "./skills/", "mcpServers": "./mcp.json"})
    dump(ROOT / ".cursor-plugin" / "plugin.json", {
        **{k: v for k, v in base.items() if k != "version"}, "displayName": NAME, "version": VERSION, "logo": "assets/logo.png", "skills": "./skills/",
        "rules": ["./agents/cursor/octopus-core.mdc", "./agents/cursor/octopus-accountant.mdc"],
        "agents": ["./agents/claude/octopus-accountant.md"],
        "mcpServers": {SLUG: {"type": "stdio", "command": "python3", "args": ["${CURSOR_PLUGIN_ROOT}/server/run_server.py"], "cwd": "${CURSOR_PLUGIN_ROOT}",
                              "env": env_map(lambda n: "${" + n + "}")}},
        "variables": {"type": "object", "properties": {n: {"type": "string", "title": t, "description": d} for n, t, d, *_ in VARS},
                      "required": [n for n, _, _, _, req, _ in VARS if req]}})
    dump(ROOT / ".claude-plugin" / "plugin.json", {
        **base, "skills": ["./skills/"], "agents": ["./agents/claude/octopus-accountant.md"],
        "mcpServers": {SLUG: {"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/server/run_server.py"],
                              "env": {n: "${user_config." + n.lower() + "}" for n, _, _, _, req, _ in VARS if req or n == "OCTOPUS_CACHE_KEY"}}},
        "userConfig": {n.lower(): {"type": "string", "title": t, "description": d, "sensitive": sec, "required": req}
                       for n, t, d, sec, req, _ in VARS if req or n == "OCTOPUS_CACHE_KEY"}})
    dump(ROOT / "server.json", {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json", "name": f"io.github.MnrAlci/{SLUG}", "title": NAME,
        "description": "Read-only Octopus REST API for Belgian accountants. Powered by FISCALCI Accounting & Tax (Askin Alci)",
        "repository": {"url": REPO, "source": "github"}, "websiteUrl": REPO, "version": VERSION,
        "packages": [{"registryType": "pypi", "registryBaseUrl": "https://pypi.org", "identifier": SLUG, "version": VERSION, "runtimeHint": "uvx",
                      "transport": {"type": "stdio"},
                      "environmentVariables": [{"name": n, "description": d, "isRequired": req, "format": "string", "isSecret": sec, **({"default": df} if df else {})}
                                               for n, _, d, sec, req, df in VARS]}]})
    print("manifesten geschreven", VERSION)


if __name__ == "__main__":
    main()

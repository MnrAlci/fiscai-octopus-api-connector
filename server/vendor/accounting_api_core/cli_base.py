"""Gedeelde bouwstenen voor connector-CLI's: uitvoer (tekst/JSON), gemeenschappelijke opties, .env-laden, validatie, shell-aanvulling.

Voorrang: CLI-opties > omgeving > bestanden (.env). Geheimen worden nooit afgedrukt.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from .exitcodes import EXIT_OK, EXIT_REFUSED, EXIT_TOOL, EXIT_USAGE  # noqa: F401 - hergebruik door connectors


class Out:
    def __init__(self, as_json: bool, quiet: bool) -> None:
        self.as_json, self.quiet = as_json, quiet

    def emit(self, data: Any, text: Optional[str] = None) -> None:
        if self.as_json:
            sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n")
        elif not self.quiet:
            sys.stdout.write((text if text is not None else json.dumps(data, ensure_ascii=False, indent=2, default=str)) + "\n")

    def info(self, text: str) -> None:
        if not self.quiet and not self.as_json:
            sys.stdout.write(text + "\n")


def common_parser(source_name: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    S = argparse.SUPPRESS
    p.add_argument("--json", action="store_true", default=S, help="machine-leesbare JSON-uitvoer")
    p.add_argument("-q", "--quiet", action="store_true", default=S, help="alleen fouten")
    p.add_argument("-v", "--verbose", action="store_true", default=S, help="meer details (debug-logging)")
    p.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], default=S)
    p.add_argument("--log-format", choices=["text", "json"], default=S, help="structurele JSON-logregels op stderr")
    p.add_argument("--env-file", default=S, help=".env-bestand (omgeving wint)")
    p.add_argument("--hooks", default=S, help="hooks-bestand (standaard uit, zie docs/HOOKS.md)")
    p.add_argument("--dry-run", action="store_true", default=S, help=f"toon wat er zou gebeuren; geen calls naar {source_name}")
    p.add_argument("--data-dir", default=S, help="map voor cache, teller en synchronisatie")
    return p


ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


def apply_env_file(path: Path, environ=None) -> list[str]:
    """Laad KEY=waarde-regels zonder bestaande omgevingsvariabelen te overschrijven. Geeft de NAMEN terug (nooit waarden)."""
    environ = os.environ if environ is None else environ
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f".env-bestand niet gevonden: {p}")
    names = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = ENV_LINE.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if v and k not in environ:
            environ[k] = v
            names.append(k)
    return names


def validate_args(schema: dict, args: dict) -> list[str]:
    miss = [r for r in schema.get("required", []) if r not in args]
    unknown = [k for k in args if schema.get("properties") is not None and k not in schema["properties"]]
    bad = []
    for k, v in args.items():
        spec = (schema.get("properties") or {}).get(k) or {}
        if "enum" in spec and v not in spec["enum"]:
            bad.append(f"{k} moet een van {', '.join(map(str, spec['enum']))} zijn")
    return [f"ontbrekende parameter: {m}" for m in miss] + [f"onbekende parameter: {u}" for u in unknown] + bad


def completion_script(shell: str, prog: str, commands: list[str], opts: str) -> str:
    words = " ".join(commands)
    fn = "_" + re.sub(r"[^a-z0-9]", "_", prog)
    if shell == "bash":
        return (f'{fn}() {{\n  local cur="${{COMP_WORDS[COMP_CWORD]}}"\n  if [ "$COMP_CWORD" -eq 1 ]; then COMPREPLY=( $(compgen -W "{words}" -- "$cur") )\n'
                f'  else COMPREPLY=( $(compgen -W "{opts}" -- "$cur") ); fi\n}}\ncomplete -F {fn} {prog}\n')
    if shell == "zsh":
        return f"#compdef {prog}\n_arguments '1:command:({words})' '*:option:({opts})'\n"
    return (f"Register-ArgumentCompleter -Native -CommandName {prog} -ScriptBlock {{\n  param($wordToComplete)\n  '{words}'.Split(' ') + '{opts}'.Split(' ') |\n"
            "    Where-Object { $_ -like \"$wordToComplete*\" } | ForEach-Object { [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) }\n}\n")


def parse_kv(pairs: list[str]) -> dict:
    """'naam=waarde'-paren naar een dict; JSON-waarden (getallen, true/false, lijsten) worden herkend."""
    out: dict = {}
    for p in pairs or []:
        if "=" not in p:
            raise ValueError(f"Verwacht naam=waarde, kreeg '{p}'.")
        k, v = p.split("=", 1)
        try:
            out[k] = json.loads(v)
        except ValueError:
            out[k] = v
    return out

"""Bouwt dist/fiscai-octopus-api-connector-<versie>.mcpb (reproduceerbaar) en print de SHA-256.

Gebruik: python scripts/build_mcpb.py   (de SHA-256 komt daarna in server.json; zie docs/maintainers/RELEASE.md)
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
SLUG = "fiscai-octopus-api-connector"
REPO = f"https://github.com/MnrAlci/{SLUG}"
ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"
FIXED_DATE = (2026, 11, 20, 0, 0, 0)

# (env-naam, titel, beschrijving, geheim, verplicht, standaard)
USER_CONFIG = [
    ("OCTOPUS_SOFTWARE_HOUSE_UUID", "Software house UUID", "UUID that Octopus assigns to your software (header softwareHouseUuid).", True, True, None),
    ("OCTOPUS_USER", "Octopus user", "User name (e-mail) of the Octopus user with API access.", True, True, None),
    ("OCTOPUS_PASSWORD", "Octopus password", "Password of that user. Kept in memory only, never logged.", True, True, None),
    ("OCTOPUS_CACHE_KEY", "Cache key", "Optional, at least 16 characters: encrypts the local cache on disk. Without it, memory only.", True, False, None),
]


def manifest() -> dict:
    return {
        "manifest_version": "0.4", "name": SLUG, "display_name": "FISCAi Octopus API Connector", "version": VERSION,
        "description": f"Read-only Octopus accounting REST API for Belgian accountants. {ATTR}",
        "long_description": ("Local MCP server (stdio) for Octopus: fiscal years, journals, bookings, relations, trial balance, open items, export and dossier transfer, "
                             "with protection for the daily call limits. Read-only by default; the two write tools need OCTOPUS_WRITE_ENABLED=true and a confirmation code. "
                             "Made for Belgium (MAR, Belgian VAT); outside Belgium, check the local rules yourself. Not endorsed by Octopus or Visma. " + ATTR),
        "author": {"name": "Askin Alci", "url": "https://github.com/MnrAlci"},
        "repository": {"type": "git", "url": REPO}, "homepage": REPO, "documentation": f"{REPO}/tree/main/docs", "support": f"{REPO}/issues",
        "icon": "assets/logo.png", "license": "Apache-2.0",
        "keywords": ["octopus", "accounting", "belgium", "vat", "mar", "mcp", "read-only"],
        "privacy_policies": [f"{REPO}/blob/main/docs/PRIVACY-DATA-FLOW.md"],
        "server": {"type": "uv", "entry_point": "server/run_server.py", "mcp_config": {
            "command": "uv", "args": ["run", "--directory", "${__dirname}", "server/run_server.py"],
            "env": {n: "${user_config." + n.lower() + "}" for n, *_ in USER_CONFIG}}},
        "tools_generated": False,
        "user_config": {n.lower(): {"type": "string", "title": t, "description": d, "sensitive": sec, "required": req}
                        for n, t, d, sec, req, _ in USER_CONFIG},
        "compatibility": {"platforms": ["darwin", "win32", "linux"], "runtimes": {"python": ">=3.10"}},
    }


def main() -> None:
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    target = out / f"{SLUG}-{VERSION}.mcpb"
    files = ["LICENSE", "NOTICE", "README.md", "pyproject.toml", "requirements.txt", "assets/logo.png"]
    files += sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "server").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            zi = zipfile.ZipInfo(name, FIXED_DATE)
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(zi, (ROOT / name).read_bytes())
        zi = zipfile.ZipInfo("manifest.json", FIXED_DATE)
        zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
        z.writestr(zi, json.dumps(manifest(), indent=2, ensure_ascii=False) + "\n")
    print(target.name, hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()

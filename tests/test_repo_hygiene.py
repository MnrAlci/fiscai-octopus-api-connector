"""Repository-hygiëne: naamgeving, versies, naamsvermelding, geen klantgegevens of geheimen, gegenereerde bestanden actueel."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:          # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"
TEXT_EXT = {".py", ".md", ".mdc", ".txt", ".json", ".toml", ".yml", ".yaml", ".cfg", ".ini", ".ps1", ".sh", ".example", ".ics", ".svg", ""}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "node_modules"}


def text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS) and (p.suffix in TEXT_EXT or p.name in ("Dockerfile", "Makefile", "LICENSE", "NOTICE")):
            yield p


def test_no_forbidden_identifiers():
    forbidden = [r"FISCALCI\s*BV", r"BE\s?0?804[.\s]?135[.\s]?542", r"0804\.135\.542", r"\[REDACTED\]"]
    hits = []
    for p in text_files():
        if p.name == "test_repo_hygiene.py":
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        hits += [f"{p.relative_to(ROOT)}: {pat}" for pat in forbidden if re.search(pat, s, re.I)]
    assert not hits, hits


def test_no_yuki_leftovers():
    """Verwijzingen naar de zuster-connector mogen ("zoals de Yuki-connector"); overgebleven Yuki-namen, variabelen of tools niet."""
    leftover = re.compile(r"YUKI_|\byuki_[a-z]|yuki-api-connector|fiscai-yuki|yuki-audit|yuki-export|\.config/yuki|administratie\s*=\s*\"\[Voorbeeld\]")
    hits = []
    for p in text_files():
        rel = p.relative_to(ROOT)
        if rel.parts[:2] == ("server", "vendor") or p.name == "test_repo_hygiene.py" or rel.parts[0] == "tests":
            continue
        for m in leftover.finditer(p.read_text(encoding="utf-8", errors="ignore")):
            hits.append(f"{rel}: {m.group(0)}")
    assert not hits, hits


def test_no_secret_like_values():
    pats = [r"OCTOPUS_PASSWORD\s*[=:]\s*['\"]?[^\s'\"$<{]{6,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"\bghp_[A-Za-z0-9]{20,}", r"\bsk-[A-Za-z0-9]{20,}"]
    hits = []
    for p in text_files():
        if p.relative_to(ROOT).parts[0] == "tests":     # testwaarden zijn synthetisch
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        for pat in pats:
            for m in re.finditer(pat, s):
                if "YOUR_" not in m.group(0) and "voorbeeld" not in m.group(0).lower():
                    hits.append(f"{p.relative_to(ROOT)}: {m.group(0)[:30]}")
    assert not hits, hits


def test_attribution_and_belgian_notice():
    for rel in ("README.md", "README.nl.md", "NOTICE", "AGENTS.md", "skills/fiscai-octopus-api-connector/SKILL.md", "docs/manuals/manual.en.md",
                "docs/manuals/handleiding.nl.md", "agents/core/instructions.md"):
        s = (ROOT / rel).read_text(encoding="utf-8")
        assert ATTR in s, rel
    assert "outside belgium" in (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "buiten belgië" in (ROOT / "README.nl.md").read_text(encoding="utf-8").lower()
    r = subprocess.run([sys.executable, str(ROOT / "server" / "run_cli.py"), "--help"], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert ATTR in " ".join(r.stdout.split())


def test_no_publisher_names_in_docs():
    pats = [r"\bInaras\b(?! *\.be)", r"Wolters", r"Kluwer"]
    hits = []
    for p in text_files():
        if p.suffix != ".md" or "vendor" in p.parts:
            continue
        s = p.read_text(encoding="utf-8")
        hits += [f"{p.relative_to(ROOT)}: {pat}" for pat in pats if re.search(pat, s)]
    assert not hits, hits


def test_versions_consistent():
    v = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    from octopus_mcp import __version__
    assert __version__ == v
    for rel in ("plugin.json", ".cursor-plugin/plugin.json", ".claude-plugin/plugin.json"):
        assert json.loads((ROOT / rel).read_text(encoding="utf-8"))["version"] == v, rel
    sj = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    assert sj["version"] == v
    assert f"## [{v}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_naming():
    pj = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert pj["name"] == "fiscai-octopus-api-connector"
    assert "FISCAi Octopus API Connector" in (ROOT / "README.md").read_text(encoding="utf-8")
    proj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert "octopus-api-connector" in proj["scripts"]
    assert proj["license"] in ("Apache-2.0", {"text": "Apache-2.0"}) or "Apache" in str(proj["license"])
    assert any("Askin Alci" in a.get("name", "") for a in proj["authors"])
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", [
    "LICENSE", "NOTICE", "README.md", "README.nl.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "AGENTS.md", "ROADMAP.md",
    "Dockerfile", ".github/workflows/ci.yml", ".github/dependabot.yml", ".github/CODEOWNERS", ".github/labels.yml", ".github/rulesets/main-protection.json",
    ".github/rulesets/release-tags.json", ".github/PULL_REQUEST_TEMPLATE.md", ".github/ISSUE_TEMPLATE/bug_report.md",
    "docs/OPEN-QUESTIONS.md", "docs/SETUP.md", "docs/TOOLS.md", "docs/TOOLS.nl.md", "docs/CLI.md", "docs/CLI.nl.md", "docs/DOSSIER-TRANSFER.md",
    "docs/EXPORT-SCHEMA.md", "docs/WRITE.md", "docs/OPERATIONS.md", "docs/maintainers/REPO-SETTINGS.md", "docs/manuals/manual.en.md", "docs/manuals/handleiding.nl.md",
    "skills/fiscai-octopus-api-connector/SKILL.md", "agents/README.md", "agents/cursor/octopus-core.mdc", "agents/cursor/octopus-accountant.mdc",
    "agents/claude/octopus-accountant.md", "assets/logo.png", "assets/logo-128.png", "examples/workflows/workflows.example.toml",
    "postman/FISCAi-Octopus-API-Connector.postman_collection.json", "postman/FISCAi-Octopus-API-Connector.postman_environment.json", "spec/endpoints.json"])
def test_project_file_present(rel):
    assert (ROOT / rel).is_file(), rel


def test_manifest_references_exist():
    for rel in (".cursor-plugin/plugin.json", ".claude-plugin/plugin.json", "plugin.json"):
        d = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for key in ("rules", "agents", "skills"):
            for ref in d.get(key, []) if isinstance(d.get(key), list) else []:
                assert (ROOT / ref).exists(), f"{rel}: {ref}"


def test_ci_and_rulesets_safe():
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "permissions:" in ci and "contents: read" in ci
    assert "secrets." not in ci and "pull_request_target" not in ci
    rs = json.loads((ROOT / ".github/rulesets/main-protection.json").read_text(encoding="utf-8"))
    types = {r["type"] for r in rs["rules"]}
    assert {"deletion", "non_fast_forward", "pull_request"} <= types
    assert not rs.get("bypass_actors")


def test_dockerfile_without_secrets():
    s = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*(ENV|ARG)\s+OCTOPUS_(PASSWORD|USER|SOFTWARE_HOUSE_UUID|CACHE_KEY)", s)
    assert "USER" in s


def test_postman_read_only_and_without_secrets():
    c = json.loads((ROOT / "postman/FISCAi-Octopus-API-Connector.postman_collection.json").read_text(encoding="utf-8"))
    methods = []

    def walk(items):
        for it in items:
            if "item" in it:
                walk(it["item"])
            else:
                methods.append((it["name"], it["request"]["method"], it["request"]["url"]["raw"] if isinstance(it["request"]["url"], dict) else it["request"]["url"]))
    walk(c["item"])
    from octopus_mcp.endpoints import BY_ID
    reads = {k for k, o in BY_ID.items() if o["kind"] == "read"}
    ops = [m[0] for m in methods if m[0].split(" ")[0] in ("GET", "POST", "PUT", "DELETE", "PATCH")]
    assert ops and set(ops) <= reads, sorted(set(ops) - reads)
    assert len(set(ops)) == len(reads) == 50
    extra = [m for m in methods if m[0] not in ops]
    assert all(re.search(r"/authentication|/dossiers\?", m[2]) for m in extra), extra
    e = json.loads((ROOT / "postman/FISCAi-Octopus-API-Connector.postman_environment.json").read_text(encoding="utf-8"))
    for v in e["values"]:
        if v["key"] in ("softwareHouseUuid", "user", "password"):
            assert v["value"] == "", v["key"]
    assert not re.search(r"management", " ".join(m[2] for m in methods), re.I)


def test_endpoint_registry_matches_spec_summary():
    eps = json.loads((ROOT / "spec/endpoints.json").read_text(encoding="utf-8"))
    from octopus_mcp.endpoints import ENDPOINTS, OPERATIONS
    assert eps["operations"] == OPERATIONS and len(OPERATIONS) == eps["meta"]["operations"] == 103
    kinds = [o["kind"] for o in OPERATIONS]
    assert kinds.count("read") == 50 and kinds.count("write") == 50 and kinds.count("auth") == 3
    by = {f"{o['method']} {o['path']}" for o in OPERATIONS}
    for ep in ENDPOINTS.values():                       # elk gebruikt endpoint bestaat in de spec en is een leesoperatie
        assert ep.op_id in by, ep.op_id


@pytest.mark.parametrize("script,paths", [
    ("build_manifests.py", ["mcp.json", "plugin.json", ".cursor-plugin", ".claude-plugin", "server.json"]),
    ("build_postman.py", ["postman"]),
    ("build_docs.py", ["docs/TOOLS.md", "docs/TOOLS.nl.md", "docs/EXPORT-SCHEMA.md"]),
    ("build_agents.py", ["agents", ".github/agents"]),
])
def test_generated_files_up_to_date(tmp_path, script, paths):
    import shutil
    before = {}
    for rel in paths:
        p = ROOT / rel
        for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
            if f.is_file():
                before[f] = f.read_bytes()
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True, capture_output=True, timeout=120)
        changed = [str(f.relative_to(ROOT)) for f, b in before.items() if f.read_bytes() != b]
    finally:
        for f, b in before.items():
            if f.read_bytes() != b:
                f.write_bytes(b)
    del shutil
    assert not changed, f"{script} wijzigt {changed}: genereer opnieuw en commit"


def test_skill_frontmatter():
    s = (ROOT / "skills/fiscai-octopus-api-connector/SKILL.md").read_text(encoding="utf-8")
    assert s.startswith("---\nname: fiscai-octopus-api-connector\ndescription: ")


def test_mcpb_bundle_reproducible(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = mod.manifest()
    assert m["license"] == "Apache-2.0" and "Powered by FISCALCI Accounting & Tax (Askin Alci)" in m["description"]
    assert m["version"] == tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    sj = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    pkg = sj["packages"][0]
    assert pkg["registryType"] == "mcpb" and pkg["identifier"].endswith(f"/v{m['version']}/fiscai-octopus-api-connector-{m['version']}.mcpb")
    assert len(pkg["fileSha256"]) == 64
    assert "pypi" not in json.dumps(sj).lower()

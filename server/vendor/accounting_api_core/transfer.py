"""Dossieroverdracht per boekjaar: neutraal pakket met per jaar een map, MANIFEST.json (rijen + SHA-256), CONTROL.md,
README.md voor de ontvanger en een checkpoint om een onderbroken export te hervatten.

De connector levert de gegevens (collectors); deze module schrijft, telt, controleert en documenteert.
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from .attribution import ATTRIBUTION
from .branding import BE_NOTICE
from .tabular import WRITERS, sha256

CHECKPOINT = ".transfer-checkpoint.json"
FORMATS = ("csv", "json", "xlsx")


class TransferError(Exception):
    pass


def safe_name(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(s)).strip("-")
    return s[:80] or "x"


class TransferPackage:
    def __init__(self, out_dir: Path, source_name: str, formats: Iterable[str] = ("csv", "json"), resume: bool = True,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self.out = Path(out_dir).expanduser()
        self.source = source_name
        self.formats = [f for f in formats]
        for f in self.formats:
            if f not in FORMATS:
                raise TransferError(f"Onbekend formaat '{f}'. Kies uit {', '.join(FORMATS)}.")
        self.clock = clock
        self.out.mkdir(parents=True, exist_ok=True)
        self.cp_path = self.out / CHECKPOINT
        self.cp: dict = {"done": [], "files": {}, "controls": {}}
        if resume and self.cp_path.is_file():
            self.cp = json.loads(self.cp_path.read_text(encoding="utf-8"))
        self.cp.setdefault("done", [])
        self.cp.setdefault("files", {})
        self.cp.setdefault("controls", {})

    # -------------------------------------------------------------- checkpoint
    def done(self, step: str) -> bool:
        return step in self.cp["done"]

    def mark(self, step: str) -> None:
        if step not in self.cp["done"]:
            self.cp["done"].append(step)
        self._save_cp()

    def _save_cp(self) -> None:
        self.cp_path.write_text(json.dumps(self.cp, ensure_ascii=False, indent=1), encoding="utf-8")

    # -------------------------------------------------------------- schrijven
    def year_dir(self, label: str) -> Path:
        d = self.out / safe_name(f"boekjaar-{label}")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write(self, folder: Path, name: str, rows: list[dict], meta: Optional[dict] = None) -> list[str]:
        written = []
        for f in self.formats:
            p = folder / f"{safe_name(name)}.{f}"
            if f == "json":
                WRITERS[f](p, rows, {"dataset": name, "bron": self.source, **(meta or {})})
            else:
                WRITERS[f](p, rows)
            rel = str(p.relative_to(self.out))
            self.cp["files"][rel] = {"rows": len(rows), "sha256": sha256(p), "bytes": p.stat().st_size}
            written.append(rel)
        self._save_cp()
        return written

    def control(self, label: str, checks: list[dict]) -> None:
        """checks: [{"controle", "ok" (True/False/None), "detail"}]. None = niet te controleren met de API."""
        self.cp["controls"][label] = checks
        self._save_cp()

    # -------------------------------------------------------------- afronden
    def write_control_md(self, title: str) -> Path:
        L = [f"# {title}", "", f"Bron: {self.source} (alleen lezen). Opgemaakt: {self.clock().isoformat(timespec='seconds')}", ""]
        for label, checks in self.cp["controls"].items():
            L += [f"## {label}", "", "| Controle | Resultaat | Detail |", "|---|---|---|"]
            for c in checks:
                res = "OK" if c.get("ok") is True else ("AFWIJKING" if c.get("ok") is False else "niet controleerbaar")
                L.append(f"| {c.get('controle')} | {res} | {str(c.get('detail', '')).replace('|', '/')} |")
            L.append("")
        L += [ATTRIBUTION, "", f"_{BE_NOTICE['nl']}_", ""]
        p = self.out / "CONTROL.md"
        p.write_text("\n".join(L), encoding="utf-8")
        return p

    def write_manifest(self, meta: dict) -> Path:
        files = dict(sorted(self.cp["files"].items()))
        for extra in ("README.md", "CONTROL.md"):
            p = self.out / extra
            if p.is_file():
                files[extra] = {"rows": None, "sha256": sha256(p), "bytes": p.stat().st_size}
        ok = all(c.get("ok") is not False for checks in self.cp["controls"].values() for c in checks)
        man = {"bron": self.source, "gemaakt": self.clock().isoformat(timespec="seconds"), "attributie": ATTRIBUTION, "scope": BE_NOTICE["nl"],
               **meta, "controles_ok": ok, "bestanden": files}
        p = self.out / "MANIFEST.json"
        p.write_text(json.dumps(man, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return p

    def write_readme(self, text: str) -> Path:
        if ATTRIBUTION not in text:
            text = text.rstrip() + "\n\n" + ATTRIBUTION + "\n"
        p = self.out / "README.md"
        p.write_text(text, encoding="utf-8")
        return p

    def zip(self, target: Optional[Path] = None) -> Path:
        target = Path(target or self.out.with_suffix(".zip"))
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(self.out.rglob("*")):
                if p.is_file() and p.name != CHECKPOINT:
                    z.write(p, p.relative_to(self.out))
        return target

    def finish(self) -> None:
        if self.cp_path.exists():
            self.cp_path.unlink()


def estimate(plan: dict[str, int], remaining: dict[str, Optional[int]]) -> dict:
    """plan: {endpointsleutel: aantal calls}. remaining: {endpointsleutel: resterend vandaag of None (geen limiet)}."""
    short = {k: {"nodig": n, "resterend": remaining.get(k)} for k, n in plan.items() if remaining.get(k) is not None and n > (remaining.get(k) or 0)}
    return {"plan": plan, "totaal_calls": sum(plan.values()), "tekort": short, "past_vandaag": not short}

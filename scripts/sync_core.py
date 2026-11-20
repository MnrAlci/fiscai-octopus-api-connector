"""Kopieert de gedeelde kern (FISCAi Accounting API Core) naar server/vendor/accounting_api_core.

Gebruik: python scripts/sync_core.py [PAD_NAAR_accounting-api-core]
Zo werkt de connector zonder extra installatie (zoals de Yuki-connector met zijn vendor-map). CI controleert dat de kopie
overeenkomt met CORE_VERSION.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT.parent / "accounting-api-core"


def main(src: Path) -> None:
    pkg = src / "src" / "accounting_api_core"
    if not pkg.is_dir():
        raise SystemExit(f"Kern niet gevonden: {pkg}")
    dst = ROOT / "server" / "vendor" / "accounting_api_core"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(pkg, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    ver = next(line.split('"')[1] for line in (pkg / "__init__.py").read_text().splitlines() if line.startswith("__version__"))
    (ROOT / "server" / "vendor" / "CORE_VERSION").write_text(ver + "\n", encoding="utf-8")
    print(f"Kern {ver} gekopieerd naar {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)

"""Opdrachtregel zonder installatie: python server/run_cli.py doctor"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "vendor")]

from octopus_mcp.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

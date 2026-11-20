"""Logging: standaard stil; optioneel JSON-regels op stderr. Berichten gaan door de geheimen-scrubber; argumenten worden nooit gelogd."""
from __future__ import annotations

import json
import logging
import os
import sys

from .profile import get_profile

LOG = logging.getLogger("accounting")
LEVELS = ("debug", "info", "warning", "error", "critical")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        from .scrub import scrub
        d = {"ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"), "level": record.levelname.lower(), "logger": record.name,
             "msg": scrub(record.getMessage())}
        for k in ("tool", "event", "duration_ms", "ok", "hook"):
            if hasattr(record, k):
                d[k] = getattr(record, k)
        return json.dumps(d, ensure_ascii=False, default=str)


def setup(level: str | None = None, fmt: str | None = None, quiet: bool = False, verbose: bool = False) -> None:
    global LOG
    pf = get_profile()
    LOG = logging.getLogger(pf.logger)
    level = (level or os.environ.get(pf.env("LOG_LEVEL")) or ("debug" if verbose else "warning")).lower()
    if level not in LEVELS:
        raise ValueError(f"Ongeldig log-niveau '{level}'. Kies uit: {', '.join(LEVELS)}.")
    if quiet:
        level = "error"
    fmt = (fmt or os.environ.get(pf.env("LOG_FORMAT")) or "text").lower()
    LOG.handlers.clear()
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(JsonFormatter() if fmt == "json" else logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    LOG.addHandler(h)
    LOG.setLevel(getattr(logging, level.upper()))
    LOG.propagate = False

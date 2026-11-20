"""MCP-server (stdio) van de FISCAi Octopus API Connector, gebouwd op de neutrale kern."""
from __future__ import annotations

import sys
from typing import Optional

from accounting_api_core.attribution import ATTRIBUTION
from accounting_api_core.mcp import Server, serve_stdio

from . import __version__, edition
from .tools import Tools

INSTRUCTIONS = (f"{edition.DISPLAY_NAME}: alleen-lezen toegang tot de Octopus-boekhoud-API (België). Octopus legt per endpoint een lage daglimiet op "
                "(stamdata 2 per dag): gebruik octopus_sync en de lokale cache, vraag niet herhaaldelijk dezelfde lijst op, en kijk met octopus_quota "
                f"hoeveel calls er nog over zijn. Geen fiscaal of juridisch advies. {ATTRIBUTION}")


def build(tools: Optional[Tools] = None) -> Server:
    return Server(tools or Tools(), edition.PLUGIN_NAME, edition.DISPLAY_NAME, __version__, edition.REQUIRE_ATTRIBUTION, instructions=INSTRUCTIONS)


def main() -> int:
    from .config import drop_unresolved_placeholders
    drop_unresolved_placeholders()
    try:
        srv = build()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Start mislukt: {exc}\n")
        return 1
    return serve_stdio(srv)

"""Connectorprofiel: alles wat per boekhoudpakket verschilt (prefix, namen, tools), zodat de kern neutraal blijft.

Elke connector roept bij het importeren één keer :func:`configure` aan, vóór andere kernmodules iets doen.
De kern leest het profiel altijd op het moment van gebruik (nooit bij import), zodat de volgorde van imports niet uitmaakt.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ConnectorProfile:
    env_prefix: str = "ACCOUNTING"                 # YUKI, OCTOPUS, ...
    source_name: str = "het boekhoudpakket"        # naam in teksten: "Yuki", "Octopus"
    source_key: str = "source"                     # korte sleutel: "yuki", "octopus"
    prog: str = "accounting-api-connector"         # CLI-naam
    display_name: str = "FISCAi Accounting API Connector"
    logger: str = "accounting"
    file_prefix: str = "accounting"                # bestandsnamen van exports: <prefix>-<dataset>.<fmt>
    secret_env: tuple = ()                         # omgevingsvariabelen waarvan de waarde nooit naar buiten mag
    export_tool: str = ""                          # naam van de exporttool (on_export-hook)
    transfer_tool: str = ""                        # naam van de dossieroverdrachttool (on_export-hook)
    # automatisering (workflows)
    wf_tools: dict = field(default_factory=dict)   # {"kpis": ..., "open_items": ..., "dossier_status": ..., "export": ...}
    wf_client_key: str = "administratie"           # sleutel in [[clients]] en argumentnaam voor de tools
    wf_client_value: str = '"[Voorbeeld] BV"'      # TOML-waarde in het voorbeeld (bv. 0 voor een numeriek dossier-id)
    wf_status_cfg_key: str = "financial_year_id"   # sleutel in [[clients]] voor de dossierstatus
    wf_status_arg: str = "jaar_id"                 # argumentnaam van de statustool
    wf_status_cast: Callable[[Any], Any] = int
    wf_example: Optional[str] = None               # voorbeeld-workflows.toml (None = generiek voorbeeld)
    tools_factory: Optional[Callable[[], tuple]] = None   # () -> (call, hooks) voor 'workflows run'

    def env(self, name: str) -> str:
        """Volledige naam van een omgevingsvariabele: env('HOOKS_FILE') -> '<PREFIX>_HOOKS_FILE'."""
        return f"{self.env_prefix}_{name}"


_ACTIVE = ConnectorProfile()


def get_profile() -> ConnectorProfile:
    return _ACTIVE


def configure(profile: Optional[ConnectorProfile] = None, **changes: Any) -> ConnectorProfile:
    """Zet het actieve profiel (volledig of met losse wijzigingen) en geef het terug."""
    global _ACTIVE
    base = profile or _ACTIVE
    _ACTIVE = replace(base, **changes) if changes else base
    return _ACTIVE


def env(name: str) -> str:
    return _ACTIVE.env(name)

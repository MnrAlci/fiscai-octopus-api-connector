"""FISCAi Octopus API Connector: alleen-lezen koppeling met de Octopus-boekhoud-API (België) als MCP-server en opdrachtregel.

Powered by FISCALCI Accounting & Tax (Askin Alci)
"""
from accounting_api_core import ConnectorProfile, configure

from . import edition

__version__ = "1.0.0"

SECRET_ENV = ("OCTOPUS_PASSWORD", "OCTOPUS_SOFTWARE_HOUSE_UUID", "OCTOPUS_CACHE_KEY", "OCTOPUS_USER")


def _tools_factory(tools=None):
    """(aanroeper, hooks) voor de automatisering; ``tools`` laat de CLI/tests een eigen Tools-instantie meegeven."""
    from accounting_api_core.automation.engine import ToolRunner
    from accounting_api_core.hooks import Hooks
    from .tools import Tools
    hooks = Hooks.from_env()
    return ToolRunner(tools or Tools(), hooks), hooks


PROFILE = configure(ConnectorProfile(
    env_prefix="OCTOPUS", source_name="Octopus", source_key="octopus", prog=edition.PROG, display_name=edition.DISPLAY_NAME,
    logger="octopus", file_prefix="octopus", secret_env=SECRET_ENV,
    export_tool="octopus_export_dataset", transfer_tool="octopus_dossier_transfer_export",
    wf_tools={"kpis": "octopus_dashboard_kpis", "open_items": "octopus_ouderdom_openstaande_posten",
              "dossier_status": "octopus_boekjaar_status", "export": "octopus_export_dataset"},
    wf_client_key="dossier_id", wf_client_value="1  # [Voorbeeld]: vervang door het dossier-id uit octopus_dossiers", wf_status_cfg_key="bookyear_id", wf_status_arg="boekjaar_id", wf_status_cast=int,
    tools_factory=_tools_factory))

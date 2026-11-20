"""FISCAi Accounting API Core: gedeelde, neutrale bouwstenen voor de FISCAi-boekhoudconnectors.

Powered by FISCALCI Accounting & Tax (Askin Alci)
"""
from .profile import ConnectorProfile, configure, get_profile

__version__ = "0.1.0"
__all__ = ["ConnectorProfile", "configure", "get_profile", "__version__"]

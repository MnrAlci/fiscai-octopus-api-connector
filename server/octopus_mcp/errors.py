"""Fouten van de Octopus-koppeling. Berichten bevatten nooit tokens, wachtwoorden of de Software House ID."""
from __future__ import annotations

import json
from typing import Any, Optional

from accounting_api_core.quota import QuotaExceeded  # noqa: F401 - hergebruik


class OctopusError(RuntimeError):
    pass


class OctopusConfigError(OctopusError):
    pass


class OctopusRefused(OctopusError):
    """Geweigerd door de veiligheidsregels (alleen lezen, schrijven uit, niet-toegelaten endpoint, dossier niet toegelaten)."""


class OctopusApiError(OctopusError):
    def __init__(self, status: int, endpoint: str, code: Optional[int] = None, message: str = "", technical: str = "", variant: str = "none") -> None:
        self.status, self.endpoint, self.code, self.message, self.technical, self.variant = status, endpoint, code, message, technical, variant
        hint = HINTS.get(status, "")
        super().__init__(f"Octopus antwoordde HTTP {status} op {endpoint}" + (f" (foutcode {code})" if code is not None else "") +
                         (f": {message}" if message else "") + (f" [{hint}]" if hint else ""))

    def as_dict(self) -> dict:
        return {"http_status": self.status, "endpoint": self.endpoint, "foutcode": self.code, "melding": self.message,
                "technisch": self.technical, "variant": self.variant}


class OctopusAuthError(OctopusApiError):
    pass


HINTS = {
    400: "ongeldige parameters; controleer de invoer",
    401: "token ongeldig of verlopen; de connector vraagt automatisch één keer een nieuw token aan",
    403: "geen toegang tot dit dossier of deze module",
    404: "niet gevonden (dossier, boekjaar of document)",
    500: "fout bij Octopus; bij rapporten vaak ongeldige querygegevens (boekjaar/periode)",
}


def parse_error(status: int, endpoint: str, body: Any) -> OctopusApiError:
    """Parse BEIDE varianten van het foutobject defensief.

    * OpenAPI-spec: ``ErrorResult{errorCode, errorMessage, technicalInfo}``
    * Handleiding: ``{octopusErrorCode, description, technicalDescription}``
    Welke variant de API effectief stuurt: verifieer actuele regel (zie docs/OPEN-QUESTIONS.md, T20).
    """
    data = body
    if isinstance(body, (bytes, str)):
        try:
            data = json.loads(body or "null")
        except ValueError:
            data = None
    cls = OctopusAuthError if status == 401 else OctopusApiError
    if isinstance(data, dict):
        if any(k in data for k in ("errorCode", "errorMessage", "technicalInfo")):
            return cls(status, endpoint, _int(data.get("errorCode")), str(data.get("errorMessage") or ""), str(data.get("technicalInfo") or ""), "spec")
        if any(k in data for k in ("octopusErrorCode", "description", "technicalDescription")):
            return cls(status, endpoint, _int(data.get("octopusErrorCode")), str(data.get("description") or ""),
                       str(data.get("technicalDescription") or ""), "manual")
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else (body if isinstance(body, str) else "")
    return cls(status, endpoint, None, text[:300].strip(), "", "none")


def _int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

"""Instellingen uit de omgeving (nooit uit de code). Geheimen worden nooit afgedrukt of gelogd."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from . import edition
from .errors import OctopusConfigError

DEFAULT_BASE_URL = "https://service.inaras.be/octopus-rest-api/v1"
ALLOWED_HOSTS = ("service.inaras.be",)
LOCALES = {0: "standaard van het dossier", 1: "Nederlands", 2: "Frans", 3: "Engels", 4: "Duits"}
TRUE = ("1", "true", "yes", "ja", "on")


@dataclass(frozen=True)
class Settings:
    software_house_uuid: str
    user: str
    password: str
    base_url: str
    locale_id: int
    data_dir: Path
    cache_key: str
    quota_reserve: int
    timeout: float
    max_retries: int
    write_enabled: bool
    write_max_per_day: int
    allowed_dossiers: tuple
    amounts_mode: str
    language: str

    @property
    def has_credentials(self) -> bool:
        return bool(self.software_house_uuid and self.user and self.password)

    def public(self) -> dict:
        """Veilige weergave: alleen of iets ingesteld is, nooit de waarde."""
        return {"software_house_uuid": bool(self.software_house_uuid), "user": bool(self.user), "password": bool(self.password),
                "base_url": self.base_url, "locale_id": self.locale_id, "data_dir": str(self.data_dir), "cache_key": bool(self.cache_key),
                "persistent_cache": len(self.cache_key) >= 16, "quota_reserve": self.quota_reserve, "timeout": self.timeout,
                "max_retries": self.max_retries, "write_enabled": self.write_enabled, "allowed_dossiers": list(self.allowed_dossiers),
                "amounts_mode": self.amounts_mode, "language": self.language}


def _int(env: Mapping, name: str, default: int, lo: int, hi: int) -> int:
    raw = str(env.get(name, "")).strip()
    if not raw:
        return default
    try:
        v = int(raw)
    except ValueError as exc:
        raise OctopusConfigError(f"{name} moet een geheel getal zijn.") from exc
    if not lo <= v <= hi:
        raise OctopusConfigError(f"{name} moet tussen {lo} en {hi} liggen.")
    return v


UNRESOLVED = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")


def drop_unresolved_placeholders(environ=None) -> list[str]:
    """Verwijder OCTOPUS_*-variabelen met een niet-ingevulde plaatshouder zoals '${OCTOPUS_USER}'.

    Sommige MCP-clients vullen ``${VAR}`` in mcp.json niet in en geven de tekst letterlijk door. Zo'n waarde telt als
    'niet ingesteld', zodat de standaardwaarde geldt (schrijven blijft dus uit). Geeft de namen terug (zonder waarden).
    """
    environ = os.environ if environ is None else environ
    weg = [k for k, v in list(environ.items()) if k.startswith("OCTOPUS_") and UNRESOLVED.match(str(v).strip())]
    for k in weg:
        del environ[k]
    return weg


def load(env: Optional[Mapping] = None) -> Settings:
    env = os.environ if env is None else env
    env = {k: v for k, v in env.items() if not (str(k).startswith("OCTOPUS_") and UNRESOLVED.match(str(v).strip()))}
    base = (env.get("OCTOPUS_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
    from urllib.parse import urlparse
    u = urlparse(base)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
        raise OctopusConfigError("OCTOPUS_BASE_URL moet https zijn op service.inaras.be (officiële Octopus REST API). "
                                 "De Management API wordt bewust niet ondersteund (kan kosten veroorzaken).")
    if "management" in u.path:
        raise OctopusConfigError("De Octopus Management API wordt niet ondersteund (kan kosten veroorzaken).")
    allowed = tuple(int(x) for x in str(env.get("OCTOPUS_ALLOWED_DOSSIERS", "")).replace(";", ",").split(",") if x.strip().isdigit())
    mode = (env.get("OCTOPUS_AMOUNTS_MODE") or "movement").strip().lower()
    if mode not in ("movement", "cumulative"):
        raise OctopusConfigError("OCTOPUS_AMOUNTS_MODE moet 'movement' of 'cumulative' zijn.")
    lang = (env.get("OCTOPUS_LANGUAGE") or "nl").strip().lower()
    return Settings(
        software_house_uuid=str(env.get("OCTOPUS_SOFTWARE_HOUSE_UUID", "")).strip(),
        user=str(env.get("OCTOPUS_USER", "")).strip(),
        password=str(env.get("OCTOPUS_PASSWORD", "")),
        base_url=base,
        locale_id=_int(env, "OCTOPUS_LOCALE_ID", 1, 0, 4),
        data_dir=Path(env.get("OCTOPUS_DATA_DIR") or (Path.home() / edition.HOME_DIR_NAME)).expanduser(),
        cache_key=str(env.get("OCTOPUS_CACHE_KEY", "")),
        quota_reserve=_int(env, "OCTOPUS_QUOTA_RESERVE", 0, 0, 100),
        timeout=float(_int(env, "OCTOPUS_TIMEOUT", 30, 5, 300)),
        max_retries=_int(env, "OCTOPUS_MAX_RETRIES", 0, 0, 3),
        write_enabled=str(env.get("OCTOPUS_WRITE_ENABLED", "")).strip().lower() in TRUE,
        write_max_per_day=_int(env, "OCTOPUS_WRITE_MAX_PER_DAY", 20, 1, 200),
        allowed_dossiers=allowed,
        amounts_mode=mode,
        language=lang if lang in ("nl", "fr", "en", "de") else "nl",
    )


ENV_TEMPLATE = """# FISCAi Octopus API Connector: voorbeeld-omgevingsbestand (alleen plaatshouders, nooit echte waarden committen).
# Software House ID: aan te vragen bij Octopus (zie docs/SETUP.md). Gebruikersnaam en wachtwoord van een Octopus-gebruiker met webservicemodule.
OCTOPUS_SOFTWARE_HOUSE_UUID=
OCTOPUS_USER=
OCTOPUS_PASSWORD=
# Taal van foutmeldingen: 0 standaard, 1 NL, 2 FR, 3 EN, 4 DE
OCTOPUS_LOCALE_ID=1
# Versleutelde cache en synchronisatie op schijf (min. 16 tekens). Zonder sleutel: alleen in het geheugen.
OCTOPUS_CACHE_KEY=
# OCTOPUS_DATA_DIR=~/.fiscai-octopus-api-connector
# Reserve per endpoint op de daglimiet (bv. 1 = laat telkens één call over voor manueel gebruik)
# OCTOPUS_QUOTA_RESERVE=0
# Alleen deze dossiers toelaten (komma-gescheiden dossier-id's); leeg = alle dossiers van de gebruiker
# OCTOPUS_ALLOWED_DOSSIERS=
# Saldi per periode: movement (beweging per periode) of cumulative; verifieer actuele regel
# OCTOPUS_AMOUNTS_MODE=movement
# Schrijven staat UIT. Alleen aanzetten na een bewuste beslissing (zie docs/WRITE.md).
# OCTOPUS_WRITE_ENABLED=false
# OCTOPUS_HOOKS_FILE=
# OCTOPUS_LOG_LEVEL=warning
"""

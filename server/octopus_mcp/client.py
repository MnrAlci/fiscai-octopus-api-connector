"""Octopus REST-client: tokens (10 min) met automatische vernieuwing, daglimiet per endpoint, cache en foutafhandeling.

Volgorde per call: toelating (alleen lezen, dossier-allowlist) -> cache -> quota-controle -> dossiertoken -> HTTP ->
bij 401 één keer nieuwe tokens en opnieuw -> fouten in beide varianten parsen -> cache vullen.
Elke verstuurde HTTP-request telt mee in de daglimiet (ook herhalingen en tokenaanvragen voor POST /dossiers).
Tokens, wachtwoord en Software House ID komen nooit in logs, antwoorden of de cache.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Optional

import httpx

from accounting_api_core.cache import ResponseCache
from accounting_api_core.quota import EndpointQuota
from accounting_api_core.rest import RestTransport
from accounting_api_core.securestore import SecureStore
from accounting_api_core.tokens import TokenCache

from . import __version__, edition
from .config import ALLOWED_HOSTS, Settings, load
from .endpoints import Endpoint, get, is_read_only, quota_limits
from .errors import OctopusApiError, OctopusAuthError, OctopusConfigError, OctopusRefused, parse_error

LOG = logging.getLogger("octopus.client")
TOKEN_TTL = 600          # 10 minuten (officiële handleiding en spec)
TOKEN_MARGIN = 60        # een minuut vóór het verlopen al vernieuwen


class OctopusClient:
    def __init__(self, settings: Optional[Settings] = None, http_transport: Optional[httpx.BaseTransport] = None,
                 clock: Callable[[], float] = time.monotonic, wall: Callable[[], float] = time.time,
                 today: Optional[Callable[[], str]] = None) -> None:
        self.s = settings or load()
        self.tokens = TokenCache(TOKEN_TTL, TOKEN_MARGIN, clock)
        self.store = SecureStore(self.s.data_dir / "store", self.s.cache_key)
        self.cache = ResponseCache(self.store, wall)
        self.quota = EndpointQuota(self.s.data_dir / "quota.json", quota_limits(), self.s.quota_reserve, today=today)
        self._http_transport = http_transport
        self._rest: Optional[RestTransport] = None
        self.calls: list[str] = []          # verstuurde requests (alleen endpoint-id's) voor status en tests

    # ------------------------------------------------------------------ infrastructuur
    @property
    def rest(self) -> RestTransport:
        if self._rest is None:
            if not self.s.has_credentials:
                raise OctopusConfigError("Octopus-gegevens ontbreken: stel OCTOPUS_SOFTWARE_HOUSE_UUID, OCTOPUS_USER en OCTOPUS_PASSWORD in "
                                         "(zie docs/SETUP.md). Er werd geen call gedaan.")
            self._rest = RestTransport(self.s.base_url, self.s.timeout, self.s.max_retries, ALLOWED_HOSTS, self._http_transport,
                                       f"{edition.PLUGIN_NAME}/{__version__}")
        return self._rest

    def _send(self, ep: Endpoint, quota_key: str, *, path: str, params=None, body=None, headers=None) -> httpx.Response:
        self.quota.check(quota_key)
        self.quota.record(quota_key)            # tellen VÓÓR verzenden: ook een mislukte request telt bij Octopus
        self.calls.append(ep.op_id)
        LOG.debug("call", extra={"event": ep.key})
        return self.rest.request(ep.method, path, params=params, json=body, headers=headers)

    # ------------------------------------------------------------------ tokens
    def _auth_token(self) -> str:
        def fetch() -> str:
            ep = get("authenticate")
            r = self._send(ep, ep.quota_key(), path="/authentication", body={"user": self.s.user, "password": self.s.password},
                           headers={"softwareHouseUuid": self.s.software_house_uuid, "Content-Type": "application/json"})
            if r.status_code != 200:
                err = parse_error(r.status_code, ep.op_id, r.content)
                raise OctopusAuthError(err.status, ep.op_id, err.code,
                                       "aanmelden mislukt; controleer gebruiker, wachtwoord, Software House ID en of de webservicemodule actief is",
                                       "", err.variant)
            tok = (r.json() or {}).get("token")
            if not tok:
                raise OctopusApiError(r.status_code, ep.op_id, None, "antwoord zonder token")
            return tok
        return self.tokens.get("auth", fetch)

    def _dossier_token(self, dossier_id: int) -> str:
        def fetch() -> str:
            ep = get("dossier_token")
            for attempt in (1, 2):
                r = self._send(ep, ep.quota_key(), path="/dossiers", params={"dossierId": int(dossier_id), "localeId": self.s.locale_id},
                               headers={"Token": self._auth_token()})
                if r.status_code == 401 and attempt == 1:
                    self.tokens.invalidate("auth")
                    continue
                if r.status_code != 200:
                    raise parse_error(r.status_code, ep.op_id, r.content)
                data = r.json() or {}
                tok = data.get("Dossiertoken") or data.get("dossiertoken") or data.get("dossierToken")
                if not tok:
                    raise OctopusApiError(r.status_code, ep.op_id, None, "antwoord zonder dossiertoken")
                return tok
            raise OctopusAuthError(401, ep.op_id, None, "token geweigerd")
        return self.tokens.get(("dossier", int(dossier_id)), fetch)

    # ------------------------------------------------------------------ publiek
    def check_dossier(self, dossier_id: Optional[int]) -> None:
        if dossier_id is not None and self.s.allowed_dossiers and int(dossier_id) not in self.s.allowed_dossiers:
            raise OctopusRefused("Dit dossier staat niet in OCTOPUS_ALLOWED_DOSSIERS.")

    def call(self, key: str, *, dossier_id: Optional[int] = None, path_params: Optional[dict] = None, query: Optional[dict] = None,
             body: Optional[dict] = None, fresh: bool = False, search: bool = False, use_cache: bool = True) -> Any:
        ep = get(key)
        if not is_read_only(ep):
            raise OctopusRefused(f"{ep.op_id} is geen leesendpoint; schrijven verloopt alleen via write.py (standaard uit).")
        if key in ("authenticate", "dossier_token"):
            raise OctopusRefused("Tokens worden intern beheerd.")
        needs_dossier = "{dossierId}" in ep.path
        if needs_dossier and dossier_id is None:
            raise ValueError("dossier_id is verplicht voor dit endpoint.")
        self.check_dossier(dossier_id)
        pp = {"dossierId": dossier_id, **(path_params or {})}
        path = ep.path
        for k, v in pp.items():
            if v is not None:
                path = path.replace("{" + k + "}", str(v))
        if "{" in path:
            raise ValueError(f"Ontbrekende padparameter voor {ep.op_id}.")
        q = {k: v for k, v in (query or {}).items() if v is not None}
        ckey = json.dumps([ep.op_id, dossier_id, pp, q, body], sort_keys=True, default=str)
        ttl = ep.cache_ttl(search)
        if use_cache and not fresh:
            hit = self.cache.get(ckey, ttl)
            if hit is not None:
                return hit
        qk = ep.quota_key(search)
        for attempt in (1, 2):
            headers: dict = {}
            if needs_dossier:
                headers["dossierToken"] = self._dossier_token(int(dossier_id))
            elif key in ("dossiers", "whoami"):
                headers["Token"] = self._auth_token()
            if body is not None:
                headers["Content-Type"] = "application/json"
            r = self._send(ep, qk, path=path, params=q, body=body, headers=headers)
            if r.status_code == 401 and attempt == 1:     # token verlopen of ingetrokken: één keer vernieuwen
                if needs_dossier:
                    self.tokens.invalidate(("dossier", int(dossier_id)))
                self.tokens.invalidate("auth")
                continue
            if r.status_code == 204:
                data: Any = None
                break
            if r.status_code >= 400:
                raise parse_error(r.status_code, ep.op_id, r.content)
            ctype = r.headers.get("content-type", "")
            data = r.json() if "json" in ctype or r.content[:1] in (b"{", b"[") else r.text
            break
        if use_cache and data is not None:
            self.cache.put(ckey, data)
        return data

    def status(self) -> dict:
        return {"configured": self.s.has_credentials, "settings": self.s.public(), "quota": self.quota.snapshot(), "cache": self.store.describe(),
                "cache_hits": self.cache.hits, "requests_this_process": len(self.calls), "tokens_issued": self.tokens.issued}

    def close(self) -> None:
        if self._rest is not None:
            self._rest.close()

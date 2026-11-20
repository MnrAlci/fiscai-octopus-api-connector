"""Neutrale JSON-REST-transport bovenop httpx: vaste basis-URL (alleen https), time-outs, geen logging van inhoud.

Herhalen gebeurt alleen bij netwerkfouten en alleen als de connector dat expliciet toelaat (elke herhaling kost quota).
"""
from __future__ import annotations

import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx


class TransportError(RuntimeError):
    pass


class RestTransport:
    def __init__(self, base_url: str, timeout: float = 30.0, max_retries: int = 0, allowed_hosts: Optional[tuple] = None,
                 transport: Optional[httpx.BaseTransport] = None, user_agent: str = "fiscai-accounting-connector") -> None:
        u = urlparse(base_url)
        if u.scheme != "https":
            raise TransportError("Alleen https-basis-URL's zijn toegelaten.")
        if allowed_hosts and u.hostname not in allowed_hosts:
            raise TransportError(f"Host '{u.hostname}' is niet toegelaten.")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(0, int(max_retries))
        # Cookies blijven aan (sommige API's vragen session cookies); geen redirects naar andere hosts.
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout, transport=transport, follow_redirects=False,
                                   headers={"User-Agent": user_agent, "Accept": "application/json"})
        self.sent = 0

    def request(self, method: str, path: str, *, params: Optional[dict] = None, json: Any = None, headers: Optional[dict] = None) -> httpx.Response:
        attempt = 0
        while True:
            try:
                self.sent += 1
                return self.client.request(method, path, params={k: v for k, v in (params or {}).items() if v is not None}, json=json, headers=headers)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                if attempt >= self.max_retries:
                    raise TransportError(f"Netwerkfout: {type(exc).__name__}") from exc
                attempt += 1
                time.sleep(min(2 ** attempt, 10))

    def close(self) -> None:
        self.client.close()

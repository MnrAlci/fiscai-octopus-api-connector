"""Mock van de Octopus REST API: geen echte calls, geen echte gegevens. Alle data is synthetisch ([Voorbeeld])."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "server" / "vendor")]

FAKE_SHU = "00000000-test-shu-not-real"
FAKE_USER = "voorbeeld-gebruiker"
FAKE_PASS = "test-password-not-real"
FAKE_CACHE = "test-cache-key-not-real-0123456789"
DOS = 101
BASE = "/octopus-rest-api/v1"
FIX = json.loads((Path(__file__).parent / "fixtures" / "octopus.json").read_text(encoding="utf-8"))


class FakeOctopus:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.auth_tokens: set[str] = set()
        self.dossier_tokens: dict[str, int] = {}
        self.n = 0
        self.fail: dict[tuple, list] = {}       # (METHOD, pad-suffix) -> [(status, body), ...] (eenmalig per item)
        self.data = json.loads(json.dumps(FIX))
        self.modified: dict = {}                 # overschrijft antwoorden van */modified per sleutel

    # -------------------------------------------------------------- hulp
    def ops(self) -> list[str]:
        return [f"{r['method']} {r['path']}" for r in self.requests]

    def count(self, method: str, suffix: str) -> int:
        return sum(1 for r in self.requests if r["method"] == method and r["path"].endswith(suffix))

    def expire_all(self) -> None:
        self.auth_tokens.clear()
        self.dossier_tokens.clear()

    @staticmethod
    def j(status: int, body) -> httpx.Response:
        return httpx.Response(status, json=body, headers={"content-type": "application/json"})

    def err(self, status=401):
        return self.j(status, {"errorCode": 1, "errorMessage": "Token is not valid", "technicalInfo": "expired"})

    # -------------------------------------------------------------- handler
    def handler(self, req: httpx.Request) -> httpx.Response:
        path = req.url.path[len(BASE):] if req.url.path.startswith(BASE) else req.url.path
        q = {k: v[0] for k, v in parse_qs(req.url.query.decode()).items()}
        body = json.loads(req.content) if req.content else None
        self.requests.append({"method": req.method, "path": path, "query": q, "body": body, "headers": dict(req.headers)})
        for (m, suf), queue in list(self.fail.items()):
            if m == req.method and path.endswith(suf) and queue:
                st, b = queue.pop(0)
                if isinstance(b, (dict, list)):
                    return self.j(st, b)
                return httpx.Response(st, text=b)
        if path == "/authentication" and req.method == "POST":
            if req.headers.get("softwareHouseUuid") != FAKE_SHU or body != {"user": FAKE_USER, "password": FAKE_PASS}:
                return self.j(401, {"octopusErrorCode": 99, "description": "Invalid credentials", "technicalDescription": "x"})
            self.n += 1
            tok = f"auth-{self.n}"
            self.auth_tokens.add(tok)
            return self.j(200, {"token": tok})
        if path == "/about/version":
            return httpx.Response(200, text="1.0.0-test")
        if path == "/error":
            return self.j(400, {"errorCode": int(q["errorCode"]), "errorMessage": "[Voorbeeld] foutmelding", "technicalInfo": "sample"})
        if path in ("/dossiers", "/authentication"):
            if req.headers.get("Token") not in self.auth_tokens:
                return self.err()
            if path == "/authentication":
                return self.j(200, {"user": "[Voorbeeld]"})
            if req.method == "GET":
                return self.j(200, self.data["dossiers"])
            self.n += 1
            tok = f"dos-{self.n}"
            self.dossier_tokens[tok] = int(q["dossierId"])
            return self.j(200, {"Dossiertoken": tok})
        if not path.startswith(f"/dossiers/{DOS}/"):
            return self.j(404, {"errorCode": 404, "errorMessage": "Dossier not found", "technicalInfo": ""})
        if self.dossier_tokens.get(req.headers.get("dossierToken")) != DOS:
            return self.err()
        sub = path[len(f"/dossiers/{DOS}"):]
        return self.route(req.method, sub, q, body)

    def route(self, method, sub, q, body):
        d = self.data
        if method != "GET" and not sub.startswith("/reports/"):
            return self.j(201, {"ok": True, "echo": body})
        if sub == "/bookyears":
            return self.j(200, d["bookyears"])
        if sub.startswith("/bookyears/") and sub.endswith("/journals"):
            return self.j(200, d["journals"])
        if sub.startswith("/bookyears/") and "/bookings/modified" in sub:
            by, jt = int(sub.split("/")[2]), int(q["journalTypeId"])
            key = ("bookings", by, jt)
            if key in self.modified:
                return self.j(200, self.modified[key])
            if by == -1:
                return self.j(200, {"modifiedBookings": [], "deletedBookings": []})
            rows = [b for b in d["bookings"] if b["bookyearKey"]["id"] == by and b["journalType"] == jt]
            return self.j(200, {"modifiedBookings": rows, "deletedBookings": []})
        if sub.startswith("/bookyears/"):
            by = int(sub.split("/")[2])
            return self.j(200, next(b for b in d["bookyears"] if b["bookyearKey"]["id"] == by))
        if sub == "/accounts":
            return self.j(200, [a for a in d["accounts"] if a["accountKey"]["bookyearKey"]["id"] == int(q["bookyearId"])])
        if sub == "/accounts/modified":
            return self.j(200, self.modified.get("accounts", {"modified": [], "deleted": []}))
        if sub == "/accounts/amounts/modified":
            return self.j(200, self.modified.get("amounts", {"modified": d["amounts"], "deleted": []}))
        if sub == "/relations":
            if q:
                return self.j(200, [r for r in d["relations"] if q.get("name", "").lower() in r["name"].lower()])
            return self.j(200, d["relations"])
        if sub == "/relations/modified":
            return self.j(200, self.modified.get("relations", {"modified": [], "deleted": []}))
        if sub == "/reports/clients/open":
            return self.j(200, d["open_clients"])
        if sub == "/reports/suppliers/open":
            return self.j(200, d["open_suppliers"])
        if sub.startswith("/reports/"):
            return self.j(200, [])
        if sub == "/vatcodes":
            return self.j(200, d["vatcodes"])
        if sub in ("/costcentres", "/costcentres/active", "/currencies", "/customfields", "/products", "/productgroups", "/bank/invoices", "/bank/paymentlist",
                   "/bank/enveloppes"):
            return self.j(200, d.get(sub.strip("/").replace("/", "_"), []))
        return self.j(200, {})


@pytest.fixture
def fake():
    return FakeOctopus()


@pytest.fixture
def env(monkeypatch, tmp_path):
    for k in list(__import__("os").environ):
        if k.startswith("OCTOPUS_"):
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("OCTOPUS_SOFTWARE_HOUSE_UUID", FAKE_SHU)
    monkeypatch.setenv("OCTOPUS_USER", FAKE_USER)
    monkeypatch.setenv("OCTOPUS_PASSWORD", FAKE_PASS)
    monkeypatch.setenv("OCTOPUS_DATA_DIR", str(tmp_path / "data"))
    return tmp_path


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, s: float) -> None:
        self.t += s


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def make_client(fake, env, clock):
    from octopus_mcp.client import OctopusClient
    from octopus_mcp.config import load

    def mk(**env_over):
        import os
        for k, v in env_over.items():
            os.environ[k] = v
        return OctopusClient(load(), httpx.MockTransport(fake.handler), clock=clock, wall=clock)
    return mk


@pytest.fixture
def tools(make_client):
    from datetime import date
    from octopus_mcp.tools import Tools
    return Tools(make_client(), today=lambda: date(2026, 11, 20))


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def _blocked(*a, **k):
        raise RuntimeError("Netwerk is geblokkeerd in de tests")
    monkeypatch.setattr(socket.socket, "connect", _blocked)

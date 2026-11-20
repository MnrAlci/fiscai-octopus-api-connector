"""Minimale MCP-server over stdio (JSON-RPC 2.0, één bericht per regel), neutraal voor elke connector.

De connector levert een object met ``list() -> [tooldefinitie]`` en ``call(name, args) -> dict``.
Fouten van tools gaan als ``isError`` terug, gescrubd van geheimen; de attributie wordt bij de start gecontroleerd.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Callable, Optional

from .attribution import AttributionError, verify_startup
from .hooks import Hooks, guarded_call
from .scrub import scrub

PROTOCOL = "2025-06-18"


class Server:
    def __init__(self, tools: Any, name: str, title: str, version: str, require_attribution: bool = True,
                 hooks: Optional[Hooks] = None, resources: Optional[Callable[[], list]] = None,
                 read_resource: Optional[Callable[[str], dict]] = None, instructions: str = "") -> None:
        verify_startup(require_attribution)
        self.tools, self.name, self.title, self.version = tools, name, title, version
        self.hooks = hooks or Hooks.from_env()
        self.resources, self.read_resource, self.instructions = resources, read_resource, instructions

    def handle(self, msg: dict) -> Optional[dict]:
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if method is None or mid is None:
            return None
        try:
            result = self._dispatch(method, params)
        except KeyError as exc:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Onbekende methode: {exc.args[0]}"}}
        except AttributionError as exc:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(exc)}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def _dispatch(self, method: str, p: dict) -> Any:
        if method == "initialize":
            res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {"listChanged": False}, "resources": {}},
                   "serverInfo": {"name": self.name, "title": self.title, "version": self.version}}
            if self.instructions:
                res["instructions"] = self.instructions
            return res
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": self.tools.list()}
        if method == "tools/call":
            return self._call(p.get("name", ""), p.get("arguments"))
        if method == "resources/list":
            return {"resources": self.resources() if self.resources else []}
        if method == "resources/read":
            if not self.read_resource:
                raise KeyError(p.get("uri"))
            return self.read_resource(p.get("uri", ""))
        raise KeyError(method)

    def _call(self, name: str, args: Optional[dict]) -> dict:
        try:
            out = guarded_call(self.hooks, self.tools.call, name, args)
            text = json.dumps(out, ensure_ascii=False, default=str)
            res: dict = {"content": [{"type": "text", "text": scrub(text)}], "isError": False}
            if isinstance(out, dict):
                res["structuredContent"] = scrub(json.loads(text))
            return res
        except AttributionError:
            raise
        except Exception as exc:  # noqa: BLE001 - toolfout, zonder geheimen
            return {"content": [{"type": "text", "text": scrub(f"{type(exc).__name__}: {exc}")}], "isError": True}


def serve_stdio(server: Server, stdin=None, stdout=None) -> int:
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = server.handle(msg)
        if resp is not None:
            stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0

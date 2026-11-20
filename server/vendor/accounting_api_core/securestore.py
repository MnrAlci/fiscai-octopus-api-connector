"""Lokale opslag voor gecachte antwoorden en synchronisatiedata.

* Met een sleutel (omgevingsvariabele, bv. <PREFIX>_CACHE_KEY): versleuteld op schijf (Fernet, bibliotheek ``cryptography``).
* Zonder sleutel: alleen in het geheugen (veilig standaard: geen klantgegevens onversleuteld op schijf).
Bestanden krijgen rechten 0600; namen zijn SHA-256-hashes, zodat er geen dossiernummers of zoektermen in bestandsnamen staan.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional


class StoreError(RuntimeError):
    pass


def _fernet(secret: str):
    try:
        from cryptography.fernet import Fernet  # type: ignore
    except ImportError as exc:  # pragma: no cover - afhankelijk van installatie
        raise StoreError("Versleutelde opslag vraagt de bibliotheek 'cryptography' (pip install cryptography).") from exc
    key = base64.urlsafe_b64encode(hashlib.sha256(("fiscai-store-v1:" + secret).encode("utf-8")).digest())
    return Fernet(key)


class SecureStore:
    def __init__(self, folder: Optional[Path], secret: Optional[str]) -> None:
        self.secret = secret or ""
        self.persistent = bool(folder) and len(self.secret) >= 16
        self.folder = Path(folder).expanduser() if folder else None
        self._mem: dict[str, bytes] = {}
        self._f = _fernet(self.secret) if self.persistent else None
        if self.persistent:
            self.folder.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(self.folder, 0o700)
            except OSError:
                pass

    @staticmethod
    def _name(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def put(self, key: str, value: Any) -> None:
        raw = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
        if not self.persistent:
            self._mem[key] = raw
            return
        p = self.folder / (self._name(key) + ".bin")
        tmp = p.with_suffix(".tmp")
        tmp.write_bytes(self._f.encrypt(raw))
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(p)

    def get(self, key: str) -> Any:
        if not self.persistent:
            raw = self._mem.get(key)
            return None if raw is None else json.loads(raw)
        p = self.folder / (self._name(key) + ".bin")
        if not p.is_file():
            return None
        try:
            return json.loads(self._f.decrypt(p.read_bytes()))
        except Exception as exc:  # noqa: BLE001 - verkeerde sleutel of beschadigd bestand
            raise StoreError("De lokale opslag kan niet ontsleuteld worden (andere sleutel of beschadigd bestand). "
                             "Gebruik dezelfde sleutel of wis de cachemap.") from exc

    def delete(self, key: str) -> None:
        self._mem.pop(key, None)
        if self.persistent:
            p = self.folder / (self._name(key) + ".bin")
            if p.exists():
                p.unlink()

    def clear(self) -> int:
        n = len(self._mem)
        self._mem.clear()
        if self.persistent:
            for p in self.folder.glob("*.bin"):
                p.unlink()
                n += 1
        return n

    def describe(self) -> dict:
        return {"persistent": self.persistent, "encrypted": self.persistent, "folder": str(self.folder) if self.persistent else None,
                "entries": (len(list(self.folder.glob("*.bin"))) if self.persistent else len(self._mem))}

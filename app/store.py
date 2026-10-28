"""Persistence of the configured Sonarr/Radarr instances (JSON file in /config)."""
from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any


class InstanceStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def _read(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text("utf-8"))
        except FileNotFoundError:
            return []

    def _write(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, self.path)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._read()

    def get(self, iid: str) -> dict[str, Any] | None:
        return next((i for i in self.list() if i["id"] == iid), None)

    def add(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            items = self._read()
            inst = {"id": uuid.uuid4().hex[:8], **data}
            items.append(inst)
            self._write(items)
            return inst

    def update(self, iid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            items = self._read()
            for i, inst in enumerate(items):
                if inst["id"] == iid:
                    items[i] = {**inst, **data}
                    self._write(items)
                    return items[i]
        return None

    def delete(self, iid: str) -> bool:
        with self._lock:
            items = self._read()
            kept = [i for i in items if i["id"] != iid]
            if len(kept) == len(items):
                return False
            self._write(kept)
            return True


def public(inst: dict[str, Any]) -> dict[str, Any]:
    """Instance as exposed to the browser: the API key never leaves the server."""
    out = {k: v for k, v in inst.items() if k != "api_key"}
    out["has_key"] = bool(inst.get("api_key"))
    return out

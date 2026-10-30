"""Scheduled full backups: every N days at a given time, keeping the last few of each instance.

The schedule and what happened at the last run live in <config>/schedule.json. A background task wakes up every
minute and runs what is due. Times are the server's local time (set `TZ` on the container to change them).
Only the backups made by the schedule are ever removed to keep the last few: manual ones are left alone.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .arr import ArrClient
from .fullbackup import FullBackups
from .porter import PorterError
from .store import InstanceStore

log = logging.getLogger("uvicorn.error")
DEFAULTS: dict[str, Any] = {"enabled": False, "everyDays": 1, "time": "03:00", "keep": 7, "deleteRemote": False, "instances": []}
TIME = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")


def _slot(now: datetime, hhmm: str) -> datetime:
    """The most recent moment at `hhmm` that is not in the future."""
    h, m = (int(x) for x in hhmm.split(":"))
    slot = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return slot if slot <= now else slot - timedelta(days=1)


class BackupSchedule:
    def __init__(self, path: Path, store: InstanceStore, backups: FullBackups, make_client: Callable[[dict[str, Any]], ArrClient]):
        self.path, self.store, self.backups, self.make_client = path, store, backups, make_client
        self._run = asyncio.Lock()

    # -- what is saved

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            data = {}
        return {"config": {**DEFAULTS, **(data.get("config") or {})}, "lastRun": data.get("lastRun"), "results": data.get("results") or {}}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), "utf-8")
        os.replace(tmp, self.path)

    def status(self, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now().astimezone()
        data = self._read()
        known = {i["id"] for i in self.store.list()}
        data["config"]["instances"] = [i for i in data["config"]["instances"] if i in known]  # an instance deleted since
        data["results"] = {k: v for k, v in data["results"].items() if k in known}
        data["nextRun"] = self._next(data, now)
        data["timezone"] = now.tzname()
        return data

    def save(self, config: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now().astimezone()
        known = {i["id"] for i in self.store.list()}
        clean: dict[str, Any] = {
            "enabled": bool(config.get("enabled")), "everyDays": config.get("everyDays"), "time": str(config.get("time", "")),
            "keep": config.get("keep"), "deleteRemote": bool(config.get("deleteRemote")),
            "instances": [i for i in dict.fromkeys(config.get("instances") or []) if i in known],
        }
        if not isinstance(clean["everyDays"], int) or isinstance(clean["everyDays"], bool) or not 1 <= clean["everyDays"] <= 365:
            raise PorterError("Back up every 1 to 365 days")
        if not TIME.fullmatch(clean["time"]):
            raise PorterError("The time must look like 03:00")
        if not isinstance(clean["keep"], int) or isinstance(clean["keep"], bool) or not 1 <= clean["keep"] <= 365:
            raise PorterError("Keep between 1 and 365 backups of each instance")
        if clean["enabled"] and not clean["instances"]:
            raise PorterError("Choose at least one instance to back up")
        data = self._read()
        if clean["enabled"] and not data["config"]["enabled"]:
            data["lastRun"] = _slot(now, clean["time"]).isoformat()  # switching it on does not back up at once: the next slot does
        data["config"] = clean
        self._write(data)
        return self.status(now)

    # -- when

    @staticmethod
    def _next(data: dict[str, Any], now: datetime) -> str | None:
        cfg = data["config"]
        if not cfg["enabled"] or not data["lastRun"]:
            return None
        last = datetime.fromisoformat(data["lastRun"])
        h, m = (int(x) for x in cfg["time"].split(":"))
        return (last + timedelta(days=cfg["everyDays"])).replace(hour=h, minute=m, second=0, microsecond=0).isoformat()

    def due(self, now: datetime) -> bool:
        data = self._read()
        nxt = self._next(data, now)
        return nxt is not None and datetime.fromisoformat(nxt) <= now

    # -- doing it

    async def tick(self, now: datetime | None = None) -> bool:
        """Runs the backups if they are due. Returns whether it did."""
        now = now or datetime.now().astimezone()
        if self._run.locked() or not self.due(now):
            return False
        async with self._run:
            data = self._read()
            cfg, results = data["config"], data["results"]
            for iid in cfg["instances"]:
                inst = self.store.get(iid)
                if inst is None:
                    continue
                try:
                    async with self.make_client(inst) as client:
                        meta = await self.backups.create(client, inst["name"], reason="scheduled", instance_id=iid,
                                                         delete_remote=cfg["deleteRemote"])
                    self.backups.prune(iid, inst["name"], cfg["keep"])
                    results[iid] = {"at": now.isoformat(timespec="seconds"), "ok": True, "backup": meta["id"], "error": None}
                except Exception as e:  # one unreachable instance must not stop the others
                    log.warning("Scheduled backup of %s failed: %s", inst["name"], e)
                    results[iid] = {"at": now.isoformat(timespec="seconds"), "ok": False, "backup": None, "error": str(e)}
            data["lastRun"] = _slot(now, cfg["time"]).isoformat()
            data["results"] = results
            self._write(data)
        return True

    async def loop(self, interval: float = 60.0) -> None:
        while True:
            await asyncio.sleep(interval)
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("The backup schedule failed")

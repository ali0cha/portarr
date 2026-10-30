"""Full backups of an instance, and full restores.

A full backup is made of two things taken at the same moment:
  * the application's own backup (a zip with its database and settings), which the application creates, so
    that everything is in it: API key, indexer passwords, history. Portarr only triggers it and downloads it;
  * Portarr's JSON export of every configuration section, which can be imported selectively later.

Each backup is a folder of `backup.zip`, `config.json` and `meta.json` under <config>/backups/full/. Restoring
sends the zip back to the application, which replaces its whole database and restarts. Before it does, the
target is backed up the same way, so a restore can be undone with another restore.
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .arr import ArrClient, ArrError
from .porter import PorterError, export_bundle
from .updates import is_newer

ID = re.compile(r"[A-Za-z0-9._-]+")
DONE = {"completed"}
FAILED = {"failed", "aborted", "cancelled", "orphaned"}


class FullBackups:
    def __init__(self, root: Path, poll: float = 1.0, command_timeout: float = 300.0,
                 down_wait: float = 20.0, up_wait: float = 180.0):
        self.root = root
        # how long to wait for the application: its backup command, then for its restart after a restore
        self.poll, self.command_timeout, self.down_wait, self.up_wait = poll, command_timeout, down_wait, up_wait

    # -- the stored backups

    def folder(self, backup_id: str) -> Path:
        if not ID.fullmatch(backup_id) or backup_id in (".", ".."):
            raise PorterError("Unknown backup")
        return self.root / backup_id

    def meta(self, backup_id: str) -> dict[str, Any]:
        try:
            return json.loads((self.folder(backup_id) / "meta.json").read_text("utf-8"))
        except (OSError, ValueError) as e:
            raise PorterError("Unknown backup") from e

    def file(self, backup_id: str, name: str) -> Path:
        path = self.folder(backup_id) / name
        if not path.is_file():
            raise PorterError("Unknown backup")
        return path

    def list(self) -> list[dict[str, Any]]:
        out = []
        for d in self.root.iterdir() if self.root.is_dir() else []:
            try:
                out.append(self.meta(d.name))
            except PorterError:
                continue  # a folder that is not a finished backup (interrupted, or not ours)
        return sorted(out, key=lambda m: m.get("createdAt", ""), reverse=True)

    def delete(self, backup_id: str) -> None:
        self.meta(backup_id)  # only ever removes something that is one of ours
        shutil.rmtree(self.folder(backup_id))

    # -- making one

    async def create(self, client: ArrClient, instance: str, reason: str = "manual") -> dict[str, Any]:
        status = await client.status()
        now = datetime.now(UTC)
        slug = re.sub(r"[^A-Za-z0-9._-]+", "_", instance)
        backup_id = f"{slug}-{now.strftime('%Y%m%d-%H%M%S')}"
        folder = self.folder(backup_id)
        if folder.exists():  # two backups of the same instance within one second
            backup_id += f"-{int(time.time() * 1000) % 1000:03d}"
            folder = self.folder(backup_id)
        try:
            folder.mkdir(parents=True)
        except OSError as e:
            raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
        try:
            remote = await self._backup_on_instance(client)
            zip_path = folder / "backup.zip"
            size = await client.download(remote["path"], zip_path)
            with zip_path.open("rb") as f:
                is_zip = f.read(2) == b"PK"
            if not is_zip:
                raise PorterError("The application did not return a backup file: check the URL base and the API key")
            bundle = await export_bundle(client, instance)
            (folder / "config.json").write_text(json.dumps(bundle, indent=2), "utf-8")
            meta = {"id": backup_id, "instance": instance, "app": status["app"], "version": status["version"],
                    "createdAt": now.isoformat(timespec="seconds"), "reason": reason, "size": size,
                    "configSize": (folder / "config.json").stat().st_size, "remoteName": remote.get("name")}
            (folder / "meta.json").write_text(json.dumps(meta, indent=2), "utf-8")  # last: its presence means "finished"
        except BaseException as e:
            shutil.rmtree(folder, ignore_errors=True)
            if isinstance(e, OSError):
                raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
            raise
        return meta

    async def _backup_on_instance(self, client: ArrClient) -> dict[str, Any]:
        """Asks the application to back itself up, waits for it, and returns the new backup it reports."""
        before = {b.get("name") for b in await client.get("system/backup") or []}
        command = await client.post("command", {"name": "Backup"})
        deadline = time.monotonic() + self.command_timeout
        while True:
            state = await client.get(f"command/{command['id']}")
            if state.get("status") in DONE:
                break
            if state.get("status") in FAILED:
                raise PorterError(f"The application could not make its backup: {state.get('message') or state.get('exception') or state['status']}")
            if time.monotonic() > deadline:
                raise PorterError("The application is still making its backup after several minutes: check it, nothing was saved")
            await asyncio.sleep(self.poll)
        backups = await client.get("system/backup") or []
        fresh = [b for b in backups if b.get("name") not in before] or [b for b in backups if b.get("type") == "manual"]
        if not fresh:
            raise PorterError("The application reports no backup after making one")
        return max(fresh, key=lambda b: b.get("time") or "")

    # -- restoring one

    async def restore(self, client: ArrClient, instance: str, backup_id: str) -> dict[str, Any]:
        meta = self.meta(backup_id)
        zip_path = self.file(backup_id, "backup.zip")
        status = await client.status()
        if status["app"] != meta["app"]:
            raise PorterError(f"This backup comes from {meta['app'].capitalize()}: it cannot be restored on {status['app'].capitalize()}")
        if meta.get("version") and status.get("version") and is_newer(str(meta["version"]), str(status["version"])):
            raise PorterError(f"This backup was made by version {meta['version']}, newer than the target's {status['version']}: "
                              "update the application first, nothing was changed")
        safety = await self.create(client, instance, reason="before-restore")  # raises, and nothing is touched, if it fails
        await client.upload("system/backup/restore/upload", zip_path)
        state = await self._wait_for_restart(client)
        return {"safety": safety["id"], "restored": meta["id"], **state}

    async def _wait_for_restart(self, client: ArrClient) -> dict[str, Any]:
        """The application restarts itself after a restore: wait for it to go down, then to come back."""
        went_down = False
        deadline = time.monotonic() + self.down_wait
        while time.monotonic() < deadline and not went_down:
            try:
                await client.get("system/status")
            except ArrError:
                went_down = True
                break
            await asyncio.sleep(self.poll)
        if not went_down:
            return {"restarted": False, "apiKeyChanged": False}
        deadline = time.monotonic() + self.up_wait
        while time.monotonic() < deadline:
            try:
                await client.get("system/status")
                return {"restarted": True, "apiKeyChanged": False}
            except ArrError as e:
                if e.status == 401:  # it is back, with the API key of the restored backup
                    return {"restarted": True, "apiKeyChanged": True}
            await asyncio.sleep(self.poll)
        return {"restarted": False, "apiKeyChanged": False}

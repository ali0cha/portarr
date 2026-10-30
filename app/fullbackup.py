"""Full backups of an instance, and full restores.

A full backup is made of two things taken at the same moment:
  * the application's own backup (a zip with its database and settings), which the application creates, so
    that everything is in it: API key, indexer passwords, history. Portarr only triggers it and downloads it;
  * Portarr's JSON export of every configuration section, which can be imported selectively later.

Each backup is a folder of `backup.zip`, `config.json` and `meta.json` under <config>/backups/full/. Restoring
sends the zip back to the application, which replaces its whole database and restarts. Before it does, the
target is backed up the same way, so a restore can be undone with another restore.

A zip made elsewhere (the application's own scheduled backups, or a file from another machine) can be brought in
too. It has no JSON export, since there is no way to read one out of it, so only a full restore is offered for it.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import time
import zipfile
from collections.abc import AsyncIterator
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .arr import API_VERSIONS, ArrClient, ArrError
from .porter import PorterError, export_bundle
from .updates import is_newer

log = logging.getLogger("uvicorn.error")
ID = re.compile(r"[A-Za-z0-9._-]+")
NAMED_VERSION = re.compile(r"^(?P<app>[a-z]+)_backup_v(?P<version>\d+(?:\.\d+){1,3})_", re.I)  # radarr_backup_v5.14.0.9383_2026.10.30_09.00.00.zip
DONE = {"completed"}
FAILED = {"failed", "aborted", "cancelled", "orphaned"}
MAX_UPLOAD = 2 * 1024**3  # a database with years of history is a few hundred MB: this only stops a runaway


def inspect_zip(path: Path) -> str:
    """The application a backup zip belongs to, read from its contents (every one holds `<app>.db`)."""
    try:
        with zipfile.ZipFile(path) as z:
            names = {n.lower() for n in z.namelist()}
    except (zipfile.BadZipFile, OSError) as e:
        raise PorterError("This file is not a backup zip") from e
    found = [app for app in API_VERSIONS if f"{app}.db" in names]
    if len(found) != 1:
        raise PorterError("This zip is not a Radarr, Sonarr, Lidarr, Whisparr or Prowlarr backup")
    return found[0]


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

    def prune(self, instance_id: str, instance: str, keep: int) -> list[str]:
        """Deletes the oldest *scheduled* backups of an instance beyond `keep`. Manual ones, the ones made
        before a restore and the imported ones are never removed automatically."""
        mine = [m for m in self.list() if m.get("reason") == "scheduled"
                and (m["instanceId"] == instance_id if m.get("instanceId") else m.get("instance") == instance)]
        gone = [m["id"] for m in mine[max(keep, 1):]]  # the list is newest first
        for backup_id in gone:
            self.delete(backup_id)
        return gone

    def _allocate(self, instance: str, suffix: str = "") -> tuple[str, Path, datetime]:
        now = datetime.now(UTC)
        slug = re.sub(r"[^A-Za-z0-9._-]+", "_", instance)
        backup_id = f"{slug}-{now.strftime('%Y%m%d-%H%M%S')}{suffix}"
        if self.folder(backup_id).exists():  # two backups of the same instance within one second
            backup_id += f"-{int(time.time() * 1000) % 1000:03d}"
        folder = self.folder(backup_id)
        try:
            folder.mkdir(parents=True)
        except OSError as e:
            raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
        return backup_id, folder, now

    # -- making one

    async def create(self, client: ArrClient, instance: str, reason: str = "manual", instance_id: str | None = None,
                     delete_remote: bool = False) -> dict[str, Any]:
        status = await client.status()
        backup_id, folder, now = self._allocate(instance)
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
                    "createdAt": now.isoformat(timespec="milliseconds"), "reason": reason, "size": size, "config": True,
                    "configSize": (folder / "config.json").stat().st_size, "remoteName": remote.get("name")}
            if instance_id:
                meta["instanceId"] = instance_id
            (folder / "meta.json").write_text(json.dumps(meta, indent=2), "utf-8")  # last: its presence means "finished"
        except BaseException as e:
            shutil.rmtree(folder, ignore_errors=True)
            if isinstance(e, OSError):
                raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
            raise
        if delete_remote and remote.get("id") is not None:
            try:  # the copy Portarr asked for and now holds: it only piles up on the application otherwise
                await client.request("DELETE", f"system/backup/{remote['id']}")
            except ArrError as e:
                log.warning("Backup %s is saved, but its copy on %s could not be removed: %s", backup_id, instance, e)
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

    # -- bringing one in

    async def on_instance(self, client: ArrClient) -> list[dict[str, Any]]:
        """The backups the application itself holds (its scheduled ones, and the ones made by hand), newest first."""
        await client.status()
        backups = await client.get("system/backup") or []
        return sorted(({k: b.get(k) for k in ("id", "name", "type", "size", "time")} for b in backups), key=lambda b: b["time"] or "", reverse=True)

    async def keep_from_instance(self, client: ArrClient, instance: str, remote_id: int, instance_id: str | None = None) -> dict[str, Any]:
        """Downloads one of the application's own backups into Portarr, so it can be restored from here."""
        status = await client.status()
        remote = next((b for b in await client.get("system/backup") or [] if b.get("id") == remote_id), None)
        if remote is None:
            raise PorterError("The application no longer has that backup")
        backup_id, folder, now = self._allocate(instance, "-imported")
        try:
            zip_path = folder / "backup.zip"
            size = await client.download(remote["path"], zip_path)
            if inspect_zip(zip_path) != status["app"]:
                raise PorterError(f"That backup is not a {status['app'].capitalize()} backup")
            named = NAMED_VERSION.match(remote.get("name") or "")
            meta = {"id": backup_id, "instance": instance, "app": status["app"], "version": named["version"] if named else None,
                    "createdAt": remote.get("time") or now.isoformat(timespec="milliseconds"), "reason": "imported", "size": size,
                    "config": False, "remoteName": remote.get("name")}
            if instance_id:
                meta["instanceId"] = instance_id
            (folder / "meta.json").write_text(json.dumps(meta, indent=2), "utf-8")
        except BaseException as e:
            shutil.rmtree(folder, ignore_errors=True)
            if isinstance(e, OSError):
                raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
            raise
        return meta

    async def add_zip(self, filename: str, chunks: AsyncIterator[bytes]) -> dict[str, Any]:
        """Keeps a backup zip that comes from elsewhere. The application is read from the zip itself."""
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).stem)[:60].strip("._-") or "uploaded"
        backup_id, folder, now = self._allocate(stem, "-uploaded")
        try:
            zip_path = folder / "backup.zip"
            size = 0
            with zip_path.open("wb") as out:
                async for chunk in chunks:
                    size += len(chunk)
                    if size > MAX_UPLOAD:
                        raise PorterError("This file is too large to be a backup")
                    out.write(chunk)
            app = inspect_zip(zip_path)
            named = NAMED_VERSION.match(Path(filename).name)
            meta = {"id": backup_id, "instance": stem, "app": app, "version": named["version"] if named else None,
                    "createdAt": now.isoformat(timespec="milliseconds"), "reason": "uploaded", "size": size, "config": False,
                    "remoteName": Path(filename).name}
            (folder / "meta.json").write_text(json.dumps(meta, indent=2), "utf-8")
        except BaseException as e:
            shutil.rmtree(folder, ignore_errors=True)
            if isinstance(e, OSError):
                raise PorterError(f"Cannot write the backup, nothing was done: {e.strerror or e}") from e
            raise
        return meta

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

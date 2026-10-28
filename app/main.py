"""Portarr: export / import Sonarr & Radarr profiles, custom formats and quality settings."""
from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__
from .arr import ArrClient, ArrError
from .porter import Importer, PorterError, export_bundle, parse_bundle
from .trash import DEFAULT_URL, TrashCatalog, build_bundle, default_selection, is_trash_profile, list_profiles, profile_detail, profile_from_catalog
from .store import InstanceStore, public

mimetypes.add_type("font/woff2", ".woff2")  # not in every base image

COMMIT = os.environ.get("PORTARR_COMMIT", "")[:7]  # baked into the Docker image by the build
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
AUTH_USER = os.environ.get("AUTH_USER", "")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "")

store = InstanceStore(CONFIG_DIR / "instances.json")
catalog = TrashCatalog(CONFIG_DIR / "cache" / "trash-guides.json", os.environ.get("TRASH_GUIDES_URL", DEFAULT_URL))
backup_dir = CONFIG_DIR / "backups"

app = FastAPI(title="Portarr", docs_url=None, redoc_url=None, openapi_url=None)
log = logging.getLogger("uvicorn.error")
app.add_middleware(GZipMiddleware, minimum_size=1024)  # app.js is 51 KB, exports and previews can be large


def config_writable() -> bool:
    path = CONFIG_DIR
    while not path.exists() and path != path.parent:
        path = path.parent
    return os.access(path, os.W_OK)


if not config_writable():
    log.warning("%s is not writable by uid %s: instances cannot be saved. Give that folder to the user running "
                "Portarr (568 on TrueNAS: chown -R 568:568 <folder>).", CONFIG_DIR, os.getuid())


# --------------------------------------------------------------------------- auth (optional)


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if AUTH_USER and AUTH_PASSWORD and request.url.path != "/healthz":
        ok = False
        header = request.headers.get("authorization", "")
        if header.lower().startswith("basic "):
            try:
                user, _, password = base64.b64decode(header[6:]).decode("utf-8").partition(":")
                ok = secrets.compare_digest(user, AUTH_USER) & secrets.compare_digest(password, AUTH_PASSWORD)
            except ValueError:
                ok = False
        if not ok:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Portarr"'})
    return await call_next(request)


@app.exception_handler(ArrError)
async def arr_error(_: Request, e: ArrError):
    return JSONResponse({"detail": str(e)}, status_code=502)


@app.exception_handler(OSError)
async def file_error(_: Request, e: OSError):
    log.error("File error: %s", e)
    return JSONResponse(
        {"detail": f"Cannot write to {CONFIG_DIR}: {e.strerror or e}. The folder must be writable by the user "
                   f"running Portarr (uid {os.getuid()}); on TrueNAS give it to user 568."},
        status_code=500)


@app.exception_handler(PorterError)
async def porter_error(_: Request, e: PorterError):
    return JSONResponse({"detail": str(e)}, status_code=400)


# --------------------------------------------------------------------------- models


class InstanceIn(BaseModel):
    name: str
    url: str
    api_key: str = ""  # empty on update = keep the stored key
    verify_ssl: bool = True


class ImportIn(BaseModel):
    bundle: dict[str, Any]
    selection: dict[str, list[str]] | None = None
    overwrite: bool = False


class ParseIn(BaseModel):
    text: str
    app: str | None = None  # the target's application: a TRaSH profile needs it to resolve its formats


class TrashBuildIn(BaseModel):
    profile_id: str
    formats: list[str] | None = None  # trash_ids of the optional formats to include; None = the guides' defaults


# --------------------------------------------------------------------------- helpers


def _client(inst: dict[str, Any]) -> ArrClient:
    return ArrClient(inst["url"], inst["api_key"], inst.get("verify_ssl", True), inst.get("app"))


def _get(iid: str) -> dict[str, Any]:
    inst = store.get(iid)
    if inst is None:
        raise HTTPException(404, "Unknown instance")
    return inst


def _clean(body: InstanceIn) -> dict[str, Any]:
    url = body.url.strip().rstrip("/")
    if not re.match(r"^https?://", url):
        raise HTTPException(400, "URL must start with http:// or https://")
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    return {"name": body.name.strip(), "url": url, "verify_ssl": body.verify_ssl}


async def _detect(url: str, api_key: str, verify: bool) -> dict[str, Any]:
    async with ArrClient(url, api_key, verify) as c:  # app unknown yet: auto-detected
        return await c.status()


# --------------------------------------------------------------------------- routes


@app.get("/healthz")
async def healthz():
    return {"ok": True, "config_writable": config_writable()}


@app.get("/api/version")
async def version():
    return {"version": __version__, "commit": COMMIT or None}


@app.get("/api/instances")
async def list_instances():
    return [public(i) for i in store.list()]


@app.post("/api/instances")
async def add_instance(body: InstanceIn):
    data = _clean(body)
    if not body.api_key.strip():
        raise HTTPException(400, "API key is required")
    data["api_key"] = body.api_key.strip()
    status = await _detect(data["url"], data["api_key"], data["verify_ssl"])
    return public(store.add({**data, "app": status["app"]}))


@app.put("/api/instances/{iid}")
async def update_instance(iid: str, body: InstanceIn):
    cur = _get(iid)
    data = _clean(body)
    data["api_key"] = body.api_key.strip() or cur["api_key"]
    status = await _detect(data["url"], data["api_key"], data["verify_ssl"])
    return public(store.update(iid, {**data, "app": status["app"]}))


@app.delete("/api/instances/{iid}")
async def delete_instance(iid: str):
    if not store.delete(iid):
        raise HTTPException(404, "Unknown instance")
    return {"ok": True}


@app.post("/api/instances/{iid}/test")
async def test_instance(iid: str):
    inst = _get(iid)
    return await _detect(inst["url"], inst["api_key"], inst.get("verify_ssl", True))


@app.get("/api/instances/{iid}/export")
async def export_instance(iid: str):
    inst = _get(iid)
    async with _client(inst) as c:
        return await export_bundle(c, inst["name"])


@app.post("/api/import/parse")
async def parse_import(body: ParseIn):
    try:
        data = json.loads(body.text)
    except ValueError as e:
        raise PorterError(f"Invalid JSON: {e}") from e
    if is_trash_profile(data):
        if body.app not in ("radarr", "sonarr"):
            raise PorterError("A TRaSH profile applies to Radarr or Sonarr: choose a target instance of one of them first")
        return build_bundle(await catalog.load(), body.app, data)
    return parse_bundle(data)


@app.get("/api/trash/{app_name}/profiles")
async def trash_profiles(app_name: str):
    files = await catalog.load()
    return {"profiles": list_profiles(files, app_name), "fetchedAt": catalog.fetched_at}


@app.get("/api/trash/{app_name}/profiles/{profile_id}")
async def trash_profile(app_name: str, profile_id: str):
    files = await catalog.load()
    detail = profile_detail(files, app_name, profile_from_catalog(files, app_name, profile_id))
    detail["defaults"] = sorted(default_selection(detail))
    return detail


@app.post("/api/trash/{app_name}/build")
async def trash_build(app_name: str, body: TrashBuildIn):
    files = await catalog.load()
    selected = None if body.formats is None else set(body.formats)
    return build_bundle(files, app_name, profile_from_catalog(files, app_name, body.profile_id), selected)


@app.post("/api/trash/refresh")
async def trash_refresh():
    files = await catalog.load(force=True)
    return {"files": len(files), "fetchedAt": catalog.fetched_at}


async def _run_import(iid: str, body: ImportIn, apply: bool) -> dict[str, Any]:
    inst = _get(iid)
    backup_name = None
    async with _client(inst) as c:
        if apply:
            # Safety net: snapshot the target before touching it. Abort if it cannot be written.
            snapshot = await export_bundle(c, inst["name"])
            slug = re.sub(r"[^A-Za-z0-9._-]+", "_", inst["name"])
            backup_name = f"{slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            try:
                backup_dir.mkdir(parents=True, exist_ok=True)
                (backup_dir / backup_name).write_text(json.dumps(snapshot, indent=2), "utf-8")
            except OSError as e:
                raise HTTPException(500, f"Cannot write backup, nothing was changed: {e}") from e
        result = await Importer(c, body.bundle, body.selection, body.overwrite, apply).run()
    if backup_name:
        result["backup"] = backup_name
    return result


@app.post("/api/instances/{iid}/import/preview")
async def import_preview(iid: str, body: ImportIn):
    return await _run_import(iid, body, apply=False)


@app.post("/api/instances/{iid}/import/apply")
async def import_apply(iid: str, body: ImportIn):
    return await _run_import(iid, body, apply=True)


@app.get("/api/backups")
async def list_backups():
    if not backup_dir.is_dir():
        return []
    files = sorted(backup_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"name": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime} for f in files]


@app.get("/api/backups/{name}")
async def get_backup(name: str):
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.json", name):
        raise HTTPException(404, "Unknown backup")
    path = backup_dir / name
    if not path.is_file():
        raise HTTPException(404, "Unknown backup")
    return FileResponse(path, media_type="application/json", filename=name)


class Assets(StaticFiles):
    """The interface files. Without a Cache-Control header browsers keep stale copies for hours, so after an
    update the old interface keeps running: revalidate every time (a 304 when nothing changed). Fonts never
    change, so they may be cached."""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code in (200, 304):
            response.headers["Cache-Control"] = "public, max-age=604800" if path.startswith("fonts/") else "no-cache"
        return response


app.mount("/", Assets(directory=Path(__file__).parent / "static", html=True), name="static")

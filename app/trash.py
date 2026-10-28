"""TRaSH Guides: turn the guides' quality profiles into Portarr bundles.

A TRaSH profile file only holds *references*: its mandatory custom formats are listed by name and
trash_id, and the scores live in each custom format's own file, keyed by the profile's "score set".
Optional formats come from "cf-groups". So the guides' JSON is downloaded once as a single archive,
indexed, and cached; everything else is a pure function of that data.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from .porter import FORMAT, SCORE_KEYS, VERSION, PorterError, normalize_cf

DEFAULT_URL = "https://codeload.github.com/TRaSH-Guides/Guides/tar.gz/refs/heads/master"
APPS = ("radarr", "sonarr")  # the only applications the guides cover
TTL = 12 * 3600
MAX_MEMBER = 2_000_000
_MEMBER = re.compile(r"^[^/]+/docs/json/((?:radarr|sonarr)/.+\.json)$")
log = logging.getLogger("uvicorn.error")


# --------------------------------------------------------------------------- download and cache


def extract_files(fileobj: BinaryIO) -> dict[str, Any]:
    """The radarr / sonarr JSON files of the guides' archive, parsed, keyed by path below docs/json/."""
    files: dict[str, Any] = {}
    with tarfile.open(fileobj=fileobj, mode="r|gz") as tar:
        for member in tar:
            m = _MEMBER.match(member.name)
            if not m or not member.isfile() or member.size > MAX_MEMBER:
                continue
            try:
                files[m.group(1)] = json.load(tar.extractfile(member))  # type: ignore[arg-type]
            except ValueError:
                continue  # a malformed file must not take the whole catalog down
    return files


class TrashCatalog:
    def __init__(self, cache_path: Path | None = None, url: str = DEFAULT_URL,
                 transport: httpx.AsyncBaseTransport | None = None, ttl: float = TTL):
        self.cache_path, self.url, self.transport, self.ttl = cache_path, url, transport, ttl
        self.files: dict[str, Any] | None = None
        self.fetched_at = 0.0
        self._lock = asyncio.Lock()

    async def load(self, force: bool = False) -> dict[str, Any]:
        async with self._lock:
            if self.files is None:
                self._read_cache()
            if self.files is not None and not force and time.time() - self.fetched_at < self.ttl:
                return self.files
            try:
                files = await self._download()
            except (httpx.HTTPError, tarfile.TarError, OSError, EOFError) as e:
                if self.files is not None:  # an outdated catalog beats none (offline NAS)
                    log.warning("TRaSH Guides refresh failed, using the cached copy: %s", e)
                    return self.files
                raise PorterError(
                    f"Cannot download the TRaSH Guides ({e.__class__.__name__}: {e}). "
                    "Portarr needs Internet access for this; pasted custom formats still work offline.") from e
            if not files:
                raise PorterError("The TRaSH Guides archive did not contain the expected files")
            self.files, self.fetched_at = files, time.time()
            self._write_cache()
            return files

    async def _download(self) -> dict[str, Any]:
        timeout = httpx.Timeout(120, connect=15)
        async with httpx.AsyncClient(transport=self.transport, timeout=timeout, follow_redirects=True) as client:
            with tempfile.TemporaryFile() as tmp:
                async with client.stream("GET", self.url) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes():
                        tmp.write(chunk)
                tmp.seek(0)
                return await asyncio.to_thread(extract_files, tmp)

    def _read_cache(self) -> None:
        if not self.cache_path:
            return
        try:
            data = json.loads(self.cache_path.read_text("utf-8"))
            self.files, self.fetched_at = data["files"], float(data["fetchedAt"])
        except (OSError, ValueError, KeyError):
            self.files = None

    def _write_cache(self) -> None:
        if not self.cache_path:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"fetchedAt": self.fetched_at, "files": self.files}), "utf-8")
            tmp.replace(self.cache_path)
        except OSError as e:  # the cache is an optimisation, never a requirement
            log.warning("Cannot write the TRaSH Guides cache: %s", e)


# --------------------------------------------------------------------------- reading the guides


def _dir(files: dict[str, Any], app: str, sub: str) -> list[Any]:
    prefix = f"{app}/{sub}/"
    return [v for p, v in sorted(files.items()) if p.startswith(prefix) and isinstance(v, dict)]


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _check_app(app: str) -> None:
    if app not in APPS:
        raise PorterError("The TRaSH Guides only cover Radarr and Sonarr")


def is_trash_profile(data: Any) -> bool:
    return (isinstance(data, dict) and "trash_id" in data and isinstance(data.get("items"), list)
            and "cutoff" in data and "specifications" not in data)


def list_profiles(files: dict[str, Any], app: str) -> list[dict[str, Any]]:
    _check_app(app)
    categories: dict[str, str] = {}
    order: list[str] = []
    for group in files.get(f"{app}/quality-profile-groups/groups.json") or []:
        order.append(group["name"])
        for trash_id in group.get("profiles", {}).values():
            categories[trash_id] = group["name"]
    out = []
    for p in _dir(files, app, "quality-profiles"):
        category = categories.get(p["trash_id"], "Other")
        if not is_trash_profile(p) or p.get("visible") is False or category.lower() == "test":
            continue
        out.append({"id": p["trash_id"], "name": p["name"], "category": category,
                    "description": _clean(p.get("trash_description")), "url": p.get("trash_url")})
    rank = {name: i for i, name in enumerate(order)}
    return sorted(out, key=lambda x: (rank.get(x["category"], len(rank)), x["name"].lower()))


def _find_profile(files: dict[str, Any], app: str, profile_id: str) -> dict[str, Any]:
    _check_app(app)
    for p in _dir(files, app, "quality-profiles"):
        if p.get("trash_id") == profile_id:
            return p
    raise PorterError("Unknown TRaSH profile")


def _score(cf: dict[str, Any], score_set: str) -> int:
    scores = cf.get("trash_scores") or {}
    return int(scores.get(score_set, scores.get("default", 0)) or 0)


def profile_detail(files: dict[str, Any], app: str, profile: dict[str, Any]) -> dict[str, Any]:
    """What a profile consists of: its mandatory formats and the optional groups that apply to it."""
    cfs = {c["trash_id"]: c for c in _dir(files, app, "cf") if "trash_id" in c}
    score_set = profile.get("trash_score_set") or "default"
    required, missing = [], []
    for name, trash_id in (profile.get("formatItems") or {}).items():
        if trash_id in cfs:
            required.append({"trash_id": trash_id, "name": cfs[trash_id]["name"], "score": _score(cfs[trash_id], score_set)})
        else:
            missing.append(name)
    groups = []
    for g in _dir(files, app, "cf-groups"):
        if profile.get("trash_id") not in ((g.get("quality_profiles") or {}).get("include") or {}).values():
            continue
        formats = []
        for e in g.get("custom_formats", []):
            if e["trash_id"] not in cfs:
                missing.append(e.get("name", e["trash_id"]))
                continue
            formats.append({"trash_id": e["trash_id"], "name": cfs[e["trash_id"]]["name"], "required": bool(e.get("required")),
                            "default": bool(e.get("default")), "score": _score(cfs[e["trash_id"]], score_set)})
        groups.append({"trash_id": g["trash_id"], "name": g["name"], "description": _clean(g.get("trash_description")),
                       "default": bool(g.get("default")), "formats": formats})
    return {"profile": {"id": profile.get("trash_id"), "name": profile["name"], "description": _clean(profile.get("trash_description"))},
            "scoreSet": score_set, "required": required, "groups": groups, "missing": sorted(set(missing))}


def default_selection(detail: dict[str, Any]) -> set[str]:
    """What the guides recommend: the mandatory formats, plus the required / default formats of default groups."""
    chosen = {r["trash_id"] for r in detail["required"]}
    for g in detail["groups"]:
        if g["default"]:
            chosen |= {f["trash_id"] for f in g["formats"] if f["required"] or f["default"]}
    return chosen


def build_bundle(files: dict[str, Any], app: str, profile: dict[str, Any], selected: set[str] | None = None) -> dict[str, Any]:
    """A Portarr bundle: the profile with its scores, and the definitions of the formats it scores."""
    _check_app(app)
    detail = profile_detail(files, app, profile)
    allowed = {r["trash_id"] for r in detail["required"]} | {f["trash_id"] for g in detail["groups"] for f in g["formats"]}
    chosen = default_selection(detail) if selected is None else (set(selected) & allowed) | {r["trash_id"] for r in detail["required"]}
    cfs = {c["trash_id"]: c for c in _dir(files, app, "cf") if "trash_id" in c}
    score_set = detail["scoreSet"]
    ordered = sorted((cfs[i] for i in chosen), key=lambda c: c["name"].lower())

    prof: dict[str, Any] = {
        "name": profile["name"],
        "upgradeAllowed": bool(profile.get("upgradeAllowed")),
        "cutoff": profile.get("cutoff"),
        # the guides list qualities highest first (as the UI shows them), the API stores them lowest first
        "items": [dict(i) for i in reversed(profile["items"])],
        "unlistedQualities": "first",  # qualities the guide does not mention sit at the bottom, disabled
        "formatItems": [{"name": c["name"], "score": _score(c, score_set)} for c in ordered if _score(c, score_set)],
    }
    for k in SCORE_KEYS:
        if k in profile:
            prof[k] = profile[k]
    if profile.get("language"):
        prof["language"] = profile["language"]
    return {
        "format": FORMAT,
        "version": VERSION,
        "source": {"app": app, "origin": "trash-guides", "profile": profile["name"], "version": None},
        "customFormats": [normalize_cf(c) for c in ordered],
        "qualityProfiles": [prof],
        "warnings": [f"Custom format '{n}' is referenced by the guides but its file was not found" for n in detail["missing"]],
    }


def profile_from_catalog(files: dict[str, Any], app: str, profile_id: str) -> dict[str, Any]:
    return _find_profile(files, app, profile_id)

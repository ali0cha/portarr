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


# --------------------------------------------------------------------------- quality sizes


def _title(slug: str) -> str:
    named = {"movie": "Movies", "series": "Series"}
    return named.get(slug) or " ".join(w.upper() if w in ("sqp", "uhd") else w.capitalize() for w in slug.split("-"))


def is_trash_sizes(data: Any) -> bool:
    return (isinstance(data, dict) and "trash_id" in data and isinstance(data.get("qualities"), list)
            and "items" not in data and "specifications" not in data)


def list_sizes(files: dict[str, Any], app: str) -> list[dict[str, Any]]:
    """The guides' size sets (per quality: minimum, preferred and maximum, in MB per minute of runtime)."""
    _check_app(app)
    sets = [s for s in _dir(files, app, "quality-size") if is_trash_sizes(s)]
    sets.sort(key=lambda s: (s.get("type") not in ("movie", "series"), str(s.get("type"))))
    return [{"id": s["trash_id"], "name": _title(str(s.get("type") or "sizes")), "qualities": len(s["qualities"])} for s in sets]


def find_sizes(files: dict[str, Any], app: str, sizes_id: str) -> dict[str, Any]:
    _check_app(app)
    for s in _dir(files, app, "quality-size"):
        if s.get("trash_id") == sizes_id and is_trash_sizes(s):
            return s
    raise PorterError("Unknown TRaSH quality sizes")


def size_definitions(sizes: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for q in sizes["qualities"]:
        if not isinstance(q, dict) or not q.get("quality"):
            continue
        out.append({"quality": q["quality"], **{k: q[src] for k, src in
                                                (("minSize", "min"), ("preferredSize", "preferred"), ("maxSize", "max")) if q.get(src) is not None}})
    return out


# --------------------------------------------------------------------------- naming

# format setting of each application -> where the guides keep it
SERVERS = {"plex": "Plex", "emby": "Emby", "jellyfin": "Jellyfin"}
IDS = {"imdb": "IMDb", "tmdb": "TMDb", "tvdb": "TVDb"}
SPECIAL = {"default": "Standard", "standard": "Standard", "original": "Original title", "p2p-scene": "P2P / scene"}


def _naming_label(key: str) -> str:
    if key in SPECIAL:
        return SPECIAL[key]
    parts = key.split("-")
    server, ident = SERVERS.get(parts[0]), IDS.get(parts[-1])
    if not server or not ident:
        return key
    extra = {"anime": "anime", "edition-alt": "alternative edition"}.get("-".join(parts[1:-1]))
    return f"{server} · {ident}" + (f" ({extra})" if extra else "")


def _plain_key(key: str) -> str:
    """The folder format that goes with a file format: variants only differ in the file name."""
    return key.replace("-anime", "").replace("-edition-alt", "")


def _naming_file(files: dict[str, Any], app: str) -> dict[str, Any]:
    for n in _dir(files, app, "naming"):
        return n
    raise PorterError("The TRaSH Guides have no naming scheme for this application")


def naming_schemes(files: dict[str, Any], app: str) -> dict[str, dict[str, str]]:
    """Every naming scheme of the guides, as the settings it sets: {scheme id: {setting: format}}."""
    _check_app(app)
    n = _naming_file(files, app)
    out: dict[str, dict[str, str]] = {}
    if app == "radarr":
        folders, names = n.get("folder") or {}, n.get("file") or {}
        for key, fmt in names.items():
            folder = folders.get(_plain_key("default" if key == "standard" else key)) or folders.get("default")
            out["default" if key == "standard" else key] = {"movieFolderFormat": folder, "standardMovieFormat": fmt}
    else:
        series, season, eps = n.get("series") or {}, n.get("season") or {}, n.get("episodes") or {}
        std, daily, anime = (eps.get(k) or {} for k in ("standard", "daily", "anime"))
        for key in series:
            out[key] = {"seriesFolderFormat": series[key], "seasonFolderFormat": season.get("default"),
                        "standardEpisodeFormat": std.get("default"), "dailyEpisodeFormat": daily.get("default"),
                        "animeEpisodeFormat": anime.get("default")}
        for key in ("original", "p2p-scene"):  # not every kind of episode has them: it keeps the standard format there
            if any(key in e for e in (std, daily, anime)):
                out[key] = {**out["default"], "standardEpisodeFormat": std.get(key) or std.get("default"),
                            "dailyEpisodeFormat": daily.get(key) or daily.get("default"),
                            "animeEpisodeFormat": anime.get(key) or anime.get("default")}
    return {k: {s: f for s, f in v.items() if isinstance(f, str) and f} for k, v in out.items()}


def list_naming(files: dict[str, Any], app: str) -> list[dict[str, Any]]:
    schemes = naming_schemes(files, app)
    keys = list(schemes)
    order = sorted(keys, key=lambda k: (k != "default", k in ("original", "p2p-scene"), keys.index(k)))  # standard first, odd ones last
    return [{"id": k, "name": _naming_label(k), "formats": schemes[k]} for k in order]


def find_naming(files: dict[str, Any], app: str, scheme: str) -> dict[str, str]:
    schemes = naming_schemes(files, app)
    if scheme not in schemes:
        raise PorterError("Unknown TRaSH naming scheme")
    return schemes[scheme]


# --------------------------------------------------------------------------- bundles


def build_bundle(files: dict[str, Any], app: str, profile: dict[str, Any] | None = None, selected: set[str] | None = None,
                 sizes: str | None = None, naming: str | None = None) -> dict[str, Any]:
    """A Portarr bundle made of what the guides recommend: a quality profile with its scores and the formats it
    scores, a set of quality sizes, a naming scheme. Each one is optional, but not all three."""
    _check_app(app)
    if profile is None and not sizes and not naming:
        raise PorterError("Choose a TRaSH profile, quality sizes or a naming scheme")
    bundle: dict[str, Any] = {
        "format": FORMAT,
        "version": VERSION,
        "source": {"app": app, "origin": "trash-guides", "profile": profile["name"] if profile else None, "version": None},
        "customFormats": [],
        "qualityProfiles": [],
        "warnings": [],
    }
    if profile is not None:
        _add_profile(bundle, files, app, profile, selected)
    if sizes:
        bundle["qualityDefinitions"] = size_definitions(find_sizes(files, app, sizes))
    if naming:
        bundle["naming"] = find_naming(files, app, naming)
    return bundle


def _add_profile(bundle: dict[str, Any], files: dict[str, Any], app: str, profile: dict[str, Any], selected: set[str] | None) -> None:
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
    bundle["customFormats"] = [normalize_cf(c) for c in ordered]
    bundle["qualityProfiles"] = [prof]
    bundle["warnings"] = [f"Custom format '{n}' is referenced by the guides but its file was not found" for n in detail["missing"]]


def profile_from_catalog(files: dict[str, Any], app: str, profile_id: str) -> dict[str, Any]:
    return _find_profile(files, app, profile_id)

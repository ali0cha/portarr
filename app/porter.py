"""Export / import of Sonarr & Radarr configuration.

Bundles are id-independent: everything is referenced by name (custom formats in
profile scores, qualities in profile items, the cutoff), so a bundle exported from
one instance can be replayed on another one where the numeric ids differ.
"""
from __future__ import annotations

import copy
from datetime import datetime, UTC
from functools import partial
from collections.abc import Awaitable, Callable
from typing import Any

from .arr import ArrClient, ArrError, gather

FORMAT = "portarr"
VERSION = 1

SECTION_ORDER = [
    "customFormats", "qualityDefinitions", "qualityProfiles", "metadataProfiles", "naming", "mediaManagement",  # Radarr / Sonarr / Lidarr / Whisparr
    "appProfiles", "indexerProxies", "indexers",  # Prowlarr
]
CONFIG_PATHS = {"naming": "config/naming", "mediaManagement": "config/mediamanagement"}
# Settings that are specific to the host / filesystem rather than to a quality setup.
CONFIG_SKIP_KEYS = {"id", "recycleBin", "chmodFolder", "chownGroup", "setPermissionsLinux"}
SCORE_KEYS = ("minFormatScore", "cutoffFormatScore", "minUpgradeFormatScore")
RENAME_KEYS = ("renameMovies", "renameEpisodes", "renameTracks")  # the switch that makes the naming formats count
GROUP_ID_START = 1000
# Lidarr metadata profile lists: key -> name of the sub-object holding the type
META_LISTS = (("primaryAlbumTypes", "albumType"), ("secondaryAlbumTypes", "albumType"), ("releaseStatuses", "releaseStatus"))
# Some apps (Whisparr v2) also carry size limits on each quality inside a profile
SIZE_KEYS = ("minSize", "maxSize", "preferredSize")
APP_PROFILE_KEYS = ("enableRss", "enableAutomaticSearch", "enableInteractiveSearch", "minimumSeeders")
PROVIDER_KEYS = ("enable", "priority", "redirect", "appProfile")
SECRET_MASK = "********"  # what the API returns instead of passwords / API keys


class PorterError(Exception):
    pass


async def _maybe(aw: Awaitable[Any]) -> Any:
    """An optional read: None when this version of the application does not have it."""
    try:
        return await aw
    except ArrError:
        return None


async def _none() -> None:
    return None


# --------------------------------------------------------------------------- normalisation


def normalize_spec(s: dict[str, Any]) -> dict[str, Any]:
    fields = s.get("fields") or {}
    if isinstance(fields, list):
        fields = {f["name"]: f.get("value") for f in fields}
    return {
        "name": s["name"],
        "implementation": s["implementation"],
        "negate": bool(s.get("negate", False)),
        "required": bool(s.get("required", False)),
        "fields": dict(fields),
    }


def normalize_cf(cf: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": cf["name"],
        "includeCustomFormatWhenRenaming": bool(cf.get("includeCustomFormatWhenRenaming", False)),
        "specifications": [normalize_spec(s) for s in cf.get("specifications", [])],
    }


def cf_payload(cf: dict[str, Any]) -> dict[str, Any]:
    n = normalize_cf(cf)
    for s in n["specifications"]:
        s["fields"] = [{"name": k, "value": v} for k, v in s["fields"].items()]
    return n


def normalize_profile(p: dict[str, Any], cf_names: dict[int, str] | None = None) -> dict[str, Any]:
    cutoff = p.get("cutoff")
    cutoff_name = None
    items: list[dict[str, Any]] = []
    for it in p.get("items", []):
        if it.get("items"):
            items.append(
                {"name": it["name"], "allowed": bool(it["allowed"]), "items": [c["quality"]["name"] for c in it["items"]]}
            )
            if it.get("id") == cutoff:
                cutoff_name = it["name"]
        else:
            q = it["quality"]
            items.append({"name": q["name"], "allowed": bool(it["allowed"]),
                          **{k: it[k] for k in SIZE_KEYS if it.get(k) is not None}})
            if q.get("id") == cutoff:
                cutoff_name = q["name"]
    out: dict[str, Any] = {
        "name": p["name"],
        "upgradeAllowed": bool(p.get("upgradeAllowed")),
        "cutoff": cutoff_name,
        "items": items,
    }
    for k in SCORE_KEYS:
        if k in p:
            out[k] = p[k]
    lang = p.get("language")
    if isinstance(lang, dict) and lang.get("name"):
        out["language"] = lang["name"]
    scores = []
    for fi in p.get("formatItems", []):
        name = fi.get("name") or (cf_names or {}).get(fi.get("format"))
        if name and fi.get("score"):
            scores.append({"name": name, "score": fi["score"]})
    out["formatItems"] = sorted(scores, key=lambda x: x["name"].lower())
    return out


def normalize_metadata_profile(p: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": p["name"]}
    for key, sub in META_LISTS:
        out[key] = sorted(i[sub]["name"] for i in p.get(key, []) if i.get("allowed"))
    return out


def normalize_definition(d: dict[str, Any]) -> dict[str, Any]:
    out = {"quality": d["quality"]["name"], "title": d.get("title")}
    for k in ("minSize", "maxSize", "preferredSize"):
        if k in d:
            out[k] = d[k]
    return out


def normalize_config(c: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in c.items() if k not in CONFIG_SKIP_KEYS}


def _is_secret(field: dict[str, Any]) -> bool:
    return field.get("privacy") not in (None, "normal") or field.get("value") == SECRET_MASK


def normalize_provider(p: dict[str, Any], tag_labels: dict[int, str]) -> dict[str, Any]:
    """Indexer / indexer proxy. Secret fields (API keys, passwords, usernames) are masked by
    the API, so they cannot be exported: only their names are kept, in `secretFields`."""
    fields: dict[str, Any] = {}
    secrets: list[str] = []
    for f in p.get("fields") or []:
        if _is_secret(f):
            secrets.append(f["name"])
        else:
            fields[f["name"]] = f.get("value")
    out: dict[str, Any] = {
        "name": p["name"],
        "implementation": p["implementation"],
        "configContract": p.get("configContract"),
        "tags": sorted((tag_labels[t] for t in p.get("tags") or [] if t in tag_labels), key=str.lower),
        "fields": fields,
    }
    if secrets:
        out["secretFields"] = sorted(secrets)
    return out


def normalize_indexer(i: dict[str, Any], tag_labels: dict[int, str], profile_names: dict[int, str]) -> dict[str, Any]:
    out = normalize_provider(i, tag_labels)
    out.update(
        definitionName=i.get("definitionName"),
        enable=bool(i.get("enable")),
        priority=i.get("priority"),
        redirect=bool(i.get("redirect")),
        appProfile=profile_names.get(i.get("appProfileId")),
    )
    return out


def normalize_app_profile(p: dict[str, Any]) -> dict[str, Any]:
    return {"name": p["name"], **{k: p[k] for k in APP_PROFILE_KEYS if k in p}}


# --------------------------------------------------------------------------- diffs


def _short(v: Any, n: int = 60) -> str:
    s = str(v)
    return s if len(s) <= n else s[: n - 1] + "…"


def _by_name(specs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for s in specs:
        key, i = s["name"], 1
        while key in out:
            i += 1
            key = f"{s['name']}#{i}"
        out[key] = s
    return out


def diff_cf(cur: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changes = []
    if cur["includeCustomFormatWhenRenaming"] != new["includeCustomFormatWhenRenaming"]:
        changes.append(
            f"includeCustomFormatWhenRenaming: {cur['includeCustomFormatWhenRenaming']} → {new['includeCustomFormatWhenRenaming']}"
        )
    cs, ns = _by_name(cur["specifications"]), _by_name(new["specifications"])
    changes += [f"+ condition '{n}'" for n in ns if n not in cs]
    changes += [f"- condition '{n}'" for n in cs if n not in ns]
    for n in ns.keys() & cs.keys():
        for k in ("implementation", "negate", "required"):
            if cs[n][k] != ns[n][k]:
                changes.append(f"'{n}'.{k}: {cs[n][k]} → {ns[n][k]}")
        # Only fields present in the bundle count: the API adds defaulted ones.
        for fk, fv in ns[n]["fields"].items():
            old = cs[n]["fields"].get(fk)
            if old != fv:
                changes.append(f"'{n}'.{fk}: {_short(old)} → {_short(fv)}")
    return changes


def diff_profile(cur: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changes = []
    for k in ("upgradeAllowed", "cutoff", *SCORE_KEYS, "language"):
        if k in new and cur.get(k) != new[k]:
            changes.append(f"{k}: {cur.get(k)} → {new[k]}")
    if cur["items"] != new["items"]:
        ca = {i["name"] for i in cur["items"] if i["allowed"]}
        na = {i["name"] for i in new["items"] if i["allowed"]}
        if na - ca:
            changes.append("qualities enabled: " + ", ".join(sorted(na - ca)))
        if ca - na:
            changes.append("qualities disabled: " + ", ".join(sorted(ca - na)))
        if ca == na:
            shape = lambda items: [(i["name"], tuple(i.get("items", []))) for i in items]
            changes.append("quality order or grouping changed" if shape(cur["items"]) != shape(new["items"])
                           else "quality size limits changed")
    cs = {x["name"]: x["score"] for x in cur["formatItems"]}
    ns = {x["name"]: x["score"] for x in new["formatItems"]}
    for name in sorted(cs.keys() | ns.keys(), key=str.lower):
        if cs.get(name, 0) != ns.get(name, 0):
            changes.append(f"score {name}: {cs.get(name, 0)} → {ns.get(name, 0)}")
    return changes


def diff_metadata(cur: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changes = []
    for key, _ in META_LISTS:
        if key not in new:
            continue
        c, n = set(cur[key]), set(new[key])
        if n - c:
            changes.append(f"{key}: + {', '.join(sorted(n - c))}")
        if c - n:
            changes.append(f"{key}: - {', '.join(sorted(c - n))}")
    return changes


def diff_simple(cur: dict[str, Any], new: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [f"{k}: {_short(cur.get(k))} → {_short(new[k])}" for k in keys if k in new and cur.get(k) != new[k]]


def diff_provider(cur: dict[str, Any], new: dict[str, Any], skip: tuple[str, ...] = ()) -> list[str]:
    changes = diff_simple(cur, {k: v for k, v in new.items() if k in PROVIDER_KEYS and k not in skip and v is not None}, PROVIDER_KEYS)
    if {t.lower() for t in cur["tags"]} != {t.lower() for t in new.get("tags", [])}:
        changes.append(f"tags: {', '.join(cur['tags']) or '–'} → {', '.join(new.get('tags', [])) or '–'}")
    for k, v in new.get("fields", {}).items():
        if cur["fields"].get(k) != v:
            changes.append(f"{k}: {_short(cur['fields'].get(k))} → {_short(v)}")
    return changes


# --------------------------------------------------------------------------- export / parse


async def export_bundle(client: ArrClient, instance_name: str = "") -> dict[str, Any]:
    status = await client.status()
    bundle: dict[str, Any] = {
        "format": FORMAT,
        "version": VERSION,
        "exportedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": {"app": status["app"], "version": status["version"], "instanceName": instance_name},
    }
    if status["app"] == "prowlarr":
        await _export_prowlarr(client, bundle)
    else:
        await _export_arr(client, bundle)
    return bundle


async def _export_arr(client: ArrClient, bundle: dict[str, Any]) -> None:
    lidarr = bundle["source"]["app"] == "lidarr"
    # the reads are independent: one round trip instead of six
    cfs, profiles, defs, meta, *configs = await gather(
        client.get("customformat"), client.get("qualityprofile"), client.get("qualitydefinition"),
        client.get("metadataprofile") if lidarr else _none(),
        *(_maybe(client.get(path)) for path in CONFIG_PATHS.values()))
    cf_names = {c["id"]: c["name"] for c in cfs}
    bundle["customFormats"] = [normalize_cf(c) for c in sorted(cfs, key=lambda c: c["name"].lower())]
    bundle["qualityProfiles"] = [normalize_profile(p, cf_names) for p in sorted(profiles, key=lambda p: p["name"].lower())]
    bundle["qualityDefinitions"] = [normalize_definition(d) for d in sorted(defs, key=lambda d: d.get("weight", 0))]
    if lidarr:
        bundle["metadataProfiles"] = [normalize_metadata_profile(p) for p in sorted(meta, key=lambda p: p["name"].lower())]
    for section, config in zip(CONFIG_PATHS, configs, strict=True):
        if config is not None:  # None: not available on this version
            bundle[section] = normalize_config(config)


async def _export_prowlarr(client: ArrClient, bundle: dict[str, Any]) -> None:
    tags, profiles, proxies, indexers = await gather(
        client.get("tag"), client.get("appprofile"), client.get("indexerproxy"), client.get("indexer"))
    tag_labels = {t["id"]: t["label"] for t in tags}
    profile_names = {p["id"]: p["name"] for p in profiles}
    by_name = lambda x: x["name"].lower()
    bundle["appProfiles"] = [normalize_app_profile(p) for p in sorted(profiles, key=by_name)]
    bundle["indexerProxies"] = [normalize_provider(p, tag_labels) for p in sorted(proxies, key=by_name)]
    bundle["indexers"] = [normalize_indexer(i, tag_labels, profile_names) for i in sorted(indexers, key=by_name)]


def validate_bundle(bundle: Any) -> dict[str, Any]:
    if not isinstance(bundle, dict) or bundle.get("format") != FORMAT:
        raise PorterError("Not an Portarr bundle")
    if not isinstance(bundle.get("version"), int) or bundle["version"] > VERSION:
        raise PorterError(f"Unsupported bundle version {bundle.get('version')!r}")
    return bundle


def parse_bundle(data: Any) -> dict[str, Any]:
    """Accept an Portarr bundle, or TRaSH-Guides custom format JSON (one object or a list)."""
    if isinstance(data, dict) and data.get("format") == FORMAT:
        return validate_bundle(data)
    cfs = data if isinstance(data, list) else [data]
    if cfs and all(isinstance(c, dict) and "name" in c and "specifications" in c for c in cfs):
        try:
            custom_formats = [normalize_cf(c) for c in cfs]
        except KeyError as e:
            raise PorterError(f"Invalid custom format JSON: missing {e}") from e
        return {
            "format": FORMAT,
            "version": VERSION,
            "source": {"app": None, "origin": "trash-guides"},
            "customFormats": custom_formats,
        }
    raise PorterError("Unrecognised file: expected an Portarr export or TRaSH-Guides custom format JSON")


# --------------------------------------------------------------------------- import


def _quality_index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for it in items:
        if it.get("items"):
            out.update(_quality_index(it["items"]))
        elif it.get("quality"):
            out[it["quality"]["name"]] = it["quality"]
    return out


def _schema_match(schema: list[dict[str, Any]], src: dict[str, Any]) -> dict[str, Any] | None:
    """The target's template for an indexer / proxy type (definitions differ between versions)."""
    cands = [x for x in schema if x.get("implementation") == src["implementation"]]
    if src.get("definitionName"):
        cands = [x for x in cands if x.get("definitionName") == src["definitionName"]]
    return cands[0] if cands else None


class Importer:
    """Plans (dry run) and optionally applies a bundle onto a target instance."""

    def __init__(
        self,
        client: ArrClient,
        bundle: dict[str, Any],
        selection: dict[str, list[str]] | None = None,
        overwrite: bool = False,
        apply: bool = False,
    ):
        self.client = client
        self.bundle = validate_bundle(bundle)
        self.selection = selection
        self.overwrite = overwrite
        self.apply = apply
        self.app = ""
        self.pending_cfs: set[str] = set()  # CFs that a dry run would create
        self.pending_app_profiles: set[str] = set()
        self.tag_ids: dict[str, int] | None = None  # Prowlarr tags, by lower-cased label
        self.tag_labels: dict[int, str] = {}

    # -- selection helpers

    def _pick(self, section: str, key: str) -> list[dict[str, Any]]:
        items = self.bundle.get(section) or []
        if self.selection is None:
            return list(items)
        wanted = set(self.selection.get(section) or [])
        return [i for i in items if i[key] in wanted]

    def _pick_config(self, section: str) -> dict[str, Any] | None:
        src = self.bundle.get(section)
        if not isinstance(src, dict):
            return None
        if self.selection is not None and section not in (self.selection.get(section) or []):
            return None
        return src

    @staticmethod
    def _item(section: str, name: str) -> dict[str, Any]:
        return {"section": section, "name": name, "action": None, "changes": [], "warnings": [], "status": None, "error": None}

    # -- main entry

    async def run(self) -> dict[str, Any]:
        status = await self.client.status()
        self.app = status["app"]
        src_app = (self.bundle.get("source") or {}).get("app")
        if src_app and src_app != self.app:
            raise PorterError(f"This bundle comes from {src_app.capitalize()} but the target is {self.app.capitalize()}")
        sections: dict[str, list[dict[str, Any]]] = {}
        for section in SECTION_ORDER:
            if section in CONFIG_PATHS:
                items = await self._plan_config(section)
            else:
                items = await getattr(self, f"_plan_{section}")()
            if not items:
                continue
            if self.apply:
                await self._execute(items)
            sections[section] = items
        summary = {"create": 0, "update": 0, "unchanged": 0, "skip": 0, "error": 0}
        for items in sections.values():
            for it in items:
                summary["error" if it["status"] == "error" else it["action"]] += 1
        return {
            "app": self.app,
            "version": status["version"],
            "applied": self.apply,
            "summary": summary,
            "sections": {
                s: [{k: v for k, v in it.items() if not k.startswith("_")} for it in items] for s, items in sections.items()
            },
        }

    async def _execute(self, items: list[dict[str, Any]]) -> None:
        for it in items:
            if it["action"] not in ("create", "update"):
                continue
            try:
                await it["_exec"]()
                it["status"] = "ok"
            except ArrError as e:
                it["status"] = "error"
                it["error"] = str(e)

    # -- custom formats

    async def _plan_customFormats(self) -> list[dict[str, Any]]:
        src = self._pick("customFormats", "name")
        if not src:
            return []
        existing = {c["name"].lower(): c for c in await self.client.get("customformat")}
        items = []
        for cf in src:
            item = self._item("customFormats", cf["name"])
            payload = cf_payload(cf)
            cur = existing.get(cf["name"].lower())
            if cur is None:
                item["action"] = "create"
                item["_exec"] = partial(self.client.post, "customformat", payload)
                if not self.apply:
                    self.pending_cfs.add(cf["name"])
            else:
                item["changes"] = diff_cf(normalize_cf(cur), normalize_cf(cf))
                self._decide_existing(item, partial(self.client.put, f"customformat/{cur['id']}", {**payload, "id": cur["id"]}))
            items.append(item)
        return items

    def _decide_existing(self, item: dict[str, Any], exec_: Callable[[], Awaitable[Any]]) -> None:
        if not item["changes"]:
            item["action"] = "unchanged"
        elif not self.overwrite:
            item["action"] = "skip"
            item["warnings"].append("Already exists: enable “overwrite existing” to update it")
        else:
            item["action"] = "update"
            item["_exec"] = exec_

    # -- quality definitions (min / preferred / max size)

    async def _plan_qualityDefinitions(self) -> list[dict[str, Any]]:
        src = self._pick("qualityDefinitions", "quality")
        if not src:
            return []
        by_name = {d["quality"]["name"]: d for d in await self.client.get("qualitydefinition")}
        items = []
        for d in src:
            item = self._item("qualityDefinitions", d["quality"])
            cur = by_name.get(d["quality"])
            if cur is None:
                item["action"] = "skip"
                item["warnings"].append("Quality unknown on the target")
                items.append(item)
                continue
            new = dict(cur)
            for k in ("title", "minSize", "maxSize", "preferredSize"):
                if k in cur and k in d and cur[k] != d[k]:
                    item["changes"].append(f"{k}: {_short(cur[k])} → {_short(d[k])}")
                    new[k] = d[k]
            if item["changes"]:
                item["action"] = "update"
                item["_exec"] = partial(self.client.put, f"qualitydefinition/{cur['id']}", new)
            else:
                item["action"] = "unchanged"
            items.append(item)
        return items

    # -- quality profiles

    async def _plan_qualityProfiles(self) -> list[dict[str, Any]]:
        src = self._pick("qualityProfiles", "name")
        if not src:
            return []
        wants_language = any(p.get("language") for p in src)  # Radarr, Whisparr v3: a language per profile
        cf_list, profile_list, schema, language_list = await gather(
            self.client.get("customformat"), self.client.get("qualityprofile"), self.client.get("qualityprofile/schema"),
            _maybe(self.client.get("language")) if wants_language else _none())
        cfs = [{"id": c["id"], "name": c["name"]} for c in cf_list]
        cf_names = {c["id"]: c["name"] for c in cfs}
        cfs += [{"id": None, "name": n} for n in sorted(self.pending_cfs)]
        existing = {p["name"].lower(): p for p in profile_list}
        qualities = _quality_index(schema["items"])
        languages = {lang["name"].lower(): lang for lang in language_list or []}
        items = []
        for p in src:
            item = self._item("qualityProfiles", p["name"])
            cur = existing.get(p["name"].lower())
            built = self._build_profile(p, cur or schema, cfs, qualities, languages, item["warnings"])
            if cur is None:
                built.pop("id", None)
                item["action"] = "create"
                item["_exec"] = partial(self.client.post, "qualityprofile", built)
            else:
                item["changes"] = diff_profile(normalize_profile(cur, cf_names), normalize_profile(built, cf_names))
                self._decide_existing(item, partial(self.client.put, f"qualityprofile/{cur['id']}", built))
            items.append(item)
        return items

    def _build_profile(
        self,
        src: dict[str, Any],
        base: dict[str, Any],
        cfs: list[dict[str, Any]],
        qualities: dict[str, dict[str, Any]],
        languages: dict[str, Any],
        warnings: list[str],
    ) -> dict[str, Any]:
        p = copy.deepcopy(base)
        p["name"] = src["name"]
        for k in ("upgradeAllowed", *SCORE_KEYS):
            if k in src and k in p:
                p[k] = src[k]

        # quality items: resolve every quality by name against the target's own list
        items: list[dict[str, Any]] = []
        used: set[str] = set()
        group_id = GROUP_ID_START
        for it in src["items"]:
            allowed = bool(it["allowed"])
            if it.get("items"):
                children = []
                for qn in it["items"]:
                    q = qualities.get(qn)
                    if q is None:
                        warnings.append(f"Quality '{qn}' unknown on the target: dropped from group '{it['name']}'")
                        continue
                    children.append({"quality": q, "items": [], "allowed": allowed})
                    used.add(qn)
                if children:
                    items.append({"id": group_id, "name": it["name"], "items": children, "allowed": allowed})
                    group_id += 1
            else:
                q = qualities.get(it["name"])
                if q is None:
                    warnings.append(f"Quality '{it['name']}' unknown on the target: dropped")
                    continue
                items.append({"quality": q, "items": [], "allowed": allowed, **{k: it[k] for k in SIZE_KEYS if it.get(k) is not None}})
                used.add(it["name"])
        # qualities the bundle does not mention (newer target version, or a TRaSH profile): keep them, disabled
        extra = [{"quality": q, "items": [], "allowed": False} for name, q in qualities.items() if name not in used]
        p["items"] = extra + items if src.get("unlistedQualities") == "first" else items + extra  # "first" = lowest priority

        # cutoff: name -> id of the matching group / quality
        cutoff_id = None
        for it in items:
            name = it["name"] if it.get("items") else it["quality"]["name"]
            ident = it["id"] if it.get("items") else it["quality"]["id"]
            if name == src.get("cutoff"):
                cutoff_id = ident
        if cutoff_id is None:
            first = next((it for it in items if it["allowed"]), None)
            if first is not None:
                cutoff_id = first["id"] if first.get("items") else first["quality"]["id"]
            warnings.append(f"Cutoff '{src.get('cutoff')}' not found: using the first enabled quality")
        p["cutoff"] = cutoff_id

        # custom format scores: by name, on the target's own CF ids
        scores = {x["name"]: x["score"] for x in src.get("formatItems", [])}
        format_items = []
        for cf in cfs:
            format_items.append({"format": cf["id"], "name": cf["name"], "score": scores.pop(cf["name"], 0)})
        for name, score in scores.items():
            warnings.append(f"Custom format '{name}' not found on the target: score {score} ignored")
        p["formatItems"] = format_items

        if src.get("language") and "language" in p:
            lang = languages.get(str(src["language"]).lower())
            if lang:
                p["language"] = {"id": lang["id"], "name": lang["name"]}
            elif languages:
                warnings.append(f"Language '{src['language']}' unknown on the target: unchanged")
        return p

    # -- Lidarr: metadata profiles (which album types / release statuses are wanted)

    async def _plan_metadataProfiles(self) -> list[dict[str, Any]]:
        src = self._pick("metadataProfiles", "name")
        if not src:
            return []
        listing, schema = await gather(self.client.get("metadataprofile"), self.client.get("metadataprofile/schema"))
        existing = {p["name"].lower(): p for p in listing}
        if isinstance(schema, list):
            schema = schema[0]
        items = []
        for s in src:
            item = self._item("metadataProfiles", s["name"])
            cur = existing.get(s["name"].lower())
            built = copy.deepcopy(cur or schema)
            built["name"] = s["name"]
            for key, sub in META_LISTS:
                if key not in s:
                    continue
                wanted = set(s[key])
                known = {i[sub]["name"] for i in built.get(key, [])}
                if wanted - known:
                    item["warnings"].append(f"{key}: {', '.join(sorted(wanted - known))} unknown on the target")
                for i in built.get(key, []):
                    i["allowed"] = i[sub]["name"] in wanted
            if cur is None:
                built.pop("id", None)
                item["action"] = "create"
                item["_exec"] = partial(self.client.post, "metadataprofile", built)
            else:
                item["changes"] = diff_metadata(normalize_metadata_profile(cur), normalize_metadata_profile(built))
                self._decide_existing(item, partial(self.client.put, f"metadataprofile/{cur['id']}", built))
            items.append(item)
        return items

    # -- naming / media management (single config objects)

    async def _plan_config(self, section: str) -> list[dict[str, Any]]:
        src = self._pick_config(section)
        if src is None:
            return []
        path = CONFIG_PATHS[section]
        cur = await self.client.get(path)
        item = self._item(section, section)
        new = dict(cur)
        ignored = []
        for k, v in normalize_config(src).items():
            if k not in cur:
                ignored.append(k)
            elif cur[k] != v:
                item["changes"].append(f"{k}: {_short(cur[k])} → {_short(v)}")
                new[k] = v
        if ignored:
            item["warnings"].append("Settings unknown on the target, ignored: " + ", ".join(ignored))
        if section == "naming" and item["changes"] and any(cur.get(k) is False and k not in src for k in RENAME_KEYS):
            item["warnings"].append("Renaming is turned off on the target: these formats apply once you enable it in Settings → Media Management")
        if item["changes"]:
            item["action"] = "update"
            item["_exec"] = partial(self.client.put, f"{path}/{cur['id']}", new)
        else:
            item["action"] = "unchanged"
        return [item]

    # -- Prowlarr: sync profiles

    async def _plan_appProfiles(self) -> list[dict[str, Any]]:
        src = self._pick("appProfiles", "name")
        if not src:
            return []
        existing = {p["name"].lower(): p for p in await self.client.get("appprofile")}
        items = []
        for p in src:
            item = self._item("appProfiles", p["name"])
            cur = existing.get(p["name"].lower())
            if cur is None:
                payload = {"name": p["name"], "enableRss": True, "enableAutomaticSearch": True,
                           "enableInteractiveSearch": True, "minimumSeeders": 1}
                payload.update({k: p[k] for k in APP_PROFILE_KEYS if k in p})
                item["action"] = "create"
                item["_exec"] = partial(self.client.post, "appprofile", payload)
                if not self.apply:
                    self.pending_app_profiles.add(p["name"])
            else:
                item["changes"] = diff_simple(cur, p, APP_PROFILE_KEYS)
                payload = {**cur, **{k: p[k] for k in APP_PROFILE_KEYS if k in p}}
                self._decide_existing(item, partial(self.client.put, f"appprofile/{cur['id']}", payload))
            items.append(item)
        return items

    # -- Prowlarr: indexers and indexer proxies

    async def _load_tags(self) -> None:
        if self.tag_ids is None:
            tags = await self.client.get("tag")
            self.tag_ids = {t["label"].lower(): t["id"] for t in tags}
            self.tag_labels = {t["id"]: t["label"] for t in tags}

    async def _plan_indexerProxies(self) -> list[dict[str, Any]]:
        return await self._plan_provider("indexerProxies", "indexerproxy")

    async def _plan_indexers(self) -> list[dict[str, Any]]:
        return await self._plan_provider("indexers", "indexer")

    async def _plan_provider(self, section: str, path: str) -> list[dict[str, Any]]:
        src = self._pick(section, "name")
        if not src:
            return []
        is_indexer = section == "indexers"
        listing, plist, _ = await gather(
            self.client.get(path), self.client.get("appprofile") if is_indexer else _none(), self._load_tags())
        existing = {x["name"].lower(): x for x in listing}
        profiles = {p["name"].lower(): p["id"] for p in plist or []}
        profile_names = {p["id"]: p["name"] for p in plist or []}
        schema: list[dict[str, Any]] | None = None
        items = []
        for s in src:
            item = self._item(section, s["name"])
            cur = existing.get(s["name"].lower())
            secrets = s.get("secretFields") or []
            if cur is None:
                if schema is None:
                    schema = await self.client.get(f"{path}/schema")
                base = _schema_match(schema, s)
                if base is None:
                    item["action"] = "skip"
                    kind = "Indexer definition" if is_indexer else "Proxy type"
                    item["warnings"].append(f"{kind} '{s.get('definitionName') or s['implementation']}' not available on the target")
                    items.append(item)
                    continue
                await self._build_provider(s, base, profiles, is_indexer, True, item["warnings"], write=False)
                if secrets:
                    what = "created disabled" if is_indexer else "created"
                    item["warnings"].append(
                        f"Secret fields not exported ({', '.join(secrets)}): {what}, fill them in on the target"
                        + (" then enable it" if is_indexer else ""))
                item["action"] = "create"
                item["_exec"] = partial(self._write_provider, path, s, base, None, profiles, is_indexer, bool(secrets))
            else:
                norm = (normalize_indexer(cur, self.tag_labels, profile_names) if is_indexer
                        else normalize_provider(cur, self.tag_labels))
                # a secret-less copy stays as the user left it (enabled or not) until its secrets are filled in
                item["changes"] = diff_provider(norm, s, skip=("enable",) if secrets else ())
                await self._build_provider(s, cur, profiles, is_indexer, False, item["warnings"], write=False)
                self._decide_existing(item, partial(self._write_provider, path, s, cur, cur["id"], profiles, is_indexer, False))
            items.append(item)
        return items

    async def _write_provider(self, path: str, src: dict[str, Any], base: dict[str, Any], existing_id: int | None,
                              profiles: dict[str, int], is_indexer: bool, force: bool) -> None:
        payload = await self._build_provider(src, base, profiles, is_indexer, existing_id is None, [], write=True)
        if existing_id is None:
            # forceSave skips the connection test, which would fail without the secrets
            await self.client.post(path + ("?forceSave=true" if force else ""), payload)
        else:
            await self.client.put(f"{path}/{existing_id}", payload)

    async def _build_provider(self, src: dict[str, Any], base: dict[str, Any], profiles: dict[str, int], is_indexer: bool,
                              creating: bool, warnings: list[str], write: bool) -> dict[str, Any]:
        assert self.tag_ids is not None
        p = copy.deepcopy(base)
        p["name"] = src["name"]
        if creating:
            p.pop("id", None)
        known = {f["name"]: f for f in p.get("fields", [])}
        unknown = [k for k in src.get("fields", {}) if k not in known]
        for k, v in src.get("fields", {}).items():
            if k in known:
                known[k]["value"] = v
        if unknown:
            warnings.append("Settings unknown on the target, ignored: " + ", ".join(unknown))

        tag_ids = []
        for label in src.get("tags", []):
            tid = self.tag_ids.get(label.lower())
            if tid is None:
                if not write:
                    warnings.append(f"Tag '{label}' will be created")
                    continue
                tid = (await self.client.post("tag", {"label": label}))["id"]
                self.tag_ids[label.lower()] = tid
            tag_ids.append(tid)
        p["tags"] = tag_ids

        if is_indexer:
            if src.get("priority") is not None:
                p["priority"] = src["priority"]
            if "redirect" in src and "redirect" in p:
                p["redirect"] = src["redirect"]
            if creating:
                p["enable"] = bool(src.get("enable", True)) and not src.get("secretFields")
            elif "enable" in src and not src.get("secretFields"):
                p["enable"] = src["enable"]
            wanted = src.get("appProfile")
            if wanted:
                pid = profiles.get(wanted.lower())
                if pid is not None:
                    p["appProfileId"] = pid
                elif wanted not in self.pending_app_profiles:
                    warnings.append(f"Sync profile '{wanted}' not found on the target: default kept")
        return p

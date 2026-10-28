"""In-memory stand-ins for the Radarr / Sonarr / Whisparr (v3), Lidarr and Prowlarr (v1) APIs
(just the endpoints Portarr uses).

Mimics the validations that matter: unique names, a cutoff that points at a real item,
scores that reference real custom format ids.  Also runnable as a demo server:
    python -m tests.fake_arr radarr-a:7001 radarr-b:7002 sonarr-c:7003 sonarr-d:7004 ...  (the name picks the app)
"""
from __future__ import annotations

import copy
import sys
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

QUALITIES = [
    (4, "HDTV-720p"), (5, "WEBDL-720p"), (6, "Bluray-720p"), (3, "WEBDL-1080p"),
    (15, "WEBRip-1080p"), (7, "Bluray-1080p"), (30, "Remux-1080p"), (18, "WEBDL-2160p"),
]


MUSIC_QUALITIES = [
    (1, "MP3-192"), (2, "MP3-256"), (3, "MP3-320"), (4, "FLAC"), (5, "ALAC"), (6, "AAC-320"), (7, "FLAC 24bit"), (8, "WAV"),
]
SIZE_NONE = {"minSize": None, "maxSize": None, "preferredSize": None}


def q(qid: int, table: list = QUALITIES) -> dict[str, Any]:
    return {"id": qid, "name": dict(table)[qid], "source": "x", "resolution": 0}


def leaf(qid: int, allowed: bool, table: list = QUALITIES, sizes: dict | None = None) -> dict[str, Any]:
    out = {"quality": q(qid, table), "items": [], "allowed": allowed}
    if sizes is not None:  # Whisparr v2 keeps size limits on each quality of a profile
        out.update(sizes)
    return out


def cf(name: str, regex: str, negate: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "includeCustomFormatWhenRenaming": False,
        "specifications": [
            {"name": name, "implementation": "ReleaseTitleSpecification", "negate": negate, "required": False,
             "fields": [{"name": "value", "value": regex}]}
        ],
    }


PRIMARY_TYPES = ["Album", "EP", "Single", "Broadcast", "Other"]
SECONDARY_TYPES = ["Studio", "Compilation", "Soundtrack", "Live", "Remix"]
STATUSES = ["Official", "Promotional", "Bootleg", "Pseudo-Release"]


def meta_profile(pid: int, name: str, primary: list, secondary: list, statuses: list) -> dict[str, Any]:
    def items(key: str, sub: str, all_names: list, wanted: list) -> list:
        return [{"id": i, sub: {"id": i, "name": n}, "allowed": n in wanted} for i, n in enumerate(all_names)]
    return {
        "id": pid, "name": name,
        "primaryAlbumTypes": items("p", "albumType", PRIMARY_TYPES, primary),
        "secondaryAlbumTypes": items("s", "albumType", SECONDARY_TYPES, secondary),
        "releaseStatuses": items("r", "releaseStatus", STATUSES, statuses),
    }


def make_fake(app_name: str = "Radarr", api_key: str = "key", seed: str = "empty", cf_id_base: int = 1) -> FastAPI:
    """Radarr, Sonarr, Whisparr (v2 flavour: sizes inside profiles) or Lidarr (/api/v1, metadata profiles)."""
    radarr, lidarr, whisparr = app_name == "Radarr", app_name == "Lidarr", app_name == "Whisparr"
    P = "/api/v1" if lidarr else "/api/v3"
    table = MUSIC_QUALITIES if lidarr else QUALITIES
    ids = [qid for qid, _ in table]
    group_name = "Lossless" if lidarr else "WEB 1080p"
    naming_key = "standardMovieFormat" if radarr else "standardTrackFormat" if lidarr else "standardEpisodeFormat"
    lf = lambda qid, allowed, sizes=None: leaf(qid, allowed, table, SIZE_NONE if whisparr and sizes is None else sizes)  # noqa: E731
    db: dict[str, Any] = {
        "cfs": [], "profiles": [], "next_id": cf_id_base, "meta": [],
        "defs": [
            {"id": 100 + i, "quality": q(qid, table), "title": name, **({} if whisparr else {"weight": i}),
             "minSize": 0.0, "maxSize": 100.0, "preferredSize": 50.0}
            for i, (qid, name) in enumerate(table)
        ],
        "naming": {"id": 1, "colonReplacementFormat": "delete", naming_key: "{Title}"},
        "media": {"id": 1, "recycleBin": "/bin", "downloadPropersAndRepacks": "preferAndUpgrade"},
    }
    api = FastAPI()
    api.state.db = db

    def nid() -> int:
        db["next_id"] += 1
        return db["next_id"]

    def store_cf(body: dict[str, Any], cid: int) -> dict[str, Any]:
        out = copy.deepcopy(body)
        out["id"] = cid
        for s in out["specifications"]:
            s["implementationName"] = s["implementation"]
            if s["implementation"] == "LanguageSpecification" and not any(f["name"] == "exceptLanguage" for f in s["fields"]):
                s["fields"].append({"name": "exceptLanguage", "value": False})  # API-side default
        return out

    def err(prop: str, msg: str) -> JSONResponse:
        return JSONResponse([{"propertyName": prop, "errorMessage": msg}], status_code=400)

    def check_profile(body: dict[str, Any], own_id: int | None) -> JSONResponse | None:
        if any(p["name"].lower() == body["name"].lower() and p["id"] != own_id for p in db["profiles"]):
            return err("Name", "Name must be unique")
        ids = set()
        for it in body["items"]:
            ids.add(it["id"] if it.get("items") else it["quality"]["id"])
        if body.get("cutoff") not in ids:
            return err("Cutoff", "Cutoff must be an allowed quality or group")
        cf_ids = {c["id"] for c in db["cfs"]}
        for fi in body["formatItems"]:
            if fi["format"] not in cf_ids:
                return err("FormatItems", f"Unknown custom format {fi['format']}")
        return None

    @api.middleware("http")
    async def auth(request: Request, call_next):
        if request.headers.get("x-api-key") != api_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

    @api.get(P + "/system/status")
    async def status():
        return {"appName": app_name, "version": "5.0.0", "instanceName": app_name}

    @api.get(P + "/customformat")
    async def list_cf():
        return db["cfs"]

    @api.post(P + "/customformat")
    async def create_cf(request: Request):
        body = await request.json()
        if any(c["name"].lower() == body["name"].lower() for c in db["cfs"]):
            return err("Name", "Name must be unique")
        if body["name"] == "Boom":
            return err("Name", "Boom is forbidden")
        c = store_cf(body, nid())
        db["cfs"].append(c)
        for p in db["profiles"]:  # real API adds the new CF to every profile at score 0
            p["formatItems"].append({"format": c["id"], "name": c["name"], "score": 0})
        return c

    @api.put(P + "/customformat/{cid}")
    async def update_cf(cid: int, request: Request):
        body = await request.json()
        for i, c in enumerate(db["cfs"]):
            if c["id"] == cid:
                db["cfs"][i] = store_cf(body, cid)
                return db["cfs"][i]
        return JSONResponse({"message": "NotFound"}, status_code=404)

    @api.get(P + "/qualityprofile")
    async def list_profiles():
        return db["profiles"]

    @api.get(P + "/qualityprofile/schema")
    async def schema():
        s = {
            "id": 0, "name": "", "upgradeAllowed": False, "cutoff": 0,
            "items": [lf(qid, False) for qid in ids],
            "minFormatScore": 0, "cutoffFormatScore": 0, **({} if lidarr else {"minUpgradeFormatScore": 1}),
            "formatItems": [{"format": c["id"], "name": c["name"], "score": 0} for c in db["cfs"]],
        }
        if radarr:
            s["language"] = {"id": -2, "name": "Original"}
        return s

    @api.post(P + "/qualityprofile")
    async def create_profile(request: Request):
        body = await request.json()
        if (e := check_profile(body, None)) is not None:
            return e
        body["id"] = nid()
        db["profiles"].append(body)
        return body

    @api.put(P + "/qualityprofile/{pid}")
    async def update_profile(pid: int, request: Request):
        body = await request.json()
        if (e := check_profile(body, pid)) is not None:
            return e
        for i, p in enumerate(db["profiles"]):
            if p["id"] == pid:
                db["profiles"][i] = body
                return body
        return JSONResponse({"message": "NotFound"}, status_code=404)

    @api.get(P + "/qualitydefinition")
    async def list_defs():
        return db["defs"]

    @api.put(P + "/qualitydefinition/{did}")
    async def update_def(did: int, request: Request):
        body = await request.json()
        for i, d in enumerate(db["defs"]):
            if d["id"] == did:
                db["defs"][i] = body
                return body
        return JSONResponse({"message": "NotFound"}, status_code=404)

    @api.get(P + "/metadataprofile")
    async def list_meta():
        return db["meta"]

    @api.get(P + "/metadataprofile/schema")
    async def meta_schema():
        return meta_profile(0, "", PRIMARY_TYPES, SECONDARY_TYPES, STATUSES)

    @api.post(P + "/metadataprofile")
    async def create_meta(request: Request):
        body = await request.json()
        if any(m["name"].lower() == body["name"].lower() for m in db["meta"]):
            return err("Name", "Name must be unique")
        if not any(i["allowed"] for i in body["primaryAlbumTypes"]):
            return err("PrimaryAlbumTypes", "At least one primary type must be allowed")
        body["id"] = nid()
        db["meta"].append(body)
        return body

    @api.put(P + "/metadataprofile/{mid}")
    async def update_meta(mid: int, request: Request):
        body = await request.json()
        for i, m in enumerate(db["meta"]):
            if m["id"] == mid:
                db["meta"][i] = body
                return body
        return JSONResponse({"message": "NotFound"}, status_code=404)

    @api.get(P + "/language")
    async def languages():
        return [{"id": -1, "name": "Any"}, {"id": -2, "name": "Original"}, {"id": 1, "name": "English"}, {"id": 2, "name": "French"}]

    @api.get(P + "/config/naming")
    async def get_naming():
        return db["naming"]

    @api.put(P + "/config/naming/{_id}")
    async def put_naming(_id: int, request: Request):
        db["naming"] = await request.json()
        return db["naming"]

    @api.get(P + "/config/mediamanagement")
    async def get_media():
        return db["media"]

    @api.put(P + "/config/mediamanagement/{_id}")
    async def put_media(_id: int, request: Request):
        db["media"] = await request.json()
        return db["media"]

    if seed == "source":
        for name, rx, neg in (("x265 (HD)", r"x265", False), ("BR-DISK", r"BR.?DISK", False), ("Not French", "FRENCH", True)):
            c = store_cf(cf(name, rx, neg), nid())
            db["cfs"].append(c)
        by_name = {c["name"]: c["id"] for c in db["cfs"]}
        db["profiles"].append({
            "id": nid(), "name": "HD Bluray + WEB", "upgradeAllowed": True, "cutoff": 1000,
            "items": [
                lf(ids[0], False),
                {"id": 1000, "name": group_name, "items": [lf(ids[3], True), lf(ids[4], True)], "allowed": True},
                lf(ids[5], True, {"minSize": 1.0, "maxSize": 20.0, "preferredSize": 10.0} if whisparr else None),
                lf(ids[1], False), lf(ids[2], False), lf(ids[6], False), lf(ids[7], False),
            ],
            "minFormatScore": 0, "cutoffFormatScore": 10000, **({} if lidarr else {"minUpgradeFormatScore": 1}),
            "formatItems": [
                {"format": by_name["x265 (HD)"], "name": "x265 (HD)", "score": -10000},
                {"format": by_name["BR-DISK"], "name": "BR-DISK", "score": -10000},
                {"format": by_name["Not French"], "name": "Not French", "score": 50},
            ],
            **({"language": {"id": 2, "name": "French"}} if radarr else {}),
        })
        db["defs"][3].update(minSize=5.0, maxSize=40.0, preferredSize=15.0)
        db["naming"].update({naming_key: "{Movie Title} ({Release Year})", "colonReplacementFormat": "smart"})
        if lidarr:
            db["meta"].append(meta_profile(11, "Studio albums", ["Album", "EP"], ["Studio"], ["Official"]))
    elif seed == "target":
        # Different ids, plus a CF with the same name as the source but different content
        db["next_id"] = 500
        for name, rx in (("Some Other CF", "foo"), ("BR-DISK", r"OLD.?REGEX")):
            db["cfs"].append(store_cf(cf(name, rx), nid()))
    return api


MASK = "********"


def field(name: str, value: Any = None, privacy: str = "normal") -> dict[str, Any]:
    return {"name": name, "value": value, "privacy": privacy, "type": "textbox"}


def indexer_template(definition: str, secret: bool = False) -> dict[str, Any]:
    fields = [field("definitionFile", definition), field("baseUrl", f"https://{definition}.example")]
    if secret:
        fields += [field("username", "", "userName"), field("apiKey", "", "apiKey")]
    return {
        "id": 0, "name": definition, "implementation": "Cardigann", "implementationName": "Cardigann",
        "configContract": "CardigannSettings", "definitionName": definition, "fields": fields, "tags": [],
        "enable": True, "redirect": False, "priority": 25, "appProfileId": 1, "protocol": "torrent", "privacy": "public",
    }


def make_fake_prowlarr(api_key: str = "key", seed: str = "empty") -> FastAPI:
    """Prowlarr (/api/v1). Secrets come back masked and are validated on save unless forceSave=true."""
    db: dict[str, Any] = {
        "next_id": 100, "tags": [], "profiles": [
            {"id": 1, "name": "Standard", "enableRss": True, "enableAutomaticSearch": True,
             "enableInteractiveSearch": True, "minimumSeeders": 1}],
        "indexers": [], "proxies": [], "secrets": {},  # secrets[(kind, id, field)] = stored value
        "saves": [],  # (kind, forceSave) log
    }
    templates = [indexer_template("publichd"), indexer_template("privtracker", secret=True)]
    proxy_template = {
        "id": 0, "name": "", "implementation": "FlareSolverr", "implementationName": "FlareSolverr",
        "configContract": "FlareSolverrSettings", "tags": [],
        "fields": [field("host", "http://localhost:8191/"), field("requestTimeout", 60)],
    }
    api = FastAPI()
    api.state.db = db

    def nid() -> int:
        db["next_id"] += 1
        return db["next_id"]

    def err(prop: str, msg: str) -> JSONResponse:
        return JSONResponse([{"propertyName": prop, "errorMessage": msg}], status_code=400)

    def masked(kind: str, obj: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(obj)
        for f in out["fields"]:
            if f["privacy"] in ("apiKey", "password") and db["secrets"].get((kind, obj["id"], f["name"])):
                f["value"] = MASK
        return out

    def save(kind: str, body: dict[str, Any], own_id: int | None, force: bool):
        store = db["indexers"] if kind == "indexer" else db["proxies"]
        db["saves"].append((kind, force))
        if any(x["name"].lower() == body["name"].lower() and x["id"] != own_id for x in store):
            return err("Name", "Should be unique")
        tag_ids = {t["id"] for t in db["tags"]}
        if any(t not in tag_ids for t in body.get("tags", [])):
            return err("Tags", "Unknown tag")
        if kind == "indexer" and body.get("appProfileId") not in {p["id"] for p in db["profiles"]}:
            return err("AppProfileId", "Unknown sync profile")
        obj = copy.deepcopy(body)
        obj["id"] = own_id or nid()
        for f in obj["fields"]:
            if f["privacy"] in ("apiKey", "password"):
                if f["value"] == MASK:  # unchanged: keep what is stored
                    f["value"] = db["secrets"].get((kind, obj["id"], f["name"]), "")
                if not f["value"] and not force:
                    return err(f["name"], "Field is required")
                db["secrets"][(kind, obj["id"], f["name"])] = f["value"]
                f["value"] = ""
        if own_id:
            for i, x in enumerate(store):
                if x["id"] == own_id:
                    store[i] = obj
        else:
            store.append(obj)
        return masked(kind, obj)

    @api.middleware("http")
    async def auth(request: Request, call_next):
        if request.headers.get("x-api-key") != api_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

    @api.get("/api/v1/system/status")
    async def status():
        return {"appName": "Prowlarr", "version": "1.30.0", "instanceName": "Prowlarr"}

    @api.get("/api/v1/tag")
    async def tags():
        return db["tags"]

    @api.post("/api/v1/tag")
    async def create_tag(request: Request):
        body = await request.json()
        if any(t["label"].lower() == body["label"].lower() for t in db["tags"]):
            return err("Label", "Tag exists")
        t = {"id": nid(), "label": body["label"].lower()}  # the real API lower-cases labels
        db["tags"].append(t)
        return t

    @api.get("/api/v1/appprofile")
    async def profiles():
        return db["profiles"]

    @api.post("/api/v1/appprofile")
    async def create_profile(request: Request):
        body = await request.json()
        if any(p["name"].lower() == body["name"].lower() for p in db["profiles"]):
            return err("Name", "Should be unique")
        body["id"] = nid()
        db["profiles"].append(body)
        return body

    @api.put("/api/v1/appprofile/{pid}")
    async def update_profile(pid: int, request: Request):
        body = await request.json()
        for i, p in enumerate(db["profiles"]):
            if p["id"] == pid:
                db["profiles"][i] = body
                return body
        return JSONResponse({"message": "NotFound"}, status_code=404)

    @api.get("/api/v1/indexer")
    async def list_indexers():
        return [masked("indexer", i) for i in db["indexers"]]

    @api.get("/api/v1/indexer/schema")
    async def indexer_schema():
        return templates

    @api.post("/api/v1/indexer")
    async def create_indexer(request: Request, forceSave: bool = False):
        return save("indexer", await request.json(), None, forceSave)

    @api.put("/api/v1/indexer/{iid}")
    async def update_indexer(iid: int, request: Request, forceSave: bool = False):
        return save("indexer", await request.json(), iid, forceSave)

    @api.get("/api/v1/indexerproxy")
    async def list_proxies():
        return [masked("proxy", p) for p in db["proxies"]]

    @api.get("/api/v1/indexerproxy/schema")
    async def proxy_schema():
        return [proxy_template]

    @api.post("/api/v1/indexerproxy")
    async def create_proxy(request: Request, forceSave: bool = False):
        return save("proxy", await request.json(), None, forceSave)

    @api.put("/api/v1/indexerproxy/{pid}")
    async def update_proxy(pid: int, request: Request, forceSave: bool = False):
        return save("proxy", await request.json(), pid, forceSave)

    if seed == "source":
        db["tags"] += [{"id": 11, "label": "anime"}, {"id": 12, "label": "flaresolverr"}]
        db["profiles"].append({"id": 2, "name": "RSS only", "enableRss": True, "enableAutomaticSearch": False,
                               "enableInteractiveSearch": False, "minimumSeeders": 3})
        pub = indexer_template("publichd")
        pub.update(id=21, name="PublicHD", priority=10, appProfileId=2, tags=[11])
        pub["fields"][1]["value"] = "https://my-mirror.example"
        priv = indexer_template("privtracker", secret=True)
        priv.update(id=22, name="PrivTracker", priority=5, tags=[11, 12])
        priv["fields"][2]["value"] = "alice"
        db["secrets"][("indexer", 22, "apiKey")] = "SUPER-SECRET"
        db["indexers"] += [pub, priv]
        db["proxies"].append({**copy.deepcopy(proxy_template), "id": 31, "name": "FlareSolverr", "tags": [12],
                              "fields": [field("host", "http://flare:8191/"), field("requestTimeout", 90)]})
    elif seed == "target":
        db["tags"].append({"id": 51, "label": "other"})
        pub = indexer_template("publichd")
        pub.update(id=61, name="PublicHD", priority=25, tags=[51])
        db["indexers"].append(pub)
    return api


class Router(httpx.AsyncBaseTransport):
    """Dispatch requests to one fake app per host name."""

    def __init__(self, apps: dict[str, FastAPI]):
        self.transports = {h: httpx.ASGITransport(app=a) for h, a in apps.items()}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        transport = self.transports.get(request.url.host)
        if transport is None:
            raise httpx.ConnectError(f"no such host {request.url.host}")
        return await transport.handle_async_request(request)


if __name__ == "__main__":
    import threading

    import uvicorn

    def serve(spec: str, seed: str, base: int) -> None:
        _, port = spec.split(":")
        if "prowlarr" in spec:
            fake = make_fake_prowlarr("demo-key", seed)
        else:
            app = next((n for n in ("Sonarr", "Lidarr", "Whisparr") if n.lower() in spec), "Radarr")
            fake = make_fake(app, "demo-key", seed, base)
        uvicorn.run(fake, host="0.0.0.0", port=int(port), log_level="warning")

    specs = sys.argv[1:] or ["radarr-a:7001", "radarr-b:7002"]
    threads = [
        # even positions are populated "source" servers, odd ones "target" servers with other ids
        threading.Thread(target=serve, args=(s, "source" if i % 2 == 0 else "target", 1 if i % 2 == 0 else 500), daemon=True)
        for i, s in enumerate(specs)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

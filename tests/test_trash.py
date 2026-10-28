import asyncio
import io
import json

import httpx
import pytest

from app import main
from app.arr import ArrClient
from app.porter import Importer, PorterError, normalize_profile
from app.store import InstanceStore
from app.trash import (TrashCatalog, build_bundle, default_selection, extract_files, is_trash_profile, list_profiles,
                       profile_detail, profile_from_catalog)
from tests.fake_arr import Router, make_fake
from tests.fake_trash import build_files, make_tarball, profile

URL = "http://trash.test/Guides.tar.gz"


def run(coro):
    return asyncio.run(coro)


class Server:
    """Serves the fake archive and counts downloads."""

    def __init__(self, blob=None, fail=False):
        self.blob, self.fail, self.hits = blob or make_tarball(), fail, 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.hits += 1
        if self.fail:
            raise httpx.ConnectError("offline")
        return httpx.Response(200, content=self.blob)


def catalog(server, cache=None, ttl=3600):
    return TrashCatalog(cache, URL, transport=httpx.MockTransport(server), ttl=ttl)


# ------------------------------------------------------------------ download and cache


def test_archive_extraction_ignores_noise():
    files = extract_files(io.BytesIO(make_tarball()))
    assert "radarr/cf/br-disk.json" in files and "sonarr/quality-profiles/web-1080p.json" in files
    assert "radarr/cf/broken.json" not in files  # malformed JSON is skipped, not fatal
    assert not any(p.startswith(("lidarr", "guide-only")) or p.endswith(".md") for p in files)


def test_download_is_cached_in_memory_and_on_disk(tmp_path):
    server, cache = Server(), tmp_path / "cache" / "trash.json"
    cat = catalog(server, cache)
    run(cat.load())
    run(cat.load())
    assert server.hits == 1 and cache.is_file()

    offline = catalog(Server(fail=True), cache)  # a fresh process: the disk copy is enough, no request at all
    assert run(offline.load()).keys() == cat.files.keys()

    server_again = Server()
    forced = catalog(server_again, cache)
    run(forced.load())
    run(forced.load(force=True))
    assert server_again.hits == 1  # first load read the disk; only the forced one downloaded


def test_stale_copy_is_used_when_offline_and_error_is_clear_without_one(tmp_path):
    cache = tmp_path / "trash.json"
    run(catalog(Server(), cache).load())
    stale = catalog(Server(fail=True), cache, ttl=0)  # expired and the network is down
    assert "radarr/cf/br-disk.json" in run(stale.load())

    with pytest.raises(PorterError, match="Internet access"):
        run(catalog(Server(fail=True)).load())


# ------------------------------------------------------------------ reading the guides


@pytest.fixture
def files():
    return build_files()


def test_profile_listing(files):
    profiles = list_profiles(files, "radarr")
    assert [(p["category"], p["name"]) for p in profiles] == [("Standard", "German HD"), ("Standard", "HD Bluray + WEB")]
    assert profiles[0]["description"] == "Line one - line two"  # markup stripped
    assert [p["name"] for p in list_profiles(files, "sonarr")] == ["WEB-1080p"]
    with pytest.raises(PorterError, match="only cover Radarr and Sonarr"):
        list_profiles(files, "lidarr")


def test_detail_resolves_mandatory_formats_scores_and_applicable_groups(files):
    p = profile_from_catalog(files, "radarr", "P1")
    detail = profile_detail(files, "radarr", p)
    assert {(r["name"], r["score"]) for r in detail["required"]} == {("BR-DISK", -10000), ("x265 (HD)", -10000)}
    assert [g["name"] for g in detail["groups"]] == ["[HDR] Formats", "[Streaming] General"]  # not the German-only group
    assert default_selection(detail) == {"cf-br", "cf-x265", "cf-hdr"}  # DTS and Netflix are opt-in

    german = profile_detail(files, "radarr", profile_from_catalog(files, "radarr", "P2"))
    assert german["scoreSet"] == "german"
    assert {(r["name"], r["score"]) for r in german["required"]} == {("BR-DISK", -10000), ("x265 (HD)", 0)}  # per score set


def test_bundle_for_defaults_and_for_a_custom_choice(files):
    p = profile_from_catalog(files, "radarr", "P1")
    b = build_bundle(files, "radarr", p)
    assert b["source"] == {"app": "radarr", "origin": "trash-guides", "profile": "HD Bluray + WEB", "version": None}
    assert [c["name"] for c in b["customFormats"]] == ["BR-DISK", "HDR", "x265 (HD)"]
    assert b["customFormats"][0]["specifications"][0]["fields"] == {"value": "BR.?DISK"}
    prof = b["qualityProfiles"][0]
    assert prof["formatItems"] == [{"name": "BR-DISK", "score": -10000}, {"name": "HDR", "score": 500}, {"name": "x265 (HD)", "score": -10000}]
    # highest first in the guide, lowest first in the API
    assert [i["name"] for i in prof["items"]] == ["WEBDL-720p", "WEB 1080p", "Bluray-1080p"]
    assert prof["unlistedQualities"] == "first" and prof["language"] == "Original" and prof["cutoff"] == "WEB 1080p"

    chosen = build_bundle(files, "radarr", p, {"cf-dts", "cf-nf", "not-in-this-profile"})
    assert [c["name"] for c in chosen["customFormats"]] == ["BR-DISK", "DTS", "Netflix", "x265 (HD)"]  # mandatory ones stay
    assert {"name": "DTS", "score": 100} in chosen["qualityProfiles"][0]["formatItems"]
    assert all(fi["name"] != "Netflix" for fi in chosen["qualityProfiles"][0]["formatItems"])  # score 0: defined, not scored

    german = build_bundle(files, "radarr", profile_from_catalog(files, "radarr", "P2"))
    assert all(fi["name"] != "x265 (HD)" for fi in german["qualityProfiles"][0]["formatItems"])  # 0 in that score set


def test_unresolvable_reference_becomes_a_warning(files):
    p = profile("PX", "Broken", formatItems={"Ghost": "cf-ghost", "BR-DISK": "cf-br"})
    b = build_bundle(files, "radarr", p)
    assert [c["name"] for c in b["customFormats"]] == ["BR-DISK"]
    assert "Ghost" in b["warnings"][0]


def test_profile_detection():
    assert is_trash_profile(profile("P1", "x"))
    assert not is_trash_profile({"trash_id": "a", "name": "x", "specifications": []})  # a custom format
    assert not is_trash_profile({"format": "portarr"})


# ------------------------------------------------------------------ importing it


@pytest.fixture
def radarr():
    apps = {"dst": make_fake("Radarr", "kb", "target"), "sonarr": make_fake("Sonarr", "ks")}
    ArrClient.transport_override = Router(apps)
    yield apps
    ArrClient.transport_override = None


async def do_import(host, key, bundle, apply=False):
    async with ArrClient(f"http://{host}", key) as c:
        return await Importer(c, bundle, None, True, apply).run()


def test_imported_profile_has_the_right_order_scores_and_language(files, radarr):
    bundle = build_bundle(files, "radarr", profile_from_catalog(files, "radarr", "P1"))
    result = run(do_import("dst", "kb", bundle, apply=True))
    assert result["summary"]["error"] == 0, result
    db = radarr["dst"].state.db
    prof = db["profiles"][0]
    assert prof["name"] == "HD Bluray + WEB" and prof["language"] == {"id": -2, "name": "Original"}
    norm = normalize_profile(prof)
    names = [i["name"] for i in norm["items"]]
    # qualities the guide does not mention come first (lowest priority), disabled; then the guide's order reversed
    assert names == ["HDTV-720p", "Bluray-720p", "Remux-1080p", "WEBDL-2160p", "WEBDL-720p", "WEB 1080p", "Bluray-1080p"]
    assert [i["allowed"] for i in norm["items"]] == [False] * 5 + [True, True]
    assert norm["cutoff"] == "WEB 1080p"
    ids = {c["name"]: c["id"] for c in db["cfs"]}
    scores = {fi["name"]: (fi["format"], fi["score"]) for fi in prof["formatItems"] if fi["score"]}
    assert scores == {"BR-DISK": (ids["BR-DISK"], -10000), "x265 (HD)": (ids["x265 (HD)"], -10000), "HDR": (ids["HDR"], 500)}

    again = run(do_import("dst", "kb", bundle))
    assert again["summary"]["create"] == again["summary"]["update"] == again["summary"]["error"] == 0


def test_a_radarr_profile_is_refused_on_sonarr(files, radarr):
    bundle = build_bundle(files, "radarr", profile_from_catalog(files, "radarr", "P1"))
    with pytest.raises(PorterError, match="Radarr but the target is Sonarr"):
        run(do_import("sonarr", "ks", bundle))


def test_sonarr_profiles_work_without_a_language(files, radarr):
    bundle = build_bundle(files, "sonarr", profile_from_catalog(files, "sonarr", "S1"))
    assert "language" not in bundle["qualityProfiles"][0]
    result = run(do_import("sonarr", "ks", bundle, apply=True))
    assert result["summary"]["error"] == 0, result


# ------------------------------------------------------------------ the HTTP API


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(main, "store", InstanceStore(tmp_path / "instances.json"))
    monkeypatch.setattr(main, "catalog", catalog(Server(), tmp_path / "trash.json"))
    with TestClient(main.app) as c:
        yield c


def test_catalog_endpoints(client):
    r = client.get("/api/trash/radarr/profiles").json()
    assert [p["name"] for p in r["profiles"]] == ["German HD", "HD Bluray + WEB"] and r["fetchedAt"] > 0
    detail = client.get("/api/trash/radarr/profiles/P1").json()
    assert detail["defaults"] == ["cf-br", "cf-hdr", "cf-x265"] and detail["scoreSet"] == "default"
    assert client.get("/api/trash/radarr/profiles/nope").status_code == 400
    assert "only cover Radarr and Sonarr" in client.get("/api/trash/lidarr/profiles").json()["detail"]

    build = client.post("/api/trash/radarr/build", json={"profile_id": "P1", "formats": ["cf-dts"]}).json()
    assert [c["name"] for c in build["customFormats"]] == ["BR-DISK", "DTS", "x265 (HD)"]
    assert client.post("/api/trash/refresh").json()["files"] > 10


def test_pasted_trash_profile_json_is_resolved_against_the_guides(client):
    text = json.dumps(profile("P1", "HD Bluray + WEB"))
    ok = client.post("/api/import/parse", json={"text": text, "app": "radarr"})
    assert ok.status_code == 200
    assert [c["name"] for c in ok.json()["customFormats"]] == ["BR-DISK", "HDR", "x265 (HD)"]
    assert ok.json()["qualityProfiles"][0]["name"] == "HD Bluray + WEB"
    no_app = client.post("/api/import/parse", json={"text": text})
    assert no_app.status_code == 400 and "choose a target instance" in no_app.json()["detail"]
    assert client.post("/api/import/parse", json={"text": text, "app": "lidarr"}).status_code == 400

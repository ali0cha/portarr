"""Radarr-family apps: the same source -> target round trip for every supported app."""
import asyncio
import copy

import pytest

from app.arr import ArrClient
from app.porter import Importer, PorterError, export_bundle
from tests.fake_arr import MUSIC_QUALITIES, QUALITIES, Router, make_fake

APPS = ["Radarr", "Sonarr", "Lidarr", "Whisparr"]
NAMING_KEY = {"Radarr": "standardMovieFormat", "Sonarr": "standardEpisodeFormat",
              "Whisparr": "standardEpisodeFormat", "Lidarr": "standardTrackFormat"}


@pytest.fixture(params=APPS)
def pair(request):
    name = request.param
    apps = {"src": make_fake(name, "ka", "source"), "dst": make_fake(name, "kb", "target")}
    ArrClient.transport_override = Router(apps)
    yield name, apps["src"], apps["dst"]
    ArrClient.transport_override = None


def run(coro):
    return asyncio.run(coro)


async def export(host, key):
    async with ArrClient(f"http://{host}", key) as c:  # app and API version are auto-detected
        return await export_bundle(c, host)


async def do_import(host, key, bundle, apply=False, overwrite=False, selection=None):
    async with ArrClient(f"http://{host}", key) as c:
        return await Importer(c, bundle, selection, overwrite, apply).run()


def test_detected_and_exported(pair):
    name, *_ = pair

    async def detect():
        async with ArrClient("http://src", "ka") as c:
            s = await c.status()
            return s["app"], c.api

    assert run(detect()) == (name.lower(), "v1" if name == "Lidarr" else "v3")
    bundle = run(export("src", "ka"))
    assert bundle["source"]["app"] == name.lower()
    profile = bundle["qualityProfiles"][0]
    assert profile["cutoff"] == ("Lossless" if name == "Lidarr" else "WEB 1080p")
    assert ("language" in profile) == (name == "Radarr")  # only apps whose profiles have one
    assert ("metadataProfiles" in bundle) == (name == "Lidarr")
    assert [c["name"] for c in bundle["customFormats"]] == ["BR-DISK", "Not French", "x265 (HD)"]


def test_roundtrip_and_idempotence(pair):
    name, src, dst = pair
    bundle = run(export("src", "ka"))
    preview = run(do_import("dst", "kb", bundle))
    assert preview["summary"]["error"] == 0 and dst.state.db["profiles"] == []  # dry run writes nothing

    result = run(do_import("dst", "kb", bundle, apply=True, overwrite=True))
    assert result["summary"]["error"] == 0, result
    db = dst.state.db
    ids = {c["name"]: c["id"] for c in db["cfs"]}
    assert ids["x265 (HD)"] >= 500  # the target's own ids
    prof = db["profiles"][0]
    assert {fi["name"]: fi["format"] for fi in prof["formatItems"] if fi["score"]}["x265 (HD)"] == ids["x265 (HD)"]
    assert prof["cutoff"] == 1000
    assert db["naming"][NAMING_KEY[name]] == "{Movie Title} ({Release Year})"
    table = MUSIC_QUALITIES if name == "Lidarr" else QUALITIES
    assert next(d for d in db["defs"] if d["quality"]["id"] == table[3][0])["maxSize"] == 40.0

    again = run(do_import("dst", "kb", bundle, overwrite=True))
    assert again["summary"]["create"] == again["summary"]["update"] == again["summary"]["error"] == 0, again
    assert again["summary"]["unchanged"] >= 14


def test_bundles_do_not_cross_apps(pair):
    name, *_ = pair
    other = next(a for a in APPS if a != name)
    ArrClient.transport_override = Router({"src": make_fake(name, "ka", "source"), "other": make_fake(other, "ko")})
    bundle = run(export("src", "ka"))
    with pytest.raises(PorterError, match=f"{name} but the target is {other}"):
        run(do_import("other", "ko", bundle))


def test_sonarr_profiles_have_no_language():
    ArrClient.transport_override = Router({"src": make_fake("Sonarr", "ka", "source"), "dst": make_fake("Sonarr", "kb")})
    bundle = run(export("src", "ka"))
    bundle["qualityProfiles"][0]["language"] = "French"  # e.g. a hand-edited file: must not break the import
    result = run(do_import("dst", "kb", bundle, apply=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
    assert result["sections"]["qualityProfiles"][0]["status"] == "ok"
    ArrClient.transport_override = None


def test_lidarr_metadata_profiles():
    src, dst = make_fake("Lidarr", "ka", "source"), make_fake("Lidarr", "kb", "target")
    ArrClient.transport_override = Router({"src": src, "dst": dst})
    try:
        bundle = run(export("src", "ka"))
        assert bundle["metadataProfiles"] == [{
            "name": "Studio albums", "primaryAlbumTypes": ["Album", "EP"], "secondaryAlbumTypes": ["Studio"],
            "releaseStatuses": ["Official"],
        }]
        result = run(do_import("dst", "kb", bundle, apply=True, selection={"metadataProfiles": ["Studio albums"]}))
        assert result["sections"]["metadataProfiles"][0]["status"] == "ok"
        created = dst.state.db["meta"][0]
        assert [i["albumType"]["name"] for i in created["primaryAlbumTypes"] if i["allowed"]] == ["Album", "EP"]
        assert [i["releaseStatus"]["name"] for i in created["releaseStatuses"] if i["allowed"]] == ["Official"]

        changed = copy.deepcopy(bundle)
        changed["metadataProfiles"][0]["primaryAlbumTypes"] = ["Album", "Single"]
        changed["metadataProfiles"][0]["releaseStatuses"].append("Bootleg")
        plan = run(do_import("dst", "kb", changed, overwrite=True, selection={"metadataProfiles": ["Studio albums"]}))
        item = plan["sections"]["metadataProfiles"][0]
        assert item["action"] == "update"
        assert item["changes"] == ["primaryAlbumTypes: + Single", "primaryAlbumTypes: - EP", "releaseStatuses: + Bootleg"]

        changed["metadataProfiles"][0]["secondaryAlbumTypes"] = ["Studio", "Karaoke"]
        plan = run(do_import("dst", "kb", changed, selection={"metadataProfiles": ["Studio albums"]}))
        assert any("Karaoke" in w for w in plan["sections"]["metadataProfiles"][0]["warnings"])
    finally:
        ArrClient.transport_override = None


def test_whisparr_keeps_size_limits_inside_profiles():
    src, dst = make_fake("Whisparr", "ka", "source"), make_fake("Whisparr", "kb", "target")
    ArrClient.transport_override = Router({"src": src, "dst": dst})
    try:
        bundle = run(export("src", "ka"))
        sized = [i for i in bundle["qualityProfiles"][0]["items"] if "minSize" in i]
        assert sized == [{"name": "Bluray-1080p", "allowed": True, "minSize": 1.0, "maxSize": 20.0, "preferredSize": 10.0}]
        assert "weight" not in src.state.db["defs"][0]  # Whisparr definitions have no weight

        run(do_import("dst", "kb", bundle, apply=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
        leaf = next(i for i in dst.state.db["profiles"][0]["items"] if i.get("quality", {}).get("name") == "Bluray-1080p")
        assert (leaf["minSize"], leaf["maxSize"], leaf["preferredSize"]) == (1.0, 20.0, 10.0)

        changed = copy.deepcopy(bundle)
        next(i for i in changed["qualityProfiles"][0]["items"] if "minSize" in i)["maxSize"] = 99.0
        plan = run(do_import("dst", "kb", changed, overwrite=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
        assert plan["sections"]["qualityProfiles"][0]["changes"] == ["quality size limits changed"]
    finally:
        ArrClient.transport_override = None

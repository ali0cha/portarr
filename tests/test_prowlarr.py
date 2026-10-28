import asyncio
import copy
import json

import pytest

from app.arr import ArrClient, ArrError
from app.porter import Importer, PorterError, export_bundle
from tests.fake_arr import Router, make_fake, make_fake_prowlarr


@pytest.fixture
def world():
    apps = {
        "psrc": make_fake_prowlarr("ka", "source"),
        "pdst": make_fake_prowlarr("kb", "target"),
        "radarr": make_fake("Radarr", "kr", "source"),
    }
    ArrClient.transport_override = Router(apps)
    yield apps
    ArrClient.transport_override = None


def run(coro):
    return asyncio.run(coro)


async def export(host, key, app="prowlarr"):
    async with ArrClient(f"http://{host}", key, app=app) as c:
        return await export_bundle(c, host)


async def do_import(host, key, bundle, apply=False, overwrite=False, selection=None, app="prowlarr"):
    async with ArrClient(f"http://{host}", key, app=app) as c:
        return await Importer(c, bundle, selection, overwrite, apply).run()


def actions(result, section):
    return {i["name"]: i["action"] for i in result["sections"][section]}


def test_app_and_api_version_are_detected(world):
    async def status(host, key):
        async with ArrClient(f"http://{host}", key) as c:
            s = await c.status()
            return s["app"], c.api

    assert run(status("psrc", "ka")) == ("prowlarr", "v1")
    assert run(status("radarr", "kr")) == ("radarr", "v3")
    with pytest.raises(ArrError, match="API key"):
        run(status("psrc", "wrong"))


def test_export_never_contains_secrets(world):
    bundle = run(export("psrc", "ka"))
    assert "SUPER-SECRET" not in json.dumps(bundle)
    assert "alice" not in json.dumps(bundle)  # usernames are masked too
    priv = next(i for i in bundle["indexers"] if i["name"] == "PrivTracker")
    assert priv["secretFields"] == ["apiKey", "username"]
    assert "apiKey" not in priv["fields"]
    pub = next(i for i in bundle["indexers"] if i["name"] == "PublicHD")
    assert pub["appProfile"] == "RSS only" and pub["tags"] == ["anime"] and pub["priority"] == 10
    assert pub["fields"]["baseUrl"] == "https://my-mirror.example"
    assert [p["name"] for p in bundle["appProfiles"]] == ["RSS only", "Standard"]
    assert bundle["indexerProxies"][0]["tags"] == ["flaresolverr"]


def test_roundtrip_remaps_tags_and_profiles_and_is_idempotent(world):
    bundle = run(export("psrc", "ka"))
    preview = run(do_import("pdst", "kb", bundle))
    assert actions(preview, "appProfiles") == {"RSS only": "create", "Standard": "unchanged"}
    assert actions(preview, "indexers") == {"PublicHD": "skip", "PrivTracker": "create"}
    assert actions(preview, "indexerProxies") == {"FlareSolverr": "create"}
    assert [t["label"] for t in world["pdst"].state.db["tags"]] == ["other"]  # dry run touches nothing

    result = run(do_import("pdst", "kb", bundle, apply=True, overwrite=True))
    assert result["summary"]["error"] == 0, result
    db = world["pdst"].state.db
    tags = {t["label"]: t["id"] for t in db["tags"]}
    assert set(tags) == {"other", "anime", "flaresolverr"}
    profile_id = next(p["id"] for p in db["profiles"] if p["name"] == "RSS only")
    pub = next(i for i in db["indexers"] if i["name"] == "PublicHD")
    assert pub["priority"] == 10 and pub["appProfileId"] == profile_id and pub["tags"] == [tags["anime"]]
    assert pub["fields"][1]["value"] == "https://my-mirror.example"
    priv = next(i for i in db["indexers"] if i["name"] == "PrivTracker")
    assert priv["enable"] is False  # secrets are missing: created disabled
    assert ("indexer", True) in db["saves"]  # ... with forceSave, since the connection test cannot pass
    assert sorted(priv["tags"]) == sorted([tags["anime"], tags["flaresolverr"]])
    created = next(i for i in result["sections"]["indexers"] if i["name"] == "PrivTracker")
    assert any("apiKey" in w and "disabled" in w for w in created["warnings"])

    again = run(do_import("pdst", "kb", bundle, overwrite=True))
    assert again["summary"] == {"create": 0, "update": 0, "unchanged": 5, "skip": 0, "error": 0}, again


def test_update_keeps_secrets_and_enabled_state(world):
    bundle = run(export("psrc", "ka"))
    run(do_import("pdst", "kb", bundle, apply=True, overwrite=True))
    db = world["pdst"].state.db
    priv = next(i for i in db["indexers"] if i["name"] == "PrivTracker")
    # the user fills in the secret on the target and enables the indexer
    db["secrets"][("indexer", priv["id"], "apiKey")] = "MINE"
    priv["enable"] = True

    changed = copy.deepcopy(bundle)
    next(i for i in changed["indexers"] if i["name"] == "PrivTracker")["priority"] = 99
    result = run(do_import("pdst", "kb", changed, apply=True, overwrite=True, selection={"indexers": ["PrivTracker"]}))
    item = result["sections"]["indexers"][0]
    assert item["action"] == "update" and item["status"] == "ok", item
    assert item["changes"] == ["priority: 5 → 99"]
    priv = next(i for i in db["indexers"] if i["name"] == "PrivTracker")
    assert priv["priority"] == 99
    assert priv["enable"] is True  # not forced back to the exported state
    assert db["secrets"][("indexer", priv["id"], "apiKey")] == "MINE"  # masked value round-tripped


def test_unknown_indexer_definition_is_skipped(world):
    bundle = run(export("psrc", "ka"))
    bundle["indexers"][0]["name"] = "Ghost"
    bundle["indexers"][0]["definitionName"] = "no-such-site"
    result = run(do_import("pdst", "kb", bundle, selection={"indexers": ["Ghost"]}))
    item = result["sections"]["indexers"][0]
    assert item["action"] == "skip" and "no-such-site" in item["warnings"][0]


def test_missing_sync_profile_warns(world):
    bundle = run(export("psrc", "ka"))
    result = run(do_import("pdst", "kb", bundle, selection={"indexers": ["PublicHD", "PrivTracker"]}, overwrite=True))
    pub = next(i for i in result["sections"]["indexers"] if i["name"] == "PublicHD")
    assert any("RSS only" in w for w in pub["warnings"])


def test_bundles_cannot_cross_apps(world):
    prowlarr_bundle = run(export("psrc", "ka"))
    radarr_bundle = run(export("radarr", "kr", app="radarr"))
    with pytest.raises(PorterError, match="Prowlarr but the target is Radarr"):
        run(do_import("radarr", "kr", prowlarr_bundle, app="radarr"))
    with pytest.raises(PorterError, match="Radarr but the target is Prowlarr"):
        run(do_import("pdst", "kb", radarr_bundle))

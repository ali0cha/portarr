import asyncio
import copy

import pytest

from app.arr import ArrClient, ArrError
from app.porter import Importer, PorterError, export_bundle, parse_bundle
from tests.fake_arr import Router, make_fake


@pytest.fixture
def world():
    src = make_fake("Radarr", "ka", seed="source")
    dst = make_fake("Radarr", "kb", seed="target")
    sonarr = make_fake("Sonarr", "ks", seed="empty")
    ArrClient.transport_override = Router({"src": src, "dst": dst, "sonarr": sonarr})
    yield {"src": src, "dst": dst, "sonarr": sonarr}
    ArrClient.transport_override = None


def run(coro):
    return asyncio.run(coro)


async def export(host, key):
    async with ArrClient(f"http://{host}", key) as c:
        return await export_bundle(c, host)


async def do_import(host, key, bundle, apply=False, overwrite=False, selection=None):
    async with ArrClient(f"http://{host}", key) as c:
        return await Importer(c, bundle, selection, overwrite, apply).run()


def actions(result, section):
    return {i["name"]: i["action"] for i in result["sections"][section]}


def test_export_is_id_independent(world):
    b = run(export("src", "ka"))
    assert b["source"]["app"] == "radarr"
    p = b["qualityProfiles"][0]
    assert p["cutoff"] == "WEB 1080p"
    assert p["language"] == "French"
    assert {"name": "WEB 1080p", "allowed": True, "items": ["WEBDL-1080p", "WEBRip-1080p"]} in p["items"]
    assert {"name": "x265 (HD)", "score": -10000} in p["formatItems"]
    assert [c["name"] for c in b["customFormats"]] == ["BR-DISK", "Not French", "x265 (HD)"]
    assert b["customFormats"][0]["specifications"][0]["fields"] == {"value": r"BR.?DISK"}
    assert "recycleBin" not in b["mediaManagement"]  # host-specific, excluded


def test_roundtrip_remaps_ids_and_is_idempotent(world):
    bundle = run(export("src", "ka"))
    preview = run(do_import("dst", "kb", bundle))
    assert actions(preview, "customFormats") == {"x265 (HD)": "create", "BR-DISK": "skip", "Not French": "create"}
    assert actions(preview, "qualityProfiles") == {"HD Bluray + WEB": "create"}
    # a dry run must not touch the target
    assert len(world["dst"].state.db["cfs"]) == 2

    result = run(do_import("dst", "kb", bundle, apply=True, overwrite=True))
    assert result["summary"]["error"] == 0, result
    db = world["dst"].state.db
    ids = {c["name"]: c["id"] for c in db["cfs"]}
    assert ids["x265 (HD)"] >= 500  # target's own ids, not the source's
    prof = db["profiles"][0]
    scores = {fi["name"]: (fi["format"], fi["score"]) for fi in prof["formatItems"]}
    assert scores["x265 (HD)"] == (ids["x265 (HD)"], -10000)
    assert scores["Not French"] == (ids["Not French"], 50)
    assert scores["Some Other CF"][1] == 0
    assert prof["cutoff"] == 1000
    assert prof["language"] == {"id": 2, "name": "French"}
    assert db["naming"]["standardMovieFormat"] == "{Movie Title} ({Release Year})"
    assert next(d for d in db["defs"] if d["quality"]["name"] == "WEBDL-1080p")["maxSize"] == 40.0
    # BR-DISK existed with other content: overwritten
    assert next(c for c in db["cfs"] if c["name"] == "BR-DISK")["specifications"][0]["fields"][0]["value"] == r"BR.?DISK"

    # second pass: everything already in place
    again = run(do_import("dst", "kb", bundle, overwrite=True))
    assert again["summary"] == {"create": 0, "update": 0, "unchanged": 14, "skip": 0, "error": 0}, again


def test_existing_items_are_skipped_without_overwrite(world):
    bundle = run(export("src", "ka"))
    result = run(do_import("dst", "kb", bundle, apply=True, overwrite=False))
    assert actions(result, "customFormats")["BR-DISK"] == "skip"
    db = world["dst"].state.db
    assert next(c for c in db["cfs"] if c["name"] == "BR-DISK")["specifications"][0]["fields"][0]["value"] == r"OLD.?REGEX"


def test_selection_limits_what_is_imported(world):
    bundle = run(export("src", "ka"))
    sel = {"customFormats": ["Not French"], "naming": ["naming"]}
    result = run(do_import("dst", "kb", bundle, apply=True, selection=sel))
    assert list(result["sections"]) == ["customFormats", "naming"]
    assert [c["name"] for c in world["dst"].state.db["cfs"]] == ["Some Other CF", "BR-DISK", "Not French"]
    assert world["dst"].state.db["profiles"] == []


def test_profile_warns_about_missing_cf(world):
    bundle = run(export("src", "ka"))
    result = run(do_import("dst", "kb", bundle, apply=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
    item = result["sections"]["qualityProfiles"][0]
    assert item["status"] == "ok"
    assert any("x265 (HD)" in w for w in item["warnings"])
    assert any("Not French" in w for w in item["warnings"])


def test_unknown_quality_and_cutoff_fallback(world):
    bundle = run(export("src", "ka"))
    bundle["qualityProfiles"][0]["items"].append({"name": "Bluray-8K", "allowed": True})
    bundle["qualityProfiles"][0]["cutoff"] = "Bluray-8K"
    result = run(do_import("dst", "kb", bundle, apply=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
    item = result["sections"]["qualityProfiles"][0]
    assert item["status"] == "ok"
    assert any("Bluray-8K" in w for w in item["warnings"])


def test_update_diff_reports_score_change(world):
    bundle = run(export("src", "ka"))
    run(do_import("dst", "kb", bundle, apply=True, overwrite=True))
    changed = copy.deepcopy(bundle)
    changed["qualityProfiles"][0]["formatItems"][0]["score"] = 123
    changed["qualityProfiles"][0]["upgradeAllowed"] = False
    result = run(do_import("dst", "kb", changed, overwrite=True, selection={"qualityProfiles": ["HD Bluray + WEB"]}))
    item = result["sections"]["qualityProfiles"][0]
    assert item["action"] == "update"
    assert "upgradeAllowed: True → False" in item["changes"]
    assert any(c.startswith("score ") and "→ 123" in c for c in item["changes"])


def test_api_error_is_reported_per_item(world):
    bundle = parse_bundle([
        {"name": "Boom", "specifications": []},  # the fake API refuses this name
        {"name": "Fine", "specifications": []},
    ])
    result = run(do_import("dst", "kb", bundle, apply=True))
    status = {i["name"]: (i["status"], i["error"]) for i in result["sections"]["customFormats"]}
    assert status["Boom"] == ("error", "Name: Boom is forbidden")
    assert status["Fine"] == ("ok", None)
    assert result["summary"]["error"] == 1 and result["summary"]["create"] == 1


def test_app_mismatch_is_refused(world):
    bundle = run(export("src", "ka"))
    with pytest.raises(PorterError, match="Radarr but the target is Sonarr"):
        run(do_import("sonarr", "ks", bundle))


def test_trash_guides_custom_format_json(world):
    trash = {
        "trash_id": "abc", "trash_scores": {"default": 1750}, "name": "Bad Dual Groups",
        "includeCustomFormatWhenRenaming": False,
        "specifications": [
            {"name": "BadDual", "implementation": "ReleaseTitleSpecification", "negate": False, "required": True,
             "fields": {"value": "\\b(BadDual)\\b"}},
            {"name": "Not French", "implementation": "LanguageSpecification", "negate": True, "required": False,
             "fields": {"value": 2}},
        ],
    }
    bundle = parse_bundle([trash])
    assert bundle["source"]["app"] is None
    result = run(do_import("dst", "kb", bundle, apply=True))
    assert result["summary"]["create"] == 1 and result["summary"]["error"] == 0
    stored = next(c for c in world["dst"].state.db["cfs"] if c["name"] == "Bad Dual Groups")
    assert stored["specifications"][0]["fields"] == [{"name": "value", "value": "\\b(BadDual)\\b"}]
    # the API added a defaulted field: it must not show up as a difference
    again = run(do_import("dst", "kb", bundle, overwrite=True))
    assert again["summary"]["unchanged"] == 1


def test_parse_rejects_garbage():
    with pytest.raises(PorterError):
        parse_bundle({"hello": "world"})
    with pytest.raises(PorterError):
        parse_bundle({"format": "portarr", "version": 99})


def test_bad_api_key(world):
    async def go():
        async with ArrClient("http://dst", "wrong") as c:
            await c.status()

    with pytest.raises(ArrError, match="API key"):
        run(go())

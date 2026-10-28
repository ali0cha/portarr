"""A miniature TRaSH-Guides repository, same structure as the real one, to test and demo offline.

Qualities and languages match tests/fake_arr.py's Radarr.  Run as a server for the demo:
    python -m tests.fake_trash 7100      # then TRASH_GUIDES_URL=http://127.0.0.1:7100/Guides.tar.gz
"""
from __future__ import annotations

import io
import json
import sys
import tarfile
from typing import Any


def cf(trash_id: str, name: str, scores: dict, regex: str = "x") -> dict[str, Any]:
    return {
        "trash_id": trash_id, "trash_scores": scores, "name": name, "includeCustomFormatWhenRenaming": False,
        "specifications": [{"name": name, "implementation": "ReleaseTitleSpecification", "negate": False, "required": True,
                            "fields": {"value": regex}}],
    }


def profile(trash_id: str, name: str, **extra: Any) -> dict[str, Any]:
    return {
        "trash_id": trash_id, "name": name, "trash_description": "Line one<br>- line two", "group": 1,
        "upgradeAllowed": True, "cutoff": "WEB 1080p", "minFormatScore": 0, "cutoffFormatScore": 10000,
        "minUpgradeFormatScore": 1, "language": "Original",
        # the guides list qualities highest first, and do not mention every quality
        "items": [
            {"name": "Bluray-1080p", "allowed": True},
            {"name": "WEB 1080p", "allowed": True, "items": ["WEBDL-1080p", "WEBRip-1080p"]},
            {"name": "WEBDL-720p", "allowed": False},
        ],
        "formatItems": {"BR-DISK": "cf-br", "x265 (HD)": "cf-x265"},
        **extra,
    }


def group(trash_id: str, name: str, include: dict, formats: list, default: bool = False) -> dict[str, Any]:
    return {"name": name, "trash_id": trash_id, "trash_description": "A group", "default": default,
            "custom_formats": [{"name": n, "trash_id": i, "required": r, "default": d} for n, i, r, d in formats],
            "quality_profiles": {"include": include}}


def build_files() -> dict[str, Any]:
    radarr = {
        "radarr/quality-profile-groups/groups.json": [
            {"name": "Standard", "profiles": {"hd-bluray-web": "P1", "german-hd": "P2"}},
            {"name": "TEST", "profiles": {"internal": "PT"}},
        ],
        "radarr/quality-profiles/hd-bluray-web.json": profile("P1", "HD Bluray + WEB"),
        "radarr/quality-profiles/german-hd.json": profile("P2", "German HD", trash_score_set="german"),
        "radarr/quality-profiles/internal.json": profile("PT", "Internal test"),
        "radarr/cf/br-disk.json": cf("cf-br", "BR-DISK", {"default": -10000}, "BR.?DISK"),
        "radarr/cf/x265-hd.json": cf("cf-x265", "x265 (HD)", {"default": -10000, "german": 0}, "x265"),
        "radarr/cf/hdr.json": cf("cf-hdr", "HDR", {"default": 500}, "HDR"),
        "radarr/cf/dts.json": cf("cf-dts", "DTS", {"default": 100}, "DTS"),
        "radarr/cf/netflix.json": cf("cf-nf", "Netflix", {"default": 0}, "NF"),
        "radarr/cf-groups/hdr-formats.json": group("G-HDR", "[HDR] Formats", {"HD Bluray + WEB": "P1"},
                                                   [("HDR", "cf-hdr", False, True), ("DTS", "cf-dts", False, False)], default=True),
        "radarr/cf-groups/streaming.json": group("G-NF", "[Streaming] General", {"HD Bluray + WEB": "P1"},
                                                 [("Netflix", "cf-nf", False, False)]),
        "radarr/cf-groups/german-only.json": group("G-DE", "[German] Only", {"German HD": "P2"}, [("DTS", "cf-dts", False, True)], default=True),
    }
    sonarr = {
        "sonarr/quality-profile-groups/groups.json": [{"name": "Standard", "profiles": {"web-1080p": "S1"}}],
        "sonarr/quality-profiles/web-1080p.json": {**profile("S1", "WEB-1080p"), "language": None, "formatItems": {"BR-DISK": "scf-br"}},
        "sonarr/cf/br-disk.json": cf("scf-br", "BR-DISK", {"default": -10000}, "BR.?DISK"),
    }
    return {**radarr, **sonarr}


def make_tarball(extra_noise: bool = True) -> bytes:
    """A .tar.gz shaped like GitHub's archive of the repo (one top-level folder)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        def add(path: str, content: bytes) -> None:
            info = tarfile.TarInfo(f"Guides-master/{path}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        for path, data in build_files().items():
            add(f"docs/json/{path}", json.dumps(data).encode())
        if extra_noise:
            add("README.md", b"# not json")
            add("docs/json/radarr/cf/broken.json", b"{ this is not json")  # must not take the catalog down
            add("docs/json/guide-only/language.json", b"{}")  # other apps / folders are ignored
            add("docs/json/lidarr/cf/x.json", b"{}")
    return buf.getvalue()


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, Response

    api = FastAPI()
    blob = make_tarball()

    @api.get("/Guides.tar.gz")
    async def archive():
        return Response(blob, media_type="application/gzip")

    uvicorn.run(api, host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv) > 1 else 7100, log_level="warning")

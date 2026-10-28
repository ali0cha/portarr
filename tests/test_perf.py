"""Guards for the optimisations: independent reads run in parallel, status is read once, assets stay lean."""
import asyncio
import re
from pathlib import Path

import pytest

from app import main
from app.arr import ArrClient, ArrError, gather
from app.porter import Importer, export_bundle
from app.store import InstanceStore
from tests.fake_arr import Router, make_fake, make_fake_prowlarr

STATIC = Path(__file__).parent.parent / "app" / "static"


class Spy(Router):
    """Counts requests and how many were in flight at once."""

    def __init__(self, apps):
        super().__init__(apps)
        self.paths, self.inflight, self.peak = [], 0, 0
        self.writing, self.write_peak = 0, 0

    async def handle_async_request(self, request):
        self.paths.append(request.url.path)
        write = request.method != "GET"
        self.inflight += 1
        self.writing += write
        self.peak = max(self.peak, self.inflight)
        self.write_peak = max(self.write_peak, self.writing)
        try:
            await asyncio.sleep(0.01)  # long enough for sibling requests to overlap
            return await super().handle_async_request(request)
        finally:
            self.inflight -= 1
            self.writing -= write


@pytest.fixture
def spy():
    s = Spy({"radarr": make_fake("Radarr", "k", "source"), "target": make_fake("Radarr", "k", "target"),
             "prowlarr": make_fake_prowlarr("k", "source"), "ptarget": make_fake_prowlarr("k", "target")})
    ArrClient.transport_override = s
    yield s
    ArrClient.transport_override = None


def run(coro):
    return asyncio.run(coro)


def test_radarr_export_reads_in_parallel(spy):
    async def go():
        async with ArrClient("http://radarr", "k") as c:
            return await export_bundle(c)

    run(go())
    assert spy.peak >= 4, f"only {spy.peak} request(s) at once"  # formats, profiles, sizes and the two settings


def test_prowlarr_export_reads_in_parallel(spy):
    async def go():
        async with ArrClient("http://prowlarr", "k") as c:
            return await export_bundle(c)

    run(go())
    assert spy.peak >= 4  # tags, sync profiles, proxies, indexers


def test_status_is_read_once_per_client(spy):
    """The backup export and the import run on the same client: one /system/status between them."""
    async def go():
        async with ArrClient("http://radarr", "k") as c:
            bundle = await export_bundle(c)
        async with ArrClient("http://target", "k") as c:
            await export_bundle(c)  # the pre-write backup
            await Importer(c, bundle, None, True, False).run()

    run(go())
    assert spy.paths.count("/api/v3/system/status") == 2  # one per client, not one per step


def test_writes_stay_sequential(spy):
    """Radarr updates every profile on each custom format creation: concurrent POSTs would race."""
    async def go():
        async with ArrClient("http://radarr", "k") as c:
            bundle = await export_bundle(c)
        async with ArrClient("http://target", "k") as c:
            await Importer(c, bundle, {"customFormats": ["x265 (HD)", "Not French"]}, True, True).run()

    run(go())
    assert len([p for p in spy.paths if p.endswith("/customformat")]) >= 4  # 2 reads + the 2 creations
    assert spy.write_peak == 1  # the creations never overlap


def test_gather_cancels_siblings_when_one_fails():
    state = {"cancelled": False}

    async def slow():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            state["cancelled"] = True
            raise

    async def boom():
        await asyncio.sleep(0.01)
        raise ArrError("nope")

    async def go():
        with pytest.raises(ArrError):
            await gather(slow(), boom())
        return [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    leftover = run(go())
    assert state["cancelled"] and leftover == []  # nothing keeps running after the error


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(main, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(main, "store", InstanceStore(tmp_path / "instances.json"))
    with TestClient(main.app) as c:
        yield c


def test_large_responses_are_gzipped_and_small_ones_are_not(client):
    big = client.get("/app.js", headers={"Accept-Encoding": "gzip"})
    assert big.headers["content-encoding"] == "gzip"
    assert big.num_bytes_downloaded < len(big.content) / 2
    small = client.get("/api/version", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in small.headers


def test_every_font_in_the_css_exists_and_none_is_orphaned():
    css = (STATIC / "style.css").read_text("utf-8")
    declared = set(re.findall(r"url\((fonts/[^)]+)\)", css))
    on_disk = {f"fonts/{p.name}" for p in (STATIC / "fonts").glob("*.woff2")}
    assert declared == on_disk  # a missing file breaks text, an orphan is dead weight in every image


def test_interface_files_are_revalidated_but_fonts_are_cached(client):
    """After an image update the browser must not keep running the old app.js."""
    js = client.get("/app.js")
    assert js.headers["cache-control"] == "no-cache" and js.headers["etag"]
    again = client.get("/app.js", headers={"If-None-Match": js.headers["etag"]})
    assert again.status_code == 304 and again.content == b""  # revalidation costs almost nothing
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert "max-age" in client.get("/fonts/inter-latin-400.woff2").headers["cache-control"]

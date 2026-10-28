import asyncio

import httpx
import pytest

from app import main
from app.store import InstanceStore
from app.updates import UpdateChecker, is_newer, parse_version

URL = "http://updates.test/app/__init__.py"


def run(coro):
    return asyncio.run(coro)


class Server:
    """Serves the project's `__init__.py` and counts requests."""

    def __init__(self, body: str = '__version__ = "0.2.0"  # shown in the sidebar\n', status: int = 200, fail: bool = False):
        self.body, self.status, self.fail, self.hits = body, status, fail, 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.hits += 1
        if self.fail:
            raise httpx.ConnectError("offline")
        return httpx.Response(self.status, text=self.body)


def checker(server: Server, current: str = "0.1.0", **kw) -> UpdateChecker:
    return UpdateChecker(URL, current, transport=httpx.MockTransport(server), **kw)


def test_version_parsing_and_comparison():
    assert parse_version("0.1.0") == (0, 1, 0) and parse_version("v1.2") == (1, 2) and parse_version("main") is None
    assert is_newer("0.2.0", "0.1.0") and is_newer("0.10.0", "0.9.0")  # numbers, not text: 10 > 9
    assert is_newer("1.0", "0.9.9") and not is_newer("0.2", "0.2.0")  # 0.2 is 0.2.0
    assert not is_newer("0.1.0", "0.1.0") and not is_newer("0.1.0", "0.2.0")  # a build ahead of main is not "outdated"
    assert not is_newer("garbage", "0.1.0") and not is_newer("0.2.0", "dev")


def test_a_newer_release_is_reported():
    s = run(checker(Server()).status())
    assert s == {"enabled": True, "current": "0.1.0", "latest": "0.2.0", "available": True}


@pytest.mark.parametrize("current", ["0.2.0", "0.3.0"])
def test_same_or_newer_than_main_is_not_an_update(current):
    assert run(checker(Server(), current).status())["available"] is False


def test_the_result_is_cached_and_simultaneous_asks_cost_one_request():
    server = Server()
    c = checker(server)

    async def go():
        await asyncio.gather(*(c.status() for _ in range(6)))
        await c.status()

    run(go())
    assert server.hits == 1


def test_an_expired_result_is_fetched_again():
    server = Server()
    c = checker(server, ttl=0)

    async def go():
        await c.status()
        await c.status()

    run(go())
    assert server.hits == 2


@pytest.mark.parametrize("server", [
    Server(fail=True),                        # offline NAS
    Server(status=404),                       # repository moved
    Server(body="<html>not python</html>"),  # unexpected content
    Server(body='__version__ = "main"'),      # not a version number
])
def test_any_failure_is_silent(server):
    s = run(checker(server).status())
    assert s["latest"] is None and s["available"] is False


def test_a_failure_is_not_retried_on_every_page_load():
    server = Server(fail=True)
    c = checker(server, retry=3600)

    async def go():
        for _ in range(4):
            await c.status()

    run(go())
    assert server.hits == 1  # one attempt, then quiet until the retry delay passes


def test_after_the_retry_delay_it_tries_again_and_recovers():
    server = Server(fail=True)
    c = checker(server, retry=0)
    run(c.status())
    server.fail = False
    assert run(c.status())["available"] is True and server.hits == 2


def test_it_can_be_turned_off_and_then_makes_no_request():
    server = Server()
    s = run(checker(server, enabled=False).status())
    assert s["enabled"] is False and s["available"] is False and server.hits == 0


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(main, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(main, "store", InstanceStore(tmp_path / "instances.json"))
    with TestClient(main.app) as c:
        yield c


def test_the_api_exposes_the_status_and_where_to_read_how_to_update(client, monkeypatch):
    monkeypatch.setattr(main, "updates", checker(Server(), current="0.0.1"))
    body = client.get("/api/update").json()
    assert body["latest"] == "0.2.0" and body["available"] is True
    assert body["url"] == f"https://github.com/{main.REPO}#updating"


@pytest.mark.parametrize("name", ["evil/../x?y=1 #", "../..", "no-slash", "a/b/c", "https://x.test/a/b", "", "/x", "x/"])
def test_an_unusable_repository_name_falls_back_to_the_default(name):
    assert main.safe_repo(name) == "ali0cha/portarr"  # it is pasted into URLs


def test_a_fork_can_point_the_check_at_itself():
    assert main.safe_repo("someone/portarr-fork") == "someone/portarr-fork"

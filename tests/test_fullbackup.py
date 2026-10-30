"""Full backups: the application's own zip plus Portarr's JSON, and restoring them."""
import asyncio
import io
import json
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.arr import ArrClient, ArrError
from app.fullbackup import FullBackups
from app.porter import PorterError
from app.store import InstanceStore
from tests.fake_arr import Router, make_fake, make_fake_prowlarr


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def apps():
    fakes = {"src": make_fake("Radarr", "ka", "source"), "other": make_fake("Radarr", "kb", "target"),
             "sonarr": make_fake("Sonarr", "ks"), "prow": make_fake_prowlarr("kp", "source")}
    ArrClient.transport_override = Router(fakes)
    yield fakes
    ArrClient.transport_override = None


@pytest.fixture
def backups(tmp_path):
    return FullBackups(tmp_path / "full", poll=0, down_wait=1, up_wait=1)  # no waiting in tests


async def make(backups, host, key, name, **kw):
    async with ArrClient(f"http://{host}", key) as c:
        return await backups.create(c, name, **kw)


async def restore(backups, host, key, name, backup_id):
    async with ArrClient(f"http://{host}", key) as c:
        return await backups.restore(c, name, backup_id)


def names(app):
    return sorted(c["name"] for c in app.state.db["cfs"])


# ------------------------------------------------------------------ making one


def test_a_backup_holds_the_zip_the_json_and_what_they_are(backups, apps, tmp_path):
    meta = run(make(backups, "src", "ka", "Radarr 4K"))
    assert meta["instance"] == "Radarr 4K" and meta["app"] == "radarr" and meta["version"] == "5.0.0" and meta["reason"] == "manual"
    folder = tmp_path / "full" / meta["id"]
    assert sorted(p.name for p in folder.iterdir()) == ["backup.zip", "config.json", "meta.json"]

    with zipfile.ZipFile(folder / "backup.zip") as z:  # the application's own backup, byte for byte
        assert "config.xml" in z.namelist()
    assert meta["size"] == (folder / "backup.zip").stat().st_size
    bundle = json.loads((folder / "config.json").read_text())
    assert bundle["format"] == "portarr" and bundle["source"]["instanceName"] == "Radarr 4K"
    assert [c["name"] for c in bundle["customFormats"]] == ["BR-DISK", "Not French", "x265 (HD)"]  # the selective import still works
    assert backups.list() == [meta]


def test_it_waits_for_the_application_to_finish_its_backup(backups, apps):
    apps["src"].state.command_polls = 3
    meta = run(make(backups, "src", "ka", "Radarr"))
    assert meta["id"] and apps["src"].state.commands[1]["polls"] == 4


def test_a_failed_backup_leaves_nothing_behind(backups, apps, tmp_path):
    apps["src"].state.failing_backup = True
    with pytest.raises(PorterError, match="could not make its backup: Disk full"):
        run(make(backups, "src", "ka", "Radarr"))
    assert backups.list() == [] and list((tmp_path / "full").iterdir()) == []


def test_a_page_that_is_not_a_zip_is_refused(backups, apps, monkeypatch):
    async def login_page(self, path, dest):
        dest.write_text("<html>login</html>")
        return 19

    monkeypatch.setattr(ArrClient, "download", login_page)
    with pytest.raises(PorterError, match="did not return a backup file"):
        run(make(backups, "src", "ka", "Radarr"))
    assert backups.list() == []


def test_the_download_copes_with_a_url_base():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, content=b"PKdata") if request.url.path == "/radarr/backup/manual/a.zip" else httpx.Response(404)

    ArrClient.transport_override = httpx.MockTransport(handler)
    try:
        async def go(path):
            async with ArrClient("http://host/radarr", "k", app="radarr") as c:
                import tempfile, pathlib
                dest = pathlib.Path(tempfile.mkdtemp()) / "x.zip"
                return await c.download(path, dest)

        assert run(go("/backup/manual/a.zip")) == 6  # the path as some versions report it
        assert run(go("/radarr/backup/manual/a.zip")) == 6  # and with the URL base already in it
        with pytest.raises(ArrError):
            run(go("/backup/manual/missing.zip"))
    finally:
        ArrClient.transport_override = None
    assert set(seen) == {"/radarr/backup/manual/a.zip", "/radarr/backup/manual/missing.zip"}


def test_prowlarr_is_backed_up_too(backups, apps):
    meta = run(make(backups, "prow", "kp", "Prowlarr"))
    assert meta["app"] == "prowlarr" and meta["version"] == "1.30.0"


def test_listing_skips_unfinished_folders_and_deleting_only_removes_backups(backups, apps, tmp_path):
    first = run(make(backups, "src", "ka", "Radarr"))
    (tmp_path / "full" / "half-done").mkdir()  # no meta.json: interrupted
    (tmp_path / "full" / "someone-elses").mkdir()
    assert [m["id"] for m in backups.list()] == [first["id"]]
    for bad in ("half-done", "someone-elses", "..", "../x", "nope"):
        with pytest.raises(PorterError, match="Unknown backup"):
            backups.delete(bad)
    assert (tmp_path / "full" / "half-done").is_dir()
    backups.delete(first["id"])
    assert backups.list() == []


# ------------------------------------------------------------------ restoring one


def test_a_restore_brings_back_everything_and_keeps_a_way_back(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    before = names(apps["src"])
    apps["src"].state.db["cfs"].clear()  # the instance gets wrecked afterwards
    assert names(apps["src"]) == []

    result = run(restore(backups, "src", "ka", "Radarr", saved["id"]))
    assert result["restored"] == saved["id"] and result["restarted"] is True and result["apiKeyChanged"] is False
    assert names(apps["src"]) == before and apps["src"].state.restores == 1

    safety = [m for m in backups.list() if m["reason"] == "before-restore"]  # what the instance was like just before
    assert [m["id"] for m in safety] == [result["safety"]]
    with zipfile.ZipFile(backups.file(safety[0]["id"], "backup.zip")) as z:
        assert json.loads(z.read("db.json"))["cfs"] == []
    run(restore(backups, "src", "ka", "Radarr", result["safety"]))  # and the restore can itself be undone
    assert names(apps["src"]) == []


def test_it_says_when_the_restored_backup_has_another_api_key(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    apps["src"].state.restored_key = "key-of-the-backup"
    result = run(restore(backups, "src", "ka", "Radarr", saved["id"]))
    assert result["restarted"] is True and result["apiKeyChanged"] is True


def test_it_does_not_claim_a_restart_it_did_not_see(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    apps["src"].state.down_after_restore = 0  # the application never goes down
    result = run(restore(backups, "src", "ka", "Radarr", saved["id"]))
    assert result["restarted"] is False and apps["src"].state.restores == 1  # restored, but nothing is said about a restart

    apps["src"].state.down_after_restore = 10 ** 9  # it goes down and does not come back within the wait
    result = run(restore(backups, "src", "ka", "Radarr", saved["id"]))
    assert result["restarted"] is False and result["apiKeyChanged"] is False and apps["src"].state.restores == 2


def test_refusals_leave_the_target_untouched(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    with pytest.raises(PorterError, match="comes from Radarr: it cannot be restored on Sonarr"):
        run(restore(backups, "sonarr", "ks", "Sonarr", saved["id"]))
    apps["other"].state.version = "4.0.0"  # older than the backup's 5.0.0
    with pytest.raises(PorterError, match="newer than the target's 4.0.0"):
        run(restore(backups, "other", "kb", "Other", saved["id"]))
    with pytest.raises(PorterError, match="Unknown backup"):
        run(restore(backups, "src", "ka", "Radarr", "nope"))
    assert apps["other"].state.restores == apps["sonarr"].state.restores == 0
    assert [m["reason"] for m in backups.list()] == ["manual"]  # not even a safety backup was made


def test_nothing_is_replaced_when_the_safety_backup_fails(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    apps["src"].state.failing_backup = True
    with pytest.raises(PorterError, match="could not make its backup"):
        run(restore(backups, "src", "ka", "Radarr", saved["id"]))
    assert apps["src"].state.restores == 0


def test_a_backup_made_on_one_instance_restores_on_another_of_the_same_app(backups, apps):
    saved = run(make(backups, "src", "ka", "Radarr"))
    assert names(apps["other"]) == ["BR-DISK", "Some Other CF"]
    run(restore(backups, "other", "kb", "Other", saved["id"]))
    assert names(apps["other"]) == ["BR-DISK", "Not French", "x265 (HD)"]


# ------------------------------------------------------------------ the HTTP API


@pytest.fixture
def client(tmp_path, apps, monkeypatch):
    monkeypatch.setattr(main, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(main, "store", InstanceStore(tmp_path / "instances.json"))
    monkeypatch.setattr(main, "backup_dir", tmp_path / "backups")
    monkeypatch.setattr(main, "full_backups", FullBackups(tmp_path / "backups" / "full", poll=0, down_wait=1, up_wait=1))
    monkeypatch.setattr(main, "AUTH_USER", "")
    monkeypatch.setattr(main, "AUTH_PASSWORD", "")
    with TestClient(main.app) as c:
        yield c


def add(client, host, key, name):
    return client.post("/api/instances", json={"name": name, "url": f"http://{host}", "api_key": key}).json()["id"]


def test_the_api_makes_lists_downloads_and_deletes(client):
    iid = add(client, "src", "ka", "Radarr 4K")
    made = client.post(f"/api/instances/{iid}/full-backup")
    assert made.status_code == 200 and made.json()["instance"] == "Radarr 4K"
    backup_id = made.json()["id"]
    assert [m["id"] for m in client.get("/api/full-backups").json()] == [backup_id]

    zipped = client.get(f"/api/full-backups/{backup_id}/zip")
    assert zipped.headers["content-type"] == "application/zip" and zipfile.is_zipfile(io.BytesIO(zipped.content))
    assert backup_id in zipped.headers["content-disposition"]
    assert client.get(f"/api/full-backups/{backup_id}/config").json()["format"] == "portarr"
    assert client.get(f"/api/full-backups/{backup_id}/other").status_code == 404
    assert client.get("/api/full-backups/nope/zip").status_code == 400

    assert client.delete(f"/api/full-backups/{backup_id}").status_code == 200
    assert client.get("/api/full-backups").json() == []
    assert client.delete(f"/api/full-backups/{backup_id}").status_code == 400


def test_the_api_restores_only_when_asked_explicitly(client, apps):
    iid = add(client, "src", "ka", "Radarr 4K")
    backup_id = client.post(f"/api/instances/{iid}/full-backup").json()["id"]
    apps["src"].state.db["cfs"].clear()

    sure = client.post(f"/api/instances/{iid}/full-restore", json={"backup_id": backup_id})
    assert sure.status_code == 400 and "confirm" in sure.json()["detail"] and apps["src"].state.restores == 0
    done = client.post(f"/api/instances/{iid}/full-restore", json={"backup_id": backup_id, "confirm": True})
    assert done.status_code == 200 and done.json()["restarted"] is True and done.json()["restored"] == backup_id
    assert len(apps["src"].state.db["cfs"]) == 3
    assert client.post("/api/instances/nope/full-restore", json={"backup_id": backup_id, "confirm": True}).status_code == 404


def test_full_backups_do_not_appear_among_the_configuration_snapshots(client):
    iid = add(client, "src", "ka", "Radarr 4K")
    client.post(f"/api/instances/{iid}/full-backup")
    assert client.get("/api/backups").json() == []  # the snapshots made before each import are a separate list

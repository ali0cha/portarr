"""Scheduled full backups: when they are due, what they keep, and what a failing instance does to the others."""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import main
from app.arr import ArrClient
from app.fullbackup import FullBackups
from app.porter import PorterError
from app.schedule import BackupSchedule
from app.store import InstanceStore
from tests.fake_arr import Router, make_fake

UTC = timezone.utc


def run(coro):
    return asyncio.run(coro)


def at(day, hour=0, minute=0, month=10):
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


@pytest.fixture
def apps():
    fakes = {"src": make_fake("Radarr", "ka", "source"), "other": make_fake("Radarr", "kb", "target")}
    ArrClient.transport_override = Router(fakes)
    yield fakes
    ArrClient.transport_override = None


@pytest.fixture
def world(tmp_path, apps):
    store = InstanceStore(tmp_path / "instances.json")
    one = store.add({"name": "Radarr HD", "url": "http://src", "api_key": "ka", "app": "radarr"})
    two = store.add({"name": "Radarr 4K", "url": "http://other", "api_key": "kb", "app": "radarr"})
    backups = FullBackups(tmp_path / "full", poll=0)
    sched = BackupSchedule(tmp_path / "schedule.json", store, backups, lambda i: ArrClient(i["url"], i["api_key"], True, i.get("app")))
    sched.ids = (one["id"], two["id"])
    sched.backups = backups
    return sched


def config(sched, **kw):
    return {"enabled": True, "everyDays": 1, "time": "03:00", "keep": 7, "deleteRemote": False, "instances": list(sched.ids), **kw}


def scheduled(sched, iid=None):
    return [m for m in sched.backups.list() if m["reason"] == "scheduled" and (iid is None or m["instanceId"] == iid)]


# ------------------------------------------------------------------ the settings


def test_it_is_off_until_asked_and_nothing_is_due(world):
    st = world.status(at(30, 14))
    assert st["config"]["enabled"] is False and st["nextRun"] is None and st["lastRun"] is None
    assert run(world.tick(at(31, 4))) is False and world.backups.list() == []


@pytest.mark.parametrize("change, message", [
    ({"everyDays": 0}, "1 to 365 days"), ({"everyDays": "2"}, "1 to 365 days"), ({"time": "25:00"}, "look like 03:00"),
    ({"time": "3am"}, "look like 03:00"), ({"keep": 0}, "between 1 and 365"), ({"instances": []}, "at least one instance"),
])
def test_wrong_settings_are_refused_with_a_clear_message(world, change, message):
    with pytest.raises(PorterError, match=message):
        world.save(config(world, **change), at(30, 14))
    assert world.status()["config"]["enabled"] is False  # nothing was saved


def test_switching_it_on_does_not_back_up_at_once(world):
    st = world.save(config(world), at(30, 14))  # 14:00: today's 03:00 slot is already past
    assert st["lastRun"].startswith("2026-10-30T03:00") and st["nextRun"].startswith("2026-10-31T03:00")
    assert run(world.tick(at(30, 14, 1))) is False and world.backups.list() == []

    early = world.save(config(world, time="16:00"), at(30, 15))  # changing the time keeps the last run
    assert early["lastRun"].startswith("2026-10-30T03:00") and early["nextRun"].startswith("2026-10-31T16:00")


def test_unknown_and_deleted_instances_are_dropped(world):
    st = world.save(config(world, instances=[*world.ids, "nope", world.ids[0]]), at(30, 14))
    assert st["config"]["instances"] == list(world.ids)
    world.store.delete(world.ids[1])
    assert world.status(at(30, 15))["config"]["instances"] == [world.ids[0]]


# ------------------------------------------------------------------ when it runs


def test_it_runs_once_when_due_for_every_instance(world, apps):
    world.save(config(world), at(30, 14))
    assert run(world.tick(at(31, 2, 59))) is False
    assert run(world.tick(at(31, 3, 0))) is True

    made = scheduled(world)
    assert sorted(m["instance"] for m in made) == ["Radarr 4K", "Radarr HD"]
    assert {m["instanceId"] for m in made} == set(world.ids)
    st = world.status(at(31, 3, 1))
    assert st["lastRun"].startswith("2026-10-31T03:00") and st["nextRun"].startswith("2026-11-01T03:00")
    assert all(r["ok"] and r["backup"] for r in st["results"].values())
    assert run(world.tick(at(31, 3, 5))) is False  # not twice for the same slot
    assert len(scheduled(world)) == 2


def test_a_machine_that_was_off_backs_up_once_not_once_per_missed_day(world):
    world.save(config(world), at(30, 14))
    assert run(world.tick(at(3, 10, 0, month=11))) is True
    assert len(scheduled(world, world.ids[0])) == 1
    assert world.status(at(3, 10, 1, month=11))["lastRun"].startswith("2026-11-03T03:00")


def test_every_few_days(world):
    world.save(config(world, everyDays=3), at(30, 14))
    assert run(world.tick(at(1, 12, month=11))) is False  # two days later
    assert run(world.tick(at(2, 3, 0, month=11))) is True  # three days after the 30th's slot


def test_one_failing_instance_does_not_stop_the_others(world, apps):
    apps["src"].state.failing_backup = True
    world.save(config(world), at(30, 14))
    assert run(world.tick(at(31, 3, 0))) is True
    first, second = (world.status(at(31, 4))["results"][i] for i in world.ids)
    assert first["ok"] is False and "Disk full" in first["error"] and first["backup"] is None
    assert second["ok"] is True
    assert [m["instance"] for m in scheduled(world)] == ["Radarr 4K"]
    assert world.status(at(31, 4))["lastRun"].startswith("2026-10-31T03:00")  # it will try again tomorrow, not every minute


def test_the_background_loop_runs_what_is_due(world):
    long_ago = datetime.now(UTC) - timedelta(days=5)
    world.save(config(world, instances=[world.ids[0]]), long_ago)

    async def go():
        task = asyncio.create_task(world.loop(interval=0.01))
        for _ in range(200):
            await asyncio.sleep(0.02)
            if scheduled(world):
                break
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    run(go())
    assert len(scheduled(world)) == 1


# ------------------------------------------------------------------ what it keeps


async def manual(world, iid):
    inst = world.store.get(iid)
    async with ArrClient(inst["url"], inst["api_key"]) as c:
        return await world.backups.create(c, inst["name"], instance_id=iid)


def test_only_the_last_few_scheduled_backups_are_kept_and_the_others_are_never_touched(world):
    first = world.ids[0]
    run(manual(world, first))  # a backup made by hand is not part of the rotation
    world.save(config(world, keep=2, instances=[first]), at(30, 14))
    for n in range(5):  # five days in a row
        assert run(world.tick(at(31, 3, 0) + timedelta(days=n))) is True
    assert len(scheduled(world, first)) == 2
    newest = world.status(at(1, 5, month=12))["results"][first]["backup"]
    assert newest in [m["id"] for m in scheduled(world, first)]  # what is kept is the newest
    assert [m["reason"] for m in world.backups.list()].count("manual") == 1


def test_nothing_is_ever_pruned_below_one(world, apps):
    world.save(config(world, keep=1, instances=[world.ids[0]]), at(30, 14))
    for n in range(2):
        run(world.tick(at(31, 3, 0) + timedelta(days=n)))
    assert len(scheduled(world, world.ids[0])) == 1


def test_the_copy_left_on_the_application_is_removed_only_when_asked(world, apps):
    world.save(config(world, instances=[world.ids[0]]), at(30, 14))
    run(world.tick(at(31, 3, 0)))
    assert len(apps["src"].state.backups) == 1  # by default it stays

    world.save(config(world, instances=[world.ids[1]], deleteRemote=True), at(31, 4))
    run(world.tick(at(1, 3, 0, month=11)))
    assert apps["other"].state.backups == [] and len(scheduled(world, world.ids[1])) == 1  # downloaded, then removed there


# ------------------------------------------------------------------ the HTTP API


@pytest.fixture
def client(world, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(main, "store", world.store)
    monkeypatch.setattr(main, "backup_dir", tmp_path / "backups")
    monkeypatch.setattr(main, "full_backups", world.backups)
    monkeypatch.setattr(main, "backup_schedule", world)
    monkeypatch.setattr(main, "AUTH_USER", "")
    monkeypatch.setattr(main, "AUTH_PASSWORD", "")
    with TestClient(main.app) as c:
        c.sched = world
        yield c


def test_the_api_reads_and_saves_the_schedule(client):
    off = client.get("/api/backup-schedule").json()
    assert off["config"]["enabled"] is False and off["nextRun"] is None and "timezone" in off

    body = {"enabled": True, "everyDays": 2, "time": "04:30", "keep": 5, "deleteRemote": True, "instances": list(client.sched.ids)}
    saved = client.put("/api/backup-schedule", json=body)
    assert saved.status_code == 200 and saved.json()["config"] == body and saved.json()["nextRun"]
    assert json.loads(client.sched.path.read_text())["config"]["keep"] == 5
    assert client.put("/api/backup-schedule", json={**body, "time": "nope"}).status_code == 400
    assert client.put("/api/backup-schedule", json={**body, "instances": []}).status_code == 400

import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.arr import ArrClient
from app.store import InstanceStore
from tests.fake_arr import Router, make_fake, make_fake_prowlarr


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "store", InstanceStore(tmp_path / "instances.json"))
    monkeypatch.setattr(main, "backup_dir", tmp_path / "backups")
    monkeypatch.setattr(main, "AUTH_USER", "")
    monkeypatch.setattr(main, "AUTH_PASSWORD", "")
    apps = {
        "src": make_fake("Radarr", "ka", "source"),
        "dst": make_fake("Radarr", "kb", "target"),
        "prow": make_fake_prowlarr("kp", "source"),
    }
    ArrClient.transport_override = Router(apps)
    with TestClient(main.app) as c:
        c.fake = apps
        c.tmp = tmp_path
        yield c
    ArrClient.transport_override = None


def add(client, host, key, name):
    return client.post("/api/instances", json={"name": name, "url": f"http://{host}", "api_key": key})


def test_instance_lifecycle_never_leaks_api_key(client):
    r = add(client, "src", "ka", "Source")
    assert r.status_code == 200, r.text
    inst = r.json()
    assert inst["app"] == "radarr" and inst["has_key"] is True and "api_key" not in inst
    assert "ka" not in client.get("/api/instances").text
    assert json.loads((client.tmp / "instances.json").read_text())[0]["api_key"] == "ka"
    assert (client.tmp / "instances.json").stat().st_mode & 0o777 == 0o600
    # update without a key keeps the stored one
    r = client.put(f"/api/instances/{inst['id']}", json={"name": "Renamed", "url": "http://src", "api_key": ""})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"
    assert client.post(f"/api/instances/{inst['id']}/test").json()["app"] == "radarr"
    assert client.delete(f"/api/instances/{inst['id']}").status_code == 200
    assert client.get("/api/instances").json() == []


def test_bad_instances_are_rejected_and_not_saved(client):
    assert add(client, "src", "wrong", "x").status_code == 502
    assert client.post("/api/instances", json={"name": "x", "url": "ftp://src", "api_key": "k"}).status_code == 400
    assert client.post("/api/instances", json={"name": "x", "url": "http://nowhere", "api_key": "k"}).status_code == 502
    assert client.get("/api/instances").json() == []


def test_full_flow_with_backup(client):
    src = add(client, "src", "ka", "Source").json()["id"]
    dst = add(client, "dst", "kb", "Target").json()["id"]
    bundle = client.get(f"/api/instances/{src}/export").json()
    body = {"bundle": bundle, "overwrite": True}

    preview = client.post(f"/api/instances/{dst}/import/preview", json=body).json()
    assert preview["applied"] is False and "backup" not in preview
    assert client.get("/api/backups").json() == []

    result = client.post(f"/api/instances/{dst}/import/apply", json=body).json()
    assert result["applied"] is True and result["summary"]["error"] == 0
    backups = client.get("/api/backups").json()
    assert [b["name"] for b in backups] == [result["backup"]]
    # the backup is the *previous* state of the target and is itself a valid bundle
    saved = client.get(f"/api/backups/{result['backup']}").json()
    assert saved["format"] == "portarr" and [c["name"] for c in saved["customFormats"]] == ["BR-DISK", "Some Other CF"]
    assert client.get("/api/backups/..%2Finstances.json").status_code == 404
    assert client.get("/api/backups/nope.json").status_code == 404


def test_parse_endpoint(client):
    ok = client.post("/api/import/parse", json={"text": json.dumps({"name": "A", "specifications": []})})
    assert ok.status_code == 200 and ok.json()["customFormats"][0]["name"] == "A"
    assert client.post("/api/import/parse", json={"text": "{nope"}).status_code == 400
    assert client.post("/api/import/parse", json={"text": "{}"}).status_code == 400


def test_basic_auth(client, monkeypatch):
    monkeypatch.setattr(main, "AUTH_USER", "me")
    monkeypatch.setattr(main, "AUTH_PASSWORD", "s3cret")
    assert client.get("/api/instances").status_code == 401
    assert client.get("/healthz").status_code == 200
    assert client.get("/api/instances", auth=("me", "wrong")).status_code == 401
    assert client.get("/api/instances", auth=("me", "s3cret")).status_code == 200


def test_prowlarr_instance_is_detected_and_exportable(client):
    inst = add(client, "prow", "kp", "Prowlarr").json()
    assert inst["app"] == "prowlarr"
    bundle = client.get(f"/api/instances/{inst['id']}/export").json()
    assert bundle["source"]["app"] == "prowlarr"
    assert {i["name"] for i in bundle["indexers"]} == {"PublicHD", "PrivTracker"}
    assert "SUPER-SECRET" not in json.dumps(bundle)
    assert client.post(f"/api/instances/{inst['id']}/test").json()["app"] == "prowlarr"

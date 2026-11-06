# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Run with installed Texstage and BOTH example wheels, never an editable plugin."""
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

from texstage.build.builder import BuildOptions, build
from texstage.build.latex import compile_deck
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.policy import catalog_for, enable
from texstage.plugins.runtime import Runtime
from texstage.server.app import ServerConfig, create_app
from texstage.server.bundles import BundleError, load_bundle

TYPE = "org.example.coordinates.plane"
KEY = "synthetic-presenter-key"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    root = tmp_path_factory.mktemp("plugins-installed")
    providers = discover()
    assert {p.id for p in providers} == {"org.example.distance", "org.example.coordinates"}
    profile = root / "profile"
    for p in providers: enable(profile, p.id, p.version, p.payload)
    catalog = catalog_for(profile)
    if other := os.environ.get("TEXSTAGE_TEST_BUNDLE"):
        source = Path(other).resolve()
        shutil.copytree(source.parent, root / "out")
        result = SimpleNamespace(bundle=root / "out" / source.name,
                                 static=root / "out/plane-static.pptx", pptx=root / "out/plane.pptx")
    else:
        tex = root / "plane.tex"
        shutil.copyfile(Path(__file__).parents[1] / "examples/plane.tex", tex)
        result = build(tex, root / "out", BuildOptions(stage=True, plugin_data=profile, key=KEY))
        for mode in ("handout", "solutions"):
            compile_deck(tex, mode, root / "out/build", plugins=catalog)
    return root, profile, catalog, result


def test_wheel_build_and_bundle_preflight(world):
    root, profile, catalog, result = world
    with pytest.raises(BundleError, match="missing or mismatched"):
        load_bundle(result.bundle)
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert bundle.deck_json["format"] == 3
    assert len(bundle.deck_json["plugins"]) == 2
    assert all("resources" not in p for p in bundle.deck_json["plugins"])
    assert bundle.items[TYPE]["walk"]["xmin"] == -5
    assert "private" not in bundle.items[TYPE]["walk"]
    assert result.static.is_file() and result.pptx.is_file()
    assert (root / "out/build/plane-solutions.pdf").is_file()
    assert (root / "out/build/plane-handout.pdf").is_file()
    assert not any(n.startswith("texstage_example_") for n in sys.modules)
    changed = json.loads((profile / "plugins.json").read_text())
    changed["enabled"][0]["payload"] = "0" * 64
    other = root / "disabled"; other.mkdir()
    (other / "plugins.json").write_text(json.dumps(changed))
    with pytest.raises(PluginError): catalog_for(other)


def test_geometry_and_loaded_style_are_verified(world):
    root, profile, catalog, result = world
    bundle = load_bundle(result.bundle, catalog=catalog)
    box = next(b for s in bundle.deck_json["slides"] for b in s.get("live", []) if b["type"] == TYPE)
    r = box["rects"]["box"]
    assert all(0 <= r[k] <= 1 for k in ("x", "y", "w", "h"))
    from texstage.build.plugins import verify_styles
    provider, spec = catalog.capability(TYPE)
    local = root / Path(spec["latex_packages"][0]).name
    local.write_bytes(provider.resources[spec["latex_packages"][0]])
    recorder = root / "shadow.fls"; recorder.write_text(f"INPUT {local}\n")
    with pytest.raises(PluginError, match="unapproved plugin style"):
        verify_styles(catalog, recorder, root)


def test_actor_scoped_correlations_in_installed_coordinate_wheel(world, tmp_path):
    _, _, catalog, result = world
    bundle = load_bundle(result.bundle, catalog=catalog)
    runtime = Runtime(tmp_path / "actors.sqlite3", catalog)
    try:
        runtime.ensure("session", TYPE, "walk", {"public": bundle.items[TYPE]["walk"],
                       **bundle.keys["items"][TYPE]["walk"]})
        runtime.activate("session", {(TYPE, "walk")})
        command = {"type": TYPE, "item": "walk", "operation": "submit-point", "epoch": 1,
                   "expected_revision": 1, "request_id": "same-request-from-two-phones", "payload": {"x": 3, "y": 4}}
        a = runtime.command("session", "alice", "participant", command)
        b = runtime.command("session", "bob", "participant", command)
        assert a["accepted"] and b["accepted"] and set(a["jobs"]).isdisjoint(b["jobs"])
        assert runtime.command("session", "alice", "participant", command) == a
        assert len(runtime.lease("session", "presenter")) == 2
    finally:
        runtime.close()


def recv(ws, kind, condition=lambda m: True):
    for _ in range(100):
        message = ws.receive_json()
        if message["t"] == "plugin.error": pytest.fail(str(message))
        if message["t"] == kind and condition(message): return message
    pytest.fail(f"no {kind} message")


def test_authenticated_phone_to_evaluator_to_projector(world, tmp_path):
    root, profile, catalog, result = world
    shutil.copytree(profile, tmp_path / "profile")
    profile = tmp_path / "profile"
    b = load_bundle(result.bundle, catalog=catalog)
    cfg = ServerConfig(bundles=[result.bundle], data_dir=profile, public_url="http://testserver", presenter_key=KEY)
    app = create_app(cfg)
    with TestClient(app) as client, client.websocket_connect("/ws") as host, client.websocket_connect("/ws") as phone:
        host.send_json({"t": "hello", "role": "stage", "key": KEY, "deck": b.deck, "bundle": b.id, "id": "hello"})
        welcome = recv(host, "welcome"); sid = welcome["session"]
        state = recv(host, "state"); pin = state["session"]["pin"]
        slide = next(s["id"] for s in b.deck_json["slides"] if any(x["type"] == TYPE for x in s.get("live", [])))
        host.send_json({"t": "slide", "slide": slide, "id": "slide"}); recv(host, "ok")
        phone.send_json({"t": "join", "pin": pin, "nickname": "Alice", "id": "join"})
        joined = recv(phone, "welcome")
        ps = recv(phone, "state", lambda m: bool(m.get("plugins", {}).get("items")))
        v = ps["plugins"]["items"][0]["views"]["participant-input"]
        assert "answer" not in v["data"]
        command = {"type": TYPE, "item": "walk", "operation": "submit-point", "epoch": v["epoch"],
                   "expected_revision": v["revision"], "request_id": "phone-point-0001", "payload": {"x": 0, "y": 5}}
        phone.send_json({"t": "plugin.command", "id": "point", "command": command})
        receipt = recv(phone, "ok")["receipt"]; assert receipt["accepted"]
        phone.send_json({"t": "plugin.command", "id": "retry", "command": command})
        assert recv(phone, "ok")["receipt"] == receipt
        phone.send_json({"t": "plugin.work", "id": "forbidden"}); assert recv(phone, "error")["error"] == "plugin"
        phone.send_json({"t": "plugin.command", "id": "forged-reveal", "command": command | {
            "operation": "reveal", "request_id": "forged-reveal", "payload": {}}})
        assert recv(phone, "error")["error"] == "plugin"
        host.send_json({"t": "plugin.work", "id": "work"})
        job = recv(host, "ok")["jobs"][0]
        assert job["binding"]["engine"] == "org.example.distance.euclidean"
        assert job["engine"]["url"].startswith("/plugins/")
        outcome = {"status": "ok", "key": "0" * 16, "namespace": job["namespace"],
                   "summary": {"kind": "text", "text": "Distance from the origin: 5.00"}}
        host.send_json({"t": "plugin.result", "id": "result", "result": {
            "id": job["id"], "generation": job["generation"], "epoch": job["epoch"], "outcome": outcome}})
        assert recv(host, "ok")["accepted"]
        ps = recv(phone, "state", lambda m: m.get("plugins", {}).get("items", [{}])[0].get("views", {}).get("participant-input", {}).get("data", {}).get("own", {}).get("status") == "ok")
        assert "correct" not in ps["plugins"]["items"][0]["views"]["participant-input"]["data"]["own"]
        row = app.state.server.plugins.runtime._item(sid, TYPE, "walk")
        host.send_json({"t": "plugin.command", "id": "reveal", "command": command | {
            "operation": "reveal", "request_id": "teacher-reveal", "expected_revision": row["revision"], "payload": {}}})
        recv(host, "ok")
        ps = recv(phone, "state", lambda m: m.get("plugins", {}).get("items", [{}])[0].get("views", {}).get("participant-input", {}).get("data", {}).get("revealed"))
        assert not ps["plugins"]["items"][0]["views"]["participant-input"]["data"]["own"]["correct"]
        # (0,5) and (3,4) have the same distance, but they are different points.
        with client.websocket_connect("/ws") as projector:
            projector.send_json({"t": "hello", "role": "display", "key": KEY, "deck": b.deck, "bundle": b.id, "id": "display"})
            recv(projector, "welcome")
            shown = recv(projector, "state")["plugins"]["items"][0]
            assert set(shown["views"]) == {"projector-overlay"}
            projector.send_json({"t": "plugin.command", "id": "denied", "command": command})
            recv(projector, "error")
        assert client.get(f"/api/archive/{sid}/plugins.json").status_code == 403
        assert client.get(f"/api/archive/{sid}/plugins.json", headers={"X-Texquiz-Key": KEY}).status_code == 200
        response = client.get(job["engine"]["url"])
        assert response.status_code == 200 and response.headers["x-content-type-options"] == "nosniff"
        assert client.get(job["engine"]["url"].rsplit("/web/", 1)[0] + "/__init__.py").status_code == 404
        assert "connect-src 'none'" in client.get("/static/stage/plugin-evaluator-worker.js").headers["content-security-policy"]

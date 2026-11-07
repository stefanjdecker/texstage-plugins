# SPDX-License-Identifier: Apache-2.0
"""Portable handoffs fail closed on altered bytes, paths and provenance."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("handoff", Path(__file__).parents[1] / "query_plan_handoff.py")
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)
SHA = "a" * 40


@pytest.fixture
def bundle(tmp_path):
    for name in ("host/core-py3-none-any.whl", "plugins/plugin-py3-none-any.whl",
                 "plugins/plugin.tar.gz", "requirements/dev.txt", "requirements/build.txt",
                 "lesson.bundle/deck.json"):
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fixture")
    data = {"format": 1, "host_commit": SHA, "host_wheel": "host/core-py3-none-any.whl",
            "plugin_wheel": "plugins/plugin-py3-none-any.whl", "plugin_sdist": "plugins/plugin.tar.gz",
            "bundle": "lesson.bundle", "files": handoff.inventory(tmp_path)}
    (tmp_path / "handoff.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def test_verifies_exact_inventory_and_commit(bundle):
    assert handoff.verify(bundle, SHA)["host_commit"] == SHA
    with pytest.raises(AssertionError, match="Wrong host commit"):
        handoff.verify(bundle, "b" * 40)


@pytest.mark.parametrize("change", ["alter", "remove", "add", "nested-manifest"])
def test_detects_all_byte_changes(bundle, change):
    if change == "alter":
        (bundle / "lesson.bundle/deck.json").write_bytes(b"changed")
    elif change == "remove":
        (bundle / "lesson.bundle/deck.json").unlink()
    elif change == "add":
        (bundle / "extra").write_bytes(b"extra")
    else:
        (bundle / "lesson.bundle/handoff.json").write_bytes(b"extra")
    with pytest.raises(AssertionError, match="bytes differ"):
        handoff.verify(bundle)


@pytest.mark.parametrize("path", ["", "../outside", "/absolute", "a//b", "a/./b", "C:/x", "a\\b"])
def test_rejects_nonportable_or_escaping_paths(bundle, path):
    data = json.loads((bundle / "handoff.json").read_text())
    data["files"][path] = {"sha256": "0" * 64, "size": 0}
    (bundle / "handoff.json").write_text(json.dumps(data))
    with pytest.raises(ValueError):
        handoff.verify(bundle)


@pytest.mark.parametrize("pin", ["main", "v1", "abc123", "A" * 40, "a" * 39])
def test_requires_full_immutable_commit(pin):
    with pytest.raises(ValueError):
        handoff.commit(pin)


def test_installed_identity_cannot_drift(monkeypatch):
    identity = {"provider": {"id": handoff.PROVIDER, "version": "0.4.0", "payload": "abc"},
                "host_version": "0.2.1.dev3", "host_resources_sha256": "def"}
    monkeypatch.setattr(handoff, "installed", lambda: copy.deepcopy(identity))
    handoff.check_installed(identity)
    for key in identity:
        changed = dict(identity, **{key: "different"})
        with pytest.raises(AssertionError, match="Installed artifact differs"):
            handoff.check_installed(changed)


def test_workflow_uses_pinned_host_and_independent_artifact_consumers():
    import re
    import yaml
    path = Path(__file__).parents[2] / ".github/workflows/query-plan-conformance.yml"
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    pin = workflow["on"]["workflow_dispatch"]["inputs"]["texstage_commit"]
    assert pin["required"] == "true" and "default" not in pin
    assert workflow["permissions"] == {"contents": "read"}
    jobs = workflow["jobs"]
    assert jobs["browser-consumer"]["strategy"]["fail-fast"] == "false"
    assert set(jobs["browser-consumer"]["strategy"]["matrix"]["browser"]) == {"chromium", "firefox", "webkit"}
    for name, job in jobs.items():
        if name != "linux-producer":
            assert job["needs"] == "linux-producer"
            assert any("query_plan_handoff.py install handoff" in s.get("run", "") for s in job["steps"])
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"actions/[a-z-]+@[a-f0-9]{40}", step["uses"])
    producer = "\n".join(s.get("run", "") for s in jobs["linux-producer"]["steps"])
    assert "texlive-lang-german" in producer
    assert "--require-hashes" in producer and "--only-binary=:all:" in producer
    assert "rev-parse HEAD" in producer and "HOST_COMMIT" in producer

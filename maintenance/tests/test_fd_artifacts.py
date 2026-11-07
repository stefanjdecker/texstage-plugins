# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("fd_artifacts", Path(__file__).parents[1] / "fd_artifacts.py")
artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifacts)
PIN = "a" * 40


@pytest.fixture
def handoff(tmp_path):
    names = {"host_wheel": "wheels/texstage-1-py3-none-any.whl",
             "plugin_wheel": "wheels/fd-1-py3-none-any.whl", "plugin_sdist": "wheels/fd-1.tar.gz"}
    for name in [*names.values(), "requirements/dev.txt", "requirements/build.txt"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"producer artifact")
    for language in ("en", "de"):
        path = tmp_path / f"bundles/{language}/lesson.bundle/deck.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"language": language}))
    data = {"format": 1, "host_commit": PIN, **names, "files": artifacts.inventory(tmp_path)}
    (tmp_path / "handoff.json").write_text(json.dumps(data))
    return tmp_path


def test_exact_bytes_and_host_pin_are_required(handoff):
    assert artifacts.verify(handoff, PIN)["host_commit"] == PIN
    with pytest.raises(AssertionError, match="Wrong host"):
        artifacts.verify(handoff, "b" * 40)
    (handoff / "wheels/fd-1-py3-none-any.whl").write_bytes(b"modified")
    with pytest.raises(AssertionError, match="Artifact bytes"):
        artifacts.verify(handoff, PIN)


@pytest.mark.parametrize("change", ["extra", "missing"])
def test_extra_and_missing_entries_are_rejected(handoff, change):
    if change == "extra":
        (handoff / "unexpected.txt").write_text("unreviewed")
    else:
        (handoff / "requirements/dev.txt").unlink()
    with pytest.raises(AssertionError, match="Artifact bytes"):
        artifacts.verify(handoff, PIN)


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a//b", "C:/escape", "a\\b", "./x"])
def test_unsafe_inventory_paths_are_rejected(handoff, name):
    path = handoff / "handoff.json"
    data = json.loads(path.read_text())
    data["files"][name] = {"sha256": "0" * 64, "size": 0}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="path"):
        artifacts.verify(handoff, PIN)


@pytest.mark.parametrize("pin", ["main", "v1", "a" * 39, "A" * 40, "a" * 41])
def test_release_pins_cannot_float(pin):
    with pytest.raises(ValueError, match="40-character"):
        artifacts.commit(pin)

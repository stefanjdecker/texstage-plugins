# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("er_artifacts", Path(__file__).parents[1] / "er_artifacts.py")
artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifacts)
COMMIT = "a" * 40


def handoff(tmp_path):
    (tmp_path / "host.whl").write_bytes(b"same portable wheel")
    artifacts.create(tmp_path, COMMIT)
    return tmp_path


def test_identical_consumer_and_wrong_revision(tmp_path):
    root = handoff(tmp_path)
    assert artifacts.verify(root, COMMIT)["host_commit"] == COMMIT
    with pytest.raises(ValueError): artifacts.verify(root, "b" * 40)
    with pytest.raises(ValueError): artifacts.create(root, "main")


@pytest.mark.parametrize("change", ["tamper", "missing", "extra"])
def test_reject_changed_bytes_or_inventory(tmp_path, change):
    root = handoff(tmp_path)
    if change == "tamper": (root / "host.whl").write_bytes(b"changed wheel")
    if change == "missing": (root / "host.whl").unlink()
    if change == "extra": (root / "stale.whl").write_bytes(b"stale wheel")
    with pytest.raises(ValueError): artifacts.verify(root, COMMIT)


@pytest.mark.parametrize("name", ["../outside", "/outside", "C:/outside", "dir\\outside", "./host.whl"])
def test_reject_nonportable_manifest_paths(tmp_path, name):
    root = handoff(tmp_path)
    data = json.loads((root / artifacts.MANIFEST).read_text())
    data["sha256"] = {name: "0" * 64}
    (root / artifacts.MANIFEST).write_text(json.dumps(data))
    with pytest.raises(ValueError): artifacts.verify(root, COMMIT)


def test_er_schema_generator_preserves_the_current_packaged_contract(tmp_path):
    root = Path(__file__).parents[2]
    package = tmp_path / 'plugins/er-decisions'
    shutil.copytree(root / 'plugins/er-decisions', package,
                    ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '*.egg-info', 'build', 'dist'))
    script = tmp_path / 'maintenance/build_er_lesson_schemas.py'
    script.parent.mkdir()
    shutil.copyfile(root / 'maintenance/build_er_lesson_schemas.py', script)
    files = [package / 'texstage-plugin.json', *sorted((package / 'texstage_er_decisions/schemas').rglob('*.json'))]
    # Git's Windows checkout policy may use CRLF; normalize only line endings.
    before = {path: path.read_text(encoding='utf-8') for path in files}
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
    assert {path: path.read_text(encoding='utf-8') for path in files} == before

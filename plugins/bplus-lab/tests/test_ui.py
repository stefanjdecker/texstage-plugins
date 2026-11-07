# SPDX-License-Identifier: Apache-2.0
"""UI helper checks resolve the installed wheel, never source-package imports."""
import json
from pathlib import Path
import subprocess
from test_engine import probe, exercise
from texstage_bplus_lab import model

ROOT = Path(__file__).resolve().parents[3]


def test_installed_editor_roundtrips_cancellable_replay_and_geometry(tmp_path):
    provider, _ = probe.installed()
    fixtures = probe.fixture(provider, "design-cases.json")
    cases = [{"seed": exercise(fixtures, row), "answer": row["answer"],
              "facts": model.analyze(exercise(fixtures, row), row["answer"])} for row in fixtures["cases"]]
    for name in ("empty", "last", "large", "cascade", "shrink"):
        source = json.loads((ROOT / "examples/bplus/activities" / (name + ".json")).read_text(encoding="utf-8"))
        cases.append({"seed": source["exercise"], "answer": source["worked"]["answer"],
                      "facts": model.analyze(source["exercise"], source["worked"]["answer"])})
    config = {"cases": cases, **{key: (provider.root / ("texstage_bplus_lab/web/" + module)).as_uri()
              for key, module in (("editor", "editor-model.mjs"), ("tree", "tree-view.mjs"), ("locale", "locale.mjs"))}}
    path = tmp_path / "ui-helpers.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    result = subprocess.run(["node", str(ROOT / "maintenance/check_bplus_editor.mjs"), str(path)],
                            check=True, text=True, capture_output=True)
    report = json.loads(result.stdout)
    assert report["roundtrips"] == report["replays"] == len(cases)
    import os
    output = Path(os.environ.get("BPLUS_REPORT_DIR", tmp_path))
    output.mkdir(parents=True, exist_ok=True)
    (output / "ui-helpers.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

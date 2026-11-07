# SPDX-License-Identifier: Apache-2.0
"""Build and verify prepared editions using an installed Query-plan wheel."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
from unittest.mock import patch

from texstage.build import authoring
from texstage.build.builder import BuildOptions, build
from texstage.build.compiler import compile_latex
from texstage.build.latex import compile_deck
from texstage.build.pdf import Pdf
from texstage.plugins.catalog import Catalog
from texstage.plugins.policy import enable
from texstage.server.bundles import load_bundle

from query_plan_probe import installed

ROOT = Path(__file__).resolve().parents[1]
TYPE = "io.github.stefanjdecker.queryplan.challenge"


def pdf_text(path):
    with Pdf(path) as pdf:
        return " ".join(page.text() for page in pdf)


def verify(output):
    """Keep all artifacts in a new directory; never alter the source example."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    provider, _ = installed()
    deck, out, profile = output / "deck", output / "out", output / "profile"
    shutil.copytree(ROOT / "examples/query-plan", deck)
    catalog = Catalog([provider])
    enable(profile, provider.id, provider.version, provider.payload)
    calls = []
    class MeasuredWorkers(authoring.Workers):
        def call(self, *args, **kwargs):
            started = time.perf_counter()
            result = super().call(*args, **kwargs)
            if "prepare_source" in args or kwargs.get("operation") == "prepare_source":
                calls.append(round((time.perf_counter() - started) * 1000, 3))
            return result
    options = BuildOptions(stage=True, key="query-plan-test-key",
                           activities=deck / "lesson.activities.json", plugin_data=profile, height=540)
    with patch.object(authoring, "Workers", MeasuredWorkers):
        result = build(deck / "lesson.tex", out, options)
    assert not result.problems, result.problems
    assert len(calls) == 4, calls
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert set(bundle.items[TYPE]) == {"selective", "broad", "library", "memory"}
    public = json.dumps(bundle.deck_json, sort_keys=True)
    for key in ('"reference"', '"worked"', '"explanation"', '"evaluations"'):
        assert key not in public, key
    assert bundle.file("keys.json") is None
    assert not list(result.bundle.rglob("*.tex"))
    assert not list(result.bundle.rglob("*.activities.json"))
    assert result.static.is_file()
    handout = compile_deck(deck / "lesson.tex", "handout", out, plugins=catalog, preparation=options.preparation)
    solutions = out / "build/lesson-solutions.pdf"
    for path in (handout.pdf, result.stage.pdf):
        assert "One worked plan" not in pdf_text(path)
        assert "Starting plan" in pdf_text(path)
    assert "One worked plan" in pdf_text(solutions)
    for item_id in bundle.items[TYPE]:
        item = bundle.items[TYPE][item_id]
        private = bundle.keys["items"][TYPE][item_id]["private"]
        assert private["reference"]["cost"] <= item["baseline_analysis"]["cost"]
    exported = options.preparation.export(deck / "lesson.tex", catalog)
    artifacts = {"handout": str(handout.pdf), "solutions": str(solutions), "stage": str(result.stage.pdf),
                 "powerpoint": str(result.static), "bundle": str(result.bundle)}
    for edition in ("handout", "solutions"):
        direct = compile_latex(exported[edition], output_dir=out / ("direct-" + edition), passes=2)
        assert direct.returncode == 0, direct.stdout[-3000:]
        assert ("One worked plan" in pdf_text(direct.pdf)) == (edition == "solutions")
        artifacts["direct-" + edition] = str(direct.pdf)
    report = {"provider": provider.requirement(), "prepare_calls": len(calls),
              "prepare_ms": calls, "artifacts": artifacts, "exported": {k: str(v) for k, v in exported.items()},
              "checks": ["live bundle privacy", "exercise/solution separation", "static PowerPoint",
                         "handout PDF", "solutions PDF", "direct pdfLaTeX editions"]}
    report["sha256"] = {k: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                        for k, p in artifacts.items() if Path(p).is_file()}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="A new disposable directory")
    args = parser.parse_args()
    print(json.dumps(verify(args.output), indent=2))

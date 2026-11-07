# SPDX-License-Identifier: Apache-2.0
"""Build bilingual transaction prepared editions using installed host/provider wheels."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
from unittest.mock import patch

import pypdfium2 as pdfium
from pptx import Presentation
from texstage.build import authoring
from texstage.build.builder import BuildOptions, build
from texstage.build.compiler import compile_latex
from texstage.build.latex import compile_deck
from texstage.build.pdf import Pdf
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.policy import enable
from texstage.server.bundles import load_bundle
from texstage.plugins.catalog import discover

def installed():
    providers = discover()
    assert {p.id for p in providers} == {"io.github.stefanjdecker.transactionengine", "io.github.stefanjdecker.transactionactivity"}
    for p in providers: p.verify()
    return providers

ROOT = Path(__file__).resolve().parents[1]
TYPE = "io.github.stefanjdecker.transactionactivity.schedule"


def pdf_text(path):
    with Pdf(path) as document:
        return " ".join(page.text() for page in document)


def inspect_pdf(path, output):
    output.mkdir(parents=True, exist_ok=True)
    with pdfium.PdfDocument(path) as document:
        for index, page in enumerate(document):
            width, height = page.get_size()
            text = page.get_textpage()
            for i in range(text.count_chars()):
                if not text.get_text_range(i, 1).strip():
                    continue
                left, bottom, right, top = text.get_charbox(i)
                assert min(left, bottom) >= -1 and right <= width + 1 and top <= height + 1, (path, index, i)
            page.render(scale=2).to_pil().save(output / f"page-{index + 1}.png")
        return len(document)


def verify(output, deck_name, language):
    """Require a fresh output directory; never mutate the example sources."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    providers = installed()
    provider = next(p for p in providers if p.id.endswith('transactionactivity'))
    deck, out, profile = output / "deck", output / "out", output / "profile"
    shutil.copytree(ROOT / "examples/transactions", deck)
    catalog = Catalog(providers)
    for p in providers: enable(profile, p.id, p.version, p.payload)
    filename = deck_name + ("-de" if language == "de" else "") + ".tex"
    sidecar = deck / f"{deck_name}.{language}.activities.json"
    item_ids = {r["id"] for r in json.loads(sidecar.read_text(encoding="utf-8"))["items"]}
    calls = []

    class MeasuredWorkers(authoring.Workers):
        def call(self, *args, **kwargs):
            started = time.perf_counter()
            result = super().call(*args, **kwargs)
            if "prepare_source" in args or kwargs.get("operation") == "prepare_source":
                calls.append(round((time.perf_counter() - started) * 1000, 3))
            return result

    options = BuildOptions(stage=True, key="transactions-prepared-test", activities=sidecar, plugin_data=profile, height=900)
    with patch.object(authoring, "Workers", MeasuredWorkers):
        result = build(deck / filename, out, options)
        assert not result.problems, result.problems
        handout = compile_deck(deck / filename, "handout", out, plugins=catalog, preparation=options.preparation)
    assert len(calls) == len(item_ids), calls
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert set(bundle.items[TYPE]) == item_ids
    public = json.dumps(bundle.deck_json, sort_keys=True)
    for key in ('"worked"', '"analysis"', '"explanation"', '"evaluations"', '"exercise_digest"'):
        assert key not in public, key
    # `feedback: staged` is a public policy, never an answer or verdict.
    for item in bundle.items[TYPE].values():
        assert item['exercise']['task']['feedback'] == 'staged'
        assert 'own' not in item and 'final' not in item and 'diagnosis' not in item
    assert bundle.file("keys.json") is None
    assert not list(result.bundle.rglob("*.tex")) and not list(result.bundle.rglob("*.activities.json"))
    assert result.static.is_file()
    solutions = out / "build" / (Path(filename).stem + "-solutions.pdf")
    heading = "Geprüfte Lösungen" if language == "de" else "Checked solutions"
    for path in (handout.pdf, result.stage.pdf):
        assert heading not in pdf_text(path)
    assert pdf_text(solutions).count(heading) == len(item_ids)
    for item_id in item_ids:
        private = bundle.keys["items"][TYPE][item_id]["private"]
        assert len(private["worked"]["repairs"]) >= 2
        assert "worked" not in bundle.items[TYPE][item_id]
    artifacts = {"handout": handout.pdf, "solutions": solutions, "stage": result.stage.pdf,
                 "powerpoint": result.static, "bundle": result.bundle}
    exported = options.preparation.export(deck / filename, catalog)
    for edition in ("handout", "solutions", "present"):
        direct = compile_latex(exported[edition], output_dir=out / ("direct-" + edition), passes=2)
        assert direct.returncode == 0, direct.stdout[-4000:]
        assert (heading in pdf_text(direct.pdf)) == (edition == "solutions")
        assert "Overfull" not in direct.log_text, direct.log_text[-4000:]
        artifacts["direct-" + edition] = direct.pdf
        options.preparation.validate_compile(direct.pdf.with_suffix(".tpa"))
    counts = {edition: inspect_pdf(path, output / "rendered" / edition)
              for edition, path in artifacts.items() if path.suffix == ".pdf"}
    expected_pages = len(item_ids) + (1 if deck_name == "lesson" else 0)
    assert set(counts.values()) == {expected_pages}, counts
    presentation = Presentation(result.static)
    assert len(presentation.slides) == expected_pages
    for index, slide in enumerate(presentation.slides):
        images = [s.image.blob for s in slide.shapes if hasattr(s, "image")]
        assert images, "Static slide has no exercise image"
        # Inspect the actual export media, not only a separately rendered PDF.
        for n, raw in enumerate(images):
            target = output / "rendered" / "powerpoint" / f"slide-{index + 1}-{n}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    identities = {item: row["digest"] for item, row in options.preparation.items.items()}
    # All TeX editions bind exactly the same prepared identities.
    for record in out.rglob("*.tpa"):
        options.preparation.validate_compile(record)
    # A raw source change must stop both Python reuse and direct pdfLaTeX.
    source = deck / "activities" / (sorted(item_ids)[0] + ".lesson.json")
    original = source.read_bytes()
    try:
        source.write_bytes(original + b"\n")
        try:
            options.preparation.validate(catalog)
            raise AssertionError("Changed source accepted")
        except PluginError as error:
            assert "stale prepared source" in str(error)
        stale = compile_latex(exported["handout"], output_dir=out / "stale-source")
        assert stale.returncode != 0 and "Stale prepared input" in stale.log_text
    finally:
        source.write_bytes(original)
    report = {"provider": provider.requirement(), "deck": deck_name, "language": language,
              "prepare_calls": len(calls), "prepare_ms": calls, "items": identities, "pages": counts,
              "artifacts": {k: str(p) for k, p in artifacts.items()},
              "sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in artifacts.items() if p.is_file()},
              "checks": ["single preparation", "live bundle privacy", "exercise/solution separation",
                         "static PowerPoint media", "three direct pdfLaTeX editions", "same item identities",
                         "no clipped PDF text", "changed source refused", "PNG renders saved for visual review"]}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="A new disposable directory")
    parser.add_argument("--scenario", action="append", choices=["lesson-en", "lesson-de", "stress-en", "stress-de"])
    args = parser.parse_args()
    if shutil.which("pdflatex") is None:
        raise SystemExit("pdfLaTeX is required; install the documented TeX/font/language packages.")
    if args.output.exists():
        raise SystemExit("Use a new output directory.")
    reports = []
    for scenario in args.scenario or ["lesson-en", "lesson-de", "stress-en", "stress-de"]:
        group, language = scenario.split("-")
        report = verify(args.output / scenario, "lesson" if group == "lesson" else "layout-stress", language)
        reports.append({"scenario": scenario, "pages": report["pages"], "prepare_calls": report["prepare_calls"]})
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()

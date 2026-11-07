# SPDX-License-Identifier: Apache-2.0
"""Installed prepared-authoring contracts, privacy, geometry and stale exports."""
import copy
import json
from pathlib import Path
import shutil
import sys

import pytest
from jsonschema import ValidationError
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.contracts import validate_portable_schema
from texstage_bplus_lab import layout, model
from texstage_bplus_lab.authoring import prepare_lesson, TYPE
from texstage_bplus_lab.state import Lesson
from test_engine import probe, exercise, acceptable

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "examples/bplus"


def lesson(name="insert"):
    return json.loads((EXAMPLES / "activities" / (name + ".json")).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def provider():
    selected, _ = probe.installed()
    import texstage_bplus_lab.authoring as module
    assert Path(module.__file__).is_relative_to(Path(sys.prefix))
    assert not Path(module.__file__).is_relative_to(ROOT / "plugins/bplus-lab")
    return selected


@pytest.mark.parametrize("language", ["en", "de", "de-AT"])
def test_all_worked_cases_and_private_boundary(provider, language):
    fixtures = probe.fixture(provider, "design-cases.json")
    requests = []
    for case in fixtures["cases"]:
        seed = exercise(fixtures, case)
        source = lesson()
        source["exercise"], source["worked"]["answer"] = seed, copy.deepcopy(case["answer"])
        before = model.canonical(source)
        made = json_value(prepare_lesson(source, {"language": language}))
        public, private = made["prepared"]["public"], made["prepared"]["private"]
        assert model.canonical(source) == before
        assert public["exercise"] == seed and public["interaction"] == "classroom"
        assert set(public) == {"format", "title", "prompt", "exercise", "interaction", "points", "rubric"}
        assert "worked" not in public and "analysis" not in public and "feedback" not in public
        assert private["exercise_digest"] == model.digest(seed)
        assert private["worked"]["analysis"] == model.analyze(seed, case["answer"])
        assert acceptable(private["worked"]["analysis"])
        assert made["prepared"]["evaluations"]["analysis"] == {"seed": model.canonical(seed), "options": {}, "references": []}
        heading = "Eine geprüfte Lösung" if language.startswith("de") else "One checked solution"
        assert heading not in made["fragments"]["exercise"] and heading in made["fragments"]["solutions"]
        assert source["worked"]["explanation"]["en"] not in made["fragments"]["exercise"]
        requests.append(probe.request(seed, case["answer"], expected=private["worked"]["analysis"]))
    if language == "en":
        rows = probe.run(requests)
        assert all(not r.get("load_or_contract_error") and r["outcome"]["data"] == q["expected"]
                   for r, q in zip(rows, requests, strict=True))


@pytest.mark.parametrize("name", ["lookup", "range", "insert", "delete", "cascade", "shrink", "empty", "last", "large"])
def test_examples_deterministic_and_within_limits(provider, name):
    source = lesson(name)
    for language in ("en", "de"):
        first = json_value(prepare_lesson(source, {"language": language}))
        assert first == json_value(prepare_lesson(source, {"language": language}))
        assert all(len(t.encode("utf-8")) < 128 * 1024 for t in first["fragments"].values())
        assert not first["prepared"]["assets"]  # diagrams are trusted generated TeX, not external files
    facts = model.analyze(source["exercise"], source["worked"]["answer"])
    if name == "large":
        assert len(facts["final"]["nodes"]) == 29 and facts["metrics"]["height_after"] == 3
        assert sum(len(n["keys"]) for n in facts["final"]["nodes"] if n["kind"] == "leaf") == 41


@pytest.mark.parametrize("fault", ["format-bool", "extra", "bad-text", "control", "wrong-path", "missing-repair",
                                   "extra-repair", "wrong-separator", "wrong-prediction", "wrong-height",
                                   "float-key", "invalid-tree", "wrong-keys", "wrong-scan", "unknown-feedback"])
def test_bad_source_or_worked_certificate_stops_preparation(provider, fault):
    value = lesson("range" if fault in ("wrong-keys", "wrong-scan") else "insert")
    answer = value["worked"]["answer"]
    if fault == "format-bool": value["format"] = True
    elif fault == "extra": value["raw_tex"] = r"\input{secret}"
    elif fault == "bad-text": value["title"]["en"] = []
    elif fault == "control": value["prompt"]["en"] = "bad\0text"
    elif fault == "wrong-path": answer["path"] = [0, 3]
    elif fault == "missing-repair": answer["repairs"] = []
    elif fault == "extra-repair": answer["repairs"].append(copy.deepcopy(answer["repairs"][0]))
    elif fault == "wrong-separator": answer["repairs"][0]["separator"] += 1
    elif fault == "wrong-prediction": answer["separators"][0]["keys"][0] += 1
    elif fault == "wrong-height": answer["height"] = 3
    elif fault == "float-key": value["exercise"]["task"]["key"] = 27.0
    elif fault == "invalid-tree": value["exercise"]["tree"]["nodes"][0]["keys"][0] += 1
    elif fault == "wrong-keys": answer["keys"] = []
    elif fault == "wrong-scan": answer["leaves"] = [2]
    else: value["feedback"] = "public-always"
    with pytest.raises((ValueError, ValidationError)):
        prepare_lesson(value, {})


def test_plain_text_escaping_fallback_and_envelope_budget(provider):
    source = lesson()
    plain = r"Task #1 & \input{secret} $x$"
    source["title"] = {"en": plain}
    source["worked"]["explanation"] = {"en": plain}
    made = prepare_lesson(source, {"language": "de"})
    assert any("Missing German" in d for d in made.prepared.diagnostics)
    for text in made.fragments.values():
        assert r"\input{secret}" not in text
        assert r"\textbackslash{}input\{secret\}" in text
        assert r"\&" in text and r"\$x\$" in text
    source["prompt"]["en"] = "x" * 21000
    with pytest.raises(model.ResourceLimit):
        prepare_lesson(source, {})


def test_classroom_state_and_style_capability(provider):
    content = provider.manifest["capabilities"]["content_types"][TYPE]
    assert content["state_schema"] == 5 and "submit-answer" in content["messages"]
    assert set(content["views"]) == {"presenter-overlay", "projector-overlay", "participant-input", "presenter-controls"}
    assert content["fallback"] == "static-slide"
    assert provider.manifest["latex_exports"]["commands"] == ["bplustree"]
    for name in content["view_schemas"].values():
        validate_portable_schema(json.loads(provider.resources[name]))
    context = {"scoring": {"maximum": 1000, "released": False, "awarded": None}, "item": json_value(prepare_lesson(lesson(), {}))["prepared"],
               "records": {"count": 0, "actor": "alice", "number": 1, "value": None},
               "record_page": {"page": 0, "pages": 1, "total": 0, "rows": []}}
    state = Lesson().initial_state(context["item"], context)
    for role, surface in (("presenter", "presenter-controls"), ("projector", "projector-overlay"), ("participant", "participant-input")):
        projected = Lesson().view(state, {"role": role, "surface": surface, "actor": "alice"}, context)
        assert projected["phase"] == "introduce"
        assert "worked" not in projected and "own" not in projected


def test_geometry_preserves_pages_order_and_nonoverlap(provider):
    fixtures = probe.fixture(provider, "design-cases.json")
    trees = [m["tree"] for m in fixtures["models"].values()]
    trees += [c["expected"]["tree"] for c in fixtures["cases"] if "tree" in c["expected"]]
    big = lesson("large")
    trees += [big["exercise"]["tree"], model.analyze(big["exercise"], big["worked"]["answer"])["final"]]
    modes = set()
    for tree in trees:
        geometry = layout.geometry(tree)
        modes.add(geometry["mode"])
        assert set(geometry["pages"]) == {n["id"] for n in tree["nodes"]}
        assert len(geometry["order"]) == len(tree["nodes"])
        for a in geometry["pages"].values():
            assert 0 <= a["x"] - a["width"] / 2 <= a["x"] + a["width"] / 2 <= geometry["width"] + 1e-8
        positions = list(geometry["pages"].values())
        for i, a in enumerate(positions):
            for b in positions[i + 1:]:
                assert abs(a["y"] - b["y"]) >= layout.HEIGHT or abs(a["x"] - b["x"]) >= (a["width"] + b["width"]) / 2
        shuffled = copy.deepcopy(tree); shuffled["nodes"].reverse()
        assert layout.geometry(shuffled) == geometry
    assert modes == {"tree", "map"}


def test_host_confinement_enablement_and_fragment_freshness(tmp_path, provider):
    from texstage.build.authoring import prepare_sources
    deck = tmp_path / "deck"; shutil.copytree(EXAMPLES, deck)
    tex, sidecar = deck / "lesson.tex", deck / "lesson.en.activities.json"
    catalog = Catalog([provider])
    with pytest.raises(PluginError, match="not enabled"):
        prepare_sources(tex, sidecar, Catalog(), tmp_path / "disabled")
    original = sidecar.read_bytes()
    data = json.loads(original); data["items"][0]["source"] = "../outside.json"
    (tmp_path / "outside.json").write_text(json.dumps(lesson()), encoding="utf-8")
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PluginError):
        prepare_sources(tex, sidecar, catalog, tmp_path / "outside")
    sidecar.write_bytes(original)
    prepared = prepare_sources(tex, sidecar, catalog, tmp_path / "prepared")
    with pytest.raises(PluginError, match="identity"):
        prepared.validate(Catalog())
    fragment = prepared.directory / "lookup-solutions.tex"
    fragment.write_bytes(fragment.read_bytes() + b"\nchanged")
    with pytest.raises(PluginError, match="artifact changed"):
        prepared.validate(catalog)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="needs pdfLaTeX; required in prepared-authoring CI")
def test_direct_export_style_staleness_and_small_box_refusal(tmp_path, provider):
    from texstage.build.authoring import prepare_sources
    from texstage.build.compiler import compile_latex
    from texstage.build.latex import compile_deck, LatexError
    deck = tmp_path / "deck"; shutil.copytree(EXAMPLES, deck)
    tex, sidecar = deck / "lesson.tex", deck / "lesson.en.activities.json"
    catalog = Catalog([provider])
    prepared = prepare_sources(tex, sidecar, catalog, tmp_path / "prepared")
    exports = prepared.export(tex, catalog)
    # The disposable installed style is restored even if the test fails.
    style = Path(__import__("texstage_bplus_lab").__file__).parent / "latex/texstage-bplus-tree.sty"
    before = style.read_bytes()
    try:
        style.write_bytes(before + b"\n% changed approved resource\n")
        direct = compile_latex(exports["handout"], output_dir=tmp_path / "stale-style")
        assert direct.returncode != 0 and "Stale prepared input" in direct.log_text
        with pytest.raises(PluginError):
            prepared.validate(catalog)
    finally:
        style.write_bytes(before)
    tex.write_text(tex.read_text(encoding="utf-8").replace(r".90\textheight", "10mm"), encoding="utf-8")
    with pytest.raises(LatexError, match="too tall"):
        compile_deck(tex, "solutions", tmp_path / "tiny", plugins=catalog, preparation=prepared)

# SPDX-License-Identifier: Apache-2.0
"""Installed prepared-authoring provider: semantics, privacy and real editions."""
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
from texstage_er_decisions import model
from texstage_er_decisions.authoring import prepare_lesson, TYPE
from test_engine import probe

ROOT = Path(__file__).resolve().parents[3]


def source():
    return json.loads((ROOT / "examples/er-decisions/activities/registrations.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def provider():
    selected, _ = probe.installed()
    assert Path(__import__("texstage_er_decisions.authoring", fromlist=["__file__"]).__file__).is_relative_to(Path(sys.prefix))
    return selected


@pytest.mark.parametrize("language", ["en", "de", "de-AT"])
def test_single_source_worked_models_masking_and_private_boundary(provider, language):
    made = json_value(prepare_lesson(source(), {"language": language}))
    public, private = made["prepared"]["public"], made["prepared"]["private"]
    assert public["interaction"] == "decision-cards"
    assert "worked" not in public and "counterexamples" not in public and "checks" not in public
    assert "worked_answers" not in model.canonical(public)
    assert "duplicate-pair" not in model.canonical(public)
    graph = public["model"]["relationship"]
    assert graph["form"] is None and graph["pair_unique"] is None
    assert graph["attributes"][0]["owner"] is None
    assert next(r for r in graph["roles"] if r["id"] == "person")["min"] is None
    assert next(r for r in graph["roles"] if r["id"] == "workshop")["min"] == 0
    assert "expected" not in public["examples"][0]
    forms = {row["model"]["relationship"]["form"] for row in private["worked"]}
    assert forms == {"relationship", "association-entity"}
    assert private["exercise_digest"] == model.digest(model.semantic_seed(model.source(source()["exercise"])))
    exercise = made["prepared"]["evaluations"]["analysis"]["seed"]
    rows = probe.run([{"seed": exercise, "text": json.dumps(w["answer"])} for w in private["worked"]])
    assert all(row["outcome"]["data"]["model_valid"] for row in rows)
    assert all(c["admits"] == (c["expected"] == "allow") for row in rows for c in row["outcome"]["data"]["checks"])
    assert len(private["teaching_witnesses"]) == 2
    for witness in private["teaching_witnesses"]:
        check = witness["finding"]
        assert check["admits"] != (check["expected"] == "allow")
    expected = "Geprüfte Alternativen" if language.startswith("de") else "Checked alternatives"
    assert expected in made["fragments"]["solutions"]
    assert expected not in made["fragments"]["exercise"]
    assert "r2:" not in made["fragments"]["exercise"]
    assert "r2:" in made["fragments"]["solutions"]
    assert all(len(text.encode()) < 128 * 1024 for text in made["fragments"].values())


@pytest.mark.parametrize("fault", ["missing-label", "duplicate-label", "missing-translation", "wrong-worked",
                                   "missing-worked", "duplicate-worked", "non-counterexample", "unknown-snapshot",
                                   "wrong-profile", "wide-layout", "long-brief", "extra-field"])
def test_invalid_authoring_fails(provider, fault):
    value = source()
    if fault == "missing-label":
        value["labels"]["entities"][0]["id"] = "unknown"
    elif fault == "duplicate-label":
        value["labels"]["entities"][1]["id"] = value["labels"]["entities"][0]["id"]
    elif fault == "missing-translation":
        value["requirements_de"].pop()
    elif fault == "wrong-worked":
        next(p for p in value["solutions"][0]["answer"]["choices"] if p[0] == "person-links")[1] = "zero-one"
    elif fault == "missing-worked":
        value["solutions"].pop()
    elif fault == "duplicate-worked":
        value["solutions"][1] = value["solutions"][0]
    elif fault == "non-counterexample":
        value["counterexamples"][0]["answer"] = value["solutions"][0]["answer"]
    elif fault == "unknown-snapshot":
        value["counterexamples"][0]["snapshot"] = "unknown"
    elif fault == "wrong-profile":
        value["exercise"]["format"] = "er-rooms-v1"
    elif fault == "wide-layout":
        value["exercise"]["requirements"].append({"id": "extra", "text": "More."})
        value["requirements_de"].append({"id": "extra", "text": "Mehr."})
    elif fault == "long-brief":
        value["exercise"]["brief"]["en"] = "x" * 181
    else:
        value["raw_tex"] = r"\input{secret}"
    with pytest.raises((ValueError, model.InputError, ValidationError)):
        prepare_lesson(value, {})


def test_plain_text_escaping_and_renamed_labels(provider):
    value = source()
    value["title"]["en"] = r"Task #1 & \input{secret} <model>"
    value["labels"]["entities"][0]["text"]["en"] = r"People & \input{secret}"
    value["solutions"][0]["explanation"]["en"] = r"Use #1 & \input{secret}."
    made = prepare_lesson(value, {})
    for text in made.fragments.values():
        assert r"\input{secret}" not in text and r"\&" in text
        assert r"\textbackslash{}input\{secret\}" in text
    assert "Task #1" in made.prepared.public["title"]["en"]


def test_state_protocol_capability_and_static_fallback(provider):
    content = provider.manifest["capabilities"]["content_types"][TYPE]
    assert set(content["views"]) == {"presenter-overlay", "projector-overlay", "presenter-controls", "participant-input"}
    assert content["state_schema"] == 4
    assert content["messages"]["submit"]["revision_policy"] == "latest"
    assert content["fallback"] == "static-slide"
    for path in content["view_schemas"].values():
        validate_portable_schema(json.loads(provider.resources[path]))


def test_host_source_confinement_enablement_and_prepared_identity(tmp_path, provider):
    from texstage.build.authoring import prepare_sources
    deck = tmp_path / "deck"
    shutil.copytree(ROOT / "examples/er-decisions", deck)
    sidecar = deck / "lesson.en.activities.json"
    tex = deck / "lesson.tex"
    catalog = Catalog([provider])
    with pytest.raises(PluginError, match="not enabled"):
        prepare_sources(tex, sidecar, Catalog(), tmp_path / "disabled")
    original = sidecar.read_bytes()
    data = json.loads(original)
    data["items"][0]["source"] = "../outside.json"
    (tmp_path / "outside.json").write_text(json.dumps(source()), encoding="utf-8")
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PluginError):
        prepare_sources(tex, sidecar, catalog, tmp_path / "outside")
    sidecar.write_bytes(original)
    prepared = prepare_sources(tex, sidecar, catalog, tmp_path / "prepared")
    with pytest.raises(PluginError, match="identity"):
        prepared.validate(Catalog())
    fragment = prepared.directory / "registrations-solutions.tex"
    assert fragment.is_file()
    fragment.write_bytes(fragment.read_bytes() + b"changed")
    with pytest.raises(PluginError, match="artifact changed"):
        prepared.validate(catalog)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="needs pdfLaTeX")
@pytest.mark.parametrize("language,filename,long_labels", [
    ("en", "lesson.tex", False), ("de", "lesson-de.tex", False), ("de", "lesson-de.tex", True)])
def test_all_editions_real_build_and_freshness(tmp_path, provider, language, filename, long_labels):
    from texstage.build.builder import BuildOptions, build
    from texstage.build.latex import compile_deck
    from texstage.build.compiler import compile_latex
    from texstage.build.pdf import Pdf
    from texstage.plugins.policy import enable
    from texstage.server.bundles import load_bundle
    deck = tmp_path / "deck"
    shutil.copytree(ROOT / "examples/er-decisions", deck)
    if long_labels:
        value = source()
        value["labels"]["entities"][0]["text"]["de"] = "Teilnehmende Kursteilnehmerin"
        value["labels"]["entities"][1]["text"]["de"] = "Fortbildungsworkshop"
        value["labels"]["relationship"]["de"] = "Verbindliche Workshopanmeldung"
        value["labels"]["attributes"][0]["text"]["de"] = "Anmeldungsstatus"
        (deck / "activities/registrations.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    catalog = Catalog([provider])
    profile = tmp_path / "profile"
    enable(profile, provider.id, provider.version, provider.payload)
    options = BuildOptions(stage=True, key="er-prepared-test", activities=deck / f"lesson.{language}.activities.json",
                           plugin_data=profile, height=720)
    out = tmp_path / "out"
    result = build(deck / filename, out, options)
    assert not result.problems, result.problems
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert set(bundle.items[TYPE]) == {"registrations"}
    public = model.canonical(bundle.deck_json)
    for marker in ('"worked"', '"checks"', '"teaching_witnesses"', '"evaluations"', '"solutions"'):
        assert marker not in public
    assert bundle.file("keys.json") is None
    assert not list(result.bundle.rglob("*.tex")) and not list(result.bundle.rglob("*.activities.json"))
    assert result.static.is_file()
    def text(path):
        with Pdf(path) as pdf:
            return " ".join(page.text() for page in pdf)
    def assert_visible_text(path):
        # Fixed-height minipages can clip without an Overfull warning.
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(path) as document:
            for page in document:
                width, height = page.get_size()
                textpage = page.get_textpage()
                for i in range(textpage.count_chars()):
                    if textpage.get_text_range(i, 1).strip():
                        left, bottom, right, top = textpage.get_charbox(i)
                        assert left >= -1 and bottom >= -1 and right <= width + 1 and top <= height + 1, (path, i)
    heading = "Geprüfte Alternativen" if language == "de" else "Checked alternatives"
    handout = compile_deck(deck / filename, "handout", out, plugins=catalog, preparation=options.preparation)
    assert heading not in text(handout.pdf) and heading not in text(result.stage.pdf)
    solutions = out / "build" / (Path(filename).stem + "-solutions.pdf")
    assert heading in text(solutions) and "r2:" in text(solutions)
    exported = options.preparation.export(deck / filename, catalog)
    for edition in ("handout", "solutions"):
        direct = compile_latex(exported[edition], output_dir=out / ("direct-" + edition), passes=2)
        assert direct.returncode == 0, direct.stdout[-4000:]
        assert (heading in text(direct.pdf)) == (edition == "solutions")
        assert "Overfull" not in direct.log_text
        assert_visible_text(direct.pdf)
    # Engine sources are still confined by the host even for this authored type.
    source_path = deck / "activities/registrations.json"
    source_path.write_bytes(source_path.read_bytes() + b"\n")
    with pytest.raises(PluginError, match="stale prepared source"):
        options.preparation.validate(catalog)
    stale = compile_latex(exported["handout"], output_dir=out / "stale")
    assert stale.returncode != 0 and "Stale prepared input" in stale.log_text

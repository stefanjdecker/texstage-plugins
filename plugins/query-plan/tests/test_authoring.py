# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel prepared authoring, static exports and fail-closed host checks."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import time
import zipfile
from unittest.mock import patch

import pytest
from texstage.build.authoring import prepare_sources
from texstage.build.compiler import compile_latex
from texstage.build.latex import compile_deck
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.contracts import validate_portable_schema
from texstage.plugins.runtime import Runtime
from texstage.plugins.worker import Workers
from texstage_query_plan import model
from texstage_query_plan.authoring import prepare_lesson, TYPE, ENGINE
from test_engine import PROVIDER, maximum_exercise

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "maintenance"))
from query_plan_authoring_probe import pdf_text, verify


def source(name="library"):
    return json.loads((ROOT / f"examples/query-plan/activities/{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["selective", "broad", "library", "memory"])
def test_preparation_single_search_private_reference_and_exact_facts(name):
    value = source(name)
    original = copy.deepcopy(value)
    with patch.object(model, "optimum", wraps=model.optimum) as search:
        made = prepare_lesson(value, {"language": "en"})
    assert search.call_count == 1 and value == original
    public, private = made.prepared.public, made.prepared.private
    assert public["baseline_analysis"] == model.analyze(value["exercise"], value["baseline"])
    assert private["worked"]["analysis"] == model.analyze(value["exercise"], value["worked_answer"])
    assert private["reference"] == model.optimum(value["exercise"])
    assert made.prepared.evaluations["analysis"] == {
        "seed": model.canonical(public["exercise"]), "options": {}, "references": []}
    assert not made.prepared.assets
    encoded = model.canonical(public)
    assert all('"' + k + '"' not in encoded for k in ("reference", "worked", "explanation", "evaluations"))
    assert value["explanation"]["en"] not in made.fragments["exercise"]
    assert "One worked plan" in made.fragments["solutions"]
    assert "Starting plan" in made.fragments["exercise"]
    assert str(private["reference"]["cost"]) in made.fragments["solutions"]


@pytest.mark.parametrize("language", ["en", "de", "de-DE"])
def test_plain_text_is_escaped_and_unicode_is_explicit(language):
    value = source()
    value["explanation"] = {k: r"50% #1 & \input{secret} _ ^ ~ $ " + "🙂" for k in ("en", "de")}
    made = prepare_lesson(value, {"language": language})
    text = made.fragments["solutions"]
    assert r"\input{secret}" not in text and r"\%" in text and r"\&" in text
    assert "[U+1F642]" in text and "🙂" not in text
    assert made.prepared.private["worked"]["explanation"] == value["explanation"]
    assert ("Ein Lösungsplan" in text) == language.startswith("de")
    assert r"\textbf{1}." in text  # display numbering; canonical node indexes remain zero-based


@pytest.mark.parametrize("fault", ["baseline", "worked", "unreachable", "nonoptimal"])
def test_invalid_lesson_cannot_be_prepared(fault):
    value = source("selective")
    if fault in ("baseline", "worked"):
        value["baseline" if fault == "baseline" else "worked_answer"]["nodes"][0]["relation"] = "missing"
    if fault == "unreachable": value["goal"] = {"kind": "budget", "max_cost": 0}
    if fault == "nonoptimal": value["worked_answer"] = value["baseline"]
    with pytest.raises(ValueError):
        prepare_lesson(value, {})


def test_budget_solution_distinguishes_worked_from_optimal():
    value = source("library")
    value["goal"] = {"kind": "budget", "max_cost": 130000}
    value["worked_answer"] = value["baseline"]
    made = prepare_lesson(value, {})
    assert made.prepared.private["worked"]["analysis"]["cost"] == 128280
    assert made.prepared.private["reference"]["cost"] == 116430
    assert "An optimal reference" in made.fragments["solutions"]
    assert "130000" in made.fragments["exercise"]
    assert "116430" not in made.fragments["exercise"]


def test_bounded_maximum_lesson_in_real_worker(tmp_path):
    value = source()
    value["exercise"] = maximum_exercise()
    reference = model.optimum(value["exercise"])
    value["worked_answer"] = value["baseline"] = reference["plan"]
    value["explanation"] = {"en": "🙂" * 2000, "de": "ä" * 2000}
    workers = Workers(Catalog([PROVIDER]))
    try:
        start = time.perf_counter()
        made = workers.call(TYPE, "prepare_source", value, {"language": "en"})
        elapsed = time.perf_counter() - start
    finally:
        workers.close()
    assert len(model.canonical(made)) < 1024 * 1024
    assert all(len(f.encode("utf-8")) < 128 * 1024 for f in made["fragments"].values())
    assert made["prepared"]["private"]["reference"]["candidates"] == 864
    (tmp_path / "worker-budget.json").write_text(json.dumps({
        "seconds_including_startup": elapsed, "response_bytes": len(model.canonical(made)),
        "fragment_bytes": {k: len(v.encode("utf-8")) for k, v in made["fragments"].items()}}), encoding="utf-8")


def test_initial_runtime_views_and_unknown_commands(tmp_path):
    schema = json.loads(PROVIDER.resources["texstage_query_plan/schemas/prepared-view-v1.json"])
    validate_portable_schema(schema)
    made = json_value(prepare_lesson(source(), {}))["prepared"]
    made["evaluations"]["analysis"]["engine"] = ENGINE
    runtime = Runtime(tmp_path / "runtime.sqlite3", Catalog([PROVIDER]))
    try:
        runtime.ensure("lesson", TYPE, "library", made)
        runtime.activate("lesson", {(TYPE, "library")})
        for role, surface in (("presenter", "presenter-overlay"), ("projector", "projector-overlay")):
            view = runtime.view("lesson", TYPE, "library", role=role, surface=surface, actor="reader")
            assert view["data"]["phase"] == "introduce" and view["data"]["count"] == 0
            assert ("solution" in view["data"]) == (role == "presenter")
        for role in ("participant", "presenter"):
            with pytest.raises(PluginError, match="operation is not allowed"):
                runtime.command("lesson", "reader", role, {
                    "type": TYPE, "item": "library", "operation": "submit",
                    "payload": {}, "epoch": 1, "expected_revision": 0, "request_id": role + "000001"})
        assert runtime.lease("lesson", "presenter", now=100) == []
    finally:
        runtime.close()


@pytest.fixture
def deck(tmp_path):
    dest = tmp_path / "source"
    shutil.copytree(ROOT / "examples/query-plan", dest)
    return dest


@pytest.mark.parametrize("path", ["../outside.json", "activities/../../outside.json", "/absolute.json", "C:/outside.json"])
def test_source_paths_are_confined_before_provider_execution(deck, tmp_path, path):
    sidecar = deck / "lesson.activities.json"
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["items"][0]["source"] = path
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with patch("texstage.build.authoring.Workers") as workers:
        with pytest.raises(PluginError):
            prepare_sources(deck / "lesson.tex", sidecar, Catalog([PROVIDER]), tmp_path / "build")
        workers.assert_not_called()


def test_missing_provider_is_explicit(deck, tmp_path):
    with pytest.raises(PluginError, match="not enabled|not available|Unknown|unknown|unavailable"):
        prepare_sources(deck / "lesson.tex", deck / "lesson.activities.json", Catalog([]), tmp_path / "build")


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="requires TeX Live")
def test_changed_source_reprepares_facts_and_invalidates_direct_export(deck, tmp_path):
    catalog = Catalog([PROVIDER])
    first = prepare_sources(deck / "lesson.tex", deck / "lesson.activities.json", catalog, tmp_path / "first")
    exported = first.export(deck / "lesson.tex", catalog)
    path = deck / "activities/selective.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["exercise"]["statistics"]["base"][0]["pages"] += 1
    path.write_text(json.dumps(value), encoding="utf-8")
    stale = compile_latex(exported["handout"], output_dir=tmp_path / "stale")
    assert stale.returncode != 0 and "Stale prepared input" in stale.log_text
    second = prepare_sources(deck / "lesson.tex", deck / "lesson.activities.json", catalog, tmp_path / "fresh")
    assert first.items["selective"]["digest"] != second.items["selective"]["digest"]
    a, b = [p.items["selective"]["prepared"]["public"]["baseline_analysis"] for p in (first, second)]
    assert b["cost"] == a["cost"] + 100
    assert first.items["library"]["digest"] == second.items["library"]["digest"]


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="requires TeX Live")
def test_real_exports_and_bundle_privacy(tmp_path):
    # Reuse only a probe from this exact installed artifact, when explicitly supplied.
    prior = os.environ.get("QUERY_PLAN_AUTHORING_OUTPUT")
    report = json.loads((Path(prior) / "report.json").read_text(encoding="utf-8")) if prior else verify(tmp_path / "editions")
    assert report["provider"] == PROVIDER.requirement()
    assert report["prepare_calls"] == 4
    for name, path in report["artifacts"].items():
        assert Path(path).exists(), name
    from pptx import Presentation
    presentation = Presentation(report["artifacts"]["powerpoint"])
    assert len(presentation.slides) == 7
    with zipfile.ZipFile(report["artifacts"]["powerpoint"]) as archive:
        assert not any("notesSlides/notesSlide" in n for n in archive.namelist())
    for edition in ("handout", "solutions"):
        text = pdf_text(report["artifacts"][edition])
        assert ("One worked plan" in text) == (edition == "solutions")
        assert "Cost rules" in text and "Hash workspace per operator" in text
        # pdfLaTeX direct exports contain exactly the same pedagogical text.
        assert text == pdf_text(report["artifacts"]["direct-" + edition])


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="requires TeX Live")
def test_german_real_pdf(deck, tmp_path):
    sidecar = deck / "lesson.activities.json"
    value = json.loads(sidecar.read_text(encoding="utf-8"))
    value["language"] = "de"
    sidecar.write_text(json.dumps(value), encoding="utf-8")
    catalog = Catalog([PROVIDER])
    prepared = prepare_sources(deck / "lesson.tex", sidecar, catalog, tmp_path / "prepared")
    for edition in ("handout", "solutions"):
        result = compile_deck(deck / "lesson.tex", edition, tmp_path / "german", plugins=catalog, preparation=prepared)
        text = pdf_text(result.pdf)
        assert "Kostenregeln" in text and "Geschätzte Statistik" in text
        assert ("Ein Lösungsplan" in text) == (edition == "solutions")

# SPDX-License-Identifier: Apache-2.0
"""Prepared lessons and real host runtime, using only the installed provider."""
import copy
import json
from pathlib import Path
import shutil
import sys

import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog, discover
from texstage.plugins.manifest import read_json
from texstage.plugins.runtime import Runtime
from texstage_relational_lab import model
from texstage_relational_lab.authoring import prepare_lesson, TYPE, ENGINE
from texstage_relational_lab.state import Lesson, SLOT_BYTES, STATE_BYTES
from test_engine import probe

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, "Use a relational-only wheel environment."
    p, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    return p


def source(mode="construct"):
    return json.loads((ROOT / f"examples/relational/activities/{mode}.json").read_text(encoding="utf-8"))


def prepared(mode="construct"):
    return json_value(prepare_lesson(source(mode), {"language": "en"}))


def context(mode="construct"):
    return {"item": prepared(mode)["prepared"], "epoch": 1, "role": "participant"}


def command(op, payload, *, actor="alice", request="request00001"):
    return {"kind": "command", "operation": op, "payload": payload, "actor": actor, "request_id": request}


def advance(state, event, ctx):
    result = json_value(Lesson().transition(state, event, ctx))
    assert "refusal" not in result, result
    return result["state"], result["effects"]


def opened(mode="construct"):
    ctx = context(mode)
    state = Lesson().initial_state(ctx["item"], ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    state, _ = advance(state, command("open", {"control": 0}), ctx | {"role": "presenter"})
    return state, ctx


def submit(state, ctx, *, actor="alice", version=0, request="request00001", answer=None):
    mode = ctx["item"]["public"]["mode"]
    answer = answer or source(mode)["worked_answer"]
    return advance(state, command("submit-" + ("tree" if mode == "construct" else "rewrite"),
        {"phase": state["phase_version"], "version": version, "answer": answer},
        actor=actor, request=request), ctx)


def complete(state, ctx, outcome=None, **changes):
    slot = state["answers"]["alice"]
    mode = ctx["item"]["public"]["mode"]
    outcome = outcome or {"status": "ok", "data": model.analyze(source(mode)["exercise"], slot["answer"])}
    return advance(state, {"kind": "evaluation.finished", "actor": "alice", "binding": "analysis",
        "job_id": "synthetic", "correlation_id": slot["correlation"], "outcome": outcome} | changes, ctx)[0]


def view(state, ctx, role, actor="alice"):
    return Lesson().view(state, {"role": role, "actor": actor}, ctx)


@pytest.mark.parametrize("mode", ["construct", "rewrite"])
def test_authoring_one_source_independent_checks_and_privacy(provider, mode):
    made = prepared(mode)
    public, private = made["prepared"]["public"], made["prepared"]["private"]
    assert "reference_tree" not in public and "worked" not in public and "expected" not in public
    assert "instances" not in public and public["instance"]["visibility"] == "public"
    assert private["expected"] == model.analyze(source(mode)["exercise"], source(mode)["worked_answer"])["fixtures"]
    assert "One worked answer" not in made["fragments"]["exercise"]
    assert "One worked answer" in made["fragments"]["solutions"]
    # Exercise/solutions are provider output, not raw caller-supplied TeX.
    changed = source(mode)
    changed["exercise"]["title"]["en"] = r"Query #1 & \input{secret}"
    escaped = prepare_lesson(changed, {"language": "en"}).fragments["exercise"]
    assert r"\input{secret}" not in escaped and r"\#" in escaped and r"\&" in escaped
    assert prepare_lesson(source(mode), {"language": "de"}).fragments["exercise"] != made["fragments"]["exercise"]


def test_authoring_rejects_wrong_worked_answer(provider):
    changed = source()
    changed["worked_answer"] = {"mode": "construct", "tree": [["rel", "books"]]}
    with pytest.raises(ValueError, match="configured instances"):
        prepare_lesson(changed, {})
    changed = source("rewrite")
    changed["worked_answer"]["steps"] = []
    with pytest.raises(ValueError, match="reduce"):
        prepare_lesson(changed, {})


@pytest.mark.parametrize("mode", ["construct", "rewrite"])
def test_lesson_success_is_hidden_until_reveal(provider, mode):
    state, ctx = opened(mode)
    state, effects = submit(state, ctx)
    assert len(effects) == 1 and effects[0]["kind"] == "evaluate"
    state = complete(state, ctx)
    assert "feedback" not in view(state, ctx, "participant")["own"]
    assert "own" not in view(state, ctx, "participant", "bob")
    assert "worked" not in view(state, ctx, "projector")
    assert view(state, ctx, "presenter")["counts"]["correct"] == 1
    for op in ("close", "reveal"):
        state, _ = advance(state, command(op, {"control": state["control_version"]}), ctx | {"role": "presenter"})
    released = view(state, ctx, "participant")
    assert released["own"]["feedback"]["correct"] and "worked" in released
    for role in ("participant", "projector", "presenter"):
        serialized = model.canonical(view(state, ctx, role))
        assert '"expected"' not in serialized and '"fixtures"' not in serialized
        for fact in ctx["item"]["private"]["expected"]:
            assert fact["relation"] not in serialized and fact["header"] not in serialized


def test_actor_versions_presenter_guards_reopen_and_navigation(provider):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    state, _ = submit(state, ctx, actor="bob", request="requestbob01")  # independent version zero
    event = command("submit-tree", {"phase": 1, "version": 0, "answer": source()["worked_answer"]})
    assert Lesson().transition(state, event, ctx) == {"refusal": "stale-answer"}
    teacher = ctx | {"role": "presenter"}
    assert Lesson().transition(state, command("close", {"control": 0}), teacher) == {"refusal": "stale-control"}
    state, _ = advance(state, command("close", {"control": 1}), teacher)
    assert Lesson().transition(state, event, ctx) == {"refusal": "closed"}
    state, _ = advance(state, command("open", {"control": 2}), teacher)
    assert Lesson().transition(state, event, ctx) == {"refusal": "stale-phase"}
    state, _ = advance(state, {"kind": "deactivate"}, ctx)
    assert Lesson().transition(state, event, ctx) == {"refusal": "closed"}
    state, _ = advance(state, {"kind": "activate"}, ctx)
    assert len(state["answers"]) == 2


def test_replacement_cancels_old_and_rejects_late_completion(provider):
    state, ctx = opened()
    state, first = submit(state, ctx)
    state, second = submit(state, ctx, version=1, request="replacement01")
    assert second[0] == {"kind": "cancel-evaluation", "correlation_id": first[0]["correlation_id"]}
    assert complete(state, ctx, correlation_id=first[0]["correlation_id"]) == state
    assert complete(state, ctx, binding="other") == state
    assert complete(state, ctx | {"epoch": 2}) == state
    state = complete(state, ctx)
    assert state["answers"]["alice"]["version"] == 2 and state["answers"]["alice"]["feedback"]["correct"]


def test_explicit_sharing_is_anonymous_and_invalidated_on_reopen(provider):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    teacher = ctx | {"role": "presenter"}
    assert Lesson().transition(state, command("select-demonstration", {"control": 1, "actor": "alice"}), teacher) == {"refusal": "phase"}
    state, _ = advance(state, command("close", {"control": 1}), teacher)
    state, _ = advance(state, command("select-demonstration", {"control": 2, "actor": "alice"}), teacher)
    projected = view(state, ctx, "projector")
    assert projected["demonstration"] == source()["worked_answer"]
    assert "alice" not in model.canonical(projected)
    state, _ = advance(state, command("open", {"control": 3}), teacher)
    assert "demonstration" not in view(state, ctx, "projector")


@pytest.mark.parametrize("fault", ["identity", "answer", "mode", "coverage", "duplicate", "trace", "metric", "certificate"])
def test_shape_valid_misbound_facts_are_unavailable_not_incorrect(provider, fault):
    mode = "rewrite" if fault == "certificate" else "construct"
    state, ctx = opened(mode)
    state, _ = submit(state, ctx)
    data = model.analyze(source(mode)["exercise"], source(mode)["worked_answer"])
    if fault == "identity": data["exercise"] = "0" * 64
    if fault == "answer": data["answer"] = "0" * 64
    if fault == "mode": data["mode"] = "rewrite"
    if fault == "coverage": data["fixtures"] = data["fixtures"][:-1]
    if fault == "duplicate": data["fixtures"][-1] = data["fixtures"][0]
    if fault == "trace": data["public"]["trace"].pop()
    if fault == "metric": data["public"]["cells"] += 1
    if fault == "certificate": data["proof"]["tree"] = [["rel", "books"]]
    state = complete(state, ctx, {"status": "ok", "data": data})
    own = state["answers"]["alice"]
    assert own["status"] == "unavailable" and "correct" not in own["feedback"]


@pytest.mark.parametrize("status", ["timeout", "error", "syntax", "refused", "cancelled"])
def test_operational_failures_preserve_answer(provider, status):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    state = complete(state, ctx, {"status": status})
    assert state["answers"]["alice"]["answer"] == source()["worked_answer"]
    assert state["answers"]["alice"]["status"] == "unavailable"
    assert "feedback" not in view(state, ctx, "participant")["own"]


def test_64_actor_budget_includes_keys_feedback_and_effects(provider):
    state, ctx = opened()
    # Near the canonical answer limit, with all 16 legal nodes.
    tree = [["rel", "books"]]
    for i in range(1, 16):
        tree.append(["select", i - 1, [["eq", ["a", "topic"], ["v", "x" * 24]]]])
    answer = {"mode": "construct", "tree": tree}
    for node in tree[1:]:
        node[2].append(["eq", ["a", "topic"], ["v", "x" * 24]])
        if len(model.canonical(answer)) > 1800:
            node[2].pop()
            break
    model.answer(answer)
    assert len(model.canonical(answer)) > 1700
    for n in range(64):
        actor = f"{n:03d}" + "x" * 253
        state, effects = submit(state, ctx, actor=actor, request=f"request{n:06d}", answer=answer)
        assert len(model.canonical({actor: state["answers"][actor]})) <= SLOT_BYTES
        assert len(model.canonical({"state": state, "effects": effects})) <= 256 * 1024
        state, _ = advance(state, {"kind": "evaluation.finished", "actor": actor,
            "binding": "analysis", "correlation_id": state["answers"][actor]["correlation"],
            "outcome": {"status": "timeout"}}, ctx)
        assert len(model.canonical({actor: state["answers"][actor]})) <= SLOT_BYTES
    refused = Lesson().transition(state, command("submit-tree",
        {"phase": 1, "version": 0, "answer": answer}, actor="extra"), ctx)
    assert refused == {"refusal": "capacity"}
    actor = "000" + "x" * 253
    state, _ = submit(state, ctx, actor=actor, version=1, request="replacement01", answer=answer)
    assert len(model.canonical(state)) < STATE_BYTES
    for role in ("participant", "presenter", "projector"):
        assert len(model.canonical(view(state, ctx, role, actor))) < 128 * 1024


@pytest.fixture
def runtime(tmp_path, provider):
    r = Runtime(tmp_path / "runtime.sqlite3", Catalog([provider]))
    spec = prepared()["prepared"]
    spec["evaluations"]["analysis"]["engine"] = ENGINE
    r.ensure("lesson", TYPE, "construct", spec)
    r.activate("lesson", {(TYPE, "construct")})
    yield r
    r.close()


def envelope(operation, payload, request="request00001", epoch=1):
    return {"type": TYPE, "item": "construct", "operation": operation, "payload": payload,
            "epoch": epoch, "expected_revision": 0, "request_id": request}


def test_installed_runtime_replay_replacement_reset_and_validated_views(runtime, monkeypatch):
    r = runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING", 1)
    assert r.command("lesson", "teacher", "presenter", envelope("open", {"control": 0}))["accepted"]
    first = envelope("submit-tree", {"phase": 1, "version": 0, "answer": source()["worked_answer"]})
    receipt = r.command("lesson", "alice", "participant", first)
    assert r.command("lesson", "alice", "participant", first) == receipt
    stale = first | {"request_id": "device000001"}
    assert r.command("lesson", "alice", "participant", stale)["error"] == "stale-answer"
    assert r.command("lesson", "teacher2", "presenter", envelope("close", {"control": 0}))["error"] == "stale-control"
    old = r.lease("lesson", "presenter", now=100)[0]
    replacement = envelope("submit-tree", {"phase": 1, "version": 1, "answer": source()["worked_answer"]}, "replacement01")
    assert r.command("lesson", "alice", "participant", replacement)["accepted"]
    assert not r.finish("lesson", "presenter", {k: old[k] for k in ("id","epoch","generation")} | {"outcome": {"status":"error"}}, now=101)
    job = r.lease("lesson", "presenter", now=101)[0]
    outcome = probe.run([{"seed": job["binding"]["seed"], "binding": job["binding"], "text": job["text"]}])[0]["outcome"]
    assert r.finish("lesson", "presenter", {k: job[k] for k in ("id","epoch","generation")} | {"outcome":outcome}, now=102)
    r.drain("lesson")
    for role, surface in (("participant","participant-input"), ("presenter","presenter-controls"),
                          ("presenter","presenter-overlay"), ("projector","projector-overlay")):
        result = r.view("lesson", TYPE, "construct", role=role, surface=surface, actor="alice")
        if role == "participant": assert "feedback" not in result["data"]["own"]
        if role == "presenter": assert result["data"]["counts"]["correct"] == 1
    reset = envelope("_reset", {}, "reset0000001")
    assert r.command("lesson", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("lesson", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("lesson", "alice", "participant", first | {"request_id":"late00000001"})["error"] == "stale-epoch"
    assert not r.finish("lesson", "presenter", {k: job[k] for k in ("id","epoch","generation")} | {"outcome":outcome}, now=103)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="needs pdfLaTeX")
def test_installed_authoring_all_editions_and_freshness(tmp_path, provider):
    from texstage.build.builder import BuildOptions, build
    from texstage.build.latex import compile_deck
    from texstage.build.compiler import compile_latex
    from texstage.build.pdf import Pdf
    from texstage.plugins.policy import enable
    from texstage.server.bundles import load_bundle
    deck = tmp_path / "deck"
    shutil.copytree(ROOT / "examples/relational", deck)
    catalog = Catalog([provider])
    profile = tmp_path / "profile"
    enable(profile, provider.id, provider.version, provider.payload)
    options = BuildOptions(stage=True, key="relational-test-key", activities=deck / "lesson.activities.json",
                           plugin_data=profile, height=540)
    out = tmp_path / "out"
    result = build(deck / "lesson.tex", out, options)
    assert not result.problems
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert set(bundle.items[TYPE]) == {"construct", "rewrite"}
    public = model.canonical(bundle.deck_json)
    assert '"expected"' not in public and '"worked"' not in public and '"evaluations"' not in public
    assert not list(result.bundle.rglob("*.tex")) and not list(result.bundle.rglob("*.activities.json"))
    assert bundle.file("keys.json") is None and result.static.is_file()
    def text(path):
        with Pdf(path) as pdf: return " ".join(page.text() for page in pdf)
    handout = compile_deck(deck / "lesson.tex", "handout", out, plugins=catalog, preparation=options.preparation)
    assert "One worked answer" not in text(handout.pdf)
    assert "One worked answer" not in text(result.stage.pdf)
    assert "One worked answer" in text(out / "build/lesson-solutions.pdf")
    exported = options.preparation.export(deck / "lesson.tex", catalog)
    for edition in ("handout", "solutions"):
        direct = compile_latex(exported[edition], output_dir=out / ("direct-" + edition), passes=2)
        assert direct.returncode == 0, direct.stdout[-3000:]
        assert ("One worked answer" in text(direct.pdf)) == (edition == "solutions")
    path = deck / "activities/construct.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    stale = compile_latex(exported["handout"], output_dir=out / "stale")
    assert stale.returncode != 0 and "Stale prepared input" in stale.log_text


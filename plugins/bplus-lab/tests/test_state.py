# SPDX-License-Identifier: Apache-2.0
"""Installed B3 protocol: feedback, races, real receipts, privacy and byte budgets."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.contracts import validate_portable_schema
from texstage.plugins.runtime import Runtime
from texstage_bplus_lab import model
from texstage_bplus_lab.authoring import prepare_lesson, TYPE
from texstage_bplus_lab.state import (
    Lesson, MAX_ACTORS, MAX_VERSION, SLOT_BYTES, FEEDBACK_RESERVE, STATE_BYTES,
    TRANSITION_BYTES, VIEW_BYTES, actor_key, size, replay_steps,
)
from test_engine import probe, exercise

ROOT = Path(__file__).resolve().parents[3]
SURFACES = (("participant", "participant-input"), ("presenter", "presenter-controls"),
            ("presenter", "presenter-overlay"), ("projector", "projector-overlay"))


@pytest.fixture(scope="module")
def provider():
    p, _ = probe.installed()
    import texstage_bplus_lab.state
    assert Path(texstage_bplus_lab.state.__file__).is_relative_to(Path(sys.prefix))
    return p


def source(name="insert"):
    return json.loads((ROOT / "examples/bplus/activities" / (name + ".json")).read_text(encoding="utf-8"))


def context(name="insert", policy="on-reveal"):
    value = source(name)
    value["feedback"] = policy
    spec = json_value(prepare_lesson(value, {}))["prepared"]
    spec["evaluations"]["analysis"]["engine"] = probe.ENGINE
    return {"item": spec, "epoch": 1, "role": "participant"}


def command(op, payload, actor="alice", request="request00001"):
    return {"kind": "command", "operation": op, "payload": payload, "actor": actor, "request_id": request}


def advance(state, event, ctx):
    old = copy.deepcopy(state)
    result = json_value(Lesson().transition(state, event, ctx))
    assert state == old
    assert "refusal" not in result, result
    return result["state"], result["effects"]


def control(state, ctx, op, **payload):
    return advance(state, command(op, {"control_version": state["control_version"], **payload}),
                   ctx | {"role": "presenter"})


def opened(name="insert", policy="on-reveal"):
    ctx = context(name, policy)
    state = Lesson().initial_state(ctx["item"], ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    state, _ = control(state, ctx, "open")
    return state, ctx


def submission(state, ctx, actor="alice", request="request00001", answer=None):
    return command("submit-answer", {
        "phase_version": state["phase_version"],
        "answer_version": state["answers"].get(actor_key(actor), {}).get("version", 0),
        "answer": copy.deepcopy(answer if answer is not None else ctx["item"]["private"]["worked"]["answer"]),
    }, actor, request)


def submit(state, ctx, **kw):
    return advance(state, submission(state, ctx, **kw), ctx)


def complete(state, ctx, actor="alice", outcome=None, **changes):
    slot = state["answers"][actor_key(actor)]
    if outcome is None:
        outcome = {"status": "ok", "data": model.analyze(json.loads(ctx["item"]["evaluations"]["analysis"]["seed"]), slot["answer"])}
    return advance(state, {"kind": "evaluation.finished", "actor": actor, "binding": "analysis",
        "correlation_id": slot["correlation"], "outcome": outcome, **changes}, ctx)[0]


def view(state, ctx, role="participant", actor="alice", surface=None):
    surface = surface or {"participant": "participant-input", "presenter": "presenter-controls",
                           "projector": "projector-overlay"}[role]
    return Lesson().view(state, {"role": role, "actor": actor, "surface": surface}, ctx)


def refusal(state, ctx, event, expected):
    original = copy.deepcopy(state)
    assert Lesson().transition(state, event, ctx) == {"refusal": expected}
    assert state == original


@pytest.mark.parametrize("name", ["lookup", "range", "insert", "delete", "cascade", "shrink", "empty", "last", "large"])
@pytest.mark.parametrize("policy", ["on-reveal", "immediate"])
def test_all_tasks_saved_feedback_release(provider, name, policy):
    state, ctx = opened(name, policy)
    state, effects = submit(state, ctx)
    assert len(effects) == 1 and effects[0]["binding"] == "analysis"
    state = complete(state, ctx)
    own = view(state, ctx)["own"]
    assert own["status"] == "saved" and ("feedback" in own) == (policy == "immediate")
    assert "own" not in view(state, ctx, actor="bob")
    assert "worked" not in view(state, ctx, "projector")
    state, _ = control(state, ctx, "close")
    state, _ = control(state, ctx, "reveal")
    assert view(state, ctx)["own"]["feedback"]["correct"] is True
    for role, surface in SURFACES:
        projected = view(state, ctx, role, surface=surface)
        assert projected["worked"]["answer"] == ctx["item"]["private"]["worked"]["answer"]
        raw = model.canonical(projected)
        for forbidden in ('"exercise_digest":', '"correlation":', '"binding":', '"evaluations":', '"analysis":'):
            assert forbidden not in raw
        if role != "presenter":
            assert actor_key("alice") not in raw
    refusal(state, ctx | {"role": "presenter"}, command("open", {"control_version": state["control_version"]}), "reset-required")


def test_different_valid_repairs_are_not_reference_equality(provider):
    fixtures = probe.fixture(provider, "design-cases.json")
    groups = {}
    for row in fixtures["cases"]:
        seed = exercise(fixtures, row)
        groups.setdefault(model.canonical(seed), []).append(row["answer"])
    alternatives = [answers for answers in groups.values() if len({model.canonical(a) for a in answers}) > 1]
    assert alternatives
    for seed_text, answers in groups.items():
        if len({model.canonical(a) for a in answers}) < 2:
            continue
        ctx = context()
        lesson = source()
        lesson["exercise"], lesson["worked"]["answer"] = json.loads(seed_text), answers[0]
        ctx["item"] = json_value(prepare_lesson(lesson, {}))["prepared"]
        ctx["item"]["evaluations"]["analysis"]["engine"] = probe.ENGINE
        state = Lesson().initial_state(ctx["item"], ctx)
        state, _ = advance(state, {"kind": "activate"}, ctx)
        state, _ = control(state, ctx, "open")
        for index, answer in enumerate(answers):
            state, _ = submit(state, ctx, actor="actor" + str(index), answer=answer)
            state = complete(state, ctx, actor="actor" + str(index))
            assert state["answers"][actor_key("actor" + str(index))]["feedback"]["correct"]


@pytest.mark.parametrize("fault,reason", [
    ("path", "wrong-path"), ("repair", "missing-repair"), ("split", "wrong-separator"),
    ("height", "prediction"), ("separator", "prediction"), ("keys", "prediction"), ("scan", "wrong-scan"),
])
def test_specific_domain_feedback(provider, fault, reason):
    state, ctx = opened("range" if fault in ("keys", "scan") else "insert")
    answer = copy.deepcopy(ctx["item"]["private"]["worked"]["answer"])
    if fault == "path": answer["path"] = [63]
    elif fault == "repair": answer["repairs"] = []
    elif fault == "split": answer["repairs"][0]["separator"] += 1
    elif fault == "height": answer["height"] = 3
    elif fault == "separator": answer["separators"][0]["keys"][0] += 1
    elif fault == "keys": answer["keys"] = []
    else: answer["leaves"] = [63]
    state, _ = submit(state, ctx, answer=answer)
    state = complete(state, ctx)
    feedback = state["answers"][actor_key("alice")]["feedback"]
    assert feedback["code"] == "revise" and feedback["correct"] is False and feedback["reason"] == reason


@pytest.mark.parametrize("fault", ["exercise", "answer", "operation", "claims", "metrics", "tree", "missing", "bool", "extra"])
def test_forged_facts_do_not_grade(provider, fault):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    slot = state["answers"][actor_key("alice")]
    facts = model.analyze(json.loads(ctx["item"]["evaluations"]["analysis"]["seed"]), slot["answer"])
    if fault in ("exercise", "answer"): facts[fault] = "0" * 64
    elif fault == "operation": facts["operation"] = "delete"
    elif fault == "claims": facts["claims"]["height"] = False
    elif fault == "metrics": facts["metrics"]["splits"] += 1
    elif fault == "tree": facts["final"]["root"] = 63
    elif fault == "missing": del facts["replay"]
    elif fault == "bool": facts["metrics"]["height_after"] = True
    else: facts["extra"] = 1
    state = complete(state, ctx, outcome={"status": "ok", "data": facts})
    own = view(state, ctx)["own"]
    assert own["status"] == "unavailable" and "correct" not in own["feedback"]


@pytest.mark.parametrize("status", ["syntax", "refused", "error", "timeout", "cancelled"])
def test_operational_failure_preserves_answer_without_wrong_grade(provider, status):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    state = complete(state, ctx, outcome={"status": status})
    own = view(state, ctx)["own"]
    assert own["answer"] == ctx["item"]["private"]["worked"]["answer"]
    assert own["feedback"] == {"code": "unavailable", "reason": "evaluation"}


@pytest.mark.parametrize("field", ["engine", "seed", "options", "references", "extra"])
def test_complete_persisted_binding_identity(provider, field):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    facts = copy.deepcopy(ctx["item"]["private"]["worked"]["analysis"])
    ctx["item"]["evaluations"]["analysis"][field] = "changed"
    state = complete(state, ctx, outcome={"status": "ok", "data": facts})
    assert view(state, ctx)["own"]["feedback"] == {"code": "unavailable", "reason": "binding"}


def test_versions_pending_close_navigation_and_late_completion(provider):
    state, ctx = opened()
    first = submission(state, ctx)
    state, effects = advance(state, first, ctx)
    old_correlation = effects[0]["correlation_id"]
    state, effects = submit(state, ctx, actor="bob")  # identical request IDs, different authenticated actors
    assert effects[0]["correlation_id"] != old_correlation
    refusal(state, ctx, first | {"request_id": "seconddevice"}, "stale-answer")
    state, effects = submit(state, ctx, request="replacement1")
    assert [e["kind"] for e in effects] == ["cancel-evaluation", "evaluate"]
    assert effects[0]["correlation_id"] == old_correlation
    original = copy.deepcopy(state)
    assert complete(state, ctx, correlation_id=old_correlation) == original
    assert complete(state, ctx | {"epoch": 2}) == original
    assert complete(state, ctx, binding="other") == original
    state, effects = advance(state, {"kind": "deactivate"}, ctx)
    assert state["phase"] == "closed" and not effects and state["answers"][actor_key("alice")]["status"] == "pending"
    state = complete(state, ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    assert state["phase"] == "closed" and state["answers"][actor_key("alice")]["status"] == "saved"
    state, _ = control(state, ctx, "open")
    stale = submission(state, ctx, actor="charlie")
    stale["payload"]["phase_version"] -= 1
    refusal(state, ctx, stale, "stale-phase")


def test_private_selection_anonymous_predictions_and_bounded_replay(provider):
    state, ctx = opened()
    answer = copy.deepcopy(ctx["item"]["private"]["worked"]["answer"])
    answer["height"] = 3
    state, _ = submit(state, ctx, answer=answer)
    state = complete(state, ctx)
    target = {"actor": actor_key("alice"), "answer_version": 1}
    state, _ = control(state, ctx, "select-answer", **target)
    assert view(state, ctx, "presenter")["selected"]["feedback"]["correct"] is False
    for role, surface in SURFACES:
        if surface != "presenter-controls":
            assert "selected" not in view(state, ctx, role, surface=surface)
    teacher = ctx | {"role": "presenter"}
    refusal(state, teacher, command("replay-step", {"control_version": state["control_version"], "source": "worked", "step": 0}), "unrevealed")
    refusal(state, teacher, command("replay-step", {"control_version": state["control_version"], "source": "shared", "step": 0}), "missing-share")
    state, _ = control(state, ctx, "close")
    state, _ = control(state, ctx, "share-answer", **target)
    for step, focus in enumerate(replay_steps(answer)):
        state, _ = control(state, ctx, "replay-step", source="shared", step=step)
        projected = view(state, ctx, "projector")
        assert projected["demonstration"] == {"answer": answer}
        assert projected["replay"]["focus"] == focus
        raw = model.canonical(projected)
        assert actor_key("alice") not in raw and "feedback" not in raw and "selected" not in raw and "worked" not in raw
    refusal(state, teacher, command("replay-step", {"control_version": state["control_version"], "source": "shared", "step": len(replay_steps(answer))}), "replay-step")
    state, _ = control(state, ctx, "clear-share")
    assert "replay" not in view(state, ctx, "projector")
    state, _ = control(state, ctx, "open")
    state, _ = submit(state, ctx, request="replacement1")
    assert state["selected"] is None and state["shared"] is None
    state, _ = control(state, ctx, "close")
    refusal(state, teacher, command("share-answer", {"control_version": state["control_version"], **target}), "stale-answer")
    state, _ = control(state, ctx, "reveal")
    state, _ = control(state, ctx, "replay-step", source="worked", step=0)
    assert view(state, ctx, "projector")["replay"]["source"] == "worked"


def test_capacity_portable_views_and_worst_escaped_budgets(provider, tmp_path):
    state, ctx = opened("large")
    ctx["epoch"] = 9007199254740991
    ctx["item"]["private"]["worked"]["explanation"] = {k: "\U0001f333" * 1200 for k in ("en", "de")}
    answer = {"format": 1, "path": [63] * 3, "repairs": [
        {"op": "split", "node": 63, "left_count": 6, "separator": -9999}] * 3,
        "separators": [{"node": 63, "keys": [-9999] * 5}] * 10, "height": 3}
    actors = [("\U0001f333" * 250) + str(i).zfill(6) for i in range(MAX_ACTORS)]
    maximum_slot = maximum_transition = 0
    cases, views = [], {}
    content = provider.manifest["capabilities"]["content_types"][TYPE]
    for actor in actors:
        state, effects = submit(state, ctx, actor=actor, answer=answer)
        key = actor_key(actor)
        state["answers"][key]["version"] = MAX_VERSION - 1
        maximum_transition = max(maximum_transition, size({"state": state, "effects": effects}))
        reserve = state["answers"][key] | {"version": MAX_VERSION, "feedback": "x" * FEEDBACK_RESERVE}
        maximum_slot = max(maximum_slot, size({key: reserve}))
    refusal(state, ctx, submission(state, ctx, actor="one-more", answer=answer), "capacity")
    state, effects = submit(state, ctx, actor=actors[0], request="replacement1", answer=answer)
    assert len(effects) == 2 and state["answers"][actor_key(actors[0])]["version"] == MAX_VERSION
    maximum_transition = max(maximum_transition, size({"state": state, "effects": effects}))
    for actor in actors:
        state = complete(state, ctx, actor=actor)
    for op in ("close", "reveal"):
        state, _ = control(state, ctx, op)
    state, _ = control(state, ctx, "select-answer", actor=actor_key(actors[0]), answer_version=MAX_VERSION)
    state, _ = control(state, ctx, "share-answer", actor=actor_key(actors[0]), answer_version=MAX_VERSION)
    state, _ = control(state, ctx, "replay-step", source="worked", step=0)
    state["phase_version"] = state["control_version"] = MAX_VERSION
    maximum_transition = max(maximum_transition, size({"state": state, "effects": effects}))
    for role, surface in SURFACES:
        value = view(state, ctx, role, actors[0], surface)
        schema = json.loads(provider.resources[content["view_schemas"][surface]])
        validate_portable_schema(schema)
        Draft202012Validator(schema).validate(value)
        views[surface] = size(value)
        cases.append({"schema": schema, "value": value, "expected": True})
        for field in ("private", "correlation", "extra"):
            bad = copy.deepcopy(value); bad[field] = "not allowed"
            assert list(Draft202012Validator(schema).iter_errors(bad))
            cases.append({"schema": schema, "value": bad, "expected": False})
    assert maximum_slot <= SLOT_BYTES and size(state) <= STATE_BYTES and maximum_transition <= TRANSITION_BYTES
    assert max(views.values()) <= VIEW_BYTES and size({"state": state, "effects": effects}) < 256 * 1024
    # Even slots filled to the admission ceiling leave room for shared state/effects.
    assert MAX_ACTORS * SLOT_BYTES + 16 * 1024 <= STATE_BYTES
    assert len(actors[0]) == 256 and len(actor_key(actors[0])) == 64 and actors[0] not in model.canonical(state)
    import texstage
    config = tmp_path / "contracts.json"
    config.write_text(json.dumps({"module": (Path(texstage.__file__).parent / "web/stage/plugin-contracts.js").as_uri(),
                                  "cases": cases}), encoding="utf-8")
    subprocess.run(["node", str(ROOT / "maintenance/check_bplus_lesson_contracts.mjs"), str(config)], check=True)
    report = {"actors": MAX_ACTORS, "answer_bytes": size(answer), "reserved_slot_bytes": maximum_slot,
              "state_bytes": size(state), "transition_bytes": maximum_transition, "view_bytes": views,
              "validator_cases": len(cases), "capacity_claim": "storage only; no throughput measurement"}
    output = Path(os.environ.get("BPLUS_REPORT_DIR", tmp_path))
    output.mkdir(parents=True, exist_ok=True)
    (output / "budgets.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def runtime(tmp_path, provider):
    r = Runtime(tmp_path / "runtime.sqlite3", Catalog([provider]))
    r.ensure("session", TYPE, "insert", context()["item"])
    r.activate("session", {(TYPE, "insert")})
    yield r
    r.close()


def envelope(op, payload, request="request00001", epoch=1):
    return {"type": TYPE, "item": "insert", "operation": op, "payload": payload,
            "epoch": epoch, "expected_revision": 0, "request_id": request}


def test_real_runtime_receipts_full_queue_close_finish_reset(runtime, monkeypatch):
    r = runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING", 1)
    assert r.command("session", "teacher", "presenter", envelope("open", {"control_version": 0}))["accepted"]
    payload = {"phase_version": 1, "answer_version": 0, "answer": source()["worked"]["answer"]}
    first = envelope("submit-answer", payload)
    receipt = r.command("session", "alice", "participant", first)
    assert receipt["accepted"] and r.command("session", "alice", "participant", first) == receipt
    with pytest.raises(PluginError, match="reused"):
        r.command("session", "alice", "participant", first | {"payload": payload | {"answer_version": 1}})
    assert r.command("session", "alice", "participant", first | {"request_id": "seconddevice1"})["error"] == "stale-answer"
    assert r.command("session", "teacher2", "presenter", envelope("close", {"control_version": 0}))["error"] == "stale-control"
    with pytest.raises(PluginError) as error:
        r.command("session", "bob", "participant", first)
    assert error.value.code == "queue-full"
    assert "own" not in r.view("session", TYPE, "insert", "participant", "participant-input", "bob")["data"]
    old = r.lease("session", "evaluator", now=100)[0]
    replacement = envelope("submit-answer", payload | {"answer_version": 1}, "replacement01")
    assert r.command("session", "alice", "participant", replacement)["accepted"]
    assert not r.finish("session", "evaluator", {k: old[k] for k in ("id", "epoch", "generation")} | {"outcome": {"status": "error"}}, now=101)
    job = r.lease("session", "evaluator", now=101)[0]
    assert r.command("session", "teacher", "presenter", envelope("close", {"control_version": 1}, "close0000001"))["accepted"]
    outcome = probe.run([{"seed": job["binding"]["seed"], "binding": job["binding"], "text": job["text"]}])[0]["outcome"]
    result = {k: job[k] for k in ("id", "epoch", "generation")} | {"outcome": outcome}
    assert not r.finish("session", "wrong-evaluator", result, now=102)
    assert not r.finish("session", "evaluator", result | {"epoch": 2}, now=102)
    assert r.finish("session", "evaluator", result, now=102)
    r.drain("session")
    before = r.view("session", TYPE, "insert", "participant", "participant-input", "alice")
    assert before["data"]["own"]["status"] == "saved" and "feedback" not in before["data"]["own"]
    r.drain("session")
    assert r.view("session", TYPE, "insert", "participant", "participant-input", "alice") == before
    assert r.command("session", "teacher", "presenter", envelope("reveal", {"control_version": 2}, "reveal000001"))["accepted"]
    assert r.view("session", TYPE, "insert", "participant", "participant-input", "alice")["data"]["own"]["feedback"]["correct"]
    reset = envelope("_reset", {}, "reset0000001")
    assert r.command("session", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("session", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("session", "teacher2", "presenter", reset | {"request_id": "reset0000002"})["error"] == "stale-epoch"
    assert not r.finish("session", "evaluator", result, now=103)
    assert r.view("session", TYPE, "insert", "participant", "participant-input", "alice")["data"]["count"] == 0


@pytest.mark.parametrize("mutation", ["bool", "extra", "role", "foreign-seed", "actor", "wrong-answer", "wrong-surface"])
def test_runtime_boundaries(runtime, mutation):
    payload, role, op = {"control_version": 0}, "presenter", "open"
    if mutation == "bool": payload["control_version"] = False
    elif mutation == "extra": payload["html"] = "<script>"
    elif mutation == "foreign-seed": payload["seed"] = "replacement"
    elif mutation == "actor": payload["actor"] = "bob"
    elif mutation == "role": role = "participant"
    elif mutation == "wrong-answer":
        op, role = "submit-answer", "participant"
        payload = {"phase_version": 0, "answer_version": 0, "answer": {"format": 1, "path": [True], "keys": []}}
    else:
        with pytest.raises(PluginError):
            runtime.view("session", TYPE, "insert", "participant", "presenter-controls", "alice")
        return
    with pytest.raises(PluginError):
        runtime.command("session", "actor", role, envelope(op, payload))


def test_restart_receipts_and_queued_delivery(tmp_path, provider):
    db = tmp_path / "restart.sqlite3"
    catalog = Catalog([provider])
    r = Runtime(db, catalog)
    message = envelope("submit-answer", {"phase_version": 1, "answer_version": 0, "answer": source()["worked"]["answer"]})
    try:
        r.ensure("session", TYPE, "insert", context()["item"])
        r.activate("session", {(TYPE, "insert")})
        r.command("session", "teacher", "presenter", envelope("open", {"control_version": 0}))
        receipt = r.command("session", "alice", "participant", message)
        job = r.lease("session", "evaluator", now=100)[0]
        outcome = probe.run([{"seed": job["binding"]["seed"], "binding": job["binding"], "text": job["text"]}])[0]["outcome"]
        assert r.finish("session", "evaluator", {k: job[k] for k in ("id", "epoch", "generation")} | {"outcome": outcome}, now=101)
    finally:
        r.close()
    r = Runtime(db, catalog)
    try:
        r.drain("session")
        assert r.command("session", "alice", "participant", message) == receipt
        before = r.view("session", TYPE, "insert", "presenter", "presenter-controls")
        assert before["data"]["counts"]["saved"] == 1
        r.drain("session")
        assert r.view("session", TYPE, "insert", "presenter", "presenter-controls") == before
    finally:
        r.close()


def test_unavailable_evaluator_retries_expire_as_operational_feedback(runtime):
    r = runtime
    r.command("session", "teacher", "presenter", envelope("open", {"control_version": 0}))
    r.command("session", "alice", "participant", envelope("submit-answer", {
        "phase_version": 1, "answer_version": 0, "answer": source()["worked"]["answer"]}))
    assert r.view("session", TYPE, "insert", "participant", "participant-input", "alice")["data"]["own"]["status"] == "pending"
    for now in (100, 221, 342):
        assert len(r.lease("session", "lost-evaluator", now=now)) == 1
    assert r.lease("session", "replacement-evaluator", now=463) == []
    r.drain("session")
    own = r.view("session", TYPE, "insert", "participant", "participant-input", "alice")["data"]["own"]
    assert own["status"] == "unavailable" and own["feedback"]["code"] == "unavailable"


def test_existing_actor_replaces_at_full_class_and_full_queue(runtime, monkeypatch):
    r = runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING", MAX_ACTORS)
    r.command("session", "teacher", "presenter", envelope("open", {"control_version": 0}))
    payload = {"phase_version": 1, "answer_version": 0, "answer": source()["worked"]["answer"]}
    for i in range(MAX_ACTORS):
        assert r.command("session", "actor" + str(i), "participant", envelope("submit-answer", payload))["accepted"]
    assert r.command("session", "newcomer", "participant", envelope("submit-answer", payload))["error"] == "capacity"
    replacement = envelope("submit-answer", payload | {"answer_version": 1}, "replace00001")
    assert r.command("session", "actor0", "participant", replacement)["accepted"]
    assert r.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','leased')").fetchone()[0] == MAX_ACTORS
    own = r.view("session", TYPE, "insert", "participant", "participant-input", "actor0")["data"]["own"]
    assert own["version"] == 2 and own["status"] == "pending"
    old = r.lease("session", "evaluator", now=100)[0]
    assert r.command("session", "teacher", "presenter", envelope("_reset", {}, "resetpending1"))["epoch"] == 2
    assert not r.finish("session", "evaluator", {k: old[k] for k in ("id", "epoch", "generation")} | {"outcome": {"status": "error"}}, now=101)
    r.drain("session")
    assert r.view("session", TYPE, "insert", "presenter", "presenter-controls")["data"]["count"] == 0
    assert r.lease("session", "evaluator", now=102) == []


def test_invalid_operation_shape_and_version_ceiling(provider):
    state, ctx = opened()
    invalid = submission(state, ctx, answer={"format": 1, "path": [0], "keys": []})
    refusal(state, ctx, invalid, "invalid-answer")
    state, _ = submit(state, ctx)
    state["answers"][actor_key("alice")]["version"] = MAX_VERSION
    refusal(state, ctx, submission(state, ctx), "reset-required")
    state["control_version"] = MAX_VERSION
    refusal(state, ctx | {"role": "presenter"}, command("close", {"control_version": MAX_VERSION}), "reset-required")

# SPDX-License-Identifier: Apache-2.0
"""Rubric facts, installed reducer, durable credits and authenticated projections."""
import copy
import json
import pytest
from jsonschema import ValidationError
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog
from texstage.plugins.runtime import Runtime
from texstage_bplus_lab import model
from texstage_bplus_lab.authoring import prepare_lesson, TYPE
from texstage_bplus_lab.grading import grade, WEIGHTS, RUBRIC, path_credit, key_credit, separator_credit
from texstage_bplus_lab.storage import pack_feedback, unpack_feedback
from texstage_bplus_lab.state import FEEDBACK_RESERVE, feedback
from test_engine import exercise, probe
from test_state import source, context, provider, runtime, envelope


def checked(name, mutate=None):
    lesson = source(name)
    answer = copy.deepcopy(lesson["worked"]["answer"])
    if mutate:
        mutate(answer)
    facts = model.analyze(lesson["exercise"], answer)
    return grade(lesson["exercise"], answer, facts)


def test_every_worked_fixture_and_legal_alternative_earns_full_credit(provider):
    fixtures = probe.fixture(provider, "design-cases.json")
    for case in fixtures["cases"]:
        seed, answer = exercise(fixtures, case), case["answer"]
        facts = model.analyze(seed, answer)
        result = grade(seed, answer, facts)
        assert result == {"rubric": RUBRIC, "credit": 1000, "parts": WEIGHTS[seed["task"]["kind"]]}, case
    for name in ("lookup", "range", "insert", "delete", "cascade", "shrink", "empty", "last", "large"):
        assert checked(name)["credit"] == 1000


def test_read_criteria_are_independent_and_penalize_extra_guesses():
    assert checked("lookup", lambda a: a.update(keys=[]))["parts"] == {"path": 400, "keys": 0}
    assert checked("lookup", lambda a: a.update(path=[0, 63]))["parts"] == {"path": 0, "keys": 600}
    assert checked("range", lambda a: a.update(leaves=[2]))["parts"] == {"path": 300, "scan": 200, "keys": 300}
    assert checked("range", lambda a: a.update(path=[0, 63], leaves=[63], keys=[25, 30]))["parts"] == {
        "path": 0, "scan": 0, "keys": 200}
    assert checked("range", lambda a: a.update(keys=[25, 30, 9999]))["parts"]["keys"] == 100
    assert checked("range", lambda a: a.update(keys=[25, 25, 30]))["parts"]["keys"] == 0
    assert checked("range", lambda a: a.update(keys=[40, 30, 25]))["parts"]["keys"] == 0
    assert checked("range", lambda a: a.update(leaves=[2, 3, 3]))["parts"]["scan"] == 266


def test_routing_edges_and_empty_results_are_explicit():
    assert path_credit([0], [0, 1, 2], 200) == 0
    assert path_credit([0, 1], [0, 1, 2], 200) == 100
    assert path_credit([0, 1, 63], [0, 1, 2], 200) == 100
    assert path_credit([0, 1, 2], [0, 1], 200) == 100
    assert path_credit([0], [0], 400) == 400
    assert path_credit([63], [0], 400) == 0
    assert key_credit([], [], 600) == 600
    assert key_credit([5], [], 600) == 0


def test_partial_updates_require_a_verified_legal_replay():
    assert checked("insert", lambda a: a.update(height=3))["credit"] == 900
    assert checked("insert", lambda a: a.update(repairs=[]))["parts"] == {
        "path": 200, "repairs": 0, "separators": 0, "height": 0}
    for repairs, expected in ((0, 0), (1, 100), (2, 200), (3, 500)):
        result = checked("cascade", lambda a: a.update(repairs=a["repairs"][:repairs]))
        assert result["parts"]["repairs"] == expected
        assert result["credit"] == (200 + expected if repairs < 3 else 1000)
    def illegal_second(answer):
        answer["repairs"][1]["node"] = 63
    result = checked("cascade", illegal_second)
    assert result["parts"] == {"path": 200, "repairs": 100, "separators": 0, "height": 0}
    result = checked("cascade", lambda a: a.update(path=[0, 10, 63]))
    assert result["parts"] == {"path": 100, "repairs": 0, "separators": 0, "height": 0}


def test_separator_credit_matches_positions_and_cannot_be_inflated():
    expected = [{"node": 0, "keys": [20, 40]}, {"node": 4, "keys": [60]}]
    assert separator_credit([{"node": 0, "keys": [20, 41]}], expected, 200) == 66
    assert separator_credit(expected + [{"node": 63, "keys": [60]}], expected, 200) == 133
    assert separator_credit(expected + expected, expected, 200) == 0
    assert separator_credit(expected[::-1], expected, 200) == 0
    assert separator_credit([], [], 200) == 200
    assert separator_credit(expected, [], 200) == 0


@pytest.mark.parametrize("points", [True, 1.0, -1, 10001, "1000", None])
def test_author_point_bounds_are_strict(points):
    lesson = source()
    lesson["points"] = points
    with pytest.raises((ValidationError, ValueError)):
        prepare_lesson(lesson, {})


@pytest.mark.parametrize("points", [None, 0, 1, 137, 10000])
def test_practice_default_and_public_rubric(points):
    lesson = source()
    if points is None:
        lesson.pop("points")
    else:
        lesson["points"] = points
    prepared = json_value(prepare_lesson(lesson, {}))["prepared"]
    assert prepared["public"]["points"] == (points or 0)
    assert prepared["public"]["rubric"] == {"id": RUBRIC, "weights": WEIGHTS["insert"]}
    assert "grade" not in prepared["public"]


def test_grade_storage_is_lossless_and_reserved():
    for name in ("lookup", "range", "insert", "delete", "cascade", "shrink"):
        ctx = context(name)
        answer = source(name)["worked"]["answer"]
        for mutated in (answer, answer | {"path": [63]}):
            result = feedback({"answer": mutated}, {"status": "ok", "data": model.analyze(source(name)["exercise"], mutated)}, ctx)
            assert unpack_feedback(pack_feedback(result)) == result
            assert len(model.canonical(pack_feedback(result))) <= FEEDBACK_RESERVE
    # Largest encoding across the four-part rubric and invalid-replay metadata.
    value = {"code": "revise", "correct": False, "reason": "wrong-pending-node",
        "checked_repairs": 3, "at": 20, "node": 63,
        "grade": {"rubric": RUBRIC, "credit": 1000, "parts": WEIGHTS["insert"]}}
    assert unpack_feedback(pack_feedback(value)) == value
    assert len(model.canonical(pack_feedback(value))) <= FEEDBACK_RESERVE


def control(r, op, request=None, epoch=1):
    v = r.view("session", TYPE, "insert", "presenter", "presenter-controls")
    payload = {} if op == "_reset" else {"control_version": v["data"]["control_version"]}
    return r.command("session", "teacher", "presenter", envelope(op, payload, request or ("control_" + op), epoch))


def submit(r, actor="alice", answer=None, request="submit00001"):
    v = r.view("session", TYPE, "insert", "participant", "participant-input", actor)
    return r.command("session", actor, "participant", envelope("submit-answer", {
        "phase_version": v["data"]["phase_version"], "answer_version": v["data"].get("own", {}).get("version", 0),
        "answer": answer or source()["worked"]["answer"]}, request, v["epoch"]))


def resolve(r, job, *, error=False, now=101):
    outcome = {"status": "error"} if error else probe.run([{
        "seed": job["binding"]["seed"], "binding": job["binding"], "text": job["text"]}])[0]["outcome"]
    accepted = r.finish("session", "evaluator", {k: job[k] for k in ("id", "epoch", "generation")} | {"outcome": outcome}, now=now)
    r.drain("session")
    return accepted


def own(r, actor="alice"):
    return r.view("session", TYPE, "insert", "participant", "participant-input", actor)["data"]


def test_runtime_replacement_reveal_late_results_actor_isolation_and_reset(runtime):
    r = runtime
    control(r, "open")
    partial = source()["worked"]["answer"] | {"height": 3}
    receipt = submit(r, answer=partial)
    job = r.lease("session", "evaluator", now=100)[0]
    assert resolve(r, job)
    assert own(r)["scoring"] == {"maximum": 1000, "released": False, "awarded": None}
    assert "feedback" not in own(r)["own"]
    # Pending replacement withdraws the grade; the previous result cannot restore it.
    submit(r, request="replacement01")
    assert own(r)["own"]["status"] == "pending"
    assert not resolve(r, job)
    submit(r, "bob", partial)
    jobs = r.lease("session", "evaluator", now=102)
    assert len(jobs) == 2
    control(r, "close")
    reveal = control(r, "reveal")
    assert r.command("session", "teacher", "presenter", envelope(
        "reveal", {"control_version": 2}, "control_reveal")) == reveal
    assert own(r)["scoring"] == {"maximum": 1000, "released": True, "awarded": None}
    for job in jobs:
        assert resolve(r, job, now=103)
    assert own(r)["own"]["feedback"]["grade"]["credit"] == 1000
    assert own(r, "bob")["own"]["feedback"]["grade"]["credit"] == 900
    assert own(r)["scoring"]["awarded"] == 1000
    assert own(r, "bob")["scoring"]["awarded"] == 900
    audiences = [{"role": "participant", "surface": "participant-input", "actor": actor} for actor in ("bob", "alice", "absent")]
    views = r.views("session", TYPE, "insert", audiences)
    assert [v["data"]["scoring"]["awarded"] for v in views] == [900, 1000, None]
    assert "bob" not in model.canonical(views[1]) and "alice" not in model.canonical(views[0])
    assert not resolve(r, jobs[-1], now=104)
    control(r, "_reset", epoch=1)
    assert own(r)["scoring"] == {"maximum": 1000, "released": False, "awarded": None}
    assert "own" not in own(r)
    assert not resolve(r, jobs[-1], now=105)
    assert r.db.execute("SELECT count(*) FROM point_credits WHERE epoch=2").fetchone()[0] == 0


def test_runtime_failures_are_ungraded_and_practice_never_adds_points(tmp_path, provider):
    r = Runtime(tmp_path / "practice.sqlite3", Catalog([provider]))
    item = context()["item"]; item["public"]["points"] = 0
    try:
        r.ensure("session", TYPE, "insert", item); r.activate("session", {(TYPE, "insert")})
        control(r, "open"); submit(r)
        job = r.lease("session", "evaluator", now=100)[0]
        resolve(r, job)
        control(r, "close"); control(r, "reveal")
        assert own(r)["own"]["feedback"]["grade"]["credit"] == 1000
        assert own(r)["scoring"]["awarded"] is None
        assert r.db.execute("SELECT count(*) FROM point_credits").fetchone()[0] == 0
        control(r, "_reset"); control(r, "open", "reopen00001", epoch=2)
        submit(r, request="newattempt01")
        job = r.lease("session", "evaluator", now=102)[0]
        resolve(r, job, error=True, now=103)
        control(r, "close", "closeagain01", epoch=2); control(r, "reveal", "revealagain1", epoch=2)
        assert own(r)["scoring"]["awarded"] is None
        assert own(r)["own"]["feedback"] == {"code": "unavailable", "reason": "evaluation"}
    finally:
        r.close()

# SPDX-License-Identifier: Apache-2.0
"""Deterministic lesson phases, bounded actor slots and audience projections."""
import copy
from texstage.plugin_api.v1 import (
    CancelEvaluation, Evaluate, Transition, evaluation_correlation, json_value,
)
from . import model

MAX_ACTORS = 64
SLOT_BYTES = 2560
STATE_BYTES = 192 * 1024
MAX_VERSION = 1000000000


def _refuse(code):
    return {"refusal": code}


def _finish(state, effects=()):
    result = Transition(state, list(effects))
    if len(model.canonical(state)) > STATE_BYTES or len(model.canonical(json_value(result))) > 256 * 1024:
        return _refuse("capacity")
    return result


def _feedback(state, actor, outcome, ctx):
    slot = state["answers"][actor]
    if outcome.get("status") != "ok":
        return {"code": "unavailable", "detail": outcome.get("status", "error")}
    data = outcome.get("data", {})
    public, private = ctx["item"]["public"], ctx["item"]["private"]
    if (data.get("format") != "relational-analysis-v1" or
            data.get("exercise") != private["exercise"] or data.get("answer") != slot["digest"] or
            data.get("mode") != public["mode"] or type(data.get("valid")) is not bool):
        return {"code": "unavailable", "detail": "identity"}
    if not data["valid"]:
        return {"code": "invalid", "correct": False}
    expected = {row["id"]: row for row in private["expected"]}
    fixtures = data.get("fixtures", [])
    if (len(fixtures) != len(expected) or any(not isinstance(row, dict) or "id" not in row for row in fixtures) or
            len({row["id"] for row in fixtures}) != len(fixtures) or
            {row["id"] for row in fixtures} != set(expected)):
        return {"code": "unavailable", "detail": "coverage"}
    tree = slot["answer"].get("tree")
    if public["mode"] == "rewrite":
        tree = copy.deepcopy(public["baseline_tree"])
        exercise = {"relations": public["relations"], "task": public["task"]}
        try:
            for step in slot["answer"]["steps"]:
                tree = model.rewrite_tree(exercise, tree, step)
        except (model.DomainError, model.InputError, model.ResourceLimit):
            return {"code": "unavailable", "detail": "certificate"}
        proof = data.get("proof", {})
        if (proof.get("verified") is not True or proof.get("tree") != tree or
                proof.get("steps") != len(slot["answer"]["steps"]) or
                proof.get("baseline_cells") != private["baseline_cells"]):
            return {"code": "unavailable", "detail": "certificate"}
    stats = data.get("public", {})
    trace = stats.get("trace", [])
    if (len(trace) != len(tree) or
            any(not isinstance(row, list) or len(row) != 3 or row[0] != i for i, row in enumerate(trace))):
        return {"code": "unavailable", "detail": "trace"}
    cells = sum(row[1] * row[2] for row, node in zip(trace, tree) if node[0] != "rel")
    if stats.get("cells") != cells:
        return {"code": "unavailable", "detail": "metric"}
    correct = all(row == expected[row["id"]] for row in fixtures)
    if public["mode"] == "rewrite":
        improved = cells < private["baseline_cells"]
        if data["proof"].get("improved") is not improved:
            return {"code": "unavailable", "detail": "metric"}
        correct = correct and bool(slot["answer"]["steps"]) and improved
    return {"code": "checked" if correct else "mismatch", "correct": correct, "cells": cells}


class Lesson:
    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "answers": {}, "selected": None, "shared": None}

    def transition(self, previous, event, ctx):
        state = copy.deepcopy(previous)
        kind = event["kind"]
        effects = []
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
        elif kind == "command":
            operation, payload, actor = event["operation"], event["payload"], event["actor"]
            public = ctx["item"]["public"]
            if operation in ("submit-tree", "submit-rewrite"):
                if ctx["role"] != "participant":
                    return _refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return _refuse("closed")
                if payload["phase"] != state["phase_version"]:
                    return _refuse("stale-phase")
                old = state["answers"].get(actor)
                version = old["version"] if old else 0
                if payload["version"] != version:
                    return _refuse("stale-answer")
                if version >= MAX_VERSION:
                    return _refuse("reset-required")
                mode = "construct" if operation == "submit-tree" else "rewrite"
                if mode != public["mode"]:
                    return _refuse("wrong-mode")
                if not old and len(state["answers"]) >= MAX_ACTORS:
                    return _refuse("capacity")
                try:
                    answer = model.answer(payload["answer"])
                except (model.InputError, model.ResourceLimit):
                    return _refuse("invalid-answer")
                if answer["mode"] != mode:
                    return _refuse("wrong-mode")
                correlation = evaluation_correlation(actor, event["request_id"], "analysis")
                slot = {"version": version + 1, "answer": answer,
                        "digest": model.digest(["relational-answer-v1", answer]),
                        "correlation": correlation, "epoch": ctx["epoch"], "status": "pending"}
                # Reserve space for the largest compact feedback before accepting.
                reserve = slot | {"feedback": {"code": "unavailable", "detail": "certificate",
                                              "correct": False, "cells": 1000000000}}
                if len(model.canonical({actor: reserve})) > SLOT_BYTES:
                    return _refuse("capacity")
                state["answers"][actor] = slot
                if state["shared"] and state["shared"]["actor"] == actor:
                    state["shared"] = None
                if old and old["status"] == "pending":
                    effects.append(CancelEvaluation(old["correlation"]))
                effects.append(Evaluate("analysis", correlation, model.canonical(answer)))
            else:
                if ctx["role"] != "presenter":
                    return _refuse("role")
                if payload["control"] != state["control_version"]:
                    return _refuse("stale-control")
                if state["control_version"] >= MAX_VERSION or state["phase_version"] >= MAX_VERSION:
                    return _refuse("reset-required")
                if operation in ("open", "close", "reveal"):
                    allowed = {"open": ("introduce", "closed", "revealed"),
                               "close": ("open",), "reveal": ("closed",)}
                    if state["phase"] not in allowed[operation]:
                        return _refuse("phase")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[operation]
                    state["phase_version"] += 1
                    if operation == "open":
                        state["shared"] = None
                elif operation in ("select-answer", "select-demonstration"):
                    target = payload["actor"]
                    if target and target not in state["answers"]:
                        return _refuse("missing-answer")
                    if operation == "select-answer":
                        state["selected"] = target or None
                    else:
                        if state["phase"] not in ("closed", "revealed"):
                            return _refuse("phase")
                        state["shared"] = ({"actor": target, "version": state["answers"][target]["version"]}
                                           if target else None)
                else:
                    return _refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            actor = event["actor"]
            own = state["answers"].get(actor)
            if (own and own["status"] == "pending" and own["epoch"] == ctx["epoch"] and
                    own["correlation"] == event["correlation_id"] and event["binding"] == "analysis"):
                own["feedback"] = _feedback(state, actor, event["outcome"], ctx)
                own["status"] = "unavailable" if own["feedback"]["code"] == "unavailable" else "saved"
                if len(model.canonical({actor: own})) > SLOT_BYTES:
                    # Replace only compact feedback; never silently discard an accepted answer.
                    own["feedback"] = {"code": "unavailable", "detail": "capacity"}
                    own["status"] = "unavailable"
        return _finish(state, effects)

    def view(self, state, audience, ctx):
        role = audience["role"]
        public = ctx["item"]["public"]
        released = state["phase"] == "revealed"
        view = {k: state[k] for k in ("phase", "phase_version", "active")}
        view["count"] = len(state["answers"])
        if role == "participant":
            own = state["answers"].get(audience["actor"])
            if own:
                view["own"] = {k: copy.deepcopy(own[k]) for k in ("version", "answer", "status")}
                if released and "feedback" in own:
                    # Operational details and private fixture diagnostics remain private.
                    view["own"]["feedback"] = {k: v for k, v in own["feedback"].items() if k != "detail"}
        if role == "presenter":
            view["control_version"] = state["control_version"]
            view["counts"] = {"pending": 0, "correct": 0, "incorrect": 0, "unavailable": 0}
            view["participants"] = []
            for index, (actor, slot) in enumerate(state["answers"].items(), 1):
                category = slot["status"] if slot["status"] in ("pending", "unavailable") else (
                    "correct" if slot["feedback"]["correct"] else "incorrect")
                view["counts"][category] += 1
                view["participants"].append({"actor": actor, "number": index, "status": category})
            selected = state["answers"].get(state["selected"])
            if selected:
                view["selected"] = {k: copy.deepcopy(selected[k]) for k in ("version", "answer", "status")}
                if "feedback" in selected:
                    view["selected"]["feedback"] = copy.deepcopy(selected["feedback"])
        if role in ("presenter", "projector"):
            shared = state["shared"]
            if shared:
                slot = state["answers"].get(shared["actor"])
                if slot and slot["version"] == shared["version"]:
                    view["demonstration"] = copy.deepcopy(slot["answer"])
        if released or role == "presenter":
            worked = ctx["item"]["private"]["worked"]
            view["worked"] = {k: copy.deepcopy(worked[k]) for k in ("answer", "explanation")}
        return view

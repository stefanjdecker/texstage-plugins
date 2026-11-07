# SPDX-License-Identifier: Apache-2.0
"""Bounded classroom state; engine facts are verified before assessment."""
import copy
from texstage.plugin_api.v1 import CancelEvaluation, Evaluate, Transition, evaluation_correlation, json_value
from . import model

MAX_ACTORS = 64
MAX_VERSION = 1000000000
ACTOR_BYTES = 1024
SLOT_BYTES = 3072
STATE_BYTES = 208 * 1024
FAILURES = {"error", "syntax", "refused", "timeout", "cancelled"}


def _refuse(code):
    return {"refusal": code}


def _finish(state, effects=()):
    result = Transition(state, list(effects))
    if len(model.canonical(state)) > STATE_BYTES or len(model.canonical(json_value(result))) > 256 * 1024:
        return _refuse("capacity")
    return result


def _actor_ok(actor):
    return (type(actor) is str and 1 <= len(actor) <= 256 and
            len(model.canonical(actor)) <= ACTOR_BYTES)


def _feedback(slot, outcome, ctx):
    if outcome.get("status") != "ok":
        status = outcome.get("status")
        return {"code": "unavailable", "detail": status if status in FAILURES else "error"}
    data = outcome.get("data")
    private, public = ctx["item"]["private"], ctx["item"]["public"]
    if (type(data) is not dict or data.get("format") != model.FORMAT or data.get("model") != model.MODEL or
            data.get("exercise") != private["exercise"] or data.get("answer") != slot["digest"]):
        return {"code": "unavailable", "detail": "identity"}
    # At most five nodes. Never enumerate references in a reducer or projection.
    expected = model.analyze(public["exercise"], slot["answer"])
    try:
        same = model.canonical(data) == model.canonical(expected)
    except (TypeError, ValueError):
        same = False
    if not same:
        return {"code": "unavailable", "detail": "facts"}
    if not expected["valid"]:
        return {"code": "invalid", "correct": False, "reason": expected["reason"], "node": expected["node"]}
    goal = public["goal"]
    correct = (expected["cost"] == private["reference"]["cost"] if goal["kind"] == "best" else
               expected["cost"] <= goal["max_cost"])
    return {"code": "goal-met" if correct else "target-missed", "correct": correct, "cost": expected["cost"]}


def _own(slot, feedback=False, detail=False):
    result = {k: copy.deepcopy(slot[k]) for k in ("version", "answer", "status")}
    if feedback and "feedback" in slot:
        result["feedback"] = {k: v for k, v in slot["feedback"].items() if detail or k != "detail"}
    return result


class Lesson:
    """State schema 2; Q2's read-only state must stay in its original environment."""
    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "answers": {}, "selected": None, "shared": None}

    def transition(self, previous, event, ctx):
        state = copy.deepcopy(previous)
        kind = event["kind"]
        effects = []
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
            if kind == "deactivate":
                state["shared"] = None
                if state["phase"] == "open":
                    state["phase"] = "closed"
                    # A saturated counter requires reset; navigation still closes safely.
                    state["phase_version"] = min(MAX_VERSION, state["phase_version"] + 1)
                    state["control_version"] = min(MAX_VERSION, state["control_version"] + 1)
        elif kind == "command":
            op, payload, actor = event["operation"], event["payload"], event["actor"]
            if op == "submit-plan":
                if ctx["role"] != "participant":
                    return _refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return _refuse("closed")
                if type(payload["phase"]) is not int or payload["phase"] != state["phase_version"]:
                    return _refuse("stale-phase")
                old = state["answers"].get(actor)
                version = old["version"] if old else 0
                if type(payload["version"]) is not int or payload["version"] != version:
                    return _refuse("stale-answer")
                if version >= MAX_VERSION:
                    return _refuse("reset-required")
                if not _actor_ok(actor) or (not old and len(state["answers"]) >= MAX_ACTORS):
                    return _refuse("capacity")
                try:
                    answer = model.answer(payload["answer"])
                except (model.InputError, model.ResourceLimit):
                    return _refuse("invalid-answer")
                correlation = evaluation_correlation(actor, event["request_id"], "analysis")
                slot = {"version": version + 1, "number": old["number"] if old else len(state["answers"]) + 1, "answer": answer,
                        "digest": model.digest(["query-plan-answer-v1", answer]),
                        "correlation": correlation, "epoch": ctx["epoch"], "status": "pending"}
                # Reserve an upper bound for every compact feedback variant, including
                # escaped actor keys, even while this answer is still pending.
                reserve = slot | {"version": MAX_VERSION, "status": "unavailable", "feedback": {
                    "code": "target-missed", "correct": False, "cost": model.COST_MAX,
                    "reason": "disconnected-join", "node": 4, "detail": "cancelled"}}
                if len(model.canonical({actor: reserve})) > SLOT_BYTES:
                    return _refuse("capacity")
                state["answers"][actor] = slot
                for selected in ("selected", "shared"):
                    if state[selected] and state[selected]["actor"] == actor:
                        state[selected] = None
                if old and old["status"] == "pending":
                    effects.append(CancelEvaluation(old["correlation"]))
                effects.append(Evaluate("analysis", correlation, model.canonical(answer)))
            else:
                if ctx["role"] != "presenter":
                    return _refuse("role")
                if type(payload["control"]) is not int or payload["control"] != state["control_version"]:
                    return _refuse("stale-control")
                if state["control_version"] >= MAX_VERSION or state["phase_version"] >= MAX_VERSION:
                    return _refuse("reset-required")
                if not state["active"]:
                    return _refuse("inactive")
                if op in ("open", "close", "reveal"):
                    if op == "open" and state["phase"] == "revealed":
                        return _refuse("reset-required")
                    allowed = {"open": ("introduce", "closed"), "close": ("open",), "reveal": ("closed",)}
                    if state["phase"] not in allowed[op]:
                        return _refuse("phase")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[op]
                    state["phase_version"] += 1
                    if op == "open":
                        state["shared"] = None
                elif op == "select-answer":
                    target = payload["actor"]
                    if target is not None and target not in state["answers"]:
                        return _refuse("missing-answer")
                    state["selected"] = ({"actor": target, "version": state["answers"][target]["version"]}
                                         if target is not None else None)
                elif op == "share-selected":
                    if state["phase"] not in ("closed", "revealed"):
                        return _refuse("phase")
                    selected = state["selected"]
                    if not selected or state["answers"].get(selected["actor"], {}).get("version") != selected["version"]:
                        return _refuse("missing-answer")
                    state["shared"] = copy.deepcopy(selected)
                elif op == "clear-shared":
                    state["shared"] = None
                else:
                    return _refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            own = state["answers"].get(event["actor"])
            if (own and own["status"] == "pending" and own["epoch"] == ctx["epoch"] and
                    own["correlation"] == event["correlation_id"] and event["binding"] == "analysis"):
                own["feedback"] = _feedback(own, event["outcome"], ctx)
                own["status"] = "unavailable" if own["feedback"]["code"] == "unavailable" else "saved"
                if len(model.canonical({event["actor"]: own})) > SLOT_BYTES:
                    # Defensive invariant: keep an accepted answer if feedback is unavailable.
                    own["feedback"] = {"code": "unavailable", "detail": "capacity"}
                    own["status"] = "unavailable"
        return _finish(state, effects)

    def view(self, state, audience, ctx):
        role = audience["role"]
        if role not in ("presenter", "participant", "projector"):
            raise ValueError("Unknown audience role")
        released = state["phase"] == "revealed"
        view = {k: state[k] for k in ("phase", "phase_version", "active")}
        view["count"] = len(state["answers"])
        if role == "participant":
            own = state["answers"].get(audience["actor"])
            if own:
                view["own"] = _own(own, released)
        if role == "presenter":
            view["control_version"] = state["control_version"]
            view["counts"] = {k: 0 for k in ("pending", "goal-met", "target-missed", "invalid", "unavailable")}
            view["participants"] = []
            for actor, slot in sorted(state["answers"].items(), key=lambda entry: entry[1]["number"]):
                category = slot["status"] if slot["status"] in ("pending", "unavailable") else slot["feedback"]["code"]
                view["counts"][category] += 1
                view["participants"].append({"actor": actor, "number": slot["number"], "status": category})
            selected = state["selected"]
            if selected:
                slot = state["answers"].get(selected["actor"])
                if slot and slot["version"] == selected["version"]:
                    view["selected"] = {"actor": selected["actor"], **_own(slot, True, True)}
        if role in ("presenter", "projector") and state["shared"]:
            shared = state["shared"]
            slot = state["answers"].get(shared["actor"])
            if slot and slot["version"] == shared["version"]:
                view["demonstration"] = copy.deepcopy(slot["answer"])
        if released or role == "presenter":
            private = ctx["item"]["private"]
            view["solution"] = {
                "worked_answer": copy.deepcopy(private["worked"]["answer"]),
                "optimal_answer": copy.deepcopy(private["reference"]["plan"]),
                "explanation": copy.deepcopy(private["worked"]["explanation"]),
                "minimum": private["reference"]["cost"], "ties": private["reference"]["count"]}
        return view

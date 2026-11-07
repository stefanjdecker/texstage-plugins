# SPDX-License-Identifier: Apache-2.0
"""Bounded classroom state; engine facts are verified before assessment."""
import copy
from texstage.plugin_api.v1 import CancelEvaluation, Evaluate, SaveActor, SetCredit, PublishPoints, Transition, evaluation_correlation, json_value
from . import model

MAX_ACTORS = 1000
PAGE_SIZE = 25
MAX_VERSION = 1000000000
ACTOR_BYTES = 1024
SLOT_BYTES = 3072
STATE_BYTES = 16 * 1024
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



def _category(slot):
    return slot["status"] if slot["status"] in ("pending", "unavailable") else slot["feedback"]["code"]


def _record(state, old, slot, effects):
    if old:
        state["counts"][_category(old)] -= 1
    else:
        state["count"] += 1
    state["counts"][_category(slot)] += 1
    effects.append(SaveActor(slot, {"status": _category(slot)}))
    feedback = slot.get("feedback", {})
    credit = 1000 if feedback.get("correct") is True else 0 if feedback.get("correct") is False else None
    effects.append(SetCredit(credit))


class Lesson:
    """State schema 4: bounded shared state plus host-owned actor records."""
    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "count": 0, "records_page": 0,
                "counts": {k: 0 for k in ("pending", "goal-met", "target-missed", "invalid", "unavailable")},
                "selected": None, "shared": None}

    def transition(self, previous, event, ctx):
        state = copy.deepcopy(previous)
        kind, effects = event["kind"], []
        record = ctx.get("records", {"actor": None, "value": None, "number": 1, "count": 0})
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
            if kind == "deactivate":
                state["shared"] = None
                if state["phase"] == "open":
                    state["phase"] = "closed"
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
                if not _actor_ok(actor) or record["actor"] != actor:
                    return _refuse("capacity")
                old = record["value"]
                version = old["version"] if old else 0
                if type(payload["version"]) is not int or payload["version"] != version:
                    return _refuse("stale-answer")
                if version >= MAX_VERSION:
                    return _refuse("reset-required")
                if not old and record["count"] >= MAX_ACTORS:
                    return _refuse("capacity")
                try:
                    answer = model.answer(payload["answer"])
                except (model.InputError, model.ResourceLimit):
                    return _refuse("invalid-answer")
                correlation = evaluation_correlation(actor, event["request_id"], "analysis")
                slot = {"version": version + 1, "number": record["number"], "answer": answer,
                        "digest": model.digest(["query-plan-answer-v1", answer]),
                        "correlation": correlation, "epoch": ctx["epoch"], "status": "pending"}
                reserve = slot | {"version": MAX_VERSION, "status": "unavailable", "feedback": {
                    "code": "target-missed", "correct": False, "cost": model.COST_MAX,
                    "reason": "disconnected-join", "node": 4, "detail": "cancelled"}}
                if len(model.canonical({actor: reserve})) > SLOT_BYTES:
                    return _refuse("capacity")
                for selected in ("selected", "shared"):
                    if state[selected] and state[selected]["actor"] == actor:
                        state[selected] = None
                if old and old["status"] == "pending":
                    effects.append(CancelEvaluation(old["correlation"]))
                effects.append(Evaluate("analysis", correlation, model.canonical(answer)))
                _record(state, old, slot, effects)
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
                    if op == "reveal":
                        effects.append(PublishPoints())
                    if op == "open":
                        state["shared"] = None
                elif op == "select-answer":
                    target = payload["actor"]
                    if target is not None and (record["actor"] != target or not record["value"]):
                        return _refuse("missing-answer")
                    state["selected"] = {"actor": target, "slot": copy.deepcopy(record["value"])} if target else None
                elif op == "share-selected":
                    if state["phase"] not in ("closed", "revealed"):
                        return _refuse("phase")
                    selected = state["selected"]
                    if not selected:
                        return _refuse("missing-answer")
                    state["shared"] = {"actor": selected["actor"], "version": selected["slot"]["version"],
                                       "answer": copy.deepcopy(selected["slot"]["answer"])}
                elif op == "clear-shared":
                    state["shared"] = None
                elif op == "roster-page":
                    page = payload["page"]
                    if type(page) is not int or not 0 <= page <= max(0, (state["count"] - 1) // PAGE_SIZE):
                        return _refuse("page")
                    state["records_page"] = page
                else:
                    return _refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            own = record["value"] if record["actor"] == event["actor"] else None
            if (own and own["status"] == "pending" and own["epoch"] == ctx["epoch"] and
                    own["correlation"] == event["correlation_id"] and event["binding"] == "analysis"):
                slot = copy.deepcopy(own)
                slot["feedback"] = _feedback(slot, event["outcome"], ctx)
                slot["status"] = "unavailable" if slot["feedback"]["code"] == "unavailable" else "saved"
                if len(model.canonical({event["actor"]: slot})) > SLOT_BYTES:
                    slot["feedback"] = {"code": "unavailable", "detail": "capacity"}
                    slot["status"] = "unavailable"
                _record(state, own, slot, effects)
                selected = state["selected"]
                if selected and selected["actor"] == event["actor"] and selected["slot"]["version"] == slot["version"]:
                    selected["slot"] = copy.deepcopy(slot)
        return _finish(state, effects)

    def view(self, state, audience, ctx):
        role = audience["role"]
        if role not in ("presenter", "participant", "projector"):
            raise ValueError("Unknown audience role")
        released = state["phase"] == "revealed"
        view = {k: state[k] for k in ("phase", "phase_version", "active", "count")}
        if role == "participant":
            record = ctx["records"]
            own = record["value"] if record["actor"] == audience["actor"] else None
            if own:
                view["own"] = _own(own, released)
                scoring = ctx.get("scoring", {})
                if released and scoring.get("released") and scoring.get("awarded") is not None:
                    view["own"]["points"] = scoring["awarded"]
        if role == "presenter":
            view["control_version"] = state["control_version"]
            view["counts"] = copy.deepcopy(state["counts"])
            page = ctx["record_page"]
            view["page"], view["pages"] = page["page"], page["pages"]
            view["participants"] = [{"actor": r["actor"], "number": r["number"], **r["summary"]} for r in page["rows"]]
            selected = state["selected"]
            if selected:
                view["selected"] = {"actor": selected["actor"], **_own(selected["slot"], True, True)}
        if role in ("presenter", "projector") and state["shared"]:
            view["demonstration"] = copy.deepcopy(state["shared"]["answer"])
        if released or role == "presenter":
            private = ctx["item"]["private"]
            view["solution"] = {
                "worked_answer": copy.deepcopy(private["worked"]["answer"]),
                "optimal_answer": copy.deepcopy(private["reference"]["plan"]),
                "explanation": copy.deepcopy(private["worked"]["explanation"]),
                "minimum": private["reference"]["cost"], "ties": private["reference"]["count"]}
        return view

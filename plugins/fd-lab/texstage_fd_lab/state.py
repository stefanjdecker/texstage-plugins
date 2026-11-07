# SPDX-License-Identifier: Apache-2.0
"""Deterministic lesson phases, host actor records and verified fixed points."""
import copy
from texstage.plugin_api.v1 import (
    SaveActor, SetCredit, PublishPoints, Transition,
    evaluation_correlation, json_value,
)
from . import model
from .grading import grade

MAX_ACTORS = 1000
SLOT_BYTES = 2048
STATE_BYTES = 160 * 1024
MAX_VERSION = 1000000000
PAGE_SIZE = 25


def _refuse(code):
    return {"refusal": code}


def _category(slot):
    return (slot["status"] if slot["status"] in ("pending", "unavailable") else
            "correct" if slot["feedback"]["correct"] else "incorrect")


def _replace(state, actor, old, new):
    if old: state["counts"][_category(old)] -= 1
    if new: state["counts"][_category(new)] += 1
    if state["selected"] and state["selected"]["actor"] == actor:
        state["selected"] = {"actor": actor, "slot": copy.deepcopy(new)} if new else None


_UNCHANGED = object()


def _finish(state, effects=(), actor_state=_UNCHANGED):
    effects = list(effects)
    if actor_state is not _UNCHANGED:
        effects.append(SaveActor(actor_state, {"status": _category(actor_state)}))
        verified = actor_state.get("feedback", {}).get("correct")
        credit = (1000 if verified is True else 0 if verified is False else None)
        effects.append(SetCredit(credit))
    result = Transition(state, effects)
    if len(model.canonical(state)) > STATE_BYTES or len(model.canonical(json_value(result))) > 256 * 1024:
        return _refuse("capacity")
    return result


class Lesson:
    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "selected": None, "shared": None, "demo_step": None, "actor_page": 0,
                "counts": {"pending": 0, "correct": 0, "incorrect": 0, "unavailable": 0}}

    def transition(self, previous, event, ctx):
        state = copy.deepcopy(previous)
        kind = event["kind"]
        effects = []
        record = ctx["records"]
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
        elif kind == "command":
            operation, payload, actor = event["operation"], event["payload"], event["actor"]
            public = ctx["item"]["public"]
            if operation == "submit":
                if ctx["role"] != "participant":
                    return _refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return _refuse("closed")
                if payload["phase"] != state["phase_version"]:
                    return _refuse("stale-phase")
                if record["actor"] != actor:
                    return _refuse("role")
                old = record["value"]
                version = old["version"] if old else 0
                if payload["version"] != version:
                    return _refuse("stale-answer")
                if version >= MAX_VERSION:
                    return _refuse("reset-required")
                mode = public["mode"]
                if not old and record["count"] >= MAX_ACTORS:
                    return _refuse("capacity")
                try:
                    answer = model.answer_for(public["seed"], payload["answer"])
                except (model.InputError, model.ResourceLimit):
                    return _refuse("invalid-answer")
                if answer["mode"] != mode:
                    return _refuse("wrong-mode")
                correlation = evaluation_correlation(actor, event["request_id"], "analysis")
                slot = {"version": version + 1, "answer": answer,
                        "digest": model.digest(["fd-answer-v1", answer]),
                        "correlation": correlation, "epoch": ctx["epoch"], "status": "saved"}
                # Reserve space for the largest compact feedback before accepting.
                reserve = slot | {"feedback": {"code": "unavailable", "detail": "certificate",
                                              "correct": False, "reason": "unmet-lhs", "missing": 255, "extra": 255, "step": 7, "needed": 255, "next_fd": 23, "missing_keys": 256, "invalid_keys": 256,
                                              "key": 255, "key_closure": 255, "removable": 255, "fd": 23}}
                if len(model.canonical({actor: reserve})) > SLOT_BYTES:
                    return _refuse("capacity")
                # Prepared finite data already verifies every engine certificate.
                # Grade here once, in the killable provider hook, and persist the
                # answer, feedback, credit and receipt in the host transaction.
                try:
                    slot["feedback"] = grade(public, ctx["item"]["private"], answer)
                except (model.InputError, model.ResourceLimit):
                    return _refuse("evaluation-unavailable")
                if state["shared"] and state["shared"]["actor"] == actor:
                    state["shared"] = None
                _replace(state, actor, old, slot)
                return _finish(state, effects, slot)
            else:
                if ctx["role"] != "presenter":
                    return _refuse("role")
                if payload["control"] != state["control_version"]:
                    return _refuse("stale-control")
                if state["control_version"] >= MAX_VERSION or state["phase_version"] >= MAX_VERSION:
                    return _refuse("reset-required")
                if operation in ("open", "close", "reveal"):
                    if operation == "open" and state["phase"] == "revealed" and public["points"]:
                        return _refuse("reset-required")
                    allowed = {"open": ("introduce", "closed", "revealed"),
                               "close": ("open",), "reveal": ("open", "closed")}
                    if state["phase"] not in allowed[operation]:
                        return _refuse("phase")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[operation]
                    state["phase_version"] += 1
                    if operation == "reveal":
                        effects.append(PublishPoints())
                    if operation == "open":
                        state["shared"] = None
                        state["demo_step"] = None
                elif operation == "roster-page":
                    page = payload["page"]
                    pages = max(1, (record["count"] + PAGE_SIZE - 1) // PAGE_SIZE)
                    if type(page) is not int or not 0 <= page < pages:
                        return _refuse("invalid-page")
                    state["actor_page"] = page
                elif operation in ("select-answer", "select-demonstration"):
                    target = payload["actor"]
                    if target and (record["actor"] != target or record["value"] is None):
                        return _refuse("missing-answer")
                    if operation == "select-answer":
                        state["selected"] = {"actor": target, "slot": copy.deepcopy(record["value"])} if target else None
                    else:
                        if state["phase"] != "revealed":
                            return _refuse("phase")
                        state["demo_step"] = None
                        state["shared"] = ({"actor": target, "version": record["value"]["version"],
                                            "answer": copy.deepcopy(record["value"]["answer"])}
                                           if target else None)
                elif operation == "demonstrate":
                    if state["phase"] != "revealed":
                        return _refuse("phase")
                    worked = ctx["item"]["private"]["worked"]["answer"]
                    if "steps" not in worked:
                        return _refuse("no-derivation")
                    step = payload["step"]
                    if type(step) is not int or not 0 <= step <= len(ctx["item"]["private"]["worked"]["answer"]["steps"]):
                        return _refuse("invalid-step")
                    state["shared"] = None
                    state["demo_step"] = step
                else:
                    return _refuse("operation")
                state["control_version"] += 1
        return _finish(state, effects)

    def view(self, state, audience, ctx):
        role = audience["role"]
        public = ctx["item"]["public"]
        released = state["phase"] == "revealed"
        view = {k: state[k] for k in ("phase", "phase_version", "active")}
        if role != "participant":
            view["count"] = ctx["records"]["count"]
        if role == "participant":
            own = ctx["records"]["value"] if ctx["records"]["actor"] == audience["actor"] else None
            if own:
                view["own"] = {k: copy.deepcopy(own[k]) for k in ("version", "answer", "status")}
                if (released or public["feedback"] == "practice") and "feedback" in own:
                    # Operational details and private fixture diagnostics remain private.
                    view["own"]["feedback"] = {k: v for k, v in own["feedback"].items() if k != "detail"}
                scoring = ctx.get("scoring", {})
                if released and scoring.get("released") and scoring.get("awarded") is not None:
                    view["own"]["points"] = scoring["awarded"]
        if role == "presenter":
            view["control_version"] = state["control_version"]
            view["demo_step"] = state["demo_step"]
            view["counts"] = copy.deepcopy(state["counts"])
            view["participants"] = []
            page = ctx["record_page"]
            view["roster_pages"] = page["pages"]
            view["roster_page"] = page["page"]
            view["participants"] = [{"actor": r["actor"], "number": r["number"], **r["summary"]}
                                    for r in page["rows"]]
            selected = state["selected"]["slot"] if state["selected"] else None
            if selected:
                view["selected"] = {k: copy.deepcopy(selected[k]) for k in ("version", "answer", "status")}
                if "feedback" in selected:
                    view["selected"]["feedback"] = copy.deepcopy(selected["feedback"])
        if role in ("presenter", "projector"):
            shared = state["shared"]
            if shared and released:
                view["demonstration"] = copy.deepcopy(shared["answer"])
            if released and state["demo_step"] is not None:
                answer = copy.deepcopy(ctx["item"]["private"]["worked"]["answer"])
                answer["steps"] = answer["steps"][:state["demo_step"]]
                seed = public["seed"]
                start = seed["task"]["start" if public["mode"] == "closure" else "lhs"]
                known = model.replay(seed, start, answer["steps"], model.Budget())["reached"]
                if public["mode"] == "closure":
                    answer["closure"] = known
                view["known"] = known
                view["demonstration"] = answer
                view["walkthrough"] = True
        if released or role == "presenter":
            worked = ctx["item"]["private"]["worked"]
            view["worked"] = {k: copy.deepcopy(worked[k]) for k in ("answer", "explanation")}
        return view

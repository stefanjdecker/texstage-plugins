# SPDX-License-Identifier: Apache-2.0
"""Bounded classroom reducer; only independently verified facts become feedback."""
import copy

from texstage.plugin_api.v1 import CancelEvaluation, Evaluate, PutRecord, SetCredit, PublishPoints, evaluation_correlation, json_value
from . import model
from .authoring import local
from .validation import InputError, ResourceLimit, answer, canonical, identity

MAX_ACTORS = 1000
PAGE_SIZE = 16
SLOT_BYTES = 3072
STATE_BYTES = 8 * 1024
MAX_VERSION = 2147483647


def handle(actor):
    return identity("normalization-actor-v1", actor)


def _slot(ctx, actor_handle):
    return ctx.get("records", {}).get(actor_handle)


def _referenced(ctx, ref):
    row = _slot(ctx, ref["handle"]) if ref else None
    return row if row and row["version"] == ref["version"] else None


def _refuse(code):
    return {"refusal": code}


def _finish(state, effects=()):
    result = {"state": state, "effects": [json_value(effect) for effect in effects]}
    if len(canonical(state)) > STATE_BYTES or len(canonical(result)) > 256 * 1024:
        return _refuse("capacity")
    return result


def _feedback(exercise, submitted, facts):
    result = {"accepted": model.accepted(exercise, submitted, facts), "normal_form": None,
              "missing": 0, "lossless": None, "preserved": None, "witness": None, "lost_fd": -1}
    if submitted["mode"] == "classify":
        form = facts["normal_form"]
        next_form = {"1nf": "2nf", "2nf": "3nf", "3nf": "bcnf"}.get(form)
        result.update(normal_form=form, witness=facts["witnesses"][next_form] if next_form else None)
    else:
        weakest = min(facts["components"], key=lambda row: model.FORMS.index(row["normal_form"]))
        result.update(normal_form=weakest["normal_form"], missing=facts["missing"],
                      witness=weakest["witnesses"][exercise["task"]["target"]])
        if facts["covered"]:
            result.update(lossless=facts["join"]["lossless"], preserved=facts["preservation"]["preserved"],
                          lost_fd=facts["preservation"]["fd"])
    return result


class Workshop:
    def record_keys(self, state, event, ctx):
        """Only own answers, explicit presenter references, or a bounded roster page."""
        kind = event["kind"]
        if kind == "view":
            audience = event["audience"]
            if audience["role"] == "participant":
                return [handle(audience["actor"])]
            if audience["role"] == "projector":
                return [ref["handle"] for ref in state["shared"]]
            if audience["role"] == "presenter":
                if audience["surface"] == "presenter-controls":
                    keys = sorted({ref["handle"] for ref in state["selected"] + state["shared"]})
                    return {"keys": keys, "page": {"offset": state["page"] * PAGE_SIZE, "limit": PAGE_SIZE}}
                return [ref["handle"] for ref in state["selected"]]
        if kind == "evaluation.finished":
            return [handle(event["actor"])]
        if kind == "command":
            if ctx["role"] == "participant":
                return [handle(event["actor"])] if event["operation"] == "submit" else []
            if ctx["role"] == "presenter":
                payload = event["payload"]
                refs = payload.get("answers", [])
                return sorted({ref["handle"] for ref in refs} |
                              ({payload["handle"]} if "handle" in payload else set()))
        return []

    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "page": 0,
                "counts": {k: 0 for k in ("received", "pending", "checked", "unavailable")},
                "selected": [], "shared": [],
                "share_checks": False, "topic": "summary"}

    def transition(self, previous, event, ctx):
        state = copy.deepcopy(previous)
        effects = []
        kind = event["kind"]
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
        elif kind == "command":
            operation, payload, actor = event["operation"], event["payload"], event["actor"]
            if operation == "submit":
                if ctx["role"] != "participant":
                    return _refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return _refuse("closed")
                if payload["phase"] != state["phase_version"]:
                    return _refuse("stale-phase")
                actor_handle = handle(actor)
                old = _slot(ctx, actor_handle)
                version = old["version"] if old else 0
                if payload["version"] != version:
                    return _refuse("stale-answer")
                if version >= MAX_VERSION:
                    return _refuse("reset-required")
                if not old and state["counts"]["received"] >= MAX_ACTORS:
                    return _refuse("capacity")
                try:
                    submitted = answer(payload["answer"], ctx["item"]["private"]["seed"])
                except (InputError, ResourceLimit):
                    return _refuse("invalid-answer")
                # Epoch and version are in the SDK slot, so reset/reused request IDs
                # cannot revive a prior job even though v1 state has no epoch field.
                correlation = evaluation_correlation(actor, event["request_id"],
                                                     f'analysis:{ctx["epoch"]}:{version + 1}')
                row = {"handle": actor_handle, "number": old["number"] if old else state["counts"]["received"] + 1,
                       "version": version + 1, "answer": submitted,
                       "correlation": correlation, "status": "pending", "feedback": None}
                if len(canonical(row)) + 256 > SLOT_BYTES:
                    return _refuse("capacity")
                if old:
                    if old["status"] == "pending":
                        effects.append(CancelEvaluation(old["correlation"]))
                    state["counts"][old["status"]] -= 1
                else:
                    state["counts"]["received"] += 1
                state["counts"]["pending"] += 1
                effects.append(PutRecord(actor_handle, row))
                effects.append(SetCredit(None))
                for key in ("selected", "shared"):
                    if any(ref["handle"] == actor_handle for ref in state[key]):
                        state[key] = []
                        if key == "shared":
                            state["share_checks"] = False
                effects.append(Evaluate("analysis", correlation, canonical(submitted)))
            else:
                if ctx["role"] != "presenter":
                    return _refuse("role")
                if not state["active"]:
                    return _refuse("inactive")
                if payload["control"] != state["control_version"]:
                    return _refuse("stale-control")
                if max(state["control_version"], state["phase_version"]) >= MAX_VERSION:
                    return _refuse("reset-required")
                if operation in ("open", "close", "reveal"):
                    allowed = {"open": ("introduce", "closed"), "close": ("open",), "reveal": ("closed",)}
                    if state["phase"] not in allowed[operation]:
                        return _refuse("reset-required" if state["phase"] == "revealed" else "phase")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[operation]
                    state["phase_version"] += 1
                    if operation == "reveal":
                        effects.append(PublishPoints())
                    if operation == "open":
                        state.update(selected=[], shared=[], share_checks=False, topic="summary")
                elif operation in ("select-answer", "share-answer", "share-analysis", "compare-answers", "share-comparison"):
                    comparing = operation in ("compare-answers", "share-comparison")
                    sharing = operation in ("share-answer", "share-analysis", "share-comparison")
                    refs = copy.deepcopy(payload["answers"]) if comparing else [
                        {key: payload[key] for key in ("handle", "version")}]
                    if comparing and (len(refs) != 2 or refs[0]["handle"] == refs[1]["handle"]):
                        return _refuse("distinct-answers")
                    rows = [_referenced(ctx, ref) for ref in refs]
                    if any(row is None for row in rows):
                        return _refuse("stale-answer")
                    if (comparing or operation == "share-analysis") and any(row["status"] != "checked" for row in rows):
                        return _refuse("not-checked")
                    if sharing and state["phase"] not in ("closed", "revealed"):
                        return _refuse("phase")
                    state["shared" if sharing else "selected"] = refs
                    if sharing:
                        state["share_checks"] = operation != "share-answer"
                    state["topic"] = "summary"
                elif operation == "page":
                    pages = max(1, (state["counts"]["received"] + PAGE_SIZE - 1) // PAGE_SIZE)
                    if type(payload["page"]) is not int or not 0 <= payload["page"] < pages:
                        return _refuse("page")
                    state["page"] = payload["page"]
                elif operation == "show-evidence":
                    if payload["topic"] not in ("summary", "lossless", "preservation"):
                        return _refuse("topic")
                    state["topic"] = payload["topic"]
                elif operation in ("unshare", "clear-selection"):
                    state["shared" if operation == "unshare" else "selected"] = []
                    if operation == "unshare":
                        state["share_checks"] = False
                else:
                    return _refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            row = copy.deepcopy(_slot(ctx, handle(event["actor"])))
            if (row and row["status"] == "pending" and row["correlation"] == event["correlation_id"]
                    and event["binding"] == "analysis"):
                outcome, exercise = event["outcome"], ctx["item"]["private"]["seed"]
                row.update(status="unavailable", correlation=None, feedback=None)
                try:
                    if outcome.get("status") == "ok" and model.verify_analysis(exercise, row["answer"], outcome.get("data")):
                        row.update(status="checked", feedback=_feedback(exercise, row["answer"], outcome["data"]["facts"]))
                except (InputError, ResourceLimit, TypeError, ValueError, KeyError):
                    # An operational/verification failure is not an incorrect answer.
                    pass
                state["counts"]["pending"] -= 1
                state["counts"][row["status"]] += 1
                effects.append(PutRecord(row["handle"], row))
                effects.append(SetCredit((1000 if row["feedback"]["accepted"] else 0)
                                         if row["status"] == "checked" else None))
        return _finish(state, effects)

    def view(self, state, audience, ctx):
        role, surface = audience["role"], audience["surface"]
        revealed = state["phase"] == "revealed"
        worked = None
        if revealed or role == "presenter":
            source = ctx["item"]["private"]["worked"]
            worked = {"answer": copy.deepcopy(source["answer"]),
                      "explanation": local(source["explanation"], ctx["item"]["private"].get("language", "en"))}
        if role == "participant" and surface == "participant-input":
            row = _slot(ctx, handle(audience["actor"]))
            return {"phase": state["phase"], "active": state["active"], "phase_version": state["phase_version"],
                    "answer_version": row["version"] if row else 0,
                    "points": ctx.get("scoring", {}).get("awarded")
                    if revealed and ctx.get("scoring", {}).get("released") else None,
                    "answer": copy.deepcopy(row["answer"]) if row else None, "status": row["status"] if row else None,
                    "feedback": copy.deepcopy(row["feedback"]) if row and revealed else None, "worked": worked,
                    "analysis": model.analyze(ctx["item"]["private"]["seed"], row["answer"])
                    if row and revealed and row["status"] == "checked" else None}
        counts = copy.deepcopy(state["counts"])
        result = {"phase": state["phase"], "counts": counts}
        if role == "projector" and surface == "projector-overlay":
            shared = []
            if state["phase"] in ("closed", "revealed"):
                for ref in state["shared"]:
                    row = _referenced(ctx, ref)
                    if row:
                        shared.append({"answer": copy.deepcopy(row["answer"]), "version": row["version"],
                            "analysis": model.analyze(ctx["item"]["private"]["seed"], row["answer"])
                            if state["share_checks"] and row["status"] == "checked" else None})
            return result | {"shared": shared, "worked": worked, "topic": state["topic"]}
        if role == "presenter" and surface == "presenter-controls":
            return result | {key: copy.deepcopy(state[key]) for key in
                             ("active", "phase_version", "control_version", "selected", "shared", "share_checks", "topic")} | {
                "page": state["page"], "pages": max(1, (counts["received"] + PAGE_SIZE - 1) // PAGE_SIZE),
                "answers": [{key: ctx["records"][h][key] for key in ("handle", "number", "version", "status")}
                            for h in ctx.get("record_page", [])],
                "pinned": [{key: ctx["records"][h][key] for key in ("handle", "number", "version", "status")}
                           for h in sorted({ref["handle"] for ref in state["selected"] + state["shared"]})
                           if h in ctx.get("records", {})]}
        if role == "presenter" and surface == "presenter-overlay":
            selected = []
            for ref in state["selected"]:
                row = _referenced(ctx, ref)
                if row and row["status"] == "checked":
                    # At most TWO bounded analyses, never the class's answer map.
                    selected.append({"answer": copy.deepcopy(row["answer"]), "version": row["version"],
                        "analysis": model.analyze(ctx["item"]["private"]["seed"], row["answer"])})
            return result | {"selected": selected, "worked": worked, "topic": state["topic"]}
        raise ValueError("Unsupported audience")

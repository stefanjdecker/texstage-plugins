# SPDX-License-Identifier: Apache-2.0
"""B+ classroom protocol. Deterministic state, bounded slots and private views."""
import copy
import json

from texstage.plugin_api.v1 import CancelEvaluation, Evaluate, SaveActor, SetCredit, PublishPoints, evaluation_correlation, json_value

from . import model
from .grading import grade
from .storage import read_slot, write_slot, pack_feedback, reserve_slot

MAX_ACTORS = 1000
PAGE_SIZE = 25
MAX_VERSION = 1_000_000_000
SLOT_BYTES = 704
FEEDBACK_RESERVE = 100
STATE_BYTES = 16 * 1024
TRANSITION_BYTES = 24 * 1024
VIEW_BYTES = 80 * 1024
SURFACES = {
    "participant": ("participant-input",),
    "presenter": ("presenter-controls", "presenter-overlay"),
    "projector": ("projector-overlay",),
}


def size(value):
    return len(model.canonical(value))


def actor_key(actor):
    # Host-owned record keys are authenticated identities, never student input.
    return actor


def binding_digest(ctx):
    # Include EVERY persisted field, including the host-added engine key.
    return model.digest(ctx["item"]["evaluations"]["analysis"])


def exercise(ctx):
    return json.loads(ctx["item"]["evaluations"]["analysis"]["seed"])


def refuse(code):
    return {"refusal": code}


def finish(state, effects=()):
    # Only effects contain SDK objects. Avoid recursively copying all students'
    # already-JSON slots. The host accepts this JSON transition form and still
    # validates the complete transition and SDK effects at its boundary.
    result = {"state": state, "effects": [json_value(effect) for effect in effects]}
    if size(state) > STATE_BYTES or size(result) > TRANSITION_BYTES:
        return refuse("capacity")
    return result


def feedback(slot, outcome, ctx):
    if outcome.get("status") != "ok":
        return {"code": "unavailable", "reason": "evaluation"}
    facts = outcome.get("data")
    if not isinstance(facts, dict):
        return {"code": "unavailable", "reason": "facts"}
    if (facts.get("exercise") != ctx["item"]["private"]["exercise_digest"] or
            facts.get("answer") != model.digest(slot["answer"])):
        return {"code": "unavailable", "reason": "identity"}
    # Bounded independent replay checks identity, task, every fact and invariant.
    # We compare with THIS submission, never with the author's worked answer.
    try:
        expected = model.analyze(exercise(ctx), slot["answer"])
    except (model.InputError, model.ResourceLimit):
        return {"code": "unavailable", "reason": "facts"}
    if model.canonical(expected) != model.canonical(facts):
        return {"code": "unavailable", "reason": "facts"}
    score = grade(exercise(ctx), slot["answer"], expected)
    replay = facts["replay"]
    if replay["state"] != "complete":
        return {"code": "revise", "correct": False, "reason": replay["reason"],
                "checked_repairs": replay["checked_repairs"], "at": replay["at"], "node": replay["node"], "grade": score}
    failed = [name for name, value in facts["claims"].items() if value is False]
    return {"code": "revise" if failed else "correct", "correct": not failed,
            "reason": "prediction" if failed else "complete", "failed": failed,
            "checked_repairs": replay["checked_repairs"], "grade": score}


def replay_steps(answer):
    """Focus steps describe predictions; they never manufacture corrected pages."""
    steps = [{"kind": "start"}]
    steps += [{"kind": "path", "index": i} for i in range(len(answer["path"]))]
    steps += [{"kind": "scan", "index": i} for i in range(len(answer.get("leaves", [])))]
    steps += [{"kind": "repair", "index": i} for i in range(len(answer.get("repairs", [])))]
    return steps + [{"kind": "prediction"}]


def worked(item):
    source = item["private"]["worked"]
    facts = source["analysis"]
    # No digests, evaluator envelopes or private state enter the teaching view.
    return {"answer": copy.deepcopy(source["answer"]), "explanation": copy.deepcopy(source["explanation"]),
            "result": {key: copy.deepcopy(facts[key]) for key in ("read", "final", "metrics") if key in facts}}


def slot_for(state, selection):
    if selection:
        slot = read_slot(selection["slot"])
        if slot and slot["version"] == selection["version"]:
            return slot
    return None


class Lesson:
    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0, "active": False,
                "count": 0, "counts": {key: 0 for key in ("pending", "saved", "unavailable")},
                "records_page": 0, "selected": None, "shared": None, "replay": None,
                "binding": binding_digest(ctx)}

    def transition(self, previous, event, ctx):
        # Only counters, controls and two explicitly selected snapshots are shared.
        # All student slots live in bounded, authenticated host actor records.
        state = {**previous, "counts": dict(previous["counts"])}
        effects = []
        kind = event["kind"]
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
            # Leaving the slide closes submissions. Returning never silently reopens.
            if kind == "deactivate" and state["phase"] == "open":
                state["phase"] = "closed"
                state["phase_version"] = min(MAX_VERSION, state["phase_version"] + 1)
                state["control_version"] = min(MAX_VERSION, state["control_version"] + 1)
        elif kind == "command":
            op, payload, actor = event["operation"], event["payload"], event["actor"]
            if op == "submit-answer":
                if ctx["role"] != "participant":
                    return refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return refuse("closed")
                if payload["phase_version"] != state["phase_version"]:
                    return refuse("stale-phase")
                if state["binding"] != binding_digest(ctx):
                    return refuse("reset-required")
                key = actor_key(actor)
                old = read_slot(ctx["records"]["value"])
                version = old["version"] if old else 0
                if payload["answer_version"] != version:
                    return refuse("stale-answer")
                if version >= MAX_VERSION:
                    return refuse("reset-required")
                if old is None and ctx["records"]["count"] >= MAX_ACTORS:
                    return refuse("capacity")
                try:
                    answer = model.answer_for(exercise(ctx), payload["answer"])
                except (model.InputError, model.ResourceLimit):
                    return refuse("invalid-answer")
                correlation = evaluation_correlation(actor, event["request_id"], "analysis")
                slot = write_slot({"version": version + 1, "answer": answer,
                        "correlation": correlation, "epoch": ctx["epoch"], "status": "pending"})
                # Reserve the maximum eventual compact feedback before admission.
                reserve = reserve_slot(slot, MAX_VERSION, FEEDBACK_RESERVE)
                if size(reserve) > SLOT_BYTES:
                    return refuse("capacity")
                state["count"] = ctx["records"]["count"] + int(old is None)
                if old:
                    state["counts"][old["status"]] -= 1
                state["counts"]["pending"] += 1
                for name in ("selected", "shared"):
                    if state[name] and state[name]["actor"] == key:
                        state[name] = None
                        if name == "shared":
                            state["replay"] = None
                if old and old["status"] == "pending":
                    effects.append(CancelEvaluation(old["correlation"]))
                effects.append(SetCredit(None))
                effects.append(Evaluate("analysis", correlation, model.canonical(answer)))
                effects.append(SaveActor(slot, {"version": version + 1, "status": "pending"}))
            else:
                if ctx["role"] != "presenter":
                    return refuse("role")
                if payload["control_version"] != state["control_version"]:
                    return refuse("stale-control")
                if state["control_version"] >= MAX_VERSION or state["phase_version"] >= MAX_VERSION:
                    return refuse("reset-required")
                if op in ("open", "close", "reveal"):
                    if op == "open" and state["phase"] == "revealed":
                        return refuse("reset-required")
                    allowed = {"open": ("introduce", "closed"), "close": ("open",), "reveal": ("closed",)}
                    if state["phase"] not in allowed[op]:
                        return refuse("phase")
                    if op == "open" and not state["active"]:
                        return refuse("inactive")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[op]
                    state["phase_version"] += 1
                    if op == "reveal":
                        effects.append(PublishPoints())
                    if op == "open":
                        state["shared"], state["replay"] = None, None
                elif op in ("select-answer", "share-answer"):
                    target, version = payload["actor"], payload["answer_version"]
                    if op == "select-answer" and target == "" and version == 0:
                        state["selected"] = None
                    else:
                        record = ctx["records"]
                        slot = read_slot(record["value"]) if record["actor"] == target else None
                        if slot is None:
                            return refuse("missing-answer")
                        if slot["version"] != version:
                            return refuse("stale-answer")
                        if op == "share-answer" and state["phase"] not in ("closed", "revealed"):
                            return refuse("phase")
                        state["selected" if op == "select-answer" else "shared"] = {"actor": target, "version": version, "slot": record["value"]}
                        if op == "share-answer":
                            state["replay"] = None
                elif op == "roster-page":
                    page = payload["page"]
                    if not 0 <= page < max(1, (state["count"] + PAGE_SIZE - 1) // PAGE_SIZE):
                        return refuse("page")
                    state["records_page"] = page
                elif op == "clear-share":
                    state["shared"] = None
                    if state["replay"] and state["replay"]["source"] == "shared":
                        state["replay"] = None
                elif op == "replay-step":
                    source = payload["source"]
                    if source == "worked":
                        if state["phase"] != "revealed":
                            return refuse("unrevealed")
                        answer = ctx["item"]["private"]["worked"]["answer"]
                    elif source == "shared":
                        slot = slot_for(state, state["shared"])
                        if slot is None:
                            return refuse("missing-share")
                        answer = slot["answer"]
                    else:
                        return refuse("replay-source")
                    if not 0 <= payload["step"] < len(replay_steps(answer)):
                        return refuse("replay-step")
                    state["replay"] = {"source": source, "step": payload["step"]}
                else:
                    return refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            key = actor_key(event["actor"])
            slot = read_slot(ctx["records"]["value"])
            if (slot and slot["status"] == "pending" and slot["epoch"] == ctx["epoch"] and
                    slot["correlation"] == event["correlation_id"] and event["binding"] == "analysis"):
                result = (feedback(slot, event["outcome"], ctx) if state["binding"] == binding_digest(ctx)
                          else {"code": "unavailable", "reason": "binding"})
                if size(pack_feedback(result)) > FEEDBACK_RESERVE:
                    result = {"code": "unavailable", "reason": "facts"}
                state["counts"]["pending"] -= 1
                slot["feedback"] = result
                slot["status"] = "unavailable" if result["code"] == "unavailable" else "saved"
                state["counts"][slot["status"]] += 1
                effects.append(SetCredit(result["grade"]["credit"] if "grade" in result else None))
                encoded = write_slot(slot)
                effects.append(SaveActor(encoded, {"version": slot["version"], "status": slot["status"]}))
                for name in ("selected", "shared"):
                    selected = state[name]
                    if selected and selected["actor"] == key and selected["version"] == slot["version"]:
                        state[name] = {**selected, "slot": encoded}
        return finish(state, effects)

    def view(self, state, audience, ctx):
        role, surface = audience["role"], audience["surface"]
        if surface not in SURFACES.get(role, ()):
            raise ValueError("surface-role")
        view = {"format": 1, **{key: state[key] for key in ("phase", "phase_version", "active")},
                "count": state["count"]}
        released = state["phase"] == "revealed"
        if role == "participant":
            del view["count"]  # Whole-class counts belong to presenter/projector views.
            view["scoring"] = copy.deepcopy(ctx["scoring"])
            slot = read_slot(ctx["records"]["value"])
            if slot:
                view["own"] = {key: copy.deepcopy(slot[key]) for key in ("version", "answer", "status")}
                if "feedback" in slot and (released or ctx["item"]["private"]["feedback"] == "immediate"
                                          or slot["status"] == "unavailable"):
                    view["own"]["feedback"] = copy.deepcopy(slot["feedback"])
        if surface == "presenter-controls":
            view["control_version"] = state["control_version"]
            page = ctx["record_page"]
            view["counts"] = dict(state["counts"])
            view["roster_page"] = {key: page[key] for key in ("page", "pages", "total")}
            view["participants"] = [{"actor": row["actor"], "number": row["number"], **row["summary"]}
                                    for row in page["rows"]]
            slot = slot_for(state, state["selected"])
            if slot:
                view["selected"] = {**{k: state["selected"][k] for k in ("actor", "version")},
                                    **{k: copy.deepcopy(slot[k]) for k in ("answer", "status")}}
                if "feedback" in slot:
                    view["selected"]["feedback"] = copy.deepcopy(slot["feedback"])
        shared = slot_for(state, state["shared"])
        if shared:
            view["demonstration"] = {"answer": copy.deepcopy(shared["answer"])}
            if released and "feedback" in shared:
                view["demonstration"]["feedback"] = copy.deepcopy(shared["feedback"])
        if released:
            view["worked"] = worked(ctx["item"])
        cursor = state["replay"]
        if cursor and (cursor["source"] == "worked" and released or cursor["source"] == "shared" and shared):
            answer = ctx["item"]["private"]["worked"]["answer"] if cursor["source"] == "worked" else shared["answer"]
            steps = replay_steps(answer)
            view["replay"] = {**cursor, "total": len(steps), "focus": steps[cursor["step"]]}
        if size(view) > VIEW_BYTES:
            raise ValueError("view-capacity")
        return view

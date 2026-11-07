# SPDX-License-Identifier: Apache-2.0
"""Registration lesson protocol; no I/O, per-actor versions and closed projections."""
import copy
import json
import unicodedata
from functools import lru_cache
from texstage.plugin_api.v1 import CancelEvaluation, Evaluate, PutRecord, SetCredit, PublishPoints, Transition, evaluation_correlation, json_value
from . import model

MAX_ACTORS = 600
PAGE_SIZE = 16
MAX_VERSION = 1_000_000_000
SLOT_BYTES = 2560
STATE_BYTES = 192 * 1024
TRANSITION_BYTES = 224 * 1024
VIEW_BYTES = 96 * 1024
RATIONALE_CHARS = 160
RATIONALE_BYTES = 1280


def size(value):
    return len(model.canonical(value))


def refuse(code):
    return {"refusal": code}


def finish(state, effects=()):
    # JSON is the API boundary. Avoid dataclasses.asdict recursively copying the
    # complete classroom index again for every durable answer and completion.
    result = {"state": state, "effects": [json_value(e) for e in effects]}
    if size(state) > STATE_BYTES or size(result) > TRANSITION_BYTES:
        return refuse("capacity")
    return result


def exercise(ctx):
    # The host supplies the immutable prepared binding, never a command's seed.
    return json.loads(ctx["item"]["evaluations"]["analysis"]["seed"])


@lru_cache(maxsize=32)
def expected_facts(seed, answer):
    """Bounded immutable oracle results, keyed by complete authored seed/answer."""
    return model.canonical(model.analyze(json.loads(seed), json.loads(answer)))


def feedback(slot, outcome, ctx):
    if outcome.get("status") != "ok":
        return {"code": "unavailable", "detail": "evaluation"}
    data = outcome.get("data")
    if not isinstance(data, dict):
        return {"code": "unavailable", "detail": "facts"}
    if (data.get("exercise_digest") != ctx["item"]["private"]["exercise_digest"] or
            data.get("answer_digest") != slot["digest"]):
        return {"code": "unavailable", "detail": "identity"}
    # The independent bounded oracle verifies complete coverage, classifications,
    # admission and deterministic witnesses. Shape-valid invented facts cannot pass.
    expected = expected_facts(ctx["item"]["evaluations"]["analysis"]["seed"], model.canonical(slot["answer"]))
    if model.canonical(data) != expected:
        return {"code": "unavailable", "detail": "facts"}
    failed = sum(row["admits"] != (row["expected"] == "allow") for row in data["checks"])
    correct = data["model_valid"] and not failed and not data["unresolved"]
    return {"code": "checked" if correct else "contradiction", "correct": correct, "failed": failed}


def teaching(item):
    return {
        "worked": copy.deepcopy(item["private"]["worked"]),
        "counterexamples": [
            {"answer": copy.deepcopy(w["answer"]), "explanation": copy.deepcopy(w["explanation"]),
             "snapshot": {k: copy.deepcopy(w["snapshot"][k]) for k in ("entities", "links")}}
            for w in item["private"]["teaching_witnesses"]],
    }


class Lesson:
    def record_keys(self, state, event, ctx):
        """Only the changed answer, or explicitly inspected/shared answers."""
        if event["kind"] == "view":
            audience = event["audience"]
            keys = [audience["actor"]] if audience["role"] == "participant" else [
                state[k]["actor"] for k in ("selected", "shared") if state[k]]
            if audience["surface"] == "presenter-controls":
                return {"keys": sorted(set(keys)), "page": {"offset": state["page"] * PAGE_SIZE, "limit": PAGE_SIZE}}
        elif event["kind"] == "evaluation.finished":
            keys = [event["actor"]]
        elif event["kind"] == "command":
            keys = [event["actor"]] if event["operation"] == "submit" else [event["payload"].get("actor")]
        else:
            keys = []
        return sorted({key for key in keys if key})

    @staticmethod
    def summary(slot, item):
        category = slot["status"] if slot["status"] in ("pending", "unavailable") else (
            "correct" if slot["feedback"]["correct"] else "incorrect")
        options = {d["id"]: [o["id"] for o in d["options"]] for d in item["public"]["decisions"]}
        choices = dict(slot["answer"]["choices"])
        return {"v": slot["version"], "s": {"pending":"p", "unavailable":"u", "correct":"c", "incorrect":"i"}[category],
                "c": [options[d["id"]].index(choices[d["id"]]) for d in item["public"]["decisions"]]}

    def adjust(self, state, slot, item, direction):
        entry = self.summary(slot, item)
        state["counts"][entry["s"]] += direction
        for row, choice in zip(state["options"], entry["c"], strict=True):
            row[choice] += direction

    def initial_state(self, item, ctx):
        return {"phase": "introduce", "phase_version": 0, "control_version": 0,
                "active": False, "page": 0, "count": 0, "selected": None, "shared": None,
                "counts": {k: 0 for k in ("p", "u", "c", "i")},
                "options": [[0] * len(d["options"]) for d in item["public"]["decisions"]]}

    def transition(self, previous, event, ctx):
        # Aggregates stay bounded independently of classroom size. Full answers
        # live in host records; at most the changed/inspected page is read.
        state = previous | {"counts": previous["counts"].copy(), "options": [row.copy() for row in previous["options"]]}
        effects = []
        kind = event["kind"]
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
        elif kind == "command":
            op, payload, actor = event["operation"], event["payload"], event["actor"]
            if op == "submit":
                if ctx["role"] != "participant":
                    return refuse("role")
                if not state["active"] or state["phase"] != "open":
                    return refuse("closed")
                if payload["phase_version"] != state["phase_version"]:
                    return refuse("stale-phase")
                if size(actor) > 258:
                    return refuse("capacity")
                old = ctx["records"].get(actor)
                version = old["version"] if old else 0
                if payload["answer_version"] != version:
                    return refuse("stale-answer")
                if version >= MAX_VERSION:
                    return refuse("reset-required")
                if old is None and state["count"] >= MAX_ACTORS:
                    return refuse("capacity")
                try:
                    answer = model.answer({"format": 1, "choices": payload["choices"]})
                    model.compile_model(exercise(ctx), answer)
                    rationale = model.normalize(payload.get("rationale", ""))
                    if (not isinstance(rationale, str) or len(rationale) > RATIONALE_CHARS or
                            size(rationale) > RATIONALE_BYTES or
                            any(unicodedata.category(c) == "Cc" and c not in "\n\t" for c in rationale)):
                        return refuse("invalid-rationale")
                except (model.InputError, model.ResourceLimit, model.DomainError):
                    return refuse("invalid-answer")
                correlation = evaluation_correlation(actor, event["request_id"], "model")
                slot = {"version": version + 1, "answer": answer, "rationale": rationale,
                        "digest": model.digest(["er-answer-v1", answer]), "correlation": correlation,
                        "epoch": ctx["epoch"], "status": "pending"}
                reserve = slot | {"feedback": {"code": "contradiction", "correct": False, "failed": 12,
                                               "detail": "evaluation"}}
                if size({actor: reserve}) > SLOT_BYTES:
                    return refuse("capacity")
                if old is None:
                    state["count"] += 1
                else:
                    self.adjust(state, old, ctx["item"], -1)
                self.adjust(state, slot, ctx["item"], 1)
                for key in ("selected", "shared"):
                    if state[key] and state[key]["actor"] == actor:
                        state[key] = None
                if old and old["status"] == "pending":
                    effects.append(CancelEvaluation(old["correlation"]))
                effects.append(Evaluate("analysis", correlation, model.canonical(answer)))
                effects.append(PutRecord(actor, slot))
                if ctx["item"]["public"]["points"]:
                    effects.append(SetCredit(None))
            else:
                if ctx["role"] != "presenter":
                    return refuse("role")
                if payload["control_version"] != state["control_version"]:
                    return refuse("stale-control")
                if state["control_version"] >= MAX_VERSION or state["phase_version"] >= MAX_VERSION:
                    return refuse("reset-required")
                if op in ("open", "close", "reveal"):
                    if op == "open" and state["phase"] == "revealed" and ctx["item"]["public"]["points"]:
                        return refuse("reset-required")
                    allowed = {"open": ("introduce", "closed", "revealed"),
                               "close": ("open",), "reveal": ("closed",)}
                    if state["phase"] not in allowed[op]:
                        return refuse("phase")
                    state["phase"] = {"open": "open", "close": "closed", "reveal": "revealed"}[op]
                    state["phase_version"] += 1
                    if op == "reveal" and ctx["item"]["public"]["points"]:
                        effects.append(PublishPoints())
                    if op == "open":
                        state["shared"] = None
                elif op in ("select-answer", "share-answer"):
                    target, version = payload["actor"], payload["answer_version"]
                    if op == "select-answer" and target == "" and version == 0:
                        state["selected"] = None
                    else:
                        slot = ctx["records"].get(target)
                        if slot is None:
                            return refuse("missing-answer")
                        if slot["version"] != version:
                            return refuse("stale-answer")
                        if op == "share-answer" and state["phase"] not in ("closed", "revealed"):
                            return refuse("phase")
                        state["selected" if op == "select-answer" else "shared"] = {
                            "actor": target, "version": version}
                        if op == "share-answer":
                            state["shared"]["include_rationale"] = payload["include_rationale"]
                elif op == "clear-share":
                    state["shared"] = None
                elif op == "set-page":
                    if payload["page"] > max(0, (state["count"] - 1) // PAGE_SIZE):
                        return refuse("page")
                    state["page"] = payload["page"]
                else:
                    return refuse("operation")
                state["control_version"] += 1
        elif kind == "evaluation.finished":
            actor = event["actor"]
            slot = copy.deepcopy(ctx["records"].get(actor))
            if (slot and slot["status"] == "pending" and slot["epoch"] == ctx["epoch"] and
                    slot["correlation"] == event["correlation_id"] and event["binding"] == "analysis"):
                self.adjust(state, slot, ctx["item"], -1)
                slot["feedback"] = feedback(slot, event["outcome"], ctx)
                slot["status"] = "unavailable" if slot["feedback"]["code"] == "unavailable" else "saved"
                self.adjust(state, slot, ctx["item"], 1)
                effects.append(PutRecord(actor, slot))
                if ctx["item"]["public"]["points"]:
                    effects.append(SetCredit(None if slot["status"] == "unavailable" else
                                             1000 if slot["feedback"]["correct"] else 0))
        return finish(state, effects)

    def view(self, state, audience, ctx):
        role, surface = audience["role"], audience["surface"]
        if surface not in {"presenter": ("presenter-controls", "presenter-overlay"),
                           "projector": ("projector-overlay",), "participant": ("participant-input",)}.get(role, ()):
            raise ValueError("surface-role")
        view = {key: state[key] for key in ("phase", "phase_version", "active")}
        if role != "participant":
            view["count"] = state["count"]
        if role == "participant":
            slot = ctx["records"].get(audience["actor"])
            if slot:
                view["own"] = {key: copy.deepcopy(slot[key]) for key in ("version", "answer", "rationale", "status")}
                if state["phase"] == "revealed" and "feedback" in slot:
                    view["own"]["feedback"] = {k: v for k, v in slot["feedback"].items() if k != "detail"}
                    scoring = ctx.get("scoring", {})
                    if scoring.get("released") and scoring.get("awarded") is not None:
                        view["own"]["points"] = scoring["awarded"]
        if surface == "presenter-controls":
            view.update(control_version=state["control_version"], page=state["page"],
                        pages=max(1, (state["count"] + PAGE_SIZE - 1) // PAGE_SIZE))
            names = {"p": "pending", "u": "unavailable", "c": "correct", "i": "incorrect"}
            view["counts"] = {names[k]: v for k, v in state["counts"].items()}
            view["participants"] = []
            decisions = ctx["item"]["public"]["decisions"]
            for index, actor in enumerate(ctx["record_page"]):
                slot = ctx["records"][actor]
                category = names[self.summary(slot, ctx["item"])["s"]]
                view["participants"].append({"actor": actor, "number": state["page"] * PAGE_SIZE + index + 1,
                                            "version": slot["version"], "status": category})
            view["options"] = [{"decision": d["id"], "counts": [{"option": o["id"], "count": n} for o, n in zip(d["options"], row, strict=True)]}
                               for d, row in zip(decisions, state["options"], strict=True)]
        if role == "presenter" and state["selected"]:
            selected = state["selected"]
            slot = ctx["records"].get(selected["actor"])
            if slot and slot["version"] == selected["version"]:
                view["selected"] = {"answer": copy.deepcopy(slot["answer"]),
                                    "model": model.compile_model(exercise(ctx), slot["answer"])}
                if surface == "presenter-controls":
                    view["selected"].update(actor=selected["actor"], version=slot["version"],
                                            rationale=slot["rationale"], status=slot["status"])
                    if "feedback" in slot:
                        view["selected"]["feedback"] = copy.deepcopy(slot["feedback"])
        if role in ("presenter", "projector") and state["shared"]:
            shared = state["shared"]
            slot = ctx["records"].get(shared["actor"])
            if slot and slot["version"] == shared["version"]:
                view["demonstration"] = {"answer": copy.deepcopy(slot["answer"]),
                                         "model": model.compile_model(exercise(ctx), slot["answer"])}
                if shared["include_rationale"]:
                    view["demonstration"]["rationale"] = slot["rationale"]
        if state["phase"] == "revealed" or role == "presenter":
            view["teaching"] = teaching(ctx["item"])
        if size(view) > VIEW_BYTES:
            raise ValueError("view-capacity")
        return view

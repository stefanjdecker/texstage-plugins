# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Synthetic reference type. Distance is feedback, never the correctness test."""
import math
from texstage.plugin_api.v1 import Evaluate, PluginV1, PreparedItem, Transition, evaluation_correlation


def prepare(record, ctx):
    p, secret = record["public"], record["private"]
    bounds = {k: float(p.get(k, v)) for k, v in {"xmin": -5, "xmax": 5, "ymin": -5, "ymax": 5}.items()}
    answer = {k: float(secret[k]) for k in ("x", "y")}
    if not all(math.isfinite(v) and abs(v) <= 10000 for v in [*bounds.values(), *answer.values()]):
        raise ValueError("invalid coordinates")
    if not bounds["xmin"] < bounds["xmax"] or not bounds["ymin"] < bounds["ymax"]:
        raise ValueError("empty coordinate range")
    if not bounds["xmin"] <= answer["x"] <= bounds["xmax"] or not bounds["ymin"] <= answer["y"] <= bounds["ymax"]:
        raise ValueError("reference is outside the plane")
    return PreparedItem(public=bounds | {"prompt": str(p.get("prompt", "Choose a point."))[:500]},
                        private=answer, evaluations={"distance": {"seed": "{}", "references": []}})


class Plane:
    def initial_state(self, item, ctx):
        return {"points": {}, "revealed": False, "active": False}

    def transition(self, state, event, ctx):
        effects = []
        kind = event["kind"]
        if kind in ("activate", "deactivate"):
            state["active"] = kind == "activate"
        elif kind == "command" and event["operation"] == "reveal":
            state["revealed"] = True
        elif kind == "command" and event["operation"] == "submit-point":
            p, limits = event["payload"], ctx["item"]["public"]
            if not limits["xmin"] <= p["x"] <= limits["xmax"] or not limits["ymin"] <= p["y"] <= limits["ymax"]:
                return {"refusal": "point-outside-plane"}
            correlation = evaluation_correlation(event["actor"], event["request_id"], "distance")
            state["points"][event["actor"]] = {"point": p, "correlation": correlation, "status": "queued"}
            effects.append(Evaluate("distance", correlation, f"{p['x']},{p['y']}"))
        elif kind == "evaluation.finished":
            own = state["points"].get(event["actor"])
            if own and own["correlation"] == event["correlation_id"]:
                own["status"] = event["outcome"]["status"]
                own["feedback"] = event["outcome"].get("summary", {}).get("text", "")
        return Transition(state, effects)

    def view(self, state, audience, ctx):
        target = ctx["item"]["private"]
        view = {"revealed": state["revealed"], "active": state["active"], "count": len(state["points"])}
        if audience["role"] == "participant":
            own = state["points"].get(audience["actor"])
            if own:
                view["own"] = {k: v for k, v in own.items() if k != "correlation"}
                if state["revealed"]:
                    view["own"]["correct"] = all(abs(own["point"][k] - target[k]) < 1e-8 for k in ("x", "y"))
        else:
            view["points"] = [p["point"] for p in state["points"].values()]
        if state["revealed"] or audience["role"] == "presenter": view["answer"] = target
        return view


def create_plugin():
    return PluginV1(build_hooks={"plane": prepare}, state_hooks={"plane": Plane()})

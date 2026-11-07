# SPDX-License-Identifier: Apache-2.0
"""Lossless, bounded private state encoding (state schema 5).

Wire answers and engine facts retain their documented object schemas. Only the
host-owned per-student answer/feedback use arrays, avoiding repeated field names.
There is no compression, executable decoding or domain-dependent pruning: even
syntactically valid but mathematically incorrect predictions round-trip exactly.
The complete slot is stored as a JSON string. Generic host copies then copy one
immutable value, rather than every tree prediction and field in the class.
"""
import json
from .grading import CRITERIA, RUBRIC
REPAIRS = ("split", "borrow", "merge")
REASONS = ("wrong-path", "wrong-scan", "missing-repair", "extra-repair",
           "wrong-pending-node", "illegal-split", "wrong-separator",
           "illegal-donor", "illegal-merge")
CLAIMS = ("keys", "separators", "height")
STATUSES = ("pending", "saved", "unavailable")


def pack_answer(answer):
    path = list(answer["path"])
    if "repairs" not in answer:
        if "leaves" in answer:
            return [1, path, list(answer["keys"]), list(answer["leaves"])]
        return [0, path, list(answer["keys"])]
    repairs = [[0, r["node"], r["left_count"], r["separator"]] if r["op"] == "split"
               else [REPAIRS.index(r["op"]), r["node"], r["sibling"]] for r in answer["repairs"]]
    return [2, path, repairs, [[r["node"], *r["keys"]] for r in answer["separators"]], answer["height"]]


def unpack_answer(value):
    answer = {"format": 1, "path": list(value[1])}
    if value[0] in (0, 1):
        answer["keys"] = list(value[2])
        if value[0] == 1:
            answer["leaves"] = list(value[3])
    else:
        answer.update(repairs=[{"op": "split", "node": r[1], "left_count": r[2], "separator": r[3]}
                               if r[0] == 0 else {"op": REPAIRS[r[0]], "node": r[1], "sibling": r[2]}
                               for r in value[2]],
                      separators=[{"node": r[0], "keys": r[1:]} for r in value[3]], height=value[4])
    return answer


def pack_feedback(value):
    if "grade" in value:
        plain = {k: v for k, v in value.items() if k != "grade"}
        return [3, pack_feedback(plain), [[CRITERIA.index(k), v] for k, v in value["grade"]["parts"].items()]]
    if value["code"] == "unavailable":
        return [0, value["reason"]]
    if value["reason"] in ("complete", "prediction"):
        return [1, [CLAIMS.index(name) for name in value["failed"]], value["checked_repairs"]]
    return [2, REASONS.index(value["reason"]), value["checked_repairs"], value["at"], value["node"]]


def unpack_feedback(value):
    if value[0] == 3:
        result = unpack_feedback(value[1])
        parts = {CRITERIA[k]: v for k, v in value[2]}
        result["grade"] = {"rubric": RUBRIC, "credit": sum(parts.values()), "parts": parts}
        return result
    if value[0] == 0:
        return {"code": "unavailable", "reason": value[1]}
    if value[0] == 1:
        failed = [CLAIMS[index] for index in value[1]]
        return {"code": "revise" if failed else "correct", "correct": not failed,
                "reason": "prediction" if failed else "complete", "failed": failed,
                "checked_repairs": value[2]}
    return {"code": "revise", "correct": False, "reason": REASONS[value[1]],
            "checked_repairs": value[2], "at": value[3], "node": value[4]}


def read_slot(slot):
    if slot is None:
        return None
    values = json.loads(slot)
    result = {"version": values[0], "answer": unpack_answer(values[1]),
              "correlation": values[2], "epoch": values[3], "status": STATUSES[values[4]]}
    if len(values) == 6:
        result["feedback"] = unpack_feedback(values[5])
    return result


def write_slot(slot):
    result = [slot["version"], pack_answer(slot["answer"]), slot["correlation"],
              slot["epoch"], STATUSES.index(slot["status"])]
    if "feedback" in slot:
        result.append(pack_feedback(slot["feedback"]))
    return json.dumps(result, separators=(",", ":"))


def reserve_slot(slot, max_version, feedback_bytes):
    values = json.loads(slot)[:5]
    values[0] = max_version
    # A quoted string is larger than any encoded feedback within this bound.
    values.append("x" * feedback_bytes)
    return json.dumps(values, separators=(",", ":"))

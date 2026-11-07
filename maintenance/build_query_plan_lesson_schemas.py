# SPDX-License-Identifier: Apache-2.0
"""Generate frozen Query-plan Q3 command and portable view schemas."""
import copy
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "plugins/query-plan/texstage_query_plan/schemas"
VERSION = {"type": "integer", "minimum": 0, "maximum": 1000000000}
COUNT = {"type": "integer", "minimum": 0, "maximum": 64}
COST = {"type": "integer", "minimum": 0, "maximum": 3000000000000}
ACTOR = {"type": "string", "minLength": 1, "maxLength": 256}
REASONS = ["invalid-tree", "unknown-relation", "duplicate-relation", "missing-relation",
           "disconnected-join", "unavailable-index", "hash-memory"]
CODES = ["pending", "goal-met", "target-missed", "invalid", "unavailable"]
def obj(properties, required=None):
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties) if required is None else required}
def string_enum(values): return {"type": "string", "enum": values}
def write(name, value):
    path = BASE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
def portable_answer():
    answer = json.loads((BASE / "answer-v1.json").read_text(encoding="utf-8"))
    answer.pop("$schema", None); answer.pop("title", None)
    answer["properties"]["format"] = {"type": "integer", "const": 1}
    relation = answer["properties"]["nodes"]["items"]["oneOf"][0]["properties"]["relation"]
    relation.pop("pattern")
    relation.update(minLength=1, maxLength=16)
    return answer

def build():
    answer = portable_answer()
    write("commands/submit-plan-v1.json", obj({"phase": VERSION, "version": VERSION, "answer": answer}))
    write("commands/control-v1.json", obj({"control": VERSION}))
    write("commands/select-answer-v1.json", obj({"control": VERSION, "actor": {"oneOf": [ACTOR, {"type": "null"}]}}))
    feedback = {"oneOf": [
        obj({"code": {"const": "goal-met"}, "correct": {"const": True}, "cost": COST}),
        obj({"code": {"const": "target-missed"}, "correct": {"const": False}, "cost": COST}),
        obj({"code": {"const": "invalid"}, "correct": {"const": False}, "reason": string_enum(REASONS),
             "node": {"type": "integer", "minimum": -1, "maximum": 4}}),
        obj({"code": {"const": "unavailable"}})]}
    private_feedback = copy.deepcopy(feedback)
    private_feedback["oneOf"][-1] = obj({"code": {"const": "unavailable"},
        "detail": string_enum(["error", "syntax", "refused", "timeout", "cancelled", "identity", "facts", "capacity"])})
    explanation = obj({language: {"type": "string", "minLength": 1, "maxLength": 2000} for language in ("en", "de")})
    solution = obj({"worked_answer": {"$ref": "#/$defs/answer"}, "optimal_answer": {"$ref": "#/$defs/answer"},
                    "explanation": explanation, "minimum": COST, "ties": {"type": "integer", "minimum": 1, "maximum": 864}})
    own = obj({"version": VERSION, "answer": {"$ref": "#/$defs/answer"},
               "status": string_enum(["pending", "saved", "unavailable"]), "feedback": feedback},
              ["version", "answer", "status"])
    base = {"phase": string_enum(["introduce", "open", "closed", "revealed"]),
            "phase_version": VERSION, "active": {"type": "boolean"}, "count": COUNT}
    for role in ("participant", "presenter", "projector"):
        fields = copy.deepcopy(base)
        fields["solution"] = solution
        required = list(base)
        if role == "participant":
            fields["own"] = own
        if role in ("presenter", "projector"):
            fields["demonstration"] = {"$ref": "#/$defs/answer"}
        if role == "presenter":
            fields["control_version"] = VERSION
            fields["counts"] = obj({k: COUNT for k in CODES})
            fields["participants"] = {"type": "array", "minItems": 0, "maxItems": 64,
                "items": obj({"actor": ACTOR, "number": {"type": "integer", "minimum": 1, "maximum": 64},
                              "status": string_enum(CODES)})}
            selected = copy.deepcopy(own)
            selected["properties"]["actor"] = ACTOR
            selected["properties"]["feedback"] = private_feedback
            selected["required"].append("actor")
            fields["selected"] = selected
            required += ["control_version", "counts", "participants", "solution"]
        schema = obj(fields, required)
        schema["$defs"] = {"answer": answer}
        write("views/" + role + "-v1.json", schema)

if __name__ == "__main__": build()

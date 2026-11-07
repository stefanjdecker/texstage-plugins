# SPDX-License-Identifier: Apache-2.0
"""Generate the frozen v1 schemas; --check detects drift without writing."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "plugins/normalization-workshop/texstage_normalization_workshop/schemas"
I = lambda lo=0, hi=255: {"type": "integer", "minimum": lo, "maximum": hi}
S = lambda lo, hi: {"type": "string", "minLength": lo, "maxLength": hi}
E = lambda *values: {"enum": list(values)}
O = lambda **fields: {"type": "object", "additionalProperties": False, "required": list(fields), "properties": fields}
A = lambda items, lo, hi, unique=False: {"type": "array", "minItems": lo, "maxItems": hi, "items": items, **({"uniqueItems": True} if unique else {})}
T = lambda *items: {"type": "array", "minItems": len(items), "maxItems": len(items), "prefixItems": list(items), "items": False}
N = lambda schema: {"anyOf": [{"type": "null"}, schema]}
R = lambda name: {"$ref": "#/$defs/" + name}
MASK, HASH, VERSION = I(), S(64, 64), I(0, 2147483647)
FORM = E("1nf", "2nf", "3nf", "bcnf")
PAIR = T(MASK, E(1, 2, 4, 8, 16, 32, 64, 128))
TASK = {"oneOf": [O(mode=E("classify")), O(mode=E("decompose"), target=E("3nf", "bcnf"), preserve={"type": "boolean"})]}
ANSWER = {"oneOf": [O(mode=E("classify"), normal_form=FORM, witness=N(PAIR)),
                    O(mode=E("decompose"), relations=A(I(1), 1, 8, True))]}
WITNESSES = O(**{name: N(PAIR) for name in ("2nf", "3nf", "bcnf")})
COMPONENT = O(relation=I(1), normal_form=FORM, prime=MASK, witnesses=R("witnesses"))
CLASS = O(normal_form=FORM, prime=MASK, keys=A(MASK, 1, 70, True),
          witnesses=R("witnesses"), witness_valid={"type": "boolean"})
PRESERVATION = O(preserved={"type": "boolean"}, fd=I(-1, 31), closure=MASK)
JOIN = O(lossless={"type": "boolean"}, rows=I(1, 8), columns=I(1, 8),
         merges=A(T(I(0, 31), I(0, 7), I(0, 7)), 0, 56),
         tableau=A(A(I(0, 71), 1, 8), 1, 8))
DECOMPOSE = O(covered={"type": "boolean"}, missing=MASK,
              components=A(R("component"), 1, 8), preservation=N(PRESERVATION), join=N(JOIN))
DATA = {"oneOf": [
    O(format={"const": 1, "type": "integer"}, exercise=HASH, answer=HASH, mode=E("classify"), facts=R("class")),
    O(format={"const": 1, "type": "integer"}, exercise=HASH, answer=HASH, mode=E("decompose"), facts=R("decompose"))]}
DEFS = {"witnesses": WITNESSES, "component": COMPONENT, "class": CLASS, "decompose": DECOMPOSE}
FEEDBACK = O(accepted={"type": "boolean"}, normal_form=N(FORM), missing=MASK,
             lossless=N({"type": "boolean"}), preserved=N({"type": "boolean"}),
             witness=N(PAIR), lost_fd=I(-1, 31))
SLOT = O(handle=HASH, version=VERSION, answer=R("answer"), correlation=N(HASH),
         status=E("pending", "checked", "unavailable"), feedback=N(R("feedback")))
REF = O(handle=HASH, version=VERSION)
PHASE = E("introduce", "open", "closed", "revealed")
WORKED = O(answer=R("answer"), explanation=S(1, 4000))
COUNTS = O(**{k: I(0, 64) for k in ("received", "pending", "checked", "unavailable")})
DEFS_VIEW = DEFS | {"answer": ANSWER, "feedback": FEEDBACK, "analysis": DATA, "worked": WORKED}
LABEL = lambda limit: O(en=S(1, limit), de=S(1, limit))
identifier = S(1, 12) | {"pattern": "^[A-Za-z][A-Za-z0-9_]{0,11}$"}
exercise_id = S(1, 48) | {"pattern": "^[A-Za-z][A-Za-z0-9_]{0,47}$"}
EXERCISE = O(format={"type": "integer", "const": 1}, id=exercise_id, title=LABEL(120),
             prompt=LABEL(1000), attributes=A(O(id=identifier, label=LABEL(48)), 1, 8),
             fds=A(O(lhs=A(identifier, 0, 8, True), rhs=A(identifier, 1, 8, True)), 0, 32), task=TASK)
schemas = {
    "seed-v1.json": O(format={"const": 1, "type": "integer"}, id=exercise_id,
                      attributes=A(identifier, 1, 8, True), fds=A(PAIR, 0, 32, True), task=TASK),
    "answer-v1.json": ANSWER,
    "analysis-result-v1.json": DATA | {"$defs": DEFS},
    "lesson-v1.json": O(format={"type": "integer", "const": 1}, exercise=EXERCISE,
                        worked_answer=ANSWER, explanation=LABEL(4000)),
    "state-v1.json": O(phase=PHASE, phase_version=VERSION, control_version=VERSION,
                       active={"type": "boolean"}, actors=A(R("slot"), 0, 64),
                       selected=N(REF), shared=N(REF)) | {"$defs": {"slot": SLOT, "answer": ANSWER, "feedback": FEEDBACK}},
    "commands/submit-v1.json": O(phase=VERSION, version=VERSION, answer=ANSWER),
    "commands/control-v1.json": O(control=VERSION),
    "commands/select-v1.json": O(control=VERSION, handle=HASH, version=VERSION),
    "views/participant-input-v1.json": O(phase=PHASE, active={"type": "boolean"}, phase_version=VERSION,
        answer_version=VERSION, answer=N(R("answer")), status=N(E("pending", "checked", "unavailable")),
        feedback=N(R("feedback")), worked=N(R("worked"))) | {"$defs": {"answer": ANSWER, "feedback": FEEDBACK, "worked": WORKED}},
    "views/projector-overlay-v1.json": O(phase=PHASE, counts=COUNTS,
        shared=N(O(answer=R("answer"), version=VERSION)), worked=N(R("worked"))) |
        {"$defs": {"answer": ANSWER, "worked": WORKED}},
    "views/presenter-overlay-v1.json": O(phase=PHASE, counts=COUNTS,
        selected=N(O(answer=R("answer"), version=VERSION, analysis=R("analysis"))),
        worked=N(R("worked"))) | {"$defs": DEFS_VIEW},
    "views/presenter-controls-v1.json": O(phase=PHASE, active={"type": "boolean"},
        control_version=VERSION, phase_version=VERSION, counts=COUNTS,
        answers=A(O(handle=HASH, version=VERSION, status=E("pending", "checked", "unavailable")), 0, 64),
        selected=N(REF), shared=N(REF)),
}

# V2 classroom projections. Frozen v1 resources above remain byte-identical.
TOPIC = E("summary", "lossless", "preservation")
REFS = A(REF, 0, 2)
DETAIL = O(answer=R("answer"), version=VERSION, analysis=R("analysis"))
SHARED_DETAIL = O(answer=R("answer"), version=VERSION, analysis=N(R("analysis")))
schemas.update({
    "state-v2.json": O(phase=PHASE, phase_version=VERSION, control_version=VERSION,
        active={"type":"boolean"}, actors=A(R("slot"), 0, 64), selected=REFS, shared=REFS,
        share_checks={"type":"boolean"}, topic=TOPIC) |
        {"$defs":{"slot":SLOT,"answer":ANSWER,"feedback":FEEDBACK}},
    "commands/compare-v1.json": O(control=VERSION, answers=A(REF, 2, 2)),
    "commands/topic-v1.json": O(control=VERSION, topic=TOPIC),
    "views/participant-input-v2.json": O(phase=PHASE, active={"type":"boolean"}, phase_version=VERSION,
        answer_version=VERSION, answer=N(R("answer")), status=N(E("pending","checked","unavailable")),
        feedback=N(R("feedback")), worked=N(R("worked")), analysis=N(R("analysis"))) | {"$defs":DEFS_VIEW},
    "views/presenter-controls-v2.json": O(phase=PHASE, active={"type":"boolean"},
        control_version=VERSION, phase_version=VERSION, counts=COUNTS,
        answers=A(O(handle=HASH,version=VERSION,status=E("pending","checked","unavailable")),0,64),
        selected=REFS,shared=REFS,share_checks={"type":"boolean"},topic=TOPIC),
    "views/presenter-overlay-v2.json": O(phase=PHASE, counts=COUNTS, topic=TOPIC,
        selected=A(DETAIL,0,2),worked=N(R("worked"))) | {"$defs":DEFS_VIEW},
    "views/projector-overlay-v2.json": O(phase=PHASE, counts=COUNTS, topic=TOPIC,
        shared=A(SHARED_DETAIL,0,2),worked=N(R("worked"))) | {"$defs":DEFS_VIEW},
})

# V3 moves actor answers to scoped item records. V1/V2 remain immutable.
COUNTS3 = O(**{k: I(0, 1000) for k in ("received", "pending", "checked", "unavailable")})
ROW3 = O(handle=HASH, number=I(1,1000), version=VERSION, status=E("pending","checked","unavailable"))
schemas.update({
    "state-v3.json": O(phase=PHASE, phase_version=VERSION, control_version=VERSION,
        active={"type":"boolean"}, page=I(0,62), counts=COUNTS3, selected=REFS, shared=REFS,
        share_checks={"type":"boolean"}, topic=TOPIC),
    "record-v1.json": O(**SLOT["properties"], number=I(1,1000)) |
        {"$defs":{"answer":ANSWER,"feedback":FEEDBACK}},
    "commands/page-v1.json": O(control=VERSION,page=I(0,62)),
    "views/presenter-controls-v3.json": O(phase=PHASE,active={"type":"boolean"},
        control_version=VERSION,phase_version=VERSION,counts=COUNTS3,
        page=I(0,62),pages=I(1,63),answers=A(ROW3,0,16),pinned=A(ROW3,0,4),
        selected=REFS,shared=REFS,share_checks={"type":"boolean"},topic=TOPIC),
    "views/presenter-overlay-v3.json": O(phase=PHASE,counts=COUNTS3,topic=TOPIC,
        selected=A(DETAIL,0,2),worked=N(R("worked"))) | {"$defs":DEFS_VIEW},
    "views/projector-overlay-v3.json": O(phase=PHASE,counts=COUNTS3,topic=TOPIC,
        shared=A(SHARED_DETAIL,0,2),worked=N(R("worked"))) | {"$defs":DEFS_VIEW},
})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    check = parser.parse_args().check
    for name, value in schemas.items():
        payload = json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                              "title": "Normalization Workshop " + name, **value}, indent=2) + "\n"
        target = ROOT / name
        if check:
            assert target.read_text(encoding="utf-8") == payload, name
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="utf-8", newline="\n")
    print(("Verified" if check else "Generated"), len(schemas), "schemas")


if __name__ == "__main__":
    main()

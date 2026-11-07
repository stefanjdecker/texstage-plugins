# SPDX-License-Identifier: Apache-2.0
"""Generate closed B3 command and audience schemas; --check detects stale files."""
import argparse
import json
from build_bplus_schemas import DEST, arr, const, definitions, document, enum, nullable, num, obj, ref, schemas as engine_schemas


def schemas():
    defs = definitions()
    defs["answer"] = {"oneOf": [ref("lookup"), ref("range"), ref("update")]}
    defs["grade"] = obj({"rubric": const("bplus-partial-v1"), "credit": num(0, 1000),
        "parts": {"oneOf": [obj({k: num(0, n) for k, n in weights.items()}) for weights in (
            {"path": 400, "keys": 600}, {"path": 300, "scan": 400, "keys": 300},
            {"path": 200, "repairs": 500, "separators": 200, "height": 100})]}})
    defs["feedback"] = {"oneOf": [
        obj({"code": const("unavailable"), "reason": enum("evaluation", "facts", "identity", "binding")}),
        obj({"code": enum("correct", "revise"), "correct": {"type": "boolean"},
             "reason": enum("complete", "prediction"), "failed": arr(enum("keys", "separators", "height"), 0, 3),
             "checked_repairs": num(0, 3), "grade": ref("grade")}),
        obj({"code": const("revise"), "correct": const(False),
             "reason": enum("wrong-path", "wrong-scan", "missing-repair", "extra-repair", "wrong-pending-node",
                            "illegal-split", "wrong-separator", "illegal-donor", "illegal-merge"),
             "checked_repairs": num(0, 3), "at": num(0, 20), "node": nullable(num(0, 63)), "grade": ref("grade")}),
    ]}
    version, actor = num(0, 1_000_000_000), {"type": "string", "minLength": 1, "maxLength": 256}
    status = enum("pending", "saved", "unavailable")
    base = {"format": {"type": "integer", "const": 1}, "phase": enum("introduce", "open", "closed", "revealed"),
            "phase_version": version, "active": {"type": "boolean"}, "count": num(0, 1000)}
    results = engine_schemas()["analysis-result-v1.json"]["oneOf"]
    defs["worked"] = obj({"answer": ref("answer"),
        "explanation": obj({lang: {"type": "string", "minLength": 1, "maxLength": 1200} for lang in ("en", "de")}, ["en"]),
        "result": {"oneOf": [obj({"read": results[0]["properties"]["read"]}),
                            obj({k: results[1]["properties"][k] for k in ("final", "metrics")})]}})
    shared = obj({"answer": ref("answer"), "feedback": ref("feedback")}, ["answer"])
    focus = {"oneOf": [obj({"kind": enum("start", "prediction")}),
                        obj({"kind": enum("path", "scan", "repair"), "index": num(0, 19)})]}
    optional = {"demonstration": shared, "worked": ref("worked"),
                "replay": obj({"source": enum("shared", "worked"), "step": num(0, 24), "total": num(2, 25), "focus": focus})}
    outputs = {}
    for surface in ("participant-input", "presenter-controls", "presenter-overlay", "projector-overlay"):
        props = {**base, **optional}
        required = list(base)
        if surface == "participant-input":
            del props["count"]; required.remove("count")
            props["scoring"] = obj({"maximum": num(0, 10000), "released": {"type": "boolean"}, "awarded": nullable(num(0, 10000))})
            required.append("scoring")
            props["own"] = obj({"version": num(1, 1_000_000_000), "answer": ref("answer"), "status": status,
                                "feedback": ref("feedback")}, ["version", "answer", "status"])
        elif surface == "presenter-controls":
            props.update(control_version=version,
                         counts=obj({k: num(0, 1000) for k in ("pending", "saved", "unavailable")}),
                         participants=arr(obj({"actor": actor, "number": num(1, 1000), "version": num(1, 1_000_000_000), "status": status}), 0, 25),
                         selected=obj({"actor": actor, "version": num(1, 1_000_000_000), "status": status,
                                       "answer": ref("answer"), "feedback": ref("feedback")},
                                      ["actor", "version", "status", "answer"]))
            props["roster_page"] = obj({"page": num(0, 39), "pages": num(1, 40), "total": num(0, 1000)})
            required += ["control_version", "counts", "participants", "roster_page"]
        used = {k: defs[k] for k in ("page", "tree", "lookup", "range", "update", "answer", "feedback", "grade", "worked")}
        outputs[surface + "-v2.json"] = document(obj(props, required), "B+ " + surface + " v2", used)
    commands = {
        "submit": obj({"phase_version": version, "answer_version": version, "answer": ref("answer")}),
        "control": obj({"control_version": version}),
        "page": obj({"control_version": version, "page": num(0, 39)}),
        "selection": obj({"control_version": version, "actor": {"type": "string", "maxLength": 256}, "answer_version": version}),
        "replay": obj({"control_version": version, "source": enum("shared", "worked"), "step": num(0, 24)}),
    }
    for name, schema in commands.items():
        outputs["command-" + name + "-v2.json"] = document(schema, "B+ " + name + " command v2",
            {k: defs[k] for k in ("lookup", "range", "update", "answer")} if name == "submit" else None)
    outputs["actor-value-v1.json"] = document({"type": "string", "maxLength": 704}, "B+ private slot v1")
    outputs["actor-summary-v1.json"] = document(obj({"version": num(1, 1_000_000_000), "status": status}), "B+ private roster summary v1")
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, schema in schemas().items():
        data = (json.dumps(schema, ensure_ascii=True, indent=2) + "\n").encode()
        path = DEST / name
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(name + " is stale; run maintenance/build_bplus_lesson_schemas.py")
        else:
            path.write_bytes(data)
    print(("Verified" if args.check else "Generated") + " eleven B+ classroom schemas")


if __name__ == "__main__":
    main()

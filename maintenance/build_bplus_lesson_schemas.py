# SPDX-License-Identifier: Apache-2.0
"""Generate closed B3 command and audience schemas; --check detects stale files."""
import argparse
import json
from build_bplus_schemas import DEST, arr, const, definitions, document, enum, nullable, num, obj, ref, schemas as engine_schemas


def schemas():
    defs = definitions()
    defs["answer"] = {"oneOf": [ref("lookup"), ref("range"), ref("update")]}
    defs["feedback"] = {"oneOf": [
        obj({"code": const("unavailable"), "reason": enum("evaluation", "facts", "identity", "binding")}),
        obj({"code": enum("correct", "revise"), "correct": {"type": "boolean"},
             "reason": enum("complete", "prediction"), "failed": arr(enum("keys", "separators", "height"), 0, 3),
             "checked_repairs": num(0, 3)}),
        obj({"code": const("revise"), "correct": const(False),
             "reason": enum("wrong-path", "wrong-scan", "missing-repair", "extra-repair", "wrong-pending-node",
                            "illegal-split", "wrong-separator", "illegal-donor", "illegal-merge"),
             "checked_repairs": num(0, 3), "at": num(0, 20), "node": nullable(num(0, 63))}),
    ]}
    version, actor = num(0, 1_000_000_000), {"type": "string", "minLength": 64, "maxLength": 64}
    status = enum("pending", "saved", "unavailable")
    base = {"format": {"type": "integer", "const": 1}, "phase": enum("introduce", "open", "closed", "revealed"),
            "phase_version": version, "active": {"type": "boolean"}, "count": num(0, 48)}
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
            props["own"] = obj({"version": num(1, 1_000_000_000), "answer": ref("answer"), "status": status,
                                "feedback": ref("feedback")}, ["version", "answer", "status"])
        elif surface == "presenter-controls":
            props.update(control_version=version,
                         counts=obj({k: num(0, 48) for k in ("pending", "saved", "unavailable")}),
                         participants=arr(obj({"actor": actor, "version": num(1, 1_000_000_000), "status": status}), 0, 48),
                         selected=obj({"actor": actor, "version": num(1, 1_000_000_000), "status": status,
                                       "answer": ref("answer"), "feedback": ref("feedback")},
                                      ["actor", "version", "status", "answer"]))
            required += ["control_version", "counts", "participants"]
        used = {k: defs[k] for k in ("page", "tree", "lookup", "range", "update", "answer", "feedback", "worked")}
        outputs[surface + "-v2.json"] = document(obj(props, required), "B+ " + surface + " v2", used)
    commands = {
        "submit": obj({"phase_version": version, "answer_version": version, "answer": ref("answer")}),
        "control": obj({"control_version": version}),
        "selection": obj({"control_version": version, "actor": {"type": "string", "maxLength": 64}, "answer_version": version}),
        "replay": obj({"control_version": version, "source": enum("shared", "worked"), "step": num(0, 24)}),
    }
    for name, schema in commands.items():
        outputs["command-" + name + "-v2.json"] = document(schema, "B+ " + name + " command v2",
            {k: defs[k] for k in ("lookup", "range", "update", "answer")} if name == "submit" else None)
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
    print(("Verified" if args.check else "Generated") + " eight B+ classroom schemas")


if __name__ == "__main__":
    main()

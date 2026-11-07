# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Generate the owned, closed B+ engine schemas; --check detects stale resources."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "plugins/bplus-lab/texstage_bplus_lab/schemas"
DIALECT = "https://json-schema.org/draft/2020-12/schema"


def obj(properties, required=None):
    return {"type": "object", "additionalProperties": False,
            "required": list(properties) if required is None else required, "properties": properties}


def arr(item, lo, hi):
    return {"type": "array", "minItems": lo, "maxItems": hi, "items": item}


def num(lo, hi):
    return {"type": "integer", "minimum": lo, "maximum": hi}


def const(value):
    return {"const": value}


def enum(*values):
    return {"enum": list(values)}


def ref(name):
    return {"$ref": "#/$defs/" + name}


def nullable(value):
    return {"anyOf": [value, {"type": "null"}]}


def document(schema, title, definitions=None):
    result = {"$schema": DIALECT, "title": title, **schema}
    if definitions:
        result["$defs"] = definitions
    return result


def definitions():
    page_id, key = num(0, 63), num(-9999, 9999)
    leaf = obj({"id": page_id, "kind": const("leaf"), "keys": arr(key, 0, 6), "next": nullable(page_id)})
    internal = obj({"id": page_id, "kind": const("internal"), "keys": arr(key, 1, 5),
                    "children": arr(page_id, 2, 6)})
    tree = obj({"root": page_id, "nodes": arr(ref("page"), 1, 35)})
    initial = obj({"root": {"type": "integer", "const": 0}, "nodes": arr(ref("page"), 1, 31)})
    task = {"oneOf": [obj({"kind": enum("lookup", "insert", "delete"), "key": key}),
                       obj({"kind": const("range"), "lower": key, "upper": key})]}
    exercise = obj({"format": {"type": "integer", "const": 1}, "semantics": const("bplus-operations-v1"),
                    "leaf_capacity": num(3, 6), "internal_capacity": num(3, 6),
                    "tree": initial, "task": task})
    repair = {"oneOf": [
        obj({"op": const("split"), "node": page_id, "left_count": num(1, 6), "separator": key}),
        obj({"op": enum("borrow", "merge"), "node": page_id, "sibling": page_id}),
    ]}
    base = {"format": {"type": "integer", "const": 1}, "path": arr(page_id, 1, 3)}
    lookup = obj({**base, "keys": arr(key, 0, 1)})
    interval = obj({**base, "keys": arr(key, 0, 40), "leaves": arr(page_id, 1, 20)})
    update = obj({**base, "repairs": arr(repair, 0, 3),
                  "separators": arr(obj({"node": page_id, "keys": arr(key, 1, 5)}), 0, 10),
                  "height": num(0, 3)})
    return {"page": {"oneOf": [leaf, internal]}, "tree": tree, "exercise": exercise,
            "lookup": lookup, "range": interval, "update": update}


def schemas():
    defs = definitions()
    answer = {"oneOf": [ref("lookup"), ref("range"), ref("update")]}
    outputs = {
        "exercise-v1.json": document(ref("exercise"), "B+ operation exercise v1",
                                      {k: defs[k] for k in ("exercise", "page")}),
        "answer-v1.json": document(answer, "B+ operation answer v1",
                                    {k: defs[k] for k in ("lookup", "range", "update")}),
    }
    digest = {"type": "string", "minLength": 64, "maxLength": 64}
    base = {"format": {"type": "integer", "const": 1}, "exercise": digest, "answer": digest}
    complete = lambda cap: obj({"state": const("complete"), "checked_repairs": num(0, cap)})
    claims = lambda read: obj({"path": const(True), "keys": {"type": "boolean" if read else "null"},
                               "separators": {"type": "null" if read else "boolean"},
                               "height": {"type": "null" if read else "boolean"}})
    read = obj({**base, "operation": enum("lookup", "range"), "replay": complete(0), "claims": claims(True),
                "read": obj({"path": arr(num(0, 63), 1, 3), "leaves": arr(num(0, 63), 1, 20),
                             "keys": arr(num(-9999, 9999), 0, 40), "page_visits": num(1, 22)})})
    update = obj({**base, "operation": enum("insert", "delete"), "replay": complete(3), "claims": claims(False),
                  "final": ref("tree"),
                  "metrics": obj({"height_before": num(0, 2), "height_after": num(0, 3), "leaf_count": num(1, 21),
                                  "splits": num(0, 3), "borrows": num(0, 3), "merges": num(0, 3)})})
    reasons = ("wrong-path", "wrong-scan", "extra-repair", "wrong-pending-node", "illegal-split",
               "wrong-separator", "illegal-donor", "illegal-merge")
    fail = lambda state, reason: obj({"state": const(state), "reason": reason, "checked_repairs": num(0, 3),
                                     "at": num(0, 20), "node": nullable(num(0, 63))})
    invalid = obj({**base, "operation": enum("lookup", "range", "insert", "delete"),
                   "replay": fail("invalid", enum(*reasons))})
    incomplete = obj({**base, "operation": enum("insert", "delete"),
                      "replay": fail("incomplete", const("missing-repair"))})
    outputs["analysis-result-v1.json"] = document(
        {"oneOf": [read, update, invalid, incomplete]}, "B+ operation facts v1",
        {k: defs[k] for k in ("tree", "page")})
    localized = lambda limit: obj({
        "en": {"type": "string", "minLength": 1, "maxLength": limit},
        "de": {"type": "string", "minLength": 1, "maxLength": limit}}, required=["en"])
    outputs["lesson-v1.json"] = document(obj({
        "format": {"type": "integer", "const": 1}, "title": localized(160), "prompt": localized(800),
        "exercise": ref("exercise"),
        "worked": obj({"answer": answer, "explanation": localized(1200)}),
        "feedback": enum("on-reveal", "immediate"),
    }), "B+ lesson envelope v1", {k: defs[k] for k in ("page", "exercise", "lookup", "range", "update")})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    for name, schema in schemas().items():
        text = json.dumps(schema, ensure_ascii=True, indent=2) + "\n"
        path = DEST / name
        if args.check:
            if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
                raise SystemExit(name + " is stale; run maintenance/build_bplus_schemas.py")
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    print(("Verified" if args.check else "Generated") + " four B+ schemas")


if __name__ == "__main__":
    main()

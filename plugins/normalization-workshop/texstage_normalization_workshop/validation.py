# SPDX-License-Identifier: Apache-2.0
"""Owned bounded parser and semantic validators; schema checks supplement these."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

FORMS = ("1nf", "2nf", "3nf", "bcnf")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,11}\Z")


class InputError(ValueError):
    pass


class ResourceLimit(ValueError):
    pass


def require(condition, reason="invalid-input"):
    if not condition:
        raise InputError(reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def identity(tag, value):
    return hashlib.sha256(canonical([tag, value]).encode("ascii")).hexdigest()


def fields(value, names):
    return type(value) is dict and set(value) == set(names)


def integer(value, lo=0, hi=255):
    return type(value) is int and lo <= value <= hi


def bounded(value):
    count = 0
    def visit(v, depth):
        nonlocal count
        count += 1
        if count > 8192 or depth > 16:
            raise ResourceLimit("json-depth-or-values")
        if type(v) is str:
            require(not any(0xD800 <= ord(c) <= 0xDFFF for c in v), "surrogate")
            return unicodedata.normalize("NFC", v)
        if type(v) is list:
            return [visit(x, depth + 1) for x in v]
        if type(v) is dict:
            out = {}
            for k, item in v.items():
                require(type(k) is str)
                key = visit(k, depth + 1)
                require(key not in out, "duplicate-key")
                out[key] = visit(item, depth + 1)
            return out
        require(v is None or type(v) is bool or integer(v, -(2**53 - 1), 2**53 - 1))
        return v
    return visit(value, 0)


def parse(text, limit=65536):
    require(type(text) is str)
    try:
        if len(text.encode("utf-8")) > limit:
            raise ResourceLimit("input-bytes")
    except UnicodeEncodeError as exc:
        raise InputError("surrogate") from exc
    def pairs(values):
        out = {}
        for key, value in values:
            require(key not in out, "duplicate-key")
            out[key] = value
        return out
    def no_float(_):
        raise InputError("integer-tokens-only")
    try:
        return bounded(json.loads(text, object_pairs_hook=pairs,
                                  parse_float=no_float, parse_constant=no_float))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise InputError("json") from exc
    except ValueError as exc:
        if isinstance(exc, (InputError, ResourceLimit)):
            raise
        raise InputError("number") from exc


def task(value):
    require(type(value) is dict)
    if value.get("mode") == "classify":
        require(fields(value, ["mode"]))
    else:
        require(fields(value, ["mode", "target", "preserve"]) and
                value["mode"] == "decompose" and value["target"] in ("3nf", "bcnf") and
                type(value["preserve"]) is bool)
    return dict(value)


def seed(value):
    value = bounded(value)
    require(fields(value, ["format", "id", "attributes", "fds", "task"]))
    require(type(value["format"]) is int and value["format"] == 1)
    require(type(value["id"]) is str and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}", value["id"])))
    attributes = value["attributes"]
    require(type(attributes) is list and 1 <= len(attributes) <= 8 and
            all(type(x) is str and ID.fullmatch(x) for x in attributes) and
            len(set(attributes)) == len(attributes))
    universe = (1 << len(attributes)) - 1
    fds = value["fds"]
    require(type(fds) is list and len(fds) <= 32)
    for pair in fds:
        require(type(pair) is list and len(pair) == 2 and
                integer(pair[0], 0, universe) and integer(pair[1], 1, universe) and
                pair[1].bit_count() == 1 and not pair[0] & pair[1], "fd")
    require(fds == [list(x) for x in sorted(set(map(tuple, fds)))], "noncanonical-fds")
    task(value["task"])
    if len(canonical(value).encode("utf-8")) > 65536:
        raise ResourceLimit("seed-bytes")
    return value


def answer(value, exercise):
    value = bounded(value)
    require(type(value) is dict and value.get("mode") == exercise["task"]["mode"], "mode")
    universe = (1 << len(exercise["attributes"])) - 1
    if value["mode"] == "classify":
        require(fields(value, ["mode", "normal_form", "witness"]) and
                value["normal_form"] in FORMS)
        witness = value["witness"]
        require(witness is None or (type(witness) is list and len(witness) == 2 and
                integer(witness[0], 0, universe) and integer(witness[1], 1, universe) and
                witness[1].bit_count() == 1), "witness")
    else:
        require(fields(value, ["mode", "relations"]))
        relations = value["relations"]
        require(type(relations) is list and 1 <= len(relations) <= 8 and
                all(integer(x, 1, universe) for x in relations) and
                len(set(relations)) == len(relations), "relations")
        value["relations"] = sorted(relations)
    if len(canonical(value)) > 512:
        raise ResourceLimit("answer-bytes")
    return value


def schema(name):
    return json.loads((Path(__file__).parent / "schemas" / f"{name}-v1.json").read_text(encoding="utf-8"))


def compile_lesson(value):
    """Validate named author data and compile it; not a TeX authoring hook."""
    from jsonschema import Draft202012Validator
    value = bounded(value)
    if len(canonical(value).encode("utf-8")) > 65536:
        raise ResourceLimit("lesson-bytes")
    require(not list(Draft202012Validator(schema("lesson")).iter_errors(value)), "lesson-schema")
    # bool is a JSON Schema non-integer, but Python direct callers also get strict checking.
    require(type(value["format"]) is int and type(value["exercise"]["format"]) is int)
    exercise = value["exercise"]
    attributes = [row["id"] for row in exercise["attributes"]]
    require(len(set(attributes)) == len(attributes), "attribute-ids")
    index = {a: 1 << i for i, a in enumerate(attributes)}
    expanded, diagnostics = [], []
    total = 0
    for fd in exercise["fds"]:
        require(len(set(fd["lhs"])) == len(fd["lhs"]) and
                len(set(fd["rhs"])) == len(fd["rhs"]))
        require(all(x in index for x in fd["lhs"] + fd["rhs"]), "unknown-attribute")
        lhs = sum(index[a] for a in fd["lhs"])
        for a in fd["rhs"]:
            total += 1
            rhs = index[a]
            if lhs & rhs:
                diagnostics.append("trivial-fd")
            elif [lhs, rhs] in expanded:
                diagnostics.append("duplicate-fd")
            else:
                expanded.append([lhs, rhs])
    require(total <= 32, "expanded-fds")
    compiled = seed({"format": 1, "id": exercise["id"], "attributes": attributes,
                     "fds": sorted(expanded), "task": task(exercise["task"])})
    worked = answer(value["worked_answer"], compiled)
    return compiled, worked, diagnostics

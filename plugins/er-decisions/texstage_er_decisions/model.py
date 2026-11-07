# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent Python registration-profile validator and finite model oracle."""
import copy
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import re
import unicodedata

from jsonschema import Draft202012Validator

SEED_MAX = 64 * 1024
ANSWER_MAX = 1024
DATA_MAX = 6 * 1024
OUTCOME_MAX = 10 * 1024
IDENT = re.compile(r"[A-Za-z0-9_-]{1,24}\Z")


class InputError(ValueError):
    pass


class ResourceLimit(ValueError):
    pass


class DomainError(ValueError):
    def __init__(self, code, target):
        super().__init__(code)
        self.issue = {"code": code, "target": target, "occurrences": []}


def need(condition, code="invalid-source"):
    if not condition:
        raise InputError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def normalize(value):
    visits = 0
    def walk(item, depth):
        nonlocal visits
        visits += 1
        need(depth <= 16 and visits <= 8192, "json-complexity")
        if type(item) is str:
            need(not any(0xd800 <= ord(c) <= 0xdfff for c in item), "unicode-scalar")
            return unicodedata.normalize("NFC", item)
        if item is None or type(item) is bool:
            return item
        if type(item) is int:
            need(abs(item) <= 9007199254740991, "integer-range")
            return item
        if type(item) is list:
            return [walk(child, depth + 1) for child in item]
        if type(item) is dict:
            result = {}
            for key, child in item.items():
                need(type(key) is str, "object-key")
                need(not any(0xd800 <= ord(c) <= 0xdfff for c in key), "unicode-scalar")
                key = unicodedata.normalize("NFC", key)
                need(key not in result, "duplicate-key")
                result[key] = walk(child, depth + 1)
            return result
        raise InputError("json-type")
    return walk(value, 0)


def parse(text, limit=SEED_MAX):
    need(type(text) is str, "json-text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise InputError("unicode-scalar") from exc
    if size > limit:
        raise ResourceLimit("input-bytes")
    def pairs(items):
        result = {}
        for key, value in items:
            key = unicodedata.normalize("NFC", key)
            need(key not in result, "duplicate-key")
            result[key] = value
        return result
    def bad_number(_):
        raise InputError("integer-token")
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_float=bad_number, parse_constant=bad_number)
    except (ValueError, RecursionError) as exc:
        raise InputError("json-syntax") from exc
    return normalize(value)


@lru_cache(maxsize=4)
def schema(name):
    return json.loads((Path(__file__).parent / "schemas" / (name + "-v1.json")).read_text(encoding="utf-8"))


def shape(name, value):
    try:
        Draft202012Validator(schema(name)).validate(value)
    except Exception as exc:
        from jsonschema import ValidationError
        if not isinstance(exc, ValidationError):
            raise
        raise InputError(name + "-shape") from exc


def ident(value):
    return type(value) is str and IDENT.fullmatch(value) is not None


def ids(values):
    need(all(ident(v) for v in values) and len(set(values)) == len(values), "ids")


def answer(value):
    value = normalize(value)
    shape("answer", value)
    need(type(value["format"]) is int, "format")
    need(all(ident(v) for pair in value["choices"] for v in pair), "choice-id")
    if len(canonical(value)) > ANSWER_MAX:
        raise ResourceLimit("answer-bytes")
    value["choices"].sort()
    return value


def check_model(value):
    shape("model", value)
    ids(value["entities"])
    rel = value["relationship"]
    need(ident(rel["id"]) and rel["id"] not in value["entities"], "relationship-id")
    ids([r["id"] for r in rel["roles"]])
    need({r["entity"] for r in rel["roles"]} == set(value["entities"]), "role-entities")
    role_ids = {r["id"] for r in rel["roles"]}
    need("relationship" not in role_ids, "reserved-role")
    for role in rel["roles"]:
        need(type(role["min"]) is int and (type(role["max"]) is int or role["max"] == "many"), "bounds-type")
    ids([a["id"] for a in rel["attributes"]])
    need(all(a["owner"] in role_ids | {"relationship"} for a in rel["attributes"]), "attribute-owner")
    need(rel["form"] != "relationship" or rel["pair_unique"], "relationship-identity")
    return value


def compile_model(exercise, submission):
    submission = answer(submission)
    choices, decisions = {}, {d["id"]: d for d in exercise["decisions"]}
    for key, option in submission["choices"]:
        if key not in decisions:
            raise DomainError("unknown-decision", key)
        if key in choices:
            raise DomainError("duplicate-decision", key)
        choices[key] = option
    for key in sorted(decisions):
        if key not in choices:
            raise DomainError("missing-decision", key)
    model = copy.deepcopy(exercise["model"])
    rel = model["relationship"]
    for key in sorted(decisions):
        decision = decisions[key]
        option = next((o for o in decision["options"] if o["id"] == choices[key]), None)
        if option is None:
            raise DomainError("unknown-option", key)
        value = option["value"]
        if decision["kind"] == "role-bounds":
            next(r for r in rel["roles"] if r["id"] == decision["target"]).update(value)
        elif decision["kind"] == "attribute-owner":
            next(a for a in rel["attributes"] if a["id"] == decision["target"])["owner"] = value
        else:
            rel.update(value)
    return model


def semantic_seed(exercise):
    return {"format": exercise["format"], "id": exercise["id"], "model": exercise["model"],
            "decisions": exercise["decisions"],
            "requirements": [r["id"] for r in exercise["requirements"]],
            "snapshots": [{k: v for k, v in w.items() if k != "visibility"} for w in exercise["snapshots"]]}


def first_failure(model, snapshot):
    """Deterministic smallest witness: pair, role, then attribute constraints."""
    rel = model["relationship"]
    links = snapshot["links"]
    by_entity = {row["entity"]: row["ids"] for row in snapshot["entities"]}
    roles = {row["id"]: dict(row["roles"]) for row in links}
    values = {row["id"]: dict(row["values"]) for row in links}
    def issue(code, target, occurrences):
        return {"code": code, "target": target, "occurrences": occurrences}
    if rel["pair_unique"]:
        seen = {}
        for row in links:
            key = tuple(roles[row["id"]][r["id"]] for r in rel["roles"])
            if key in seen:
                return issue("pair-unique", rel["id"], [seen[key], row["id"]])
            seen[key] = row["id"]
    for role in rel["roles"]:
        for entity in by_entity[role["entity"]]:
            incident = [row["id"] for row in links if roles[row["id"]][role["id"]] == entity]
            if len(incident) < role["min"]:
                return issue("role-minimum", role["id"], [entity])
            if role["max"] != "many" and len(incident) > role["max"]:
                return issue("role-maximum", role["id"], incident[:2])
    for attribute in rel["attributes"]:
        if attribute["owner"] == "relationship":
            continue
        groups = {}
        for row in links:
            owner = roles[row["id"]][attribute["owner"]]
            value = values[row["id"]][attribute["id"]]
            if owner in groups and groups[owner][0] != value:
                return issue("attribute-dependency", attribute["id"], [groups[owner][1], row["id"]])
            groups.setdefault(owner, (value, row["id"]))
    return None


def source(value):
    value = normalize(value)
    shape("exercise", value)
    if len(canonical(value)) > SEED_MAX:
        raise ResourceLimit("seed-bytes")
    need(ident(value["id"]), "exercise-id")
    check_model(value["model"])
    rel = value["model"]["relationship"]
    value["model"]["entities"].sort()
    rel["roles"].sort(key=lambda r: r["id"])
    rel["attributes"].sort(key=lambda a: a["id"])
    ids([r["id"] for r in value["requirements"]])
    ids([d["id"] for d in value["decisions"]])
    ids([w["id"] for w in value["snapshots"]])
    requirement_ids = {r["id"] for r in value["requirements"]}
    role_ids = {r["id"] for r in rel["roles"]}
    attributes = {a["id"]: a for a in rel["attributes"]}
    used = set()
    for decision in value["decisions"]:
        ids([o["id"] for o in decision["options"]])
        target, kind = decision["target"], decision["kind"]
        need(ident(target) and (kind, target) not in used, "slot-ownership")
        used.add((kind, target))
        if kind == "role-bounds":
            need(target in role_ids, "role-target")
        elif kind == "attribute-owner":
            need(target in attributes, "attribute-target")
        else:
            need(target == rel["id"], "relationship-target")
        values_seen = set()
        for option in decision["options"]:
            payload = option["value"]
            if kind == "attribute-owner":
                need(payload in role_ids | {"relationship"}, "owner-option")
            elif kind == "relationship-form":
                need(payload["form"] != "relationship" or payload["pair_unique"], "form-option")
            else:
                need(type(payload["min"]) is int and (type(payload["max"]) is int or payload["max"] == "many"), "bounds-option")
            identity = canonical(payload)
            need(identity not in values_seen, "duplicate-option-meaning")
            values_seen.add(identity)
        decision["options"].sort(key=lambda o: o["id"])
    value["decisions"].sort(key=lambda d: d["id"])
    value["requirements"].sort(key=lambda r: r["id"])
    value["snapshots"].sort(key=lambda w: w["id"])
    need(any(w["visibility"] == "public" for w in value["snapshots"]), "public-example")
    for snapshot in value["snapshots"]:
        need(set(snapshot["requirements"]) <= requirement_ids, "witness-requirements")
        snapshot["requirements"].sort()
        ids([e["entity"] for e in snapshot["entities"]])
        need({e["entity"] for e in snapshot["entities"]} == set(value["model"]["entities"]), "snapshot-entities")
        count = len(snapshot["links"])
        entity_sets = {}
        for entity in snapshot["entities"]:
            ids(entity["ids"])
            entity["ids"].sort()
            count += len(entity["ids"])
            entity_sets[entity["entity"]] = set(entity["ids"])
        need(count <= 32, "snapshot-occurrences")
        ids([row["id"] for row in snapshot["links"]])
        snapshot["entities"].sort(key=lambda e: e["entity"])
        snapshot["links"].sort(key=lambda row: row["id"])
        for row in snapshot["links"]:
            ids([p[0] for p in row["roles"]])
            ids([p[0] for p in row["values"]])
            need(set(dict(row["roles"])) == role_ids and set(dict(row["values"])) == set(attributes), "observation-fields")
            for role in rel["roles"]:
                need(dict(row["roles"])[role["id"]] in entity_sets[role["entity"]], "dangling-observation")
            for key, scalar in row["values"]:
                wanted = {"int": int, "bool": bool, "text": str}[attributes[key]["type"]]
                need(type(scalar) is wanted, "attribute-type")
            row["roles"].sort()
            row["values"].sort()
    # Validate bounded compositions; authored choices never produce dangling models.
    for options in itertools.product(*(d["options"] for d in value["decisions"])):
        choice = {"format": 1, "choices": [[d["id"], o["id"]] for d, o in zip(value["decisions"], options)]}
        check_model(compile_model(value, choice))
    normalized_worked = []
    for worked in value["worked_answers"]:
        worked = answer(worked)
        try:
            candidate = compile_model(value, worked)
        except DomainError as exc:
            raise InputError("worked-answer") from exc
        need(all((first_failure(candidate, w) is None) == (w["expected"] == "allow") for w in value["snapshots"]),
             "worked-answer-contradicts-witness")
        normalized_worked.append(worked)
    need(len({canonical(a) for a in normalized_worked}) == len(normalized_worked), "duplicate-worked")
    value["worked_answers"] = sorted(normalized_worked, key=canonical)
    return value


def analyze(exercise, submission):
    submission = answer(submission)
    data = {"format": 1, "exercise_digest": digest(semantic_seed(exercise)),
            "answer_digest": digest(["er-answer-v1", submission]),
            "model_valid": True, "structural_issues": [], "checks": [], "unresolved": []}
    try:
        model = compile_model(exercise, submission)
    except DomainError as exc:
        data["model_valid"] = False
        data["structural_issues"] = [exc.issue]
    else:
        for snapshot in exercise["snapshots"]:
            reason = first_failure(model, snapshot)
            data["checks"].append({"id": snapshot["id"], "expected": snapshot["expected"],
                                   "admits": reason is None, "reason": reason})
    if len(canonical(data)) > DATA_MAX:
        raise ResourceLimit("facts-bytes")
    return data

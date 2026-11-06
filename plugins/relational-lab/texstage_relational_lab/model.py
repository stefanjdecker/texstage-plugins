# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent Python specification model; no host, browser or session state."""
from dataclasses import dataclass
import copy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
OPS = ("rel", "select", "project", "rename", "product", "join", "union", "difference")
RULES = ("split-select", "push-select-left", "push-select-right", "product-to-join", "collapse-project")
CHILDREN = {"rel": (), "select": (1,), "project": (1,), "rename": (1,),
            "product": (1, 2), "join": (1, 2), "union": (1, 2), "difference": (1, 2)}
VALIDATORS = {name: Draft202012Validator(json.loads((ROOT / "schemas" / (name + "-v1.json")).read_text()))
              for name in ("exercise", "answer", "analysis-result")}


class InputError(ValueError):
    """Malformed source/answer, as opposed to a well-formed invalid query."""


class DomainError(ValueError):
    def __init__(self, reason, node=-1, step=-1):
        super().__init__(reason)
        self.reason, self.node, self.step = reason, node, step


class ResourceLimit(ValueError):
    """Operational refusal, not a mathematical counterexample."""


@dataclass
class Budget:
    remaining: int = 100000

    def charge(self, amount=1):
        self.remaining -= amount
        if self.remaining < 0:
            raise ResourceLimit("work-limit")


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def _normalize(value, depth=0, counter=None):
    counter = [0] if counter is None else counter
    counter[0] += 1
    if depth > 16 or counter[0] > 8192:
        raise InputError("json-depth")
    if type(value) is str:
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise InputError("unpaired-surrogate")
        return unicodedata.normalize("NFC", value)
    if type(value) is int and abs(value) > 9007199254740991:
        raise InputError("unsafe-integer")
    if type(value) in (bool, int) or value is None:
        return value
    if type(value) is list:
        return [_normalize(v, depth + 1, counter) for v in value]
    if type(value) is dict and all(type(k) is str for k in value):
        # Keys are identifiers/contract fields and must already be canonical.
        return {k: _normalize(v, depth + 1, counter) for k, v in value.items()}
    raise InputError("json-type")


def parse(text, limit=65536):
    if type(text) is not str:
        raise InputError("json-text")
    try:
        if len(text.encode("utf-8")) > limit:
            raise ResourceLimit("input-bytes")
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise InputError("duplicate-key")
                result[key] = value
            return result
        def bad_number(_):
            raise InputError("integer-token-required")
        def integer(token):
            if len(token) > 17 or abs(value := int(token)) > 9007199254740991:
                raise InputError("unsafe-integer")
            return value
        return _normalize(json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                                     parse_float=bad_number, parse_constant=bad_number))
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise InputError("json-syntax") from error


def _shape(name, value):
    if not VALIDATORS[name].is_valid(value):
        raise InputError(name + "-shape")


def _ident(value):
    return type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,11}", value) is not None


def _header(columns):
    if not all(_ident(name) and kind in ("int", "text", "bool") for name, kind in columns):
        raise InputError("header")
    if len({name for name, _ in columns}) != len(columns):
        raise InputError("duplicate-header")
    return tuple(sorted(map(tuple, columns)))


def _scalar(value):
    kind = {int: "int", str: "text", bool: "bool"}.get(type(value))
    if kind is None or kind == "int" and abs(value) > 1000000 or kind == "text" and len(value) > 24:
        raise InputError("literal")
    return kind


def answer(value):
    value = _normalize(copy.deepcopy(value))
    _shape("answer", value)
    if len(canonical(value)) > 1800:
        raise ResourceLimit("answer-bytes")
    if value["mode"] == "construct":
        for node in value["tree"]:
            identifiers = [node[1]] if node[0] == "rel" else node[2] if node[0] == "project" else (
                [n for pair in node[2] for n in pair] if node[0] == "rename" else [])
            if not all(_ident(n) for n in identifiers):
                raise InputError("identifier")
            if node[0] in ("join", "select"):
                for atom in node[-1]:
                    for kind, term in atom[1:]:
                        if kind == "a" and not _ident(term):
                            raise InputError("identifier")
                        if kind == "v":
                            _scalar(term)
    return value


def infer(tree, schemas, allowed=OPS):
    answer({"mode": "construct", "tree": tree})
    parents, headers, depths = [0] * len(tree), [], []
    for index, node in enumerate(tree):
        def fail(reason):
            raise DomainError(reason, index)
        op = node[0]
        if op not in allowed:
            fail("operator-not-allowed")
        children = [node[p] for p in CHILDREN[op]]
        if any(child >= index for child in children):
            fail("child-index")
        for child in children:
            parents[child] += 1
        depth = 1 + max((depths[c] for c in children), default=0)
        if depth > 8:
            fail("tree-depth")
        depths.append(depth)
        if op == "rel":
            if node[1] not in schemas:
                fail("unknown-relation")
            header = _header(schemas[node[1]])
        else:
            left = dict(headers[children[0]])
            if op == "project":
                if not set(node[2]) <= left.keys():
                    fail("unknown-attribute")
                header = tuple(sorted((n, left[n]) for n in node[2]))
            elif op == "rename":
                mapping = dict(node[2])
                if len(mapping) != len(node[2]):
                    fail("duplicate-attribute")
                if not mapping.keys() <= left.keys():
                    fail("unknown-attribute")
                header = tuple(sorted((mapping.get(n, n), t) for n, t in left.items()))
                if len({n for n, _ in header}) != len(header):
                    fail("attribute-collision")
            elif op == "select":
                header = headers[children[0]]
            else:
                right = dict(headers[children[1]])
                if op in ("union", "difference"):
                    if left != right:
                        fail("incompatible-headers")
                    header = headers[children[0]]
                else:
                    if left.keys() & right.keys():
                        fail("attribute-collision")
                    header = tuple(sorted((left | right).items()))
            if len(header) > 12:
                fail("width-limit")
            if op in ("select", "join"):
                names = dict(header)
                for comparison, a, b in node[-1]:
                    types = []
                    for kind, value in (a, b):
                        if kind == "a" and value not in names:
                            fail("unknown-attribute")
                        types.append(names[value] if kind == "a" else _scalar(value))
                    if types[0] != types[1]:
                        fail("type-mismatch")
                    if comparison not in ("eq", "ne") and types[0] != "int":
                        fail("unordered-type")
        headers.append(header)
    if parents[-1] != 0 or any(p != 1 for p in parents[:-1]):
        raise DomainError("not-a-tree")
    order = []
    def visit(index):
        for position in CHILDREN[tree[index][0]]:
            visit(tree[index][position])
        order.append(index)
    visit(len(tree) - 1)
    if order != list(range(len(tree))):
        raise DomainError("postorder")
    return headers


@dataclass(frozen=True)
class Relation:
    header: tuple
    rows: frozenset

    def data(self):
        return {"header": [list(c) for c in self.header], "rows": [list(r) for r in sorted(self.rows)]}

    def facts(self, identity):
        data = self.data()
        return {"id": identity, "header": digest(["header-v1", data["header"]]),
                "relation": digest(["relation-v1", data["header"], data["rows"]])}


def source(value):
    value = _normalize(copy.deepcopy(value))
    _shape("exercise", value)
    if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > 65536:
        raise ResourceLimit("seed-bytes")
    if not _ident(value["id"]):
        raise InputError("exercise-id")
    for columns in value["relations"].values():
        _header(columns)
    ids = [i["id"] for i in value["instances"]]
    if len(set(ids)) != len(ids) or not all(_ident(i) for i in ids):
        raise InputError("instance-id")
    if sum(i["visibility"] == "public" for i in value["instances"]) != 1:
        raise InputError("public-instance")
    for instance in value["instances"]:
        if instance["tables"].keys() != value["relations"].keys():
            raise InputError("instance-tables")
        for name, columns in value["relations"].items():
            for row in instance["tables"][name]:
                if len(row) != len(columns) or any(_scalar(v) != t for v, (_, t) in zip(row, columns)):
                    raise InputError("row-type")
    tree = value.get("reference_tree", value.get("baseline_tree"))
    try:
        headers = infer(tree, value["relations"], value["task"]["allowed_operators"])
        if value["task"]["mode"] == "construct":
            if headers[-1] != _header(value["task"]["expected_header"]):
                raise InputError("reference-header")
            if value["initial_tree"]:
                infer(value["initial_tree"], value["relations"], value["task"]["allowed_operators"])
    except DomainError as error:
        raise InputError("invalid-reference:" + error.reason) from error
    return value


def _base(schemas, tables, name):
    columns = schemas[name]
    header = _header(columns)
    indices = [next(i for i, c in enumerate(columns) if c[0] == n) for n, _ in header]
    return Relation(header, frozenset(tuple(row[i] for i in indices) for row in tables[name]))


def source_diagnostics(exercise):
    """Author-only diagnostics; duplicate tuples have set semantics."""
    return [{"instance": instance["id"], "relation": name, "duplicate_rows": duplicates}
            for instance in exercise["instances"] for name, rows in instance["tables"].items()
            if (duplicates := len(rows) - len(_base(exercise["relations"], instance["tables"], name).rows))]


def source_identity(exercise):
    relations = {name: list(map(list, _header(columns))) for name, columns in exercise["relations"].items()}
    instances = [{"id": i["id"], "visibility": i["visibility"],
                  "tables": {n: _base(exercise["relations"], i["tables"], n).data()["rows"] for n in relations}}
                 for i in sorted(exercise["instances"], key=lambda i: i["id"])]
    task = {k: v for k, v in exercise["task"].items() if k != "feedback"}
    for key in ("allowed_operators", "allowed_rules"):
        if key in task:
            task[key] = sorted(task[key])
    if "expected_header" in task:
        task["expected_header"] = list(map(list, _header(task["expected_header"])))
    policy = {k: exercise[k] for k in ("reference_tree", "baseline_tree") if k in exercise}
    return digest(["relational-exercise-v1", {"id": exercise["id"], "relations": relations,
                    "instances": instances, "task": task, **policy}])


def evaluate_tree(exercise, tree, instance, budget=None):
    budget = budget if budget is not None else Budget()
    headers = infer(tree, exercise["relations"], exercise["task"]["allowed_operators"])
    results, trace, cells = [], [], 0
    def records(relation):
        for row in sorted(relation.rows):
            budget.charge()
            yield dict(zip((n for n, _ in relation.header), row))
    def predicate(atoms, row):
        for comparison, a, b in atoms:
            budget.charge()
            x, y = (row[t[1]] if t[0] == "a" else t[1] for t in (a, b))
            if not {"eq": lambda: x == y, "ne": lambda: x != y, "lt": lambda: x < y,
                    "le": lambda: x <= y, "gt": lambda: x > y, "ge": lambda: x >= y}[comparison]():
                return False
        return True
    for index, node in enumerate(tree):
        op, header = node[0], headers[index]
        if op == "rel":
            result = _base(exercise["relations"], instance["tables"], node[1])
            budget.charge(len(instance["tables"][node[1]]))
        else:
            left = results[node[1]]
            rows = set()
            def add(row):
                rows.add(tuple(row[n] for n, _ in header))
                if len(rows) > 256:
                    raise ResourceLimit("row-limit")
            if op in ("select", "project", "rename"):
                for row in records(left):
                    if op == "select" and not predicate(node[2], row):
                        continue
                    if op == "rename":
                        mapping = dict(node[2])
                        row = {mapping.get(n, n): v for n, v in row.items()}
                    add(row)
            else:
                right = results[node[2]]
                if op in ("join", "product"):
                    # Charge each input once, then each candidate pair; no full product.
                    a, b = list(records(left)), list(records(right))
                    for x in a:
                        for y in b:
                            budget.charge()
                            row = x | y
                            if op == "product" or predicate(node[3], row):
                                add(row)
                else:
                    a, b = list(records(left)), list(records(right))
                    candidates = left.rows | right.rows if op == "union" else left.rows - right.rows
                    for row in candidates:
                        add(dict(zip((n for n, _ in header), row)))
            result = Relation(header, frozenset(rows))
            cells += len(result.rows) * len(header)
        results.append(result)
        trace.append([index, len(result.rows), len(header)])
    return results[-1], {"trace": trace, "cells": cells}


def rewrite_tree(exercise, tree, step):
    headers = infer(tree, exercise["relations"], exercise["task"]["allowed_operators"])
    selected = len(tree) - 1
    for child in step["path"]:
        positions = CHILDREN[tree[selected][0]]
        if child >= len(positions):
            raise DomainError("rule-path")
        selected = tree[selected][positions[child]]
    rule, node = step["rule"], tree[selected]
    if rule not in exercise["task"]["allowed_rules"]:
        raise DomainError("rule-not-allowed", selected)
    def nest(index):
        node = copy.deepcopy(tree[index])
        for p in CHILDREN[node[0]]:
            node[p] = nest(node[p])
        return node
    target = nest(selected)
    if rule == "split-select" and node[0] == "select" and len(node[2]) > 1:
        replacement = ["select", ["select", target[1], target[2][1:]], target[2][:1]]
    elif rule in ("push-select-left", "push-select-right") and node[0] == "select" and target[1][0] in ("join", "product"):
        side = 1 if rule.endswith("left") else 2
        binary = tree[node[1]]
        names = {n for atom in node[2] for kind, n in atom[1:] if kind == "a"}
        if not names <= dict(headers[binary[side]]).keys():
            raise DomainError("attribute-side-condition", selected)
        replacement = target[1]
        replacement[side] = ["select", replacement[side], target[2]]
    elif rule == "product-to-join" and node[0] == "select" and target[1][0] == "product":
        replacement = ["join", target[1][1], target[1][2], target[2]]
    elif rule == "collapse-project" and node[0] == "project" and target[1][0] == "project":
        if not set(node[2]) <= set(target[1][2]):
            raise DomainError("projection-side-condition", selected)
        replacement = ["project", target[1][1], target[2]]
    else:
        raise DomainError("rule-not-applicable", selected)
    root = nest(len(tree) - 1)
    parent = None
    cursor = root
    for child in step["path"]:
        parent = cursor
        position = CHILDREN[cursor[0]][child]
        cursor = cursor[position]
    if parent is None:
        root = replacement
    else:
        parent[position] = replacement
    result = []
    def flatten(node):
        row = copy.deepcopy(node)
        for p in CHILDREN[node[0]]:
            row[p] = flatten(node[p])
        result.append(row)
        return len(result) - 1
    flatten(root)
    try:
        infer(result, exercise["relations"], exercise["task"]["allowed_operators"])
    except InputError as error:
        raise ResourceLimit("derived-tree") from error
    return result


def analyze(exercise, submission, budget=None):
    """Return facts, never a construction grade; callers supply a validated source."""
    submission = answer(submission)
    budget = budget if budget is not None else Budget()
    base = {"format": "relational-analysis-v1", "exercise": source_identity(exercise),
            "answer": digest(["relational-answer-v1", submission]), "mode": exercise["task"]["mode"]}
    step_index = -1
    try:
        if submission["mode"] != base["mode"]:
            raise DomainError("wrong-mode")
        tree = submission.get("tree", exercise.get("baseline_tree"))
        baseline_cells = None
        sequence = [tree]
        if base["mode"] == "rewrite":
            for step_index, step in enumerate(submission["steps"]):
                tree = rewrite_tree(exercise, tree, step)
                sequence.append(tree)
        for tree_index, tree in enumerate(sequence):
            fixtures, public = [], None
            for instance in sorted(exercise["instances"], key=lambda i: i["id"]):
                relation, stats = evaluate_tree(exercise, tree, instance, budget)
                fixtures.append(relation.facts(instance["id"]))
                if instance["visibility"] == "public":
                    public = stats
            if tree_index == 0:
                baseline_cells = public["cells"]
        result = base | {"valid": True, "fixtures": fixtures, "public": public}
        if base["mode"] == "rewrite":
            result["proof"] = {"verified": True, "steps": len(submission["steps"]), "tree": tree,
                               "baseline_cells": baseline_cells, "improved": public["cells"] < baseline_cells}
    except DomainError as error:
        result = base | {"valid": False, "reason": error.reason, "node": error.node, "step": step_index}
    _shape("analysis-result", result)
    if len(canonical(result)) > 8192:
        raise ResourceLimit("data-bytes")
    return result

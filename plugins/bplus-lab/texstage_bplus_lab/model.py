# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent nested-page model for the bounded B+ operations contract."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
import hashlib
import json

MAX_WORK = 20000


class InputError(ValueError):
    pass


class ResourceLimit(ValueError):
    pass


class Budget:
    def __init__(self, limit=MAX_WORK):
        if type(limit) is not int or not 0 <= limit <= MAX_WORK:
            raise ValueError("Invalid work limit")
        self.remaining = limit

    def charge(self, amount=1):
        self.remaining -= amount
        if self.remaining < 0:
            raise ResourceLimit("work")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def need(condition, reason="input"):
    if not condition:
        raise InputError(reason)


def fields(value, names):
    return type(value) is dict and set(value) == set(names)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def array(value, low, high, predicate=lambda x: True):
    return type(value) is list and low <= len(value) <= high and all(predicate(x) for x in value)


def parse(text, byte_limit=32768):
    need(type(text) is str)
    if len(text.encode("utf-8", errors="surrogatepass")) > byte_limit:
        raise ResourceLimit("input-bytes")

    def reject(*_):
        raise InputError("Only finite integer JSON tokens are supported")

    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, "duplicate-json-key")
            out[key] = value
        return out

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise InputError("Invalid bounded JSON") from exc
    count = 0

    def walk(item, depth):
        nonlocal count
        count += 1
        need(depth <= 16 and count <= 8192, "json-complexity")
        if type(item) is str:
            need(all(not 0xD800 <= ord(c) <= 0xDFFF for c in item), "surrogate")
        elif type(item) is dict:
            for key, child in item.items():
                walk(key, depth + 1)
                walk(child, depth + 1)
        elif type(item) is list:
            for child in item:
                walk(child, depth + 1)
        elif type(item) is int:
            need(abs(item) <= 9007199254740991, "integer-range")
    walk(value, 0)
    return value


@dataclass
class Page:
    id: int
    entries: list[int] = field(default_factory=list)
    children: list[Page] | None = None

    @property
    def leaf(self):
        return self.children is None

    @property
    def items(self):
        return self.entries if self.leaf else self.children


def read_tree(tree, leaf_capacity, internal_capacity, budget, *, initial=True, pending=None):
    need(fields(tree, ("root", "nodes")) and integer(tree["root"], 0, 63))
    need(array(tree["nodes"], 1, 31 if initial else 35))
    pages = {}
    for node in tree["nodes"]:
        need(type(node) is dict and integer(node.get("id"), 0, 63))
        need(node["id"] not in pages, "duplicate-page")
        pages[node["id"]] = node
    need(list(pages) == sorted(pages), "page-order")
    seen, leaves, depths, preorder, violations = set(), [], set(), [], []

    def descend(page_id, depth):
        need(integer(page_id, 0, 63) and page_id in pages, "missing-page")
        need(page_id not in seen, "repeated-page")
        need(depth <= (2 if initial else 3), "height")
        seen.add(page_id)
        preorder.append(page_id)
        raw = pages[page_id]
        leaf = raw.get("kind") == "leaf"
        need(fields(raw, ("id", "kind", "keys", "next") if leaf else ("id", "kind", "keys", "children")))
        need(raw["kind"] in ("leaf", "internal"))
        keys = raw["keys"]
        need(array(keys, 0, 7, lambda k: integer(k, -9999, 9999)), "keys")
        budget.charge(1 + len(keys))
        need(all(a < b for a, b in zip(keys, keys[1:])), "key-order")
        items = keys if leaf else raw["children"]
        need(array(items, 0, 7))
        if not leaf:
            budget.charge(len(items))
        cap = leaf_capacity if leaf else internal_capacity
        minimum = (0 if leaf else 2) if page_id == tree["root"] else (cap + 1) // 2
        size = len(items)
        if not minimum <= size <= cap:
            allowed = size == cap + 1 or (page_id != tree["root"] and size == minimum - 1)
            need(not initial and page_id == pending and allowed, "occupancy")
            violations.append(page_id)
        if leaf:
            need(raw["next"] is None or integer(raw["next"], 0, 63), "leaf-link")
            leaves.append(page_id)
            depths.add(depth)
            return Page(page_id, list(keys)), list(keys)
        need(len(keys) == len(items) - 1 and len(items) >= 1, "separator-count")
        children_and_keys = [descend(child, depth + 1) for child in items]
        children, groups = zip(*children_and_keys, strict=True)
        need(all(groups), "empty-subtree")
        need(all(a[-1] < b[0] for a, b in zip(groups, groups[1:])), "child-range")
        need(keys == [g[0] for g in groups[1:]], "separator-minimum")
        return Page(page_id, children=list(children)), [k for group in groups for k in group]

    root, keys = descend(tree["root"], 0)
    need(seen == set(pages), "orphan")
    need(len(depths) == 1, "leaf-depth")
    need(len(keys) <= (40 if initial else 41), "key-count")
    need(violations == ([] if pending is None else [pending]), "pending-occupancy")
    for i, page_id in enumerate(leaves):
        need(pages[page_id]["next"] == (leaves[i + 1] if i + 1 < len(leaves) else None), "leaf-chain")
    if initial:
        need(preorder == list(range(len(pages))) and tree["root"] == 0, "preorder-ids")
    return root, {"keys": keys, "height": next(iter(depths)), "leaves": leaves}


def source_for(value, budget=None):
    budget = budget or Budget()
    need(fields(value, ("format", "semantics", "leaf_capacity", "internal_capacity", "tree", "task")))
    need(type(value["format"]) is int and value["format"] == 1 and value["semantics"] == "bplus-operations-v1")
    need(integer(value["leaf_capacity"], 3, 6) and integer(value["internal_capacity"], 3, 6))
    task = value["task"]
    need(type(task) is dict)
    if task.get("kind") == "range":
        need(fields(task, ("kind", "lower", "upper")) and
             integer(task["lower"], -9999, 9999) and integer(task["upper"], -9999, 9999) and
             task["lower"] <= task["upper"])
    else:
        need(fields(task, ("kind", "key")) and task["kind"] in ("lookup", "insert", "delete") and
             integer(task["key"], -9999, 9999))
    read_tree(value["tree"], value["leaf_capacity"], value["internal_capacity"], budget)
    if len(canonical(value)) > 12288:
        raise ResourceLimit("seed-bytes")
    return value


def answer_for(seed, value):
    kind = seed["task"]["kind"]
    names = ("format", "path", "repairs", "separators", "height") if kind in ("insert", "delete") else (
        ("format", "path", "keys", "leaves") if kind == "range" else ("format", "path", "keys"))
    need(fields(value, names))
    need(type(value["format"]) is int and value["format"] == 1)
    need(array(value["path"], 1, 3, lambda n: integer(n, 0, 63)))
    if kind in ("lookup", "range"):
        need(array(value["keys"], 0, 40 if kind == "range" else 1, lambda k: integer(k, -9999, 9999)))
        if kind == "range":
            need(array(value["leaves"], 1, 20, lambda n: integer(n, 0, 63)))
    else:
        need(integer(value["height"], 0, 3) and array(value["repairs"], 0, 3))
        need(array(value["separators"], 0, 10))
        for record in value["separators"]:
            need(fields(record, ("node", "keys")) and integer(record["node"], 0, 63) and
                 array(record["keys"], 1, 5, lambda k: integer(k, -9999, 9999)))
        for repair in value["repairs"]:
            need(type(repair) is dict)
            if repair.get("op") == "split":
                need(fields(repair, ("op", "node", "left_count", "separator")) and
                     integer(repair["left_count"], 1, 6) and integer(repair["separator"], -9999, 9999))
            else:
                need(fields(repair, ("op", "node", "sibling")) and repair["op"] in ("borrow", "merge") and
                     integer(repair["sibling"], 0, 63))
            need(integer(repair["node"], 0, 63))
    if len(canonical(value)) > 1800:
        raise ResourceLimit("answer-bytes")
    return value


def minimum(page, budget):
    while not page.leaf:
        budget.charge()
        page = page.children[0]
    budget.charge()
    return page.entries[0]


def flatten(root, budget):
    leaves, raw = [], []

    def visit(page):
        budget.charge(1 + len(page.items))
        if page.leaf:
            leaves.append(page.id)
            raw.append({"id": page.id, "kind": "leaf", "keys": list(page.entries), "next": None})
        else:
            raw.append({"id": page.id, "kind": "internal",
                        "keys": [minimum(c, budget) for c in page.children[1:]],
                        "children": [c.id for c in page.children]})
            for child in page.children:
                visit(child)
    visit(root)
    by_id = {node["id"]: node for node in raw}
    for left, right in zip(leaves, leaves[1:]):
        by_id[left]["next"] = right
    return {"root": root.id, "nodes": sorted(raw, key=lambda n: n["id"])}


def path_for(root, key, budget):
    route, page = [], root
    while True:
        budget.charge(1 + len(page.items))
        route.append(page.id)
        if page.leaf:
            return route, page
        separators = [minimum(child, budget) for child in page.children[1:]]
        page = page.children[bisect_right(separators, key)]


def family(root, page, budget):
    if root is page:
        return None, None
    todo = [root]
    while todo:
        current = todo.pop()
        budget.charge(1 + len(current.items))
        if not current.leaf:
            for i, child in enumerate(current.children):
                if child is page:
                    return current, i
            todo.extend(current.children)
    raise RuntimeError("Replay page is unreachable")


def fault(data, state, reason, checked, at, node):
    return data | {"replay": {"state": state, "reason": reason, "checked_repairs": checked, "at": at, "node": node}}


def mismatch(actual, expected):
    return next((i for i in range(max(len(actual), len(expected)))
                 if i >= len(actual) or i >= len(expected) or actual[i] != expected[i]), None)


def analyze(seed, answer, budget=None):
    budget = budget or Budget()
    source_for(seed, budget)
    answer_for(seed, answer)
    root, before = read_tree(seed["tree"], seed["leaf_capacity"], seed["internal_capacity"], budget)
    task, kind = seed["task"], seed["task"]["kind"]
    key = task["lower"] if kind == "range" else task["key"]
    expected_path, target = path_for(root, key, budget)
    data = {"format": 1, "exercise": digest(seed), "answer": digest(answer), "operation": kind}
    wrong = mismatch(answer["path"], expected_path)
    if wrong is not None:
        return fault(data, "invalid", "wrong-path", 0, wrong, expected_path[wrong] if wrong < len(expected_path) else None)
    claims = {"path": True, "keys": None, "separators": None, "height": None}
    if kind in ("lookup", "range"):
        nodes = {n["id"]: n for n in seed["tree"]["nodes"]}
        scan, output = [], []
        current = target.id
        while True:
            node = nodes[current]
            budget.charge(1 + len(node["keys"]))
            scan.append(current)
            output.extend(k for k in node["keys"] if (k == key if kind == "lookup" else key <= k <= task["upper"]))
            if kind == "lookup" or not node["keys"] or node["keys"][-1] >= task["upper"] or node["next"] is None:
                break
            current = node["next"]
        if kind == "range":
            wrong = mismatch(answer["leaves"], scan)
            if wrong is not None:
                return fault(data, "invalid", "wrong-scan", 0, wrong, scan[wrong] if wrong < len(scan) else None)
        claims["keys"] = answer["keys"] == output
        return data | {"replay": {"state": "complete", "checked_repairs": 0}, "claims": claims,
                       "read": {"path": expected_path, "leaves": scan, "keys": output,
                                "page_visits": len(expected_path) + len(scan) - 1}}

    cap = lambda p: seed["leaf_capacity" if p.leaf else "internal_capacity"]
    lower = lambda p: (cap(p) + 1) // 2
    pending = None
    budget.charge(1 + len(target.entries))
    if kind == "insert" and key not in target.entries:
        target.entries.append(key)
        target.entries.sort()
        if len(target.entries) > cap(target):
            pending = target
    elif kind == "delete" and key in target.entries:
        target.entries.remove(key)
        if target is not root and len(target.entries) < lower(target):
            pending = target
    expected_keys = sorted(set(before["keys"]) | {key}) if kind == "insert" else [k for k in before["keys"] if k != key]
    next_id = max(n["id"] for n in seed["tree"]["nodes"]) + 1
    counts = {"splits": 0, "borrows": 0, "merges": 0}

    def check_invariants():
        flat = flatten(root, budget)
        try:
            _, state = read_tree(flat, seed["leaf_capacity"], seed["internal_capacity"], budget,
                                 initial=False, pending=pending.id if pending else None)
            need(state["keys"] == expected_keys, "key-conservation")
        except InputError as exc:
            raise RuntimeError("Replay invariant: " + str(exc)) from exc
        return flat, state

    check_invariants()
    for i, repair in enumerate(answer["repairs"]):
        budget.charge()
        if pending is None:
            return fault(data, "invalid", "extra-repair", i, i, repair["node"])
        node = pending
        if repair["node"] != node.id:
            return fault(data, "invalid", "wrong-pending-node", i, i, node.id)
        parent, at = family(root, node, budget)
        op = repair["op"]
        reason = {"split": "illegal-split", "borrow": "illegal-donor", "merge": "illegal-merge"}[op]
        if op == "split":
            cut = repair["left_count"]
            length = len(node.items)
            if length != cap(node) + 1 or not lower(node) <= cut <= cap(node) or not lower(node) <= length - cut <= cap(node):
                return fault(data, "invalid", reason, i, i, node.id)
            boundary = node.entries[cut] if node.leaf else minimum(node.children[cut], budget)
            if repair["separator"] != boundary:
                return fault(data, "invalid", "wrong-separator", i, i, node.id)
            budget.charge(length)
            if node.leaf:
                right = Page(next_id, node.entries[cut:])
                node.entries = node.entries[:cut]
            else:
                right = Page(next_id, children=node.children[cut:])
                node.children = node.children[:cut]
            next_id += 1
            if parent is None:
                root = Page(next_id, children=[node, right])
                next_id += 1
                pending = None
            else:
                parent.children.insert(at + 1, right)
                pending = parent if len(parent.children) > cap(parent) else None
            counts["splits"] += 1
        else:
            if parent is None or len(node.items) != lower(node) - 1:
                return fault(data, "invalid", reason, i, i, node.id)
            siblings = [(j, p) for j, p in enumerate(parent.children)
                        if abs(j - at) == 1 and p.id == repair["sibling"]]
            if not siblings:
                return fault(data, "invalid", reason, i, i, node.id)
            side, sibling = siblings[0]
            if op == "borrow":
                if len(sibling.items) <= lower(sibling):
                    return fault(data, "invalid", reason, i, i, node.id)
                budget.charge(1 + len(node.items) + len(sibling.items))
                if side < at:
                    node.items.insert(0, sibling.items.pop())
                else:
                    node.items.append(sibling.items.pop(0))
                pending = None
                counts["borrows"] += 1
            else:
                if len(node.items) + len(sibling.items) > cap(node):
                    return fault(data, "invalid", reason, i, i, node.id)
                left, right = (sibling, node) if side < at else (node, sibling)
                budget.charge(len(left.items) + len(right.items))
                left.items.extend(right.items)
                parent.children.remove(right)
                if parent is root and len(parent.children) == 1:
                    root = parent.children[0]
                    pending = None
                else:
                    pending = parent if parent is not root and len(parent.children) < lower(parent) else None
                counts["merges"] += 1
        check_invariants()
    if pending:
        return fault(data, "incomplete", "missing-repair", len(answer["repairs"]), len(answer["repairs"]), pending.id)
    final, state = check_invariants()
    expected_separators = [{"node": n["id"], "keys": n["keys"]} for n in final["nodes"] if n["kind"] == "internal"]
    claims["separators"] = answer["separators"] == expected_separators
    claims["height"] = answer["height"] == state["height"]
    return data | {"replay": {"state": "complete", "checked_repairs": len(answer["repairs"])}, "claims": claims,
                   "final": final, "metrics": {"height_before": before["height"], "height_after": state["height"],
                                             "leaf_count": len(state["leaves"]), **counts}}

# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Check finite B+ design snapshots and reads, not update-certificate replay.

Uses only the standard library. No package is built or imported, and no browser,
host schema, performance, or implementation conformance is established.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "design" / "bplus-tree"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def byte_count(value):
    return len(canonical(value).encode("ascii"))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate-json-key")
        result[key] = value
    return result


def read_json(path):
    def invalid_constant(value):
        raise ValueError("non-finite-json:" + value)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def inspect_tree(tree, leaf_capacity, internal_capacity, *, initial=False):
    require(type(leaf_capacity) is int and 3 <= leaf_capacity <= 6, "leaf-capacity")
    require(type(internal_capacity) is int and 3 <= internal_capacity <= 6, "internal-capacity")
    require(set(tree) == {"root", "nodes"} and type(tree["root"]) is int, "tree-shape")
    require(1 <= len(tree["nodes"]) <= (31 if initial else 35), "page-count")
    ids = [n["id"] for n in tree["nodes"]]
    require(all(type(n) is int and 0 <= n <= 63 for n in ids), "page-id")
    require(ids == sorted(set(ids)), "page-order")
    nodes = {n["id"]: n for n in tree["nodes"]}
    require(tree["root"] in nodes, "missing-root")
    seen, leaves, depths, preorder = set(), [], set(), []

    def visit(node_id, depth):
        require(type(node_id) is int and node_id in nodes, "unknown-child")
        require(node_id not in seen, "repeated-page")
        require(depth <= (2 if initial else 3), "height-limit")
        seen.add(node_id)
        preorder.append(node_id)
        node = nodes[node_id]
        require(node["kind"] in ("leaf", "internal"), "page-kind")
        keys = node["keys"]
        require(type(keys) is list and all(type(k) is int and -9999 <= k <= 9999 for k in keys),
                "integer-key")
        require(keys == sorted(set(keys)), "key-order")
        if node["kind"] == "leaf":
            require(set(node) == {"id", "kind", "keys", "next"}, "leaf-shape")
            require(node["next"] is None or type(node["next"]) is int, "next-id")
            minimum = 0 if node_id == tree["root"] else (leaf_capacity + 1) // 2
            require(minimum <= len(keys) <= leaf_capacity, "occupancy")
            leaves.append(node_id)
            depths.add(depth)
            return list(keys)
        require(set(node) == {"id", "kind", "keys", "children"}, "internal-shape")
        children = node["children"]
        require(type(children) is list, "child-list")
        minimum = 2 if node_id == tree["root"] else (internal_capacity + 1) // 2
        require(minimum <= len(children) <= internal_capacity, "occupancy")
        require(len(keys) == len(children) - 1, "separator-count")
        groups = [visit(child, depth + 1) for child in children]
        require(all(groups), "empty-subtree")
        require(all(a[-1] < b[0] for a, b in zip(groups, groups[1:])), "child-ranges")
        require(keys == [g[0] for g in groups[1:]], "separator-minimum")
        return [key for group in groups for key in group]

    keys = visit(tree["root"], 0)
    require(seen == set(nodes), "unreachable-page")
    require(len(depths) == 1, "leaf-depth")
    require(len(keys) <= (40 if initial else 41), "entry-count")
    require(keys == sorted(set(keys)), "entry-order")
    for index, node_id in enumerate(leaves):
        expected = leaves[index + 1] if index + 1 < len(leaves) else None
        require(nodes[node_id]["next"] == expected, "leaf-chain")
    if initial:
        require(ids == list(range(len(nodes))) and preorder == ids, "initial-preorder-ids")
    return {"keys": keys, "height": next(iter(depths)), "leaves": leaves, "nodes": nodes}


def lookup_path(tree, key):
    nodes = {n["id"]: n for n in tree["nodes"]}
    path, current = [], tree["root"]
    while True:
        path.append(current)
        node = nodes[current]
        if node["kind"] == "leaf":
            return path
        current = node["children"][bisect_right(node["keys"], key)]


def check_case(case, model):
    before = inspect_tree(model["tree"], model["leaf_capacity"], model["internal_capacity"], initial=True)
    answer, task = case["answer"], case["task"]
    lower = task["lower"] if task["kind"] == "range" else task["key"]
    expected_path = lookup_path(model["tree"], lower)
    require(answer["format"] == 1 and answer["path"] == expected_path, "answer-path")
    require(byte_count(answer) <= 1800, "answer-budget")
    if task["kind"] in ("lookup", "range"):
        if task["kind"] == "lookup":
            keys = [lower] if lower in before["keys"] else []
            visits = len(expected_path)
        else:
            require(task["lower"] <= task["upper"], "interval")
            scan, current = [], expected_path[-1]
            while True:
                scan.append(current)
                node = before["nodes"][current]
                if not node["keys"] or node["keys"][-1] >= task["upper"] or node["next"] is None:
                    break
                current = node["next"]
            require(answer["leaves"] == scan, "answer-scan")
            keys = [k for k in before["keys"] if task["lower"] <= k <= task["upper"]]
            visits = len(expected_path) + len(scan) - 1
        require(answer["keys"] == keys == case["expected"]["keys"], "read-keys")
        require(case["expected"]["page_visits"] == visits, "page-visits")
        return

    require(task["kind"] in ("insert", "delete"), "task-kind")
    after_tree = case["expected"]["tree"]
    after = inspect_tree(after_tree, model["leaf_capacity"], model["internal_capacity"])
    expected_keys = set(before["keys"])
    if task["kind"] == "insert":
        expected_keys.add(task["key"])
    else:
        expected_keys.discard(task["key"])
    require(after["keys"] == sorted(expected_keys), "operation-key-set")
    require(type(answer["height"]) is int and answer["height"] == after["height"] == case["expected"]["height"],
            "answer-height")
    separators = [{"node": n["id"], "keys": n["keys"]} for n in after_tree["nodes"] if n["kind"] == "internal"]
    require(answer["separators"] == separators and len(separators) <= 10, "answer-separators")
    require(len(answer["repairs"]) <= 3, "repair-count")
    for repair in answer["repairs"]:
        fields = {"op", "node", "left_count", "separator"} if repair["op"] == "split" else {"op", "node", "sibling"}
        require(repair["op"] in ("split", "borrow", "merge") and set(repair) == fields, "repair-shape")
        require(all(type(v) is int for k, v in repair.items() if k != "op"), "repair-integer")
    # Deliberately no repair execution here. B0/B1 must validate each certificate.


def encoding_probes():
    """Conservative shape encodings, deliberately NOT valid domain trees."""
    answer = {
        "format": 1, "path": [63] * 3,
        "repairs": [{"op": "split", "node": 63, "left_count": 6, "separator": -9999}] * 3,
        "separators": [{"node": 63, "keys": [-9999] * 5}] * 10, "height": 3,
    }
    final = {
        "root": 63,
        "nodes": [{"id": 63, "kind": "internal", "keys": [-9999] * 5, "children": [63] * 6}] * 35,
    }
    data = {
        "format": 1, "exercise": "f" * 64, "answer": "f" * 64, "operation": "insert",
        "replay": {"state": "complete", "checked_repairs": 3},
        "claims": {"path": True, "keys": None, "separators": True, "height": True},
        "final": final,
        "metrics": {"height_before": 2, "height_after": 3, "leaf_count": 21,
                    "splits": 3, "borrows": 3, "merges": 3},
    }
    result = {"status": "ok", "canonical": "bplus-v1:" + "f" * 64 + ":" + "f" * 64,
              "summary": {"kind": "text", "text": "x" * 160}, "data": data}
    actor = "\U0010ffff" * 256
    actor_key = hashlib.sha256(canonical(["bplus-actor-v1", actor]).encode("ascii")).hexdigest()
    slot = {
        "answer": canonical(answer), "version": 999999999, "phase": 999999999,
        "exercise": "f" * 64, "answer_identity": "f" * 64, "correlation": "f" * 64,
        "status": "pending", "feedback_reserve": "x" * 768,
    }
    values = {
        "conservative_answer_bytes": byte_count(answer),
        "conservative_typed_facts_bytes": byte_count(data),
        "conservative_complete_result_bytes": byte_count(result),
        "actor_slot_with_digest_and_feedback_reserve_bytes": byte_count({actor_key: slot}),
        "raw_non_bmp_actor_json_bytes": byte_count(actor),
        "proposed_max_state_bytes": 48 * 4096 + 16384,
        "note": "Shape encodings only; final runtime state/effects, valid maximum results and host validators remain untested.",
    }
    require(values["conservative_answer_bytes"] <= 1800, "answer-shape-budget")
    require(values["conservative_typed_facts_bytes"] <= 6 * 1024, "facts-shape-budget")
    require(values["conservative_complete_result_bytes"] <= 8 * 1024, "result-shape-budget")
    require(values["actor_slot_with_digest_and_feedback_reserve_bytes"] <= 4096, "slot-shape-budget")
    require(values["proposed_max_state_bytes"] <= 224 * 1024, "state-design-budget")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the reproducible design validation.json")
    args = parser.parse_args()
    fixtures = read_json(DATA / "fixtures.json")
    for model in fixtures["models"].values():
        inspect_tree(model["tree"], model["leaf_capacity"], model["internal_capacity"], initial=True)
    for case in fixtures["cases"]:
        try:
            check_case(case, fixtures["models"][case["source"]])
        except ValueError as exc:
            raise ValueError(case["id"] + ": " + str(exc)) from exc
    for case in fixtures["negative_trees"]:
        try:
            inspect_tree(case["tree"], case["leaf_capacity"], case["internal_capacity"])
        except ValueError as exc:
            require(str(exc) == case["reason"], case["id"] + ": unexpected reason " + str(exc))
        else:
            raise ValueError(case["id"] + ": invalid tree accepted")

    lesson = read_json(DATA / "insert-leaf.lesson.json")
    worked = next(c for c in fixtures["cases"] if c["id"] == "insert-leaf-split")
    require(lesson["exercise"] == {
        "format": 1, "semantics": "bplus-operations-v1",
        **fixtures["models"][worked["source"]], "task": worked["task"],
    }, "lesson-exercise")
    require(lesson["worked"]["answer"] == worked["answer"], "lesson-worked-answer")
    require(byte_count(lesson["exercise"]) <= 12 * 1024 and byte_count(lesson) <= 20 * 1024, "source-budget")
    probes = encoding_probes()
    sources = [DATA / "fixtures.json", DATA / "insert-leaf.lesson.json", Path(__file__)]
    report = {
        "format": 1, "status": "design-checks-passed",
        "coverage": {
            "initial_models": len(fixtures["models"]),
            "worked_cases": len(fixtures["cases"]),
            "read_cases": sum(c["task"]["kind"] in ("lookup", "range") for c in fixtures["cases"]),
            "invalid_trees_rejected": len(fixtures["negative_trees"]),
            "update_certificate_replay": False,
            "production_schemas": False, "installed_wheel": False,
            "browser_or_classroom_capacity": False,
        },
        "case_ids": [c["id"] for c in fixtures["cases"]],
        "largest_fixture_answer_bytes": max(byte_count(c["answer"]) for c in fixtures["cases"]),
        "encoding_probes": probes,
        "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
    }
    if args.write:
        (DATA / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    else:
        require(read_json(DATA / "validation.json") == report, "stale-validation-record: rerun with --write")
    print(json.dumps({"status": report["status"], **report["coverage"], "encoding_probes": probes}, ensure_ascii=True))


if __name__ == "__main__":
    main()

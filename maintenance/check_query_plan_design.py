# SPDX-License-Identifier: Apache-2.0
"""Check trusted, finite Query-plan Challenge design fixtures.

This is a specification aid, not a production parser, plugin engine or host
conformance test. Standard library only. Default is read-only; --write-report
refreshes the deterministic evidence next to the fixtures.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/design/query-plan-challenge"


class Invalid(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def read(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def connected(subset, edges):
    if not subset:
        return False
    reached = {min(subset)}
    while True:
        before = len(reached)
        for a, b in edges:
            if a in subset and b in subset and (a in reached or b in reached):
                reached.update((a, b))
        if before == len(reached):
            return reached == set(subset)


def prepare(exercise):
    """Semantic checks used by these trusted fixtures, not a full schema validator."""
    require(exercise["format"] == 1 and exercise["model"] == "teaching-cost-v1",
            "model")
    query = exercise["query"]
    relations = {item["id"]: item for item in query["relations"]}
    require(1 <= len(relations) <= 3 and len(relations) == len(query["relations"]),
            "relations")
    columns = {name: {c["id"]: c["type"] for c in r["columns"]}
               for name, r in relations.items()}
    edges = []
    for join in query["joins"]:
        (a, ac), (b, bc) = join["left"], join["right"]
        require(a in columns and b in columns and a != b, "query-join")
        require(ac in columns[a] and bc in columns[b] and
                columns[a][ac] == columns[b][bc], "join-type")
        edges.append(frozenset((a, b)))
    require(len(edges) == len(relations) - 1 and len(set(edges)) == len(edges)
            and connected(relations, edges), "query-graph")
    for relation, column in query["output"]:
        require(relation in columns and column in columns[relation], "projection")
    for name, relation in relations.items():
        if "filter" in relation:
            f = relation["filter"]
            kind = {int: "int", str: "text", bool: "bool"}.get(type(f["value"]))
            require(f["column"] in columns[name] and
                    columns[name][f["column"]] == kind, "filter-type")
        if "index" in relation:
            require("filter" in relation and
                    relation["index"]["column"] == relation["filter"]["column"],
                    "index-filter")
    statistics = exercise["statistics"]
    base = {item["relation"]: item for item in statistics["base"]}
    require(set(base) == set(relations) and len(base) == len(statistics["base"]),
            "base-coverage")
    for item in base.values():
        for field, low, high in (("rows", 0, 1000000), ("pages", 0, 1000000),
                                 ("row_bytes", 1, 1024)):
            value = item[field]
            require(type(value) is int and low <= value <= high, "base-bound")
        require(item["rows"] == 0 or item["pages"] > 0, "empty-pages")
    cards = {frozenset(item["relations"]): item["rows"]
             for item in statistics["cardinalities"]}
    expected = {frozenset(combination)
                for size in range(1, len(relations) + 1)
                for combination in itertools.combinations(relations, size)
                if connected(combination, edges)}
    require(set(cards) == expected and len(cards) == len(statistics["cardinalities"]),
            "statistics-coverage")
    for subset, rows in cards.items():
        require(type(rows) is int and 0 <= rows <= 1000000, "cardinality")
        if len(subset) == 1:
            name = next(iter(subset))
            require(rows <= base[name]["rows"], "filtered-cardinality")
            require("filter" in relations[name] or rows == base[name]["rows"],
                    "unfiltered-cardinality")
        else:
            for left in cards:
                right = subset - left
                if left < subset and right in cards:
                    require(rows <= cards[left] * cards[right], "join-cardinality")
    memory = exercise["limits"]["hash_bytes"]
    require(type(memory) is int and 0 <= memory <= 16777216, "memory-bound")
    return {"relations": relations, "edges": edges, "base": base,
            "cards": cards, "memory": memory}


def evaluate(model, answer):
    nodes = answer["nodes"]
    require(answer["format"] == 1 and 1 <= len(nodes) <= 5, "invalid-tree")
    parents = [0] * len(nodes)
    traversal = []

    def visit(index):
        node = nodes[index]
        if node["op"] == "join":
            visit(node["left"])
            visit(node["right"])
        traversal.append(index)

    # Check topology before recursion, so a cycle/shared child cannot be traversed.
    for index, node in enumerate(nodes):
        require(node["op"] in ("scan", "join"), "invalid-tree")
        if node["op"] == "join":
            for child in (node["left"], node["right"]):
                require(type(child) is int and 0 <= child < index, "invalid-tree")
                parents[child] += 1
    require(parents[-1] == 0 and all(count == 1 for count in parents[:-1]),
            "invalid-tree")
    visit(len(nodes) - 1)
    require(traversal == list(range(len(nodes))), "invalid-tree")

    built, seen, facts = [], set(), []
    for index, node in enumerate(nodes):
        method = node["method"]
        if node["op"] == "scan":
            name = node["relation"]
            require(name in model["relations"], "unknown-relation")
            require(name not in seen, "duplicate-relation")
            seen.add(name)
            subset = frozenset((name,))
            rows = model["cards"][subset]
            base = model["base"][name]
            width, workspace = base["row_bytes"], 0
            if method == "seq":
                local = 100 * base["pages"] + base["rows"]
            elif method == "index":
                relation = model["relations"][name]
                require("index" in relation, "unavailable-index")
                local = 400 * (relation["index"]["height"] + rows) + rows
            else:
                raise Invalid("scan-method")
            total = local
        else:
            left, right = built[node["left"]], built[node["right"]]
            require(not (left["subset"] & right["subset"]), "duplicate-relation")
            subset = left["subset"] | right["subset"]
            require(subset in model["cards"], "disconnected-join")
            rows = model["cards"][subset]
            width = left["width"] + right["width"]
            if method == "nested":
                local = left["rows"] * right["rows"] + rows
                workspace = 0
            elif method in ("hash-left", "hash-right"):
                build, probe = ((left, right) if method == "hash-left"
                                else (right, left))
                workspace = build["rows"] * (build["width"] + 16)
                require(workspace <= model["memory"], "hash-memory")
                local = 2 * build["rows"] + probe["rows"] + rows
            else:
                raise Invalid("join-method")
            total = local + left["cost"] + right["cost"]
        require(type(total) is int and 0 <= total <= 9007199254740991,
                "unsafe-integer")
        built.append({"subset": subset, "rows": rows, "width": width, "cost": total})
        facts.append({"node": index, "relations": sorted(subset), "rows": rows,
                      "row_bytes": width, "local_cost": local, "total_cost": total,
                      "hash_bytes": workspace})
    require(seen == set(model["relations"]), "missing-relation")
    return {"cost": built[-1]["cost"], "nodes": facts}


def trees(names, model):
    """Enumerate ordered labeled binary trees, scans and join methods independently."""
    if len(names) == 1:
        name = names[0]
        for method in ("seq", "index"):
            if method != "index" or "index" in model["relations"][name]:
                yield ("scan", name, method)
        return
    for size in range(1, len(names)):
        for left_names in itertools.combinations(names, size):
            right_names = tuple(name for name in names if name not in left_names)
            for left in trees(left_names, model):
                for right in trees(right_names, model):
                    for method in ("nested", "hash-left", "hash-right"):
                        yield ("join", left, right, method)


def flatten(tree):
    nodes = []

    def walk(node):
        if node[0] == "scan":
            result = {"op": "scan", "relation": node[1], "method": node[2]}
        else:
            left, right = walk(node[1]), walk(node[2])
            result = {"op": "join", "left": left, "right": right, "method": node[3]}
        nodes.append(result)
        return len(nodes) - 1

    walk(tree)
    return {"format": 1, "nodes": nodes}


def solve(model):
    candidates, valid = [], []
    for tree in trees(tuple(sorted(model["relations"])), model):
        answer = flatten(tree)
        candidates.append(canonical(answer))
        try:
            analysis = evaluate(model, answer)
        except Invalid as error:
            require(str(error) in ("disconnected-join", "hash-memory"),
                    "unexpected-enumeration-error")
            continue
        valid.append((analysis["cost"], tree, answer))
    require(len(candidates) == len(set(candidates)) <= 864, "enumeration-bound")
    require(bool(valid), "no-feasible-plan")
    best = min(cost for cost, _, _ in valid)
    return {"enumerated": len(candidates), "feasible": len(valid), "cost": best,
            "count": sum(cost == best for cost, _, _ in valid)}, valid


def mirror(tree):
    if tree[0] == "scan":
        return tree
    methods = {"nested": "nested", "hash-left": "hash-right",
               "hash-right": "hash-left"}
    return ("join", mirror(tree[2]), mirror(tree[1]), methods[tree[3]])


def expect_invalid(action, reason):
    try:
        action()
    except Invalid as error:
        require(str(error) == reason, "unexpected-reason:" + str(error))
    else:
        raise AssertionError("Expected rejection: " + reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    exercises, expected = read("exercises.json"), read("expected-cases.json")
    models = {name: prepare(exercise) for name, exercise in exercises.items()}
    outcomes = []
    for case in expected["cases"]:
        if case["expect"]["valid"]:
            facts = evaluate(models[case["exercise"]], case["answer"])
            require(facts["cost"] == case["expect"]["cost"], case["id"])
            outcomes.append({"id": case["id"], "valid": True, "cost": facts["cost"]})
        else:
            expect_invalid(lambda: evaluate(models[case["exercise"]], case["answer"]),
                           case["expect"]["reason"])
            outcomes.append({"id": case["id"], **case["expect"]})

    optima, mirror_count = {}, 0
    for name, model in models.items():
        summary, feasible = solve(model)
        require({key: summary[key] for key in ("cost", "count", "feasible")}
                == expected["optima"][name], "optimum:" + name)
        optima[name] = summary
        for cost, tree, _ in feasible:
            require(evaluate(model, flatten(mirror(tree)))["cost"] == cost,
                    "mirror-cost")
            mirror_count += 1

    # Exact memory boundary and monotonic optimum across all relevant thresholds.
    memory_answer = next(c["answer"] for c in expected["cases"]
                         if c["id"] == "memory-best")
    exact = copy.deepcopy(exercises["library"])
    exact["limits"]["hash_bytes"] = 480
    require(evaluate(prepare(exact), memory_answer)["cost"] == 214330,
            "workspace-exact")
    exact["limits"]["hash_bytes"] = 479
    expect_invalid(lambda: evaluate(prepare(exact), memory_answer), "hash-memory")
    previous, memory_costs = 9007199254740991, []
    for limit in (0, 479, 480, 1024, 3999, 4000, 95999, 96000, 240000, 1048576):
        changed = copy.deepcopy(exercises["library"])
        changed["limits"]["hash_bytes"] = limit
        optimum, _ = solve(prepare(changed))
        require(optimum["cost"] <= previous, "memory-monotonicity")
        previous = optimum["cost"]
        memory_costs.append({"hash_bytes": limit, "cost": previous})

    # An absent cardinality and an impossible estimate must not silently default.
    missing = copy.deepcopy(exercises["library"])
    missing["statistics"]["cardinalities"].pop()
    expect_invalid(lambda: prepare(missing), "statistics-coverage")
    impossible = copy.deepcopy(exercises["tiny"])
    impossible["statistics"]["cardinalities"][-1]["rows"] = 2
    expect_invalid(lambda: prepare(impossible), "join-cardinality")
    wrong_type = copy.deepcopy(exercises["selective"])
    wrong_type["query"]["relations"][0]["filter"]["value"] = True
    expect_invalid(lambda: prepare(wrong_type), "filter-type")

    # The maximum raw family really enumerates 864 unique candidates.
    maximum = copy.deepcopy(exercises["library"])
    for relation in maximum["query"]["relations"]:
        column = relation["columns"][0]["id"]
        relation["filter"] = {"column": column, "value": 1}
        relation["index"] = {"column": column, "height": 8}
    maximum_model = prepare(maximum)
    summary, _ = solve(maximum_model)
    require(summary["enumerated"] == 864, "maximum-family")

    files = ["exercises.json", "expected-cases.json",
             "exercise.schema.json", "answer.schema.json"]
    hashes = {name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
              for name in files}
    hashes["maintenance/check_query_plan_design.py"] = hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()
    report = {
        "status": "design-fixtures-only",
        "model": "teaching-cost-v1",
        "date": "2026-11-06",
        "files_sha256": hashes,
        "expected_cases_passed": len(outcomes),
        "cases": outcomes,
        "optima": optima,
        "mirrored_feasible_plans_checked": mirror_count,
        "memory_monotonicity": memory_costs,
        "workspace_exact_boundary": "480 accepted; 479 rejected",
        "invalid_statistics_checks_passed": 3,
        "maximum_candidates_enumerated": summary["enumerated"],
        "runtime_plugin_or_browser_tested": False,
    }
    if args.write_report:
        (FIXTURES / "validation.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent fixture, sorted-set, differential and installed-contract checks."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

import jsonschema
import pytest
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, validate_outcome, validate_portable_schema
from texstage_bplus_lab import model

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("bplus_probe", ROOT / "maintenance/bplus_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture(scope="module")
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, "Use a B+-only installed-wheel environment."
    selected, _ = probe.installed()
    assert Path(model.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    assert not Path(model.__file__).resolve().is_relative_to(ROOT / "plugins/bplus-lab")
    subprocess.run([sys.executable, "-c",
                    "import sys; from texstage.plugins.catalog import discover; discover(); assert 'texstage_bplus_lab' not in sys.modules"],
                   check=True)
    return selected


@pytest.fixture(scope="module")
def fixtures(provider):
    return probe.fixture(provider, "design-cases.json")


def exercise(fixtures, case):
    return {"format": 1, "semantics": "bplus-operations-v1",
            **deepcopy(fixtures["models"][case["source"]]), "task": deepcopy(case["task"])}


def acceptable(data):
    return data["replay"]["state"] == "complete" and all(v is not False for v in data["claims"].values())


def checked(seed, answer, row):
    assert not row.get("load_or_contract_error"), row
    assert row["result"]["status"] == "ok", row
    assert row["reuseRefused"] and row["disposalRefused"]
    assert row["result"]["data"] == model.analyze(seed, answer) == row["outcome"]["data"]
    data = row["outcome"]["data"]
    assert row["result"]["canonical"] == "bplus-v1:" + data["exercise"] + ":" + data["answer"]
    assert len(model.canonical(data)) <= 6144
    assert len(model.canonical(row["outcome"])) <= 8192
    return data


def test_manifest_discovery_and_schemas(provider, fixtures):
    assert set(provider.manifest["capabilities"]) == {"engines", "content_types"}
    assert set(provider.manifest["capabilities"]["content_types"]) == {"io.github.stefanjdecker.bpluslab.tree"}
    assert set(provider.manifest["capabilities"]["engines"]) == {probe.ENGINE}
    assert fixtures == json.loads((ROOT / "docs/design/bplus-tree/fixtures.json").read_text(encoding="utf-8"))
    for name in ("exercise", "answer", "analysis-result", "lesson"):
        schema = json.loads(provider.resources[f"{probe.PACKAGE}/schemas/{name}-v1.json"])
        validate_portable_schema(schema)
    worker = provider.resources[f"{probe.PACKAGE}/web/engine.worker.mjs"].decode()
    assert not any(line.startswith("import ") for line in worker.splitlines())


def test_hand_specified_trees_and_reads(provider, fixtures):
    inputs = [(exercise(fixtures, case), case["answer"]) for case in fixtures["cases"]]
    rows = probe.run([probe.request(seed, answer) for seed, answer in inputs])
    schemas = {name: json.loads(provider.resources[f"{probe.PACKAGE}/schemas/{name}-v1.json"])
               for name in ("exercise", "answer", "analysis-result")}
    for case, (seed, answer), row in zip(fixtures["cases"], inputs, rows, strict=True):
        data = checked(seed, answer, row)
        assert acceptable(data), case["id"]
        for name, value in (("exercise", seed), ("answer", answer), ("analysis-result", data)):
            jsonschema.validate(value, schemas[name])
        if "tree" in case["expected"]:
            assert data["final"] == case["expected"]["tree"], case["id"]
            assert data["metrics"]["height_after"] == case["expected"]["height"]
        else:
            assert data["read"]["keys"] == case["expected"]["keys"]
            assert data["read"]["page_visits"] == case["expected"]["page_visits"]


def case_named(fixtures, name):
    case = next(case for case in fixtures["cases"] if case["id"] == name)
    return exercise(fixtures, case), deepcopy(case["answer"])


def test_invalid_repairs_and_incomplete_are_domain_facts(fixtures):
    cases = []
    def add(name, change, reason, state="invalid"):
        seed, answer = case_named(fixtures, name)
        change(answer)
        cases.append((seed, answer, state, reason))
    add("insert-leaf-split", lambda a: a.__setitem__("path", [0, 1]), "wrong-path")
    add("range-cross-leaves", lambda a: a.__setitem__("leaves", [2]), "wrong-scan")
    add("insert-leaf-split", lambda a: a["repairs"].clear(), "missing-repair", "incomplete")
    add("insert-leaf-split", lambda a: a["repairs"][0].__setitem__("node", 3), "wrong-pending-node")
    add("insert-leaf-split", lambda a: a["repairs"][0].__setitem__("left_count", 1), "illegal-split")
    add("insert-leaf-split", lambda a: a["repairs"][0].__setitem__("separator", 25), "wrong-separator")
    add("insert-with-space", lambda a: a["repairs"].append({"op": "split", "node": 1, "left_count": 2, "separator": 10}), "extra-repair")
    add("delete-merge-left", lambda a: a["repairs"][0].__setitem__("op", "borrow"), "illegal-donor")
    add("delete-borrow-right", lambda a: a["repairs"][0].__setitem__("op", "merge"), "illegal-merge")
    add("delete-borrow-left", lambda a: a["repairs"][0].__setitem__("sibling", 1), "illegal-donor")
    add("delete-internal-borrow-right", lambda a: a["repairs"][0].__setitem__("sibling", 5), "illegal-merge")
    add("insert-three-level-cascade", lambda a: a["repairs"].pop(), "missing-repair", "incomplete")
    rows = probe.run([probe.request(s, a) for s, a, _, _ in cases])
    for (seed, answer, state, reason), row in zip(cases, rows, strict=True):
        data = checked(seed, answer, row)
        assert data["replay"]["state"] == state
        assert data["replay"]["reason"] == reason
        assert not {"final", "metrics", "read", "claims"} & set(data)


def test_wrong_predictions_do_not_invalidate_legal_replay(fixtures):
    inputs = []
    for kind in ("separator", "height", "coverage", "order"):
        seed, answer = case_named(fixtures, "insert-three-level-cascade")
        if kind == "separator":
            answer["separators"][0]["keys"][0] += 1
        elif kind == "height":
            answer["height"] = 2
        elif kind == "coverage":
            answer["separators"].pop()
        else:
            answer["separators"].reverse()
        inputs.append((seed, answer))
    seed, answer = case_named(fixtures, "range-cross-leaves")
    answer["keys"].reverse()
    inputs.append((seed, answer))
    rows = probe.run([probe.request(s, a) for s, a in inputs])
    for (seed, answer), row in zip(inputs, rows, strict=True):
        data = checked(seed, answer, row)
        assert data["replay"]["state"] == "complete"
        assert not acceptable(data)


def route(seed):
    nodes = {n["id"]: n for n in seed["tree"]["nodes"]}
    key = seed["task"]["key"]
    out, node = [], nodes[seed["tree"]["root"]]
    while True:
        out.append(node["id"])
        if node["kind"] == "leaf":
            return out
        node = nodes[node["children"][sum(k <= key for k in node["keys"])]]


def reindex(tree):
    """Re-label a new authored checkpoint; never alter IDs inside an operation."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    order = []
    def visit(i):
        order.append(i)
        if nodes[i]["kind"] == "internal":
            for child in nodes[i]["children"]:
                visit(child)
    visit(tree["root"])
    mapping = {old: new for new, old in enumerate(order)}
    result = []
    for old in order:
        n = deepcopy(nodes[old])
        n["id"] = mapping[old]
        if n["kind"] == "internal":
            n["children"] = [mapping[c] for c in n["children"]]
        else:
            n["next"] = None if n["next"] is None else mapping[n["next"]]
        result.append(n)
    return {"root": 0, "nodes": result}


def seed_for(tree, key, kind="insert", leaf=3, internal=4):
    return {"format": 1, "semantics": "bplus-operations-v1", "leaf_capacity": leaf,
            "internal_capacity": internal, "tree": reindex(tree), "task": {"kind": kind, "key": key}}


EMPTY = {"root": 0, "nodes": [{"id": 0, "kind": "leaf", "keys": [], "next": None}]}


@lru_cache(maxsize=8192)
def certificates(raw_seed, all_choices=False):
    """Enumerate finite candidate certificates; final expectations come from set/invariant oracles.

    This is a test generator, not the independent correctness oracle. It uses
    model refusals to prune candidates, then compares every selected case with JS.
    """
    seed = json.loads(raw_seed)
    base = {"format": 1, "path": route(seed), "repairs": [], "separators": [], "height": 0}
    keys = sorted({k for n in seed["tree"]["nodes"] if n["kind"] == "leaf" for k in n["keys"]} | {seed["task"]["key"]})
    def descend(answer):
        result = model.analyze(seed, answer)
        state = result["replay"]["state"]
        if state == "invalid":
            return []
        if state == "complete":
            answer["height"] = result["metrics"]["height_after"]
            answer["separators"] = [{"node": n["id"], "keys": n["keys"]}
                                    for n in result["final"]["nodes"] if n["kind"] == "internal"]
            return [(deepcopy(answer), result["final"])]
        if len(answer["repairs"]) == 3:
            return []
        node = result["replay"]["node"]
        if seed["task"]["kind"] == "insert":
            choices = [{"op": "split", "node": node, "left_count": c, "separator": k}
                       for c in range(1, 7) for k in keys]
        else:
            choices = [{"op": op, "node": node, "sibling": sibling}
                       for op in ("borrow", "merge") for sibling in range(len(seed["tree"]["nodes"]) + 4)]
        output = []
        for choice in choices:
            candidate = deepcopy(answer)
            candidate["repairs"].append(choice)
            output += descend(candidate)
            if output and not all_choices:
                break
        return output
    result = descend(base)
    assert result, raw_seed
    return result


def verify_set(seed, result):
    before = {k for n in seed["tree"]["nodes"] if n["kind"] == "leaf" for k in n["keys"]}
    key = seed["task"]["key"]
    expected = (before | {key}) if seed["task"]["kind"] == "insert" else (before - {key})
    entries = [k for n in result["nodes"] if n["kind"] == "leaf" for k in n["keys"]]
    assert len(entries) == len(expected) and set(entries) == expected
    # Independent snapshot checker was written before the production replay.
    spec = importlib.util.spec_from_file_location("bplus_design", ROOT / "maintenance/check_bplus_design.py")
    independent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(independent)
    independent.inspect_tree(result, seed["leaf_capacity"], seed["internal_capacity"])


def test_every_five_key_insertion_and_deletion_permutation(provider, record_property):
    requests, finals = [], {}
    for order in itertools.permutations(range(1, 6)):
        tree = deepcopy(EMPTY)
        for key in order:
            seed = seed_for(tree, key)
            answer, tree = deepcopy(certificates(model.canonical(seed))[0])
            verify_set(seed, tree)
            requests.append(probe.request(seed, answer))
        finals[model.canonical(reindex(tree))] = reindex(tree)
    for initial in finals.values():
        for order in itertools.permutations(range(1, 6)):
            tree = deepcopy(initial)
            for key in order:
                seed = seed_for(tree, key, "delete")
                answer, tree = deepcopy(certificates(model.canonical(seed))[0])
                verify_set(seed, tree)
                requests.append(probe.request(seed, answer))
            assert tree["nodes"] == [{"id": tree["root"], "kind": "leaf", "keys": [], "next": None}]
    rows = probe.run(requests, timeout=180)
    for request, row in zip(requests, rows, strict=True):
        assert acceptable(checked(json.loads(request["seed"]), json.loads(request["text"]), row))
    record_property("exhaustive_operation_cases", len(requests))
    record_property("distinct_terminal_shapes", len(finals))


def test_all_legal_choices_at_selected_boundaries(fixtures):
    seeds = [case_named(fixtures, name)[0] for name in (
        "leaf-capacity-four-split-two", "insert-internal-root-split", "delete-merge-left")]
    # Both neighbours can lend; and a separate L=4 case permits borrow OR merge.
    seeds.append(seed_for({"root": 0, "nodes": [
        {"id": 0, "kind": "internal", "keys": [10, 20], "children": [1, 2, 3]},
        {"id": 1, "kind": "leaf", "keys": [1, 2, 3], "next": 2},
        {"id": 2, "kind": "leaf", "keys": [10, 11], "next": 3},
        {"id": 3, "kind": "leaf", "keys": [20, 21, 22], "next": None}]}, 10, "delete"))
    seeds.append(seed_for({"root": 0, "nodes": [
        {"id": 0, "kind": "internal", "keys": [10], "children": [1, 2]},
        {"id": 1, "kind": "leaf", "keys": [1, 2], "next": 2},
        {"id": 2, "kind": "leaf", "keys": [10, 11, 12], "next": None}]}, 1, "delete", leaf=4))
    requests, groups = [], []
    for seed in seeds:
        choices = deepcopy(certificates(model.canonical(seed), True))
        assert len(choices) == 2
        groups.append(choices)
        for answer, final in choices:
            verify_set(seed, final)
            requests.append(probe.request(seed, answer))
    assert {a["height"] for a, _ in groups[-1]} == {0, 1}
    rows = probe.run(requests)
    for request, row in zip(requests, rows, strict=True):
        assert acceptable(checked(json.loads(request["seed"]), json.loads(request["text"]), row))
    assert all(rows[i]["outcome"]["key"] != rows[i + 1]["outcome"]["key"] for i in range(0, len(rows), 2))


def test_seeded_sequences_all_capacity_pairs(provider, record_property):
    rng, requests = random.Random(20261106), []
    for leaf, internal in itertools.product(range(3, 7), repeat=2):
        tree, current = deepcopy(EMPTY), set()
        for step in range(90):
            key = rng.randrange(-50, 51)
            kind = "delete" if step % 3 == 0 else "insert"
            if len(current) >= 35:
                kind, key = "delete", rng.choice(sorted(current))
            seed = seed_for(tree, key, kind, leaf, internal)
            answer, final = deepcopy(certificates(model.canonical(seed))[0])
            verify_set(seed, final)
            requests.append(probe.request(seed, answer))
            # Checkpoint input deliberately stops at height two.
            if answer["height"] == 3:
                tree, current = deepcopy(EMPTY), set()
            else:
                tree = final
                if kind == "insert": current.add(key)
                else: current.discard(key)
    rows = probe.run(requests, timeout=180)
    for request, row in zip(requests, rows, strict=True):
        assert acceptable(checked(json.loads(request["seed"]), json.loads(request["text"]), row))
    record_property("seeded_operation_cases", len(requests))


@pytest.mark.parametrize("text", [
    "{", "null", "[]", '{"format":1,"format":1}', '{"format":1.0,"path":[0],"keys":[]}',
    '{"format":1e0,"path":[0],"keys":[]}', '{"format":true,"path":[0],"keys":[]}',
    '{"format":1,"path":[true],"keys":[]}', '{"format":1,"path":[64],"keys":[]}',
    '{"format":1,"path":[0],"keys":[10000]}', '{"format":1,"path":[0],"keys":[1.0]}',
    '{"format":1,"path":[0],"keys":[],"extra":0}', '{"format":1,"path":[0],"keys":[NaN]}',
    '{"format":1,"path":[0],"keys":[],"x":"\\ud800"}', '{"format":1,"path":[0],"keys":[],"__proto__":{}}',
    '{"format":1,"\\u0066ormat":1,"path":[0],"keys":[]}', "[" * 100 + "0" + "]" * 100,
])
def test_malformed_answers_are_syntax(fixtures, text):
    seed, _ = case_named(fixtures, "empty-lookup")
    row = probe.run([{"seed": model.canonical(seed), "text": text}])[0]
    assert row["outcome"]["status"] == "syntax"


def test_bad_source_shapes_and_tree_invariants(fixtures):
    sources = [{"format": 1, "semantics": "bplus-operations-v1", "leaf_capacity": n["leaf_capacity"],
                "internal_capacity": n["internal_capacity"], "tree": n["tree"], "task": {"kind": "lookup", "key": 0}}
               for n in fixtures["negative_trees"]]
    seed, answer = case_named(fixtures, "empty-lookup")
    for key, value in [("leaf_capacity", True), ("internal_capacity", 2), ("format", 1.0), ("semantics", "unknown")]:
        bad = deepcopy(seed); bad[key] = value; sources.append(bad)
    bad = deepcopy(seed); bad["tree"]["nodes"][0]["id"] = 1; sources.append(bad)
    bad = deepcopy(seed); bad["task"] = {"kind": "range", "lower": 10, "upper": 9}; sources.append(bad)
    for source in sources:
        with pytest.raises(model.InputError):
            model.source_for(source)
    rows = probe.run([probe.request(s, answer) for s in sources])
    assert all(row.get("load_or_contract_error") for row in rows)
    rows = probe.run([{"seed": "[]", "text": "{}"}, {"seed": '{"format":1,"format":1}', "text": "{}"}])
    assert all(row.get("load_or_contract_error") for row in rows)


def test_identity_namespace_budget_and_result_corruption(provider, fixtures):
    seed, answer = case_named(fixtures, "insert-three-level-cascade")
    rows = probe.run([probe.request(seed, answer, budget=0), probe.request(seed, answer),
                      probe.request(seed, answer, data_patch={"extra": 1}),
                      probe.request(seed, answer, options={"capacity": 100}),
                      probe.request(seed, answer) | {"text": " " * 2001}])
    assert rows[0]["budget_error"] == "ResourceLimit"
    assert acceptable(checked(seed, answer, rows[1]))
    assert rows[2].get("load_or_contract_error") and rows[3].get("load_or_contract_error")
    assert rows[4]["outcome"]["status"] == "refused"
    with pytest.raises(model.ResourceLimit):
        model.analyze(seed, answer, model.Budget(0))
    _, engine = probe.installed()
    binding = {"engine": probe.ENGINE, "seed": model.canonical(seed), "options": {}, "references": []}
    actual = namespace(provider, probe.ENGINE, engine, binding)
    changed = namespace(provider, probe.ENGINE, engine, binding | {"seed": ""})
    assert actual != changed
    with pytest.raises(PluginError):
        validate_outcome(rows[1]["outcome"], provider, engine, changed)
    corrupted = deepcopy(rows[1]["outcome"])
    corrupted["data"]["final"]["nodes"][0]["extra"] = 0
    with pytest.raises(PluginError):
        validate_outcome(corrupted, provider, engine, actual)


def test_integer_token_parser_and_http_identity_vectors():
    for text in ('{"x":1.0}', '{"x":1e0}', '{"x":1,"x":2}', '{"x":"\\ud800"}'):
        with pytest.raises(model.InputError):
            model.parse(text)
    with pytest.raises(model.ResourceLimit):
        model.parse(" " * 32769)
    vectors = ["", "abc", "ä", "\U0001f333", "bplus-operations-v1"]
    rows = probe.run([{"hash": text} for text in vectors])
    assert [row["hash"] for row in rows] == [hashlib.sha256(s.encode("utf-8")).hexdigest() for s in vectors]


def test_source_and_answers_are_not_mutated(fixtures):
    seed, answer = case_named(fixtures, "insert-three-level-cascade")
    original = model.canonical([seed, answer])
    first = model.analyze(seed, answer)
    assert model.canonical([seed, answer]) == original
    assert model.analyze(seed, answer) == first
    rows = probe.run([probe.request(seed, answer), probe.request(seed, answer)])
    assert rows[0]["outcome"] == rows[1]["outcome"]


def test_valid_large_cascade_and_full_range_fit_transport(provider, record_property):
    # Nineteen leaves under five internal children. Two three-entry leaves
    # give forty keys; the last insertion splits leaf, parent and root.
    groups = [3, 3, 3, 5, 5]
    nodes, leaves = [], []
    next_id, key = 1, -9999
    parents, minima = [], []
    for count in groups:
        parent_id = next_id
        next_id += 1
        parent = {"id": parent_id, "kind": "internal", "keys": [], "children": []}
        parents.append(parent_id)
        minima.append(key)
        for i in range(count):
            leaf_id = next_id
            next_id += 1
            size = 3 if len(leaves) in (0, 18) else 2
            values = list(range(key, key + size))
            key += size
            if i:
                parent["keys"].append(values[0])
            parent["children"].append(leaf_id)
            leaves.append(leaf_id)
            nodes.append({"id": leaf_id, "kind": "leaf", "keys": values, "next": None})
        nodes.append(parent)
    by_id = {n["id"]: n for n in nodes}
    for a, b in zip(leaves, leaves[1:]):
        by_id[a]["next"] = b
    initial = {"root": 0, "nodes": sorted([
        {"id": 0, "kind": "internal", "keys": minima[1:], "children": parents}, *nodes], key=lambda n: n["id"])}
    seed = seed_for(initial, key, leaf=3, internal=5)
    answer, final = deepcopy(certificates(model.canonical(seed))[0])
    assert len(answer["repairs"]) == 3 and answer["height"] == 3
    assert len(final["nodes"]) == 29
    verify_set(seed, final)
    interval = deepcopy(seed)
    interval["task"] = {"kind": "range", "lower": -9999, "upper": 9999}
    nodes_by_id = {n["id"]: n for n in interval["tree"]["nodes"]}
    first_path, node = [0], nodes_by_id[0]
    while node["kind"] != "leaf":
        node = nodes_by_id[node["children"][0]]
        first_path.append(node["id"])
    range_answer = {"format": 1, "path": first_path, "leaves": leaves,
                    "keys": list(range(-9999, key))}
    rows = probe.run([probe.request(seed, answer), probe.request(interval, range_answer)])
    for s, a, row in zip((seed, interval), (answer, range_answer), rows, strict=True):
        assert acceptable(checked(s, a, row))
    assert rows[0]["outcome"]["data"]["metrics"]["splits"] == 3
    record_property("large_valid_facts_bytes", len(model.canonical(rows[0]["outcome"]["data"])))
    record_property("large_valid_outcome_bytes", len(model.canonical(rows[0]["outcome"])))
    with pytest.raises(model.InputError):
        model.source_for(seed_for(final, key, "delete", leaf=3, internal=5))


def test_author_envelope_schema_and_worked_fixture(provider):
    lesson = json.loads((ROOT / "docs/design/bplus-tree/insert-leaf.lesson.json").read_text(encoding="utf-8"))
    schema = json.loads(provider.resources[f"{probe.PACKAGE}/schemas/lesson-v1.json"])
    jsonschema.validate(lesson, schema)
    assert acceptable(model.analyze(lesson["exercise"], lesson["worked"]["answer"]))
    invalid = deepcopy(lesson)
    invalid["extra"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)

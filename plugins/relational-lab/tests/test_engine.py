# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel checks: hand answers, independent Python, tiny domains and SDK."""
import copy
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, validate_outcome, validate_portable_schema
from texstage_relational_lab import model

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("relational_probe", ROOT / "maintenance/relational_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture(scope="module")
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, "Use a relational-only installed-wheel environment."
    selected, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    assert not Path(model.__file__).is_relative_to(ROOT / "plugins/relational-lab")
    code = "import sys; from texstage.plugins.catalog import discover; discover(); assert 'texstage_relational_lab' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)
    return selected


@pytest.fixture(scope="module")
def example(provider):
    return model.source(probe.fixture(provider, "construct.exercise.json"))


@pytest.fixture(scope="module")
def rewrite(provider):
    return model.source(probe.fixture(provider, "rewrite.exercise.json"))


@pytest.fixture(scope="module")
def cases(provider):
    return probe.fixture(provider, "expected-cases.json")


def facts(row):
    assert not row.get("load_or_contract_error"), row
    assert row["result"]["status"] == "ok", row
    assert row["reuseRefused"] and row["disposalRefused"]
    assert row["milliseconds"] < 2000
    data = row["result"]["data"]
    assert json.loads(row["result"]["canonical"]) == data == row["outcome"]["data"]
    assert len(model.canonical(data)) <= 8192
    assert len(model.canonical(row["outcome"])) <= 12288
    return data


def tiny(schemas=None, tables=None, *, mode="construct", baseline=None):
    schemas = schemas or {"r": [["x", "int"]], "s": [["y", "int"]], "t": [["x", "int"]]}
    if tables is None:
        tables = {"r": [[0], [1]], "s": [[0], [1]], "t": [[1], [2]]}
    source = {"format": 1, "id": "tiny", "title": {"en": "Tiny", "de": "Klein"},
              "prompt": {"en": "Inspect the tree.", "de": "Untersuchen Sie den Baum."},
              "relations": schemas, "instances": [{"id": "shown", "visibility": "public", "tables": tables}],
              "task": {"mode": mode, "allowed_operators": list(model.OPS), "feedback": "on-reveal"}}
    if mode == "construct":
        first = next(iter(schemas))
        source |= {"initial_tree": [], "reference_tree": [["rel", first]]}
        source["task"]["expected_header"] = schemas[first]
    else:
        source["baseline_tree"] = baseline
        source["task"] |= {"allowed_rules": list(model.RULES), "goal": "reduce-public-materialization"}
    return model.source(source)


def atom(op, a, b, *, literal=True):
    return [op, ["a", a], ["v" if literal else "a", b]]


def answer(tree):
    return {"mode": "construct", "tree": tree}


def verify(exercise, submission, row):
    data = facts(row)
    assert data == model.analyze(exercise, submission)
    return data


def test_owned_schemas_and_fixtures(provider, example, rewrite, cases):
    for name in ("construct.exercise.json", "rewrite.exercise.json", "expected-cases.json"):
        assert probe.fixture(provider, name) == json.loads((ROOT / "docs/design/relational-algebra" / name).read_text(encoding="utf-8"))
    for name in ("answer", "analysis-result"):
        schema = json.loads(provider.resources[f"{probe.PACKAGE}/schemas/{name}-v1.json"])
        validate_portable_schema(schema)
    assert all("/" in p for p in provider.resources)
    assert not provider.manifest["capabilities"].get("content_types")


def test_hand_cases_and_independent_sqlite(example, cases):
    rows = probe.run([probe.request(example, answer(c["tree"])) for c in cases["construction"]])
    for case, row in zip(cases["construction"], rows, strict=True):
        data = verify(example, answer(case["tree"]), row)
        if "error" in case:
            assert not data["valid"] and data["reason"] == case["error"]
            assert "fixtures" not in data and "public" not in data
            continue
        values = {}
        for instance in example["instances"]:
            result, _ = model.evaluate_tree(example, case["tree"], instance)
            values[instance["id"]] = result.data()["rows"]
        if "expected" in case:
            assert values == case["expected"]
        if "shown" in case:
            assert values["shown"] == case["shown"]
        if "renamed" in case:
            assert values["renamed"] == case["renamed"]
        if "public_metric" in case:
            assert data["public"]["cells"] == case["public_metric"]
        if case.get("passes_all") is False:
            assert values != cases["construction"][0]["expected"]
    assert facts(rows[0])["fixtures"] == facts(rows[1])["fixtures"]
    assert rows[0]["outcome"]["key"] != rows[1]["outcome"]["key"]
    for instance in example["instances"]:
        with sqlite3.connect(":memory:") as db:
            for name, columns in example["relations"].items():
                db.execute(f"CREATE TABLE {name} (" + ",".join(n + " " + ("TEXT" if t == "text" else "INTEGER") for n, t in columns) + ")")
                db.executemany(f"INSERT INTO {name} VALUES (" + ",".join("?" for _ in columns) + ")", instance["tables"][name])
            actual = db.execute("SELECT DISTINCT name FROM books JOIN loans ON book=item JOIN members ON borrower=member WHERE open=1 AND topic='db' ORDER BY name").fetchall()
            assert list(map(list, actual)) == cases["construction"][0]["expected"][instance["id"]]


def test_operator_examples(cases):
    inputs = [(tiny(c["relations"], c["tables"]), answer(c["tree"]), c) for c in cases["operators"]]
    rows = probe.run([probe.request(e, a) for e, a, _ in inputs])
    for (exercise, submission, case), row in zip(inputs, rows, strict=True):
        data = verify(exercise, submission, row)
        if "error" in case:
            assert not data["valid"] and data["reason"] == case["error"]
        else:
            relation, _ = model.evaluate_tree(exercise, submission["tree"], exercise["instances"][0])
            assert relation.data()["rows"] == case["expected"]
            if "header" in case:
                assert relation.data()["header"] == case["header"]


def test_worked_certificate(rewrite, cases):
    steps = cases["rewrite"]["steps"]
    submissions = [{"mode": "rewrite", "steps": steps[:n]} for n in range(6)]
    submissions.append({"mode": "rewrite", "steps": [cases["rewrite"]["invalid_step"]]})
    rows = probe.run([probe.request(rewrite, a) for a in submissions])
    for submission, row in zip(submissions, rows, strict=True):
        verify(rewrite, submission, row)
    good, bad = facts(rows[-2]), facts(rows[-1])
    assert good["proof"] == {"verified": True, "steps": 5, "tree": cases["rewrite"]["derived_tree"],
                             "baseline_cells": 83, "improved": True}
    assert good["public"]["cells"] == 51
    assert not facts(rows[0])["proof"]["improved"]
    assert not bad["valid"] and bad["reason"] == "attribute-side-condition" and bad["step"] == 0


def powerset(values):
    return [list(c) for n in range(len(values) + 1) for c in combinations(values, n)]


def test_all_tiny_unions_and_differences():
    inputs = []
    for a, b in product(powerset([-1, 0, 1]), repeat=2):
        exercise = tiny(tables={"r": [[x] for x in a], "s": [], "t": [[x] for x in b]})
        for op in ("union", "difference"):
            tree = [["rel", "r"], ["rel", "t"], [op, 0, 1]]
            expected = sorted(set(a) | set(b) if op == "union" else set(a) - set(b))
            inputs.append((exercise, answer(tree), [[v] for v in expected]))
    for (exercise, submission, expected), row in zip(inputs, probe.run([probe.request(e, a) for e, a, _ in inputs]), strict=True):
        data = verify(exercise, submission, row)
        expected_fact = model.Relation((("x", "int"),), frozenset(map(tuple, expected))).facts("shown")
        assert data["fixtures"] == [expected_fact]


def test_all_tiny_selection_rewrites():
    base = [["rel", "r"], ["rel", "s"], ["product", 0, 1],
            ["select", 2, [atom("lt", "x", 1), atom("ge", "y", 0)]]]
    steps = [{"rule": "split-select", "path": []},
             {"rule": "push-select-right", "path": [0]},
             {"rule": "push-select-left", "path": []}]
    inputs = []
    for a, b in product(powerset([-1, 0, 1]), repeat=2):
        exercise = tiny(tables={"r": [[x] for x in a], "s": [[x] for x in b], "t": []}, mode="rewrite", baseline=base)
        expected = frozenset((x, y) for x in a for y in b if x < 1 and y >= 0)
        inputs.append((exercise, {"mode": "rewrite", "steps": steps}, expected))
    for (exercise, submission, expected), row in zip(inputs, probe.run([probe.request(e, a) for e, a, _ in inputs]), strict=True):
        data = verify(exercise, submission, row)
        assert data["proof"]["verified"]
        assert data["fixtures"] == [model.Relation((("x", "int"), ("y", "int")), expected).facts("shown")]


def test_all_tiny_product_join_rewrites():
    base = [["rel", "r"], ["rel", "s"], ["product", 0, 1], ["select", 2, [atom("eq", "x", "y", literal=False)]]]
    submission = {"mode": "rewrite", "steps": [{"rule": "product-to-join", "path": []}]}
    exercises = [tiny(tables={"r": [[x] for x in a], "s": [[x] for x in b], "t": []}, mode="rewrite", baseline=base)
                 for a, b in product(powerset([-1, 0, 1]), repeat=2)]
    for exercise, row in zip(exercises, probe.run([probe.request(e, submission) for e in exercises]), strict=True):
        data = verify(exercise, submission, row)
        a = {r[0] for r in exercise["instances"][0]["tables"]["r"]}
        b = {r[0] for r in exercise["instances"][0]["tables"]["s"]}
        assert data["fixtures"] == [model.Relation((("x", "int"), ("y", "int")), frozenset((v, v) for v in a & b)).facts("shown")]


def test_all_tiny_projection_collapses():
    base = [["rel", "r"], ["project", 0, ["x", "y"]], ["project", 1, ["x"]]]
    submission = {"mode": "rewrite", "steps": [{"rule": "collapse-project", "path": []}]}
    exercises = [tiny({"r": [["x", "int"], ["y", "int"]]}, {"r": list(map(list, subset))}, mode="rewrite", baseline=base)
                 for subset in powerset(list(product([0, 1], repeat=2)))]
    for exercise, row in zip(exercises, probe.run([probe.request(e, submission) for e in exercises]), strict=True):
        data = verify(exercise, submission, row)
        expected = frozenset((r[0],) for r in exercise["instances"][0]["tables"]["r"])
        assert data["fixtures"] == [model.Relation((("x", "int"),), expected).facts("shown")]


@pytest.mark.parametrize("rule", model.RULES)
def test_inapplicable_rules(rewrite, rule):
    submission = {"mode": "rewrite", "steps": [{"rule": rule, "path": [0, 0, 0, 0]}]}
    data = verify(rewrite, submission, probe.run([probe.request(rewrite, submission)])[0])
    assert not data["valid"] and data["reason"] == "rule-not-applicable"


@pytest.mark.parametrize("tree,reason", [
    ([["rel","missing"]], "unknown-relation"),
    ([["rel","r"],["rel","s"]], "not-a-tree"),
    ([["rel","r"],["union",0,0]], "not-a-tree"),
    ([["select",0,[atom("eq","x",1)]]], "child-index"),
    ([["rel","r"],["project",0,["absent"]]], "unknown-attribute"),
    ([["rel","r"],["select",0,[atom("eq","x",True)]]], "type-mismatch"),
    ([["rel","r"],["rel","t"],["product",0,1]], "attribute-collision"),
    ([["rel","r"],["rename",0,[["x","y"],["x","z"]]]], "duplicate-attribute"),
    ([["rel","r"],["rel","s"],["rel","t"],["union",0,2],["product",3,1]], "postorder"),
    ([["rel","r"]] + [["select",i,[atom("eq","x",0)]] for i in range(8)], "tree-depth"),
])
def test_invalid_domain_trees(tree, reason):
    exercise = tiny()
    submission = answer(tree)
    data = verify(exercise, submission, probe.run([probe.request(exercise, submission)])[0])
    assert not data["valid"] and data["reason"] == reason


@pytest.mark.parametrize("text", [
    "{", '{"mode":"construct","mode":"rewrite","tree":[]}', '{"mode":"construct","tree":[]}',
    '{"mode":"construct","tree":[["rel","r"]],"hidden":true}',
    '{"mode":"construct","tree":[["project",true,["x"]]]}',
    '{"mode":"construct","tree":[["project",1.0,["x"]]]}',
    '{"mode":"construct","tree":[["project",1e0,["x"]]]}',
    '{"mode":"construct","tree":[["rel",["r"]]]}',
    '{"mode":"construct","tree":[["rel","r"],["select",0,[["eq",["a","x"],["v",NaN]]]]]}',
    '{"mode":"construct","tree":[["rel","r"],["select",0,[["eq",["a","x"],["v","\\ud800"]]]]]}',
])
def test_malformed_answers(text):
    exercise = tiny()
    row = probe.run([probe.request(exercise, text=text)])[0]
    assert row["result"] == {"status": "syntax"}
    with pytest.raises((model.InputError, model.ResourceLimit)):
        model.answer(model.parse(text))


def test_unicode_types_rename_and_set_normalization():
    schemas = {"r": [["word","text"],["n","int"],["flag","bool"]]}
    tables = {"r": [["e\u0301",-1,True], ["é",-1,True], ["\U00010000",2,False], ["\ue000",2,False], ["\x7f",0,False]]}
    exercise = tiny(schemas, tables)
    tree = [["rel","r"],["project",0,["word"]]]
    data = verify(exercise, answer(tree), probe.run([probe.request(exercise, answer(tree))])[0])
    expected = frozenset((x,) for x in ["é","\U00010000","\ue000","\x7f"])
    assert data["fixtures"] == [model.Relation((("word","text"),), expected).facts("shown")]
    assert model.source_diagnostics(exercise) == [{"instance":"shown","relation":"r","duplicate_rows":1}]
    wrong = [["rel","r"],["select",0,[atom("lt","word","z")]]]
    assert facts(probe.run([probe.request(exercise, answer(wrong))])[0])["reason"] == "unordered-type"
    swap = tiny({"r":[["x","int"],["y","int"]]}, {"r":[[1,2],[3,4]]})
    renamed = [["rel","r"],["rename",0,[["x","y"],["y","x"]]]]
    assert verify(swap, answer(renamed), probe.run([probe.request(swap, answer(renamed))])[0])["valid"]


def test_semantic_identity_and_mode_guard(example):
    renamed = copy.deepcopy(example)
    renamed["title"]["en"] = "Different presentation"
    renamed["instances"].reverse()
    renamed["task"]["allowed_operators"].reverse()
    for instance in renamed["instances"]:
        for name, rows in instance["tables"].items():
            instance["tables"][name] = list(reversed(rows))
    reordered = copy.deepcopy(renamed)
    for name, columns in reordered["relations"].items():
        columns.reverse()
        for instance in reordered["instances"]:
            instance["tables"][name] = [list(reversed(row)) for row in instance["tables"][name]]
    submissions = [probe.request(e) for e in (example, renamed, reordered)]
    data = [facts(row) for row in probe.run(submissions)]
    assert data[0] == data[1] == data[2]
    bad_mode = {"mode":"rewrite", "steps":[]}
    data = verify(example, bad_mode, probe.run([probe.request(example, bad_mode)])[0])
    assert data["reason"] == "wrong-mode" and not data["valid"]


@pytest.mark.parametrize("mutation", ["duplicate-instance", "no-public", "bad-row", "unknown-field", "bad-reference", "duplicate-header"])
def test_bad_sources(example, mutation):
    value = copy.deepcopy(example)
    if mutation == "duplicate-instance": value["instances"][1]["id"] = value["instances"][0]["id"]
    if mutation == "no-public": value["instances"][0]["visibility"] = "private"
    if mutation == "bad-row": value["instances"][0]["tables"]["books"][0][0] = True
    if mutation == "unknown-field": value["execute"] = "unexpected"
    if mutation == "bad-reference": value["reference_tree"] = [["rel","missing"]]
    if mutation == "duplicate-header": value["relations"]["books"][1][0] = "book"
    with pytest.raises(model.InputError): model.source(value)
    assert probe.run([probe.request(value)])[0]["load_or_contract_error"]


def test_work_rows_and_encoded_answer_limits():
    tables = {name:[[n] for n in range(12)] for name in ("r","s","t","u")}
    schemas = {name:[[attr,"int"]] for name,attr in zip(tables, ("a","b","c","d"))}
    exercise = tiny(schemas, tables)
    wide = [["rel","r"],["rel","s"],["product",0,1],["rel","t"],["product",2,3]]
    row = probe.run([probe.request(exercise, answer(wide))])[0]
    assert row["result"] == {"status":"refused"}
    with pytest.raises(model.ResourceLimit): model.analyze(exercise, answer(wide))
    expensive = [["rel","r"],["rel","s"],["product",0,1],["rel","t"],["rel","u"],["product",3,4],
                 ["join",2,5,[atom("eq","a","c",literal=False),atom("eq","b","d",literal=False)]]]
    good = facts(probe.run([probe.request(exercise, answer(expensive))])[0])
    assert good["valid"] and good["public"]["trace"][-1][1] == 144
    for n in range(3):
        exercise["instances"].append({"id":f"private{n}", "visibility":"private", "tables":copy.deepcopy(tables)})
    assert probe.run([probe.request(exercise, answer(expensive))])[0]["result"] == {"status":"refused"}
    with pytest.raises(model.ResourceLimit): model.analyze(exercise, answer(expensive))
    small = tiny({"r":[["word","text"]]}, {"r":[["hello"]]})
    huge = [["rel","r"]] + [["select",i,[atom("eq","word","\U0001f642"*24)]] for i in range(7)]
    assert len(model.canonical(answer(huge))) > 1800
    raw = json.dumps(answer(huge), ensure_ascii=False)
    assert len(raw) < 2000
    assert probe.run([probe.request(small, text=raw)])[0]["result"] == {"status":"refused"}
    assert probe.run([probe.request(small, text=" " * 2001)])[0]["result"] == {"status":"refused"}


def test_hash_vectors_without_webcrypto():
    strings = ["", "abc", "x"*1000, "é\U0001f642", "\x00"]
    assert [r["hash"] for r in probe.run([{"hash":s} for s in strings])] == [hashlib.sha256(s.encode()).hexdigest() for s in strings]


def test_real_contract_rejects_mutated_facts(example):
    selected, engine = probe.installed()
    request = probe.request(example)
    row = probe.run([request])[0]
    expected_namespace = namespace(selected, probe.ENGINE, engine, {"seed":request["seed"],"options":{},"references":[]})
    validate_outcome(row["outcome"], selected, engine, expected_namespace)
    bad = copy.deepcopy(row["outcome"])
    bad["data"]["public"]["cells"] = "83"
    with pytest.raises(PluginError): validate_outcome(bad, selected, engine, expected_namespace)
    assert probe.run([request | {"data_patch":{"public":bad["data"]["public"]}}])[0]["load_or_contract_error"]
    bad = copy.deepcopy(row["outcome"])
    bad["data"]["leaked_rows"] = [["secret"]]
    with pytest.raises(PluginError): validate_outcome(bad, selected, engine, expected_namespace)
    assert probe.run([request | {"data_patch":{"leaked_rows":[["secret"]]}}])[0]["load_or_contract_error"]


def test_operator_and_rule_allowlists_and_path(rewrite):
    exercise = tiny()
    exercise["task"]["allowed_operators"] = ["rel"]
    submission = answer([["rel","r"],["project",0,["x"]]])
    data = verify(exercise, submission, probe.run([probe.request(exercise, submission)])[0])
    assert data["reason"] == "operator-not-allowed"
    exercise = copy.deepcopy(rewrite)
    exercise["task"]["allowed_rules"] = ["collapse-project"]
    submission = {"mode":"rewrite","steps":[{"rule":"split-select","path":[0]}]}
    assert verify(exercise, submission, probe.run([probe.request(exercise, submission)])[0])["reason"] == "rule-not-allowed"
    submission = {"mode":"rewrite","steps":[{"rule":"collapse-project","path":[1]}]}
    assert verify(exercise, submission, probe.run([probe.request(exercise, submission)])[0])["reason"] == "rule-path"


def test_rule_side_conditions_and_identical_independent_leaves():
    exercise = tiny(mode="rewrite", baseline=[["rel","r"],["rel","s"],["product",0,1],
        ["select",2,[atom("eq","x","y",literal=False)]]])
    for rule in ("push-select-left","push-select-right"):
        submission = {"mode":"rewrite","steps":[{"rule":rule,"path":[]}]}
        assert verify(exercise, submission, probe.run([probe.request(exercise, submission)])[0])["reason"] == "attribute-side-condition"
    exercise = tiny()
    repeated = answer([["rel","r"],["rel","r"],["union",0,1]])
    assert verify(exercise, repeated, probe.run([probe.request(exercise, repeated)])[0])["valid"]
    collision = tiny({"r":[["x","int"],["y","int"]]}, {"r":[[1,2]]})
    submission = answer([["rel","r"],["rename",0,[["x","y"]]]])
    assert verify(collision, submission, probe.run([probe.request(collision, submission)])[0])["reason"] == "attribute-collision"
    # Projection collapse cannot recover an attribute removed by the inner projection.
    invalid = copy.deepcopy(exercise)
    invalid["initial_tree"] = [["rel","r"],["project",0,["x"]],["project",1,["absent"]]]
    with pytest.raises(model.InputError): model.source(invalid)
    assert probe.run([probe.request(invalid)])[0]["load_or_contract_error"]


def test_parser_boundaries_and_different_seed_identity(example):
    request = probe.request(example)
    for prefix in ('{"id":"duplicate",', '{"\\u0069d":"duplicate",'):
        bad_seed = prefix + request["seed"][1:]
        assert probe.run([request | {"seed":bad_seed}])[0]["load_or_contract_error"]
        with pytest.raises(model.InputError): model.parse(bad_seed)
    assert probe.run([request | {"seed":" " * 65537}])[0]["load_or_contract_error"]
    with pytest.raises(model.ResourceLimit): model.parse(" " * 65537)
    for options in ({'extra':True}, [], None):
        assert probe.run([request | {"options":options}])[0]["load_or_contract_error"]
    changed = copy.deepcopy(example)
    changed["instances"][1]["tables"]["members"][0][1] = "Other"
    rows = probe.run([request, probe.request(changed)])
    assert facts(rows[0])["exercise"] != facts(rows[1])["exercise"]


def test_declared_payload_upper_bound(rewrite):
    # Exercise shape maxima together: 4 fixture entries, 16 trace rows and a
    # near-limit derived tree, including supplementary Unicode escaping.
    selected, engine = probe.installed()
    request = probe.request(rewrite)
    row = probe.run([request])[0]
    data = copy.deepcopy(facts(row))
    tree = [["rel","members"]]
    for i in range(7):
        candidate = tree + [["select",i,[["eq",["v","\U0001f642"*12],["v","\U0001f642"*12]]]]]
        if len(model.canonical(answer(candidate))) > 1800:
            break
        tree = candidate
    assert 1400 <= len(model.canonical(answer(tree))) <= 1800
    data["proof"]["tree"] = tree
    data["proof"]["steps"] = 8
    data["proof"]["baseline_cells"] = 49152
    data["public"] = {"trace":[[i,256,12] for i in range(16)], "cells":49152}
    data["fixtures"] = [{"id":str(i).rjust(12,"a"),"header":"f"*64,"relation":"f"*64} for i in range(4)]
    # Deliberately a schema/budget fixture, not a claim this trace arose from
    # the supplied exercise. Semantic fact verification belongs to the lesson.
    assert len(model.canonical(data)) < 4096
    patched = probe.run([request | {"data_patch":data}])[0]
    assert not patched.get("load_or_contract_error")
    assert len(model.canonical(patched["outcome"])) < 5120
    expected_namespace = namespace(selected, probe.ENGINE, engine, {"seed":request["seed"],"options":{},"references":[]})
    validate_outcome(patched["outcome"], selected, engine, expected_namespace)
    oversized = copy.deepcopy(data)
    oversized["proof"]["tree"] = (oversized["proof"]["tree"] * 4)[:17]
    assert probe.run([request | {"data_patch":oversized}])[0]["load_or_contract_error"]
    bad = copy.deepcopy(patched["outcome"]); bad["data"] = oversized
    with pytest.raises(PluginError): validate_outcome(bad, selected, engine, expected_namespace)

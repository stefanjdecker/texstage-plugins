# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel M2 checks against the independent design oracle."""
from collections import Counter
import copy
import hashlib
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys

import pytest
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import validate_outcome

ROOT = Path(__file__).resolve().parents[3]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "maintenance" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


probe = module("transaction_engine_probe")
oracle = module("check_transaction_design")


@pytest.fixture(scope="module")
def provider():
    providers = discover()
    assert {p.id for p in providers} == {probe.PROVIDER}, "Use an engine-only environment."
    assert probe.PACKAGE not in sys.modules, "Discovery must not import the provider."
    selected, _ = probe.installed()
    assert not (selected.root / probe.PACKAGE).is_relative_to(ROOT / "plugins/transaction-engine")
    return selected


@pytest.fixture(scope="module")
def counter(provider):
    return probe.fixture(provider, "counter.exercise.json")


def facts(row):
    assert not row.get("load_or_contract_error"), row
    assert row["result"]["status"] == "ok", row
    assert row["reuseRefused"] and row["disposalRefused"]
    assert row["milliseconds"] < 2000
    data = row["result"]["data"]
    assert json.loads(row["result"]["canonical"]) == data
    assert row["outcome"]["data"] == data
    return data


def check_analysis(exercise, order, data):
    expected = oracle.analyze(exercise, order)
    assert data["valid"] is True and data["order"] == order
    assert data["vertices"] == sorted(t["id"] for t in exercise["transactions"])
    assert data["final"] == expected["final"] and data["reads"] == expected["reads"]
    assert [[e["from"], e["to"]] for e in data["edges"]] == expected["edges"]
    ops = {op["id"]: op | {"transaction": t["id"]} for t in exercise["transactions"] for op in t["operations"]}
    witnesses = []
    for edge in data["edges"]:
        assert edge["witnesses"] == sorted(edge["witnesses"])
        for a, b in edge["witnesses"]:
            assert ops[a]["transaction"] == edge["from"] and ops[b]["transaction"] == edge["to"]
            witnesses.append([a, b])
    assert sorted(witnesses) == sorted(expected["conflicts"])
    assert data["acyclic"] == expected["csr"]
    if data["acyclic"]:
        assert data["serial_order"] in expected["serial_orders"] and data["cycle"] == []
    else:
        cycle = data["cycle"]
        assert data["serial_order"] == [] and cycle[0] == cycle[-1]
        assert len(set(cycle[:-1])) == len(cycle) - 1
        assert all([a, b] in expected["edges"] for a, b in zip(cycle, cycle[1:]))
    values, reads, replay = dict(exercise["initial"]), {}, []
    for step, oid in zip(data["trace"], order, strict=True):
        assert step["operation"] == oid
        op = ops[oid]
        if op["kind"] == "read":
            reads[oid] = step["value"]
        elif op["kind"] == "write":
            values[op["object"]] = step["value"]
        else:
            assert set(step) == {"operation"}
        replay.append({"operation": oid, "values": dict(values), "reads": dict(reads)})
    assert replay == expected["trace"]
    return expected


def test_hand_checked_cases_and_fixture_parity(provider, counter):
    cases = probe.fixture(provider, "cases.json")["cases"]
    assert cases == json.loads((oracle.ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert counter == json.loads((oracle.ROOT / "counter.exercise.json").read_text(encoding="utf-8"))
    packaged = json.loads(provider.resources[f"{probe.PACKAGE}/schemas/exercise-v1.json"])
    assert packaged == oracle.SCHEMA
    requests = []
    for case in cases:
        exercise = case.get("exercise", counter)
        requests.append(probe.request(exercise, case.get("schedule")))
    rows = probe.run(requests)
    assert len(rows) == 9
    for case, row in zip(cases, rows, strict=True):
        exercise = case.get("exercise", counter)
        data = facts(row)
        expected = check_analysis(exercise, case.get("schedule", exercise["schedule"]), data)
        for key, value in case["expected"].items():
            assert expected[key] == value, (case["id"], key)
        if "cycle" in case["expected"]:
            assert data["cycle"] == case["expected"]["cycle"]
    assert len({rows[i]["result"]["canonical"] for i in [1, 2, 3]}) == 3
    same_final = cases[-1]["exercise"]
    serial = oracle.analyze(same_final, oracle.serial_schedule(same_final, ["T2", "T1"]))
    assert facts(rows[-1])["final"] == serial["final"]
    assert not facts(rows[-1])["acyclic"] and serial["csr"]


def test_every_legal_small_interleaving(provider, counter):
    cases = probe.fixture(provider, "cases.json")["cases"]
    exercises = {counter["id"]: counter}
    exercises.update({c["exercise"]["id"]: c["exercise"] for c in cases if "exercise" in c})
    pairs = []
    for exercise in exercises.values():
        programs = [[op["id"] for op in t["operations"]] for t in exercise["transactions"]]
        pairs.extend((exercise, order) for order in oracle.interleavings(programs))
    assert len(exercises) == 6 and len(pairs) == 1742
    rows = probe.run([probe.request(e, order) for e, order in pairs], timeout=45)
    assert len(rows) == len(pairs)
    counts = Counter()
    for (exercise, order), row in zip(pairs, rows, strict=True):
        data = facts(row)
        check_analysis(exercise, order, data)
        if exercise["id"] == counter["id"]:
            counts[data["acyclic"], data["final"]["x"]] += 1
    assert counts == {(True, 120): 8, (False, 110): 12}


@pytest.mark.parametrize("order,reasons", [
    ([], ["missing-operation"]),
    (["a1", "b1", "a2", "b2", "a3"], ["missing-operation"]),
    (["a1", "b1", "a2", "b2", "a3", "a3"], ["duplicate-operation", "missing-operation"]),
    (["a1", "b1", "a2", "b2", "a3", "unknown"], ["unknown-operation", "missing-operation"]),
    (["a2", "b1", "a1", "b2", "a3", "b3"], ["program-order"]),
    (["a1", "a3", "a2", "b1", "b2", "b3"], ["program-order"]),
    (["unknown"] * 30, ["unknown-operation", "duplicate-operation", "missing-operation"]),
])
def test_invalid_orders_have_feedback_without_analysis(counter, order, reasons):
    data = facts(probe.run([probe.request(counter, order)])[0])
    assert data["valid"] is False and data["reasons"] == reasons
    assert set(data) == {"format", "exercise", "order", "valid", "reasons"}


@pytest.mark.parametrize("text", [
    "", "null", "{}", "[]", '{"order":null}', '{"order":"a1"}',
    '{"order":["A1"]}', '{"order":[1]}', '{"order":[],"extra":0}',
    '{"order":[],"order":[]}', '{"order":[],"or\\u0064er":[]}',
    '{"order":[],}', '{"order":[] trailing}', '{"order":[true]}',
    '{"order":["a1",]}', '{"order":[NaN]}', '{"order":[Infinity]}',
    '{"order":[01]}', '{"order":[1e9999]}', '{"order":["bad\\q"]}',
    '{"order":["control\u0001"]}', '{"order":[]}' + '[]',
    '[' * 18 + '0' + ']' * 18, json.dumps({"order": ["a1"] * 31}),
    json.dumps({"order": ["a" * 13]}),
])
def test_malformed_answers(counter, text):
    row = probe.run([probe.request(counter) | {"text": text}])[0]
    assert row.get("result") == {"status": "syntax"}, row
    assert row["outcome"] == {"status": "syntax"}


def test_input_and_seed_budgets(counter):
    seed = json.dumps(counter)
    unicode_seed = copy.deepcopy(counter)
    unicode_seed["title"]["en"] = "😀" * 600
    unicode_seed = json.dumps(unicode_seed, ensure_ascii=False) + " " * 30000
    requests = [
        probe.request(counter) | {"text": " " * 2001},
        probe.request(counter) | {"text": 42},
        probe.request(counter) | {"seed": seed + " " * 32768},
        probe.request(counter) | {"seed": unicode_seed},
        probe.request(counter) | {"seed": seed[:-1] + ',"id":"counter"}'},
        probe.request(counter) | {"options": {"unexpected": 1}},
        probe.request(counter) | {"options": None},
    ]
    rows = probe.run(requests)
    assert [r.get("result") for r in rows[:2]] == [{"status": "refused"}] * 2
    assert all(r.get("load_or_contract_error") for r in rows[2:])
    # Whitespace at the documented answer boundary remains legal.
    good = probe.request(counter)
    good["text"] = good["text"].ljust(2000)
    assert facts(probe.run([good])[0])["valid"]
    # The byte limit is exact, including insignificant seed whitespace.
    good = probe.request(counter) | {"seed": seed.ljust(32768)}
    assert facts(probe.run([good])[0])["valid"]


def changed(exercise, path, value):
    result = copy.deepcopy(exercise)
    target = result
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    return result


@pytest.mark.parametrize("path,value", [
    (["format"], 2), (["format"], True), (["id"], "BAD"),
    (["language"], "fr"), (["title", "en"], ""), (["prompt", "de"], "x" * 601),
    (["initial", "x"], 1000001), (["initial", "x"], -1000001),
    (["initial", "x"], 1.1), (["initial", "x"], True),
    (["transactions", 1, "id"], "T1"), (["transactions", 0, "id"], ["T1"]),
    (["transactions", 0, "operations", 0, "object"], "unknown"),
    (["transactions", 0, "operations", 1, "value"], {"read": "b1", "add": 10}),
    (["transactions", 0, "operations", 1, "value"], {"read": "a3", "add": 10}),
    (["transactions", 0, "operations", 1, "value"], {"read": "a1", "add": 10001}),
    (["transactions", 0, "operations", 1, "value"], {"constant": True}),
    (["transactions", 0, "operations", 1, "value"], {"constant": -1000001}),
    (["transactions", 0, "operations", 1, "value"], {"constant": 10, "read": "a1", "add": 0}),
    (["transactions", 0, "operations", 1, "id"], "a1"),
    (["transactions", 0, "operations", 0], {"id": "a1", "kind": "commit"}),
    (["transactions", 0, "operations", 2], {"id": "a3", "kind": "read", "object": "x"}),
    (["transactions", 0, "operations", 2], {"id": "a3", "kind": "commit", "object": "x"}),
    (["schedule"], ["a2", "a1", "a3", "b1", "b2", "b3"]),
    (["task", "repair"], "same-final-value"),
    (["unexpected"], 1),
])
def test_invalid_exercises_fail_initialization(counter, path, value):
    row = probe.run([probe.request(changed(counter, path, value))])[0]
    assert row.get("load_or_contract_error"), row


def test_semantic_identity_and_fresh_state(counter):
    localized = copy.deepcopy(counter)
    localized["language"] = "en"
    localized["title"]["en"] = "Another title"
    localized["prompt"]["de"] = "Neue Frage"
    reordered = dict(reversed(list(counter.items())))
    reordered["transactions"] = list(reversed(counter["transactions"]))
    altered = changed(counter, ["initial", "x"], 101)
    alternate_seed = copy.deepcopy(counter)
    alternate_seed["schedule"] = ["a1", "a2", "a3", "b1", "b2", "b3"]
    requests = [probe.request(e, counter["schedule"]) for e in [counter, localized, reordered, altered, alternate_seed, counter]]
    requests[1]["context"] = {"language": "de", "actor": "other", "timestamp": 123, "job": "different"}
    rows = probe.run(requests)
    assert rows[0]["result"]["canonical"] == rows[1]["result"]["canonical"] == rows[2]["result"]["canonical"]
    assert rows[0]["result"] == rows[5]["result"]
    assert facts(rows[0])["exercise"] != facts(rows[3])["exercise"] != facts(rows[4])["exercise"]
    assert facts(rows[3])["final"]["x"] == 111 and facts(rows[5])["final"]["x"] == 110
    semantic = {key: counter[key] for key in ["format", "id", "initial", "transactions", "schedule"]}
    expected = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert facts(rows[0])["exercise"] == expected


def test_sha256_without_web_crypto():
    vectors = ["", "abc", "Grüße 😀", *["a" * n for n in [55, 56, 63, 64, 65, 127, 128, 32768]]]
    rows = probe.run([{"hash": text} for text in vectors])
    assert [r["hash"] for r in rows] == [hashlib.sha256(t.encode()).hexdigest() for t in vectors]


def maximum_exercise(counter, mode):
    result = copy.deepcopy(counter)
    result["initial"] = {"counterxxxxx": 1000000, "constructor": -1000000, "zxxxxxxxxxxx": 0}
    transactions = []
    for number in range(3):
        prefix = chr(97 + number)
        ops = []
        for i in range(4):
            oid = f"{prefix}{i:011d}"
            if mode == "writes":
                op = {"id": oid, "kind": "write", "object": "counterxxxxx", "value": {"constant": (-1)**i * 1000000}}
            elif i % 2 == 0:
                op = {"id": oid, "kind": "read", "object": "counterxxxxx"}
            else:
                op = {"id": oid, "kind": "write", "object": "counterxxxxx",
                      "value": {"read": f"{prefix}{i-1:011d}", "add": 10000}}
            ops.append(op)
        ops.append({"id": f"{prefix}commitxxxxx", "kind": "commit"})
        transactions.append({"id": f"T{number+1}", "operations": ops})
    result["transactions"] = transactions
    result["schedule"] = [t["operations"][i]["id"] for i in range(5) for t in transactions]
    return result


@pytest.mark.parametrize("mode", ["writes", "reads"])
def test_maximum_exercises_and_result_budgets(counter, mode):
    exercise = maximum_exercise(counter, mode)
    orders = [exercise["schedule"], *[
        oracle.serial_schedule(exercise, p) for p in permutations(["T1", "T2", "T3"])]]
    rows = probe.run([probe.request(exercise, order) for order in orders])
    for order, row in zip(orders, rows, strict=True):
        data = facts(row)
        check_analysis(exercise, order, data)
        assert len(json.dumps(data, separators=(",", ":")).encode()) <= 8192
        assert len(json.dumps(row["outcome"], separators=(",", ":")).encode()) <= 12288
    if mode == "writes":
        assert sum(len(e["witnesses"]) for e in facts(rows[0])["edges"]) == 48
    # Thirteenth read/write operation is refused even with a legal schedule.
    extra = {"id": "extra", "kind": "read", "object": "counterxxxxx"}
    exercise["transactions"][0]["operations"].insert(-1, extra)
    exercise["schedule"].insert(exercise["schedule"].index("acommitxxxxx"), "extra")
    assert probe.run([probe.request(exercise)])[0].get("load_or_contract_error")


def test_host_contract_rejects_mutated_results(counter):
    row = probe.run([probe.request(counter)])[0]
    provider, engine = probe.installed()
    expected_namespace = row["outcome"]["namespace"]
    validate_outcome(row["outcome"], provider, engine, expected_namespace)
    for path, value in [
        (["data", "acyclic"], "false"),
        (["data", "final", "x"], 1120001),
        (["data", "cycle"], []),
        (["data", "unexpected"], 1),
        (["namespace"], "wrong"),
    ]:
        with pytest.raises(PluginError):
            validate_outcome(changed(row["outcome"], path, value), provider, engine, expected_namespace)


def test_process_deadline(counter):
    with pytest.raises(subprocess.TimeoutExpired):
        probe.run([probe.request(counter)], timeout=0.001)

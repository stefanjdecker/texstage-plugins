# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel N1/N2 checks; no provider source imports."""
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import time

import pytest
from jsonschema import Draft202012Validator
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import validate_portable_schema, validate_outcome
from texstage_normalization_workshop import model, validation as v

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("normalization_probe", ROOT / "maintenance/normalization_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture(scope="module", autouse=True)
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, "Use a normalization-only installed-wheel environment."
    p, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    assert not Path(model.__file__).is_relative_to(ROOT / "plugins/normalization-workshop")
    subprocess.run([sys.executable, "-c", "import sys; from texstage.plugins.catalog import discover; discover(); assert 'texstage_normalization_workshop' not in sys.modules"], check=True)
    return p


def mask(letters, attrs):
    return sum(1 << attrs.index(a) for a in letters)


def seed_for(case, mode="decompose"):
    attrs = list(case["attributes"])
    fds = sorted({(mask(x, attrs), mask(a, attrs)) for x, y in case["fds"] for a in y if a not in x})
    return {"format": 1, "id": case["id"].replace("-", "_"), "attributes": attrs,
            "fds": [list(x) for x in fds],
            "task": {"mode": mode} if mode == "classify" else {"mode": mode, "target": "bcnf", "preserve": False}}


def cases(provider):
    return probe.fixture(provider, "expected-cases.json")["cases"]


def answer(parts):
    return {"mode": "decompose", "relations": parts}


def analyze_rows(requests):
    rows = probe.run(requests, timeout=120)
    for req, row in zip(requests, rows, strict=True):
        assert not row.get("load_or_contract_error"), row
        assert row["result"]["status"] == "ok", row
        exercise, submitted = json.loads(req["seed"]), json.loads(req["text"])
        expected = model.analyze(exercise, submitted)
        assert expected == row["result"]["data"] == row["outcome"]["data"]
        assert model.verify_analysis(exercise, submitted, expected)
        assert row["reuseRefused"] and row["disposalRefused"]
        assert row["milliseconds"] < 2000
    return rows


def test_hand_derived_cases(provider):
    requests = []
    for case in cases(provider):
        seed = seed_for(case)
        submitted = answer([mask(p, case["attributes"]) for p in case["relations"]])
        data = model.analyze(seed, submitted)["facts"]
        expected = case["expected"]
        assert data["covered"] == expected["covered"]
        assert (data["join"]["lossless"] if data["join"] else None) == expected["lossless"]
        assert (data["preservation"]["preserved"] if data["preservation"] else None) == expected["preserved"]
        by_relation = {mask(p, case["attributes"]): f for p, f in zip(case["relations"], expected["component_forms"], strict=True)}
        assert [c["normal_form"] for c in data["components"]] == [by_relation[c["relation"]] for c in data["components"]]
        theory = model.Theory(v.seed(seed))
        description, keys = theory.describe(theory.universe)
        assert set(keys) == {mask(k, case["attributes"]) for k in expected["keys"]}
        assert description["normal_form"] == expected["normal_form"]
        for x, y in expected["closures"].items():
            assert theory.closures[mask(x, case["attributes"])] == mask(y, case["attributes"])
        requests.append(probe.request(seed, submitted))
    analyze_rows(requests)


@pytest.mark.parametrize("filename", ["registration.lesson.draft.json", "tutor.lesson.draft.json"])
def test_named_lesson_compilation(provider, filename):
    lesson = probe.fixture(provider, filename)
    checked = model.check_lesson(lesson)
    assert model.accepted(checked["seed"], checked["answer"], checked["analysis"]["facts"])
    bad = copy.deepcopy(lesson)
    bad["worked_answer"]["relations"] = [1]
    with pytest.raises(v.InputError, match="incorrect-worked-answer"):
        model.check_lesson(bad)
    bad = copy.deepcopy(lesson)
    bad["exercise"]["fds"][0]["lhs"] = ["missing"]
    with pytest.raises(v.InputError):
        model.check_lesson(bad)
    bad = copy.deepcopy(lesson)
    bad["exercise"]["attributes"][1]["id"] = bad["exercise"]["attributes"][0]["id"]
    with pytest.raises(v.InputError):
        model.check_lesson(bad)
    redundant = copy.deepcopy(lesson)
    redundant["exercise"]["fds"].extend([redundant["exercise"]["fds"][0], {"lhs": ["S"], "rhs": ["S"]}])
    result = model.check_lesson(redundant)
    assert result["seed"] == checked["seed"]
    assert set(result["diagnostics"]) == {"trivial-fd", "duplicate-fd"}


def test_normal_forms_and_witnesses(provider):
    requests = []
    for case in cases(provider):
        seed = seed_for(case, "classify")
        description, _ = model.Theory(v.seed(seed)).describe((1 << len(seed["attributes"])) - 1)
        form = description["normal_form"]
        witness = None if form == "bcnf" else description["witnesses"][{"1nf": "2nf", "2nf": "3nf", "3nf": "bcnf"}[form]]
        submitted = {"mode": "classify", "normal_form": form, "witness": witness}
        assert model.accepted(seed, submitted, model.analyze(seed, submitted)["facts"])
        requests.append(probe.request(seed, submitted))
        wrong = submitted | {"normal_form": "bcnf" if form != "bcnf" else "1nf", "witness": [0, 1]}
        assert not model.accepted(seed, wrong, model.analyze(seed, wrong)["facts"])
        requests.append(probe.request(seed, wrong))
    analyze_rows(requests)


def test_alternate_answers_and_projection(provider):
    seed = seed_for(cases(provider)[2])
    a, b = answer([3, 6]), answer([5, 3])
    first, second = analyze_rows([probe.request(seed, a), probe.request(seed, b)])
    assert model.accepted(seed, a, first["result"]["data"]["facts"])
    assert model.accepted(seed, b, second["result"]["data"]["facts"])  # preserve is optional here
    assert first["outcome"]["key"] != second["outcome"]["key"]
    strict = seed | {"task": {"mode": "decompose", "target": "bcnf", "preserve": True}}
    assert not model.accepted(strict, b, model.analyze(strict, b)["facts"])
    ordered = probe.run([probe.request(seed, answer([6, 3]))])[0]
    assert ordered["result"] == first["result"]
    # Different keys need not have the same size: A -> BC, BC -> A.
    theory = model.Theory({"format": 1, "id": "unequal", "attributes": list("ABC"),
                           "fds": [[1, 2], [1, 4], [6, 1]], "task": {"mode": "classify"}})
    assert theory.describe(7)[1] == [1, 6]


def check_counterexample(seed, facts):
    join = facts["join"]
    if join is None or join["lossless"]:
        return
    table = join["tableau"]
    n = len(seed["attributes"])
    assert list(range(n)) not in table
    for lhs, rhs in seed["fds"]:
        xs = [i for i in range(n) if lhs & (1 << i)]
        col = rhs.bit_length() - 1
        for a, b in itertools.product(table, repeat=2):
            assert not all(a[j] == b[j] for j in xs) or a[col] == b[col]
    for component in facts["components"]:
        xs = [i for i in range(n) if component["relation"] & (1 << i)]
        assert any(all(row[j] == j for j in xs) for row in table)


def test_counterexamples_and_tamper_detection(provider):
    for case in cases(provider):
        seed = seed_for(case)
        submitted = answer([mask(p, case["attributes"]) for p in case["relations"]])
        data = model.analyze(seed, submitted)
        check_counterexample(seed, data["facts"])
        patches = [{"exercise": "0" * 64}, {"answer": "0" * 64}, {"mode": "classify"}]
        for patch in patches:
            assert not model.verify_analysis(seed, submitted, data | patch)
        tampered = copy.deepcopy(data)
        tampered["facts"]["covered"] = not tampered["facts"]["covered"]
        assert not model.verify_analysis(seed, submitted, tampered)
        if data["facts"]["join"]:
            for field in ("lossless", "tableau", "merges"):
                tampered = copy.deepcopy(data)
                j = tampered["facts"]["join"]
                if field == "lossless": j[field] = not j[field]
                elif field == "tableau": j[field][0][0] = 71
                else: j[field].append([0, 0, 0])
                assert not model.verify_analysis(seed, submitted, tampered)


@pytest.mark.parametrize("text", [
    '{"mode":"decompose","mode":"decompose","relations":[3,6]}',
    '{"mode":"decompose","relations":[3.0,6]}',
    '{"mode":"decompose","relations":[3e0,6]}',
    '{"mode":"decompose","relations":[true,6]}',
    '{"mode":"decompose","relations":[3,3]}',
    '{"mode":"decompose","relations":[0]}',
    '{"mode":"decompose","relations":[8]}',
    '{"mode":"decompose","relations":[-1]}',
    '{"mode":"decompose","relations":[NaN]}',
    '{"mode":"decompose","relations":[3,6],"extra":1}',
    '{"mode":"classify","normal_form":"bcnf","witness":null}',
    '{"mode":"decompose","relations":[3,6],"\\ud800":1}',
    '[]', 'null', '{}', '{"mode":"decompose","relations":[]}', '{"relations":[3,6]',
])
def test_malformed_answers(provider, text):
    seed = seed_for(cases(provider)[2])
    row = probe.run([probe.request(seed, answer([3, 6]), text=text)])[0]
    assert row["result"] == {"status": "syntax"}, row
    with pytest.raises(v.InputError):
        v.answer(v.parse(text), seed)


def test_resource_guards_and_seed_validation(provider):
    seed = seed_for(cases(provider)[2])
    rows = probe.run([probe.request(seed, answer([3, 6]), text=" " * 2001),
                      probe.request(seed, answer([3, 6]), text="[" * 20 + "0" + "]" * 20),
                      probe.request(seed, answer([3, 6]), direct=True, work_limit=0)])
    assert rows[0]["result"] == rows[1]["result"] == {"status": "refused"}
    assert rows[2]["error"] == "ResourceLimit"
    with pytest.raises(v.ResourceLimit):
        model.analyze(seed, answer([3, 6]), model.Budget(0))
    bad = []
    for key, value in [("format", True), ("format", 1.0), ("attributes", ["A", "A"]),
                       ("fds", [[2, 4], [1, 2]]), ("fds", [[1, 2], [1, 2]]),
                       ("fds", [[1, 3]]), ("fds", [[1, 1]]), ("fds", [[8, 2]])]:
        invalid = seed | {key: value}
        bad.append(probe.request(invalid, answer([3, 6])))
        with pytest.raises(v.InputError):
            v.seed(invalid)
    bad.append(probe.request(seed, answer([3, 6]), options={"extra": True}))
    assert all(row.get("load_or_contract_error") for row in probe.run(bad))


def test_transport_schema_and_binding(provider):
    seed = seed_for(cases(provider)[0])
    submitted = answer([3, 5, 28, 48])
    requests = [probe.request(seed, submitted)]
    requests += [probe.request(seed, submitted, data_patch=patch) for patch in
                 ({"extra": 1}, {"format": 2}, {"mode": "classify"}, {"exercise": ""}, {"facts": {}})]
    rows = probe.run(requests)
    assert rows[0]["result"]["status"] == "ok"
    assert all(row.get("load_or_contract_error") for row in rows[1:])
    p, engine = probe.installed()
    with pytest.raises(PluginError):
        validate_outcome(rows[0]["outcome"], p, engine, "foreign")
    assert probe.run([{"hash": "abc"}])[0]["hash"] == hashlib.sha256(b"abc").hexdigest()


def test_exhaustive_three_attribute_theories():
    possible = [[left, 1 << right] for left in range(8) for right in range(3) if not left & (1 << right)]
    pairs = [list(pair) for pair in itertools.combinations(range(1, 8), 2) if pair[0] | pair[1] == 7]
    pending, expected = [], []
    count = 0
    def flush():
        nonlocal count
        rows = probe.run(pending, timeout=120)
        assert [r.get("digest") for r in rows] == expected
        count += len(rows)
        pending.clear(); expected.clear()
    for selection in range(1 << len(possible)):
        exercise = {"format": 1, "id": "tiny", "attributes": list("ABC"),
                    "fds": [f for i, f in enumerate(possible) if selection & (1 << i)],
                    "task": {"mode": "classify"}}
        theory = model.Theory(exercise)
        desc, keys = theory.describe(7)
        for x in range(8):
            c = theory.closures[x]
            assert model.subset(x, c) and theory.closures[c] == c
            assert (c == 7) == any(model.subset(k, x) for k in keys)
            for y in range(8):
                if model.subset(x, y): assert model.subset(c, theory.closures[y])
        variants = [(exercise, {"mode": "classify", "normal_form": "bcnf", "witness": None})]
        decompose = exercise | {"task": {"mode": "decompose", "target": "bcnf", "preserve": False}}
        variants.extend((decompose, answer(pair)) for pair in pairs)
        for seed, submitted in variants:
            data = model.analyze(seed, submitted)
            if submitted["mode"] == "decompose":
                a, b = submitted["relations"]
                closure = theory.closures[a & b]
                assert data["facts"]["join"]["lossless"] == (model.subset(a, closure) or model.subset(b, closure))
            pending.append(probe.request(seed, submitted, direct=True))
            expected.append(hashlib.sha256(v.canonical(data).encode("ascii")).hexdigest())
        if len(pending) >= 2000: flush()
    if pending: flush()
    assert count == 53248


def test_large_seeded_cases_and_verifier_deadline():
    rng = random.Random(20261106)
    requests, timings, budgets = [], [], []
    for index in range(120):
        n = 4 + index % 5
        universe = (1 << n) - 1
        pool = [[x, 1 << j] for x in range(universe + 1) for j in range(n) if not x & (1 << j)]
        fds = sorted(rng.sample(pool, min(index % 33, len(pool))))
        seed = {"format": 1, "id": "seeded", "attributes": list("ABCDEFGH"[:n]),
                "fds": fds, "task": {"mode": "decompose", "target": "bcnf", "preserve": False}}
        parts = sorted(rng.sample(range(1, universe + 1), 1 + index % 8))
        submitted = answer(parts)
        budget = model.Budget()
        data = model.analyze(seed, submitted, budget)
        check_counterexample(seed, data["facts"])
        began = time.perf_counter()
        assert model.verify_analysis(seed, submitted, data)
        timings.append((time.perf_counter() - began) * 1000)
        budgets.append(budget.used)
        requests.append(probe.request(seed, submitted))
    rows = analyze_rows(requests)
    assert max(timings) < 250
    report = {"cases": len(rows), "max_python_verification_ms": max(timings),
              "max_python_work": max(budgets), "max_node_with_contract_ms": max(r["milliseconds"] for r in rows)}
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/normalization-limits.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

def test_equivalent_dependencies_and_attribute_permutation(provider):
    base = {"format": 1, "id": "equivalent", "attributes": list("ABCD"),
            "fds": [[1, 2], [2, 4]], "task": {"mode": "classify"}}
    submitted = {"mode": "classify", "normal_form": "1nf", "witness": [1, 2]}
    redundant = base | {"fds": [[1, 2], [1, 4], [2, 4]]}
    original = model.analyze(base, submitted)
    assert original["facts"] == model.analyze(redundant, submitted)["facts"]
    order = [2, 0, 3, 1]
    def renamed(mask):
        return sum(1 << order[i] for i in range(4) if mask & (1 << i))
    attrs = [None] * 4
    for i, name in enumerate(base["attributes"]): attrs[order[i]] = name
    permuted = base | {"attributes": attrs,
                      "fds": sorted([[renamed(x), renamed(a)] for x, a in base["fds"]])}
    moved = submitted | {"witness": [renamed(x) for x in submitted["witness"]]}
    result = model.analyze(permuted, moved)
    assert original["facts"]["normal_form"] == result["facts"]["normal_form"]
    assert renamed(original["facts"]["prime"]) == result["facts"]["prime"]
    assert sorted(renamed(k) for k in original["facts"]["keys"]) == result["facts"]["keys"]
    assert result["facts"]["witness_valid"]
    analyze_rows([probe.request(base, submitted), probe.request(redundant, submitted), probe.request(permuted, moved)])
    for bad in ([], None, {"x": float("nan")}, {"x": object()}, {"x": "\ud800"}):
        assert not model.verify_analysis(base, submitted, bad)
    data = model.analyze(base, submitted)
    tampered = copy.deepcopy(data)
    tampered["facts"]["keys"] = []
    assert not model.verify_analysis(base, submitted, tampered)
    tampered = copy.deepcopy(data)
    tampered["facts"]["witness_valid"] = False
    assert not model.verify_analysis(base, submitted, tampered)

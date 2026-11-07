# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel contracts, independent expected facts and bag-semantics evidence."""
import collections
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import sys
import time

import pytest
from jsonschema import Draft202012Validator
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import validate_outcome, validate_portable_schema
from texstage.plugins import PluginError
from texstage_query_plan import model
import texstage_query_plan

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "maintenance"))
import query_plan_probe as probe

PROVIDER, ENGINE = probe.installed()
EXERCISES = probe.fixture(PROVIDER, "exercises.json")
CASES = probe.fixture(PROVIDER, "expected-cases.json")
ANSWERS = {c["id"]: c["answer"] for c in CASES["cases"]}


def facts(row):
    assert "load_or_contract_error" not in row, row
    assert row["result"]["status"] == row["outcome"]["status"] == "ok"
    assert row["reuseRefused"] and row["disposalRefused"]
    result = row["result"]["data"]
    assert row["result"]["canonical"] == model.canonical(result)
    assert result == row["outcome"]["data"]
    assert len(model.canonical(result)) <= 8192
    assert len(model.canonical(row["outcome"])) <= 12288
    return result


def test_installed_wheel_and_metadata_discovery():
    assert Path(texstage_query_plan.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    assert {p.id for p in discover()} == {probe.PROVIDER}
    assert set(PROVIDER.manifest["capabilities"]["content_types"]) == {probe.PROVIDER + ".challenge"}
    spec = PROVIDER.manifest["capabilities"]["content_types"][probe.PROVIDER + ".challenge"]
    assert spec["authoring_hook"] == "challenge" and spec["state_schema"] == 4
    assert "participant-input" in spec["views"]
    assert "texstage_query_plan.model" not in PROVIDER.manifest.get("resources", {})
    PROVIDER.verify()
    assert importlib.metadata.version("texstage-query-plan") == "0.6.0"
    for resource in PROVIDER.resources:
        assert not resource.startswith(("/", "C:", "../"))
    for name in ("exercise", "answer", "lesson", "analysis-result"):
        schema = json.loads(PROVIDER.resources[f"texstage_query_plan/schemas/{name}-v1.json"])
        Draft202012Validator.check_schema(schema)
    validate_portable_schema(json.loads(PROVIDER.resources[
        "texstage_query_plan/schemas/analysis-result-v1.json"]))
    # Run discovery in a clean interpreter: it must not execute the provider factory.
    import subprocess
    text = subprocess.check_output([sys.executable, "-c",
        "import sys; from texstage.plugins.catalog import discover; "
        "assert len(discover()) == 1; assert 'texstage_query_plan' not in sys.modules"],
        text=True)
    assert text == ""


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: c["id"])
def test_hand_derived_cases(case):
    exercise, answer = EXERCISES[case["exercise"]], case["answer"]
    result = facts(probe.run([probe.request(exercise, answer)])[0])
    assert result == model.analyze(exercise, answer)
    assert result["valid"] == case["expect"]["valid"]
    if result["valid"]:
        assert result["cost"] == case["expect"]["cost"]
    else:
        assert result["reason"] == case["expect"]["reason"]
        assert "cost" not in result and "nodes" not in result


@pytest.mark.parametrize("name", sorted(EXERCISES))
def test_exhaustive_candidates(name):
    exercise = EXERCISES[name]
    candidates = list(model.candidates(exercise))
    assert len({model.canonical(a) for a in candidates}) == len(candidates) <= 864
    results = probe.run([probe.request(exercise, a) for a in candidates])
    valid = []
    for answer, row in zip(candidates, results, strict=True):
        data = facts(row)
        assert data == model.analyze(exercise, answer)
        if data["valid"]:
            valid.append(data["cost"])
    expected = CASES["optima"][name]
    assert min(valid) == expected["cost"]
    assert len(valid) == expected["feasible"]
    assert valid.count(min(valid)) == expected["count"]
    optimum = model.optimum(exercise)
    assert (optimum["cost"], optimum["count"], optimum["feasible"]) == (
        expected["cost"], expected["count"], expected["feasible"])
    assert model.analyze(exercise, optimum["plan"])["cost"] == expected["cost"]


def test_both_best_answers_have_distinct_keys():
    exercise = EXERCISES["tie"]
    rows = probe.run([probe.request(exercise, ANSWERS["tie-seq"]),
                      probe.request(exercise, ANSWERS["tie-index"])])
    assert facts(rows[0])["cost"] == facts(rows[1])["cost"] == 4810
    assert rows[0]["outcome"]["key"] != rows[1]["outcome"]["key"]


def changed_source(case):
    e = copy.deepcopy(EXERCISES["library"])
    if case == "bool-rows": e["statistics"]["base"][0]["rows"] = True
    if case == "float-rows": e["statistics"]["base"][0]["rows"] = 10000.0
    if case == "duplicate-relation": e["query"]["relations"][1]["id"] = "books"
    if case == "duplicate-column": e["query"]["relations"][0]["columns"].append(e["query"]["relations"][0]["columns"][0])
    if case == "array-id": e["query"]["relations"][0]["id"] = ["books"]
    if case == "linebreak-id": e["query"]["relations"][0]["id"] = "books\n"
    if case == "bad-filter-type": e["query"]["relations"][0]["filter"]["value"] = True
    if case == "decomposed-text": e["query"]["relations"][0]["filter"]["value"] = "e\u0301"
    if case == "bad-index": e["query"]["relations"][0]["index"]["column"] = "book_id"
    if case == "index-no-filter": del e["query"]["relations"][0]["filter"]
    if case == "missing-stats": e["statistics"]["cardinalities"].pop()
    if case == "duplicate-stats": e["statistics"]["cardinalities"].append(e["statistics"]["cardinalities"][0])
    if case == "impossible-stats": e["statistics"]["cardinalities"][-1]["rows"] = 1000000
    if case == "unfiltered-stats": e["statistics"]["cardinalities"][2]["rows"] = 1
    if case == "zero-pages": e["statistics"]["base"][0]["pages"] = 0
    if case == "large-width": e["statistics"]["base"][0]["row_bytes"] = 1025
    if case == "large-memory": e["limits"]["hash_bytes"] = 16777217
    if case == "missing-column": e["query"]["output"][0][1] = "missing"
    if case == "wrong-join-type": e["query"]["joins"][0]["left"][1] = "topic"
    if case == "parallel-edge": e["query"]["joins"][1] = copy.deepcopy(e["query"]["joins"][0])
    if case == "self-edge": e["query"]["joins"][0]["right"] = copy.deepcopy(e["query"]["joins"][0]["left"])
    if case == "extra-field": e["cost"] = 0
    if case == "boolean-format": e["format"] = True
    if case == "wrong-model": e["model"] = "real-postgresql-cost"
    return e


BAD_SOURCES = ["bool-rows", "float-rows", "duplicate-relation", "duplicate-column", "array-id",
    "linebreak-id", "bad-filter-type", "decomposed-text", "bad-index", "index-no-filter",
    "missing-stats", "duplicate-stats", "impossible-stats", "unfiltered-stats", "zero-pages",
    "large-width", "large-memory", "missing-column", "wrong-join-type", "parallel-edge",
    "self-edge", "extra-field", "boolean-format", "wrong-model"]


@pytest.mark.parametrize("case", BAD_SOURCES)
def test_seed_rejection(case):
    exercise = changed_source(case)
    with pytest.raises((model.InputError, model.ResourceLimit)):
        model.source(exercise)
    row = probe.run([probe.request(exercise, ANSWERS["library-best"])])[0]
    assert row.get("load_or_contract_error"), row


BAD_TEXT = [
    "{", "null", "[]", '{"format":1,"format":1,"nodes":[]}',
    '{"format":1,"\\u0066ormat":1,"nodes":[]}',
    '{"format":1.0,"nodes":[]}', '{"format":1e0,"nodes":[]}',
    '{"format":NaN,"nodes":[]}', '{"format":Infinity,"nodes":[]}',
    '{"format":9007199254740992,"nodes":[]}', "["*18+"0"+"]"*18,
    '{"format":true,"nodes":[]}',
    '{"format":1,"nodes":[{"op":"scan","relation":["books"],"method":"seq"}]}',
    '{"format":1,"nodes":[{"op":"scan","relation":"books\\n","method":"seq"}]}',
    '{"format":1,"nodes":[{"op":"scan","relation":"books","method":["seq"]}]}',
    '{"format":1,"nodes":[{"op":"join","left":true,"right":0,"method":"nested"}]}',
    '{"format":1,"nodes":[{"op":"scan","relation":"books","method":"seq","cost":0}]}',
    '{"format":1,"nodes":[{"op":"scan","relation":"books","method":"bitmap"}]}',
    '{"format":1,"nodes":[{"op":"scan","relation":"\\ud800","method":"seq"}]}',
]


@pytest.mark.parametrize("text", BAD_TEXT)
def test_malformed_answers(text):
    with pytest.raises(model.InputError):
        model.answer(model.parse(text,2000))
    row = probe.run([probe.request(EXERCISES["selective"], ANSWERS["selective-seq"], text=text)])[0]
    assert row["outcome"] == {"status":"syntax"}, row


def test_budgets_and_options():
    request = probe.request(EXERCISES["selective"], ANSWERS["selective-seq"])
    for text in (" "*2001, json.dumps({"padding":"x"*1100})):
        row = probe.run([request | {"text":text}])[0]
        assert row["outcome"] == {"status":"refused"}
    for options in ([], None, "x", {"cost":0}):
        assert probe.run([request | {"options":options}])[0].get("load_or_contract_error")
    assert probe.run([request | {"seed":" "*32769}])[0].get("load_or_contract_error")
    assert probe.run([request | {"seed":'{"format":1,"format":1}'}])[0].get("load_or_contract_error")


def test_domain_topology_and_reference_errors():
    inputs = [
        ({"format":1,"nodes":[{"op":"join","left":0,"right":0,"method":"nested"}]}, "invalid-tree"),
        ({"format":1,"nodes":[{"op":"scan","relation":"unknown","method":"seq"}]}, "unknown-relation"),
        ({"format":1,"nodes":[{"op":"scan","relation":"a","method":"seq"},
          {"op":"scan","relation":"b","method":"seq"},
          {"op":"join","left":1,"right":0,"method":"nested"}]}, "invalid-tree"),
        ({"format":1,"nodes":[{"op":"scan","relation":"a","method":"seq"},
          {"op":"scan","relation":"b","method":"seq"}]}, "invalid-tree"),
    ]
    for (answer, reason), row in zip(inputs, probe.run([
            probe.request(EXERCISES["tiny"], answer) for answer,_ in inputs]),strict=True):
        data = facts(row)
        assert data == model.analyze(EXERCISES["tiny"],answer)
        assert not data["valid"] and data["reason"] == reason


def test_normalization_and_identity():
    exercise = copy.deepcopy(EXERCISES["library"])
    exercise["query"]["relations"].reverse()
    for relation in exercise["query"]["relations"]: relation["columns"].reverse()
    exercise["query"]["joins"].reverse()
    for join in exercise["query"]["joins"]: join["left"],join["right"] = join["right"],join["left"]
    exercise["statistics"]["base"].reverse()
    exercise["statistics"]["cardinalities"].reverse()
    for c in exercise["statistics"]["cardinalities"]: c["relations"].reverse()
    a = ANSWERS["library-best"]
    rows = probe.run([probe.request(e,a) for e in (EXERCISES["library"],exercise)])
    assert facts(rows[0]) == facts(rows[1])
    assert model.exercise_identity(exercise) == facts(rows[0])["exercise"]
    exercise["limits"]["hash_bytes"] -= 1
    assert model.exercise_identity(exercise) != facts(rows[0])["exercise"]
    vectors = ["", "abc", "\x7f", "é🙂", "x"*1000]
    assert [r["hash"] for r in probe.run([{"hash":v} for v in vectors])] == [
        hashlib.sha256(v.encode()).hexdigest() for v in vectors]


def test_memory_boundary_and_monotonicity():
    last = model.COST_MAX
    exercises = []
    for limit in (0,479,480,1024,3999,4000,96000,240000,1048576):
        e = copy.deepcopy(EXERCISES["library"])
        e["limits"]["hash_bytes"] = limit
        exercises.append(e)
        best = model.optimum(e)["cost"]
        assert best <= last
        last = best
    rows = probe.run([probe.request(x,ANSWERS["memory-best"]) for x in exercises])
    for exercise,row in zip(exercises,rows,strict=True):
        assert facts(row) == model.analyze(exercise,ANSWERS["memory-best"])
    e["limits"]["hash_bytes"] = 480
    accepted = model.analyze(e,ANSWERS["memory-best"])
    e["limits"]["hash_bytes"] = 479
    rejected = model.analyze(e,ANSWERS["memory-best"])
    assert accepted["valid"] and accepted["cost"] == 214330
    assert not rejected["valid"] and rejected["reason"] == "hash-memory"


def test_portable_results_and_namespace():
    exercise, answer = EXERCISES["library"], ANSWERS["library-best"]
    request = probe.bound_requests(PROVIDER,ENGINE,[probe.request(exercise,answer)])[0]
    row = probe.run([request])[0]
    validate_outcome(row["outcome"],PROVIDER,ENGINE,request["namespace"])
    with pytest.raises(PluginError):
        validate_outcome(row["outcome"],PROVIDER,ENGINE,"0"*64)
    for patch in ({"cost":-1},{"cost":True},{"cost":3000000000001},{"unexpected":1},
                  {"model":"wrong"},{"valid":False}):
        assert probe.run([request | {"data_patch":patch}])[0].get("load_or_contract_error")
    schema = json.loads(PROVIDER.resources["texstage_query_plan/schemas/analysis-result-v1.json"])
    Draft202012Validator(schema).validate(facts(row))


def maximum_exercise():
    e = copy.deepcopy(EXERCISES["library"])
    rename = {"books":"a"*16, "loans":"b"*16, "members":"c"*16}
    for r in e["query"]["relations"]:
        old = r["id"]
        r["id"] = rename[old]
        # Fill every relation's column capacity and use worst-case escaped literals.
        while len(r["columns"]) < 8:
            r["columns"].append({"id":"x"+str(len(r["columns"]))*15,"type":"text"})
        r["filter"] = {"column":r["columns"][-1]["id"],"value":"🙂"*64}
        r["index"] = {"column":r["filter"]["column"],"height":8}
    for j in e["query"]["joins"]:
        j["left"][0],j["right"][0] = rename[j["left"][0]],rename[j["right"][0]]
    e["query"]["output"] = [[rename["members"],"name"] for _ in range(8)]
    for b in e["statistics"]["base"]:
        b.update(relation=rename[b["relation"]],rows=1000000,pages=1000000,row_bytes=1024)
    for c in e["statistics"]["cardinalities"]:
        c["relations"] = [rename[n] for n in c["relations"]]
        c["rows"] = 1000000
    return e


def test_maximum_family_numbers_and_payloads(tmp_path):
    exercise = maximum_exercise()
    candidates = list(model.candidates(exercise))
    assert len(candidates) == 864
    assert len(model.canonical(exercise)) <= model.SEED_MAX
    assert max(len(model.canonical(a)) for a in candidates) <= model.ANSWER_MAX
    results = probe.run([probe.request(exercise,a) for a in candidates])
    max_data = max_outcome = 0
    for answer,row in zip(candidates,results,strict=True):
        data = facts(row)
        assert data == model.analyze(exercise,answer)
        max_data = max(max_data,len(model.canonical(data)))
        max_outcome = max(max_outcome,len(model.canonical(row["outcome"])))
    assert max_data <= 8192 and max_outcome <= 12288
    start = time.perf_counter()
    optimum = model.optimum(exercise)
    elapsed = time.perf_counter()-start
    assert optimum["candidates"] == 864
    # Record timing as evidence; correctness does not depend on a brittle timing assertion.
    report = {"seed_bytes":len(model.canonical(exercise)),
              "max_answer_bytes":max(len(model.canonical(a)) for a in candidates),
              "max_data_bytes":max_data,"max_outcome_bytes":max_outcome,
              "reference_seconds":elapsed,"candidates":len(candidates)}
    (tmp_path/"bounds.json").write_text(json.dumps(report,indent=2),encoding="utf-8")


def lesson():
    return {"format":1,"exercise":copy.deepcopy(EXERCISES["library"]),
            "baseline":copy.deepcopy(ANSWERS["library-late-books"]),
            "goal":{"kind":"best"},"worked_answer":copy.deepcopy(ANSWERS["library-best"]),
            "explanation":{"en":"Join the filtered books first.","de":"Zuerst die gefilterten Bücher verbinden."}}


def test_frozen_lesson_source_and_goals():
    value = lesson()
    schema = json.loads(PROVIDER.resources["texstage_query_plan/schemas/lesson-v1.json"])
    Draft202012Validator(schema).validate(value)
    prepared = model.prepare_reference(value)
    assert prepared["reference"]["cost"] == 116430
    original = copy.deepcopy(value)
    prepared["source"]["goal"]["kind"] = "other"
    assert value == original
    value["goal"] = {"kind":"budget","max_cost":128280}
    value["worked_answer"] = value["baseline"]
    assert model.prepare_reference(value)["worked"]["cost"] == 128280
    value["goal"]["max_cost"] = 116429
    with pytest.raises(model.InputError,match="Unreachable"):
        model.prepare_reference(value)
    value = lesson(); value["worked_answer"] = value["baseline"]
    with pytest.raises(model.InputError,match="misses goal"):
        model.prepare_reference(value)
    value = lesson(); value["baseline"] = ANSWERS["disconnected-join"]
    with pytest.raises(model.InputError,match="Invalid baseline"):
        model.prepare_reference(value)


def physical_rows(exercise, answer, tables):
    """Independent tiny row interpreter for the declared scan/join meanings."""
    query, built = exercise["query"], []
    relations = {r["id"]:r for r in query["relations"]}
    for node in answer["nodes"]:
        if node["op"] == "scan":
            name = node["relation"]; relation = relations[name]; f = relation.get("filter")
            rows = [{(name,c["id"]):v for c,v in zip(relation["columns"],row,strict=True)}
                    for row in tables[name]]
            if f: rows = [row for row in rows if row[(name,f["column"])] == f["value"]]
            built.append((rows,{name}))
        else:
            left,lnames = built[node["left"]]; right,rnames = built[node["right"]]
            edges = []
            for j in query["joins"]:
                a,b=tuple(j["left"]),tuple(j["right"])
                if a[0] in lnames and b[0] in rnames: edges.append((a,b))
                elif b[0] in lnames and a[0] in rnames: edges.append((b,a))
            assert len(edges) == 1
            a,b=edges[0]
            if node["method"] == "nested":
                rows = [x|y for x in left for y in right if x[a] == y[b]]
            else:
                first,second,ka,kb = (left,right,a,b) if node["method"] == "hash-left" else (right,left,b,a)
                buckets = collections.defaultdict(list)
                for row in first: buckets[row[ka]].append(row)
                rows = [x|y for y in second for x in buckets[y[kb]]]
            built.append((rows,lnames|rnames))
    return collections.Counter(tuple(row[tuple(ref)] for ref in query["output"]) for row in built[-1][0])


@pytest.mark.parametrize("variant", ["duplicates","empty","filtered","multiple-members"])
def test_every_library_plan_preserves_bag_query(variant):
    e = EXERCISES["library"]
    tables = {"books":[[1,"db"],[2,"net"],[3,"db"]],
              "loans":[[1,1,True],[1,1,True],[3,1,True],[2,2,True],[3,1,False]],
              "members":[[1,"Ada"],[2,"Ben"]]}
    if variant == "empty": tables["books"] = []
    if variant == "filtered": tables["loans"] = [[1,1,False],[2,2,True]]
    if variant == "multiple-members": tables["members"].append([1,"Ada"])
    with sqlite3.connect(":memory:") as db:
        for r in e["query"]["relations"]:
            columns = ",".join(c["id"]+" "+("TEXT" if c["type"] == "text" else "INTEGER") for c in r["columns"])
            db.execute("CREATE TABLE "+r["id"]+" ("+columns+")")
            db.executemany("INSERT INTO "+r["id"]+" VALUES ("+",".join("?" for _ in r["columns"])+")",tables[r["id"]])
        expected = collections.Counter(db.execute(
            "SELECT members.name FROM books JOIN loans ON books.book_id=loans.book_id "
            "JOIN members ON loans.member_id=members.member_id WHERE books.topic='db' AND loans.open=1"))
    if variant == "duplicates": assert expected == {("Ada",):3}
    if variant == "multiple-members": assert expected == {("Ada",):6}
    valid = 0
    for answer in model.candidates(e):
        if model.analyze(e,answer)["valid"]:
            assert physical_rows(e,answer,tables) == expected
            valid += 1
    assert valid == 144


def test_schema_fixtures_and_strict_identifier_end():
    es = Draft202012Validator(json.loads(PROVIDER.resources["texstage_query_plan/schemas/exercise-v1.json"]))
    ans = Draft202012Validator(json.loads(PROVIDER.resources["texstage_query_plan/schemas/answer-v1.json"]))
    for exercise in [*EXERCISES.values(), maximum_exercise()]:
        es.validate(exercise)
    for case in CASES["cases"]:
        ans.validate(case["answer"])
    assert not es.is_valid(changed_source("linebreak-id"))


def test_empty_joins_and_zero_goal():
    e = copy.deepcopy(EXERCISES["tiny"])
    e["statistics"]["base"][0].update(rows=0,pages=0)
    e["statistics"]["cardinalities"][0]["rows"] = 0
    e["statistics"]["cardinalities"][-1]["rows"] = 0
    e["limits"]["hash_bytes"] = 0
    nested = copy.deepcopy(ANSWERS["tiny-nested"])
    hashed = copy.deepcopy(ANSWERS["tiny-hash"])
    rows = probe.run([probe.request(e,nested),probe.request(e,hashed)])
    assert facts(rows[0])["cost"] == 101
    assert facts(rows[1])["cost"] == 102
    assert facts(rows[1])["nodes"][-1]["hash_bytes"] == 0
    for b in e["statistics"]["base"]: b.update(rows=0,pages=0)
    for c in e["statistics"]["cardinalities"]: c["rows"] = 0
    assert model.optimum(e)["cost"] == 0 and model.optimum(e)["count"] == 6
    value = lesson()
    value.update(exercise=e,baseline=nested,worked_answer=hashed,goal={"kind":"budget","max_cost":0})
    assert model.prepare_reference(value)["worked"]["cost"] == 0


def test_schema_upper_bound_and_maximum_lesson(tmp_path):
    # Deliberately schema-valid upper-bound facts, not a semantically possible trace.
    # This measures transport capacity; a future lesson must still validate meaning.
    patch = {"exercise":"🙂"*64, "answer":"🙂"*64, "cost":model.COST_MAX, "nodes":[
        {"node":4,"subset":7,"rows":1000000,"row_bytes":3072,
         "local_cost":model.COST_MAX,"total_cost":model.COST_MAX,"hash_bytes":16777216}
        for _ in range(5)]}
    row = probe.run([probe.request(EXERCISES["library"],ANSWERS["library-best"],
                                  data_patch=patch)])[0]
    assert "load_or_contract_error" not in row, row
    assert row["outcome"]["status"] == "ok"
    data = row["outcome"]["data"]
    assert data["cost"] == model.COST_MAX
    assert len(model.canonical(data)) <= 8192
    value = lesson()
    value["exercise"] = maximum_exercise()
    best = model.optimum(value["exercise"])
    value["baseline"] = value["worked_answer"] = best["plan"]
    value["explanation"] = {"en":"🙂"*2000,"de":"🙂"*2000}
    assert len(model.canonical(value)) <= model.LESSON_MAX
    samples = []
    for _ in range(5):
        start = time.perf_counter()
        model.prepare_reference(value)
        samples.append(time.perf_counter()-start)
    report = {"schema_data_upper_bytes":len(model.canonical(data)),
              "schema_outcome_witness_bytes":len(model.canonical(row["outcome"])),
              "maximum_shaped_lesson_bytes":len(model.canonical(value)),
              "prepare_reference_seconds":samples}
    (tmp_path/"schema-bounds.json").write_text(json.dumps(report,indent=2),encoding="utf-8")

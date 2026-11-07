# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel conformance against hand-derived cases and independent Python."""
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator, ValidationError
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, validate_outcome, validate_portable_schema
from texstage_er_decisions import model

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("er_probe", ROOT / "maintenance/er_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture(scope="module")
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, "Use an ER-only installed-wheel environment."
    selected, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    assert not Path(model.__file__).is_relative_to(ROOT / "plugins/er-decisions")
    subprocess.run([sys.executable, "-c",
                    "import sys; from texstage.plugins.catalog import discover; discover(); "
                    "assert 'texstage_er_decisions' not in sys.modules"], check=True)
    return selected


@pytest.fixture(scope="module")
def seed(provider):
    return model.source(probe.fixture(provider))


def facts(row):
    assert not row.get("load_or_contract_error"), row
    assert row["result"]["status"] == "ok", row
    assert row["reuseRefused"] and row["disposalRefused"]
    assert row["milliseconds"] < 2000
    data = row["outcome"]["data"]
    assert data == row["result"]["data"]
    assert row["result"]["canonical"] == "er-decisions-v1:" + model.digest(data)
    assert len(model.canonical(data)) <= model.DATA_MAX
    assert len(model.canonical(row["outcome"])) <= model.OUTCOME_MAX
    Draft202012Validator(model.schema("analysis")).validate(data)
    return data


def passing(data):
    return data["model_valid"] and all(c["admits"] == (c["expected"] == "allow") for c in data["checks"])


def test_schemas_and_owned_resources(provider, seed):
    for name in ("exercise", "model", "answer", "analysis"):
        validate_portable_schema(model.schema(name))
    assert set(provider.manifest["capabilities"]["content_types"]) == {probe.PROVIDER + ".lesson"}
    assert seed["format"] == "er-registration-v1"
    assert "texstage_er_decisions/web/engine.worker.mjs" in provider.resources
    assert all(k.startswith("texstage_er_decisions/") or k == "LICENSE" for k in provider.resources)
    bundle = provider.resources["texstage_er_decisions/web/engine.worker.mjs"].decode("utf-8")
    assert "from \"./" not in bundle and "from \"../" not in bundle


def test_all_27_against_hand_examples_and_independent_oracle(seed):
    expected = json.loads((ROOT / "docs/design/er-modelling-decisions/expected-cases.json").read_text(encoding="utf-8"))
    oracle_spec = importlib.util.spec_from_file_location("er_design_oracle", ROOT / "maintenance/check_er_design.py")
    oracle = importlib.util.module_from_spec(oracle_spec)
    oracle_spec.loader.exec_module(oracle)
    design_seed = oracle.read("registrations.json")
    submissions = list(probe.answers(seed))
    rows = probe.run([probe.request(seed, a) for a in submissions])
    accepted = []
    for submission, row in zip(submissions, rows, strict=True):
        data = facts(row)
        assert data == model.analyze(seed, submission)
        original = oracle.analyse(design_seed, dict(submission["choices"]))
        assert {c["id"]: c["admits"] for c in data["checks"]} == {c["id"]: c["admits"] for c in original["checks"]}
        assert {c["id"] for c in data["checks"]} == {w["id"] for w in seed["snapshots"]}
        if passing(data):
            accepted.append(dict(submission["choices"]))
    assert len(rows) == 27 and len(accepted) == 2
    assert sorted(map(model.canonical, accepted)) == sorted(map(model.canonical, expected["checked_models"]["registrations"]))
    for case in expected["counterexamples"]:
        if case["fixture"] != "registrations":
            continue
        data = model.analyze(seed, {"format": 1, "choices": [[k, v] for k, v in case["choices"].items()]})
        check = next(c for c in data["checks"] if c["id"] == case["world"])
        assert check["admits"] != (check["expected"] == "allow")
    good_rows = [r for r in rows if passing(r["outcome"]["data"])]
    assert good_rows[0]["outcome"]["key"] != good_rows[1]["outcome"]["key"]
    assert good_rows[0]["outcome"]["data"]["checks"] == good_rows[1]["outcome"]["data"]["checks"]


@pytest.mark.parametrize("change,code", [
    ("unknown-decision", "unknown-decision"), ("duplicate-decision", "duplicate-decision"),
    ("missing-decision", "missing-decision"), ("unknown-option", "unknown-option")
])
def test_well_formed_invalid_decisions_are_domain_findings(seed, change, code):
    answer = copy.deepcopy(seed["worked_answers"][0])
    if change == "unknown-decision":
        answer["choices"][0][0] = "unknown"
    elif change == "duplicate-decision":
        answer["choices"][1] = answer["choices"][0][:]
    elif change == "missing-decision":
        answer["choices"].pop()
    else:
        answer["choices"][0][1] = "unknown"
    data = facts(probe.run([probe.request(seed, answer)])[0])
    assert data == model.analyze(seed, answer)
    assert not data["model_valid"] and data["checks"] == []
    assert data["structural_issues"][0]["code"] == code


@pytest.mark.parametrize("text,status", [
    ("{", "syntax"),
    ('{"format":1,"format":1,"choices":[]}', "syntax"),
    ('{"format":1.0,"choices":[]}', "syntax"),
    ('{"format":true,"choices":[]}', "syntax"),
    ('{"format":1,"choices":[["x","a\\nb"]]}', "syntax"),
    ('{"format":1,"choices":[["x","\\ud800"]]}', "syntax"),
    ('{"format":1,"choices":[["x",3]]}', "syntax"),
    ('{"format":1,"choices":[["x",["a"]]]}', "syntax"),
    ('{"format":1,"choices":[],"assumption":"excuse"}', "syntax"),
    ('{"format":1,"choices":[],"rationale":"ignored"}', "syntax"),
    ('{"format":1,"choices":[],"__proto__":{}}', "syntax"),
    ("[" * 20 + "]" * 20, "syntax"),
    (" " * 1025, "refused"),
])
def test_malformed_answers(seed, text, status):
    row = probe.run([probe.request(seed, text=text)])[0]
    assert row["result"] == {"status": status}
    assert row["reuseRefused"] and row["disposalRefused"]
    with pytest.raises((model.InputError, model.ResourceLimit)):
        model.answer(model.parse(text, model.ANSWER_MAX))


def mutate(seed, case):
    value = copy.deepcopy(seed)
    rel = value["model"]["relationship"]
    if case == "unsupported-profile":
        value["format"] = "er-rooms-v1"
    elif case == "open-assumption":
        value["assumptions"] = []
    elif case == "unknown-owner":
        rel["attributes"][0]["owner"] = "absent"
    elif case == "reserved-role":
        rel["roles"][0]["id"] = "relationship"
    elif case == "same-entity":
        rel["roles"][1]["entity"] = rel["roles"][0]["entity"]
    elif case == "implicit-multiset-relationship":
        rel["pair_unique"] = False
    elif case == "boolean-minimum":
        rel["roles"][0]["min"] = False
    elif case == "boolean-maximum":
        rel["roles"][0]["max"] = True
    elif case == "string-number":
        rel["roles"][0]["max"] = "1"
    elif case == "duplicate-slot":
        value["decisions"].append(copy.deepcopy(value["decisions"][0]))
        value["decisions"][-1]["id"] = "another"
    elif case == "duplicate-option":
        value["decisions"][0]["options"][1]["id"] = value["decisions"][0]["options"][0]["id"]
    elif case == "same-option-meaning":
        value["decisions"][0]["options"][1]["value"] = value["decisions"][0]["options"][0]["value"]
    elif case == "unknown-target":
        value["decisions"][0]["target"] = "absent"
    elif case == "unknown-requirement":
        value["snapshots"][0]["requirements"] = ["absent"]
    elif case == "dangling-record":
        value["snapshots"][0]["links"][0]["roles"][0][1] = "absent"
    elif case == "duplicate-occurrence":
        value["snapshots"][0]["links"][1]["id"] = value["snapshots"][0]["links"][0]["id"]
    elif case == "missing-attribute":
        value["snapshots"][0]["links"][0]["values"] = []
    elif case == "wrong-scalar":
        value["snapshots"][0]["links"][0]["values"][0][1] = True
    elif case == "no-public":
        for world in value["snapshots"]:
            world["visibility"] = "private"
    elif case == "false-worked-answer":
        next(p for p in value["worked_answers"][0]["choices"] if p[0] == "person-links")[1] = "zero-one"
    elif case == "duplicate-worked":
        value["worked_answers"][1] = value["worked_answers"][0]
    elif case == "too-many-snapshots":
        value["snapshots"] *= 3
    elif case == "long-label":
        value["brief"]["en"] = "x" * 801
    elif case == "too-many-records":
        value["snapshots"][0]["entities"][0]["ids"] += ["x" + str(n) for n in range(32)]
    else:
        raise ValueError(case)
    return value


@pytest.mark.parametrize("case", [
    "unsupported-profile", "open-assumption", "unknown-owner", "reserved-role", "same-entity",
    "implicit-multiset-relationship", "boolean-minimum", "boolean-maximum", "string-number",
    "duplicate-slot", "duplicate-option", "same-option-meaning", "unknown-target",
    "unknown-requirement", "dangling-record", "duplicate-occurrence", "missing-attribute",
    "wrong-scalar", "no-public", "false-worked-answer", "duplicate-worked",
    "too-many-snapshots", "long-label", "too-many-records"
])
def test_author_seed_rejected_in_both_implementations(seed, case):
    changed = mutate(seed, case)
    with pytest.raises((model.InputError, model.ResourceLimit)):
        model.source(changed)
    row = probe.run([probe.request(changed)])[0]
    assert row.get("load_or_contract_error"), (case, row)


def test_permutations_and_prose_do_not_change_semantic_identity(seed):
    changed = copy.deepcopy(seed)
    changed["brief"]["en"] = "Another explanation."
    changed["requirements"].reverse()
    for requirement in changed["requirements"]:
        requirement["text"] = "Reworded."
    changed["model"]["entities"].reverse()
    changed["model"]["relationship"]["roles"].reverse()
    changed["decisions"].reverse()
    for decision in changed["decisions"]:
        decision["options"].reverse()
    changed["snapshots"].reverse()
    for world in changed["snapshots"]:
        world["entities"].reverse(); world["links"].reverse(); world["requirements"].reverse()
        for entity in world["entities"]:
            entity["ids"].reverse()
        for row in world["links"]:
            row["roles"].reverse(); row["values"].reverse()
    answer = copy.deepcopy(seed["worked_answers"][0])
    answer["choices"].reverse()
    rows = probe.run([probe.request(seed), probe.request(changed, answer)])
    assert facts(rows[0]) == facts(rows[1])
    assert rows[0]["result"]["canonical"] == rows[1]["result"]["canonical"]
    assert rows[0]["outcome"]["key"] == rows[1]["outcome"]["key"]
    assert rows[0]["outcome"]["namespace"] != rows[1]["outcome"]["namespace"], "Host binds the complete distinct seed."


@pytest.mark.parametrize("kind", ["int", "bool", "text"])
def test_scalar_types_generic_ids_and_unicode(seed, kind):
    changed = json.loads(json.dumps(seed).replace('"person"', '"Member_A"').replace('"workshop"', '"Class_B"')
                         .replace('"registration"', '"Enrolment"').replace('"status"', '"state"'))
    changed["model"]["relationship"]["attributes"][0]["type"] = kind
    for world in changed["snapshots"]:
        for row in world["links"]:
            value = row["values"][0][1] == "confirmed"
            row["values"][0][1] = (10 if value else 20) if kind == "int" else (
                value if kind == "bool" else ("e\u0301\U0001f642" if value else "other"))
    normalized = model.source(changed)
    rows = probe.run([probe.request(changed, a) for a in probe.answers(normalized)])
    for answer, row in zip(probe.answers(normalized), rows, strict=True):
        assert facts(row) == model.analyze(normalized, answer)
    assert sum(passing(facts(row)) for row in rows) == 2


def test_hash_vectors(seed):
    vectors = ["", "abc", "e\u0301", "\U0001f642", "x" * 1024]
    rows = probe.run([{"hash": v} for v in vectors])
    assert [r["hash"] for r in rows] == [hashlib.sha256(v.encode()).hexdigest() for v in vectors]


def test_forged_facts_and_full_binding_namespace(seed, provider):
    bad = probe.run([probe.request(seed, data_patch={"checks": []}),
                     probe.request(seed, data_patch={"unexpected": "field"})])
    assert all(r.get("load_or_contract_error") for r in bad)
    provider, engine = probe.installed()
    request = probe.bound_requests(provider, engine, [probe.request(seed)])[0]
    row = probe.run([request])[0]
    facts(row)
    validate_outcome(row["outcome"], provider, engine, request["namespace"])
    subset = {k: v for k, v in request["binding"].items() if k != "engine"}
    with pytest.raises(PluginError):
        validate_outcome(row["outcome"], provider, engine, namespace(provider, probe.ENGINE, engine, subset))


def test_negative_business_world_is_retained(seed):
    world = next(w for w in seed["snapshots"] if w["id"] == "duplicate-pair")
    assert len(world["links"]) == 2
    assert world["links"][0]["roles"] == world["links"][1]["roles"]
    answer = copy.deepcopy(seed["worked_answers"][0])
    next(p for p in answer["choices"] if p[0] == "registration-form")[1] = "entity-id-only"
    check = next(c for c in facts(probe.run([probe.request(seed, answer)])[0])["checks"] if c["id"] == world["id"])
    assert check == {"id": "duplicate-pair", "expected": "forbid", "admits": True, "reason": None}


def test_all_small_status_assignments(seed):
    # Four possible pairs, each absent/confirmed/waitlisted: 3**4 legal worlds.
    # Expectations below inspect the observation's representability directly.
    worlds = []
    for index, assignment in enumerate(itertools.product([None, "confirmed", "waitlisted"], repeat=4)):
        links = []
        for position, ((person, workshop), status) in enumerate(zip(
                itertools.product(["p1", "p2"], ["w1", "w2"]), assignment, strict=True)):
            if status is not None:
                links.append({"id": "r" + str(position), "roles": [["person", person], ["workshop", workshop]],
                              "values": [["status", status]]})
        worlds.append({"id": "tiny-" + str(index), "visibility": "public", "expected": "allow",
                       "requirements": ["person-many", "workshop-many", "pair-unique", "status-pair"],
                       "entities": [{"entity": "person", "ids": ["p1", "p2"]},
                                    {"entity": "workshop", "ids": ["w1", "w2"]}], "links": links})
    requests, expectations = [], []
    for start in range(0, len(worlds), 12):
        changed = copy.deepcopy(seed)
        changed["snapshots"] = worlds[start:start + 12]
        exercise = model.source(changed)
        for submission in probe.answers(exercise):
            requests.append(probe.request(exercise, submission))
            choices = dict(submission["choices"])
            admitted = {}
            for world in exercise["snapshots"]:
                observations = [(dict(r["roles"])["person"], dict(r["roles"])["workshop"], r["values"][0][1])
                                for r in world["links"]]
                counts = [sum(p == person for p, _, _ in observations) for person in ("p1", "p2")]
                cardinality = (all(c <= 1 for c in counts) if choices["person-links"] == "zero-one" else
                               all(c >= 1 for c in counts) if choices["person-links"] == "one-many" else True)
                owner = choices["status-owner"]
                determinants = [(p if owner == "person" else w, status) for p, w, status in observations]
                attribute_ok = owner == "registration" or all(
                    len({v for k, v in determinants if k == key}) <= 1 for key, _ in determinants)
                admitted[world["id"]] = cardinality and attribute_ok
            expectations.append((exercise, submission, admitted))
    rows = probe.run(requests, timeout=120)
    assert len(rows) == 189
    for row, (exercise, submission, admitted) in zip(rows, expectations, strict=True):
        data = facts(row)
        assert data == model.analyze(exercise, submission)
        assert {c["id"]: c["admits"] for c in data["checks"]} == admitted


def test_raw_answer_boundary_and_duplicate_seed_keys(seed):
    answer_text = json.dumps(seed["worked_answers"][0])
    exact = answer_text + " " * (1024 - len(answer_text))
    rows = probe.run([probe.request(seed, text=exact), probe.request(seed, text=exact + " "),
                      probe.request(seed, seed='{"format":1,"format":1}'),
                      probe.request(seed, options={"network": True}), probe.request(seed, options=[])])
    facts(rows[0])
    assert rows[1]["result"] == {"status": "refused"}
    assert all(r.get("load_or_contract_error") for r in rows[2:])
    with pytest.raises(model.InputError):
        model.parse('{"format":1,"format":1}')


def test_escaped_source_cap(seed):
    changed = copy.deepcopy(seed)
    for attribute in changed["model"]["relationship"]["attributes"]:
        attribute["type"] = "text"
    prototype = copy.deepcopy(next(w for w in changed["snapshots"] if w["id"] == "intro"))
    prototype["links"] = []
    prototype["entities"] = [{"entity": "person", "ids": ["p"]},
                             {"entity": "workshop", "ids": ["w" + str(i) for i in range(15)]}]
    for i in range(15):
        prototype["links"].append({"id": "r" + str(i), "roles": [["person", "p"], ["workshop", "w" + str(i)]],
                                   "values": [["status", "\U0001f642" * 64]]})
    changed["snapshots"] = [copy.deepcopy(prototype) for _ in range(12)]
    for i, world in enumerate(changed["snapshots"]):
        world["id"] = "large-" + str(i)
    assert all(sum(len(e["ids"]) for e in w["entities"]) + len(w["links"]) == 31 for w in changed["snapshots"])
    assert len(model.canonical(changed)) > model.SEED_MAX
    with pytest.raises(model.ResourceLimit):
        model.source(changed)
    assert probe.run([probe.request(changed)])[0].get("load_or_contract_error")


def test_maximum_fact_shape_fits_both_host_validators(seed):
    # Schema-level maximum, including escaped text budget and occurrence keys.
    # This is a transport-cap measurement, not an evaluation of 12 fake worlds.
    issues = {"code": "attribute-dependency", "target": "t" * 24, "occurrences": ["a" * 24, "b" * 24]}
    checks = [{"id": ("w" * 22) + f"{i:02}", "expected": "forbid", "admits": False, "reason": issues}
              for i in range(12)]
    row = probe.run([probe.request(seed, data_patch={"checks": checks})])[0]
    assert not row.get("load_or_contract_error"), row
    assert row["outcome"]["status"] == "ok"
    data = row["outcome"]["data"]
    Draft202012Validator(model.schema("analysis")).validate(data)
    assert len(model.canonical(data)) < model.DATA_MAX
    assert len(model.canonical(row["outcome"])) < model.OUTCOME_MAX


def test_positive_count_boundaries_and_all_four_slots(seed):
    changed = copy.deepcopy(seed)
    rel = changed["model"]["relationship"]
    rel["attributes"] += [
        {"id": "counter", "type": "int", "owner": "relationship"},
        {"id": "flag", "type": "bool", "owner": "relationship"},
        {"id": "note", "type": "text", "owner": "relationship"}]
    first = next(d for d in changed["decisions"] if d["id"] == "person-links")
    first["options"].append({"id": "one-one", "value": {"min": 1, "max": 1}})
    changed["decisions"].append({"id": "workshop-links", "kind": "role-bounds", "target": "workshop",
                                  "options": copy.deepcopy(first["options"])})
    for answer in changed["worked_answers"]:
        answer["choices"].append(["workshop-links", "zero-many"])
    world = {
        "id": "boundary", "visibility": "public", "expected": "allow",
        "requirements": ["person-many", "workshop-many", "pair-unique", "status-pair"],
        "entities": [{"entity": "person", "ids": ["p1", "unused"]},
                     {"entity": "workshop", "ids": ["w" + str(i) for i in range(15)]}],
        "links": [{"id": "r" + str(i), "roles": [["person", "p1"], ["workshop", "w" + str(i)]],
                   "values": [["status", "confirmed" if i % 2 else "waitlisted"],
                              ["counter", -1000000 if i % 2 else 1000000], ["flag", bool(i % 2)],
                              ["note", "x" * 64]]} for i in range(15)]
    }
    changed["snapshots"] = [copy.deepcopy(world) for _ in range(12)]
    for i, snapshot in enumerate(changed["snapshots"]):
        snapshot["id"] = "s" * 22 + f"{i:02}"
    exercise = model.source(changed)
    assert len(model.canonical(exercise)) <= model.SEED_MAX
    assert len(list(probe.answers(exercise))) == 144
    submissions = [exercise["worked_answers"][0],
                   {"format": 1, "choices": [[d["id"], d["options"][-1]["id"]] for d in exercise["decisions"]]}]
    for answer, row in zip(submissions, probe.run([probe.request(exercise, a) for a in submissions]), strict=True):
        assert facts(row) == model.analyze(exercise, answer)
        assert len(row["outcome"]["data"]["checks"]) == 12


def test_empty_populations_do_not_prove_participation(seed):
    changed = copy.deepcopy(seed)
    world = copy.deepcopy(next(w for w in changed["snapshots"] if w["id"] == "intro"))
    world["links"] = []
    for entity in world["entities"]:
        entity["ids"] = []
    changed["snapshots"] = [world]
    exercise = model.source(changed)
    rows = probe.run([probe.request(exercise, a) for a in probe.answers(exercise)])
    assert len(rows) == 27 and all(passing(facts(r)) for r in rows)

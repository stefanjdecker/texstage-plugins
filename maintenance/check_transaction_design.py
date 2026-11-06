# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent mathematical oracle for transaction exercises.

Requires jsonschema from the compatible Texstage development lock. No network,
course files, installed plugin hooks or database server are used.
"""
from collections import Counter
import copy
from itertools import combinations, permutations
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1] / "docs/design/transaction-schedules"
SCHEMA = json.loads((ROOT / "activity-v1.schema.json").read_text(encoding="utf-8"))


class InvalidExercise(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidExercise(message)


def validate_exercise(exercise):
    Draft202012Validator(SCHEMA).validate(exercise)
    require(len({t["id"] for t in exercise["transactions"]}) == len(exercise["transactions"]),
            "duplicate transaction ID")
    operations = {}
    count = 0
    for transaction in exercise["transactions"]:
        program = transaction["operations"]
        require(program[-1]["kind"] == "commit" and sum(o["kind"] == "commit" for o in program) == 1,
                "one terminal commit is required")
        own_reads = set()
        for op in program:
            require(op["id"] not in operations, "duplicate operation ID")
            operations[op["id"]] = op | {"transaction": transaction["id"]}
            if op["kind"] == "commit":
                continue
            count += 1
            require(op["object"] in exercise["initial"], "unknown object")
            if op["kind"] == "read":
                own_reads.add(op["id"])
            elif "read" in op["value"]:
                require(op["value"]["read"] in own_reads, "write must reference an earlier own read")
    require(count <= 12, "read/write operation limit")
    validate_order(exercise, exercise["schedule"])
    return operations


def validate_order(exercise, order):
    programs = [[op["id"] for op in t["operations"]] for t in exercise["transactions"]]
    required = {op for program in programs for op in program}
    require(isinstance(order, list) and all(isinstance(op, str) for op in order), "invalid order")
    require(len(order) == len(required) and set(order) == required, "not an exact operation permutation")
    for program in programs:
        require([op for op in order if op in program] == program, "transaction program order changed")


def analyze(exercise, order=None):
    operations = validate_exercise(exercise)
    order = exercise["schedule"] if order is None else order
    validate_order(exercise, order)
    values, reads, trace = dict(exercise["initial"]), {}, []
    for oid in order:
        op = operations[oid]
        if op["kind"] == "read":
            reads[oid] = values[op["object"]]
        elif op["kind"] == "write":
            expression = op["value"]
            values[op["object"]] = (expression["constant"] if "constant" in expression
                                    else reads[expression["read"]] + expression["add"])
        trace.append({"operation": oid, "values": dict(values), "reads": dict(reads)})
    conflicts = []
    for left, right in combinations(order, 2):
        a, b = operations[left], operations[right]
        if (a["kind"] != "commit" and b["kind"] != "commit"
                and a["transaction"] != b["transaction"]
                and a["object"] == b["object"] and "write" in (a["kind"], b["kind"])):
            conflicts.append([left, right])
    edges = sorted({(operations[a]["transaction"], operations[b]["transaction"]) for a, b in conflicts})
    vertices = sorted(t["id"] for t in exercise["transactions"])
    # Exhaustive certificates are feasible for <= 3 transactions and independent
    # of the production engine's planned graph traversal algorithm.
    serial_orders = [list(p) for p in permutations(vertices) if all(p.index(a) < p.index(b) for a, b in edges)]
    cycle = []
    if not serial_orders:
        for size in range(2, len(vertices) + 1):
            for candidate in permutations(vertices, size):
                closed = (*candidate, candidate[0])
                if all((a, b) in edges for a, b in zip(closed, closed[1:])):
                    cycle = list(closed)
                    break
            if cycle:
                break
        require(bool(cycle), "no cycle certificate")
    return {"final": values, "reads": reads, "trace": trace, "conflicts": conflicts,
            "edges": [list(e) for e in edges], "csr": bool(serial_orders),
            "serial_orders": serial_orders, "cycle": cycle}


def serial_schedule(exercise, transaction_order):
    programs = {t["id"]: [op["id"] for op in t["operations"]] for t in exercise["transactions"]}
    return [op for tid in transaction_order for op in programs[tid]]


def interleavings(programs):
    if not any(programs):
        yield []
    for i, program in enumerate(programs):
        if program:
            remaining = [p[1:] if j == i else p for j, p in enumerate(programs)]
            for tail in interleavings(remaining):
                yield [program[0], *tail]


def main():
    Draft202012Validator.check_schema(SCHEMA)
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        exercise = case.get("exercise") or json.loads((ROOT / case["file"]).read_text(encoding="utf-8"))
        result = analyze(exercise, case.get("schedule"))
        for key, expected in case["expected"].items():
            require(result[key] == expected, f"{case['id']}: {key} differs from hand-specified expectation")
        if "same_final_serial_order" in case:
            serial = analyze(exercise, serial_schedule(exercise, case["same_final_serial_order"]))
            require(serial["csr"] and serial["final"] == result["final"] and not result["csr"],
                    "final-state equality must not imply CSR")

    counter = json.loads((ROOT / "counter.exercise.json").read_text(encoding="utf-8"))
    programs = [[op["id"] for op in t["operations"]] for t in counter["transactions"]]
    counts = Counter()
    vertices = [t["id"] for t in counter["transactions"]]
    serial_conflicts = {
        tuple(p): set(map(tuple, analyze(counter, serial_schedule(counter, p))["conflicts"]))
        for p in permutations(vertices)
    }
    for order in interleavings(programs):
        result = analyze(counter, order)
        equivalent = [list(p) for p, pairs in serial_conflicts.items()
                      if pairs == set(map(tuple, result["conflicts"]))]
        require(equivalent == result["serial_orders"], "graph and operation-order criteria disagree")
        counts[(result["csr"], result["final"]["x"])] += 1
    require(dict(counts) == {(True, 120): 8, (False, 110): 12},
            "twenty legal counter interleavings must have the expected outcomes")

    invalid = [
        counter["schedule"][:-1],
        ["a1", "b1", "a2", "b2", "a3", "a3"],
        ["a2", "a1", "b1", "b2", "a3", "b3"],
        ["a1", "a3", "a2", "b1", "b2", "b3"],
        ["a1", "b1", "a2", "b2", "a3", "unknown"],
    ]
    for order in invalid:
        try:
            analyze(counter, order)
        except InvalidExercise:
            continue
        raise AssertionError("invalid schedule accepted")
    bad_read = copy.deepcopy(counter)
    bad_read["transactions"][0]["operations"][1]["value"]["read"] = "b1"
    try:
        analyze(bad_read)
    except InvalidExercise:
        pass
    else:
        raise AssertionError("cross-transaction local read accepted")
    invalid_schema = copy.deepcopy(counter)
    invalid_schema["initial"]["x"] = 1.5
    try:
        analyze(invalid_schema)
    except ValidationError:
        pass
    else:
        raise AssertionError("non-integer value accepted")
    print(json.dumps({"expected_cases": len(cases), "legal_counter_interleavings": sum(counts.values()),
                      "csr_repairs": counts[(True, 120)], "lost_update_schedules": counts[(False, 110)],
                      "invalid_inputs_rejected": len(invalid) + 2,
                      "scope": "independent design checker; runtime engine has separate installed-wheel tests"}, indent=2))


if __name__ == "__main__":
    main()

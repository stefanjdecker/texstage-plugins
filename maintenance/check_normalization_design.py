# SPDX-License-Identifier: Apache-2.0
"""Check trusted Normalization Workshop design examples with the standard library.

This is a finite specification aid, not a runtime plugin or hostile-input parser.
Default is read-only; --write-record writes the evidence JSON beside the fixtures.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/design/normalization-workshop"


def subsets(attributes):
    ordered = sorted(attributes)
    return [frozenset(s) for n in range(len(ordered) + 1)
            for s in itertools.combinations(ordered, n)]


def closure(initial, fds):
    found = set(initial)
    while True:
        before = found.copy()
        for left, right in fds:
            if set(left) <= found:
                found.update(right)
        if found == before:
            return frozenset(found)


def keys_and_form(attributes, fds):
    universe = frozenset(attributes)
    keys = []
    for candidate in subsets(universe):
        if universe <= closure(candidate, fds) and not any(k <= candidate for k in keys):
            keys.append(candidate)
    prime = frozenset().union(*keys)
    second = third = bcnf = True
    for left in subsets(universe):
        reached = closure(left, fds) & universe
        for right in reached - left:
            if reached != universe:
                bcnf = False
                if right not in prime:
                    third = False
            if right not in prime and any(left < key for key in keys):
                second = False
    form = "bcnf" if bcnf else "3nf" if third else "2nf" if second else "1nf"
    return keys, form


def preserved_by_projection(fds, parts):
    # Enumerate a basis containing every singleton nontrivial projected FD.
    projected = []
    for part in parts:
        for left in subsets(part):
            projected.extend((left, {right}) for right in (closure(left, fds) & part) - left)
    return all(set(right) <= closure(left, projected) for left, right in fds)


def preserved_by_iteration(fds, parts):
    for left, right in fds:
        reached = set(left)
        while True:
            before = reached.copy()
            for part in parts:
                reached.update(closure(reached & part, fds) & part)
            if reached == before:
                break
        if not set(right) <= reached:
            return False
    return True


def chase(attributes, fds, parts):
    columns = list(attributes)
    n = len(columns)
    table = [[j if col in part else n + i * n + j
              for j, col in enumerate(columns)] for i, part in enumerate(parts)]
    singleton = [(set(left), right) for left, rights in fds for right in sorted(rights)]
    merges = 0
    while True:
        changed = False
        for left, right in singleton:
            determinant = [columns.index(col) for col in left]
            col = columns.index(right)
            for first, second in itertools.combinations(range(len(parts)), 2):
                if all(table[first][j] == table[second][j] for j in determinant):
                    a, b = table[first][col], table[second][col]
                    if a == b:
                        continue
                    keep, remove = min(a, b), max(a, b)
                    for row in table:
                        if row[col] == remove:
                            row[col] = keep
                    changed = True
                    merges += 1
        if not changed:
            break
    assert merges <= n * (len(parts) - 1)
    target = list(range(n))
    lossless = target in table
    if not lossless:
        # Independently check the proposed legal relation and missing join tuple.
        for left, right in fds:
            xs = [columns.index(col) for col in left]
            ys = [columns.index(col) for col in right]
            for a, b in itertools.product(table, repeat=2):
                assert not all(a[j] == b[j] for j in xs) or all(a[j] == b[j] for j in ys)
        for part in parts:
            indices = [columns.index(col) for col in part]
            assert any(all(row[j] == target[j] for j in indices) for row in table)
        assert target not in table
    return lossless, merges


def check_case(case):
    attributes, fds = case["attributes"], case["fds"]
    parts = [frozenset(p) for p in case["relations"]]
    expected = case["expected"]
    keys, form = keys_and_form(attributes, fds)
    assert set(keys) == {frozenset(k) for k in expected["keys"]}, case["id"]
    assert form == expected["normal_form"], (case["id"], form)
    forms = [keys_and_form(p, fds)[1] for p in parts]
    assert forms == expected["component_forms"], (case["id"], forms)
    covered = frozenset().union(*parts) == set(attributes)
    assert covered == expected["covered"]
    for left, right in expected["closures"].items():
        assert closure(left, fds) == set(right)
    lossless = preserved = None
    merges = 0
    if covered:
        lossless, merges = chase(attributes, fds, parts)
        preserved = preserved_by_projection(fds, parts)
        assert preserved == preserved_by_iteration(fds, parts)
        if len(parts) == 2:
            overlap = closure(parts[0] & parts[1], fds)
            assert lossless == (parts[0] <= overlap or parts[1] <= overlap)
    assert lossless == expected["lossless"], case["id"]
    assert preserved == expected["preserved"], case["id"]
    return {"id": case["id"], "passed": True, "lossless": lossless,
            "preserved": preserved, "chase_merges": merges}


def check_lesson(filename, case):
    lesson = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    exercise = lesson["exercise"]
    attributes = [a["id"] for a in exercise["attributes"]]
    assert "".join(attributes) == case["attributes"]
    fds = [(fd["lhs"], fd["rhs"]) for fd in exercise["fds"]]
    assert all(closure(x, fds) == closure(x, case["fds"]) for x in subsets(attributes))
    def decode(mask):
        assert type(mask) is int and 0 < mask < (1 << len(attributes))
        return frozenset(a for i, a in enumerate(attributes) if mask & (1 << i))
    parts = [decode(mask) for mask in lesson["worked_answer"]["relations"]]
    assert set(parts) == {frozenset(p) for p in case["relations"]}
    assert frozenset().union(*parts) == set(attributes)
    assert chase(attributes, fds, parts)[0]
    assert all(keys_and_form(p, fds)[1] == "bcnf" for p in parts)
    if exercise["task"]["preserve"]:
        assert preserved_by_projection(fds, parts)
    return {"file": filename, "worked_answer_checked": True}


def exhaustive_binary_check():
    # All 4,096 subsets of the 12 nontrivial singleton FDs on three attributes.
    attrs = "ABC"
    possible = [(left, {right}) for left in subsets(attrs)
                for right in attrs if right not in left]
    nonempty = subsets(attrs)[1:]
    pairs = [(a, b) for a, b in itertools.combinations(nonempty, 2)
             if a | b == set(attrs)]
    count = 0
    for selected in range(1 << len(possible)):
        fds = [fd for i, fd in enumerate(possible) if selected & (1 << i)]
        for a, b in pairs:
            overlap = closure(a & b, fds)
            expected = a <= overlap or b <= overlap
            actual, _ = chase(attrs, fds, [a, b])
            assert actual == expected
            count += 1
    return {"attributes": 3, "fd_sets": 1 << len(possible),
            "covered_binary_decompositions_per_set": len(pairs), "comparisons": count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-record", action="store_true")
    args = parser.parse_args()
    document = json.loads((ROOT / "expected-cases.json").read_text(encoding="utf-8"))
    cases = document["cases"]
    checked = [check_case(case) for case in cases]
    lessons = [check_lesson("registration.lesson.draft.json", cases[0]),
               check_lesson("tutor.lesson.draft.json", cases[6])]
    evidence = {"format": 1, "scope": "trusted finite design examples; no runtime conformance",
                "cases": checked, "lessons": lessons,
                "exhaustive_binary": exhaustive_binary_check(),
                "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(ROOT.glob("*.json")) if p.name != "validation.json"},
                "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if args.write_record:
        (ROOT / "validation.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed_cases": len(checked), "worked_lessons": len(lessons),
                      "binary_comparisons": evidence["exhaustive_binary"]["comparisons"]}))


if __name__ == "__main__":
    main()

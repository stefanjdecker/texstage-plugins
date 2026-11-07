"""Check trusted, finite ER design examples; not a production plugin/validator.

Independent Python oracle for the hand-derived examples. Does not prove
unbounded model equivalence or validate author input, runtime schemas or UI.
The default is read-only; --write-report deliberately refreshes the record.
"""
# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/design/er-modelling-decisions"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def unique(rows, fields):
    keys = [tuple(row[field] for field in fields) for row in rows]
    return len(keys) == len(set(keys))


def fd(rows, determinant, dependent):
    seen = {}
    for row in rows:
        key = tuple(row[field] for field in determinant)
        value = row[dependent]
        if key in seen and seen[key] != value:
            return False
        seen[key] = value
    return True


def degree(entities, links, role, minimum, maximum):
    ids = {entity["id"] for entity in entities}
    if any(link[role] not in ids for link in links):
        return False
    counts = {ident: 0 for ident in ids}
    for link in links:
        counts[link[role]] += 1
    return all(count >= minimum and (maximum is None or count <= maximum)
               for count in counts.values())


def admits(kind, choice, tables):
    # Candidate-specific constraints are kept separate from scenario labels.
    if kind == "registrations":
        rows = tables["registrations"]
        low, high = {"zero-many": (0, None), "one-many": (1, None),
                     "zero-one": (0, 1)}[choice["person-links"]]
        if not degree(tables["people"], rows, "person", low, high):
            return False
        if not degree(tables["workshops"], rows, "workshop", 0, None):
            return False
        if choice["registration-form"] != "entity-id-only" and not unique(rows, ["person", "workshop"]):
            return False
        owner = choice["status-owner"]
        determinant = {"person": ["person"], "workshop": ["workshop"],
                       "registration": ["id"]}[owner]
        return fd(rows, determinant, "status")
    if kind == "rooms":
        rows = tables["rooms"]
        owners = {row["id"] for row in tables["buildings"]}
        if any(row["building"] not in owners for row in rows):
            return False
        fields = {"owner-number": ["building", "number"],
                  "surrogate-scoped": ["building", "number"],
                  "global-number": ["number"], "surrogate-only": ["id"]}[choice["identity"]]
        return unique(rows, fields)
    if kind == "mentoring":
        rows = tables["links"]
        return (unique(rows, ["student", "mentor"])
                and degree(tables["students"], rows, "student", 1, 1)
                and degree(tables["mentors"], rows, "mentor",
                           1 if choice["mentor-links"] == "one-many" else 0, None))
    raise ValueError("unknown trusted fixture")


def analyse(source, choices, assumption=None):
    checks, violations, unresolved = [], [], []
    for world in source["worlds"]:
        expected = world["expected"]
        if isinstance(expected, dict):
            expected = expected["unresolved" if assumption is None else assumption]
        admitted = admits(source["id"], choices, world["tables"])
        check = {"id": world["id"], "expected": expected, "admits": admitted}
        checks.append(check)
        if expected is None:
            unresolved.append(world["id"])
        elif admitted != (expected == "allow"):
            violations.append({"world": world["id"],
                               "direction": "excludes-allowed" if expected == "allow" else "admits-forbidden"})
    outcome = ("contradiction" if violations else
               "needs-clarification" if unresolved else
               "conditional" if assumption is not None else "checked")
    return {"choices": choices, "assumption": assumption, "outcome": outcome,
            "checks": checks, "violations": violations, "unresolved": unresolved}


def enumerate_source(source):
    names = sorted(source["choices"])
    for values in itertools.product(*(source["choices"][name] for name in names)):
        for assumption in source.get("assumptions", [None]):
            yield analyse(source, dict(zip(names, values)), assumption)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    expected = read("expected-cases.json")
    sources = {name: read(name + ".json") for name in expected["counts"]}
    results = {}
    for name, source in sources.items():
        require(source["id"] == name, "fixture identity")
        ids = [world["id"] for world in source["worlds"]]
        require(len(ids) == len(set(ids)), "duplicate world ID")
        for world in source["worlds"]:
            require(world["requirements"] and set(world["requirements"]) <= set(source["requirements"]),
                    "every witness must cite visible requirements")
            for rows in world["tables"].values():
                require(unique(rows, ["id"]), "fixture occurrence IDs must be unique")
        results[name] = list(enumerate_source(source))
        require(len(results[name]) == expected["counts"][name], "combination count")
        if name in expected["checked_models"]:
            actual = [result["choices"] for result in results[name] if result["outcome"] == "checked"]
            normalize = lambda rows: sorted(json.dumps(row, sort_keys=True) for row in rows)
            require(normalize(actual) == normalize(expected["checked_models"][name]),
                    name + ": hand-derived accepted alternatives disagree")
            require(all(result["outcome"] in ("checked", "contradiction") for result in results[name]),
                    "closed requirements must not become discussion")

    for case in expected["mentoring"]:
        matches = [r for r in results["mentoring"]
                   if r["choices"] == case["choices"] and r["assumption"] == case["assumption"]]
        require(len(matches) == 1 and matches[0]["outcome"] == case["outcome"],
                "mentoring interpretation outcome")
        # All profiles retain the fixed exact-one constraint.
        fixed = {c["id"]: c for c in matches[0]["checks"]}
        for ident in ("student-without-mentor", "student-two-mentors"):
            require(fixed[ident]["expected"] == "forbid" and not fixed[ident]["admits"],
                    "assumption weakened a fixed fact")
    for case in expected["counterexamples"]:
        result = analyse(sources[case["fixture"]], case["choices"])
        require({"world": case["world"], "direction": case["direction"]} in result["violations"],
                "named hand-derived counterexample disagrees")
    # The deliberately tiny public introduction cannot distinguish wrong models.
    registration = results["registrations"]
    require(all(next(c for c in r["checks"] if c["id"] == "intro")["admits"] for r in registration),
            "public introduction should expose no answer")
    require(sum(r["outcome"] == "contradiction" for r in registration) == 25,
            "nontrivial witnesses must discriminate wrong registration models")

    paths = [ROOT / (name + ".json") for name in sources]
    paths += [ROOT / "expected-cases.json", Path(__file__)]
    report = {
        "format": 1, "scope": "trusted finite design examples only",
        "limitations": ["not a general model compiler", "not an equivalence proof",
                        "no production schema, host, browser, UI, privacy or capacity validation"],
        "hashes": {str(path.relative_to(ROOT.parents[2])).replace("\\", "/"):
                   hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "combinations": sum(len(rows) for rows in results.values()),
        "snapshot_evaluations": sum(len(r["checks"]) for rows in results.values() for r in rows),
        "named_counterexamples": len(expected["counterexamples"]),
        "results": results
    }
    report_path = ROOT / "validation.json"
    if args.write_report:
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n",
                               encoding="utf-8", newline="\n")
    else:
        require(report_path.is_file(), "missing validation.json; run --write-report after review")
        require(read("validation.json") == report, "validation record stale; review design before refreshing")
    counts = {name: {outcome: sum(r["outcome"] == outcome for r in rows)
                     for outcome in sorted({r["outcome"] for r in rows})}
              for name, rows in results.items()}
    print(json.dumps({"combinations": report["combinations"],
                      "snapshot_evaluations": report["snapshot_evaluations"],
                      "named_counterexamples": report["named_counterexamples"],
                      "outcomes": counts, "record_matches": True}, indent=2))


if __name__ == "__main__":
    run()

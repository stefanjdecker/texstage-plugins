# SPDX-License-Identifier: Apache-2.0
"""Independent finite oracle: closures are intersections of FD-closed sets.

The browser uses forward chaining and direct tableau replacement. This model uses
closed-set intersections and union/find, with a shared deterministic wire format.
"""
from functools import lru_cache
import json

from .validation import (FORMS, InputError, ResourceLimit, answer, canonical,
                         bounded, compile_lesson, identity, require, seed)


class Budget:
    def __init__(self, limit=1_000_000):
        self.remaining = limit
        self.used = 0

    def tick(self, count=1):
        self.remaining -= count
        self.used += count
        if self.remaining < 0:
            raise ResourceLimit("work")


def subset(left, right):
    return left & right == left


class Theory:
    def __init__(self, exercise, budget=None):
        self.exercise = exercise
        self.n = len(exercise["attributes"])
        self.universe = (1 << self.n) - 1
        self.fds = exercise["fds"]
        self.budget = budget or Budget()
        closed = []
        for mask in range(self.universe + 1):
            good = True
            for left, right in self.fds:
                self.budget.tick()
                if subset(left, mask) and not subset(right, mask):
                    good = False
                    break
            if good:
                closed.append(mask)
        self.closures = []
        for mask in range(self.universe + 1):
            result = self.universe
            for candidate in closed:
                self.budget.tick()
                if subset(mask, candidate):
                    result &= candidate
            self.closures.append(result)
        self.forms = {}

    def describe(self, relation):
        if relation in self.forms:
            return self.forms[relation]
        masks = sorted((x for x in range(self.universe + 1) if subset(x, relation)),
                       key=lambda x: (x.bit_count(), x))
        keys = []
        for mask in masks:
            self.budget.tick()
            if self.closures[mask] & relation == relation:
                minimal = True
                for i in range(self.n):
                    self.budget.tick()
                    if mask & (1 << i) and self.closures[mask ^ (1 << i)] & relation == relation:
                        minimal = False
                if minimal:
                    keys.append(mask)
        prime = 0
        for key in keys:
            prime |= key
        witnesses = {"2nf": None, "3nf": None, "bcnf": None}
        for left in masks:
            reached = self.closures[left] & relation
            for i in range(self.n):
                self.budget.tick()
                right = 1 << i
                if not (right & reached) or right & left:
                    continue
                if reached != relation:
                    witnesses["bcnf"] = witnesses["bcnf"] or [left, right]
                    if not right & prime:
                        witnesses["3nf"] = witnesses["3nf"] or [left, right]
                if not right & prime:
                    for key in keys:
                        self.budget.tick()
                        if left != key and subset(left, key):
                            witnesses["2nf"] = witnesses["2nf"] or [left, right]
                            break
        form = "bcnf" if witnesses["bcnf"] is None else "3nf" if witnesses["3nf"] is None else "2nf" if witnesses["2nf"] is None else "1nf"
        result = {"relation": relation, "normal_form": form, "prime": prime, "witnesses": witnesses}
        self.forms[relation] = (result, sorted(keys))
        return self.forms[relation]

    def witness_valid(self, claim, witness):
        if claim == "bcnf":
            return witness is None
        if witness is None:
            return False
        left, right = witness
        description, keys = self.describe(self.universe)
        if left & right or not self.closures[left] & right:
            return False
        if claim == "1nf":
            return not right & description["prime"] and any(left != k and subset(left, k) for k in keys)
        nonkey = self.closures[left] != self.universe
        return nonkey and (claim == "3nf" or not right & description["prime"])

    def preservation(self, parts):
        # Independently construct the union of all singleton projected dependencies.
        projected = set()
        for part in parts:
            for left in range(self.universe + 1):
                self.budget.tick()
                if subset(left, part):
                    reached = self.closures[left] & part & ~left
                    for i in range(self.n):
                        if reached & (1 << i):
                            projected.add((left, 1 << i))
        projected = sorted(projected)
        for index, (left, right) in enumerate(self.fds):
            reached = left
            while True:
                before = reached
                for x, a in projected:
                    self.budget.tick()
                    if subset(x, reached):
                        reached |= a
                if reached == before:
                    break
            if not reached & right:
                return {"preserved": False, "fd": index, "closure": reached}
        return {"preserved": True, "fd": -1, "closure": 0}

    def chase(self, parts):
        n, m = self.n, len(parts)
        symbols = [[j if part & (1 << j) else n + i * n + j
                    for j in range(n)] for i, part in enumerate(parts)]
        parent = list(range(n + n * m))
        def find(symbol):
            while parent[symbol] != symbol:
                self.budget.tick()
                symbol = parent[symbol]
            return symbol
        trace = []
        while True:
            before = len(trace)
            for f, (left, right) in enumerate(self.fds):
                col = right.bit_length() - 1
                determinant = [j for j in range(n) if left & (1 << j)]
                for i in range(m):
                    for k in range(i + 1, m):
                        self.budget.tick()
                        if all(find(symbols[i][j]) == find(symbols[k][j]) for j in determinant):
                            a, b = find(symbols[i][col]), find(symbols[k][col])
                            if a != b:
                                parent[max(a, b)] = min(a, b)
                                trace.append([f, i, k])
            if len(trace) == before:
                break
        table = [[find(s) for s in row] for row in symbols]
        require(len(trace) <= n * (m - 1), "chase-bound")
        return {"lossless": list(range(n)) in table, "rows": m, "columns": n,
                "merges": trace, "tableau": table}


def analyze(exercise, submitted, budget=None):
    exercise = seed(exercise)
    submitted = answer(submitted, exercise)
    theory = Theory(exercise, budget)
    mode = exercise["task"]["mode"]
    data = {"format": 1, "exercise": identity("normalization-exercise-v1", exercise),
            "answer": identity("normalization-answer-v1", submitted), "mode": mode}
    if mode == "classify":
        description, keys = theory.describe(theory.universe)
        data["facts"] = {k: v for k, v in description.items() if k != "relation"}
        data["facts"].update(keys=keys, witness_valid=theory.witness_valid(
            submitted["normal_form"], submitted["witness"]))
    else:
        parts = submitted["relations"]
        cover = 0
        for p in parts:
            cover |= p
        covered = cover == theory.universe
        data["facts"] = {"covered": covered, "missing": theory.universe & ~cover,
                         "components": [theory.describe(p)[0] for p in parts],
                         "preservation": theory.preservation(parts) if covered else None,
                         "join": theory.chase(parts) if covered else None}
    if len(canonical(data)) > 8192:
        raise ResourceLimit("data-bytes")
    return data


def accepted(exercise, submitted, facts):
    """Lesson policy helper; call verify_analysis before using untrusted facts."""
    if exercise["task"]["mode"] == "classify":
        return facts["normal_form"] == submitted["normal_form"] and facts["witness_valid"]
    return (facts["covered"] and facts["join"]["lossless"] and
            all(FORMS.index(c["normal_form"]) >= FORMS.index(exercise["task"]["target"])
                for c in facts["components"]) and
            (not exercise["task"]["preserve"] or facts["preservation"]["preserved"]))


@lru_cache(maxsize=64)
def _expected_analysis(exercise_text, submitted_text):
    """Immutable independent facts, keyed by the complete seed and answer.

    Never cache a worker's supplied facts or a student's grade. Valid inputs and
    the analysis contract bound each entry; LRU eviction bounds retained entries.
    """
    return canonical(analyze(json.loads(exercise_text), json.loads(submitted_text)))


def verify_analysis(exercise, submitted, data, budget=None):
    """Bounded independent verification, including every certificate and identity.

    Host lease/namespace/epoch checks remain the caller's responsibility.
    Canonical comparison is against an independently computed analysis of THIS
    answer, never against a teacher's preferred answer.
    """
    try:
        if type(data) is not dict:
            return False
        encoded = canonical(bounded(data))
        if len(encoded) > 8192:
            return False
    except (InputError, ResourceLimit, TypeError, ValueError, RecursionError):
        return False
    expected = (canonical(analyze(exercise, submitted, budget)) if budget is not None
                else _expected_analysis(canonical(exercise), canonical(submitted)))
    return encoded == expected


def check_lesson(value):
    exercise, worked, diagnostics = compile_lesson(value)
    data = analyze(exercise, worked)
    require(accepted(exercise, worked, data["facts"]), "incorrect-worked-answer")
    return {"seed": exercise, "answer": worked, "analysis": data, "diagnostics": diagnostics}

# SPDX-License-Identifier: Apache-2.0
"""Independent bounded Python model; no browser code or design-checker imports."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
import unicodedata

MODEL = "teaching-cost-v1"
FORMAT = "query-plan-analysis-v1"
SEED_MAX, ANSWER_MAX, LESSON_MAX = 32768, 1024, 98304
COST_MAX = 3000000000000


class InputError(ValueError):
    pass


class ResourceLimit(ValueError):
    pass


class DomainError(ValueError):
    def __init__(self, reason, node=-1):
        super().__init__(reason)
        self.reason, self.node = reason, node


def require(ok, message="Invalid query-plan input"):
    if not ok:
        raise InputError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _text(value, low, high):
    return (type(value) is str and low <= len(value) <= high
            and not any(0xD800 <= ord(c) <= 0xDFFF for c in value))


def _id(value):
    return type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,15}", value) is not None


def _fields(value, names, optional=()):
    require(type(value) is dict and set(names) <= set(value)
            and set(value) <= set(names) | set(optional))


def _array(value, low, high):
    require(type(value) is list and low <= len(value) <= high)


def _plain(value):
    count = 0
    def visit(item, depth):
        nonlocal count
        count += 1
        require(count <= 2048 and depth <= 16, "JSON complexity")
        if type(item) is dict:
            for key, child in item.items():
                require(_text(key, 0, 98304))
                visit(child, depth + 1)
        elif type(item) is list:
            for child in item:
                visit(child, depth + 1)
        else:
            require(item is None or type(item) is bool or
                    _integer(item, -9007199254740991, 9007199254740991) or
                    _text(item, 0, 98304), "Nonportable JSON")
    visit(value, 0)


def _budget(value, limit):
    _plain(value)
    if len(canonical(value)) > limit:
        raise ResourceLimit("canonical-bytes")


def parse(text, byte_limit=SEED_MAX):
    require(type(text) is str)
    try:
        if len(text.encode("utf-8")) > byte_limit:
            raise ResourceLimit("input-bytes")
    except UnicodeError as exc:
        raise InputError("Unicode scalar values required") from exc
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def no_number(_):
        raise InputError("Integer JSON tokens required")
    def number(raw):
        require(len(raw) <= 17)
        value = int(raw)
        require(abs(value) <= 9007199254740991)
        return value
    # Bound nesting before handing text to the standard-library parser.
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            require(depth <= 17, "JSON complexity")
        elif char in "]}":
            depth -= 1
    try:
        result = json.loads(text, object_pairs_hook=pairs, parse_float=no_number,
                            parse_constant=no_number, parse_int=number)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise InputError("Invalid bounded JSON") from exc
    _plain(result)
    return result


def _connected(mask, edges):
    if not mask:
        return False
    reached = mask & -mask
    while True:
        previous = reached
        for edge in edges:
            if edge & mask == edge and edge & reached:
                reached |= edge
        if previous == reached:
            return reached == mask


def source(value):
    """Validate semantic invariants and return an owned, normalized source."""
    _budget(value, SEED_MAX)
    _fields(value, ("format", "model", "query", "statistics", "limits"))
    require(_integer(value["format"], 1, 1) and value["model"] == MODEL)
    query = value["query"]
    _fields(query, ("relations", "joins", "output"))
    _array(query["relations"], 1, 3)
    relations = {}
    for relation in query["relations"]:
        _fields(relation, ("id", "columns"), ("filter", "index"))
        name = relation["id"]
        require(_id(name) and name not in relations, "Relation identity")
        _array(relation["columns"], 1, 8)
        columns = {}
        for column in relation["columns"]:
            _fields(column, ("id", "type"))
            require(_id(column["id"]) and column["id"] not in columns
                    and column["type"] in ("int", "text", "bool"), "Columns")
            columns[column["id"]] = column["type"]
        if "filter" in relation:
            f = relation["filter"]
            _fields(f, ("column", "value"))
            require(_id(f["column"]) and f["column"] in columns)
            v, t = f["value"], columns[f["column"]]
            require((t == "int" and _integer(v, -1000000, 1000000)) or
                    (t == "bool" and type(v) is bool) or
                    (t == "text" and _text(v, 0, 64) and
                     unicodedata.normalize("NFC", v) == v), "Filter type/NFC")
        if "index" in relation:
            index = relation["index"]
            _fields(index, ("column", "height"))
            require("filter" in relation and _id(index["column"]) and
                    index["column"] == relation["filter"]["column"] and
                    _integer(index["height"], 1, 8), "Index eligibility")
        relations[name] = columns
    names = sorted(relations)
    bits = {name: 1 << index for index, name in enumerate(names)}
    def column_ref(ref):
        _array(ref, 2, 2)
        require(all(_id(v) for v in ref) and ref[0] in relations
                and ref[1] in relations[ref[0]], "Column reference")
        return relations[ref[0]][ref[1]]
    _array(query["joins"], len(names) - 1, len(names) - 1)
    edges, joins = [], []
    for join in query["joins"]:
        _fields(join, ("left", "right"))
        require(column_ref(join["left"]) == column_ref(join["right"]), "Join type")
        a, b = join["left"][0], join["right"][0]
        require(a != b, "Self join")
        edge = bits[a] | bits[b]
        require(edge not in edges, "Parallel join")
        edges.append(edge)
        left, right = sorted((join["left"], join["right"]))
        joins.append({"left": left, "right": right})
    require(_connected((1 << len(names)) - 1, edges), "Disconnected query")
    _array(query["output"], 1, 8)
    for ref in query["output"]:
        column_ref(ref)
    stats = value["statistics"]
    _fields(stats, ("base", "cardinalities"))
    _array(stats["base"], len(names), len(names))
    bases = {}
    for base in stats["base"]:
        _fields(base, ("relation", "rows", "pages", "row_bytes"))
        name = base["relation"]
        require(_id(name) and name in bits and name not in bases)
        require(_integer(base["rows"], 0, 1000000) and
                _integer(base["pages"], 0, 1000000) and
                _integer(base["row_bytes"], 1, 1024), "Base bounds")
        require(base["rows"] == 0 or base["pages"] > 0, "Nonempty table pages")
        bases[name] = base
    _array(stats["cardinalities"], 1, 7)
    cards = {}
    for card in stats["cardinalities"]:
        _fields(card, ("relations", "rows"))
        _array(card["relations"], 1, 3)
        require(all(_id(n) and n in bits for n in card["relations"]))
        require(len(set(card["relations"])) == len(card["relations"]))
        mask = sum(bits[n] for n in card["relations"])
        require(mask not in cards and _integer(card["rows"], 0, 1000000))
        cards[mask] = card["rows"]
    expected = {m for m in range(1, 1 << len(names)) if _connected(m, edges)}
    require(set(cards) == expected, "Exact connected-subset coverage")
    by_name = {r["id"]: r for r in query["relations"]}
    for mask, rows in cards.items():
        if mask.bit_count() == 1:
            name = next(n for n in names if bits[n] == mask)
            require(rows <= bases[name]["rows"])
            require("filter" in by_name[name] or rows == bases[name]["rows"],
                    "Unfiltered rows")
        else:
            for left in cards:
                right = mask ^ left
                if left & mask == left and left != mask and right in cards:
                    require(rows <= cards[left] * cards[right], "Impossible estimate")
    _fields(value["limits"], ("hash_bytes",))
    require(_integer(value["limits"]["hash_bytes"], 0, 16777216))
    normalized = copy.deepcopy(value)
    normalized["query"]["relations"] = sorted(normalized["query"]["relations"], key=lambda r: r["id"])
    for relation in normalized["query"]["relations"]:
        relation["columns"].sort(key=lambda c: c["id"])
    normalized["query"]["joins"] = sorted(copy.deepcopy(joins), key=canonical)
    normalized["statistics"]["base"] = [copy.deepcopy(bases[n]) for n in names]
    normalized["statistics"]["cardinalities"] = [
        {"relations": [n for n in names if bits[n] & mask], "rows": cards[mask]}
        for mask in sorted(cards)]
    return normalized


def answer(value):
    _budget(value, ANSWER_MAX)
    _fields(value, ("format", "nodes"))
    require(_integer(value["format"], 1, 1))
    _array(value["nodes"], 1, 5)
    for node in value["nodes"]:
        require(type(node) is dict)
        if node.get("op") == "scan":
            _fields(node, ("op", "relation", "method"))
            require(_id(node["relation"]) and node["method"] in ("seq", "index"))
        elif node.get("op") == "join":
            _fields(node, ("op", "left", "right", "method"))
            require(_integer(node["left"], 0, 3) and _integer(node["right"], 0, 3)
                    and node["method"] in ("nested", "hash-left", "hash-right"))
        else:
            raise InputError("Unknown operator")
    return copy.deepcopy(value)


def exercise_identity(exercise):
    return digest(["query-plan-exercise-v1", source(exercise)])


def _evaluate(exercise, submission):
    nodes = submission["nodes"]
    parents = [0] * len(nodes)
    def domain(ok, reason, node=-1):
        if not ok:
            raise DomainError(reason, node)
    for index, node in enumerate(nodes):
        if node["op"] == "join":
            for child in (node["left"], node["right"]):
                domain(child < index, "invalid-tree", index)
                parents[child] += 1
    domain(parents[-1] == 0 and all(n == 1 for n in parents[:-1]), "invalid-tree")
    order = []
    def visit(index):
        node = nodes[index]
        if node["op"] == "join":
            visit(node["left"])
            visit(node["right"])
        order.append(index)
    visit(len(nodes) - 1)
    domain(order == list(range(len(nodes))), "invalid-tree")
    relations = {r["id"]: r for r in exercise["query"]["relations"]}
    bits = {name: 1 << i for i, name in enumerate(relations)}
    bases = {b["relation"]: b for b in exercise["statistics"]["base"]}
    cards = {sum(bits[n] for n in c["relations"]): c["rows"]
             for c in exercise["statistics"]["cardinalities"]}
    seen, facts = set(), []
    for index, node in enumerate(nodes):
        method = node["method"]
        if node["op"] == "scan":
            name = node["relation"]
            domain(name in relations, "unknown-relation", index)
            domain(name not in seen, "duplicate-relation", index)
            seen.add(name)
            mask, base = bits[name], bases[name]
            rows, width, memory = cards[mask], base["row_bytes"], 0
            if method == "seq":
                local = 100 * base["pages"] + base["rows"]
            else:
                domain("index" in relations[name], "unavailable-index", index)
                local = 400 * (relations[name]["index"]["height"] + rows) + rows
            total = local
        else:
            left, right = facts[node["left"]], facts[node["right"]]
            mask = left["subset"] | right["subset"]
            domain(not left["subset"] & right["subset"], "duplicate-relation", index)
            domain(mask in cards, "disconnected-join", index)
            rows, width = cards[mask], left["row_bytes"] + right["row_bytes"]
            if method == "nested":
                local, memory = left["rows"] * right["rows"] + rows, 0
            else:
                build, probe = (left, right) if method == "hash-left" else (right, left)
                memory = build["rows"] * (build["row_bytes"] + 16)
                domain(memory <= exercise["limits"]["hash_bytes"], "hash-memory", index)
                local = 2 * build["rows"] + probe["rows"] + rows
            total = local + left["total_cost"] + right["total_cost"]
        require(0 <= total <= COST_MAX, "Cost bound")
        facts.append({"node": index, "subset": mask, "rows": rows, "row_bytes": width,
                      "local_cost": local, "total_cost": total, "hash_bytes": memory})
    domain(len(seen) == len(relations), "missing-relation")
    return {"cost": facts[-1]["total_cost"], "nodes": facts}


def analyze(exercise, submission):
    exercise, submission = source(exercise), answer(submission)
    result = {"format": FORMAT, "model": MODEL,
              "exercise": digest(["query-plan-exercise-v1", exercise]),
              "answer": digest(["query-plan-answer-v1", submission])}
    try:
        result |= {"valid": True, **_evaluate(exercise, submission)}
    except DomainError as exc:
        result |= {"valid": False, "reason": exc.reason, "node": exc.node}
    _budget(result, 8192)
    return result


def candidates(exercise):
    """All <=864 ordered candidates; feasibility is intentionally checked later."""
    exercise = source(exercise)
    relations = {r["id"]: r for r in exercise["query"]["relations"]}
    def trees(names):
        if len(names) == 1:
            name = names[0]
            for method in (("seq", "index") if "index" in relations[name] else ("seq",)):
                yield ("scan", name, method)
        else:
            for size in range(1, len(names)):
                for left in itertools.combinations(names, size):
                    right = tuple(n for n in names if n not in left)
                    for a in trees(left):
                        for b in trees(right):
                            for method in ("nested", "hash-left", "hash-right"):
                                yield ("join", a, b, method)
    for tree in trees(tuple(relations)):
        nodes = []
        def append(item):
            if item[0] == "scan":
                node = {"op": "scan", "relation": item[1], "method": item[2]}
            else:
                left, right = append(item[1]), append(item[2])
                node = {"op": "join", "left": left, "right": right, "method": item[3]}
            nodes.append(node)
            return len(nodes) - 1
        append(tree)
        yield {"format": 1, "nodes": nodes}


def optimum(exercise):
    """Reference enumeration only; retain one deterministic representative of ties."""
    exercise = source(exercise)
    best, count, chosen, total, feasible = None, 0, None, 0, 0
    for submission in candidates(exercise):
        total += 1
        require(total <= 864, "Enumeration bound")
        try:
            cost = _evaluate(exercise, submission)["cost"]
        except DomainError:
            continue
        feasible += 1
        if best is None or cost < best:
            best, count, chosen = cost, 1, submission
        elif cost == best:
            count += 1
            if canonical(submission) < canonical(chosen):
                chosen = submission
    require(chosen is not None, "No feasible plan")
    return {"cost": best, "count": count, "plan": chosen,
            "candidates": total, "feasible": feasible}


def prepare_reference(value):
    """Validate the frozen future lesson source, without declaring a lesson hook."""
    _budget(value, LESSON_MAX)
    _fields(value, ("format", "exercise", "baseline", "goal", "worked_answer", "explanation"), ("points", "time"))
    require(_integer(value.get("points", 0), 0, 10000), "Activity points must be 0–10000")
    require(_integer(value.get("time", 120), 1, 3600), "Scoring time must be 1–3600 seconds")
    require(_integer(value["format"], 1, 1))
    exercise = source(value["exercise"])
    baseline, worked = answer(value["baseline"]), answer(value["worked_answer"])
    goal = value["goal"]
    require(type(goal) is dict)
    if goal.get("kind") == "best":
        _fields(goal, ("kind",))
    else:
        _fields(goal, ("kind", "max_cost"))
        require(goal["kind"] == "budget" and _integer(goal["max_cost"], 0, COST_MAX))
    _fields(value["explanation"], ("en", "de"))
    require(all(_text(t, 1, 2000) and unicodedata.normalize("NFC", t) == t
                for t in value["explanation"].values()))
    reference = optimum(exercise)
    ceiling = reference["cost"] if goal["kind"] == "best" else goal["max_cost"]
    require(ceiling >= reference["cost"], "Unreachable goal")
    baseline_facts, worked_facts = analyze(exercise, baseline), analyze(exercise, worked)
    require(baseline_facts["valid"], "Invalid baseline")
    require(worked_facts["valid"] and worked_facts["cost"] <= ceiling,
            "Worked answer misses goal")
    return {"source": {"format": 1, "exercise": exercise, "baseline": baseline,
                      "goal": copy.deepcopy(goal), "worked_answer": worked,
                      "explanation": copy.deepcopy(value["explanation"]), "points": value.get("points", 0), "time": value.get("time", 120)},
            "reference": reference, "baseline": baseline_facts, "worked": worked_facts}

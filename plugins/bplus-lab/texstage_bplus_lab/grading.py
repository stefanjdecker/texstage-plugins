# SPDX-License-Identifier: Apache-2.0
"""Fixed partial credit from independently verified B+ facts, never elapsed time.

One thousand credit units mean 100%. The host scales these units to the author's
point maximum. Each component is rounded down; full correctness earns all 1000.
"""
from . import model

RUBRIC = 'bplus-partial-v1'
CRITERIA = ('path', 'scan', 'keys', 'repairs', 'separators', 'height')
WEIGHTS = {
    'lookup': {'path': 400, 'keys': 600},
    'range': {'path': 300, 'scan': 400, 'keys': 300},
    'insert': {'path': 200, 'repairs': 500, 'separators': 200, 'height': 100},
    'delete': {'path': 200, 'repairs': 500, 'separators': 200, 'height': 100},
}


def rubric(kind):
    return {'id': RUBRIC, 'weights': dict(WEIGHTS[kind])}


def prefix(actual, expected):
    matched = 0
    for left, right in zip(actual, expected):
        if left != right:
            break
        matched += 1
    return matched


def path_credit(actual, expected, maximum):
    # The editor supplies the root. Credit routing edges, not that free root.
    if not actual or actual[0] != expected[0]:
        return 0
    steps = max(len(actual), len(expected)) - 1
    return maximum if steps == 0 else maximum * max(0, prefix(actual, expected) - 1) // steps


def key_credit(actual, expected, maximum):
    if actual != sorted(set(actual)):
        return 0  # Ordered unique results are part of the answer contract.
    wanted, supplied = set(expected), set(actual)
    if not wanted:
        return maximum if not supplied else 0
    return maximum * max(0, len(wanted & supplied) - len(supplied - wanted)) // len(wanted)


def separator_credit(actual, expected, maximum):
    ids = [row['node'] for row in actual]
    if ids != sorted(set(ids)):
        return 0
    wanted = {(row['node'], i): key for row in expected for i, key in enumerate(row['keys'])}
    supplied = {(row['node'], i): key for row in actual for i, key in enumerate(row['keys'])}
    if not wanted:
        return maximum if not supplied else 0
    hits = sum(position in supplied and supplied[position] == key for position, key in wanted.items())
    extra = len(supplied.keys() - wanted.keys())
    return maximum * max(0, hits - extra) // len(wanted)


def grade(seed, answer, verified):
    """Grade facts already matched to independent replay by the lesson reducer.

    Reading criteria are independent. Update predictions require a complete legal
    replay of the submitted repair choices; another legal choice is equally valid.
    An unfinished/invalid update earns 10 percentage points per verified repair,
    at most 20, instead of the full 50-point repair component.
    """
    kind = seed['task']['kind']
    weights = WEIGHTS[kind]
    budget = model.Budget()
    root, before = model.read_tree(seed['tree'], seed['leaf_capacity'], seed['internal_capacity'], budget)
    key = seed['task']['lower'] if kind == 'range' else seed['task']['key']
    route, leaf = model.path_for(root, key, budget)
    parts = {'path': path_credit(answer['path'], route, weights['path'])}
    if kind in ('lookup', 'range'):
        wanted = [k for k in before['keys'] if (k == key if kind == 'lookup' else key <= k <= seed['task']['upper'])]
        if kind == 'range':
            nodes = {node['id']: node for node in seed['tree']['nodes']}
            scan, current = [], leaf.id
            while True:
                node = nodes[current]; scan.append(current)
                budget.charge(1 + len(node['keys']))
                if not node['keys'] or node['keys'][-1] >= seed['task']['upper'] or node['next'] is None:
                    break
                current = node['next']
            parts['scan'] = weights['scan'] * prefix(answer['leaves'], scan) // max(len(answer['leaves']), len(scan))
        parts['keys'] = key_credit(answer['keys'], wanted, weights['keys'])
    else:
        complete = verified['replay']['state'] == 'complete'
        parts['repairs'] = weights['repairs'] if complete else min(200, 100 * verified['replay']['checked_repairs'])
        parts['separators'] = parts['height'] = 0
        if complete:
            expected = [{'node': node['id'], 'keys': node['keys']} for node in verified['final']['nodes'] if node['kind'] == 'internal']
            parts['separators'] = separator_credit(answer['separators'], expected, weights['separators'])
            parts['height'] = weights['height'] if verified['claims']['height'] else 0
    return {'rubric': RUBRIC, 'credit': sum(parts.values()), 'parts': parts}

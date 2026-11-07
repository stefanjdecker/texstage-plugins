# SPDX-License-Identifier: Apache-2.0
"""Bounded Python schedule model, independent of the browser graph traversal."""
import copy
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent
EXERCISE = Draft202012Validator(json.loads((ROOT / 'schemas/exercise-v1.json').read_text(encoding='utf-8')))
ANALYSIS = Draft202012Validator(json.loads((ROOT / 'schemas/analysis-result.json').read_text(encoding='utf-8')))
MAX_VALUE = 1_120_000


class InputError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def require(ok, code):
    if not ok:
        raise InputError(code)


def operations(exercise):
    return {op['id']: dict(op, transaction=t['id']) for t in exercise['transactions'] for op in t['operations']}


def validate(exercise):
    try:
        require(len(canonical(exercise).encode('ascii')) <= 32768, 'exercise-size')
        EXERCISE.validate(exercise)
    except (ValidationError, TypeError, OverflowError, RecursionError) as error:
        raise InputError('exercise-shape') from error
    require(len({t['id'] for t in exercise['transactions']}) == len(exercise['transactions']), 'transaction-id')
    seen, reads, rw = set(), set(), 0
    for transaction in exercise['transactions']:
        program = transaction['operations']
        require(program[-1]['kind'] == 'commit' and sum(o['kind'] == 'commit' for o in program) == 1, 'terminal-commit')
        reads.clear()
        for op in program:
            require(op['id'] not in seen, 'operation-id')
            seen.add(op['id'])
            if op['kind'] == 'commit':
                continue
            rw += 1
            require(op['object'] in exercise['initial'], 'unknown-object')
            if op['kind'] == 'read':
                reads.add(op['id'])
            elif 'read' in op['value']:
                require(op['value']['read'] in reads, 'earlier-own-read')
    require(rw <= 12, 'operation-limit')
    order(exercise, exercise['schedule'])
    return copy.deepcopy(exercise)


def order(exercise, value):
    require(isinstance(value, list) and 4 <= len(value) <= 15 and all(isinstance(x, str) for x in value), 'order-shape')
    known = operations(exercise)
    require(len(set(value)) == len(value) == len(known) and set(value) == set(known), 'operation-permutation')
    for transaction in exercise['transactions']:
        program = [op['id'] for op in transaction['operations']]
        require([x for x in value if x in program] == program, 'program-order')
    return list(value)


def identity(exercise):
    return digest({k: copy.deepcopy(exercise[k]) for k in ('format', 'id', 'initial', 'schedule')} | {
        'transactions': sorted(exercise['transactions'], key=lambda t: t['id'])})


def certificate_ok(vertices, edges, kind, sequence):
    if not isinstance(sequence, list) or not all(isinstance(v, str) for v in sequence):
        return False
    arcs = {(e['from'], e['to']) for e in edges}
    if kind == 'serial':
        return (len(sequence) == len(vertices) and set(sequence) == set(vertices)
                and all(sequence.index(a) < sequence.index(b) for a, b in arcs))
    return (kind == 'cycle' and 3 <= len(sequence) <= len(vertices) + 1
            and sequence[0] == sequence[-1] and len(set(sequence[:-1])) == len(sequence) - 1
            and set(sequence) <= set(vertices)
            and all((a, b) in arcs for a, b in zip(sequence, sequence[1:])))


def analyze(exercise, proposed=None):
    """Simulation plus exhaustive <=3-vertex certificates, not the engine's DFS."""
    proposed = order(exercise, exercise['schedule'] if proposed is None else proposed)
    ops = operations(exercise)
    values, reads, trace, witnesses = dict(exercise['initial']), {}, [], {}
    for oid in proposed:
        op, step = ops[oid], {'operation': oid}
        if op['kind'] == 'read':
            reads[oid] = step['value'] = values[op['object']]
        elif op['kind'] == 'write':
            value = op['value']
            values[op['object']] = step['value'] = value['constant'] if 'constant' in value else reads[value['read']] + value['add']
        trace.append(step)
    for left, right in combinations(proposed, 2):
        a, b = ops[left], ops[right]
        if (a['kind'] != 'commit' and b['kind'] != 'commit' and a['transaction'] != b['transaction']
                and a['object'] == b['object'] and 'write' in (a['kind'], b['kind'])):
            witnesses.setdefault((a['transaction'], b['transaction']), []).append([left, right])
    edges = [{'from': a, 'to': b, 'witnesses': sorted(pairs)} for (a, b), pairs in sorted(witnesses.items())]
    vertices = sorted(t['id'] for t in exercise['transactions'])
    serial = next((list(p) for p in permutations(vertices) if certificate_ok(vertices, edges, 'serial', list(p))), [])
    cycle = []
    if not serial:
        for length in range(2, len(vertices) + 1):
            cycle = next((list(p) + [p[0]] for p in permutations(vertices, length)
                          if certificate_ok(vertices, edges, 'cycle', list(p) + [p[0]])), [])
            if cycle:
                break
    return {'format': 'schedule-analysis-v1', 'exercise': identity(exercise), 'order': proposed, 'valid': True,
            'vertices': vertices, 'final': values, 'reads': reads, 'trace': trace, 'edges': edges,
            'acyclic': bool(serial), 'serial_order': serial, 'cycle': cycle}


def verify_analysis(exercise, proposed, facts):
    """Verify this answer's facts; accept any valid certificate, not one chosen DFS."""
    try:
        ANALYSIS.validate(facts)
        expected = analyze(exercise, proposed)
        fields = set(expected) - {'serial_order', 'cycle'}
        if not isinstance(facts, dict) or any(facts.get(k) != expected[k] for k in fields):
            return False
        kind = 'serial' if expected['acyclic'] else 'cycle'
        return (not facts['cycle' if expected['acyclic'] else 'serial_order']
                and certificate_ok(expected['vertices'], expected['edges'], kind,
                                   facts['serial_order' if expected['acyclic'] else 'cycle']))
    except (ValidationError, InputError, KeyError, TypeError, ValueError):
        return False


def answer(exercise, phase, value):
    require(isinstance(value, dict), 'answer-shape')
    if phase == 'prediction':
        require(set(value) == {'values'} and isinstance(value['values'], dict), 'prediction-shape')
        require(set(value['values']) == set(exercise['initial']), 'prediction-objects')
        require(all(type(v) is int and abs(v) <= MAX_VALUE for v in value['values'].values()), 'prediction-value')
    elif phase == 'repair':
        require(set(value) == {'order'}, 'repair-shape')
        order(exercise, value['order'])
    elif phase == 'diagnosis':
        require(set(value) == {'edges', 'certificate'}, 'diagnosis-shape')
        require(isinstance(value['edges'], list) and len(value['edges']) <= 6, 'edge-shape')
        vertices = {t['id'] for t in exercise['transactions']}
        ops, seen = operations(exercise), set()
        for edge in value['edges']:
            require(isinstance(edge, dict) and set(edge) == {'from', 'to', 'witness'}, 'edge-shape')
            a, b = edge['from'], edge['to']
            require(isinstance(a, str) and isinstance(b, str) and a in vertices and b in vertices and a != b, 'edge-vertices')
            require((a, b) not in seen, 'edge-duplicate')
            seen.add((a, b))
            witness = edge['witness']
            require(isinstance(witness, list) and len(witness) == 2 and all(isinstance(x, str) and x in ops for x in witness), 'witness-shape')
        cert = value['certificate']
        require(isinstance(cert, dict) and set(cert) == {'kind', 'vertices'} and cert['kind'] in ('serial', 'cycle'), 'certificate-shape')
        require(isinstance(cert['vertices'], list) and len(cert['vertices']) <= 4
                and all(isinstance(x, str) and x in vertices for x in cert['vertices']), 'certificate-vertices')
        value = dict(value, edges=sorted(value['edges'], key=lambda e: (e['from'], e['to'])))
    else:
        raise InputError('answer-phase')
    return copy.deepcopy(value)


def snapshot(exercise, trace, cursor):
    values, reads = dict(exercise['initial']), {}
    ops = operations(exercise)
    for step in trace[:cursor]:
        op = ops[step['operation']]
        if op['kind'] == 'read':
            reads[op['id']] = step['value']
        elif op['kind'] == 'write':
            values[op['object']] = step['value']
    return {'values': values, 'reads': reads, 'operation': trace[cursor - 1]['operation'] if cursor else None}

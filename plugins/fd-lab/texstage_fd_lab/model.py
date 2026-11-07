# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Independent set-based FD model and named-source compiler; no session state."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import unicodedata

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent
VALIDATORS = {name: Draft202012Validator(json.loads(
    (ROOT / 'schemas' / (name + '-v1.json')).read_text(encoding='utf-8')))
    for name in ('seed', 'answer', 'lesson', 'analysis-result')}


class InputError(ValueError):
    """Malformed input, distinct from a mathematically wrong answer."""


class ResourceLimit(ValueError):
    """A deterministic work or byte budget was exceeded."""


@dataclass
class Budget:
    remaining: int = 65536

    def charge(self):
        self.remaining -= 1
        if self.remaining < 0:
            raise ResourceLimit('work-limit')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def require(condition, reason='invalid-input'):
    if not condition:
        raise InputError(reason)


def normalize(value, depth=0, count=None):
    count = [0] if count is None else count
    count[0] += 1
    require(depth <= 16 and count[0] <= 8192, 'json-complexity')
    if type(value) is str:
        require(not any(0xD800 <= ord(c) <= 0xDFFF for c in value), 'unpaired-surrogate')
        return unicodedata.normalize('NFC', value)
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        require(abs(value) <= 9007199254740991, 'unsafe-integer')
        return value
    if type(value) is list:
        return [normalize(v, depth + 1, count) for v in value]
    require(type(value) is dict and all(type(k) is str for k in value), 'json-type')
    result = {}
    for k, v in value.items():
        key = normalize(k, depth + 1, count)
        require(key not in result, 'duplicate-key')
        result[key] = normalize(v, depth + 1, count)
    return result


def parse(text, limit=32768):
    require(type(text) is str, 'json-text')
    try:
        if len(text.encode('utf-8')) > limit:
            raise ResourceLimit('input-bytes')
    except UnicodeEncodeError as error:
        raise InputError('unpaired-surrogate') from error

    def pairs(items):
        result = {}
        for key, value in items:
            key = unicodedata.normalize('NFC', key)
            require(key not in result, 'duplicate-key')
            result[key] = value
        return result

    def invalid(_value):
        raise InputError('integer-tokens-required')

    try:
        return normalize(json.loads(text, object_pairs_hook=pairs, parse_float=invalid, parse_constant=invalid))
    except (ValueError, RecursionError) as error:
        raise InputError('json-syntax') from error


def validated(name, value):
    value = normalize(value)
    try:
        VALIDATORS[name].validate(value)
    except ValidationError as error:
        raise InputError(name + '-shape') from error
    return value


def source(value):
    value = validated('seed', value)
    if len(canonical(value).encode('utf-8')) > 32768:
        raise ResourceLimit('seed-bytes')
    universe = (1 << len(value['attributes'])) - 1
    require(len({fd['id'] for fd in value['fds']}) == len(value['fds']), 'duplicate-fd-id')
    masks = [v for fd in value['fds'] for v in (fd['lhs'], fd['rhs'])]
    masks += [value['task'][field] for field in ('start', 'lhs', 'rhs') if field in value['task']]
    require(all(type(m) is int and 0 <= m <= universe for m in masks), 'mask-outside-relation')
    return value


def answer_for(seed, value):
    answer = validated('answer', value)
    require(answer['mode'] == seed['task']['mode'], 'wrong-mode')
    universe = (1 << len(seed['attributes'])) - 1
    masks = answer.get('keys', []) + [answer[k] for k in ('closure', 'agree') if k in answer]
    require(all(type(m) is int and 0 <= m <= universe for m in masks), 'mask-outside-relation')
    require(all(type(i) is int and 0 <= i < len(seed['fds']) for i in answer.get('steps', [])), 'fd-index')
    if 'keys' in answer:
        if seed['task']['require'] == 'one':
            require(len(answer['keys']) == 1, 'one-key-required')
        answer['keys'].sort()
    if len(canonical(answer)) > 1800:
        raise ResourceLimit('answer-bytes')
    return answer


def members(mask):
    return {i for i in range(8) if mask & (1 << i)}


def mask_of(values):
    return sum(1 << i for i in values)


def closure(start, fds, budget=None):
    """Set-based fixed point, independent of the browser bit-mask implementation."""
    budget = Budget() if budget is None else budget
    known = members(start)
    dependencies = [(members(fd['lhs']), members(fd['rhs'])) for fd in fds]
    while True:
        before = set(known)
        for lhs, rhs in dependencies:
            budget.charge()
            if lhs <= known:
                known.update(rhs)
        if before == known:
            return mask_of(known)


def closure_table(seed, budget=None):
    budget = Budget() if budget is None else budget
    return [closure(s, seed['fds'], budget) for s in range(1 << len(seed['attributes']))]


def candidate_keys(table):
    # Check all smaller superkeys, independently of JS's single-removal test.
    superkeys = [members(s) for s, c in enumerate(table) if c == len(table) - 1]
    return sorted(mask_of(s) for s in superkeys if not any(t < s for t in superkeys))


def replay(seed, start, steps, budget):
    known, applied = members(start), []
    for index, fd_index in enumerate(steps):
        budget.charge()
        fd = seed['fds'][fd_index]
        lhs, rhs = members(fd['lhs']), members(fd['rhs'])
        kind = 'unmet-lhs' if not lhs <= known else 'no-progress' if rhs <= known else None
        if kind:
            return {'reached': mask_of(known), 'steps': applied,
                    'error': {'kind': kind, 'step': index, 'missing': mask_of(lhs - known)}}
        added = rhs - known
        known.update(rhs)
        applied.append([fd_index, mask_of(added)])
    return {'reached': mask_of(known), 'steps': applied, 'error': None}


def analyze(seed, submission, budget=None):
    seed = source(seed)
    answer = answer_for(seed, submission)
    budget = Budget() if budget is None else budget
    task, mode = seed['task'], seed['task']['mode']
    if mode == 'keys':
        table = closure_table(seed, budget)
        checks = []
        for key in answer['keys']:
            removable = {i for i in members(key) if table[key ^ (1 << i)] == len(table) - 1}
            checks.append([key, table[key], mask_of(removable)])
        facts = {'candidate_keys': candidate_keys(table), 'checks': checks}
    elif mode == 'closure':
        facts = {'closure': closure(task['start'], seed['fds'], budget),
                 'trace': replay(seed, task['start'], answer['steps'], budget)}
    else:
        reached = closure(task['lhs'], seed['fds'], budget)
        if answer['implied']:
            proof = {'kind': 'derivation', **replay(seed, task['lhs'], answer['steps'], budget)}
        else:
            # Evaluate the actual pair of tuples, not the browser mask predicate.
            rows = [[0] * len(seed['attributes']),
                    [0 if i in members(answer['agree']) else 1 for i in range(len(seed['attributes']))]]

            def holds(lhs, rhs):
                budget.charge()
                agrees = lambda columns: all(rows[0][i] == rows[1][i] for i in members(columns))
                return not agrees(lhs) or agrees(rhs)

            proof = {'kind': 'pair', 'agree': answer['agree'],
                     'violated_fds': [i for i, fd in enumerate(seed['fds']) if not holds(fd['lhs'], fd['rhs'])],
                     'violates_target': not holds(task['lhs'], task['rhs'])}
        facts = {'closure': reached, 'implied': members(task['rhs']) <= members(reached), 'proof': proof}
    data = {'format': 1, 'exercise': digest(['fd-exercise-v1', seed]),
            'answer': digest(['fd-answer-v1', answer]), 'mode': mode, 'facts': facts}
    VALIDATORS['analysis-result'].validate(data)
    if len(canonical(data)) > 8192:
        raise ResourceLimit('data-bytes')
    return data


def compile_lesson(value):
    """Validate a named lesson and its worked answer; return only seed and answer.

    This does not prepare TeX fragments, register a content type or expose a UI.
    """
    lesson = validated('lesson', value)
    if len(json.dumps(lesson, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > 32768:
        raise ResourceLimit('lesson-bytes')
    ex = lesson['exercise']
    attributes = [a['id'] for a in ex['attributes']]
    fd_ids = [fd['id'] for fd in ex['fds']]
    require(len(set(attributes)) == len(attributes), 'duplicate-attribute')
    require(len(set(fd_ids)) == len(fd_ids), 'duplicate-fd-id')

    def mask(names):
        require(set(names) <= set(attributes), 'unknown-attribute')
        return sum(1 << attributes.index(name) for name in names)

    task = dict(ex['task'])
    for field in ('start', 'lhs', 'rhs'):
        if field in task:
            task[field] = mask(task[field])
    seed = source({'format': 1, 'id': ex['id'], 'attributes': attributes,
                   'fds': [{'id': fd['id'], 'lhs': mask(fd['lhs']), 'rhs': mask(fd['rhs'])} for fd in ex['fds']],
                   'task': task})
    named = lesson['worked_answer']
    answer = {'format': 1, 'mode': named['mode']}
    for field in ('closure', 'agree'):
        if field in named:
            answer[field] = mask(named[field])
    if 'keys' in named:
        answer['keys'] = [mask(key) for key in named['keys']]
    if 'steps' in named:
        require(set(named['steps']) <= set(fd_ids), 'unknown-fd')
        answer['steps'] = [fd_ids.index(name) for name in named['steps']]
    if 'implied' in named:
        answer['implied'] = named['implied']
    answer = answer_for(seed, answer)
    facts = analyze(seed, answer)['facts']
    if task['mode'] == 'keys':
        ok = all(key in facts['candidate_keys'] for key in answer['keys'])
        ok = ok and (task['require'] == 'one' or answer['keys'] == facts['candidate_keys'])
    elif task['mode'] == 'closure':
        ok = facts['trace']['error'] is None and facts['trace']['reached'] == facts['closure'] == answer['closure']
    elif answer['implied']:
        ok = facts['proof']['error'] is None and members(task['rhs']) <= members(facts['proof']['reached'])
    else:
        ok = not facts['proof']['violated_fds'] and facts['proof']['violates_target']
    require(ok, 'invalid-worked-answer')
    return seed, answer

# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Check trusted FD design fixtures, not an installed plugin or production parser.

Requires jsonschema from the compatible host development lock. Uses only local
synthetic fixtures. No provider, course, database or network access is needed.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/design/functional-dependencies'


def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('ascii')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sub(left, right):
    return left & right == left


def forward(start, fds):
    known, tests = start, 0
    while True:
        before = known
        for left, right in fds:
            tests += 1
            if sub(left, known):
                known |= right
        if known == before:
            return known, tests


def closed_sets(n, fds):
    # Independent model: enumerate every model of the attribute-set implications.
    return [s for s in range(1 << n) if all(not sub(l, s) or sub(r, s) for l, r in fds)]


def intersection_closure(start, n, closed):
    result = (1 << n) - 1
    for s in closed:
        if sub(start, s):
            result &= s
    return result


def keys_by_all_subsets(table, universe):
    superkeys = [s for s, closure in enumerate(table) if closure == universe]
    return [s for s in superkeys if not any(t != s and sub(t, s) for t in superkeys)]


def keys_by_single_removal(table, n):
    universe = (1 << n) - 1
    return [s for s, c in enumerate(table) if c == universe and all(
        table[s ^ (1 << i)] != universe for i in range(n) if s & (1 << i))]


def rows_for(agree, n):
    return [[0] * n, [0 if agree & (1 << i) else 1 for i in range(n)]]


def rows_satisfy(rows, lhs, rhs, n):
    # Compare actual cells, independently of the agreement-mask implication test.
    same_left = all(rows[0][i] == rows[1][i] for i in range(n) if lhs & (1 << i))
    same_right = all(rows[0][i] == rows[1][i] for i in range(n) if rhs & (1 << i))
    return not same_left or same_right


def compile_lesson(lesson):
    Draft202012Validator(read('lesson-v1.schema.json')).validate(lesson)
    ex = lesson['exercise']
    attrs = [a['id'] for a in ex['attributes']]
    ids = [f['id'] for f in ex['fds']]
    require(len(attrs) == len(set(attrs)), 'duplicate attribute ID')
    require(len(ids) == len(set(ids)), 'duplicate FD ID')

    def mask(names):
        require(len(names) == len(set(names)), 'duplicate attribute')
        require(set(names) <= set(attrs), 'unknown attribute')
        return sum(1 << attrs.index(a) for a in names)

    def steps(names):
        require(set(names) <= set(ids), 'unknown FD')
        return [ids.index(name) for name in names]

    fds = [(mask(fd['lhs']), mask(fd['rhs'])) for fd in ex['fds']]
    task = copy.deepcopy(ex['task'])
    for field in ('start', 'lhs', 'rhs'):
        if field in task:
            task[field] = mask(task[field])
    named = lesson['worked_answer']
    require(named['mode'] == task['mode'], 'worked answer mode mismatch')
    answer = {'format': 1, 'mode': named['mode']}
    for field in ('closure', 'agree'):
        if field in named:
            answer[field] = mask(named[field])
    if 'keys' in named:
        answer['keys'] = sorted(mask(key) for key in named['keys'])
    if 'steps' in named:
        answer['steps'] = steps(named['steps'])
    if 'implied' in named:
        answer['implied'] = named['implied']
    return attrs, fds, task, answer, mask


def check_answer(answer, n, fds, task, table):
    Draft202012Validator(read('answer-v1.schema.json')).validate(answer)
    require(answer['mode'] == task['mode'], 'wrong task mode')
    require(len(canonical(answer)) <= 1800, 'answer byte budget')
    universe = (1 << n) - 1
    values = answer.get('keys', []) + [answer[k] for k in ('closure', 'agree') if k in answer]
    require(all(type(s) is int and 0 <= s <= universe for s in values), 'invalid mask')
    require(all(type(i) is int and 0 <= i < len(fds) for i in answer.get('steps', [])), 'invalid FD index')

    def replay(start):
        known = start
        for index in answer['steps']:
            lhs, rhs = fds[index]
            if not sub(lhs, known):
                return known, 'unmet-lhs'
            if sub(rhs, known):
                return known, 'no-progress'
            known |= rhs
        return known, None

    if task['mode'] == 'keys':
        submitted = sorted(answer['keys'])
        if task['require'] == 'one':
            require(len(submitted) == 1, 'one-key answer requires one key')
        expected = keys_by_all_subsets(table, universe)
        if any(table[s] != universe for s in submitted):
            return False, 'not-superkey'
        if any(s not in expected for s in submitted):
            return False, 'nonminimal'
        if task['require'] == 'all' and submitted != expected:
            return False, 'missing-key'
        return True, 'complete' if task['require'] == 'all' else 'candidate-key'
    if task['mode'] == 'closure':
        reached, error = replay(task['start'])
        if error:
            return False, error
        expected = table[task['start']]
        if answer['closure'] & ~expected:
            return False, 'overclaimed'
        ok = answer['closure'] == reached == expected
        return ok, 'complete' if ok else 'incomplete'
    if answer['implied']:
        reached, error = replay(task['lhs'])
        if error:
            return False, error
        ok = sub(task['rhs'], reached)
        return ok, 'derivation' if ok else 'incomplete'
    rows = rows_for(answer['agree'], n)
    if not all(rows_satisfy(rows, l, r, n) for l, r in fds):
        return False, 'violated-premise'
    if rows_satisfy(rows, task['lhs'], task['rhs'], n):
        return False, 'target-holds'
    return True, 'counterexample'


def verify_theory(n, fds):
    closed = closed_sets(n, fds)
    table = []
    for start in range(1 << n):
        got, tests = forward(start, fds)
        require(got == intersection_closure(start, n, closed), 'closure/model disagreement')
        require(tests <= (n + 1) * len(fds), 'closure operation bound')
        table.append(got)
        rows = rows_for(got, n)
        require(all(rows_satisfy(rows, l, r, n) for l, r in fds), 'illegal constructed witness')
        for i in range(n):
            if not got & (1 << i):
                require(not rows_satisfy(rows, start, 1 << i, n), 'witness fails to refute target')
    require(keys_by_single_removal(table, n) == keys_by_all_subsets(table, (1 << n) - 1),
            'key minimality models disagree')
    return table


def verify():
    lessons, parsed = read('examples.json')['examples'], {}
    for item in lessons:
        lesson = item['lesson']
        attrs, fds, task, worked, mask = compile_lesson(lesson)
        table = verify_theory(len(attrs), fds)
        expected = item['expected']
        require(sorted(mask(key) for key in expected['keys']) == keys_by_all_subsets(table, (1 << len(attrs)) - 1),
                'hand-derived keys differ')
        if 'closure' in expected:
            require(mask(expected['closure']) == table[task['start']], 'hand-derived closure differs')
        if 'implied' in expected:
            require(expected['implied'] == sub(task['rhs'], table[task['lhs']]), 'hand-derived implication differs')
        require(check_answer(worked, len(attrs), fds, task, table)[0], 'invalid worked answer')
        parsed[lesson['exercise']['id']] = (len(attrs), fds, task, table)

    cases = read('expected-cases.json')['cases']
    for case in cases:
        result = check_answer(case['answer'], *parsed[case['example']])
        require(result == (case['accepted'], case['reason']), 'case differs: ' + case['id'])

    # 12 possible nontrivial singleton FDs over three attributes, including
    # empty determinants. All 4096 combinations, not just acyclic examples.
    atoms = [(lhs, 1 << i) for i in range(3) for lhs in range(8) if not lhs & (1 << i)]
    for theory in range(1 << len(atoms)):
        verify_theory(3, [fd for i, fd in enumerate(atoms) if theory & (1 << i)])

    # Composite RHS and determinant; alternative productive order; trivial proof.
    workshop = parsed['workshop_closure']
    n, fds, _, table = workshop
    for steps in ([0, 2, 3], [2, 3, 0]):
        require(check_answer({'format': 1, 'mode': 'closure', 'closure': 63, 'steps': steps},
                             n, fds, {'mode': 'closure', 'start': 5}, table)[0], 'alternative trace rejected')
    require(check_answer({'format': 1, 'mode': 'implication', 'implied': True, 'steps': []},
                         n, fds, {'mode': 'implication', 'lhs': 5, 'rhs': 1}, table)[0], 'trivial proof rejected')
    require(check_answer({'format': 1, 'mode': 'implication', 'implied': True, 'steps': [2]},
                         n, fds, {'mode': 'implication', 'lhs': 4, 'rhs': 8}, table)[0], 'target prefix rejected')
    max_table = verify_theory(8, [(1 << i, 1 << (i ^ 1)) for i in range(8)])
    require(len(keys_by_all_subsets(max_table, 255)) == 16, 'eight-attribute key example')

    invalid = []
    for change in ('unknown-attribute', 'duplicate-attribute', 'duplicate-fd', 'bad-worked-proof'):
        lesson = copy.deepcopy(lessons[0]['lesson'])
        if change == 'unknown-attribute':
            lesson['exercise']['fds'][0]['lhs'] = ['unknown']
        elif change == 'duplicate-attribute':
            lesson['exercise']['attributes'][1]['id'] = 'person'
        elif change == 'duplicate-fd':
            lesson['exercise']['fds'][1]['id'] = 'f1'
        else:
            lesson['worked_answer']['steps'] = ['f4', 'f3']
        try:
            a, f, t, w, _ = compile_lesson(lesson)
            require(check_answer(w, len(a), f, t, verify_theory(len(a), f))[0], 'bad worked answer')
        except ValueError:
            invalid.append(change)
        else:
            raise ValueError('accepted invalid source: ' + change)
    for value in (True, 1.0, 64, -1):
        try:
            check_answer({'format': 1, 'mode': 'closure', 'closure': value, 'steps': []}, *workshop)
        except (ValueError, ValidationError):
            invalid.append('invalid-mask:' + repr(value))
        else:
            raise ValueError('accepted invalid mask')

    maximal_answer = {'format': 1, 'mode': 'keys', 'keys': list(range(256))}
    # Deliberately conservative structural envelope; all subsets cannot be keys.
    facts = {'format': 1, 'exercise': 'f' * 64, 'answer': 'f' * 64, 'mode': 'keys',
             'facts': {'candidate_keys': list(range(256)),
                       'checks': [[s, 255, 255] for s in range(256)]}}
    outcome = {'status': 'ok', 'key': 'f' * 16, 'namespace': 'f' * 64,
               'summary': {'kind': 'text', 'text': 'Dependency analysis completed.'}, 'data': facts}
    sizes = {'answer': len(canonical(maximal_answer)), 'data': len(canonical(facts)),
             'outcome': len(canonical(outcome))}
    require(sizes['answer'] <= 1800 and sizes['data'] <= 8192 and sizes['outcome'] <= 12288,
            'structural envelope exceeds budget')
    inputs = [p for p in sorted(DATA.glob('*.json')) if p.name != 'validation.json']
    inputs.append(Path(__file__).resolve())
    return {
        'status': 'design-checks-passed', 'python': platform.python_version(),
        'examples': len(lessons), 'answer_cases': len(cases), 'invalid_cases': len(invalid),
        'exhaustive': {'attributes': 3, 'possible_singleton_nontrivial_fds': len(atoms),
                       'theories': 1 << len(atoms), 'closures': 8 * (1 << len(atoms))},
        'additional_checks': ['alternative proof orders', 'trivial implication',
                              'target-prefix proof', 'eight attributes with 16 keys'],
        'conservative_envelope_ascii_bytes': sizes,
        'input_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'exclusions': ['production parser', 'JavaScript engine', 'installed wheel',
                       'result/view schemas and host outcome validation', 'TeX builds',
                       'browser/security conformance', 'state and race tests',
                       'physical phones and classroom performance'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true', help='write design validation.json')
    args = parser.parse_args()
    report = verify()
    text = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    if args.write_report:
        (DATA / 'validation.json').write_text(text, encoding='utf-8', newline='\n')
    print(text, end='')

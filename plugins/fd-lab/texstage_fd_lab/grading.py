# SPDX-License-Identifier: Apache-2.0
"""Verify bound engine facts using prepared tables and small proof certificates."""
from . import model


def expected_facts(public, private, answer):
    seed, mode = public['seed'], public['mode']
    if mode == 'keys':
        table = private['table']
        checks = []
        for key in answer['keys']:
            removable = sum(1 << i for i in range(len(seed['attributes']))
                            if key & (1 << i) and table[key ^ (1 << i)] == len(table) - 1)
            checks.append([key, table[key], removable])
        return {'candidate_keys': private['candidate_keys'], 'checks': checks}
    start = seed['task']['start' if mode == 'closure' else 'lhs']
    if mode == 'closure' or answer['implied']:
        trace = model.replay(seed, start, answer['steps'], model.Budget())
        if mode == 'closure':
            return {'closure': private['closure'], 'trace': trace}
        proof = {'kind': 'derivation', **trace}
    else:
        # Reconstruct the two tuples and inspect column equality; no engine search.
        row1 = [0] * len(seed['attributes'])
        row2 = [0 if answer['agree'] & (1 << i) else 1 for i in range(len(row1))]
        def violates(lhs, rhs):
            same = lambda mask: all(a == b for i, (a, b) in enumerate(zip(row1, row2)) if mask & (1 << i))
            return same(lhs) and not same(rhs)
        proof = {'kind': 'pair', 'agree': answer['agree'],
                 'violated_fds': [i for i, fd in enumerate(seed['fds']) if violates(fd['lhs'], fd['rhs'])],
                 'violates_target': violates(seed['task']['lhs'], seed['task']['rhs'])}
    return {'closure': private['closure'], 'implied': private['implied'], 'proof': proof}


def feedback(public, private, slot, outcome):
    if outcome.get('status') != 'ok':
        return {'code': 'unavailable', 'detail': outcome.get('status', 'error')}
    seed, answer, mode = public['seed'], slot['answer'], public['mode']
    facts = expected_facts(public, private, answer)
    expected = {'format': 1, 'exercise': private['exercise'], 'answer': slot['digest'], 'mode': mode, 'facts': facts}
    if model.canonical(outcome.get('data')) != model.canonical(expected):
        return {'code': 'unavailable', 'detail': 'facts'}
    if mode == 'keys':
        invalid = [row for row in facts['checks'] if row[0] not in private['candidate_keys']]
        missing = len(set(private['candidate_keys']) - set(answer['keys'])) if seed['task']['require'] == 'all' else 0
        first = invalid[0] if invalid else [0, 0, 0]
        correct = not invalid and not missing
        reason = ('not-superkey' if first[1] != (1 << len(seed['attributes'])) - 1 else 'not-minimal') if invalid else (
            'missing-keys' if missing else 'checked')
        return {'code': 'checked' if correct else 'mismatch', 'correct': correct, 'reason': reason,
                'missing_keys': missing, 'invalid_keys': len(invalid), 'key': first[0],
                'key_closure': first[1], 'removable': first[2]}
    if mode == 'implication' and not answer['implied']:
        proof = facts['proof']
        correct = not facts['implied'] and not proof['violated_fds'] and proof['violates_target']
        return {'code': 'checked' if correct else 'mismatch', 'correct': correct,
                'reason': 'premise-violated' if proof['violated_fds'] else 'target-not-violated' if not proof['violates_target'] else 'checked',
                'fd': proof['violated_fds'][0] if proof['violated_fds'] else -1}
    trace = facts['trace' if mode == 'closure' else 'proof']
    actual, reached = private['closure'], trace['reached']
    if mode == 'closure':
        claimed = answer['closure']
        correct = trace['error'] is None and actual == claimed == reached
        reason = (trace['error']['kind'] if trace['error'] else 'overclaimed' if claimed & ~actual else
                  'incomplete' if reached != actual else 'final-set' if claimed != actual else 'checked')
        missing, extra = actual & ~reached, claimed & ~actual
    else:
        missing, extra = seed['task']['rhs'] & ~reached, 0
        correct = trace['error'] is None and not missing and facts['implied']
        reason = trace['error']['kind'] if trace['error'] else 'target-missing' if missing else 'checked'
    next_fd = next((i for i, fd in enumerate(seed['fds'])
                    if fd['lhs'] & reached == fd['lhs'] and fd['rhs'] & ~reached), -1)
    return {'code': 'checked' if correct else 'mismatch', 'correct': correct, 'reason': reason,
            'missing': missing, 'extra': extra, 'step': trace['error']['step'] if trace['error'] else -1,
            'needed': trace['error']['missing'] if trace['error'] else 0, 'next_fd': next_fd}

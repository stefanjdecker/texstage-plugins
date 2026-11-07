# SPDX-License-Identifier: Apache-2.0
"""Formative feedback; correctness is separate from canonical equality."""
from . import model


def prediction(answer, facts):
    matched = sorted(k for k, v in answer['values'].items() if facts['final'][k] == v)
    wrong = sorted(set(facts['final']) - set(matched))
    return {'code': 'revise' if wrong else 'correct', 'correct': not wrong, 'matched': matched, 'wrong': wrong}


def diagnosis(answer, facts):
    actual = {(e['from'], e['to']): e['witnesses'] for e in facts['edges']}
    proposed = {(e['from'], e['to']): e['witness'] for e in answer['edges']}
    missing = sorted(actual.keys() - proposed.keys())
    extra = sorted(proposed.keys() - actual.keys())
    bad = sorted(key for key in actual.keys() & proposed.keys() if proposed[key] not in actual[key])
    cert = answer['certificate']
    verified = (cert['kind'] == ('serial' if facts['acyclic'] else 'cycle')
                and model.certificate_ok(facts['vertices'], facts['edges'], cert['kind'], cert['vertices']))
    correct = not (missing or extra or bad) and verified
    return {'code': 'correct' if correct else 'revise', 'correct': correct,
            'missing': [list(x) for x in missing], 'extra': [list(x) for x in extra],
            'witnesses': [list(x) for x in bad], 'certificate': verified}


def repair(exercise, answer, outcome):
    if outcome.get('status') != 'ok':
        return {'code': 'unavailable', 'reason': 'evaluation'}
    facts = outcome.get('data')
    if not model.verify_analysis(exercise, answer['order'], facts):
        return {'code': 'unavailable', 'reason': 'facts'}
    return {'code': 'correct' if facts['acyclic'] else 'revise', 'correct': facts['acyclic'],
            'valid': True, 'acyclic': facts['acyclic'], 'final': facts['final'],
            'certificate': {'kind': 'serial' if facts['acyclic'] else 'cycle',
                            'vertices': facts['serial_order'] if facts['acyclic'] else facts['cycle']}}

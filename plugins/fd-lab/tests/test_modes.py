# SPDX-License-Identifier: Apache-2.0
"""Prepared keys and implication modes, using installed provider and real runtime."""
import copy

import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog
from texstage.plugins.runtime import Runtime
from texstage_fd_lab import model
from texstage_fd_lab.authoring import prepare_lesson, TYPE, ENGINE
from texstage_fd_lab.grading import expected_facts
from texstage_fd_lab.state import Lesson, SLOT_BYTES, STATE_BYTES
from test_lesson import provider, source, prepared, opened, submit, complete, view, advance, command, envelope, transition, shared_state
from test_engine import probe


@pytest.mark.parametrize('mode', ['keys_one', 'keys_all', 'implied', 'refuted', 'different_sizes', 'empty_key'])
def test_prepared_modes_are_private_and_independently_checked(provider, mode):
    spec = prepared(mode)
    ctx = {'item': spec['prepared'], 'epoch': 1, 'role': 'participant'}
    public, private = ctx['item']['public'], ctx['item']['private']
    assert not {'table', 'candidate_keys', 'worked', 'closure', 'implied'} & set(public)
    assert 'One worked answer' not in spec['fragments']['exercise']
    assert 'One worked answer' in spec['fragments']['solutions']
    assert 'Eine mögliche Lösung' in prepare_lesson(source(mode), {'language': 'de'}).fragments['solutions']
    answer = private['worked']['answer']
    assert expected_facts(public, private, answer) == model.analyze(public['seed'], answer)['facts']
    bad = source(mode)
    bad['worked_answer'] = {'mode': 'keys', 'keys': []} if public['mode'] == 'keys' else {'mode': 'implication', 'implied': not answer['implied'], **({'agree': []} if answer['implied'] else {'steps': []})}
    with pytest.raises(ValueError): prepare_lesson(bad, {})
    if public['mode'] == 'keys':
        assert len(private['table']) == 1 << len(public['seed']['attributes'])
    else:
        assert type(private['implied']) is bool


@pytest.mark.parametrize('mode,answer,reason,correct', [
    ('keys_one', {'format': 1, 'mode': 'keys', 'keys': [6]}, 'checked', True),
    ('keys_one', {'format': 1, 'mode': 'keys', 'keys': [1]}, 'not-superkey', False),
    ('keys_one', {'format': 1, 'mode': 'keys', 'keys': [7]}, 'not-minimal', False),
    ('keys_all', {'format': 1, 'mode': 'keys', 'keys': [5]}, 'missing-keys', False),
    ('keys_all', {'format': 1, 'mode': 'keys', 'keys': []}, 'missing-keys', False),
    ('keys_all', {'format': 1, 'mode': 'keys', 'keys': [6, 5]}, 'checked', True),
    ('different_sizes', {'format': 1, 'mode': 'keys', 'keys': [1, 6]}, 'checked', True),
    ('different_sizes', {'format': 1, 'mode': 'keys', 'keys': [1]}, 'missing-keys', False),
    ('empty_key', {'format': 1, 'mode': 'keys', 'keys': [0]}, 'checked', True),
    ('empty_key', {'format': 1, 'mode': 'keys', 'keys': []}, 'missing-keys', False),
    ('empty_key', {'format': 1, 'mode': 'keys', 'keys': [1]}, 'not-minimal', False),
    ('implied', {'format': 1, 'mode': 'implication', 'implied': True, 'steps': [2, 3]}, 'checked', True),
    ('implied', {'format': 1, 'mode': 'implication', 'implied': True, 'steps': [2]}, 'target-missing', False),
    ('implied', {'format': 1, 'mode': 'implication', 'implied': True, 'steps': [3]}, 'unmet-lhs', False),
    ('refuted', {'format': 1, 'mode': 'implication', 'implied': False, 'agree': 8}, 'checked', True),
    ('refuted', {'format': 1, 'mode': 'implication', 'implied': False, 'agree': 40}, 'checked', True),
    ('refuted', {'format': 1, 'mode': 'implication', 'implied': False, 'agree': 24}, 'premise-violated', False),
    ('refuted', {'format': 1, 'mode': 'implication', 'implied': False, 'agree': 0}, 'target-not-violated', False),
    ('refuted', {'format': 1, 'mode': 'implication', 'implied': True, 'steps': []}, 'target-missing', False),
])
def test_distinct_mathematical_feedback_and_alternatives(provider, mode, answer, reason, correct):
    state, ctx = opened(mode)
    state, _ = submit(state, ctx, answer=answer)
    state = complete(state, ctx)
    feedback = state['answers']['alice']['feedback']
    assert feedback['correct'] is correct and feedback['reason'] == reason
    assert 'worked' not in view(state, ctx, 'participant')
    assert 'table' not in model.canonical(view(state, ctx, 'projector'))
    if reason == 'not-minimal': assert feedback['removable']
    if reason == 'premise-violated': assert feedback['fd'] == 3


@pytest.mark.parametrize('mode', ['keys_one', 'keys_all', 'implied', 'refuted', 'empty_key'])
def test_corrupt_or_misbound_facts_never_grade(provider, mode):
    state, ctx = opened(mode)
    state, _ = submit(state, ctx)
    answer = ctx['item']['private']['worked']['answer']
    data = model.analyze(ctx['item']['public']['seed'], answer)
    mutations = []
    for field in ('answer', 'exercise', 'mode', 'format'):
        changed = copy.deepcopy(data); changed[field] = True; mutations.append(changed)
    for field in data['facts']:
        changed = copy.deepcopy(data); changed['facts'][field] = None; mutations.append(changed)
    if answer['mode'] == 'keys':
        changed = copy.deepcopy(data); changed['facts']['checks'][0][1] ^= 1; mutations.append(changed)
        changed = copy.deepcopy(data); changed['facts']['checks'].append(changed['facts']['checks'][0]); mutations.append(changed)
    else:
        changed = copy.deepcopy(data); changed['facts']['proof']['extra'] = 1; mutations.append(changed)
    for bad in mutations:
        result = complete(state, ctx, {'status': 'ok', 'data': bad})
        assert result['answers']['alice']['status'] == 'unavailable'
        assert 'correct' not in result['answers']['alice']['feedback']


def test_positive_implication_needs_target_not_complete_closure(provider):
    value = source('implied')
    value['exercise']['task']['rhs'] = ['tutor']
    value['worked_answer']['steps'] = ['f3']
    spec = json_value(prepare_lesson(value, {}))['prepared']
    ctx = {'item': spec, 'epoch': 1, 'role': 'participant'}
    state = Lesson().initial_state(spec, ctx)
    state, _ = advance(state, {'kind': 'activate'}, ctx)
    state, _ = advance(state, command('open', {'control': 0}), ctx | {'role': 'presenter'})
    state, _ = submit(state, ctx)
    state = complete(state, ctx)
    assert state['answers']['alice']['feedback']['correct']
    value['exercise']['task']['rhs'] = ['workshop']
    value['worked_answer']['steps'] = []
    assert prepare_lesson(value, {}).prepared.private['implied']


@pytest.mark.parametrize('mode', ['keys_all', 'implied', 'refuted'])
def test_real_runtime_mode_contracts_and_revealed_sharing(tmp_path, provider, mode):
    r = Runtime(tmp_path / 'state.sqlite3', Catalog([provider]))
    try:
        spec = prepared(mode)['prepared']; spec['public']['feedback'] = 'after-reveal'
        spec['evaluations']['analysis']['engine'] = ENGINE
        r.ensure('lesson', TYPE, 'closure', spec); r.activate('lesson', {(TYPE, 'closure')})
        assert r.command('lesson', 'teacher', 'presenter', envelope('open', {'control': 0}))['accepted']
        answer = spec['private']['worked']['answer']
        assert r.command('lesson', 'alice', 'participant', envelope('submit', {'phase': 1, 'version': 0, 'answer': answer}))['accepted']
        job = r.lease('lesson', 'presenter', now=100)[0]
        outcome = probe.run([{'seed': job['binding']['seed'], 'binding': job['binding'], 'text': job['text']}])[0]['outcome']
        assert r.finish('lesson', 'presenter', {k: job[k] for k in ('id', 'epoch', 'generation')} | {'outcome': outcome}, now=101)
        r.drain('lesson')
        before = r.view('lesson', TYPE, 'closure', role='participant', surface='participant-input', actor='alice')['data']
        assert 'feedback' not in before['own'] and 'worked' not in before
        assert r.command('lesson', 'teacher', 'presenter', envelope('reveal', {'control': 1}, 'reveal000001'))['accepted']
        assert r.command('lesson', 'teacher', 'presenter', envelope('select-demonstration', {'control': 2, 'actor': 'alice'}, 'share0000001'))['accepted']
        for role, surface in (('participant', 'participant-input'), ('presenter', 'presenter-controls'), ('presenter', 'presenter-overlay'), ('projector', 'projector-overlay')):
            data = r.view('lesson', TYPE, 'closure', role=role, surface=surface, actor='alice')['data']
            assert data['worked']['answer'] == answer
            if role == 'participant': assert data['own']['feedback']['correct']
            if role == 'projector':
                assert data['demonstration'] == answer
                assert 'alice' not in model.canonical(data)
        receipt = r.command('lesson', 'teacher', 'presenter', envelope('demonstrate', {'control': 3, 'step': 1}, 'demo00000001'))
        if mode == 'implied':
            assert receipt['accepted']
            data = r.view('lesson', TYPE, 'closure', role='projector', surface='projector-overlay')['data']
            assert data['known'] == 28 and data['demonstration']['steps'] == [2]
        else: assert receipt['error'] == 'no-derivation'
    finally: r.close()


def test_largest_key_submissions_fit_completed_slots(provider):
    value = source('keys_all')
    ex = value['exercise']; ex['attributes'] = [{'id': chr(97+i), 'label': {'en': chr(97+i), 'de': chr(97+i)}} for i in range(8)]
    ex['fds'] = []; value['worked_answer'] = {'mode': 'keys', 'keys': [[a['id'] for a in ex['attributes']]]}
    spec = json_value(prepare_lesson(value, {}))['prepared']
    assert len(model.canonical(spec['private'])) < 16 * 1024
    ctx = {'item': spec, 'epoch': 1, 'role': 'participant'}
    state = Lesson().initial_state(spec, ctx)
    state, _ = advance(state, {'kind': 'activate'}, ctx)
    state, _ = advance(state, command('open', {'control': 0}), ctx | {'role': 'presenter'})
    answer = {'format': 1, 'mode': 'keys', 'keys': list(range(256))}
    facts = model.analyze(spec['public']['seed'], answer)
    for i in range(600):
        actor = str(i).zfill(3) + 'x' * 253
        state, effects = submit(state, ctx, actor=actor, answer=answer)
        state, _ = advance(state, {'kind': 'evaluation.finished', 'actor': actor, 'binding': 'analysis',
            'correlation_id': next(e['correlation_id'] for e in effects if e['kind'] == 'evaluate'), 'outcome': {'status': 'ok', 'data': facts}}, ctx)
        assert state['answers'][actor]['status'] == 'saved'
        assert len(model.canonical({actor: state['answers'][actor]})) < SLOT_BYTES
    assert len(model.canonical(shared_state(state))) < STATE_BYTES
    state, effects = submit(state, ctx, actor=actor, version=1, answer=answer, request='replace00001')
    assert len(model.canonical({'state': shared_state(state), 'effects': effects})) < 256 * 1024
    for role in ('participant', 'projector', 'presenter'):
        assert len(model.canonical(view(state, ctx, role, actor))) < 128 * 1024


def test_one_key_shape_and_mode_guards(provider):
    state, ctx = opened('keys_one')
    for answer in ({'format': 1, 'mode': 'keys', 'keys': []}, {'format': 1, 'mode': 'keys', 'keys': [5, 6]},
                   {'format': 1, 'mode': 'implication', 'implied': False, 'agree': 8}):
        result = transition(state, command('submit', {'phase': 1, 'version': 0, 'answer': answer}), ctx)
        assert result == {'refusal': 'invalid-answer'}

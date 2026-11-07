# SPDX-License-Identifier: Apache-2.0
"""Deterministic phased lesson with authenticated per-actor storage."""
import copy
import json
from texstage.plugin_api.v1 import Evaluate, CancelEvaluation, SaveActor, evaluation_correlation, json_value
from . import model, feedback, storage

PHASES = ('ready', 'predict', 'inspect', 'diagnose', 'repair', 'reveal')
ANSWER_PHASE = {'predict': 'prediction', 'diagnose': 'diagnosis', 'repair': 'repair'}
SURFACES = {'participant': ('participant-input',), 'presenter': ('presenter-controls', 'presenter-overlay'), 'projector': ('projector-overlay',)}
STATE_BYTES, TRANSITION_BYTES, VIEW_BYTES = 32 * 1024, 64 * 1024, 64 * 1024


def finish(state, effects=()):
    result = {'state': state, 'effects': [json_value(e) for e in effects]}
    if storage.size(state) > STATE_BYTES or storage.size(result) > TRANSITION_BYTES:
        return {'refusal': 'state-capacity'}
    return result


def binding(ctx):
    return model.digest(ctx['item']['evaluations']['analysis'])


def contribution(slot):
    if not slot:
        return None
    return slot['feedback']['code'] if slot['status'] == 'saved' else slot['status']


def save(state, before, after, ctx, actor, effects, *, replacement):
    after['version'] += 1
    if after['version'] > storage.MAX_VERSION:
        raise model.InputError('reset-required')
    storage.check(after)
    for phase in storage.PHASES:
        for value, delta in ((before, -1), (after, 1)):
            key = contribution(value[phase])
            if key:
                state['counts'][phase][key] += delta
    state['count'] = ctx['records']['count'] + int(ctx['records']['value'] is None)
    effects.append(SaveActor(after, storage.summary(after)))
    for name in ('selected', 'shared'):
        snapshot = state[name]
        if snapshot and snapshot['actor'] == actor:
            if replacement:
                state[name] = None
            elif snapshot['version'] == before['version']:
                state[name] = {'actor': actor, 'version': after['version'], 'record': copy.deepcopy(after)}


class Lesson:
    def initial_state(self, item, ctx):
        return {'phase': 'ready', 'phase_token': 0, 'control_version': 0, 'active': False, 'paused': False,
                'cursor': 0, 'prediction_revealed': False, 'count': 0, 'records_page': 0,
                'counts': {p: dict.fromkeys(('correct', 'revise', 'pending', 'unavailable'), 0) for p in storage.PHASES},
                'selected': None, 'shared': None, 'binding': binding(ctx)}

    def transition(self, previous, event, ctx):
        state, effects = copy.deepcopy(previous), []
        try:
            kind = event['kind']
            if kind in ('activate', 'deactivate'):
                state['active'] = kind == 'activate'
                if kind == 'deactivate' and state['phase'] in ANSWER_PHASE:
                    state['paused'] = True
                    state['phase_token'] += 1
                    state['control_version'] += 1
            elif kind == 'command':
                op, payload = event['operation'], event['payload']
                if op.startswith('submit-') or op == 'retry-analysis':
                    self.submit(state, event, ctx, effects)
                else:
                    self.control(state, op, payload, ctx)
            elif kind == 'evaluation.finished':
                before = storage.record(ctx)
                slot = before['repair']
                if (slot and slot['status'] == 'pending' and before['epoch'] == ctx['epoch']
                        and slot['correlation'] == event['correlation_id'] and event['binding'] == 'analysis'):
                    after = copy.deepcopy(before)
                    outcome = (feedback.repair(ctx['item']['public']['exercise'], slot['answer'], event['outcome'])
                               if state['binding'] == binding(ctx) else {'code': 'unavailable', 'reason': 'binding'})
                    after['repair']['feedback'] = outcome
                    after['repair']['status'] = 'unavailable' if outcome['code'] == 'unavailable' else 'saved'
                    save(state, before, after, ctx, event['actor'], effects, replacement=False)
            if max(state['control_version'], state['phase_token']) > storage.MAX_VERSION:
                raise model.InputError('reset-required')
        except model.InputError as error:
            return {'refusal': str(error)}
        return finish(state, effects)

    def submit(self, state, event, ctx, effects):
        op, payload, actor = event['operation'], event['payload'], event['actor']
        model.require(ctx['role'] == 'participant' and ctx['records']['actor'] == actor, 'role')
        model.require(state['active'], 'inactive')
        before = storage.record(ctx)
        model.require(before['epoch'] == ctx['epoch'], 'stale-epoch')
        phase = 'repair' if op == 'retry-analysis' else op.removeprefix('submit-')
        model.require(phase in storage.PHASES, 'operation')
        old = before[phase]
        version = old['version'] if old else 0
        model.require(payload['answer_version'] == version, 'stale-answer')
        model.require(payload['phase_token'] == state['phase_token'], 'stale-phase')
        model.require(version < storage.MAX_VERSION, 'reset-required')
        if op == 'retry-analysis':
            model.require(old is not None and old['status'] == 'unavailable', 'retry-unavailable')
            value = copy.deepcopy(old['answer'])
        else:
            model.require(not state['paused'] and ANSWER_PHASE.get(state['phase']) == phase, 'closed')
            value = model.answer(ctx['item']['public']['exercise'], phase, payload['answer'])
        model.require(ctx['records']['value'] is not None or ctx['records']['count'] < storage.MAX_ACTORS, 'actor-capacity')
        after = copy.deepcopy(before)
        slot = {'version': version if op == 'retry-analysis' else version + 1, 'answer': value, 'status': 'saved'}
        if phase == 'repair':
            if old and old['status'] == 'pending':
                effects.append(CancelEvaluation(old['correlation']))
            slot['status'] = 'pending'
            slot['correlation'] = evaluation_correlation(actor, event['request_id'], 'repair')
            effects.append(Evaluate('analysis', slot['correlation'], model.canonical(value)))
        else:
            slot['feedback'] = getattr(feedback, phase)(value, ctx['item']['private']['original'])
        after[phase] = slot
        save(state, before, after, ctx, actor, effects, replacement=op != 'retry-analysis')

    def control(self, state, op, payload, ctx):
        model.require(ctx['role'] == 'presenter', 'role')
        model.require(payload['control_version'] == state['control_version'], 'stale-control')
        model.require(state['active'], 'inactive')
        if op == 'advance-phase':
            model.require(state['phase'] != 'reveal', 'reset-required')
            state['phase'] = PHASES[PHASES.index(state['phase']) + 1]
            state['phase_token'] += 1
            state['paused'] = False
            if state['phase'] == 'diagnose':
                state['prediction_revealed'] = True
        elif op == 'seek-step':
            model.require(state['phase'] == 'inspect', 'phase')
            model.require(0 <= payload['cursor'] <= len(ctx['item']['public']['exercise']['schedule']), 'cursor')
            state['cursor'] = payload['cursor']
            state['prediction_revealed'] |= state['cursor'] == len(ctx['item']['public']['exercise']['schedule'])
        elif op == 'resume-phase':
            model.require(state['phase'] in ANSWER_PHASE and state['paused'], 'phase')
            state['paused'] = False
            state['phase_token'] += 1
        elif op == 'roster-page':
            model.require(0 <= payload['page'] < max(1, (state['count'] + 24) // 25), 'page')
            state['records_page'] = payload['page']
        elif op in ('select-answer', 'share-answer'):
            if op == 'share-answer':
                model.require(state['phase'] == 'reveal', 'unrevealed')
            if op == 'select-answer' and payload['actor'] == '' and payload['record_version'] == 0:
                state['selected'] = None
            else:
                record = ctx['records']['value']
                model.require(record is not None and ctx['records']['actor'] == payload['actor'], 'missing-answer')
                model.require(record['version'] == payload['record_version'], 'stale-answer')
                state['selected' if op == 'select-answer' else 'shared'] = {
                    'actor': payload['actor'], 'version': record['version'], 'record': copy.deepcopy(record)}
        elif op == 'clear-share':
            state['shared'] = None
        else:
            raise model.InputError('operation')
        state['control_version'] += 1

    def view(self, state, audience, ctx):
        role, surface = audience['role'], audience['surface']
        model.require(surface in SURFACES.get(role, ()), 'surface-role')
        revealed = state['phase'] == 'reveal'
        result = {'format': 1, **{k: state[k] for k in ('phase', 'phase_token', 'active', 'paused', 'cursor', 'prediction_revealed')}}
        original = ctx['item']['private']['original']
        if role == 'participant':
            own = ctx['records']['value']
            if own:
                result['own'] = storage.projected(own, prediction_revealed=state['prediction_revealed'], revealed=revealed)
        else:
            result['count'] = state['count']
            result['counts'] = {p: {'submitted': sum(c.values()), 'pending': c['pending'], 'unavailable': c['unavailable']}
                                for p, c in state['counts'].items()}
            if role == 'presenter' or revealed:
                result['outcomes'] = copy.deepcopy(state['counts'])
        if state['phase'] not in ('ready', 'predict'):
            result['trace'] = model.snapshot(ctx['item']['public']['exercise'], original['trace'], state['cursor'])
        if state['prediction_revealed']:
            result['final'] = copy.deepcopy(original['final'])
        if surface == 'presenter-controls':
            result['control_version'] = state['control_version']
            page = ctx['record_page']
            result['roster'] = copy.deepcopy(page)
            if state['selected']:
                result['selected'] = {'actor': state['selected']['actor'], **storage.projected(
                    state['selected']['record'], prediction_revealed=True, revealed=True)}
        if revealed:
            result['worked'] = copy.deepcopy(ctx['item']['private']['worked'])
            if state['shared']:
                result['shared'] = storage.projected(state['shared']['record'], prediction_revealed=True, revealed=True)
        if storage.size(result) > VIEW_BYTES:
            raise ValueError('view-capacity')
        return result

# SPDX-License-Identifier: Apache-2.0
"""Bounded actor values. Full engine traces are never stored per participant."""
import copy
from .model import canonical, InputError

MAX_ACTORS = 1000
MAX_VERSION = 1_000_000_000
VALUE_BYTES = 3072
SUMMARY_BYTES = 256
FEEDBACK_RESERVE = 512
PHASES = ('prediction', 'diagnosis', 'repair')


def size(value):
    return len(canonical(value).encode('ascii'))


def record(ctx):
    value = ctx['records']['value']
    return copy.deepcopy(value) if value else {'epoch': ctx['epoch'], 'version': 0, **dict.fromkeys(PHASES)}


def summary(value):
    return {'version': value['version'], **{phase: value[phase]['status'] if value[phase] else 'none' for phase in PHASES}}


def check(value):
    reserve = FEEDBACK_RESERVE if value['repair'] and value['repair']['status'] == 'pending' else 0
    if size(value) + reserve > VALUE_BYTES or size(summary(value)) > SUMMARY_BYTES:
        raise InputError('answer-capacity')
    return value


def projected(value, *, prediction_revealed, revealed):
    result = {'version': value['version']}
    for phase in PHASES:
        slot = value[phase]
        if slot:
            result[phase] = {k: copy.deepcopy(slot[k]) for k in ('version', 'answer', 'status')}
            if 'feedback' in slot and (revealed or phase == 'prediction' and prediction_revealed or slot['status'] == 'unavailable'):
                result[phase]['feedback'] = copy.deepcopy(slot['feedback'])
    return result

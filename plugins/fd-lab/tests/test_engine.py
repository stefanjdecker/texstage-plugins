# SPDX-License-Identifier: Apache-2.0
"""Installed artifact, mathematical, parser, lifecycle and host contract checks."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest
from texstage.plugins import PluginError
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, validate_outcome, validate_portable_schema
from texstage_fd_lab import model

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('fd_probe', ROOT / 'maintenance/fd_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture(scope='module')
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}, 'Use an FD-only installed-wheel environment.'
    selected, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    assert not Path(model.__file__).is_relative_to(ROOT / 'plugins/fd-lab')
    subprocess.run([sys.executable, '-c', "import sys; from texstage.plugins.catalog import discover; discover(); assert 'texstage_fd_lab' not in sys.modules"], check=True)
    return selected


@pytest.fixture(scope='module')
def examples(provider):
    return {item['lesson']['exercise']['id']: model.compile_lesson(item['lesson'])
            for item in probe.fixture(provider, 'examples.json')['examples']}


def checked(seed, answer, row):
    assert not row.get('load_or_contract_error'), row
    assert row['result']['status'] == 'ok', row
    assert row['reuseRefused'] and row['disposalRefused']
    data = row['result']['data']
    assert data == model.analyze(seed, answer) == row['outcome']['data']
    assert row['result']['canonical'] == model.digest(['fd-analysis-v1', data['exercise'], data['answer']])
    assert len(model.canonical(data)) <= 8192
    assert len(model.canonical(row['outcome'])) <= 12288
    return data['facts']


def accepted(seed, answer, facts):
    # Explicit test policy, separate from the engine's facts and canonical key.
    if answer['mode'] == 'keys':
        return (set(answer['keys']) == set(facts['candidate_keys']) if seed['task']['require'] == 'all'
                else answer['keys'][0] in facts['candidate_keys'])
    if answer['mode'] == 'closure':
        return facts['trace']['error'] is None and answer['closure'] == facts['closure'] == facts['trace']['reached']
    if answer['implied']:
        proof = facts['proof']
        return proof['error'] is None and seed['task']['rhs'] & proof['reached'] == seed['task']['rhs']
    return not facts['proof']['violated_fds'] and facts['proof']['violates_target']


def tiny(n, fds, task=None):
    return {'format': 1, 'id': 'tiny', 'attributes': [chr(97 + i) for i in range(n)],
            'fds': [{'id': 'f' + str(i), 'lhs': lhs, 'rhs': rhs} for i, (lhs, rhs) in enumerate(fds)],
            'task': task or {'mode': 'keys', 'require': 'all'}}


def test_manifest_and_owned_schemas(provider):
    assert set(provider.manifest['capabilities']) == {'engines', 'content_types'}
    assert set(provider.manifest['capabilities']['content_types']) == {probe.PROVIDER + '.exercise'}
    assert set(provider.manifest['capabilities']['engines']) == {probe.ENGINE}
    for name in ('answer', 'analysis-result'):
        validate_portable_schema(json.loads(provider.resources[f'{probe.PACKAGE}/schemas/{name}-v1.json']))
    for name in ('examples.json', 'expected-cases.json'):
        assert probe.fixture(provider, name) == json.loads((ROOT / 'docs/design/functional-dependencies' / name).read_text(encoding='utf-8'))
    module = provider.resources[f'{probe.PACKAGE}/web/engine.worker.mjs'].decode()
    assert not any(line.startswith('import ') for line in module.splitlines())


def test_all_hand_derived_cases(provider, examples):
    cases = probe.fixture(provider, 'expected-cases.json')['cases']
    inputs = [(examples[c['example']][0], c['answer']) for c in cases]
    rows = probe.run([probe.request(seed, answer) for seed, answer in inputs])
    for case, (seed, answer), row in zip(cases, inputs, rows, strict=True):
        facts = checked(seed, answer, row)
        assert accepted(seed, answer, facts) is case['accepted'], case['id']


def test_worked_lessons(examples):
    values = list(examples.values())
    rows = probe.run([probe.request(seed, answer) for seed, answer in values])
    for (seed, answer), row in zip(values, rows, strict=True):
        assert accepted(seed, answer, checked(seed, answer, row))


def test_all_three_attribute_theories(provider):
    atoms = [(lhs, 1 << i) for i in range(3) for lhs in range(8) if not lhs & (1 << i)]
    requests, tables = [], []
    answer = {'format': 1, 'mode': 'keys', 'keys': list(range(8))}
    for choice in range(1 << len(atoms)):
        fds = [fd for i, fd in enumerate(atoms) if choice & (1 << i)]
        seed = tiny(3, fds)
        # Closed-set intersection is independent of forward chaining in both engines.
        closed = [s for s in range(8) if all(lhs & s != lhs or rhs & s == rhs for lhs, rhs in fds)]
        table = []
        for start in range(8):
            result = 7
            for s in closed:
                if start & s == start:
                    result &= s
            table.append(result)
        assert model.closure_table(seed) == table
        tables.append(table)
        requests.append(probe.request(seed, answer))
    rows = probe.run(requests, timeout=120)
    for request, table, row in zip(requests, tables, rows, strict=True):
        facts = checked(json.loads(request['seed']), answer, row)
        assert [check[1] for check in facts['checks']] == table


def test_large_composite_theories_and_transport(provider):
    rng = random.Random(26536)
    seeds = [tiny(8, [(1 << i, 1 << (i ^ 1)) for i in range(8)])]
    seeds += [tiny(8, [(rng.randrange(256), rng.randrange(1, 256)) for _ in range(24)]) for _ in range(32)]
    answer = {'format': 1, 'mode': 'keys', 'keys': list(range(256))}
    rows = probe.run([probe.request(seed, answer) for seed in seeds])
    for seed, row in zip(seeds, rows, strict=True):
        facts = checked(seed, answer, row)
        budget = model.Budget()
        model.analyze(seed, answer, budget)
        assert 0 <= budget.remaining < 65536
        for key, closure, removable in facts['checks']:
            assert removable & key == removable
            if closure != 255:
                assert removable == 0
    assert len(rows[0]['result']['data']['facts']['candidate_keys']) == 16


def test_derivation_prefix_alternatives_trivial_and_empty():
    requests = []
    for steps in ([0, 1], [1, 0]):
        seed = tiny(3, [(1, 2), (1, 4)], {'mode': 'closure', 'start': 1})
        requests.append(probe.request(seed, {'format': 1, 'mode': 'closure', 'closure': 7, 'steps': steps}))
    for task, steps in [({'mode': 'implication', 'lhs': 1, 'rhs': 2}, [0]),
                        ({'mode': 'implication', 'lhs': 1, 'rhs': 1}, [])]:
        requests.append(probe.request(tiny(3, [(1, 2), (2, 4)], task),
                                      {'format': 1, 'mode': 'implication', 'implied': True, 'steps': steps}))
    requests.append(probe.request(tiny(1, [], {'mode': 'closure', 'start': 0}),
                                  {'format': 1, 'mode': 'closure', 'closure': 0, 'steps': []}))
    rows = probe.run(requests)
    for req, row in zip(requests, rows, strict=True):
        seed, answer = json.loads(req['seed']), json.loads(req['text'])
        assert accepted(seed, answer, checked(seed, answer, row))
    assert rows[0]['outcome']['key'] != rows[1]['outcome']['key']


@pytest.mark.parametrize('text', [
    '{', 'null', '[]', '{"format":1,"format":1}',
    '{"format":1.0,"mode":"keys","keys":[]}',
    '{"format":1e0,"mode":"keys","keys":[]}',
    '{"format":true,"mode":"keys","keys":[]}',
    '{"format":1,"mode":"keys","keys":[true]}',
    '{"format":1,"mode":"keys","keys":[5,5]}',
    '{"format":1,"mode":"keys","keys":[64]}',
    '{"format":1,"mode":"keys","keys":[-1]}',
    '{"format":1,"mode":"keys","keys":[],"extra":0}',
    '{"format":1,"mode":"keys","keys":[NaN]}',
    '{"format":1,"mode":"keys","keys":[Infinity]}',
    '{"format":1,"mode":"keys","keys":[9007199254740992]}',
    '{"format":1,"mode":"closure","closure":0,"steps":[]}',
    '"\\ud800"', '[' * 20 + '0' + ']' * 20,
])
def test_malformed_answers(examples, text):
    seed = examples['workshop_all'][0]
    row = probe.run([{'seed': model.canonical(seed), 'text': text}])[0]
    assert row['outcome'] == {'status': 'syntax'}
    assert row['reuseRefused'] and row['disposalRefused']


@pytest.mark.parametrize('change', ['extra', 'duplicate-id', 'unknown-attribute', 'rhs-zero', 'mask', 'empty-schema', 'too-many-fds', 'newline-id', 'bad-mode'])
def test_invalid_seed(examples, change):
    seed = copy.deepcopy(examples['workshop_all'][0])
    if change == 'extra': seed['extra'] = 0
    elif change == 'duplicate-id': seed['fds'][1]['id'] = seed['fds'][0]['id']
    elif change == 'unknown-attribute': seed['attributes'][0] = 'Not valid'
    elif change == 'rhs-zero': seed['fds'][0]['rhs'] = 0
    elif change == 'mask': seed['fds'][0]['lhs'] = 64
    elif change == 'empty-schema': seed['attributes'] = []
    elif change == 'too-many-fds': seed['fds'] *= 7
    elif change == 'newline-id': seed['id'] += '\n'
    else: seed['task'] = {'mode': 'covers'}
    with pytest.raises(model.InputError): model.source(seed)
    assert probe.run([probe.request(seed, {'format': 1, 'mode': 'keys', 'keys': []})])[0]['load_or_contract_error']


def test_named_source_validation(provider):
    original = probe.fixture(provider, 'examples.json')['examples'][0]['lesson']
    for change in ('duplicate-attribute', 'unknown-name', 'duplicate-fd', 'worked-proof', 'worked-mode', 'duplicate-normalized-key'):
        value = copy.deepcopy(original)
        if change == 'duplicate-attribute': value['exercise']['attributes'][1]['id'] = 'person'
        elif change == 'unknown-name': value['exercise']['fds'][0]['lhs'] = ['absent']
        elif change == 'duplicate-fd': value['exercise']['fds'][1]['id'] = 'f1'
        elif change == 'worked-proof': value['worked_answer']['steps'] = ['f4', 'f3']
        elif change == 'worked-mode': value['worked_answer'] = {'mode': 'keys', 'keys': [['person', 'workshop']]}
        else:
            value['exercise']['task'] = {'mode': 'keys', 'require': 'all'}
            value['worked_answer'] = {'mode': 'keys', 'keys': [['person', 'workshop'], ['workshop', 'person']]}
        with pytest.raises(model.InputError): model.compile_lesson(value)
    value = copy.deepcopy(original)
    value['exercise']['title']['de'] = 'Gru\u0308ße 😀'
    assert model.compile_lesson(value) == model.compile_lesson(original)


def test_budget_options_lifecycle_and_hashes(examples):
    seed, answer = examples['workshop_all']
    requests = [probe.request(seed, answer, budget=0),
                probe.request(seed, answer, options={'hidden': True}),
                {'seed': model.canonical(seed), 'text': ' ' * 2001},
                probe.request(seed, answer),
                *[{'hash': text} for text in ('', 'abc', 'Grüße 😀', 'a' * 1000)]]
    rows = probe.run(requests)
    assert rows[0]['budget_error'] == 'ResourceLimit'
    assert rows[1]['load_or_contract_error']
    assert rows[2]['outcome'] == {'status': 'refused'}
    checked(seed, answer, rows[3])
    with pytest.raises(model.ResourceLimit): model.analyze(seed, answer, model.Budget(0))
    for row, req in zip(rows[4:], requests[4:], strict=True):
        assert row['hash'] == hashlib.sha256(req['hash'].encode('utf-8')).hexdigest()


def test_actual_bound_outcomes_and_schema_rejection(examples, provider):
    seed, answer = examples['workshop_all']
    _, engine = probe.installed()
    req = probe.bound_requests(provider, engine, [probe.request(seed, answer)])[0]
    row = probe.run([req])[0]
    validate_outcome(row['outcome'], provider, engine, req['namespace'])
    assert req['namespace'] == namespace(provider, probe.ENGINE, engine, req['binding'])
    with pytest.raises(PluginError): validate_outcome(row['outcome'], provider, engine, 'f' * 64)
    for patch in ({'extra': 1}, {'format': 2}, {'exercise': 'x'},
                  {'facts': {'candidate_keys': [], 'checks': []}},
                  {'facts': {'candidate_keys': [1], 'checks': [[1, 3]]}}):
        bad = copy.deepcopy(row['outcome'])
        bad['data'].update(patch)
        with pytest.raises(PluginError): validate_outcome(bad, provider, engine, req['namespace'])
        assert probe.run([probe.request(seed, answer, data_patch=patch)])[0]['load_or_contract_error']


def test_canonical_key_order_and_exercise_identity(examples):
    seed, answer = examples['workshop_all']
    reversed_answer = answer | {'keys': list(reversed(answer['keys']))}
    changed_seed = copy.deepcopy(seed)
    changed_seed['attributes'][0], changed_seed['attributes'][1] = changed_seed['attributes'][1], changed_seed['attributes'][0]
    rows = probe.run([probe.request(seed, answer), probe.request(seed, reversed_answer), probe.request(changed_seed, answer)])
    assert rows[0]['outcome'] == rows[1]['outcome']
    assert rows[0]['result']['data']['exercise'] != rows[2]['result']['data']['exercise']


def test_seed_text_and_proof_indices(examples):
    seed, answer = examples['workshop_closure']
    bad_seeds = ['{"format":1,"format":1}', '"\\ud800"', '[' * 20 + '0' + ']' * 20,
                 '9' * 5000, model.canonical(seed).replace('"format":1', '"format":1.0')]
    for text in bad_seeds:
        with pytest.raises(model.InputError):
            model.source(model.parse(text))
    rows = probe.run([{'seed': text, 'text': model.canonical(answer)} for text in bad_seeds])
    assert all(row['load_or_contract_error'] for row in rows)
    invalid = [answer | {'steps': [4]}, answer | {'steps': [True]},
               answer | {'steps': [0] * 9}, answer | {'steps': [-1]}]
    assert all(row['outcome'] == {'status': 'syntax'} for row in probe.run([probe.request(seed, a) for a in invalid]))


def test_counterexamples_on_small_instances():
    rng = random.Random(26537)
    requests = []
    for _ in range(100):
        n = rng.randrange(1, 9)
        universe = (1 << n) - 1
        fds = [(rng.randrange(universe + 1), rng.randrange(1, universe + 1)) for _ in range(12)]
        lhs, rhs = rng.randrange(universe + 1), rng.randrange(1, universe + 1)
        seed = tiny(n, fds, {'mode': 'implication', 'lhs': lhs, 'rhs': rhs})
        closure = model.closure(lhs, seed['fds'])
        requests.append(probe.request(seed, {'format': 1, 'mode': 'implication', 'implied': False, 'agree': closure}))
    for req, row in zip(requests, probe.run(requests), strict=True):
        facts = checked(json.loads(req['seed']), json.loads(req['text']), row)
        assert not facts['proof']['violated_fds']
        assert facts['proof']['violates_target'] is not facts['implied']

# SPDX-License-Identifier: Apache-2.0
"""Probe an installed B+ tree engine and the matching installed host result contracts."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import texstage
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, result_contract, validate_outcome
from texstage_bplus_lab import model

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = 'io.github.stefanjdecker.bpluslab'
ENGINE = PROVIDER + '.operations'
PACKAGE = 'texstage_bplus_lab'


def installed():
    providers = {p.id: p for p in discover()}
    if PROVIDER not in providers:
        raise RuntimeError('Install the B+ Tree Lab wheel in this environment first.')
    provider = providers[PROVIDER]
    if not provider.root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError('Use an isolated environment with installed wheels.')
    provider.verify()
    return provider, provider.manifest['capabilities']['engines'][ENGINE]


def fixture(provider, name):
    return json.loads(provider.resources[f'{PACKAGE}/fixtures/{name}'])


def configuration(provider, engine):
    host = Path(texstage.__file__).resolve().parent
    binding = {'engine': ENGINE, 'seed': '', 'options': {}, 'references': []}
    return {
        'module': (provider.root / engine['module']).as_uri(),
        'identity': (provider.root / f'{PACKAGE}/web/identity.mjs').as_uri(),
        'contract_module': (host / 'web/stage/plugin-contracts.js').as_uri(),
        'host_root': str(host), 'provider_root': str(provider.root), 'payload': provider.payload,
        'job': {'engine': engine | {'result_contract': result_contract(provider, engine)},
                'namespace': namespace(provider, ENGINE, engine, binding), 'binding': binding},
    }


def request(seed, answer, **extra):
    return {'seed': model.canonical(seed), 'text': model.canonical(answer), **extra}


def bound_requests(provider, engine, requests):
    result = []
    for row in requests:
        if 'hash' in row:
            result.append(row)
            continue
        binding = row.get('binding', {'engine': ENGINE, 'seed': row['seed'],
                                     'options': row.get('options', {}), 'references': []})
        result.append(row | {'binding': binding, 'namespace': namespace(provider, ENGINE, engine, binding)})
    return result


def run(requests, *, timeout=120):
    provider, engine = installed()
    config = configuration(provider, engine)
    requests = bound_requests(provider, engine, requests)
    with tempfile.TemporaryDirectory(prefix='bplus-lab-') as temporary:
        path = Path(temporary) / 'config.json'
        path.write_text(json.dumps(config), encoding='utf-8')
        completed = subprocess.run(
            ['node', str(ROOT / 'maintenance/run_bplus_engine.mjs'), str(path)],
            input=json.dumps(requests), text=True, capture_output=True, encoding='utf-8',
            timeout=timeout, check=True)
    results = json.loads(completed.stdout)
    for row, request_row in zip(results, requests, strict=True):
        if 'outcome' in row:
            validate_outcome(row['outcome'], provider, engine, request_row['namespace'])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/bplus-lab')
    args = parser.parse_args()
    provider, engine = installed()
    examples = fixture(provider, 'design-cases.json')
    requests = []
    for case in examples['cases']:
        seed = {'format': 1, 'semantics': 'bplus-operations-v1',
                **examples['models'][case['source']], 'task': case['task']}
        requests.append(request(seed, case['answer'], case_id=case['id'],
                                expected=model.analyze(seed, case['answer'])))
    rows = run(requests)
    for row, req in zip(rows, requests, strict=True):
        if row.get('load_or_contract_error') or row['outcome'].get('data') != req['expected']:
            raise RuntimeError('Independent engine comparison failed: ' + str(row))
    config = configuration(provider, engine)
    report = {'provider': provider.requirement(), 'host_version': importlib.metadata.version('texstage'),
              'result_schema_sha256': config['job']['engine']['result_contract']['data_schema_digest'],
              'python': platform.python_version(), 'node': subprocess.check_output(['node', '--version'], text=True).strip(),
              'cases': len(rows), 'max_evaluation_ms': max(row['milliseconds'] for row in rows),
              'scope': 'Engine conformance; prepared authoring, classroom protocol and visual UI have separate probes'}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('report.json', report), ('browser-config.json', config),
                        ('browser-requests.json', bound_requests(provider, engine, requests))]:
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

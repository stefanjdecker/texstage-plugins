# SPDX-License-Identifier: Apache-2.0
"""Installed ER engine, independent Python oracle, and both host validators."""
import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import texstage
from texstage.plugins.catalog import discover
from texstage.plugins.contracts import namespace, result_contract, validate_outcome
from texstage_er_decisions import model

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "io.github.stefanjdecker.erdecisions"
ENGINE = PROVIDER + ".model"
PACKAGE = "texstage_er_decisions"


def installed():
    providers = {p.id: p for p in discover()}
    if PROVIDER not in providers:
        raise RuntimeError("Install the ER wheel in an isolated environment.")
    provider = providers[PROVIDER]
    if not provider.root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError("Expected an installed provider under the active environment.")
    provider.verify()
    return provider, provider.manifest["capabilities"]["engines"][ENGINE]


def fixture(provider):
    return json.loads(provider.resources[PACKAGE + "/fixtures/registrations.json"])


def configuration(provider, engine):
    host = Path(texstage.__file__).resolve().parent
    binding = {"engine": ENGINE, "seed": "", "options": {}, "references": []}
    return {
        "module": (provider.root / engine["module"]).as_uri(),
        "identity": (provider.root / (PACKAGE + "/web/identity.mjs")).as_uri(),
        "contract_module": (host / "web/stage/plugin-contracts.js").as_uri(),
        "host_root": str(host), "provider_root": str(provider.root), "payload": provider.payload,
        "job": {"engine": engine | {"result_contract": result_contract(provider, engine)},
                "namespace": namespace(provider, ENGINE, engine, binding), "binding": binding},
    }


def request(exercise, submission=None, **extra):
    return {"seed": json.dumps(exercise), "text": json.dumps(submission or exercise["worked_answers"][0]), **extra}


def bound_requests(provider, engine, requests):
    rows = []
    for row in requests:
        if "hash" in row:
            rows.append(row)
            continue
        binding = row.get("binding", {"engine": ENGINE, "seed": row["seed"],
                                      "options": row.get("options", {}), "references": []})
        rows.append(row | {"binding": binding, "namespace": namespace(provider, ENGINE, engine, binding)})
    return rows


def run(requests, timeout=60):
    provider, engine = installed()
    requests = bound_requests(provider, engine, requests)
    with tempfile.TemporaryDirectory(prefix="er-engine-", dir=os.environ.get("ER_TEST_TMP")) as temporary:
        path = Path(temporary) / "config.json"
        path.write_text(json.dumps(configuration(provider, engine)), encoding="utf-8")
        # The existing runner is domain-independent; retain its original name.
        completed = subprocess.run(["node", str(ROOT / "maintenance/run_relational_engine.mjs"), str(path)],
                                   input=json.dumps(requests), text=True, capture_output=True,
                                   encoding="utf-8", timeout=timeout, check=True)
    results = json.loads(completed.stdout)
    for row, request_row in zip(results, requests, strict=True):
        if "outcome" in row:
            validate_outcome(row["outcome"], provider, engine, request_row["namespace"])
    return results


def answers(exercise):
    for options in itertools.product(*(d["options"] for d in exercise["decisions"])):
        yield {"format": 1, "choices": [[d["id"], o["id"]]
               for d, o in zip(exercise["decisions"], options, strict=True)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/er-decisions")
    args = parser.parse_args()
    provider, engine = installed()
    exercise = model.source(fixture(provider))
    submissions = list(answers(exercise))
    requests = [request(exercise, a) for a in submissions]
    results = run(requests)
    for submission, row in zip(submissions, results, strict=True):
        if row.get("load_or_contract_error"):
            raise RuntimeError(row)
        if row["outcome"].get("data") != model.analyze(exercise, submission):
            raise RuntimeError("Independent Python and installed browser engine disagree.")
    args.output.mkdir(parents=True, exist_ok=True)
    config = configuration(provider, engine)
    host = Path(config["host_root"])
    host_hashes = {path.relative_to(host).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted(host.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}
    report = {
        "provider": provider.requirement(),
        "host_version": importlib.metadata.version("texstage"),
        "host_payload_sha256": hashlib.sha256(json.dumps(host_hashes, sort_keys=True).encode()).hexdigest(),
        "result_schema_sha256": config["job"]["engine"]["result_contract"]["data_schema_digest"],
        "python": platform.python_version(), "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "cases": len(results), "max_evaluation_ms": max(r["milliseconds"] for r in results),
        "max_data_bytes": max(len(model.canonical(r["outcome"]["data"])) for r in results),
        "max_outcome_bytes": max(len(model.canonical(r["outcome"])) for r in results),
        "scope": "Registration-profile engine only; no authoring, lesson state, UI or classroom-capacity claim",
    }
    for name, value in [("report", report), ("host-files", host_hashes), ("results", results),
                        ("browser-config", config), ("browser-requests", bound_requests(provider, engine, requests))]:
        (args.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

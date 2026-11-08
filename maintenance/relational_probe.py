# SPDX-License-Identifier: Apache-2.0
"""Exercise an installed engine wheel; no source-tree provider imports."""
import argparse
import hashlib
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

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "io.github.stefanjdecker.relationallab"
ENGINE = PROVIDER + ".algebra"
PACKAGE = "texstage_relational_lab"


def installed():
    providers = {p.id: p for p in discover()}
    if PROVIDER not in providers:
        raise RuntimeError("Install the relational-lab wheel in this environment first.")
    provider = providers[PROVIDER]
    if not provider.root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError("Use an isolated environment with installed wheels.")
    provider.verify()
    engine = provider.manifest["capabilities"]["engines"][ENGINE]
    return provider, engine


def fixture(provider, name):
    return json.loads(provider.resources[f"{PACKAGE}/fixtures/{name}"])


def configuration(provider, engine):
    host = Path(texstage.__file__).resolve().parent
    binding = {"seed": "", "options": {}, "references": []}
    return {
        "module": (provider.root / engine["module"]).as_uri(),
        "identity": (provider.root / f"{PACKAGE}/web/identity.mjs").as_uri(),
        "contract_module": (host / "web/stage/plugin-contracts.js").as_uri(),
        "host_root": str(host), "provider_root": str(provider.root), "payload": provider.payload,
        "job": {"engine": engine | {"result_contract": result_contract(provider, engine)},
                "namespace": namespace(provider, ENGINE, engine, binding), "binding": binding},
    }


def run(requests, *, timeout=30):
    provider, engine = installed()
    config = configuration(provider, engine)
    requests = bound_requests(provider, engine, requests)
    with tempfile.TemporaryDirectory(prefix="relational-lab-") as temporary:
        path = Path(temporary) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        completed = subprocess.run(
            ["node", str(ROOT / "maintenance/run_relational_engine.mjs"), str(path)],
            input=json.dumps(requests), text=True, capture_output=True, encoding="utf-8",
            timeout=timeout, check=True)
    results = json.loads(completed.stdout)
    for row, request in zip(results, requests, strict=True):
        if "outcome" in row:
            validate_outcome(row["outcome"], provider, engine, request["namespace"])
    return results


def request(exercise, submission=None, **extra):
    if submission is None:
        submission = ({"mode": "construct", "tree": exercise["reference_tree"]}
                      if exercise["task"]["mode"] == "construct" else {"mode": "rewrite", "steps": []})
    return {"seed": json.dumps(exercise), "text": json.dumps(submission), **extra}


def bound_requests(provider, engine, requests):
    return [row if "hash" in row else row | {"namespace": namespace(provider, ENGINE, engine,
            row.get("binding", {"seed": row["seed"], "options": row.get("options", {}), "references": []}))}
            for row in requests]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/relational-lab")
    args = parser.parse_args()
    provider, engine = installed()
    exercise = fixture(provider, "construct.exercise.json")
    rewrite = fixture(provider, "rewrite.exercise.json")
    expected = fixture(provider, "expected-cases.json")
    cases = [
        ("late-filter", request(exercise)),
        ("early-filter", request(exercise, {"mode": "construct", "tree": expected["construction"][1]["tree"]})),
        ("overfit-public", request(exercise, {"mode": "construct", "tree": expected["construction"][4]["tree"]})),
        ("verified-rewrite", request(rewrite, {"mode": "rewrite", "steps": expected["rewrite"]["steps"]})),
    ]
    results = run([row for _, row in cases])
    for row in results:
        if row.get("load_or_contract_error"):
            raise RuntimeError(row["error"])
    args.output.mkdir(parents=True, exist_ok=True)
    for (name, _), row in zip(cases, results):
        (args.output / f"{name}.json").write_text(json.dumps(row["outcome"], indent=2) + "\n", encoding="utf-8")
    config = configuration(provider, engine)
    host = Path(config["host_root"])
    host_hashes = {path.relative_to(host).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted(host.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}
    report = {
        "provider": provider.requirement(), "host_version": importlib.metadata.version("texstage"),
        "host_payload_sha256": hashlib.sha256(json.dumps(host_hashes, sort_keys=True).encode()).hexdigest(),
        "host_files": host_hashes,
        "result_schema_sha256": config["job"]["engine"]["result_contract"]["data_schema_digest"],
        "python": platform.python_version(), "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "cases": len(results), "max_evaluation_ms": max(row["milliseconds"] for row in results),
        "scope": "Installed engine and contract checks only; lesson/editor validation is recorded separately",
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "browser-config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    (args.output / "browser-requests.json").write_text(json.dumps(
        bound_requests(provider, engine, [row for _, row in cases]),
        indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "host_files"}, indent=2))


if __name__ == "__main__":
    main()

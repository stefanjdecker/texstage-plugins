# SPDX-License-Identifier: Apache-2.0
"""Contract shape and byte ceilings, independent of future lesson implementation."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

from jsonschema import Draft202012Validator
from texstage.plugins.contracts import validate_portable_schema
from texstage_normalization_workshop import validation as v
from texstage_normalization_workshop import model

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("normalization_probe_contracts", ROOT / "maintenance/normalization_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def maximum(schema, root):
    if "$ref" in schema:
        target = root
        for part in schema["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return maximum(target, root)
    if "oneOf" in schema or "anyOf" in schema:
        choices = [maximum(s, root) for s in schema.get("oneOf", schema.get("anyOf"))]
        return max(choices, key=lambda x: len(v.canonical(x)))
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return max(schema["enum"], key=lambda x: len(v.canonical(x)))
    kind = schema.get("type")
    if kind == "null": return None
    if kind == "boolean": return False
    if kind == "integer": return schema["maximum"]
    if kind == "string": return "\U0001F680" * schema["maxLength"]
    if kind == "object": return {k: maximum(s, root) for k, s in schema["properties"].items()}
    if kind == "array":
        if "prefixItems" in schema:
            return [maximum(s, root) for s in schema["prefixItems"]]
        value = maximum(schema["items"], root)
        values = [copy.deepcopy(value) for _ in range(schema["maxItems"])]
        if schema.get("uniqueItems"):
            assert type(value) is int, "Extend this generator if the frozen format changes."
            values = [value - i for i in range(schema["maxItems"])]
        return values
    raise AssertionError(schema)


def test_frozen_schema_freshness():
    subprocess.run(["python", str(ROOT / "maintenance/build_normalization_schemas.py"), "--check"], check=True)


def test_portable_views_state_and_result_budgets():
    provider, _ = probe.installed()
    config = probe.configuration(*probe.installed())
    requests, sizes = [], {}
    for name, raw in provider.resources.items():
        if "/schemas/" not in name or not name.endswith(".json"): continue
        schema = json.loads(raw)
        Draft202012Validator.check_schema(schema)
        if name.endswith(("lesson-v1.json", "lesson-v2.json", "seed-v1.json")): continue
        validate_portable_schema(schema)
        largest = maximum(schema, schema)
        assert not list(Draft202012Validator(schema).iter_errors(largest)), name
        size = len(v.canonical(largest).encode("ascii"))
        sizes[name] = size
        requests.append({"schema": schema, "value": largest, "expected": True})
        requests.append({"schema": schema, "value": largest | {"private_leak": "not declared"}, "expected": False})
        if name.endswith("analysis-result-v1.json"):
            # Also exercise the other branch: the bound includes all 70 possible keys.
            classifier = maximum(schema["oneOf"][0], schema)
            assert len(classifier["facts"]["keys"]) == 70
            assert not list(Draft202012Validator(schema).iter_errors(classifier))
            requests.append({"schema": schema, "value": classifier, "expected": True})
            sizes["classify_70_keys"] = len(v.canonical(classifier))
            assert sizes["classify_70_keys"] < 8192
            assert size < 8192
            outcome = {"status": "ok", "key": "f" * 64, "namespace": "e" * 64,
                       "summary": {"kind": "text", "text": "Schema properties checked under the stated functional dependencies."},
                       "data": largest}
            sizes["complete_outcome"] = len(v.canonical(outcome))
            assert sizes["complete_outcome"] < 12288
        if "/views/" in name: assert size < 128 * 1024
        if name.endswith("state-v3.json"): assert size < 8192
        if name.endswith("record-v1.json"): assert size + 256 < 3072
        if name.endswith(("state-v1.json", "state-v2.json")):
            assert size < 224 * 1024
            assert max(len(v.canonical(slot)) for slot in largest["actors"]) < 3072
            assert max(len(v.canonical(slot["feedback"])) for slot in largest["actors"]) <= 256
            # One cancellation and one accepted replacement evaluation.
            transition = {"state": largest, "effects": [
                {"kind": "cancel-evaluation", "correlation_id": "a" * 64},
                {"kind": "evaluate", "binding": "analysis", "correlation_id": "b" * 64, "text": "x" * 512}]}
            sizes["replacement_transition"] = len(v.canonical(transition))
            assert sizes["replacement_transition"] < 256 * 1024
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "contracts.json"
        path.write_text(json.dumps({"module": config["contract_module"], "cases": requests}), encoding="utf-8")
        subprocess.run(["node", str(ROOT / "maintenance/check_normalization_contracts.mjs"), str(path)], check=True)
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/normalization-schema-budgets.json").write_text(json.dumps(sizes, indent=2) + "\n", encoding="utf-8", newline="\n")


def test_compilation_budget_and_type_boundaries():
    provider, _ = probe.installed()
    lesson = probe.fixture(provider, "registration.lesson.draft.json")
    excessive = copy.deepcopy(lesson)
    excessive["exercise"]["fds"] = [{"lhs": [], "rhs": list("SNCTIO")}] * 6
    try:
        v.compile_lesson(excessive)
    except v.InputError as error:
        assert "expanded-fds" in str(error)
    else:
        raise AssertionError("Expanded FD cap was ignored.")
    missing = copy.deepcopy(lesson)
    missing["worked_answer"] = {"mode": "classify", "normal_form": "bcnf", "witness": None}
    try: v.compile_lesson(missing)
    except v.InputError: pass
    else: raise AssertionError("Mode is fixed by source.")
    for text in ['{"x":1,"x":2}', '{"x":1.0}', '{"x":Infinity}', '{"\\u00e9":1,"e\\u0301":2}']:
        try: v.parse(text)
        except v.InputError: pass
        else: raise AssertionError(text)

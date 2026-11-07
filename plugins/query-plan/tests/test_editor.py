# SPDX-License-Identifier: Apache-2.0
"""Installed selector reachability versus the independently written cost model."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from texstage_query_plan import model
import texstage_query_plan

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "maintenance"))
import query_plan_probe as probe

PROVIDER, _ = probe.installed()
WEB = Path(texstage_query_plan.__file__).parent / "web"


def node(script, value):
    prefix = (
        f'import * as editor from {json.dumps((WEB / "plan-editor.mjs").as_uri())};\n'
        f'import {{analyze}} from {json.dumps((WEB / "model.mjs").as_uri())};\n'
        f'import {{arithmetic}} from {json.dumps((WEB / "cost-inspector.mjs").as_uri())};\n'
        'import fs from "node:fs";const input=JSON.parse(fs.readFileSync(0,"utf8"));\n'
    )
    result = subprocess.run(["node", "--input-type=module", "-e", prefix + script],
        input=json.dumps(value), text=True, encoding="utf-8", capture_output=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize("name", ["selective", "broad", "library", "memory"])
def test_selectors_reach_every_feasible_plan_and_preserve_roundtrips(name):
    source = json.loads((ROOT / f"examples/query-plan/activities/{name}.json").read_text())
    expected = {}
    all_plans = list(model.candidates(source["exercise"]))
    for answer in all_plans:
        result = model.analyze(source["exercise"], answer)
        if result["valid"]:
            expected[model.canonical(answer)] = result["cost"]
    actual = node("""
const {exercise,baseline}=input.source, found={};
for(const tree of editor.topologies(exercise)){
 const plan=editor.retopologize(baseline,tree);
 const choices=plan.nodes.map(n=>n.op==="join"?["nested","hash-left","hash-right"]:
  exercise.query.relations.find(r=>r.id===n.relation).index?["seq","index"]:["seq"]);
 function walk(i){
  if(i<plan.nodes.length){for(const method of choices[i]){plan.nodes[i].method=method;walk(i+1);}return;}
  const result=analyze(exercise,plan);if(result.valid)found[editor.key(plan)]=result.cost;
 }
 walk(0);
}
for(const answer of input.all){
 const r=analyze(exercise,answer),ok=editor.supported(exercise,answer);
 if(r.valid&&!ok)throw Error("unreachable feasible answer");
 if(ok&&editor.key(answer)!==editor.key(editor.retopologize(answer,editor.topology(answer))))throw Error("roundtrip changed answer");
 if(r.valid){
  const g=editor.geometry(exercise,answer);
  for(const f of r.nodes)if(g[f.node].rows!==f.rows||g[f.node].width!==f.row_bytes)throw Error("geometry disagrees");
 }
}
console.log(JSON.stringify(found));
""", {"source": source, "all": all_plans})
    assert actual == expected
    assert len(actual) > 0


def test_three_index_chain_excludes_cartesian_shapes_from_864_candidates():
    exercise = json.loads((ROOT / "examples/query-plan/activities/library.json").read_text())["exercise"]
    # Three eligible indexes achieve the enumerator bound. The frozen query is
    # a tree (two predicates); the selector excludes disconnected subtrees.
    for r in exercise["query"]["relations"]:
        if "filter" not in r:
            r["filter"] = {"column": r["columns"][0]["id"], "value": 1}
        r["index"] = {"column": r["filter"]["column"], "height": 1}
    count = node("""
console.log(JSON.stringify(editor.topologies(input).length));
""", exercise)
    assert count == 8
    assert len(list(model.candidates(exercise))) == 864


def test_infeasible_saved_hash_remains_editable_with_explained_workspace():
    source = json.loads((ROOT / "examples/query-plan/activities/memory.json").read_text())
    answer = next(p for p in model.candidates(source["exercise"])
                  if model.analyze(source["exercise"], p).get("reason") == "hash-memory")
    result = node("""
const r=analyze(input.exercise,input.answer),g=editor.geometry(input.exercise,input.answer);
console.log(JSON.stringify({supported:editor.supported(input.exercise,input.answer),result:r,geometry:g}));
""", {"exercise": source["exercise"], "answer": answer})
    assert result["supported"]
    fact = result["geometry"][result["result"]["node"]]
    chosen = answer["nodes"][result["result"]["node"]]["method"]
    assert fact["leftBytes" if chosen == "hash-left" else "rightBytes"] > 1024


def test_invalid_external_answers_do_not_recurse_or_crash_the_editor():
    exercise = json.loads((ROOT / "examples/query-plan/activities/library.json").read_text())["exercise"]
    malformed = [
        {"format": 1, "nodes": []},
        {"format": 1, "nodes": [{"op": "join", "left": 0, "right": 0, "method": "nested"}]},
        {"format": 1, "nodes": [{"op": "scan", "relation": "missing", "method": "seq"}]},
        None,
    ]
    assert node("console.log(JSON.stringify(input.answers.map(a=>editor.supported(input.exercise,a))));",
                {"exercise": exercise, "answers": malformed}) == [False] * len(malformed)


def test_inspector_arithmetic_has_independent_hand_calculated_values():
    source = json.loads((ROOT / "examples/query-plan/activities/selective.json").read_text())
    result = node("""
const r=analyze(input.exercise,input.worked_answer);
console.log(JSON.stringify(arithmetic(input.exercise,input.worked_answer,r,0,"en")));
""", source)
    assert result == {"formula": "400 × (3 + 10) + 10 = 5,210", "memory": ""}


def test_all_renderer_imports_are_in_the_installed_payload():
    import re
    resources = PROVIDER.resources
    prefix = "texstage_query_plan/web/"
    for name, content in resources.items():
        if name.startswith(prefix) and name.endswith(".mjs"):
            for relative in re.findall(r'from\s+["\']\./([^"\']+)["\']', content.decode()):
                assert prefix + relative in resources, (name, relative)
    content = PROVIDER.manifest["capabilities"]["content_types"][probe.PROVIDER + ".challenge"]
    assert set(content["views"]) == {"participant-input", "presenter-overlay", "projector-overlay", "presenter-controls"}

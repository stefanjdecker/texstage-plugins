# SPDX-License-Identifier: Apache-2.0
"""Generate the E3 registration message and four closed portable view schemas."""
import copy
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "plugins/er-decisions"
PKG = ROOT / "texstage_er_decisions"
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
def obj(props, optional=()):
    return {"type":"object","additionalProperties":False,"properties":props,
            "required":[k for k in props if k not in optional]}
def string(limit, minimum=0):
    return {"type":"string","minLength":minimum,"maxLength":limit}
def integer(maximum, minimum=0):
    return {"type":"integer","minimum":minimum,"maximum":maximum}
def array(item, maximum, minimum=0):
    return {"type":"array","minItems":minimum,"maxItems":maximum,"items":item}
def ref(name):
    return {"$ref":"#/$defs/"+name}
def expand(node, root):
    if isinstance(node, list):
        return [expand(x, root) for x in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        value=root
        for key in node["$ref"][2:].split("/"):
            value=value[key]
        return expand(value, root)
    return {k:expand(v, root) for k,v in node.items() if k not in ("$defs","$schema")}

source = json.loads((PKG/"schemas/exercise-v1.json").read_text(encoding="utf-8"))
answer = expand(source["$defs"]["answer"], source)
graph = expand(source["$defs"]["model"], source)
snapshot = expand(source["$defs"]["snapshot"], source)
for key in ("id", "expected", "visibility", "requirements"):
    snapshot["properties"].pop(key)
    snapshot["required"].remove(key)
locale=obj({"en":string(150,1),"de":string(150,1)})
feedback = {"oneOf":[obj({"code":{"enum":["checked","contradiction"]},"correct":{"type":"boolean"},"failed":integer(12)}),
                       obj({"code":{"const":"unavailable"}})]}
private_feedback={"oneOf":feedback["oneOf"][:1]+[
    obj({"code":{"const":"unavailable"},"detail":{"enum":["identity","facts","evaluation"]}})]}
defs={"answer":answer,"model":graph,"feedback":feedback,"privateFeedback":private_feedback,
      "demonstration":obj({"answer":ref("answer"),"model":ref("model"),"rationale":string(160)},("rationale",)),
      "teaching":obj({
          "worked":array(obj({"answer":ref("answer"),"model":ref("model"),"explanation":locale}),2,1),
          "counterexamples":array(obj({"answer":ref("answer"),"snapshot":snapshot,"explanation":locale}),2,1)})}
base={"phase":{"enum":["introduce","open","closed","revealed"]},"phase_version":integer(1_000_000_000),
      "active":{"type":"boolean"},"count":integer(600)}
status={"enum":["pending","saved","unavailable"]}
own=obj({"version":integer(1_000_000_000,1),"answer":ref("answer"),"rationale":string(160),
         "status":status,"feedback":ref("feedback"),"points":integer(10000)},("feedback","points"))
selected=obj({"answer":ref("answer"),"model":ref("model"),"actor":string(256,1),
              "version":integer(1_000_000_000,1),"rationale":string(160),"status":status,
              "feedback":ref("privateFeedback")},("feedback",))
schemas={
    "participant-input":obj({k:v for k,v in base.items() if k != "count"}|{"own":own,"teaching":ref("teaching")},("own","teaching")),
    "projector-overlay":obj(base|{"demonstration":ref("demonstration"),"teaching":ref("teaching")},("demonstration","teaching")),
    "presenter-overlay":obj(base|{"selected":obj({"answer":ref("answer"),"model":ref("model")}),
                                 "demonstration":ref("demonstration"),"teaching":ref("teaching")},("selected","demonstration")),
    "presenter-controls":obj(base|{
        "control_version":integer(1_000_000_000),"page":integer(37),"pages":integer(38,1),
        "counts":obj({k:integer(600) for k in ("pending","correct","incorrect","unavailable")}),
        "participants":array(obj({"actor":string(256,1),"number":integer(600,1),"version":integer(1_000_000_000,1),
                                  "status":{"enum":["pending","correct","incorrect","unavailable"]}}),16),
        "options":array(obj({"decision":string(24,1),"counts":array(obj({"option":string(24,1),"count":integer(600)}),4,1)}),3,1),
        "selected":selected,"demonstration":ref("demonstration"),"teaching":ref("teaching")
    },("selected","demonstration")),
}
for name,schema in schemas.items():
    # Only reachable definitions; avoid unused-schema traversal and ambiguity.
    needed=set()
    def visit(value):
        if isinstance(value,dict):
            if "$ref" in value:
                key=value["$ref"].rsplit("/",1)[1]
                if key not in needed:
                    needed.add(key); visit(defs[key])
            for key, child in value.items():
                if key!="$ref": visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    visit(schema)
    write(PKG/f"schemas/views/{name}.json",schema|{"$defs":{k:defs[k] for k in sorted(needed)}})

version=integer(1_000_000_000)
control={"control_version":version}
commands={
    "submit":obj({"phase_version":version,"answer_version":version,
                  "choices":answer["properties"]["choices"],"rationale":string(160)},("rationale",)),
    "control":obj(control),
    "select":obj(control|{"actor":string(256),"answer_version":version}),
    "share":obj(control|{"actor":string(256,1),"answer_version":integer(1_000_000_000,1),
                         "include_rationale":{"type":"boolean"}}),
    "page":obj(control|{"page":integer(37)}),
}
for name, schema in commands.items():
    write(PKG/f"schemas/commands/{name}.json",schema)

manifest=json.loads((ROOT/"texstage-plugin.json").read_text(encoding="utf-8"))
manifest["version"]=tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
manifest["manifest_version"]=4
manifest["description"]="ER registration engine and interactive prepared lesson."
content=manifest["capabilities"]["content_types"]["io.github.stefanjdecker.erdecisions.lesson"]
content["state_schema"]=4
content["scoring"]={"policy":"fixed-v1","points_field":"points"}
content["state_records"]=True
content["participant_updates"]="actor"
manifest["capabilities"]["engines"]["io.github.stefanjdecker.erdecisions.model"]["result_cache"]="by-input"
for name in schemas:
    content["views"][name]="texstage_er_decisions/web/"+({"participant-input":"participant", "presenter-controls":"presenter-controls"}.get(name,"lesson-overlay"))+".mjs"
    content["view_schemas"][name]="texstage_er_decisions/schemas/views/"+name+".json"
content["messages"]={}
for op, kind in (("submit","submit"),("open","control"),("close","control"),("reveal","control"),
                 ("select-answer","select"),("share-answer","share"),("clear-share","control"),("set-page","page")):
    content["messages"][op]={"from":["participant" if op=="submit" else "presenter"],
        "revision_policy":"latest","schema":"texstage_er_decisions/schemas/commands/"+kind+".json"}
write(ROOT/"texstage-plugin.json",manifest)
print("Generated ER lesson schemas and provider manifest.")

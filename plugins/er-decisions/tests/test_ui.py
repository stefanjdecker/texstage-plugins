# SPDX-License-Identifier: Apache-2.0
"""The public-only preview must represent the same choices as the independent oracle."""
import itertools
import json
from pathlib import Path
import subprocess
import sys
from texstage_er_decisions import model
from texstage_er_decisions.authoring import prepare_lesson
from test_authoring import source

def test_public_preview_all_combinations_and_masking(tmp_path):
    public = prepare_lesson(source(), {}).prepared.public
    exercise = model.source(source()["exercise"])
    choices = [sorted([list(pair) for pair in zip([d["id"] for d in public["decisions"]], row)])
               for row in itertools.product(*[[o["id"] for o in d["options"]] for d in public["decisions"]])]
    module = Path(__import__("texstage_er_decisions").__file__).parent/"web/diagram.mjs"
    assert module.is_relative_to(Path(sys.prefix))
    data = tmp_path/"cases.json"
    data.write_text(json.dumps({"public":public,"choices":choices}),encoding="utf-8")
    script = tmp_path/"check.mjs"
    script.write_text('import fs from "node:fs";\n'
        'import {previewModel,constraints} from '+json.dumps(module.as_uri())+';\n'
        'const {public:item,choices}=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));\n'
        'const before=JSON.stringify(item);\n'
        'const rows=choices.map(c=>previewModel(item,c));\n'
        'if(JSON.stringify(item)!==before)throw new Error("Public input mutated");\n'
        'console.log(JSON.stringify({rows,empty:previewModel(item,[]),'
        'en:constraints(item,rows[0],"en"),de:constraints(item,rows[0],"de")}));\n',encoding="utf-8")
    results=json.loads(subprocess.check_output(["node",str(script),str(data)],text=True,encoding="utf-8"))
    assert results["empty"]==public["model"]
    assert results["rows"]==[model.compile_model(exercise,{"format":1,"choices":c}) for c in choices]
    first=results["rows"][0]["relationship"]["roles"][0]
    bound=str(first["min"])+".."+("*" if first["max"]=="many" else str(first["max"]))
    assert f"Each individual Person participates in {bound} links." in results["en"]
    assert f"Jede einzelne Entität Person nimmt an {bound} Verknüpfungen teil." in results["de"]


# SPDX-License-Identifier: Apache-2.0
"""Build a disposable bilingual accessibility fixture using the installed provider."""
import argparse,json,shutil
from pathlib import Path
from texstage.build.builder import build,BuildOptions
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True)
parser.add_argument("--language",choices=["en","de"],default="de")
args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
provider=next(p for p in discover() if p.id=="io.github.stefanjdecker.normalizationworkshop")
provider.verify()
source=out/"source";source.mkdir(exist_ok=True)
shutil.copytree(ROOT/"examples/normalization/activities",source/"activities",dirs_exist_ok=True)
items=json.loads((ROOT/"examples/normalization/lesson.activities.json").read_text(encoding="utf-8"))
items["language"]=args.language
# Empty determinants and a constant relation are an intentional part of the model.
constant={
 "format":1,"exercise":{"format":1,"id":"constant","title":{"en":"One fixed value","de":"Ein fester Wert"},
 "prompt":{"en":"A is constant. Classify this relation and explain the role of the empty key.",
            "de":"A ist konstant. Bestimmen Sie die Normalform und die Rolle des leeren Schlüssels."},
 "attributes":[{"id":"A","label":{"en":"Fixed value","de":"Fester Wert"}}],
 "fds":[{"lhs":[],"rhs":["A"]}],"task":{"mode":"classify"}},
 "worked_answer":{"mode":"classify","normal_form":"bcnf","witness":None},
 "explanation":{"en":"The empty set is a key. Every determinant of a nontrivial FD is therefore a superkey.",
                "de":"Die leere Menge ist ein Schlüssel. Damit ist jede Determinante einer nichttrivialen FD ein Superschlüssel."}}
(source/"activities/constant.json").write_text(json.dumps(constant,ensure_ascii=False,indent=2),encoding="utf-8")
items["items"].append({"id":"constant","type":provider.id+".workshop","source":"activities/constant.json"})
(source/"accessibility.activities.json").write_text(json.dumps(items,indent=2),encoding="utf-8")
language="ngerman" if args.language=="de" else "english"
tex=r"""\documentclass[aspectratio=169]{beamer}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{babel}
\usepackage{texstage}
\usepackage{texstage-normalization-workshop}
\setbeamertemplate{navigation symbols}{}
\begin{document}
""".replace(r"\usepackage{babel}",r"\usepackage["+language+r"]{babel}")
for item in items["items"]:
 tex+=r"\begin{frame}{"+("Normalisierung" if args.language=="de" else "Normalization")+r"}"+"\n"
 tex+=r"\normalizationworkshop{"+item["id"]+r"}{.96\linewidth}{.78\textheight}"+"\n"+r"\end{frame}"+"\n"
tex+=r"\end{document}"+"\n"
(source/"accessibility.tex").write_text(tex,encoding="utf-8")
profile=out/"profile";enable(profile,provider.id,provider.version,provider.payload)
result=build(source/"accessibility.tex",out/"build",BuildOptions(stage=True,key="accessibility-fixture",
 activities=source/"accessibility.activities.json",plugin_data=profile,height=540))
assert not result.problems,result.problems
record={"language":args.language,"provider_version":provider.version,"payload":provider.payload,
        "bundle":str(result.bundle),"stage_pdf":str(result.stage.pdf)}
(out/"build.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
print(json.dumps(record))

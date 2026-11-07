# SPDX-License-Identifier: Apache-2.0
"""Build a disposable installed-provider lesson with a navigation sentinel."""
import argparse, shutil, json
from pathlib import Path
from texstage.build.builder import BuildOptions, build
from texstage.plugins.policy import enable
from er_probe import installed
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--output",type=Path,required=True)
p.add_argument("--language",choices=["en","de"],default="en")
p.add_argument("--points",type=int,default=0,help="Fixed points for this disposable lesson; 0 keeps practice mode")
args=p.parse_args()
if not 0 <= args.points <= 10000:
    p.error("--points must be between 0 and 10000")
args.output=args.output.resolve()
root=Path(__file__).resolve().parents[1]
deck=args.output/"source"
shutil.copytree(root/"examples/er-decisions",deck,dirs_exist_ok=True)
source_path=deck/"activities/registrations.json"
source=json.loads(source_path.read_text(encoding="utf-8"));source["points"]=args.points
source_path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
filename="lesson-de.tex" if args.language=="de" else "lesson.tex"
path=deck/filename
text=path.read_text(encoding="utf-8").replace(r"\end{document}",
    "\\begin{frame}{Discussion}\nWhich choices enforce the requirements?\n\\end{frame}\n\\end{document}")
path.write_text(text,encoding="utf-8")
provider,_=installed();profile=args.output/"profile"
enable(profile,provider.id,provider.version,provider.payload)
result=build(path,args.output/"out",BuildOptions(stage=True,key="er-ui-test",height=720,
    activities=deck/f"lesson.{args.language}.activities.json",plugin_data=profile))
assert not result.problems,result.problems
print(result.bundle)


# SPDX-License-Identifier: Apache-2.0
"""Public preview agrees with the independent Python model in the installed wheel."""
import json
from pathlib import Path
import subprocess
import sys
from texstage_relational_lab import model
from texstage_relational_lab.authoring import prepare_lesson
from texstage.plugin_api.v1 import json_value
from test_engine import provider, probe, tiny

ROOT=Path(__file__).resolve().parents[3]

def test_public_editor_previews_cancellation_and_tree_edits(provider,tmp_path):
    cases=[]
    def add(name,exercise,answer,public=None):
        instance=next(i for i in exercise['instances'] if i['visibility']=='public')
        tree=answer.get('tree',exercise.get('baseline_tree'))
        for step in answer.get('steps',[]):tree=model.rewrite_tree(exercise,tree,step)
        relation,stats=model.evaluate_tree(exercise,tree,instance)
        public=public or {'mode':answer['mode'],'relations':exercise['relations'],'task':exercise['task'],'instance':instance,'baseline_tree':exercise.get('baseline_tree')}
        cases.append({'name':name,'item':public,'answer':answer,'expected':{'relation':relation.data(),'stats':stats}})
    for mode in ('construct','rewrite'):
        source=json.loads((ROOT/f'examples/relational/activities/{mode}.json').read_text(encoding='utf-8'))
        public=json_value(prepare_lesson(source,{}))['prepared']['public']
        add(mode,source['exercise'],source['worked_answer'],public)
    exercise=tiny()
    trees={
        'relation':[['rel','r']],
        'selection':[['rel','r'],['select',0,[['eq',['a','x'],['v',1]]]]],
        'projection':[['rel','r'],['project',0,['x']]],
        'rename':[['rel','r'],['rename',0,[['x','z']]]],
        'product':[['rel','r'],['rel','s'],['product',0,1]],
        'join':[['rel','r'],['rel','s'],['join',0,1,[['eq',['a','x'],['a','y']]]]],
        'union':[['rel','r'],['rel','t'],['union',0,1]],
        'difference':[['rel','r'],['rel','t'],['difference',0,1]],
        'empty':[['rel','r'],['select',0,[['eq',['a','x'],['v',99]]]]],
    }
    for name,tree in trees.items():add(name,exercise,{'mode':'construct','tree':tree})
    heavy=tiny(tables={'r':[[i] for i in range(12)],'s':[[i] for i in range(12)],'t':[[i] for i in range(12)]})
    add('cooperative-pairs',heavy,{'mode':'construct','tree':trees['product']})
    root=Path(model.__file__).parent
    assert root.is_relative_to(Path(sys.prefix))
    result=subprocess.run(['node',str(ROOT/'maintenance/relational_editor_probe.mjs')],input=json.dumps({'root':str(root),'cases':cases}),text=True,capture_output=True,encoding='utf-8',timeout=30)
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout);assert report['cases']==12 and report['cancellation'] and report['history'] and report['bounds']
    (tmp_path/'editor-preview.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

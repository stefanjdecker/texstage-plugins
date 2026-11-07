# SPDX-License-Identifier: Apache-2.0
"""Generate closed, bounded lesson schemas; --check verifies checked-in bytes."""
import argparse
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'plugins/transaction-activity/texstage_transaction_activity/schemas'

def obj(properties, required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}
def arr(items,maximum,minimum=0):return {'type':'array','items':items,'minItems':minimum,'maxItems':maximum}
def text(maximum=12,minimum=1):return {'type':'string','minLength':minimum,'maxLength':maximum}
def enum(*values):return {'enum':list(values)}
def integer(maximum=1_000_000_000,minimum=0):return {'type':'integer','minimum':minimum,'maximum':maximum}
def ref(name):return {'$ref':'#/$defs/'+name}
def optional(schema):return {'anyOf':[{'type':'null'},schema]}
def mapping(schema,maximum,minimum=0):return {'type':'object','additionalProperties':schema,'maxProperties':maximum,'minProperties':minimum}

def schemas():
    defs={'id':text(),'vertex':enum('T1','T2','T3'),'value':integer(1120000,-1120000),'boolean':{'type':'boolean'}}
    defs['localized']=obj({'en':text(600),'de':text(600)})
    defs['values']=mapping(ref('value'),3,1)
    defs['pair']=arr(ref('vertex'),2,2)
    defs['certificate']=obj({'kind':enum('cycle','serial'),'vertices':arr(ref('vertex'),4)})
    defs['edge']=obj({'from':ref('vertex'),'to':ref('vertex'),'witness':arr(ref('id'),2,2)})
    defs['prediction']=obj({'values':ref('values')})
    defs['diagnosis']=obj({'edges':arr(ref('edge'),6),'certificate':ref('certificate')})
    defs['repair']=obj({'order':arr(ref('id'),15,4)})
    defs['prediction_feedback']=obj({'code':enum('correct','revise'),'correct':ref('boolean'),'matched':arr(ref('id'),3),'wrong':arr(ref('id'),3)})
    defs['diagnosis_feedback']=obj({'code':enum('correct','revise'),'correct':ref('boolean'),
        'missing':arr(ref('pair'),6),'extra':arr(ref('pair'),6),'witnesses':arr(ref('pair'),6),'certificate':ref('boolean')})
    defs['repair_feedback']={'oneOf':[obj({'code':enum('unavailable'),'reason':enum('evaluation','facts','binding')}),
        obj({'code':enum('correct','revise'),'correct':ref('boolean'),'valid':{'const':True},'acyclic':ref('boolean'),
             'final':ref('values'),'certificate':ref('certificate')})]}
    defs['status']=enum('saved','pending','unavailable')
    for phase in ('prediction','diagnosis','repair'):
        props={'version':integer(),'answer':ref(phase),'status':ref('status'),'feedback':ref(phase+'_feedback')}
        defs[phase+'_view']=obj(props,['version','answer','status'])
        if phase=='repair':props=props|{'correlation':text(64,64)}
        defs[phase+'_slot']=obj(props,['version','answer','status']+(['correlation'] if phase=='repair' else ['feedback']))
    defs['actor']=obj({'epoch':integer(),'version':integer(),**{p:optional(ref(p+'_slot')) for p in ('prediction','diagnosis','repair')}})
    defs['own']=obj({'version':integer(),**{p:ref(p+'_view') for p in ('prediction','diagnosis','repair')}},['version'])
    defs['summary']=obj({'version':integer(),**{p:enum('none','saved','pending','unavailable') for p in ('prediction','diagnosis','repair')}})
    defs['trace']=obj({'values':ref('values'),'reads':mapping(ref('value'),12),'operation':optional(ref('id'))})
    defs['worked']=obj({'original':obj({'final':ref('values'),'diagnosis':ref('diagnosis')}),
        'repairs':arr(obj({'order':arr(ref('id'),15,4),'final':ref('values'),'serial_order':arr(ref('vertex'),3,2)}),3,2),
        'explanation':ref('localized')})
    defs['count']=integer(1000)
    defs['outcomes']=obj({p:obj({k:ref('count') for k in ('correct','revise','pending','unavailable')}) for p in ('prediction','diagnosis','repair')})
    defs['counts']=obj({p:obj({k:ref('count') for k in ('submitted','pending','unavailable')}) for p in ('prediction','diagnosis','repair')})
    defs['roster']=obj({'page':integer(39),'pages':integer(40,1),'total':ref('count'),
        'rows':arr(obj({'actor':text(256),'number':integer(1000,1),'summary':ref('summary')}),25)})
    defs['selected']=obj(defs['own']['properties']|{'actor':text(256)},['version','actor'])
    base={'format':{'const':1},'phase':enum('ready','predict','inspect','diagnose','repair','reveal'),
          'phase_token':integer(),'active':ref('boolean'),'paused':ref('boolean'),'cursor':integer(15),'prediction_revealed':ref('boolean')}
    extra={'trace':ref('trace'),'final':ref('values'),'worked':ref('worked'),'shared':ref('own')}
    output={'actor-value-v1.json':ref('actor'),'actor-summary-v1.json':ref('summary')}
    for surface in ('participant-input','presenter-controls','presenter-overlay','projector-overlay'):
        props=base|extra
        if surface=='participant-input':props=props|{'own':ref('own')}
        else:props=props|{'count':ref('count'),'counts':ref('counts'),'outcomes':ref('outcomes')}
        if surface=='presenter-controls':props=props|{'control_version':integer(),'roster':ref('roster'),'selected':ref('selected')}
        output[surface+'-view-v1.json']=obj(props,list(base))
    for phase in ('prediction','diagnosis','repair'):
        output['command-'+phase+'.json']=obj({'phase_token':integer(),'answer_version':integer(),'answer':ref(phase)})
    output['command-retry.json']=obj({'phase_token':integer(),'answer_version':integer()})
    control={'control_version':integer()}
    output['command-control.json']=obj(control)
    output['command-cursor.json']=obj(control|{'cursor':integer(15)})
    output['command-page.json']=obj(control|{'page':integer(39)})
    output['command-selection.json']=obj(control|{'actor':text(256,0),'record_version':integer()})
    # These definitions are finite and acyclic. Inline their exact constraints
    # to avoid repeated reference resolution for every actor projection. This
    # changes no accepted values and keeps all validation on the host/browser.
    def expand(value):
        if isinstance(value,dict):
            if '$ref' in value:
                assert set(value)=={'$ref'}
                return expand(defs[value['$ref'].split('/')[-1]])
            return {key:expand(child) for key,child in value.items()}
        if isinstance(value,list):return [expand(child) for child in value]
        return value
    results={}
    for name,schema in output.items():
        results[name]={'$schema':'https://json-schema.org/draft/2020-12/schema',**expand(schema)}
    return results

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    for name,schema in schemas().items():
        # Compact generated bytes retain the host's 32-KiB schema-resource cap.
        raw=json.dumps(schema,separators=(',',':'))+'\n';path=DEST/name
        assert len(raw.encode('utf-8'))<=32768,name
        if args.check:assert path.read_text(encoding='utf-8')==raw,'Stale schema: '+name
        else:path.write_text(raw,encoding='utf-8',newline='\n')
    print('Transaction schemas are current.' if args.check else 'Generated transaction schemas.')
if __name__=='__main__':main()

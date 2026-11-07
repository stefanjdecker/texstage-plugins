# SPDX-License-Identifier: Apache-2.0
"""Installed pair: domain independence, complete protocol and real host boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator, ValidationError
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog, discover
from texstage.plugins.contracts import validate_portable_schema
from texstage.plugins.runtime import Runtime
from texstage_transaction_activity import model, feedback, storage
from texstage_transaction_activity.authoring import TYPE, ENGINE, prepare_lesson
from texstage_transaction_activity.state import Lesson, SURFACES

ROOT=Path(__file__).resolve().parents[3]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'maintenance'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
oracle=module('check_transaction_design')
probe=module('transaction_engine_probe')
NAMES=['counter','independent','read_read','write_write','chain','blind_write']

def source(name='counter'):
    return json.loads((ROOT/f'examples/transactions/activities/{name}.lesson.json').read_text(encoding='utf-8'))
def prepared(name='counter'):
    result=json_value(prepare_lesson(source(name),{'language':'en'}))['prepared']
    result['evaluations']['analysis']['engine']=ENGINE
    return result

@pytest.fixture(scope='module',autouse=True)
def installed():
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    assert {p.id for p in discover()}=={'io.github.stefanjdecker.transactionactivity','io.github.stefanjdecker.transactionengine'}
    from texstage.plugins.contracts import resource_schema
    for p in discover():
        p.verify()
        for spec in p.manifest['capabilities'].get('content_types',{}).values():
            paths=list(spec['view_schemas'].values())+[spec['actor_records']['value_schema'],spec['actor_records']['summary_schema']]
            paths += [m['schema'] for m in spec['messages'].values()]
            for path in paths:resource_schema(p,path)

class Harness:
    def __init__(self,name='counter'):
        self.item=prepared(name);self.slots={};self.summaries={};self.lesson=Lesson();self.epoch=1;self.counter=0
        self.state=self.lesson.initial_state(self.item,self.ctx())
        self.apply({'kind':'activate'})
    def ctx(self,actor=None,role='system'):
        keys=list(self.slots);page=getattr(self,'state',{}).get('records_page',0)
        return {'item':self.item,'epoch':self.epoch,'role':role,'actor':actor,
                'records':{'actor':actor,'value':self.slots.get(actor),'number':keys.index(actor)+1 if actor in keys else len(keys)+1,'count':len(keys)},
                'record_page':{'page':page,'pages':max(1,(len(keys)+24)//25),'total':len(keys),
                               'rows':[{'actor':a,'number':keys.index(a)+1,'summary':self.summaries[a]} for a in keys[page*25:(page+1)*25]]}}
    def apply(self,event,role='system',expected=None):
        actor=event.get('actor') if role=='participant' or event['kind']=='evaluation.finished' else event.get('payload',{}).get('actor')
        before=copy.deepcopy(self.state)
        result=self.lesson.transition(self.state,event,self.ctx(actor,role))
        assert before==self.state,'Reducer mutated its input'
        if expected:
            assert result=={'refusal':expected};return []
        assert 'refusal' not in result,result
        self.state=result['state']
        for e in result['effects']:
            if e['kind']=='save-actor':self.slots[event['actor']]=e['value'];self.summaries[event['actor']]=e['summary']
        return [e for e in result['effects'] if e['kind']!='save-actor']
    def command(self,op,payload,actor='teacher',role='presenter',expected=None):
        self.counter+=1
        return self.apply({'kind':'command','operation':op,'payload':payload,'actor':actor,'request_id':f'request{self.counter:08}'},role,expected)
    def control(self,op='advance-phase',expected=None,**payload):
        return self.command(op,{'control_version':self.state['control_version'],**payload},expected=expected)
    def phase(self,phase):
        while self.state['phase']!=phase:self.control()
    def submit(self,phase,answer=None,actor='alice',expected=None,**guards):
        old=self.slots.get(actor,{}).get(phase)
        if answer is None:
            worked=self.item['private']['worked']
            answer={'values':worked['original']['final']} if phase=='prediction' else worked['original']['diagnosis'] if phase=='diagnosis' else {'order':worked['repairs'][0]['order']}
        return self.command('submit-'+phase,{'phase_token':self.state['phase_token'],'answer_version':old['version'] if old else 0,'answer':copy.deepcopy(answer),**guards},actor,'participant',expected)
    def complete(self,actor='alice',outcome=None,**changes):
        slot=self.slots[actor]['repair']
        if outcome is None:outcome={'status':'ok','data':model.analyze(self.item['public']['exercise'],slot['answer']['order'])}
        return self.apply({'kind':'evaluation.finished','actor':actor,'binding':'analysis','correlation_id':slot['correlation'],'outcome':outcome,**changes})
    def view(self,role='participant',actor='alice',surface=None):
        surface=surface or SURFACES[role][0]
        return self.lesson.view(self.state,{'role':role,'actor':actor,'surface':surface},self.ctx(actor if role=='participant' else None,role))

@pytest.mark.parametrize('name',NAMES)
def test_authoring_and_every_small_interleaving(name):
    s=source(name);ex=s['exercise'];model.validate(ex)
    programs=[[o['id'] for o in t['operations']] for t in ex['transactions']]
    for order in oracle.interleavings(programs):
        facts=model.analyze(ex,order);expected=oracle.analyze(ex,order)
        assert facts['final']==expected['final'] and facts['reads']==expected['reads']
        assert [[e['from'],e['to']] for e in facts['edges']]==expected['edges']
        assert facts['acyclic']==expected['csr']
        assert model.verify_analysis(ex,order,facts)
    for language in ('en','de'):
        made=json_value(prepare_lesson(s,{'language':language}))
        assert set(made['prepared']['public'])=={'format','exercise'}
        assert 'worked' not in made['prepared']['public']
        assert made['fragments']['exercise']!=made['fragments']['solutions']
    before=model.canonical(s);prepare_lesson(s,{});assert model.canonical(s)==before

def test_python_model_accepts_installed_engine_facts():
    requests=[probe.request(source(n)['exercise'],r) for n in NAMES for r in source(n)['worked_repairs']]
    results=probe.run(requests)
    for request,result in zip(requests,results,strict=True):
        assert not result.get('load_or_contract_error'),result
        assert model.verify_analysis(json.loads(request['seed']),json.loads(request['text'])['order'],result['outcome']['data'])

@pytest.mark.parametrize('fault',['bool','unknown','own-read','duplicate','commit','wrong-worked','duplicate-worked'])
def test_bad_sources_fail_before_tex(fault):
    s=source()
    if fault=='bool':s['exercise']['initial']['x']=True
    elif fault=='unknown':s['exercise']['transactions'][0]['operations'][0]['object']='unknown'
    elif fault=='own-read':s['exercise']['transactions'][0]['operations'][1]['value']['read']='b1'
    elif fault=='duplicate':s['exercise']['transactions'][0]['operations'][1]['id']='a1'
    elif fault=='commit':s['exercise']['transactions'][0]['operations'][-1]={'id':'a3','kind':'read','object':'x'}
    elif fault=='wrong-worked':s['worked_repairs'][0]=s['exercise']['schedule']
    else:s['worked_repairs'][1]=s['worked_repairs'][0]
    with pytest.raises((ValueError,ValidationError)):prepare_lesson(s,{})

def test_multiple_repairs_and_counterexample():
    for name in ('counter','blind_write'):
        s=source(name);original=model.analyze(s['exercise'])
        assert not original['acyclic']
        for order in s['worked_repairs']:
            facts=model.analyze(s['exercise'],order)
            assert feedback.repair(s['exercise'],{'order':order},{'status':'ok','data':facts})['correct']
        if name=='blind_write':assert any(model.analyze(s['exercise'],r)['final']==original['final'] for r in s['worked_repairs'])
    assert source()['worked_repairs'][2]!=source()['worked_repairs'][0]

@pytest.mark.parametrize('name',NAMES)
def test_full_lesson_staged_privacy_and_views(name):
    h=Harness(name);h.phase('predict');h.submit('prediction')
    assert 'feedback' not in h.view()['own']['prediction']
    assert 'own' not in h.view(actor='bob') and 'final' not in h.view('projector')
    h.phase('inspect');h.control('seek-step',cursor=len(h.item['public']['exercise']['schedule']))
    assert h.view()['own']['prediction']['feedback']['correct']
    h.control('seek-step',cursor=0);assert h.view()['own']['prediction']['feedback']['correct']
    h.phase('diagnose');h.submit('diagnosis');assert 'feedback' not in h.view()['own']['diagnosis']
    h.phase('repair');h.submit('repair');h.complete();assert 'feedback' not in h.view()['own']['repair']
    assert h.view()['own']['repair']['status']=='saved'
    h.phase('reveal');assert h.view()['own']['diagnosis']['feedback']['correct']
    assert h.view()['own']['repair']['feedback']['correct']
    provider=next(p for p in discover() if p.id.endswith('transactionactivity'))
    declaration=provider.manifest['capabilities']['content_types'][TYPE]
    for role,surfaces in SURFACES.items():
        for surface in surfaces:
            view=h.view(role,surface=surface)
            schema=json.loads(provider.resources[declaration['view_schemas'][surface]])
            validate_portable_schema(schema);Draft202012Validator(schema).validate(view)
            encoded=model.canonical(view)
            for private in ('"correlation":','"binding":','"evaluations":','"exercise_digest":'):assert private not in encoded
            if role!='presenter':assert 'alice' not in encoded

def test_witness_and_certificate_semantics_remain_private():
    h=Harness();h.phase('diagnose');answer=copy.deepcopy(h.item['private']['worked']['original']['diagnosis'])
    answer['edges'][0]['witness']=['a3','b3']
    h.submit('diagnosis',answer);assert 'feedback' not in h.view()['own']['diagnosis']
    h.phase('reveal');assert h.view()['own']['diagnosis']['feedback']['witnesses']
    facts=model.analyze(source('chain')['exercise']);good=source('chain')
    diagnosis=h.item['private']['worked']['original']['diagnosis']
    # A two-vertex cycle rotated to another start is still a valid certificate.
    diagnosis=copy.deepcopy(diagnosis);diagnosis['certificate']['vertices']=['T2','T1','T2']
    assert feedback.diagnosis(diagnosis,model.analyze(source()['exercise']))['correct']
    assert model.certificate_ok(['T1','T2','T3'],[], 'serial',['T3','T1','T2'])
    assert not model.certificate_ok(['T1','T2','T3'],[], 'serial',['T1','T2'])

def test_guards_navigation_and_peer_updates():
    h=Harness();h.phase('predict');before=h.view(actor='bob');control=h.state['control_version'];h.submit('prediction')
    assert h.view(actor='bob')==before and h.state['control_version']==control
    h.submit('prediction',answer_version=0,expected='stale-answer')
    h.submit('prediction',actor='bob')
    h.command('advance-phase',{'control_version':0},expected='stale-control')
    h.apply({'kind':'deactivate'});h.apply({'kind':'activate'})
    h.submit('prediction',expected='closed');h.control('resume-phase');h.submit('prediction')
    h.phase('inspect');h.submit('prediction',expected='closed')

@pytest.mark.parametrize('fault',['exercise','order','final','reads','trace','edges','certificate','status','binding'])
def test_misbound_or_inconsistent_facts_are_unavailable(fault):
    h=Harness();h.phase('repair');h.submit('repair');slot=h.slots['alice']['repair']
    data=model.analyze(h.item['public']['exercise'],slot['answer']['order']);out={'status':'ok','data':data}
    if fault=='exercise':data['exercise']='0'*64
    elif fault=='order':data['order']=source()['worked_repairs'][1]
    elif fault=='final':data['final']['x']+=1
    elif fault=='reads':data['reads']['a1']+=1
    elif fault=='trace':data['trace'][0]['value']+=1
    elif fault=='edges':data['edges']=[]
    elif fault=='certificate':data['serial_order']=list(reversed(data['serial_order']))
    elif fault=='status':out={'status':'timeout'}
    else:h.state['binding']='0'*64
    h.complete(outcome=out)
    assert h.view()['own']['repair']['status']=='unavailable'
    assert 'correct' not in h.view()['own']['repair']['feedback']

def test_replacement_late_completion_sharing_and_retry():
    h=Harness();h.phase('repair');old=h.submit('repair')[0]['correlation_id'];effects=h.submit('repair',{'order':source()['worked_repairs'][1]})
    assert effects[0]=={'kind':'cancel-evaluation','correlation_id':old}
    h.complete(correlation_id=old);assert h.slots['alice']['repair']['status']=='pending'
    h.phase('reveal');h.control('select-answer',actor='alice',record_version=h.slots['alice']['version'])
    h.control('share-answer',actor='alice',record_version=h.slots['alice']['version']);assert 'alice' not in model.canonical(h.view('projector'))
    h.complete(outcome={'status':'error'});assert h.view('projector')['shared']['repair']['feedback']['code']=='unavailable'
    version=h.slots['alice']['repair']['version'];h.command('retry-analysis',{'phase_token':h.state['phase_token'],'answer_version':version},'alice','participant')
    assert h.slots['alice']['repair']['version']==version
    h.complete();assert h.view()['own']['repair']['feedback']['correct']

def envelope(op,payload,request='request00001',epoch=1):
    return {'type':TYPE,'item':'counter','operation':op,'payload':payload,'epoch':epoch,'expected_revision':0,'request_id':request}

@pytest.fixture
def runtime(tmp_path):
    r=Runtime(tmp_path/'runtime.sqlite3',Catalog(discover()))
    r.ensure('session',TYPE,'counter',prepared());r.activate('session',{(TYPE,'counter')})
    yield r
    r.close()
def runtime_phase(r,target):
    while True:
        d=r.view('session',TYPE,'counter','presenter','presenter-controls')['data']
        if d['phase']==target:return d
        assert r.command('session','teacher','presenter',envelope('advance-phase',{'control_version':d['control_version']},'advance'+str(d['control_version']).zfill(8)))['accepted']

def test_real_runtime_atomicity_receipts_notifications_reset(runtime,monkeypatch):
    r=runtime;d=runtime_phase(r,'repair');r.take_changes('session');monkeypatch.setattr('texstage.plugins.runtime.MAX_PENDING',1)
    payload={'phase_token':d['phase_token'],'answer_version':0,'answer':{'order':source()['worked_repairs'][0]}}
    first=envelope('submit-repair',payload);before=r.view('session',TYPE,'counter','participant','participant-input','bob')['data']
    receipt=r.command('session','alice','participant',first);assert receipt['accepted'];assert r.command('session','alice','participant',first)==receipt
    assert r.take_changes('session')=={'alice'} and r.view('session',TYPE,'counter','participant','participant-input','bob')['data']==before
    with pytest.raises(PluginError) as err:r.command('session','bob','participant',first)
    assert err.value.code=='queue-full';assert 'own' not in r.view('session',TYPE,'counter','participant','participant-input','bob')['data']
    old=r.lease('session','evaluator',now=100)[0]
    assert r.command('session','alice','participant',envelope('submit-repair',payload|{'answer_version':1},'replace00001'))['accepted']
    assert not r.finish('session','evaluator',{k:old[k] for k in ('id','epoch','generation')}|{'outcome':{'status':'error'}},now=101)
    job=r.lease('session','evaluator',now=101)[0];runtime_phase(r,'reveal')
    outcome=probe.run([{'seed':job['binding']['seed'],'binding':job['binding'],'text':job['text']}])[0]['outcome']
    result={k:job[k] for k in ('id','epoch','generation')}|{'outcome':outcome}
    assert not r.finish('session','foreign',result,now=102)
    assert r.finish('session','evaluator',result,now=102);r.drain('session')
    assert r.view('session',TYPE,'counter','participant','participant-input','alice')['data']['own']['repair']['feedback']['correct']
    reset=envelope('_reset',{},'reset0000001');assert r.command('session','teacher','presenter',reset)['epoch']==2
    assert r.command('session','teacher','presenter',reset)['epoch']==2
    assert not r.finish('session','evaluator',result,now=103)
    assert 'own' not in r.view('session',TYPE,'counter','participant','participant-input','alice')['data']

@pytest.mark.parametrize('fault',['actor','seed','bool','role','surface'])
def test_host_authentication_and_closed_schemas(runtime,fault):
    r=runtime;payload={'control_version':0};role='presenter'
    if fault=='surface':
        with pytest.raises(PluginError):r.view('session',TYPE,'counter','participant','presenter-controls','alice')
        return
    if fault=='actor':payload['actor']='bob'
    if fault=='seed':payload['seed']='other'
    if fault=='bool':payload['control_version']=False
    if fault=='role':role='participant'
    with pytest.raises(PluginError):r.command('session','actor',role,envelope('advance-phase',payload))

def test_portable_actor_schemas_and_capacity():
    h=Harness('chain');h.phase('predict');h.submit('prediction');h.phase('diagnose');h.submit('diagnosis');h.phase('repair');h.submit('repair');h.complete()
    root=Path(model.__file__).parent/'schemas'
    for name,value in [('actor-value-v1.json',h.slots['alice']),('actor-summary-v1.json',h.summaries['alice'])]:
        schema=json.loads((root/name).read_text());validate_portable_schema(schema);Draft202012Validator(schema).validate(value)
    assert storage.size(h.slots['alice'])<=storage.VALUE_BYTES
    assert storage.size(h.summaries['alice'])<=storage.SUMMARY_BYTES
    # Real maximum admission; existing actors still replace without adding slots.
    for i in range(999):h.submit('repair',actor='synthetic'+str(i))
    h.submit('repair',actor='overflow',expected='actor-capacity');h.submit('repair',actor='alice')
    assert len(h.slots)==1000 and storage.size(h.state)<32768


def test_restart_preserves_pending_answers_and_accepts_new_evaluator(tmp_path):
    catalog=Catalog(discover());db=tmp_path/'restart.sqlite'
    r=Runtime(db,catalog)
    try:
        r.ensure('session',TYPE,'counter',prepared());r.activate('session',{(TYPE,'counter')})
        runtime_phase(r,'repair')
        v=r.view('session',TYPE,'counter','participant','participant-input','alice')
        answer={'order':source()['worked_repairs'][1]}
        payload={'phase_token':v['data']['phase_token'],'answer_version':0,'answer':answer}
        receipt=r.command('session','alice','participant',envelope('submit-repair',payload,'restart00001'))
        assert receipt['accepted'];r.lease('session','departed',now=100)
    finally:r.close()
    r=Runtime(db,catalog)
    try:
        assert r.view('session',TYPE,'counter','participant','participant-input','alice')['data']['own']['repair']['answer']==answer
        job=r.lease('session','replacement',now=221)[0]
        outcome=probe.run([{'seed':job['binding']['seed'],'binding':job['binding'],'text':job['text']}])[0]['outcome']
        assert r.finish('session','replacement',{k:job[k] for k in ('id','epoch','generation')}|{'outcome':outcome},now=222)
        r.drain('session');runtime_phase(r,'reveal')
        assert r.view('session',TYPE,'counter','participant','participant-input','alice')['data']['own']['repair']['feedback']['correct']
        public=r.public_archive('session')
        assert 'actor_records' not in public and 'alice' not in json.dumps(public)
        assert public['items'][0]['snapshot']['data']['worked']
        assert len(r.archive('session')['actor_records'])==1
    finally:r.close()


def test_largest_lesson_record_and_surface_budgets():
    h=Harness('maximum');h.phase('predict');h.submit('prediction');h.phase('diagnose')
    # Six submitted direct edges with maximum-length operation witnesses reserve
    # the full answer size, even if some are semantically wrong.
    ids=[op['id'] for t in h.item['public']['exercise']['transactions'] for op in t['operations']]
    edges=[{'from':a,'to':b,'witness':[ids[0],ids[-1]]} for a in ('T1','T2','T3') for b in ('T1','T2','T3') if a!=b]
    h.submit('diagnosis',{'edges':edges,'certificate':{'kind':'cycle','vertices':['T1','T2','T3','T1']}})
    h.phase('repair');h.submit('repair');h.complete();h.phase('reveal')
    assert storage.size(h.slots['alice'])<=storage.VALUE_BYTES
    for role,surfaces in SURFACES.items():
        for surface in surfaces:
            assert storage.size(h.view(role,surface=surface))<65536
    h.control('select-answer',actor='alice',record_version=h.slots['alice']['version'])
    h.control('share-answer',actor='alice',record_version=h.slots['alice']['version'])
    assert storage.size(h.state)<32768


def test_portable_javascript_validator_matches_role_contracts(tmp_path):
    import subprocess
    import texstage
    h=Harness();h.phase('predict');h.submit('prediction');h.phase('diagnose');h.submit('diagnosis');h.phase('repair');h.submit('repair');h.complete();h.phase('reveal')
    rows=[];root=Path(model.__file__).parent/'schemas'
    for role,surfaces in SURFACES.items():
        for surface in surfaces:
            schema=json.loads((root/(surface+'-view-v1.json')).read_text())
            value=h.view(role,surface=surface)
            rows.append({'schema':schema,'value':value,'expected':True})
            rows.append({'schema':schema,'value':value|{'unexpected_private_field':'no'},'expected':False})
            rows.append({'schema':schema,'value':value|{'cursor':True},'expected':False})
    config=tmp_path/'contracts.json';config.write_text(json.dumps({'module':(Path(texstage.__file__).parent/'web/stage/plugin-contracts.js').as_uri(),'cases':rows}))
    subprocess.run(['node',ROOT/'maintenance/check_transaction_contracts.mjs',config],check=True,capture_output=True,text=True)


def test_full_durable_queue_allows_replacement_and_isolates_competing_item(runtime):
    r=runtime;d=runtime_phase(r,'repair');answer={'order':source()['worked_repairs'][0]}
    payload={'phase_token':d['phase_token'],'answer_version':0,'answer':answer}
    for i in range(1000):
        assert r.command('session','s'+str(i),'participant',envelope('submit-repair',payload,'fullqueue'+str(i).zfill(5)))['accepted']
    replacement=r.command('session','s0','participant',envelope('submit-repair',payload|{'answer_version':1},'replace-full-queue'))
    assert replacement['accepted']
    r.ensure('session',TYPE,'other',prepared());r.activate('session',{(TYPE,'counter'),(TYPE,'other')})
    for i in range(4):
        data=r.view('session',TYPE,'other','presenter','presenter-controls')['data']
        r.command('session','teacher','presenter',envelope('advance-phase',{'control_version':data['control_version']},'othercontrol'+str(i))|{'item':'other'})
    data=r.view('session',TYPE,'other','participant','participant-input','s0')['data']
    with pytest.raises(PluginError) as refused:
        r.command('session','s0','participant',envelope('submit-repair',payload|{'phase_token':data['phase_token']},'other-full-queue')|{'item':'other'})
    assert refused.value.code=='queue-full'
    assert 'own' not in r.view('session',TYPE,'other','participant','participant-input','s0')['data']
    assert r.view('session',TYPE,'counter','participant','participant-input','s0')['data']['own']['repair']['version']==2

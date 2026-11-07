# SPDX-License-Identifier: Apache-2.0
"""Verified ER facts publish fixed points once, with the host's durable guards."""
import copy
import json
import pytest
from jsonschema import ValidationError
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog
from texstage.plugins.runtime import Runtime
from texstage_er_decisions.authoring import prepare_lesson,TYPE,ENGINE
from test_state import provider,source,envelope
from test_engine import probe


@pytest.mark.parametrize('points',[0,250,1000,10000])
def test_authoring_points_and_both_static_editions(points):
    src=source();src['points']=points
    result=json_value(prepare_lesson(src,{}))
    assert result['prepared']['public']['points']==points
    if points:
        assert all(str(points)+' points' in text for text in result['fragments'].values())


@pytest.mark.parametrize('points',[-1,10001,True,1.2,'1000',None])
def test_invalid_points_rejected(points):
    src=source();src['points']=points
    with pytest.raises(ValidationError):prepare_lesson(src,{})


def test_omission_keeps_practice_mode():
    assert json_value(prepare_lesson(source(),{}))['prepared']['public']['points']==0


@pytest.fixture
def scored(tmp_path,provider):
    src=source();src['points']=250
    spec=json_value(prepare_lesson(src,{}))['prepared'];spec['evaluations']['analysis']['engine']=ENGINE
    r=Runtime(tmp_path/'points.sqlite3',Catalog([provider]));r.ensure('session',TYPE,'registrations',spec)
    r.activate('session',{(TYPE,'registrations')})
    yield r
    r.close()


def view(r,actor='alice'):
    return r.view('session',TYPE,'registrations','participant','participant-input',actor)['data']


def control(r,op,request='control00001'):
    p=r.view('session',TYPE,'registrations','presenter','presenter-controls')
    return r.command('session','teacher','presenter',envelope(op,{} if op=='_reset' else
        {'control_version':p['data']['control_version']},request,p['epoch']))


def submit(r,actor='alice',answer=None,request='answer000001'):
    p=r.view('session',TYPE,'registrations','participant','participant-input',actor)
    message=envelope('submit',{'phase_version':p['data']['phase_version'],
        'answer_version':p['data'].get('own',{}).get('version',0),
        'choices':(answer or source()['solutions'][0]['answer'])['choices']},request,p['epoch'])
    reply=r.command('session',actor,'participant',message)
    assert reply['accepted'];r.drain('session')
    return message,reply


def evaluate(r,status=None):
    for job in r.lease('session','evaluator',now=100):
        outcome={'status':status} if status else probe.run([{'seed':job['binding']['seed'],
            'binding':job['binding'],'text':job['text']}])[0]['outcome']
        assert r.finish('session','evaluator',{k:job[k] for k in ('id','epoch','generation')}|{'outcome':outcome},now=101)
    r.drain('session')


def snapshot(r):
    return r.points.snapshot(r.points.heads('session')[0])


def test_two_correct_models_publish_once_and_reset_withdraws(scored):
    r=scored;control(r,'open')
    first,receipt=submit(r);submit(r,'bob',source()['solutions'][1]['answer']);evaluate(r)
    assert not snapshot(r)['published'] and 'points' not in view(r)['own']
    control(r,'close','control00002');control(r,'reveal','control00003')
    assert snapshot(r)['awards']=={'alice':{'credit':1000,'points':250},'bob':{'credit':1000,'points':250}}
    assert view(r)['own']['points']==250 and 'points' not in view(r,'charlie').get('own',{})
    assert r.command('session','alice','participant',first)==receipt
    assert r.command('session','teacher','presenter',envelope('reveal',{'control_version':2},'control00003'))['accepted']
    assert snapshot(r)['awards']['alice']['points']==250
    assert control(r,'open','control00004')['error']=='reset-required'
    control(r,'_reset','control00005')
    assert not snapshot(r)['awards'] and not snapshot(r)['published']
    assert 'own' not in view(r)


def test_replacement_stale_results_and_late_success(scored):
    r=scored;control(r,'open');submit(r)
    old=r.lease('session','old-owner',now=100)[0]
    wrong=copy.deepcopy(source()['counterexamples'][0]['answer'])
    submit(r,answer=wrong,request='answer000002')
    assert not r.finish('session','old-owner',{k:old[k] for k in ('id','epoch','generation')}|{'outcome':{'status':'timeout'}},now=101)
    evaluate(r);assert 'points' not in view(r)['own']
    submit(r,answer=source()['solutions'][1]['answer'],request='answer000003')
    control(r,'close','control00002');control(r,'reveal','control00003')
    assert snapshot(r)['awards']['alice']['credit'] is None
    assert 'points' not in view(r)['own']
    evaluate(r);assert view(r)['own']['points']==250


def test_wrong_and_unavailable_results_are_distinct(scored):
    r=scored;control(r,'open');submit(r,answer=source()['counterexamples'][0]['answer']);evaluate(r)
    submit(r,'bob',source()['solutions'][1]['answer']);evaluate(r,'timeout')
    control(r,'close','control00002');control(r,'reveal','control00003')
    assert view(r)['own']['points']==0
    assert view(r,'bob')['own']['status']=='unavailable' and 'points' not in view(r,'bob')['own']
    assert snapshot(r)['awards']['bob']['credit'] is None


def test_shape_valid_forged_facts_never_earn_points(scored):
    r=scored;control(r,'open');submit(r)
    job=r.lease('session','evaluator',now=100)[0]
    outcome=probe.run([{'seed':job['binding']['seed'],'binding':job['binding'],'text':job['text']}])[0]['outcome']
    outcome['data']['checks'].pop()
    assert r.finish('session','evaluator',{k:job[k] for k in ('id','epoch','generation')}|{'outcome':outcome},now=101)
    r.drain('session');control(r,'close','control00002');control(r,'reveal','control00003')
    assert view(r)['own']['status']=='unavailable' and 'points' not in view(r)['own']

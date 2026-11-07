# SPDX-License-Identifier: Apache-2.0
"""Opt-in game points from verified activity feedback, not evaluator claims."""
import pytest
from texstage.plugin_api.v1 import json_value
from texstage_query_plan.authoring import prepare_lesson
from test_authoring import source
from test_state import runtime, start_runtime, submit_runtime, finish_job, envelope, runtime_view, probe


def snapshot(r):
    return r.points.snapshot(r.points.heads('lesson')[0])


def reveal(r):
    for op, version in [('close', 1), ('reveal', 2)]:
        assert r.command('lesson', 'teacher', 'presenter',
                         envelope(op, {'control': version}, op+'request01'))['accepted']


@pytest.mark.parametrize('points', [0, 250, 10000])
def test_points_authoring(points):
    value=source(); value['points']=points
    assert json_value(prepare_lesson(value, {}))['prepared']['public']['points']==points


def test_old_source_defaults_to_practice():
    value=source(); value.pop('points', None)
    assert json_value(prepare_lesson(value, {}))['prepared']['public']['points']==0


@pytest.mark.parametrize('points', [-1, 10001, True, 1.5, '1000', None])
def test_points_authoring_rejects_invalid_values(points):
    value=source(); value['points']=points
    with pytest.raises(ValueError): prepare_lesson(value, {})


def test_verified_points_release_late_result_and_reset(runtime,monkeypatch):
    r,ctx,_=runtime
    clock=[0.0]
    monkeypatch.setattr('texstage.plugins.runtime.time.time',lambda:clock[0])
    start_runtime(r); clock[0]=30.0; submit_runtime(r)
    submit_runtime(r, actor='bob', request='bobrequest01')
    first=r.lease('lesson','presenter',now=100,limit=1)[0]
    finish_job(r,first); r.drain('lesson')
    assert snapshot(r)['awards']=={}
    assert 'points' not in runtime_view(r)['data']['own']
    reveal(r)
    assert snapshot(r)['awards']['alice']=={'credit':1000,'points':875,'answer_ms':30000}
    # The isolated reducer has no game-wide streak; the authenticated bridge
    # supplies the complete award only after the game projection is committed.
    assert 'points' not in runtime_view(r)['data']['own']
    assert 'points' not in runtime_view(r,actor='bob')['data']['own']
    late=r.lease('lesson','presenter',now=103,limit=1)[0]
    finish_job(r,late,now=104); r.drain('lesson')
    assert snapshot(r)['awards']['bob']=={'credit':1000,'points':875,'answer_ms':30000}
    assert r.command('lesson','teacher','presenter',envelope('_reset',{},'resetrequest1'))['accepted']
    assert snapshot(r)['awards']=={} and not snapshot(r)['published']
    assert 'own' not in runtime_view(r)['data']


@pytest.mark.parametrize('outcome', ['miss', 'forged', 'unavailable'])
def test_missed_or_unverified_plan_never_awards_points(runtime, outcome):
    r,ctx,_=runtime;start_runtime(r)
    answer=source()['baseline'] if outcome=='miss' else source()['worked_answer']
    assert r.command('lesson','alice','participant',envelope('submit-plan',
        {'phase':1,'version':0,'answer':answer},'submission01'))['accepted']
    job=r.lease('lesson','presenter',now=100)[0]
    result=probe.run([{'seed':job['binding']['seed'],'binding':job['binding'],'text':job['text']}])[0]['outcome']
    if outcome=='forged':result['data']['cost']+=1
    if outcome=='unavailable':result={'status':'error'}
    assert r.finish('lesson','presenter',{k:job[k] for k in ('id','epoch','generation')}|{'outcome':result},now=101)
    r.drain('lesson');reveal(r)
    award=snapshot(r)['awards']['alice']
    assert award['credit']==(0 if outcome=='miss' else None) and award['points']==0
    assert 0 <= award['answer_ms'] <= 120000
    own=runtime_view(r)['data']['own']
    assert 'points' not in own  # complete awards are projected by the game engine


@pytest.mark.parametrize('seconds',[0,3601,True,1.5,None,'120'])
def test_invalid_speed_window(seconds):
    value=source();value['time']=seconds
    with pytest.raises(ValueError):prepare_lesson(value,{})


def test_speed_window_default_and_bounds():
    for seconds in (None,1,3600):
        value=source();value.pop('time',None)
        if seconds is not None:value['time']=seconds
        assert json_value(prepare_lesson(value,{}))['prepared']['public']['time']==(seconds or 120)

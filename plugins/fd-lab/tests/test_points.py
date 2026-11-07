# SPDX-License-Identifier: Apache-2.0
"""Installed FD records and points: verified, private, replaceable and durable."""
import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog
from texstage.plugins.runtime import Runtime
from texstage_fd_lab import model
from texstage_fd_lab.authoring import prepare_lesson, TYPE, ENGINE
from test_lesson import provider, runtime, source, worked, envelope, probe


def snapshot(r):
    heads = r.points.heads('lesson')
    return r.points.snapshot(heads[0]) if heads else {'awards': {}, 'published': False}


def own(r, actor='alice'):
    return r.view('lesson', TYPE, 'closure', 'participant', 'participant-input', actor)['data']


def open_round(r, epoch=1):
    assert r.command('lesson', 'teacher', 'presenter', envelope('open', {'control': 0}, 'open'+str(epoch).zfill(8), epoch))['accepted']


def submit(r, actor='alice', version=0, answer=None, epoch=1):
    return r.command('lesson', actor, 'participant', envelope('submit',
        {'phase': 1, 'version': version, 'answer': worked() if answer is None else answer},
        'answer'+str(epoch).zfill(3)+str(version).zfill(3), epoch))



def reveal(r, epoch=1):
    return r.command('lesson', 'teacher', 'presenter', envelope('reveal', {'control': 1}, 'reveal'+str(epoch).zfill(6), epoch))


@pytest.mark.parametrize('points', [0, 100, 10000])
def test_authoring_points(points):
    value = source(); value['points'] = points
    made = json_value(prepare_lesson(value, {}))
    assert made['prepared']['public']['points'] == points
    assert ('Maximum points' in made['fragments']['exercise']) == bool(points)


def test_legacy_source_defaults_to_unscored():
    value = source(); value.pop('points', None)
    assert prepare_lesson(value, {}).prepared.public['points'] == 0


@pytest.mark.parametrize('points', [-1, 10001, True, False, 1.0, 1.5, '100', None])
def test_invalid_points(points):
    value = source(); value['points'] = points
    with pytest.raises(ValueError): prepare_lesson(value, {})


def test_release_receipts_and_reset(runtime):
    r=runtime;open_round(r)
    receipt=submit(r)
    assert receipt['accepted'] and receipt['jobs']=={} and submit(r)==receipt
    assert submit(r,actor='bob')['accepted']
    assert snapshot(r)['awards']=={} and 'points' not in own(r)['own']
    assert 'feedback' not in own(r)['own'] and 'own' not in own(r,'charlie')
    publication=reveal(r)
    assert publication['accepted'] and reveal(r)==publication
    assert snapshot(r)['awards']=={a:{'credit':1000,'points':100} for a in ('alice','bob')}
    for actor in ('alice','bob'):assert own(r,actor)['own']['points']==100
    assert r.command('lesson','teacher','presenter',envelope('open',{'control':2},'reopen000001'))['error']=='reset-required'
    for role,surface in [('projector','projector-overlay'),('presenter','presenter-controls')]:
        assert 'points' not in model.canonical(r.view('lesson',TYPE,'closure',role,surface)['data'])
    reset=envelope('_reset',{},'reset0000001')
    assert r.command('lesson','teacher','presenter',reset)['epoch']==2
    assert r.command('lesson','teacher','presenter',reset)['epoch']==2
    assert not snapshot(r)['awards'] and not snapshot(r)['published'] and 'own' not in own(r)
    open_round(r,2);assert submit(r,epoch=2)['accepted'];reveal(r,2)
    assert snapshot(r)['awards']=={'alice':{'credit':1000,'points':100}}


@pytest.mark.parametrize('mode', ['closure','practice','keys_one','keys_all','implied','refuted','different_sizes','empty_key'])
def test_each_mode_awards_only_after_reveal(tmp_path, provider, mode):
    value = source(mode); value['points'] = 250
    spec = json_value(prepare_lesson(value, {}))['prepared']
    r = Runtime(tmp_path/'runtime.sqlite3', Catalog([provider]))
    try:
        r.ensure('lesson', TYPE, 'closure', spec); r.activate('lesson', {(TYPE, 'closure')})
        open_round(r); assert submit(r, answer=spec['private']['worked']['answer'])['accepted']
        assert snapshot(r)['awards'] == {} and 'points' not in own(r)['own']
        assert ('feedback' in own(r)['own']) == (value['feedback'] == 'practice')
        reveal(r); assert own(r)['own']['points'] == 250
    finally: r.close()


def test_wrong_answers_receive_zero_without_a_browser_claim(runtime):
    r=runtime;open_round(r)
    assert submit(r,answer=worked()|{'steps':[],'closure':0})['accepted']
    assert r.lease('lesson','presenter')==[]
    reveal(r)
    assert snapshot(r)['awards']['alice']=={'credit':0,'points':0}
    assert own(r)['own']['points']==0


def test_replacement_updates_credit_atomically_and_fake_results_cannot_change_it(runtime):
    r=runtime;open_round(r);submit(r)
    assert r.db.execute('SELECT credit FROM point_credits').fetchone()[0]==1000
    assert submit(r,version=1,answer=worked()|{'steps':[],'closure':0})['accepted']
    assert r.db.execute('SELECT credit FROM point_credits').fetchone()[0]==0
    assert not r.finish('lesson','presenter',{'id':'0'*32,'generation':1,'epoch':1,'outcome':{'status':'error'}})
    reveal(r)
    assert snapshot(r)['awards']['alice']=={'credit':0,'points':0} and own(r)['own']['version']==2


def test_failed_storage_does_not_accept_an_answer_or_award_credit(runtime,monkeypatch):
    import sqlite3
    r=runtime;open_round(r)
    apply=r.points.apply
    def fail(*args,**kwargs):
        apply(*args,**kwargs)
        raise sqlite3.OperationalError('simulated disk failure')
    monkeypatch.setattr(r.points,'apply',fail)
    with pytest.raises(sqlite3.OperationalError):submit(r)
    assert 'own' not in own(r)
    assert r.db.execute('SELECT count(*) FROM point_credits').fetchone()[0]==0
    monkeypatch.setattr(r.points,'apply',apply)
    assert submit(r)['accepted'];reveal(r)
    assert own(r)['own']['points']==100


def test_failed_hook_does_not_accept_an_answer_and_retry_is_safe(runtime,monkeypatch):
    from texstage.plugins import PluginError
    r=runtime;open_round(r);call=r.workers.call
    def fail(*args,**kwargs):raise PluginError('simulated provider timeout',code='worker-timeout')
    monkeypatch.setattr(r.workers,'call',fail)
    with pytest.raises(PluginError):submit(r)
    assert r.db.execute('SELECT count(*) FROM actor_records').fetchone()[0]==0
    assert r.db.execute('SELECT count(*) FROM point_credits').fetchone()[0]==0
    monkeypatch.setattr(r.workers,'call',call)
    assert submit(r)['accepted'];reveal(r)
    assert own(r)['own']['points']==100


def test_other_actors_do_not_change_a_participants_projection(runtime):
    r=runtime;open_round(r);submit(r)
    before=own(r)
    r.take_changes('lesson')
    assert submit(r, actor='bob')['accepted']
    assert own(r)==before
    assert r.take_changes('lesson')=={'bob'}
    assert 'count' not in own(r)
    presenter=r.view('lesson',TYPE,'closure','presenter','presenter-controls')['data']
    assert presenter['count']==2 and presenter['counts']['correct']==2


def test_revealed_points_and_records_survive_runtime_restart(tmp_path, provider):
    db=tmp_path/'runtime.sqlite3';cat=Catalog([provider])
    r=Runtime(db,cat)
    spec=json_value(prepare_lesson(source(),{}))['prepared']
    r.ensure('lesson',TYPE,'closure',spec);r.activate('lesson',{(TYPE,'closure')})
    open_round(r);submit(r);reveal(r);before=snapshot(r);r.close()
    r=Runtime(db,cat)
    try:
        assert snapshot(r)==before and own(r)['own']['points']==100
        assert submit(r)['accepted']  # replay of original receipt, no new attempt
        assert snapshot(r)==before
    finally:r.close()


def test_practice_never_creates_point_ledger(tmp_path, provider):
    spec=json_value(prepare_lesson(source('practice'),{}))['prepared']
    r=Runtime(tmp_path/'runtime.sqlite3',Catalog([provider]))
    try:
        r.ensure('lesson',TYPE,'closure',spec);r.activate('lesson',{(TYPE,'closure')})
        open_round(r);submit(r,answer=spec['private']['worked']['answer']);reveal(r)
        assert not r.points.heads('lesson') and 'points' not in own(r)['own']
        assert r.command('lesson','teacher','presenter',envelope('open',{'control':2},'reopen000001'))['accepted']
    finally:r.close()

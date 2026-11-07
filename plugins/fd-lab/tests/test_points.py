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


def finish(r, job=None, outcome=None, now=102):
    job = job or r.lease('lesson', 'presenter', now=now-1, limit=1)[0]
    if outcome is None:
        outcome = probe.run([{'seed':job['binding']['seed'], 'binding':job['binding'], 'text':job['text']}])[0]['outcome']
    accepted = r.finish('lesson', 'presenter', {k: job[k] for k in ('id', 'epoch', 'generation')} | {'outcome': outcome}, now=now)
    r.drain('lesson')
    return accepted


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


def test_release_late_result_receipts_and_reset(runtime):
    r = runtime; open_round(r)
    receipt = submit(r)
    assert receipt['accepted'] and submit(r) == receipt
    assert submit(r, actor='bob')['accepted']
    assert finish(r)
    assert snapshot(r)['awards'] == {} and 'points' not in own(r)['own']
    assert 'feedback' not in own(r)['own']
    assert 'own' not in own(r, 'charlie')
    publication = reveal(r)
    assert publication['accepted'] and reveal(r) == publication
    assert snapshot(r)['awards']['alice'] == {'credit': 1000, 'points': 100}
    assert own(r)['own']['points'] == 100
    assert 'points' not in own(r, 'bob')['own']
    assert finish(r, now=104)
    assert own(r, 'bob')['own']['points'] == 100
    assert r.command('lesson', 'teacher', 'presenter', envelope('open', {'control': 2}, 'reopen000001'))['error'] == 'reset-required'
    for role, surface in [('projector','projector-overlay'), ('presenter','presenter-controls')]:
        view = r.view('lesson', TYPE, 'closure', role, surface)['data']
        assert 'points' not in model.canonical(view)
    reset = envelope('_reset', {}, 'reset0000001')
    assert r.command('lesson', 'teacher', 'presenter', reset)['epoch'] == 2
    assert r.command('lesson', 'teacher', 'presenter', reset)['epoch'] == 2
    assert not snapshot(r)['awards'] and not snapshot(r)['published']
    assert 'own' not in own(r)
    open_round(r, 2); assert submit(r, epoch=2)['accepted']; assert finish(r, now=106); reveal(r, 2)
    assert snapshot(r)['awards'] == {'alice': {'credit': 1000, 'points': 100}}


@pytest.mark.parametrize('mode', ['closure','practice','keys_one','keys_all','implied','refuted','different_sizes','empty_key'])
def test_each_mode_awards_only_after_reveal(tmp_path, provider, mode):
    value = source(mode); value['points'] = 250
    spec = json_value(prepare_lesson(value, {}))['prepared']
    spec['evaluations']['analysis']['engine'] = ENGINE
    r = Runtime(tmp_path/'runtime.sqlite3', Catalog([provider]))
    try:
        r.ensure('lesson', TYPE, 'closure', spec); r.activate('lesson', {(TYPE, 'closure')})
        open_round(r); assert submit(r, answer=spec['private']['worked']['answer'])['accepted']; finish(r)
        assert snapshot(r)['awards'] == {} and 'points' not in own(r)['own']
        assert ('feedback' in own(r)['own']) == (value['feedback'] == 'practice')
        reveal(r); assert own(r)['own']['points'] == 250
    finally: r.close()


@pytest.mark.parametrize('fault', ['incorrect','forged','unavailable'])
def test_no_award_for_wrong_or_unverified_answers(runtime, fault):
    r=runtime; open_round(r)
    answer=worked() | ({'steps':[], 'closure':0} if fault=='incorrect' else {})
    assert submit(r, answer=answer)['accepted']
    job=r.lease('lesson','presenter',now=100)[0]
    outcome=probe.run([{'seed':job['binding']['seed'], 'binding':job['binding'], 'text':job['text']}])[0]['outcome']
    if fault=='forged': outcome['data']['facts']['closure'] ^= 1
    if fault=='unavailable': outcome={'status':'timeout'}
    assert finish(r, job, outcome); reveal(r)
    award=snapshot(r)['awards']['alice']
    assert award=={'credit':0 if fault=='incorrect' else None,'points':0}
    assert ('points' in own(r)['own']) == (fault=='incorrect')


def test_replacement_clears_old_credit_and_ignores_old_result(runtime):
    r=runtime;open_round(r);submit(r);finish(r)
    assert r.db.execute('SELECT credit FROM point_credits').fetchone()[0]==1000
    assert submit(r,version=1)['accepted']
    assert r.db.execute('SELECT credit FROM point_credits').fetchone()[0] is None
    obsolete=r.lease('lesson','presenter',now=103)[0]
    assert submit(r,version=2,answer=worked()|{'steps':[],'closure':0})['accepted']
    assert not finish(r,obsolete,now=104)
    finish(r,now=106);reveal(r)
    assert snapshot(r)['awards']['alice']=={'credit':0,'points':0}
    assert own(r)['own']['version']==3


def test_other_actors_do_not_change_a_participants_projection(runtime):
    r=runtime;open_round(r);submit(r);finish(r)
    before=own(r)
    r.take_changes('lesson')
    assert submit(r, actor='bob')['accepted']; finish(r, now=104)
    assert own(r)==before
    assert r.take_changes('lesson')=={'bob'}
    assert 'count' not in own(r)
    presenter=r.view('lesson',TYPE,'closure','presenter','presenter-controls')['data']
    assert presenter['count']==2 and presenter['counts']['correct']==2


def test_revealed_points_and_records_survive_runtime_restart(tmp_path, provider):
    db=tmp_path/'runtime.sqlite3';cat=Catalog([provider])
    r=Runtime(db,cat)
    spec=json_value(prepare_lesson(source(),{}))['prepared'];spec['evaluations']['analysis']['engine']=ENGINE
    r.ensure('lesson',TYPE,'closure',spec);r.activate('lesson',{(TYPE,'closure')})
    open_round(r);submit(r);finish(r);reveal(r);before=snapshot(r);r.close()
    r=Runtime(db,cat)
    try:
        assert snapshot(r)==before and own(r)['own']['points']==100
        assert submit(r)['accepted']  # replay of original receipt, no new attempt
        assert snapshot(r)==before
    finally:r.close()


def test_practice_never_creates_point_ledger(tmp_path, provider):
    spec=json_value(prepare_lesson(source('practice'),{}))['prepared']
    spec['evaluations']['analysis']['engine']=ENGINE
    r=Runtime(tmp_path/'runtime.sqlite3',Catalog([provider]))
    try:
        r.ensure('lesson',TYPE,'closure',spec);r.activate('lesson',{(TYPE,'closure')})
        open_round(r);submit(r,answer=spec['private']['worked']['answer']);finish(r);reveal(r)
        assert not r.points.heads('lesson') and 'points' not in own(r)['own']
        assert r.command('lesson','teacher','presenter',envelope('open',{'control':2},'reopen000001'))['accepted']
    finally:r.close()

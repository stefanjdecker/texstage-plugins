# SPDX-License-Identifier: Apache-2.0
"""Installed provider, actual durable host ledger, and verified fixed awards."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog
from texstage.plugins.runtime import Runtime
from texstage_normalization_workshop.authoring import prepare_lesson, TYPE, ENGINE
from texstage_normalization_workshop.state import handle
from test_lesson import source, envelope, provider
from test_engine import probe


@pytest.fixture
def workshop(tmp_path, provider):
    runtimes = []
    def make(name="registration", points=1000):
        value=source(name);value.update(format=2,points=points)
        item=json_value(prepare_lesson(value,{}))["prepared"]
        item["evaluations"]["analysis"]["engine"]=ENGINE
        r=Runtime(tmp_path/f"points-{len(runtimes)}.sqlite3",Catalog([provider]))
        r.ensure("lesson",TYPE,"registration",item)
        r.activate("lesson",{(TYPE,"registration")})
        runtimes.append(r)
        send(r,"open")
        return r
    yield make
    for r in runtimes:r.close()


def own(r,actor="alice"):
    return r.view("lesson",TYPE,"registration",role="participant",
                  surface="participant-input",actor=actor)["data"]


def send(r,operation,**extra):
    v=r.view("lesson",TYPE,"registration",role="presenter",surface="presenter-controls")
    e=envelope(operation,{"control":v["data"]["control_version"],**extra},
               f"control-{v['epoch']}-{v['revision']:06}",v["epoch"])
    receipt=r.command("lesson","teacher","presenter",e)
    assert receipt["accepted"],receipt
    return e,receipt


def save(r,actor="alice",answer=None,request=None):
    v=r.view("lesson",TYPE,"registration",role="participant",surface="participant-input",actor=actor)
    item=json.loads(r.db.execute("SELECT spec FROM items").fetchone()[0])
    e=envelope("submit",{"phase":v["data"]["phase_version"],"version":v["data"]["answer_version"],
                         "answer":answer or item["private"]["worked"]["answer"]},
               request or f"save-{v['epoch']}-{v['data']['answer_version']:06}",v["epoch"])
    result=r.command("lesson",actor,"participant",e)
    assert result["accepted"],result
    return e,result


def finish(r,job,outcome=None,now=101):
    if outcome is None:
        outcome=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
    return r.finish("lesson","presenter",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=now)


def settle(r,now=100):
    jobs=r.lease("lesson","presenter",now=now,limit=2)
    for job in jobs:assert finish(r,job,now=now+1)
    r.drain("lesson")


def snapshot(r):
    heads=r.points.heads("lesson")
    return r.points.snapshot(heads[0]) if heads else None


def credits(r):
    return {row["actor"]:row["credit"] for row in r.db.execute("SELECT * FROM point_credits")}


@pytest.mark.parametrize("points",[0,75,1000,10000])
def test_authoring_points_and_static_notice(points):
    value=source();value.update(format=2,points=points)
    p=json_value(prepare_lesson(value,{}))
    assert p["prepared"]["public"]["points"]==points
    assert ("points for a correct answer" in p["fragments"]["exercise"]) == (points>0)
    assert p["prepared"]["private"]["seed"]==json_value(prepare_lesson(value|{"points":0},{}))["prepared"]["private"]["seed"]


@pytest.mark.parametrize("points",[-1,10001,True,False,1.0,1.5,"1000",None])
def test_invalid_points_are_rejected(points):
    value=source();value.update(format=2,points=points)
    with pytest.raises(ValueError):prepare_lesson(value,{})


def test_legacy_unscored_source_stays_practice_and_v2_requires_points():
    old=source();old["format"]=1;old.pop("points")
    assert json_value(prepare_lesson(old,{}))["prepared"]["public"]["points"]==0
    with pytest.raises(ValueError):prepare_lesson(old|{"points":1000},{})
    with pytest.raises(ValueError):prepare_lesson(old|{"format":2},{})


@pytest.mark.parametrize("name",["registration","classify","tradeoff"])
def test_latest_correct_answer_awarded_once_on_reveal(workshop,name):
    r=workshop(name,75)
    first,receipt=save(r)
    assert r.command("lesson","alice","participant",first)==receipt
    settle(r)
    assert credits(r)=={"alice":1000} and own(r)["points"] is None
    assert snapshot(r)["awards"]=={} and not snapshot(r)["published"]
    # A new save, not just a replayed receipt; the current credit replaces the old.
    second,receipt=save(r)
    assert credits(r)=={"alice":None}
    settle(r,103)
    assert credits(r)=={"alice":1000}
    assert r.command("lesson","alice","participant",second)==receipt
    assert len(r.archive("lesson")["point_credits"])==1
    send(r,"close")
    send(r,"share-analysis",handle=handle("alice"),version=2)
    assert snapshot(r)["awards"]=={} and own(r)["points"] is None
    e,reveal=send(r,"reveal")
    expected={"alice":{"credit":1000,"points":75}}
    assert snapshot(r)["awards"]==expected and own(r)["points"]==75
    assert own(r,"bob")["points"] is None
    assert r.command("lesson","teacher","presenter",e)==reveal
    r.drain("lesson")
    assert snapshot(r)["awards"]==expected
    # Ordinary navigation and a fresh Runtime process cannot accumulate an award.
    r.activate("lesson",set());r.activate("lesson",{(TYPE,"registration")})
    db=Path(r.db.execute("PRAGMA database_list").fetchone()[2])
    with_runtime=Runtime(db,r.catalog)
    try:
        assert snapshot(with_runtime)["awards"]==expected
        assert own(with_runtime)["points"]==75
    finally:with_runtime.close()


def test_pending_result_after_reveal_and_reset_cannot_farm_points(workshop):
    r=workshop()
    save(r)
    old=r.lease("lesson","presenter",now=100)[0]
    send(r,"close");send(r,"reveal")
    assert snapshot(r)["awards"]["alice"]=={"credit":None,"points":0}
    assert own(r)["points"] is None
    assert finish(r,old)
    r.drain("lesson")
    assert own(r)["points"]==1000
    assert not finish(r,old,now=102)
    assert own(r)["points"]==1000
    e=envelope("_reset",{},"reset-points-01")
    assert r.command("lesson","teacher","presenter",e)["epoch"]==2
    assert r.command("lesson","teacher","presenter",e)["epoch"]==2
    assert snapshot(r)["awards"]=={} and credits(r)=={}
    assert own(r)["points"] is None
    assert not finish(r,old,now=103)
    send(r,"open");save(r);settle(r,104);send(r,"close");send(r,"reveal")
    assert snapshot(r)["awards"]=={"alice":{"credit":1000,"points":1000}}
    assert own(r)["points"]==1000


@pytest.mark.parametrize("mode",["wrong","forged","timeout"])
def test_replacement_never_retains_an_obsolete_correct_award(workshop,mode):
    r=workshop();save(r);settle(r)
    wrong={"mode":"decompose","relations":[3,28,48]}
    save(r,answer=wrong)
    assert credits(r)=={"alice":None}
    job=r.lease("lesson","presenter",now=103)[0]
    outcome=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
    if mode=="forged":outcome["data"]["facts"]["join"]["lossless"]=True
    if mode=="timeout":outcome={"status":"timeout"}
    assert finish(r,job,outcome,104)
    r.drain("lesson");send(r,"close");send(r,"reveal")
    assert snapshot(r)["awards"]["alice"]=={"credit":0 if mode=="wrong" else None,"points":0}
    assert own(r)["points"]==(0 if mode=="wrong" else None)


def test_stale_job_and_full_queue_replacement_are_atomic(workshop,monkeypatch):
    r=workshop();monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING",1)
    save(r)
    old=r.lease("lesson","presenter",now=100)[0]
    save(r,answer={"mode":"decompose","relations":[3,28,48]})
    assert not finish(r,old)
    assert credits(r)=={"alice":None}
    settle(r,102);send(r,"close");send(r,"reveal")
    assert own(r)["points"]==0


def test_practice_creates_no_credit_or_award(workshop):
    r=workshop(points=0);save(r);settle(r);send(r,"close");send(r,"reveal")
    assert own(r)["feedback"]["accepted"] is True and own(r)["points"] is None
    assert snapshot(r) is None and credits(r)=={}


def test_1000_credit_capacity_and_replacement_at_ceiling(workshop):
    r=workshop()
    for i in range(1000):save(r,actor=f"student-{i}")
    assert len(credits(r))==1000
    save(r,actor="student-999")
    assert len(credits(r))==1000
    # Pending publication stays non-awarding, even for a full-capacity round.
    send(r,"close");send(r,"reveal")
    awards=snapshot(r)["awards"]
    assert len(awards)==1000 and all(a=={"credit":None,"points":0} for a in awards.values())
    e=envelope("_reset",{},"reset-full-01")
    assert r.command("lesson","teacher","presenter",e)["epoch"]==2
    assert credits(r)=={} and snapshot(r)["awards"]=={}



def test_pre_points_capacity_schemas_stay_frozen():
    from test_lesson import ROOT
    from texstage_normalization_workshop import model
    record=json.loads((ROOT/"docs/design/normalization-workshop-600-validation.json").read_text(encoding="utf-8"))
    schemas={k.split("texstage_normalization_workshop/")[1]:v for k,v in
             record["provider"]["source_files"].items() if "/schemas/" in k}
    assert len(schemas)==6
    for rel,digest in schemas.items():
        assert hashlib.sha256((Path(model.__file__).parent/rel).read_bytes()).hexdigest()==digest

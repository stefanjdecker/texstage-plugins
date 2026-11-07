# SPDX-License-Identifier: Apache-2.0
"""Installed Q3 state, adversarial facts, role boundaries and real host durability."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
import texstage
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.contracts import resource_schema, validate_portable_schema
from texstage.plugins.manifest import validate_json
from texstage.plugins.runtime import Runtime
from texstage.plugins.worker import Workers
from texstage_query_plan import model
from texstage_query_plan.authoring import prepare_lesson, TYPE, ENGINE
from texstage_query_plan.state import Lesson, MAX_ACTORS, MAX_VERSION, SLOT_BYTES, STATE_BYTES
from test_authoring import source
from test_engine import PROVIDER, probe, EXERCISES, maximum_exercise

ROOT = Path(__file__).resolve().parents[3]


class Snapshot(dict):
    """Test fixture keeps host records OUTSIDE the serialized shared state.

    Existing semantic assertions access answers through this test-only lookup.
    Hooks always receive plain shared dictionaries and one actor context, never
    this full fixture. Actual SQLite authorization/atomicity is tested separately.
    """
    def __init__(self, shared=(), records=None):
        super().__init__(shared)
        self.records = records if records is not None else {}
    def __getitem__(self, key):
        return self.records if key == "answers" else super().__getitem__(key)


def hook_context(state, ctx, *, actor=None, role=None):
    role = role or ctx["role"]
    rows = getattr(state, "records", {})
    own = rows.get(actor)
    result = ctx | {"records": {"actor": actor, "value": copy.deepcopy(own),
                                "number": own["number"] if own else len(rows)+1, "count": len(rows)}}
    if role == "presenter":
        ordered = sorted(rows.items(), key=lambda row: row[1]["number"])
        pages = max(1, (len(rows)+24)//25)
        page = min(state.get("records_page", 0), pages-1)
        result["record_page"] = {"page": page, "pages": pages, "total": len(rows),
            "rows": [{"actor":a,"number":r["number"],"summary":{"status":r["status"] if r["status"] in ("pending","unavailable") else r["feedback"]["code"]}}
                     for a,r in ordered[page*25:(page+1)*25]]}
    return result


def transition(state, event, ctx):
    actor = event.get("actor")
    if event.get("operation") == "select-answer":
        actor = event["payload"]["actor"]
    return Lesson().transition(dict(state), event, hook_context(state, ctx, actor=actor))


def context(name="library", value=None):
    return {"item": json_value(prepare_lesson(value or source(name), {}))["prepared"],
            "epoch": 1, "role": "participant"}


def advance(state, event, ctx):
    result = json_value(transition(state, event, ctx))
    assert "refusal" not in result, result
    records = copy.deepcopy(getattr(state, "records", {}))
    for effect in result["effects"]:
        if effect["kind"] == "save-actor":
            records[event["actor"]] = copy.deepcopy(effect["value"])
    return Snapshot(result["state"], records), result["effects"]


def command(op, payload, actor="alice", request="request00001"):
    return {"kind": "command", "operation": op, "payload": payload, "actor": actor, "request_id": request}


def control(state, ctx, op, **payload):
    return advance(state, command(op, {"control": state["control_version"], **payload}), ctx | {"role": "presenter"})[0]


def opened(name="library", value=None):
    ctx = context(name, value)
    state = Lesson().initial_state(ctx["item"], ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    return control(state, ctx, "open"), ctx


def submit(state, ctx, answer=None, actor="alice", request="request00001"):
    version = state["answers"].get(actor, {}).get("version", 0)
    return advance(state, command("submit-plan", {"phase": state["phase_version"], "version": version,
                   "answer": answer or ctx["item"]["private"]["worked"]["answer"]}, actor, request), ctx)


def complete(state, ctx, actor="alice", outcome=None, **changes):
    slot = state["answers"][actor]
    outcome = outcome or {"status": "ok", "data": model.analyze(ctx["item"]["public"]["exercise"], slot["answer"])}
    event = {"kind": "evaluation.finished", "actor": actor, "binding": "analysis",
             "correlation_id": slot["correlation"], "outcome": outcome} | changes
    return advance(state, event, ctx)[0]


def view(state, ctx, role, actor="alice"):
    return Lesson().view(dict(state), {"role": role, "actor": actor}, hook_context(state, ctx, actor=actor, role=role))


def validate_views(state, ctx):
    for role in ("presenter", "projector", "participant"):
        data = view(state, ctx, role)
        schema = resource_schema(PROVIDER, "texstage_query_plan/schemas/views/" + role + "-v1.json")
        validate_portable_schema(schema)
        validate_json(schema, data)
        assert len(model.canonical(data)) < 128 * 1024


@pytest.mark.parametrize("mode", ["best", "budget", "miss", "invalid"])
def test_acceptance_uses_verified_facts_and_release_boundary(mode):
    value = source("library")
    answer = value["worked_answer"]
    if mode in ("budget", "miss"):
        answer = value["baseline"]
    if mode == "budget":
        value["goal"] = {"kind": "budget", "max_cost": 130000}
    if mode == "invalid":
        value = source("memory")
        answer = source("library")["worked_answer"]  # final hash does not fit
    state, ctx = opened(value=value)
    with patch.object(model, "optimum", side_effect=AssertionError("No reference enumeration at runtime")):
        state, _ = submit(state, ctx, answer)
        state = complete(state, ctx)
        assert "feedback" not in view(state, ctx, "participant")["own"]
        assert "solution" not in view(state, ctx, "projector")
        assert "own" not in view(state, ctx, "participant", "bob")
        state = control(control(state, ctx, "close"), ctx, "reveal")
        feedback = view(state, ctx, "participant")["own"]["feedback"]
        assert feedback["code"] == {"best":"goal-met","budget":"goal-met","miss":"target-missed","invalid":"invalid"}[mode]
        assert feedback["correct"] == (mode in ("best", "budget"))
        if mode == "invalid":
            assert feedback["reason"] == "hash-memory" and "cost" not in feedback
        assert "solution" in view(state, ctx, "projector")
        validate_views(state, ctx)


def test_all_tied_optima_are_accepted_with_distinct_answers():
    state, ctx = opened()
    exercise = ctx["item"]["public"]["exercise"]
    optimum = ctx["item"]["private"]["reference"]
    ties = [a for a in model.candidates(exercise) if (d := model.analyze(exercise,a))["valid"] and d["cost"]==optimum["cost"]]
    assert len(ties) == 4
    for i, answer in enumerate(ties):
        state, _ = submit(state, ctx, answer, actor=str(i))
        state = complete(state, ctx, actor=str(i))
        assert state["answers"][str(i)]["feedback"]["correct"]
    assert len({s["digest"] for s in state["answers"].values()}) == 4


@pytest.mark.parametrize("fault", ["exercise","answer","model","format","cost","node","coverage","duplicate",
                                  "subset","rows","width","local","total","memory","boolean","float","extra","invalid"])
def test_shape_valid_or_malformed_forged_facts_are_unavailable(fault):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    data = model.analyze(ctx["item"]["public"]["exercise"], state["answers"]["alice"]["answer"])
    if fault in ("exercise","answer"): data[fault] = "0"*64
    if fault in ("model","format"): data[fault] = "foreign"
    if fault == "cost": data["cost"] += 1
    if fault == "node": data["nodes"][0]["node"] = 1
    if fault == "coverage": data["nodes"].pop()
    if fault == "duplicate": data["nodes"][-1] = data["nodes"][0]
    field = {"subset":"subset","rows":"rows","width":"row_bytes","local":"local_cost","total":"total_cost","memory":"hash_bytes"}.get(fault)
    if field: data["nodes"][0][field] += 1
    if fault == "boolean": data["nodes"][0]["node"] = False
    if fault == "float": data["nodes"][0]["node"] = 0.0
    if fault == "extra": data["unexpected"] = 1
    if fault == "invalid": data = {k:v for k,v in data.items() if k not in ("cost","nodes")} | {"valid":False,"reason":"hash-memory","node":4}
    state = complete(state, ctx, outcome={"status":"ok","data":data})
    slot = state["answers"]["alice"]
    assert slot["status"] == "unavailable" and "correct" not in slot["feedback"]


@pytest.mark.parametrize("fault", ["reason","node","valid"])
def test_invalid_analysis_must_also_match_independent_model(fault):
    state, ctx = opened("memory")
    state, _ = submit(state, ctx, source("library")["worked_answer"])
    facts = model.analyze(ctx["item"]["public"]["exercise"], state["answers"]["alice"]["answer"])
    assert facts["valid"] is False
    if fault=="reason":facts["reason"]="unknown-relation"
    if fault=="node":facts["node"]=0
    if fault=="valid":facts["valid"]=True
    state=complete(state,ctx,outcome={"status":"ok","data":facts})
    assert state["answers"]["alice"]["status"]=="unavailable"


@pytest.mark.parametrize("status", ["timeout","error","syntax","refused","cancelled","unexpected"])
def test_operational_failures_keep_answers_without_grade(status):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    answer=copy.deepcopy(state["answers"]["alice"]["answer"])
    state=complete(state,ctx,outcome={"status":status})
    state=control(control(state,ctx,"close"),ctx,"reveal")
    own=view(state,ctx,"participant")["own"]
    assert own["answer"]==answer and own["status"]=="unavailable"
    assert own["feedback"]=={"code":"unavailable"}
    validate_views(state,ctx)


def test_actor_versions_control_versions_navigation_and_irreversible_reveal():
    state,ctx=opened()
    stale_control=state["control_version"]
    state,_=submit(state,ctx)
    state,_=submit(state,ctx,actor="bob")  # same request, distinct actor/correlation
    assert state["answers"]["alice"]["correlation"]!=state["answers"]["bob"]["correlation"]
    late=command("submit-plan",{"phase":state["phase_version"],"version":0,"answer":source()["worked_answer"]})
    assert transition(state,late,ctx)=={"refusal":"stale-answer"}
    state=control(state,ctx,"close")
    assert transition(state,command("reveal",{"control":stale_control}),ctx|{"role":"presenter"})=={"refusal":"stale-control"}
    state=complete(state,ctx)  # closing retains accepted work
    state=control(state,ctx,"open")
    assert transition(state,late,ctx)=={"refusal":"stale-phase"}
    state,_=advance(state,{"kind":"deactivate"},ctx)
    assert state["phase"]=="closed" and not state["active"]
    assert transition(state,late,ctx)=={"refusal":"closed"}
    state,_=advance(state,{"kind":"activate"},ctx)
    assert state["phase"]=="closed"
    state=control(state,ctx,"reveal")
    assert transition(state,command("open",{"control":state["control_version"]}),ctx|{"role":"presenter"})=={"refusal":"reset-required"}
    assert "solution" in view(state,ctx,"projector")


def test_replacement_is_atomic_intent_and_stale_completions_are_ignored():
    state,ctx=opened()
    state,effects=submit(state,ctx)
    old=copy.deepcopy(state)
    state,new=submit(state,ctx,request="replace00001")
    assert new[0]=={"kind":"cancel-evaluation","correlation_id":effects[0]["correlation_id"]}
    assert new[1]["kind"]=="evaluate"
    for changes in ({"correlation_id":old["answers"]["alice"]["correlation"]},{"binding":"foreign"}):
        assert complete(state,ctx,**changes)==state
    assert advance(state, {"kind":"evaluation.finished", "actor":"bob", "binding":"analysis",
                           "correlation_id":state["answers"]["alice"]["correlation"], "outcome":{"status":"error"}}, ctx)[0] == state
    assert complete(state,ctx|{"epoch":2})==state
    done=complete(state,ctx)
    assert complete(done,ctx,outcome={"status":"timeout"})==done
    assert state["answers"]["alice"]["status"]=="pending"  # immutable input
    assert done["answers"]["alice"]["version"]==2


def test_selection_is_private_and_sharing_is_explicit_anonymous_and_versioned():
    state,ctx=opened()
    state,_=submit(state,ctx)
    state=complete(state,ctx)
    state=control(state,ctx,"select-answer",actor="alice")
    assert "selected" in view(state,ctx,"presenter") and "demonstration" not in view(state,ctx,"projector")
    assert transition(state,command("share-selected",{"control":state["control_version"]}),ctx|{"role":"presenter"})=={"refusal":"phase"}
    state=control(control(state,ctx,"close"),ctx,"share-selected")
    projection=view(state,ctx,"projector")
    assert projection["demonstration"]==source()["worked_answer"]
    assert "alice" not in model.canonical(projection) and "solution" not in projection
    assert "demonstration" not in view(state,ctx,"participant")
    state=control(state,ctx,"clear-shared")
    assert "demonstration" not in view(state,ctx,"projector")
    state=control(state,ctx,"share-selected")
    state=control(state,ctx,"open")
    assert state["shared"] is None
    state,_=submit(state,ctx,request="replacement1")
    assert state["selected"] is None and state["shared"] is None
    validate_views(state,ctx)


def test_roster_numbers_survive_canonical_persistence_and_new_actors():
    state,ctx=opened()
    state,_=submit(state,ctx,actor="zzz")
    state=Snapshot(json.loads(model.canonical(state)),json.loads(model.canonical(state.records)))
    state,_=submit(state,ctx,actor="aaa")
    state=Snapshot(json.loads(model.canonical(state)),json.loads(model.canonical(state.records)))
    state,_=submit(state,ctx,actor="zzz",request="replace00001")
    roster=view(state,ctx,"presenter")["participants"]
    assert [(r["actor"],r["number"]) for r in roster]==[("zzz",1),("aaa",2)]


def test_paginated_selection_tracks_completion_and_replacement():
    state,ctx=opened()
    for i in range(26):
        state,_=submit(state,ctx,actor=f"student{i}")
    first=view(state,ctx,"presenter")
    assert first["page"]==0 and first["pages"]==2 and len(first["participants"])==25
    state=control(state,ctx,"roster-page",page=1)
    last=view(state,ctx,"presenter")
    assert last["participants"]==[{"actor":"student25","number":26,"status":"pending"}]
    state=control(state,ctx,"select-answer",actor="student25")
    state=control(state,ctx,"roster-page",page=0)
    assert view(state,ctx,"presenter")["selected"]["actor"]=="student25"
    state=complete(state,ctx,actor="student25")
    assert view(state,ctx,"presenter")["selected"]["feedback"]["correct"]
    assert state["counts"]["pending"]==25 and state["counts"]["goal-met"]==1
    state,_=submit(state,ctx,actor="student25",request="replacement1")
    assert "selected" not in view(state,ctx,"presenter")
    assert state["counts"]["pending"]==26 and state["counts"]["goal-met"]==0
    bad=command("roster-page",{"control":state["control_version"],"page":2})
    assert transition(state,bad,ctx|{"role":"presenter"})=={"refusal":"page"}
    validate_views(state,ctx)


def test_refusals_and_counter_bounds():
    state,ctx=opened()
    bad=source()["worked_answer"]
    bad["nodes"][0]["relation"]="illegal-name"
    result=transition(state,command("submit-plan",{"phase":1,"version":0,"answer":bad}),ctx)
    assert result=={"refusal":"invalid-answer"}
    event=command("submit-plan",{"phase":True,"version":0,"answer":source()["worked_answer"]})
    assert transition(state,event,ctx)=={"refusal":"stale-phase"}
    assert transition(state,event,ctx|{"role":"presenter"})=={"refusal":"role"}
    event=command("open",{"control":1})
    assert transition(state,event,ctx)=={"refusal":"role"}
    state["control_version"]=state["phase_version"]=MAX_VERSION
    assert transition(state,command("close",{"control":MAX_VERSION}),ctx|{"role":"presenter"})=={"refusal":"reset-required"}
    state,_=advance(state,{"kind":"deactivate"},ctx)
    assert state["phase"]=="closed" and state["control_version"]==MAX_VERSION
    state["active"]=True
    state["phase"]="open";state["phase_version"]=1
    state,_=submit(state,ctx)
    state["answers"]["alice"]["version"]=MAX_VERSION
    event=command("submit-plan",{"phase":1,"version":MAX_VERSION,"answer":source()["worked_answer"]})
    assert transition(state,event,ctx)=={"refusal":"reset-required"}


def test_1000_partitioned_slots_views_effects_and_both_host_schema_validators(tmp_path):
    value=source()
    value["exercise"]=maximum_exercise()
    reference=model.optimum(value["exercise"])
    value["baseline"]=value["worked_answer"]=reference["plan"]
    value["explanation"]={"en":"🙂"*2000,"de":"🙂"*2000}
    state,ctx=opened(value=value)
    largest = max(model.candidates(value["exercise"]), key=lambda a:len(model.canonical(a)))
    actors=[f"{i:03d}"+"🙂"*84 for i in range(MAX_ACTORS)]
    largest_transition=0
    for i,actor in enumerate(actors):
        state,effects=submit(state,ctx,largest,actor=actor,request=f"request{i:06d}")
        largest_transition=max(largest_transition,len(model.canonical({"state":state,"effects":effects})))
        state=complete(state,ctx,actor=actor)
        assert len(model.canonical({actor:state["answers"][actor]}))<=SLOT_BYTES
    event=command("submit-plan",{"phase":1,"version":0,"answer":largest},actor="extra")
    assert transition(state,event,ctx)=={"refusal":"capacity"}
    state,effects=submit(state,ctx,largest,actor=actors[0],request="replacement01")
    assert len(state["answers"])==MAX_ACTORS
    state=control(state,ctx,"select-answer",actor=actors[0])
    state=control(control(state,ctx,"close"),ctx,"share-selected")
    state=control(state,ctx,"reveal")
    assert len(model.canonical(state))<STATE_BYTES
    validate_views(state,ctx)
    workers=Workers(Catalog([PROVIDER]))
    cases=[]
    try:
        for role in ("participant","presenter","projector"):
            data=workers.call(TYPE,"view",dict(state),{"role":role,"actor":actors[0]},hook_context(state,ctx,actor=actors[0],role=role))
            schema=resource_schema(PROVIDER,"texstage_query_plan/schemas/views/"+role+"-v1.json")
            cases.append({"schema":schema,"value":data})
    finally:workers.close()
    host=(Path(texstage.__file__).parent/"web/stage/plugin-contracts.js").as_uri()
    javascript="const {conforms,jsonSize}=await import(process.argv[1]);let raw='';for await(const c of process.stdin)raw+=c;for(const c of JSON.parse(raw)){if(!conforms(c.schema,c.value)||jsonSize(c.value)>128*1024)throw Error('view');c.value.leak=true;if(conforms(c.schema,c.value))throw Error('open schema');}"
    subprocess.run(["node","--input-type=module","-e",javascript,host],input=json.dumps(cases),text=True,check=True)
    record={"state_bytes":len(model.canonical(state)),"max_transition_bytes":largest_transition,
            "view_bytes":{r:len(model.canonical(view(state,ctx,r,actors[0]))) for r in ("participant","presenter","projector")},
            "slot_bytes":max(len(model.canonical({a:s})) for a,s in state["answers"].items()),"actors":MAX_ACTORS}
    (tmp_path/"state-budget.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    # A huge authenticated ID must be rejected instead of truncated or exhausting the view.
    fresh,ctx=opened(value=value)
    event=command("submit-plan",{"phase":1,"version":0,"answer":largest},actor="🙂"*256)
    assert transition(fresh,event,ctx)=={"refusal":"capacity"}


@pytest.fixture
def runtime(tmp_path):
    ctx=context()
    ctx["item"]["evaluations"]["analysis"]["engine"]=ENGINE
    path=tmp_path/"runtime.sqlite3"
    runtime=Runtime(path,Catalog([PROVIDER]))
    runtime.ensure("lesson",TYPE,"library",ctx["item"])
    runtime.activate("lesson",{(TYPE,"library")})
    yield runtime,ctx,path
    runtime.close()


def envelope(op,payload,request="request00001",epoch=1):
    return {"type":TYPE,"item":"library","operation":op,"payload":payload,"epoch":epoch,
            "expected_revision":0,"request_id":request}


def runtime_view(r,role="participant",actor="alice"):
    surface={"participant":"participant-input","presenter":"presenter-overlay","projector":"projector-overlay"}[role]
    return r.view("lesson",TYPE,"library",role,surface,actor)


def start_runtime(r):
    assert r.command("lesson","teacher","presenter",envelope("open",{"control":0}))["accepted"]


def submit_runtime(r,version=0,actor="alice",request="submission01",epoch=1,phase=1):
    return r.command("lesson",actor,"participant",envelope("submit-plan",
        {"phase":phase,"version":version,"answer":source()["worked_answer"]},request,epoch))


def finish_job(r,job,now=102):
    row=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]
    assert r.finish("lesson","presenter",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":row["outcome"]},now=now)


def test_actual_runtime_receipts_queue_replacement_multi_actor_and_reset(runtime,monkeypatch):
    r,ctx,path=runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING",1)
    start_runtime(r)
    receipt=submit_runtime(r)
    assert submit_runtime(r)==receipt
    assert submit_runtime(r,request="seconddevice")["error"]=="stale-answer"
    before=runtime_view(r)
    with pytest.raises(PluginError,match="queue is full"):
        submit_runtime(r,actor="bob",request="bobrequest01")
    assert runtime_view(r)==before
    old=r.lease("lesson","presenter",now=100)[0]
    assert submit_runtime(r,version=1,request="replacement1")["accepted"]
    assert not r.finish("lesson","presenter",{k:old[k] for k in ("id","epoch","generation")}|{"outcome":{"status":"error"}},now=101)
    new=r.lease("lesson","presenter",now=101)[0]
    finish_job(r,new)
    r.drain("lesson")
    assert "feedback" not in runtime_view(r)["data"]["own"]
    assert runtime_view(r,"presenter")["data"]["counts"]["goal-met"]==1
    # The failed queue-full save made no receipt or state: the exact request can retry.
    assert submit_runtime(r,actor="bob",request="bobrequest01")["accepted"]
    reset_job=r.lease("lesson","presenter",now=103)[0]
    assert r.command("lesson","teacher2","presenter",envelope("close",{"control":0},"teacher20001"))["error"]=="stale-control"
    reset=envelope("_reset",{},"resetrequest1")
    assert r.command("lesson","teacher","presenter",reset)["epoch"]==2
    assert not r.finish("lesson","presenter",{k:reset_job[k] for k in ("id","epoch","generation")}|{"outcome":{"status":"error"}},now=104)
    assert r.command("lesson","teacher","presenter",reset)["epoch"]==2
    assert r.command("lesson","teacher2","presenter",envelope("_reset",{},"resetrequest2"))["error"]=="stale-epoch"
    assert runtime_view(r)["data"]["phase"]=="introduce" and "own" not in runtime_view(r)["data"]
    assert submit_runtime(r,request="lateanswer01")["error"]=="stale-epoch"
    with pytest.raises(PluginError,match="role"):
        r.command("lesson","alice","participant",envelope("reveal",{"control":0},"forged000001",epoch=2))


def test_schema_valid_but_false_cost_is_rejected_by_installed_reducer(runtime):
    r,ctx,path=runtime
    start_runtime(r);submit_runtime(r)
    job=r.lease("lesson","presenter",now=100)[0]
    result=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
    result["data"]["cost"]+=1
    assert r.finish("lesson","presenter",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":result},now=101)
    r.drain("lesson")
    data=runtime_view(r,"presenter")["data"]
    assert data["counts"]["unavailable"]==1 and data["counts"]["goal-met"]==0


def test_restart_delivery_lease_loss_and_partial_reveal(runtime):
    r,ctx,path=runtime
    start_runtime(r)
    submit_runtime(r)
    submit_runtime(r,actor="bob",request="bobrequest01")
    first=r.lease("lesson","presenter",now=100,limit=1)[0]
    replacement=r.lease("lesson","presenter",now=221,limit=1)[0]
    assert first["id"]==replacement["id"] and replacement["generation"]==2
    assert not r.finish("lesson","presenter",{k:first[k] for k in ("id","epoch","generation")}|{"outcome":{"status":"error"}},now=222)
    finish_job(r,replacement,now=222)
    # Completed-but-undelivered work survives a genuine connection/worker restart.
    r.workers.close();r.db.close()
    restarted=Runtime(path,Catalog([PROVIDER]))
    r.__dict__.update(restarted.__dict__)
    r.drain("lesson")
    assert runtime_view(r,"presenter")["data"]["counts"]["goal-met"]==1
    assert r.command("lesson","teacher","presenter",envelope("close",{"control":1},"close0000001"))["accepted"]
    assert r.command("lesson","teacher","presenter",envelope("reveal",{"control":2},"reveal000001"))["accepted"]
    assert runtime_view(r,"participant","bob")["data"]["own"]["status"]=="pending"
    # Exhaust the absent evaluator's lease attempts: result is unavailable, no grade.
    for now in (300,421,542): assert r.lease("lesson","lost",now=now,limit=1)
    assert not r.lease("lesson","lost",now=663)
    r.drain("lesson")
    own=runtime_view(r,"participant","bob")["data"]["own"]
    assert own["status"]=="unavailable" and own["feedback"]=={"code":"unavailable"}
    assert runtime_view(r)["data"]["own"]["feedback"]["correct"]

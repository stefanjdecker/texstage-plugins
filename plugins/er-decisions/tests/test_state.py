# SPDX-License-Identifier: Apache-2.0
"""Installed E3 state protocol: races, binding, privacy, portable views and budgets."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog
from texstage.plugins.contracts import validate_portable_schema
from texstage.plugins.runtime import Runtime
from jsonschema import Draft202012Validator
from texstage_er_decisions import model
from texstage_er_decisions.authoring import prepare_lesson, TYPE, ENGINE
from texstage_er_decisions.state import Lesson, SLOT_BYTES, STATE_BYTES, TRANSITION_BYTES, VIEW_BYTES, size
from test_engine import probe

ROOT=Path(__file__).resolve().parents[3]
SURFACES=(("participant","participant-input"),("presenter","presenter-controls"),
          ("presenter","presenter-overlay"),("projector","projector-overlay"))


@pytest.fixture(scope="module")
def provider():
    selected,_=probe.installed()
    import texstage_er_decisions.state
    assert Path(texstage_er_decisions.state.__file__).is_relative_to(Path(sys.prefix))
    return selected


def source():
    return json.loads((ROOT/"examples/er-decisions/activities/registrations.json").read_text(encoding="utf-8"))


def ctx():
    return {"item":json_value(prepare_lesson(source(),{}))["prepared"],"epoch":1,"role":"participant","records":{}}


def command(op,payload,actor="alice",request="request00001"):
    return {"kind":"command","operation":op,"payload":payload,"actor":actor,"request_id":request}


def advance(state,event,context):
    original=copy.deepcopy(state)
    result=json_value(Lesson().transition(state,event,context))
    assert state==original, "Reducer mutated its input"
    assert "refusal" not in result,result
    context["last_transition_bytes"]=size(result)
    effects=[]
    for effect in result["effects"]:
        if effect["kind"]=="put-record": context["records"][effect["key"]]=effect["value"]
        else: effects.append(effect)
    return result["state"],effects


def opened():
    context=ctx()
    state=Lesson().initial_state(context["item"],context)
    state,_=advance(state,{"kind":"activate"},context)
    state,_=control(state,context,"open")
    return state,context


def control(state,context,op,**payload):
    return advance(state,command(op,{"control_version":state["control_version"],**payload}),
                   context|{"role":"presenter"})


def submission(state,context,actor="alice",request="request00001",rationale="",answer=None):
    answer=answer or source()["solutions"][0]["answer"]
    return command("submit",{"phase_version":state["phase_version"],
        "answer_version":context["records"].get(actor,{}).get("version",0),
        "choices":answer["choices"],"rationale":rationale},actor,request)


def submit(state,context,**kw):
    return advance(state,submission(state,context,**kw),context)


def complete(state,context,actor="alice",outcome=None,**changes):
    slot=context["records"][actor]
    if outcome is None:
        outcome={"status":"ok","data":model.analyze(json.loads(context["item"]["evaluations"]["analysis"]["seed"]),slot["answer"])}
    return advance(state,{"kind":"evaluation.finished","actor":actor,"binding":"analysis",
        "correlation_id":slot["correlation"],"outcome":outcome,**changes},context)[0]


def view(state,context,role="participant",actor="alice",surface=None):
    surface=surface or {"participant":"participant-input","presenter":"presenter-controls","projector":"projector-overlay"}[role]
    audience={"role":role,"surface":surface,"actor":actor}
    request=Lesson().record_keys(state,{"kind":"view","audience":audience},context)
    page=[]
    if isinstance(request,dict):
        bounds=request["page"]; page=sorted(context["records"])[bounds["offset"]:bounds["offset"]+bounds["limit"]]
        keys=request["keys"]+page
    else: keys=request
    limited=context|{"records":{k:context["records"][k] for k in keys if k in context["records"]},"record_page":page}
    return Lesson().view(state,audience,limited)


@pytest.mark.parametrize("index",[0,1])
def test_two_passing_models_private_until_reveal(provider,index):
    state,context=opened()
    state,effects=submit(state,context,answer=source()["solutions"][index]["answer"],rationale="My name is Alice")
    assert len(effects)==1 and effects[0]["binding"]=="analysis"
    assert "rationale" not in effects[0]["text"] and "My name" not in effects[0]["text"]
    state=complete(state,context)
    assert view(state,context,"presenter")["counts"]["correct"]==1
    assert "feedback" not in view(state,context)["own"]
    assert "own" not in view(state,context,actor="bob")
    assert "teaching" not in view(state,context,"projector")
    state,_=control(state,context,"close")
    state,_=control(state,context,"reveal")
    assert view(state,context)["own"]["feedback"]["correct"]
    for role,surface in SURFACES:
        projected=view(state,context,role,surface=surface)
        assert len(projected["teaching"]["worked"])==2
        raw=model.canonical(projected)
        for forbidden in ('"expected":','"evaluations":','"finding":','"visibility":','"exercise_digest":','duplicate-pair'):
            assert forbidden not in raw
        if role=="projector":
            assert "Alice" not in raw and "alice" not in raw and "rationale" not in raw


def test_incorrect_model_and_operational_failure_are_distinct(provider):
    state,context=opened()
    state,_=submit(state,context,answer=source()["counterexamples"][0]["answer"])
    state=complete(state,context)
    feedback=context["records"]["alice"]["feedback"]
    assert feedback["code"]=="contradiction" and feedback["failed"]>0 and not feedback["correct"]
    state,_=submit(state,context,request="replacement01")
    state=complete(state,context,outcome={"status":"timeout"})
    assert context["records"]["alice"]["feedback"]=={"code":"unavailable","detail":"evaluation"}
    assert context["records"]["alice"]["answer"]["choices"]


@pytest.mark.parametrize("fault",["exercise","answer","missing","duplicate","unexpected","classification",
                                  "admission","reason","unresolved","validity","empty","bool"])
def test_shape_valid_forged_or_incomplete_facts_never_pass(provider,fault):
    state,context=opened()
    state,_=submit(state,context)
    facts=model.analyze(json.loads(context["item"]["evaluations"]["analysis"]["seed"]),context["records"]["alice"]["answer"])
    if fault=="exercise": facts["exercise_digest"]="0"*64
    elif fault=="answer": facts["answer_digest"]="0"*64
    elif fault=="missing": facts["checks"].pop()
    elif fault=="duplicate": facts["checks"][-1]=facts["checks"][0]
    elif fault=="unexpected": facts["checks"][0]["id"]="invented"
    elif fault=="classification": facts["checks"][0]["expected"]="allow" if facts["checks"][0]["expected"]=="forbid" else "forbid"
    elif fault=="admission": facts["checks"][0]["admits"]=not facts["checks"][0]["admits"]
    elif fault=="reason": next(x for x in facts["checks"] if x["reason"])["reason"]=None
    elif fault=="unresolved": facts["unresolved"]=["invented"]
    elif fault=="validity": facts["model_valid"]=False
    elif fault=="bool": facts["format"]=True
    else: facts={}
    state=complete(state,context,outcome={"status":"ok","data":facts})
    assert context["records"]["alice"]["status"]=="unavailable"
    assert "correct" not in context["records"]["alice"]["feedback"]


def test_versions_selection_pending_reveal_and_navigation(provider):
    state,context=opened()
    stale=submission(state,context)
    state,_=submit(state,context)
    state,_=submit(state,context,actor="bob") # same request ID, distinct correlation
    assert context["records"]["alice"]["correlation"]!=context["records"]["bob"]["correlation"]
    assert Lesson().transition(state,stale,context)=={"refusal":"stale-answer"}
    state,_=control(state,context,"select-answer",actor="alice",answer_version=1)
    assert view(state,context,"presenter")["selected"]["version"]==1
    old_correlation=context["records"]["alice"]["correlation"]
    state,effects=submit(state,context,request="replacement01")
    assert effects[0]=={"kind":"cancel-evaluation","correlation_id":old_correlation}
    assert "selected" not in view(state,context,"presenter")
    assert complete(state,context,correlation_id=old_correlation)==state
    assert complete(state,context,binding="other")==state
    assert complete(state,context|{"epoch":2})==state
    state,_=control(state,context,"close")
    state,_=control(state,context,"reveal")
    assert view(state,context)["own"]["status"]=="pending" and "feedback" not in view(state,context)["own"]
    state=complete(state,context)
    assert view(state,context)["own"]["feedback"]["correct"]
    old_phase=state["phase_version"]
    state,_=control(state,context,"open")
    stale=submission(state,context); stale["payload"]["phase_version"]=old_phase
    assert Lesson().transition(state,stale,context)=={"refusal":"stale-phase"}
    assert "feedback" not in view(state,context)["own"]
    state,_=advance(state,{"kind":"deactivate"},context)
    assert Lesson().transition(state,submission(state,context),context)=={"refusal":"closed"}
    state,_=advance(state,{"kind":"activate"},context)
    assert state["count"]==2


def test_sharing_requires_version_phase_and_explicit_rationale_choice(provider):
    state,context=opened()
    state,_=submit(state,context,rationale="Alice identifying text")
    args={"actor":"alice","answer_version":1,"include_rationale":False}
    teacher=context|{"role":"presenter"}
    message=command("share-answer",{"control_version":1,**args})
    assert Lesson().transition(state,message,teacher)=={"refusal":"phase"}
    state,_=control(state,context,"close")
    state,_=control(state,context,"share-answer",**args)
    demo=view(state,context,"projector")["demonstration"]
    assert set(demo)=={"answer","model"} and "alice" not in model.canonical(demo)
    state,_=control(state,context,"share-answer",**(args|{"include_rationale":True}))
    assert view(state,context,"projector")["demonstration"]["rationale"]=="Alice identifying text"
    state,_=control(state,context,"clear-share")
    assert "demonstration" not in view(state,context,"projector")
    state,_=control(state,context,"share-answer",**args)
    state,_=control(state,context,"open")
    assert "demonstration" not in view(state,context,"projector")
    state,_=submit(state,context,request="replacement01")
    message=command("select-answer",{"control_version":state["control_version"],"actor":"alice","answer_version":1})
    assert Lesson().transition(state,message,teacher)=={"refusal":"stale-answer"}


def test_page_order_is_independent_of_json_object_insertion_order(provider):
    state,context=opened()
    state,_=submit(state,context,actor="zebra")
    state,_=submit(state,context,actor="alice")
    reordered=context|{"records":dict(reversed(list(context["records"].items())))}
    assert view(state,context,"presenter")==view(state,reordered,"presenter")


@pytest.mark.parametrize("fault",["missing","unknown","duplicate","option","rationale","surrogate","control-char"])
def test_semantic_submission_refusal_preserves_saved_answer(provider,fault):
    state,context=opened(); state,_=submit(state,context)
    event=submission(state,context,request="replacement01")
    if fault=="missing": event["payload"]["choices"].pop()
    elif fault=="unknown": event["payload"]["choices"][0][0]="unknown"
    elif fault=="duplicate": event["payload"]["choices"][1]=event["payload"]["choices"][0]
    elif fault=="option": event["payload"]["choices"][0][1]="unknown"
    elif fault=="rationale": event["payload"]["rationale"]="😀"*160
    elif fault=="surrogate": event["payload"]["rationale"]="\ud800"
    else: event["payload"]["rationale"]="bad\0text"
    original=copy.deepcopy(state)
    assert "refusal" in Lesson().transition(state,event,context)
    assert state==original and context["records"]["alice"]["version"]==1


def validate_views(provider,state,context,actor="alice"):
    caps=provider.manifest["capabilities"]["content_types"][TYPE]
    cases=[]
    for role,surface in SURFACES:
        schema=json.loads(provider.resources[caps["view_schemas"][surface]])
        validate_portable_schema(schema)
        value=view(state,context,role,actor,surface)
        Draft202012Validator(schema).validate(value)
        assert size(value)<=VIEW_BYTES
        cases += [{"schema":schema,"value":value,"expected":True},
                  {"schema":schema,"value":value|{"private":{"secret":1}},"expected":False}]
    return cases


def test_bounded_paging_state_effects_and_both_view_validators(provider,tmp_path):
    state,context=opened()
    # Valid sources with maximum-length choice IDs and escaped teaching prose.
    large=source()
    mapping={}
    for i,decision in enumerate(large["exercise"]["decisions"]):
        old=decision["id"]; decision["id"]=f"d{i}"+"d"*22
        mapping[old]=(decision["id"],{})
        for j,option in enumerate(decision["options"]):
            old_option=option["id"]; option["id"]=f"o{j}"+"o"*22
            mapping[old][1][old_option]=option["id"]
    def renamed(answer):
        return {"format":1,"choices":[[mapping[d][0],mapping[d][1][o]] for d,o in answer["choices"]]}
    large["exercise"]["worked_answers"]=[renamed(a) for a in large["exercise"]["worked_answers"]]
    for row in large["solutions"]+large["counterexamples"]:
        row["answer"]=renamed(row["answer"])
        row["explanation"]={"en":"😀"*150,"de":"😀"*150}
    context["item"]=json_value(prepare_lesson(large,{}))["prepared"]
    context["epoch"]=9007199254740991
    answer=large["solutions"][0]["answer"]
    cases=validate_views(provider,state,context)
    largest_slot=largest_transition=0
    # Long escaped rationale plus maximum authenticated actor-key length.
    rationale="😀"*106
    for index in range(600):
        actor=f"{index:03d}"+"x"*253
        note="😀"*105+f"{index:06d}"
        state,effects=submit(state,context,actor=actor,request=f"request{index:06d}",rationale=note,answer=answer)
        assert context["records"][actor]["rationale"]==note
        largest_transition=max(largest_transition,context["last_transition_bytes"])
        context["records"][actor]["version"]=999999999
        state=complete(state,context,actor=actor,outcome={"status":"error"})
        largest_slot=max(largest_slot,size({actor:context["records"][actor]}))
        largest_transition=max(largest_transition,size({"state":state,"effects":effects}))
    assert largest_slot<=SLOT_BYTES and largest_transition<=TRANSITION_BYTES and size(state)<=STATE_BYTES
    extra=submission(state,context,actor="overflow")
    assert Lesson().transition(state,extra,context)=={"refusal":"capacity"}
    actor="000"+"x"*253
    state,_=submit(state,context,actor=actor,request="replacement01",rationale=rationale,answer=answer)
    state,_=control(state,context,"select-answer",actor=actor,answer_version=1000000000)
    assert Lesson().transition(state,submission(state,context,actor=actor,answer=answer),context)=={"refusal":"reset-required"}
    state,_=control(state,context,"set-page",page=3)
    listing=view(state,context,"presenter")
    assert len(listing["participants"])==16 and listing["participants"][0]["number"]==49
    assert listing["pages"]==38 and sum(listing["counts"].values())==600
    assert all(sum(o["count"] for o in d["counts"])==600 for d in listing["options"])
    cases+=validate_views(provider,state,context,actor)
    state,_=control(state,context,"close"); state,_=control(state,context,"reveal")
    state,_=control(state,context,"share-answer",actor=actor,answer_version=1000000000,include_rationale=True)
    cases+=validate_views(provider,state,context,actor)
    import texstage
    module=(Path(texstage.__file__).parent/"web/stage/plugin-contracts.js").as_uri()
    config=tmp_path/"contracts.json"
    config.write_text(json.dumps({"module":module,"cases":cases}),encoding="utf-8")
    subprocess.run(["node",str(ROOT/"maintenance/check_er_lesson_contracts.mjs"),str(config)],check=True,capture_output=True,text=True)
    (tmp_path/"budgets.json").write_text(json.dumps({"slot_bytes":largest_slot,"state_bytes":size(state),
        "transition_bytes":largest_transition,"view_bytes":{surface:size(view(state,context,role,actor,surface)) for role,surface in SURFACES},
        "validator_cases":len(cases)},indent=2),encoding="utf-8")


@pytest.fixture
def runtime(tmp_path,provider):
    runtime=Runtime(tmp_path/"runtime.sqlite3",Catalog([provider]))
    spec=ctx()["item"]; spec["evaluations"]["analysis"]["engine"]=ENGINE
    runtime.ensure("session",TYPE,"registrations",spec)
    runtime.activate("session",{(TYPE,"registrations")})
    yield runtime
    runtime.close()


def envelope(op,payload,request="request00001",epoch=1):
    return {"type":TYPE,"item":"registrations","operation":op,"payload":payload,
            "epoch":epoch,"expected_revision":0,"request_id":request}


def test_real_runtime_receipts_queue_replacement_finish_replay_reset(runtime,monkeypatch):
    r=runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING",1)
    assert r.command("session","teacher","presenter",envelope("open",{"control_version":0}))["accepted"]
    payload={"phase_version":1,"answer_version":0,"choices":source()["solutions"][0]["answer"]["choices"],"rationale":"Private note"}
    first=envelope("submit",payload)
    receipt=r.command("session","alice","participant",first)
    assert receipt["accepted"] and r.command("session","alice","participant",first)==receipt
    with pytest.raises(PluginError,match="reused"):
        r.command("session","alice","participant",first|{"payload":payload|{"rationale":"Different"}})
    assert r.command("session","alice","participant",first|{"request_id":"seconddevice1"})["error"]=="stale-answer"
    assert r.command("session","teacher2","presenter",envelope("close",{"control_version":0}))["error"]=="stale-control"
    with pytest.raises(PluginError) as error:
        r.command("session","bob","participant",first)
    assert error.value.code=="queue-full"
    old=r.lease("session","evaluator",now=100)[0]
    replacement=envelope("submit",payload|{"answer_version":1},"replacement01")
    assert r.command("session","alice","participant",replacement)["accepted"]
    assert not r.finish("session","evaluator",{k:old[k] for k in ("id","epoch","generation")}|{"outcome":{"status":"error"}},now=101)
    job=r.lease("session","evaluator",now=101)[0]
    assert r.command("session","teacher","presenter",envelope("close",{"control_version":1},"close0000001"))["accepted"]
    assert r.command("session","teacher","presenter",envelope("reveal",{"control_version":2},"reveal000001"))["accepted"]
    outcome=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
    assert r.finish("session","evaluator",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=102)
    r.drain("session"); r.drain("session")
    for role,surface in SURFACES:
        result=r.view("session",TYPE,"registrations",role=role,surface=surface,actor="alice")
        if role=="participant": assert result["data"]["own"]["feedback"]["correct"]
        if role=="projector": assert "Private note" not in model.canonical(result)
    reset=envelope("_reset",{},"reset0000001")
    assert r.command("session","teacher","presenter",reset)["epoch"]==2
    assert r.command("session","teacher","presenter",reset)["epoch"]==2
    assert r.command("session","teacher2","presenter",reset|{"request_id":"reset0000002"})["error"]=="stale-epoch"
    assert not r.finish("session","evaluator",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=103)
    assert "own" not in r.view("session",TYPE,"registrations","participant","participant-input",actor="alice")["data"]


@pytest.mark.parametrize("mutation",["bool","extra","role","foreign-seed"])
def test_runtime_command_schema_and_role_boundary(runtime,mutation):
    payload={"control_version":0}
    role="presenter"; op="open"
    if mutation=="bool": payload["control_version"]=False
    elif mutation=="extra": payload["raw"]="<script>"
    elif mutation=="foreign-seed": payload["seed"]="replacement"
    else: role="participant"
    with pytest.raises(PluginError):
        runtime.command("session","actor",role,envelope(op,payload))


def test_restart_delivers_committed_result_once_and_preserves_receipts(tmp_path,provider):
    db=tmp_path/"restart.sqlite3"; catalog=Catalog([provider])
    spec=ctx()["item"]; spec["evaluations"]["analysis"]["engine"]=ENGINE
    r=Runtime(db,catalog)
    try:
        r.ensure("session",TYPE,"registrations",spec); r.activate("session",{(TYPE,"registrations")})
        r.command("session","teacher","presenter",envelope("open",{"control_version":0}))
        message=envelope("submit",{"phase_version":1,"answer_version":0,
            "choices":source()["solutions"][0]["answer"]["choices"]})
        receipt=r.command("session","alice","participant",message)
        job=r.lease("session","evaluator",now=100)[0]
        outcome=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
        assert r.finish("session","evaluator",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=101)
    finally:
        r.close()
    r=Runtime(db,catalog)
    try:
        r.drain("session")
        before=r.view("session",TYPE,"registrations","presenter","presenter-controls")
        assert before["data"]["counts"]["correct"]==1
        assert r.command("session","alice","participant",message)==receipt
        r.drain("session")
        assert r.view("session",TYPE,"registrations","presenter","presenter-controls")==before
    finally:
        r.close()

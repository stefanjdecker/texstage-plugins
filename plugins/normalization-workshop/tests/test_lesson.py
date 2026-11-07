# SPDX-License-Identifier: Apache-2.0
"""Installed-wheel authoring, state/privacy and actual host runtime regressions."""
import copy
import json
from pathlib import Path
import shutil
import sys

import pytest
from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import json_value
from texstage.plugins import PluginError
from texstage.plugins.catalog import Catalog, discover
from texstage.plugins.runtime import Runtime
from texstage_normalization_workshop import model, validation as v
from texstage_normalization_workshop.authoring import prepare_lesson, TYPE, ENGINE
from texstage_normalization_workshop.state import Workshop, handle, SLOT_BYTES, STATE_BYTES, MAX_ACTORS, PAGE_SIZE
from test_engine import probe

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module", autouse=True)
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}
    p, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    return p


def schema2(name):
    version = 2 if name == "views/participant-input" else 3
    return json.loads((Path(model.__file__).parent / "schemas" / (name + f"-v{version}.json")).read_text(encoding="utf-8"))


def source(name="registration"):
    return json.loads((ROOT / f"examples/normalization/activities/{name}.json").read_text(encoding="utf-8"))


def prepared(name="registration", language="en"):
    return json_value(prepare_lesson(source(name), {"language": language}))


def context(name="registration"):
    return {"item": prepared(name)["prepared"], "epoch": 1, "role": "participant", "records": {}}


def command(op, payload, actor="alice", request="request00001"):
    return {"kind": "command", "operation": op, "payload": payload, "actor": actor, "request_id": request}


def advance(state, event, ctx):
    result = json_value(Workshop().transition(state, event, ctx))
    assert "refusal" not in result, result
    state = result["state"]
    Draft202012Validator(schema2("state")).validate(state)
    for effect in result["effects"]:
        if effect["kind"] == "put-record":
            ctx["records"][effect["key"]] = copy.deepcopy(effect["value"])
    assert state["counts"]["received"] == len(ctx["records"])
    assert sum(state["counts"][k] for k in ("pending","checked","unavailable")) == len(ctx["records"])
    for effect in result["effects"]:
        if effect["kind"] != "put-record": continue
        row = effect["value"]
        assert len(v.canonical(row)) <= SLOT_BYTES
        assert (row["status"] == "pending") == (row["correlation"] is not None)
        assert (row["status"] == "checked") == (row["feedback"] is not None)
    return state, result["effects"]


def control(state, ctx, op, **extra):
    return advance(state, command(op, {"control": state["control_version"], **extra}),
                   ctx | {"role": "presenter"})[0]


def opened(name="registration"):
    ctx = context(name)
    state = Workshop().initial_state(ctx["item"], ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    return control(state, ctx, "open"), ctx


def submit(state, ctx, *, actor="alice", answer=None, version=None, request="request00001"):
    row = next((r for r in list(ctx["records"].values()) if r["handle"] == handle(actor)), None)
    return advance(state, command("submit", {"phase": state["phase_version"],
        "version": version if version is not None else row["version"] if row else 0,
        "answer": answer or ctx["item"]["private"]["worked"]["answer"]}, actor, request), ctx)


def completion(state, ctx, actor="alice", outcome=None):
    row = next(r for r in list(ctx["records"].values()) if r["handle"] == handle(actor))
    return {"kind": "evaluation.finished", "actor": actor, "binding": "analysis",
            "correlation_id": row["correlation"], "outcome": outcome or {
                "status": "ok", "data": model.analyze(ctx["item"]["private"]["seed"], row["answer"])}}


def view(state, ctx, role="participant", surface=None, actor="alice"):
    surface = surface or {"participant":"participant-input", "presenter":"presenter-controls",
                          "projector":"projector-overlay"}[role]
    audience = {"role": role, "surface": surface, "actor": actor}
    request = Workshop().record_keys(state, {"kind":"view","audience":audience}, ctx)
    keys = request if isinstance(request,list) else request["keys"]
    page = [] if isinstance(request,list) else sorted(ctx["records"])[request["page"]["offset"]:request["page"]["offset"]+request["page"]["limit"]]
    scoped = ctx | {"records": {k:ctx["records"][k] for k in set(keys+page) if k in ctx["records"]}, "record_page":page}
    result = Workshop().view(state, audience, scoped)
    Draft202012Validator(schema2("views/" + surface)).validate(result)
    assert len(v.canonical(result)) <= 128 * 1024
    return result


@pytest.mark.parametrize("name", ["registration", "classify", "tradeoff"])
def test_prepared_one_source_checked_private_and_escaped(name):
    p = prepared(name)
    public = v.canonical(p["prepared"]["public"])
    assert all(s not in public for s in ('"worked"', '"analysis"', '"evaluations"', '"explanation"'))
    assert "One worked answer" not in p["fragments"]["exercise"]
    assert "One worked answer" in p["fragments"]["solutions"]
    assert "Eine mögliche Lösung" in prepared(name, "de")["fragments"]["solutions"]
    bad = source(name)
    bad["worked_answer"] = ({"mode":"classify","normal_form":"bcnf","witness":None} if name=="classify"
                           else {"mode":"decompose","relations":[1]})
    with pytest.raises(v.InputError, match="incorrect-worked"):
        prepare_lesson(bad,{})
    hostile = source(name)
    hostile["exercise"]["title"]["en"] = r"50% & #1 \input{private}_$"
    fragment = prepare_lesson(hostile,{}).fragments["exercise"]
    assert r"50\% \& \#1 \textbackslash{}input\{private\}\_\$" in fragment


@pytest.mark.parametrize("name", ["registration", "classify", "tradeoff"])
def test_phases_views_privacy_explicit_share_and_reveal(name):
    state, ctx = opened(name)
    state, _ = submit(state, ctx)
    state, _ = advance(state, completion(state,ctx), ctx)
    state, _ = submit(state, ctx, actor="bob")
    mine = view(state,ctx)
    assert mine["status"] == "checked" and mine["feedback"] is None and mine["worked"] is None
    assert view(state,ctx,actor="charlie")["answer"] is None
    assert view(state,ctx,"projector")["shared"] == []
    ref={"handle":handle("alice"),"version":1}
    state = control(state,ctx,"select-answer",**ref)
    private = view(state,ctx,"presenter","presenter-overlay")
    assert private["selected"][0]["analysis"]["facts"] and private["worked"]
    assert view(state,ctx,"projector")["shared"] == []
    assert Workshop().transition(state,command("share-answer",{"control":state["control_version"],**ref}),
                                 ctx|{"role":"presenter"}) == {"refusal":"phase"}
    state = control(state,ctx,"close")
    state = control(state,ctx,"share-answer",**ref)
    projector = view(state,ctx,"projector")
    assert projector["shared"][0]["answer"] == mine["answer"] and projector["worked"] is None
    assert "handle" not in v.canonical(projector)
    state = control(state,ctx,"unshare")
    assert view(state,ctx,"projector")["shared"] == []
    state = control(state,ctx,"reveal")
    assert view(state,ctx)["feedback"]["accepted"] is True
    assert view(state,ctx)["worked"]["answer"] == ctx["item"]["private"]["worked"]["answer"]
    assert Workshop().transition(state,command("open",{"control":state["control_version"]}),
                                 ctx|{"role":"presenter"}) == {"refusal":"reset-required"}


def test_actor_versions_control_guards_replacement_and_navigation():
    state, ctx = opened()
    state, _ = submit(state,ctx)
    late = completion(state,ctx)
    state, _ = submit(state,ctx,actor="bob")
    result = Workshop().transition(state,command("submit",{"phase":1,"version":0,
                 "answer":source()["worked_answer"]}),ctx)
    assert result == {"refusal":"stale-answer"}
    result = Workshop().transition(state,command("close",{"control":0}),ctx|{"role":"presenter"})
    assert result == {"refusal":"stale-control"}
    result = Workshop().transition(state,command("submit",{"phase":0,"version":1,
                 "answer":source()["worked_answer"]}),ctx)
    assert result == {"refusal":"stale-phase"}
    state = control(state,ctx,"select-answer",handle=handle("alice"),version=1)
    state, effects = submit(state,ctx,request="replace00001")
    assert [e["kind"] for e in effects] == ["cancel-evaluation","put-record","evaluate"]
    assert state["selected"] == []
    before = copy.deepcopy(state)
    state, _ = advance(state,late,ctx)
    assert state == before
    state = control(state,ctx,"close")
    state, _ = advance(state,completion(state,ctx),ctx)
    assert list(ctx["records"].values())[0]["status"] == "checked"
    state = control(state,ctx,"share-answer",handle=handle("alice"),version=2)
    state = control(state,ctx,"open")
    assert state["shared"] == state["selected"] == []
    state, _ = advance(state,{"kind":"deactivate"},ctx)
    assert view(state,ctx)["answer_version"] == 2 and not state["active"]
    state, _ = advance(state,{"kind":"activate"},ctx)
    assert view(state,ctx)["answer_version"] == 2
    ctx["records"] = {}
    reset = Workshop().initial_state(ctx["item"],ctx)
    reset, _ = advance(reset,{"kind":"activate"},ctx)
    reset = control(reset,ctx,"open")
    reset, _ = submit(reset,ctx|{"epoch":2})
    assert list(ctx["records"].values())[0]["correlation"] != late["correlation_id"]
    before = copy.deepcopy(reset)
    reset, _ = advance(reset,late,ctx|{"epoch":2})
    assert reset == before


@pytest.mark.parametrize("status", ["timeout","error","syntax","refused","cancelled"])
def test_unavailable_is_not_wrong_and_retains_answer(status):
    state, ctx = opened()
    state, _ = submit(state,ctx)
    state, _ = advance(state,completion(state,ctx,outcome={"status":status}),ctx)
    own = list(ctx["records"].values())[0]
    assert own["status"] == "unavailable" and own["feedback"] is None
    assert own["answer"] == source()["worked_answer"]
    state, _ = submit(state,ctx,request="retry0000001")
    state, _ = advance(state,completion(state,ctx),ctx)
    assert list(ctx["records"].values())[0]["feedback"]["accepted"]


def test_wrong_and_forged_facts_and_alternate_valid_answer():
    state, ctx = opened()
    wrong = {"mode":"decompose","relations":[3,28,48]} # Covers FDs; loses SC association.
    state, _ = submit(state,ctx,answer=wrong)
    event = completion(state,ctx)
    forged = copy.deepcopy(event)
    forged["outcome"]["data"]["facts"]["join"]["lossless"] = True
    forged_ctx = copy.deepcopy(ctx)
    unavailable, _ = advance(state,forged,forged_ctx)
    assert list(forged_ctx["records"].values())[0]["status"] == "unavailable"
    state, _ = advance(state,event,ctx)
    f=list(ctx["records"].values())[0]["feedback"]
    assert not f["accepted"] and f["preserved"] and not f["lossless"]
    state, _ = submit(state,ctx,answer={"mode":"decompose","relations":[3,5,12,20,48]},request="alternate001")
    state, _ = advance(state,completion(state,ctx),ctx)
    assert list(ctx["records"].values())[0]["feedback"]["accepted"]
    event=completion(state,ctx) # Completed slots cannot be overwritten.
    event["outcome"]={"status":"timeout"}
    unchanged,_=advance(state,event,ctx)
    assert unchanged == state


def test_full_capacity_and_bounded_selected_analysis(monkeypatch):
    state, ctx = opened()
    for n in range(MAX_ACTORS):
        actor=f"{n:03}"+"x"*253
        state, _ = submit(state,ctx,actor=actor,request=f"request{n:06}")
        state, _ = advance(state,completion(state,ctx,actor),ctx)
    assert len(v.canonical(state)) < STATE_BYTES
    assert "xxx" not in v.canonical(state)
    assert Workshop().transition(state,command("submit",{"phase":1,"version":0,
        "answer":source()["worked_answer"]},actor="extra"),ctx) == {"refusal":"capacity"}
    actor="000"+"x"*253
    state,_=submit(state,ctx,actor=actor,request="replacement1")
    state,_=advance(state,completion(state,ctx,actor),ctx)
    state=control(state,ctx,"select-answer",handle=handle(actor),version=2)
    calls=[]
    original=model.analyze
    def count(*args,**kwargs):
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(model,"analyze",count)
    for role,surface in (("participant","participant-input"),("projector","projector-overlay"),
                         ("presenter","presenter-controls"),("presenter","presenter-overlay")):
        view(state,ctx,role,surface,actor)
    assert len(calls)==1


@pytest.fixture
def runtime(tmp_path,provider):
    r=Runtime(tmp_path/"runtime.sqlite3",Catalog([provider]))
    item=prepared()["prepared"]
    item["evaluations"]["analysis"]["engine"]=ENGINE
    r.ensure("lesson",TYPE,"registration",item)
    r.activate("lesson",{(TYPE,"registration")})
    yield r
    r.close()


def envelope(op,payload,request="request00001",epoch=1):
    return {"type":TYPE,"item":"registration","operation":op,"payload":payload,
            "epoch":epoch,"expected_revision":0,"request_id":request}


def test_real_runtime_receipts_atomic_replacement_reset_and_portable_views(runtime,monkeypatch):
    r=runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING",1)
    assert r.command("lesson","teacher","presenter",envelope("open",{"control":0}))["accepted"]
    first=envelope("submit",{"phase":1,"version":0,"answer":source()["worked_answer"]})
    receipt=r.command("lesson","alice","participant",first)
    assert receipt["accepted"] and r.command("lesson","alice","participant",first)==receipt
    with pytest.raises(PluginError, match="changed envelope"):
        r.command("lesson","alice","participant",first|{"payload":first["payload"]|{"version":1}})
    assert r.command("lesson","alice","participant",first|{"request_id":"device000001"})["error"]=="stale-answer"
    assert r.command("lesson","teacher2","presenter",envelope("close",{"control":0}))["error"]=="stale-control"
    old=r.lease("lesson","presenter",now=100)[0]
    replacement=envelope("submit",first["payload"]|{"version":1},"replace00001")
    assert r.command("lesson","alice","participant",replacement)["accepted"]
    assert not r.finish("lesson","presenter",{k:old[k] for k in ("id","epoch","generation")}|{"outcome":{"status":"error"}},now=101)
    job=r.lease("lesson","presenter",now=101)[0]
    assert r.command("lesson","teacher","presenter",envelope("close",{"control":1},"close0000001"))["accepted"]
    outcome=probe.run([{"seed":job["binding"]["seed"],"binding":job["binding"],"text":job["text"]}])[0]["outcome"]
    assert r.finish("lesson","presenter",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=102)
    r.drain("lesson")
    for role,surface in (("participant","participant-input"),("presenter","presenter-controls"),
                         ("presenter","presenter-overlay"),("projector","projector-overlay")):
        data=r.view("lesson",TYPE,"registration",role=role,surface=surface,actor="alice")["data"]
        if role=="participant":assert data["status"]=="checked" and data["feedback"] is None
        if role!="participant":assert data["counts"]["checked"]==1
    reset=envelope("_reset",{},"reset0000001")
    assert r.command("lesson","teacher","presenter",reset)["epoch"]==2
    assert r.command("lesson","teacher","presenter",reset)["epoch"]==2
    assert r.command("lesson","alice","participant",first|{"request_id":"late00000001"})["error"]=="stale-epoch"
    assert not r.finish("lesson","presenter",{k:job[k] for k in ("id","epoch","generation")}|{"outcome":outcome},now=103)


@pytest.mark.skipif(shutil.which("pdflatex") is None,reason="needs pdfLaTeX")
def test_installed_authoring_editions_exports_freshness_and_public_bundle(tmp_path,provider):
    from texstage.build.builder import BuildOptions, build
    from texstage.build.latex import compile_deck
    from texstage.build.compiler import compile_latex
    from texstage.build.pdf import Pdf
    from texstage.plugins.policy import enable
    from texstage.server.bundles import load_bundle
    from pptx import Presentation
    deck=tmp_path/"deck"
    shutil.copytree(ROOT/"examples/normalization",deck)
    catalog=Catalog([provider]);profile=tmp_path/"profile"
    enable(profile,provider.id,provider.version,provider.payload)
    options=BuildOptions(stage=True,key="normalization-test-key",activities=deck/"lesson.activities.json",
                         plugin_data=profile,height=540)
    out=tmp_path/"out"
    result=build(deck/"lesson.tex",out,options)
    assert not result.problems
    bundle=load_bundle(result.bundle,catalog=catalog)
    assert set(bundle.items[TYPE])=={"registration","classify","tradeoff"}
    public=v.canonical(bundle.deck_json)
    assert all(k not in public for k in ('"worked"','"evaluations"','"explanation"'))
    assert not list(result.bundle.rglob("*.tex")) and not list(result.bundle.rglob("*.activities.json"))
    assert bundle.file("keys.json") is None and result.static.is_file()
    assert len(Presentation(result.static).slides)==7
    def text(path):
        with Pdf(path) as pdf:return " ".join(page.text() for page in pdf)
    handout=compile_deck(deck/"lesson.tex","handout",out,plugins=catalog,preparation=options.preparation)
    assert "One worked answer" not in text(handout.pdf)
    assert "One worked answer" not in text(result.stage.pdf)
    assert "One worked answer" in text(out/"build/lesson-solutions.pdf")
    exported=options.preparation.export(deck/"lesson.tex",catalog)
    for edition in ("handout","solutions"):
        direct=compile_latex(exported[edition],output_dir=out/("direct-"+edition),passes=2)
        assert direct.returncode==0,direct.stdout[-3000:]
        assert ("One worked answer" in text(direct.pdf))==(edition=="solutions")
    path=deck/"activities/registration.json"
    path.write_text(path.read_text(encoding="utf-8")+"\n",encoding="utf-8")
    stale=compile_latex(exported["handout"],output_dir=out/"stale")
    assert stale.returncode!=0 and "Stale prepared input" in stale.log_text

# SPDX-License-Identifier: Apache-2.0
"""V2 comparison privacy and independently checked displayed counterexamples."""
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

import pytest
from texstage_normalization_workshop import model, validation as v
from texstage_normalization_workshop.state import Workshop, handle
from test_lesson import (ROOT, advance, command, completion, context, control, opened,
                         provider, submit, view)


def ready():
    state,ctx=opened()
    for actor,parts in (("alice",[3,5,28,48]),("bob",[3,5,12,20,48]),("charlie",[3,28,48])):
        state,_=submit(state,ctx,actor=actor,answer={"mode":"decompose","relations":parts})
        state,_=advance(state,completion(state,ctx,actor),ctx)
    return state,ctx


def refs(*actors):
    return [{"handle":handle(a),"version":1} for a in actors]


def test_v1_schemas_stay_frozen(provider):
    record=json.loads((ROOT/"docs/design/normalization-workshop-n3-validation.json").read_text(encoding="utf-8"))
    package=Path(model.__file__).parent
    for name,digest in record["frozen_schema_hashes"].items():
        assert hashlib.sha256((package/name).read_bytes()).hexdigest()==digest,name


def test_two_different_correct_answers_and_checked_comparison_guards(provider):
    state,ctx=ready()
    assert all(row["feedback"]["accepted"] for row in list(ctx["records"].values())[:2])
    state=control(state,ctx,"compare-answers",answers=refs("alice","bob"))
    selected=view(state,ctx,"presenter","presenter-overlay")["selected"]
    assert len(selected)==2 and selected[0]["answer"]!=selected[1]["answer"]
    assert view(state,ctx,"projector")["shared"]==[]
    for bad,code in ((refs("alice","alice"),"distinct-answers"),
                     ([refs("alice")[0],refs("bob")[0]|{"version":0}],"stale-answer")):
        result=Workshop().transition(state,command("compare-answers",{"control":state["control_version"],"answers":bad}),
                                      ctx|{"role":"presenter"})
        assert result=={"refusal":code}
    state,_=submit(state,ctx,actor="dora")
    result=Workshop().transition(state,command("compare-answers",{"control":state["control_version"],"answers":refs("alice","dora")}),
                                  ctx|{"role":"presenter"})
    assert result=={"refusal":"not-checked"}
    for op in ("share-comparison","share-analysis"):
        payload={"answers":refs("alice","bob")} if op=="share-comparison" else refs("alice")[0]
        assert Workshop().transition(state,command(op,{"control":state["control_version"],**payload}),
                                     ctx|{"role":"presenter"})=={"refusal":"phase"}


def test_explicit_checks_sharing_and_own_reveal_only(provider):
    state,ctx=ready()
    state=control(state,ctx,"close")
    state=control(state,ctx,"share-answer",**refs("alice")[0])
    assert view(state,ctx,"projector")["shared"][0]["analysis"] is None
    state=control(state,ctx,"share-analysis",**refs("charlie")[0])
    public=view(state,ctx,"projector")
    assert public["shared"][0]["analysis"]["facts"]["join"]["lossless"] is False
    assert public["worked"] is None and "handle" not in v.canonical(public)
    assert view(state,ctx)["analysis"] is view(state,ctx)["feedback"] is None
    state=control(state,ctx,"share-comparison",answers=refs("alice","bob"))
    public=view(state,ctx,"projector")
    assert len(public["shared"])==2 and all(row["analysis"] for row in public["shared"])
    assert "handle" not in v.canonical(public)
    state=control(state,ctx,"show-evidence",topic="lossless")
    assert view(state,ctx,"projector")["topic"]=="lossless"
    old=state["control_version"]-1
    assert Workshop().transition(state,command("show-evidence",{"control":old,"topic":"preservation"}),
                                 ctx|{"role":"presenter"})=={"refusal":"stale-control"}
    state=control(state,ctx,"unshare")
    assert view(state,ctx,"projector")["shared"]==[]
    state=control(state,ctx,"reveal")
    for actor in ("alice","bob","charlie"):
        personal=view(state,ctx,actor=actor)
        assert personal["analysis"]["answer"]==v.identity("normalization-answer-v1",personal["answer"])
    assert view(state,ctx,actor="outsider")["analysis"] is None


def test_references_cleared_on_replacement_reopen_reset_and_two_analysis_budget(provider,monkeypatch):
    state,ctx=ready()
    state=control(state,ctx,"compare-answers",answers=refs("alice","bob"))
    state,_=submit(state,ctx,actor="charlie",request="unrelated001")
    assert len(state["selected"])==2
    state,_=submit(state,ctx,actor="alice",request="replace00001")
    assert not state["selected"]
    state,_=advance(state,completion(state,ctx),ctx)
    pair=[{"handle":handle("alice"),"version":2},refs("bob")[0]]
    state=control(state,ctx,"compare-answers",answers=pair)
    state=control(state,ctx,"close")
    state=control(state,ctx,"share-comparison",answers=pair)
    calls=[];original=model.analyze
    def count(*args,**kwargs):
        calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(model,"analyze",count)
    for role,surface in (("presenter","presenter-overlay"),("projector","projector-overlay")):
        start=time.perf_counter();view(state,ctx,role,surface)
        assert time.perf_counter()-start<.25
    assert len(calls)==4 # Two per view, not all actors.
    state=control(state,ctx,"open")
    assert state["selected"]==state["shared"]==[] and not state["share_checks"]
    assert state["topic"]=="summary"
    reset=Workshop().initial_state(ctx["item"],ctx|{"epoch":2})
    assert reset["selected"]==reset["shared"]==[] and reset["counts"]["received"]==0


def holds(rows,left,right,n):
    columns=[j for j in range(n) if left&(1<<j)]
    col=right.bit_length()-1
    return all(not all(a[j]==b[j] for j in columns) or a[col]==b[col] for a in rows for b in rows)


def test_displayed_evidence_independently_satisfies_its_claims(provider,tmp_path):
    rng=random.Random(7342)
    cases=[]
    for name,parts in (("registration",[3,5,28,48]),("registration",[3,28,48]),("tradeoff",[5,6])):
        ctx=context(name);exercise=ctx["item"]["private"]["seed"]
        cases.append((exercise,{"mode":"decompose","relations":parts}))
    for i in range(240):
        n=1+i%8;universe=(1<<n)-1
        possible=[[x,1<<j] for x in range(universe+1) for j in range(n) if not x&(1<<j)]
        fds=sorted(rng.sample(possible,min(len(possible),i%18)))
        parts=sorted(set([universe] if n==1 else rng.sample(range(1,universe+1),min(n,universe))))
        # Ensure coverage, including genuine multiway decompositions.
        cover=0
        for part in parts:cover|=part
        if cover!=universe:parts=sorted(set(parts+[universe&~cover]))
        exercise={"format":1,"id":"e"+str(i),"attributes":[chr(65+j) for j in range(n)],"fds":fds,
                  "task":{"mode":"decompose","target":"bcnf","preserve":False}}
        cases.append((exercise,{"mode":"decompose","relations":parts}))
    rows=[{"item":{"attributes":[{"id":a} for a in ex["attributes"]],"fds":ex["fds"]},
           "answer":ans,"data":model.analyze(ex,ans)} for ex,ans in cases]
    module=(Path(model.__file__).parent/"web/evidence.mjs").as_uri()
    script=tmp_path/"evidence.mjs"
    script.write_text('import fs from "node:fs";\nimport {chaseFrames,joinWitness,lostDependency} from '+json.dumps(module)+';\n'
      'const rows=JSON.parse(fs.readFileSync(0,"utf8"));process.stdout.write(JSON.stringify(rows.map(r=>({frames:chaseFrames(r.item,r.answer,r.data),'
      'join:joinWitness(r.item,r.answer,r.data),lost:lostDependency(r.item,r.data)}))));',encoding="utf-8")
    result=subprocess.run(["node",str(script)],input=json.dumps(rows),encoding="utf-8",capture_output=True,check=True)
    evidence=json.loads(result.stdout)
    lossy=lost=0
    for (ex,ans),request,proof in zip(cases,rows,evidence,strict=True):
        n=len(ex["attributes"]);data=request["data"]
        assert proof["frames"][-1]["table"]==data["facts"]["join"]["tableau"]
        for frame,merge in zip(proof["frames"][1:],data["facts"]["join"]["merges"],strict=True):
            assert frame["merge"]["fd"]==merge[0]
        joined=proof["join"]
        assert all(holds(joined["table"],x,a,n) for x,a in ex["fds"])
        if not data["facts"]["join"]["lossless"]:
            lossy+=1
            assert joined["target"] not in joined["table"]
            for mask in ans["relations"]:
                indices=[j for j in range(n) if mask&(1<<j)]
                target=[joined["target"][j] for j in indices]
                assert target in [[row[j] for j in indices] for row in joined["table"]]
        if proof["lost"]:
            lost+=1;counter=proof["lost"];left,right=counter["dependency"]
            assert not holds(counter["rows"],left,right,n)
            theory=model.Theory(ex)
            for part in ans["relations"]:
                for determinant in range(1<<n):
                    if determinant&part!=determinant:continue
                    for j in range(n):
                        if (1<<j)&theory.closures[determinant]&part:
                            assert holds(counter["rows"],determinant,1<<j,n)
    assert lossy>15 and lost>15
    report=ROOT/'artifacts/normalization-discussion/evidence-cases.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps({'cases':len(cases),'lossy':lossy,'lost_fd':lost,'seed':7342},indent=2)+'\n',encoding='utf-8')

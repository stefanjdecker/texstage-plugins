# SPDX-License-Identifier: Apache-2.0
"""Large rosters, cross-page comparisons and transactional capacity boundaries."""
import copy
import json

from texstage_normalization_workshop.state import Workshop, handle, PAGE_SIZE
from texstage_normalization_workshop.validation import canonical
from test_lesson import (advance, command, completion, control, envelope, opened,
                         provider, runtime, source, submit, view)


def test_pages_cross_page_comparison_and_bounded_record_reads():
    state, ctx = opened()
    for i in range(40):
        actor = f"student-{i}"
        state, _ = submit(state, ctx, actor=actor)
        state, _ = advance(state, completion(state, ctx, actor), ctx)
    pages, refs = set(), []
    for page in range(3):
        state = control(state, ctx, "page", page=page)
        data = view(state, ctx, "presenter")
        assert data["pages"] == 3 and data["page"] == page
        assert len(data["answers"]) <= PAGE_SIZE
        assert len(canonical(data)) < 8192
        pages.update(row["number"] for row in data["answers"])
        refs.append({k:data["answers"][0][k] for k in ("handle","version")})
    assert pages == set(range(1,41))
    state = control(state, ctx, "compare-answers", answers=[refs[0],refs[2]])
    assert len(view(state, ctx, "presenter", "presenter-overlay")["selected"]) == 2
    assert len(view(state, ctx, "presenter")["pinned"]) == 2
    state = control(state, ctx, "close")
    state = control(state, ctx, "share-comparison", answers=[refs[0],refs[2]])
    assert len(view(state, ctx, "projector")["shared"]) == 2
    w = Workshop()
    for actor in ("student-0", "student-39", "outsider"):
        audience = {"role":"participant","surface":"participant-input","actor":actor}
        assert w.record_keys(state, {"kind":"view","audience":audience}, ctx) == [handle(actor)]
        # A forged presenter selection payload cannot expand a participant read.
        assert w.record_keys(state, command("compare-answers",{"answers":refs}),ctx) == []
        assert "counts" not in view(state,ctx,actor=actor)
    assert w.transition(state, command("page", {"control":state["control_version"],"page":3}),
                        ctx|{"role":"presenter"}) == {"refusal":"page"}


def test_actual_host_1000_records_queue_refusal_replacement_privacy_and_reset(runtime):
    r = runtime
    assert r.command("lesson","teacher","presenter",envelope("open",{"control":0}))["accepted"]
    payload = {"phase":1,"version":0,"answer":source()["worked_answer"]}
    for i in range(1000):
        assert r.command("lesson",f"student-{i}","participant",envelope("submit",payload))["accepted"]
    row = r.db.execute("SELECT state FROM items").fetchone()
    state = json.loads(row["state"])
    assert state["counts"] == {"received":1000,"pending":1000,"checked":0,"unavailable":0}
    assert len(row["state"]) < 1024
    assert r.db.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 1000
    assert r.command("lesson","overflow","participant",envelope("submit",payload))["error"] == "capacity"
    # Replacing an existing pending answer frees its job atomically even at queue capacity.
    assert r.command("lesson","student-999","participant",envelope("submit",payload|{"version":1},"replacement1000"))["accepted"]
    own = r.view("lesson",envelope("",{})["type"],"registration",role="participant",surface="participant-input",actor="student-999")["data"]
    assert own["answer_version"] == 2 and own["feedback"] is None
    other = r.view("lesson",envelope("",{})["type"],"registration",role="participant",surface="participant-input",actor="outsider")["data"]
    assert other["answer"] is None
    assert r.command("lesson","teacher","presenter",envelope("page",{"control":1,"page":62},"lastpage1000"))["accepted"]
    data = r.view("lesson",envelope("",{})["type"],"registration",role="presenter",surface="presenter-controls")["data"]
    assert data["pages"] == 63 and len(data["answers"]) == 8
    assert r.command("lesson","teacher","presenter",envelope("_reset",{},"reset1000001"))["epoch"] == 2
    assert r.db.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0
    assert json.loads(r.db.execute("SELECT state FROM items").fetchone()[0])["counts"]["received"] == 0


def test_old_schema_resources_remain_byte_identical():
    import hashlib
    from pathlib import Path
    from texstage_normalization_workshop import model
    # Historical artifact record includes every v1/v2 resource, not just active schemas.
    from test_lesson import ROOT
    hashes = {
        "schemas/analysis-result-v1.json": "1a4616042f0af3d34e024b0b38ba3f4af58b5510022578f1d5f7e9a1f28f00c0",
        "schemas/answer-v1.json": "bc37cf8e330d561629bbb7eded058524d731e59ee63a0d763afc203c6bfe54cd",
        "schemas/commands/compare-v1.json": "fddc31f5ad5f8cefb1d86bcfbd8926d3718344fd77816af7f1c2fe387835ded4",
        "schemas/commands/control-v1.json": "bfeefc4194827b393f2fffccb0e9111963f51805e076fffae5f9bb9431d3a7a9",
        "schemas/commands/select-v1.json": "7f7dfce80daa395408722d3de08803353afb8e7bbf24450cd620dee4b7204871",
        "schemas/commands/submit-v1.json": "daf15d56b3be7fc17c6d74f54043325abef5192086e4a9be29f8e42e660d2668",
        "schemas/commands/topic-v1.json": "a554d940205ee1b80dd5890f8e83846730a955418a781ba9c4448b6b5aeb7714",
        "schemas/lesson-v1.json": "42c20057546e5e3dc24120c7076fcdf546467de487daf8d36019a38bc06cbe8e",
        "schemas/seed-v1.json": "c9943dd1e58822916cbc2922f1c5a22a931025af6186b0666d19dd03473d36d1",
        "schemas/state-v1.json": "3b4997e7971bed58580f7712378438a4605007b6f894260541277cdab7583475",
        "schemas/state-v2.json": "7f731129cffb42fcbb8454342cdd520a89fa1aaff26450e8416904785fbe7e5b",
        "schemas/views/participant-input-v1.json": "bfe088b55d7253e50d4fc5f5a9beebfcf9540cf2880f5e2404d372654c391c55",
        "schemas/views/participant-input-v2.json": "f7cc42810a44860cb7c5b28fd8b1001aedaa4e61d5820b09eb633a8209f79fb3",
        "schemas/views/presenter-controls-v1.json": "96120e228b59c35a693fa369b9c1522a6f207524feef017ca96b94748e42b7de",
        "schemas/views/presenter-controls-v2.json": "6414653a2ce8900de63841fb5ced108e2f351f3fd21cefa481e79707ea479b65",
        "schemas/views/presenter-overlay-v1.json": "329d9b54696056acd3446d2fb7b8f6008bb4ce45986d71fbb5cc579e4790050f",
        "schemas/views/presenter-overlay-v2.json": "42f24f6c9a306cf6d3ef90915e8aa3ceec45900fb84aa4fb7c56107cff9b9f91",
        "schemas/views/projector-overlay-v1.json": "60eb4ed6cf32e8cb9c8b48118237005e020a4918a070dd3f3c65bc2b34ced71b",
        "schemas/views/projector-overlay-v2.json": "9f6193471c0c2abc9664f26cac12681861dd185d21d214eb8d284ae865cff82b"
    }
    for name, digest in hashes.items():
        assert hashlib.sha256((Path(model.__file__).parent/name).read_bytes()).hexdigest() == digest, name


def test_independent_verifier_cache_is_bounded_and_never_trusts_supplied_facts(monkeypatch):
    from texstage_normalization_workshop import model
    from test_lesson import context
    ctx = context()
    exercise, submitted = ctx["item"]["private"]["seed"], source()["worked_answer"]
    expected = model.analyze(exercise, submitted)
    model._expected_analysis.cache_clear()
    calls = []
    analyze = model.analyze
    def counted(*args, **kwargs):
        calls.append(1)
        return analyze(*args, **kwargs)
    monkeypatch.setattr(model, "analyze", counted)
    assert model.verify_analysis(exercise, submitted, expected)
    forged = copy.deepcopy(expected)
    forged["facts"]["join"]["lossless"] = not forged["facts"]["join"]["lossless"]
    assert not model.verify_analysis(exercise, submitted, forged)
    assert model.verify_analysis(copy.deepcopy(exercise),copy.deepcopy(submitted),expected)
    assert len(calls) == 1
    changed = exercise | {"id":"another"}
    assert not model.verify_analysis(changed,submitted,expected)
    assert len(calls) == 2
    # A caller-supplied budget bypasses the cache and remains enforced.
    from texstage_normalization_workshop.validation import ResourceLimit
    import pytest
    with pytest.raises(ResourceLimit):
        model.verify_analysis(exercise, submitted, expected, model.Budget(0))
    for i in range(70):
        e = exercise | {"id":f"bounded{i}"}
        assert model.verify_analysis(e,submitted,analyze(e,submitted))
    assert model._expected_analysis.cache_info().currsize == 64

# SPDX-License-Identifier: Apache-2.0
"""Installed closure lesson: authoring, facts, races, privacy and real exports."""
import copy
import json
from pathlib import Path
import shutil
import sys

import pytest
from texstage.plugin_api.v1 import json_value
from texstage.plugins.catalog import Catalog, discover
from texstage.plugins.runtime import Runtime
from texstage_fd_lab import model
from texstage_fd_lab.authoring import prepare_lesson, TYPE, ENGINE
from texstage_fd_lab.state import Lesson, SLOT_BYTES, STATE_BYTES
from test_engine import probe

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def provider():
    assert {p.id for p in discover()} == {probe.PROVIDER}
    p, _ = probe.installed()
    assert Path(model.__file__).is_relative_to(Path(sys.prefix))
    return p


def source(mode="closure"):
    return json.loads((ROOT / f"examples/functional-dependencies/activities/{mode}.json").read_text(encoding="utf-8"))


def worked(mode="closure"):
    return model.compile_lesson(source(mode))[1]


def prepared(mode="closure"):
    return json_value(prepare_lesson(source(mode), {"language": "en"}))


def context(mode="closure"):
    return {"item": prepared(mode)["prepared"], "epoch": 1, "role": "participant"}


def command(op, payload, *, actor="alice", request="request00001"):
    return {"kind": "command", "operation": op, "payload": payload, "actor": actor, "request_id": request}


def advance(state, event, ctx):
    result = json_value(Lesson().transition(state, event, ctx))
    assert "refusal" not in result, result
    return result["state"], result["effects"]


def opened(mode="closure"):
    ctx = context(mode)
    state = Lesson().initial_state(ctx["item"], ctx)
    state, _ = advance(state, {"kind": "activate"}, ctx)
    state, _ = advance(state, command("open", {"control": 0}), ctx | {"role": "presenter"})
    return state, ctx


def submit(state, ctx, *, actor="alice", version=0, request="request00001", answer=None):
    answer = ctx["item"]["private"]["worked"]["answer"] if answer is None else answer
    return advance(state, command("submit", {"phase": state["phase_version"], "version": version, "answer": answer},
                                  actor=actor, request=request), ctx)


def complete(state, ctx, outcome=None, **changes):
    slot = state["answers"]["alice"]
    outcome = outcome or {"status": "ok", "data": model.analyze(ctx["item"]["public"]["seed"], slot["answer"])}
    return advance(state, {"kind": "evaluation.finished", "actor": "alice", "binding": "analysis",
        "job_id": "synthetic", "correlation_id": slot["correlation"], "outcome": outcome} | changes, ctx)[0]


def view(state, ctx, role, actor="alice"):
    return Lesson().view(state, {"role": role, "actor": actor}, ctx)


@pytest.mark.parametrize('policy', ['closure', 'practice'])
def test_authoring_privacy_and_feedback_release(provider, policy):
    made = prepared(policy)
    assert not {'worked', 'closure', 'exercise', 'evaluations'} & set(made['prepared']['public'])
    assert 'One worked answer' not in made['fragments']['exercise']
    assert 'One worked answer' in made['fragments']['solutions']
    state, ctx = opened(policy)
    state, _ = submit(state, ctx)
    state = complete(state, ctx)
    own = view(state, ctx, 'participant')['own']
    assert ('feedback' in own) == (policy == 'practice')
    assert 'own' not in view(state, ctx, 'participant', 'bob')
    assert 'worked' not in view(state, ctx, 'participant')
    assert 'worked' not in view(state, ctx, 'projector')
    state, _ = advance(state, command('reveal', {'control': state['control_version']}), ctx | {'role': 'presenter'})
    assert view(state, ctx, 'participant')['own']['feedback']['correct']
    for role in ('participant', 'presenter', 'projector'):
        projected = model.canonical(view(state, ctx, role))
        assert ctx['item']['private']['exercise'] not in projected
        assert '"evaluations"' not in projected and '"private"' not in projected


def test_authoring_language_escaping_and_rejections(provider):
    value = source()
    value['exercise']['title']['en'] = r'Closure #1 & \input{secret}'
    fragment = prepare_lesson(value, {}).fragments['exercise']
    assert r'\input{secret}' not in fragment and r'\#' in fragment and r'\&' in fragment
    assert 'Eine mögliche Lösung' in prepare_lesson(source(), {'language': 'de'}).fragments['solutions']
    value = source()
    value['worked_answer']['steps'] = ['f4', 'f3']
    with pytest.raises(ValueError, match='invalid-worked-answer'): prepare_lesson(value, {})
    for entry in probe.fixture(provider, 'examples.json')['examples'][1:]:
        assert prepare_lesson(entry['lesson'], {}).prepared.public['mode'] == entry['lesson']['exercise']['task']['mode']
    value = source()
    value['exercise']['fds'] = []
    value['exercise']['task']['start'] = []
    value['worked_answer'] = {'mode': 'closure', 'closure': [], 'steps': []}
    assert 'No FDs given.' in prepare_lesson(value, {}).fragments['exercise']


@pytest.mark.parametrize('answer,reason', [
    ({'format': 1, 'mode': 'closure', 'closure': 60, 'steps': [3, 2]}, 'unmet-lhs'),
    ({'format': 1, 'mode': 'closure', 'closure': 60, 'steps': [2, 2, 3]}, 'no-progress'),
    ({'format': 1, 'mode': 'closure', 'closure': 28, 'steps': [2]}, 'incomplete'),
    ({'format': 1, 'mode': 'closure', 'closure': 61, 'steps': [2, 3]}, 'overclaimed'),
    ({'format': 1, 'mode': 'closure', 'closure': 4, 'steps': [2, 3]}, 'final-set'),
])
def test_informative_math_feedback(provider, answer, reason):
    state, ctx = opened()
    state, _ = submit(state, ctx, answer=answer)
    state = complete(state, ctx)
    feedback = state['answers']['alice']['feedback']
    assert feedback['reason'] == reason and feedback['correct'] is False
    assert state['answers']['alice']['status'] == 'saved'


def test_alternative_proof_and_guarded_classroom_controls(provider):
    state, ctx = opened('practice')
    answer = worked('practice') | {'steps': [2, 3, 0]}
    state, first = submit(state, ctx, answer=answer)
    state = complete(state, ctx)
    assert state['answers']['alice']['feedback']['correct']
    teacher = ctx | {'role': 'presenter'}
    assert Lesson().transition(state, command('close', {'control': 0}), teacher) == {'refusal': 'stale-control'}
    assert Lesson().transition(state, command('close', {'control': 1}), ctx) == {'refusal': 'role'}
    assert Lesson().transition(state, command('select-demonstration', {'control': 1, 'actor': 'alice'}), teacher) == {'refusal': 'phase'}
    assert Lesson().transition(state, command('demonstrate', {'control': 1, 'step': 0}), teacher) == {'refusal': 'phase'}
    state, _ = advance(state, command('reveal', {'control': 1}), teacher)
    state, _ = advance(state, command('select-demonstration', {'control': 2, 'actor': 'alice'}), teacher)
    assert view(state, ctx, 'projector')['demonstration'] == answer
    assert 'alice' not in model.canonical(view(state, ctx, 'projector'))
    state, _ = advance(state, command('demonstrate', {'control': 3, 'step': 1}), teacher)
    projected = view(state, ctx, 'projector')
    assert projected['walkthrough'] and projected['demonstration']['closure'] == 7
    assert projected['demonstration']['steps'] == [0]
    assert Lesson().transition(state, command('demonstrate', {'control': 4, 'step': 8}), teacher) == {'refusal': 'invalid-step'}
    state, _ = advance(state, command('open', {'control': 4}), teacher)
    assert 'demonstration' not in view(state, ctx, 'projector') and state['demo_step'] is None
    assert 'worked' not in view(state, ctx, 'participant')


@pytest.mark.parametrize('fault', ['exercise', 'answer', 'mode', 'closure', 'steps', 'reached', 'error', 'extra', 'format'])
def test_facts_must_match_the_exact_submission(provider, fault):
    state, ctx = opened()
    state, _ = submit(state, ctx)
    data = model.analyze(ctx['item']['public']['seed'], worked())
    if fault in ('exercise', 'answer'): data[fault] = '0' * 64
    elif fault == 'mode': data['mode'] = 'keys'
    elif fault == 'closure': data['facts']['closure'] = 63
    elif fault == 'steps': data['facts']['trace']['steps'][0][1] = 0
    elif fault == 'reached': data['facts']['trace']['reached'] = 63
    elif fault == 'error': data['facts']['trace']['error'] = {'kind': 'no-progress', 'step': 0, 'missing': 0}
    elif fault == 'extra': data['facts']['extra'] = True
    else: data['format'] = True
    state = complete(state, ctx, {'status': 'ok', 'data': data})
    assert state['answers']['alice']['status'] == 'unavailable'
    assert 'correct' not in state['answers']['alice']['feedback']


def test_replacement_close_and_unavailable_preserve_answers(provider):
    state, ctx = opened()
    state, first = submit(state, ctx)
    state, second = submit(state, ctx, version=1, request='replace00001')
    assert second[0] == {'kind': 'cancel-evaluation', 'correlation_id': first[0]['correlation_id']}
    assert complete(state, ctx, correlation_id=first[0]['correlation_id']) == state
    assert complete(state, ctx, binding='other') == state
    assert complete(state, ctx | {'epoch': 2}) == state
    state, _ = advance(state, command('close', {'control': 1}), ctx | {'role': 'presenter'})
    state = complete(state, ctx)
    assert state['answers']['alice']['feedback']['correct']
    assert 'feedback' not in view(state, ctx, 'participant')['own']
    for status in ('error', 'timeout', 'refused', 'syntax'):
        state, ctx = opened()
        state, _ = submit(state, ctx)
        state = complete(state, ctx, {'status': status})
        own = view(state, ctx, 'participant')['own']
        assert own['status'] == 'unavailable' and own['answer'] == worked()
        assert 'correct' not in state['answers']['alice']['feedback']


def test_bounded_state_actor_versions_and_correlations(provider):
    state, ctx = opened()
    answer = worked() | {'steps': [2] * 8, 'closure': 63}
    correlations = []
    for i in range(64):
        actor = 'actor' + str(i).zfill(3) + 'x' * 248
        state, effects = submit(state, ctx, actor=actor, answer=answer)
        correlations.append(effects[-1]['correlation_id'])
        assert len(model.canonical({actor: state['answers'][actor]})) < SLOT_BYTES
    assert len(set(correlations)) == 64
    for actor, slot in list(state['answers'].items()):
        state, _ = advance(state, {'kind': 'evaluation.finished', 'actor': actor, 'binding': 'analysis',
            'correlation_id': slot['correlation'], 'outcome': {'status': 'ok',
            'data': model.analyze(ctx['item']['public']['seed'], slot['answer'])}}, ctx)
        assert state['answers'][actor]['status'] == 'saved'
        assert len(model.canonical({actor: state['answers'][actor]})) < SLOT_BYTES
    refused = Lesson().transition(state, command('submit', {'phase': 1, 'version': 0, 'answer': answer}, actor='extra'), ctx)
    assert refused == {'refusal': 'capacity'}
    actor = next(iter(state['answers']))
    state, effects = submit(state, ctx, actor=actor, version=1, answer=worked(), request='replacement1')
    assert len(effects) == 1 and state['answers'][actor]['version'] == 2
    assert len(model.canonical(state)) < STATE_BYTES
    assert len(model.canonical({'state': state, 'effects': effects})) < 256 * 1024
    for role in ('participant', 'projector', 'presenter'):
        assert len(model.canonical(view(state, ctx, role, actor))) < 128 * 1024


@pytest.fixture
def runtime(tmp_path, provider):
    r = Runtime(tmp_path / "runtime.sqlite3", Catalog([provider]))
    spec = prepared()["prepared"]
    spec["evaluations"]["analysis"]["engine"] = ENGINE
    r.ensure("lesson", TYPE, "closure", spec)
    r.activate("lesson", {(TYPE, "closure")})
    yield r
    r.close()


def envelope(operation, payload, request="request00001", epoch=1):
    return {"type": TYPE, "item": "closure", "operation": operation, "payload": payload,
            "epoch": epoch, "expected_revision": 0, "request_id": request}


def test_installed_runtime_replay_replacement_reset_and_validated_views(runtime, monkeypatch):
    r = runtime
    monkeypatch.setattr("texstage.plugins.runtime.MAX_PENDING", 1)
    assert r.command("lesson", "teacher", "presenter", envelope("open", {"control": 0}))["accepted"]
    first = envelope("submit", {"phase": 1, "version": 0, "answer": worked()})
    receipt = r.command("lesson", "alice", "participant", first)
    assert r.command("lesson", "alice", "participant", first) == receipt
    stale = first | {"request_id": "device000001"}
    assert r.command("lesson", "alice", "participant", stale)["error"] == "stale-answer"
    assert r.command("lesson", "teacher2", "presenter", envelope("close", {"control": 0}))["error"] == "stale-control"
    old = r.lease("lesson", "presenter", now=100)[0]
    replacement = envelope("submit", {"phase": 1, "version": 1, "answer": worked()}, "replacement01")
    assert r.command("lesson", "alice", "participant", replacement)["accepted"]
    assert not r.finish("lesson", "presenter", {k: old[k] for k in ("id","epoch","generation")} | {"outcome": {"status":"error"}}, now=101)
    job = r.lease("lesson", "presenter", now=101)[0]
    outcome = probe.run([{"seed": job["binding"]["seed"], "binding": job["binding"], "text": job["text"]}])[0]["outcome"]
    assert r.finish("lesson", "presenter", {k: job[k] for k in ("id","epoch","generation")} | {"outcome":outcome}, now=102)
    r.drain("lesson")
    for role, surface in (("participant","participant-input"), ("presenter","presenter-controls"),
                          ("presenter","presenter-overlay"), ("projector","projector-overlay")):
        result = r.view("lesson", TYPE, "closure", role=role, surface=surface, actor="alice")
        if role == "participant": assert "feedback" not in result["data"]["own"]
        if role == "presenter": assert result["data"]["counts"]["correct"] == 1
    reset = envelope("_reset", {}, "reset0000001")
    assert r.command("lesson", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("lesson", "teacher", "presenter", reset)["epoch"] == 2
    assert r.command("lesson", "alice", "participant", first | {"request_id":"late00000001"})["error"] == "stale-epoch"
    assert not r.finish("lesson", "presenter", {k: job[k] for k in ("id","epoch","generation")} | {"outcome":outcome}, now=103)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="needs pdfLaTeX")
def test_installed_authoring_all_editions_and_freshness(tmp_path, provider):
    from texstage.build.builder import BuildOptions, build
    from texstage.build.latex import compile_deck
    from texstage.build.compiler import compile_latex
    from texstage.build.pdf import Pdf
    from texstage.plugins.policy import enable
    from texstage.server.bundles import load_bundle
    deck = tmp_path / "deck"
    shutil.copytree(ROOT / "examples/functional-dependencies", deck)
    catalog = Catalog([provider])
    profile = tmp_path / "profile"
    enable(profile, provider.id, provider.version, provider.payload)
    options = BuildOptions(stage=True, key="fd-test-key", activities=deck / "lesson.activities.json",
                           plugin_data=profile, height=540)
    out = tmp_path / "out"
    result = build(deck / "lesson.tex", out, options)
    assert not result.problems
    bundle = load_bundle(result.bundle, catalog=catalog)
    assert set(bundle.items[TYPE]) == {"closure", "practice", "keys_one", "keys_all", "implied", "refuted", "different_sizes", "empty_key"}
    public = model.canonical(bundle.deck_json)
    assert '"expected"' not in public and '"worked"' not in public and '"evaluations"' not in public
    assert not list(result.bundle.rglob("*.tex")) and not list(result.bundle.rglob("*.activities.json"))
    assert bundle.file("keys.json") is None and result.static.is_file()
    def text(path):
        with Pdf(path) as pdf: return " ".join(page.text() for page in pdf)
    handout = compile_deck(deck / "lesson.tex", "handout", out, plugins=catalog, preparation=options.preparation)
    assert "One worked answer" not in text(handout.pdf)
    assert "One worked answer" not in text(result.stage.pdf)
    assert "One worked answer" in text(out / "build/lesson-solutions.pdf")
    exported = options.preparation.export(deck / "lesson.tex", catalog)
    for edition in ("handout", "solutions"):
        direct = compile_latex(exported[edition], output_dir=out / ("direct-" + edition), passes=2)
        assert direct.returncode == 0, direct.stdout[-3000:]
        assert ("One worked answer" in text(direct.pdf)) == (edition == "solutions")
    path = deck / "activities/closure.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    stale = compile_latex(exported["handout"], output_dir=out / "stale")
    assert stale.returncode != 0 and "Stale prepared input" in stale.log_text

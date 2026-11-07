# FD Lab: implementation plan

Status: F1-F3 implemented; F4 automated load and recovery measured locally,
2026-11-07. See the [F4 evidence](functional-dependencies-f4-validation.md).
The package owns engine, command and four audience-view schemas, a thin LaTeX
style, prepared exercise/solution fragments and phone/presenter controls.
See the [F1 record](functional-dependencies-f1-validation.md),
[F2 record](functional-dependencies-f2-validation.md) and [lesson guide](../fd-lesson.md).
F3 adds one/all key editors, derivation/counterexample editors, the full workshop
sequence and bilingual guides. See the [F3 record](functional-dependencies-f3-validation.md).
F4's physical-phone check is deferred at the user's request. Full performance
acceptance remains open: WebKit misses the provisional 10-second feedback p95
target. F5 release remains pending.
Privacy/race/storage checks already run in F2/F3.
Start with [the design](functional-dependencies.md) and
[the contract](functional-dependencies-contract.md).

## Repository boundary and host readiness

| Repository | Planned work |
| --- | --- |
| `texstage-plugins` | New `fd-lab` package, its schemas/algorithms/UI/style, example deck, independent checks, conformance jobs and documentation |
| Active `texstage-public` (one code history mirrored to GitHub/GitLab) | Reuse existing host contracts; only generic fixes if an integration test exposes a gap |
| `lecture-tools-next` | No change needed; existing compilation orchestration can invoke the enabled provider through TeXStage |
| Original tools, existing courses, archived host and private media | No changes or environment/pin updates |

Host `de33515` already provides typed facts, revision-2 views, prepared authoring,
structured errors, atomic cancellation/replacement, mount lifecycle handling and
epoch reset. The Firefox/WebKit worker correction is already implemented under
unchanged restrictions. Reuse and regression-test these features; do not reopen
them as speculative prerequisites. Remaining shared gates are measured queue
fairness/classroom throughput and a published immutable compatible host release.
Neither the transaction lesson nor the relational visual editor blocks this plan.

## Planned files

```text
texstage-plugins/
  docs/design/functional-dependencies{,-contract,-plan}.md
  docs/design/functional-dependencies/
    README.md
    lesson-v1.schema.json
    answer-v1.schema.json
    examples.json
    expected-cases.json
    validation.json
  plugins/fd-lab/
    pyproject.toml, MANIFEST.in, LICENSE, README.md, texstage-plugin.json
    texstage_fd_lab/
      __init__.py
      model.py              # independent Python preparation/reference model
      authoring.py          # named source -> public/private/prepared TeX
      state.py              # phases, versions, effects, grading, projections
      schemas/
        lesson-v1.json, seed-v1.json, answer-v1.json, analysis-result-v1.json
        commands/, views/
      web/
        validation.mjs, identity.mjs, dependencies.mjs
        engine.mjs, engine.worker.mjs
        set-editor.mjs, derivation-editor.mjs, witness-editor.mjs
        participant.mjs, presenter-controls.mjs, lesson-overlay.mjs
      latex/texstage-fd-lab.sty
      templates/, locales/en.json, locales/de.json
    tests/test_model.py, test_engine.py, test_authoring.py, test_lesson.py
  examples/functional-dependencies/
    lesson.tex, lesson.activities.json, activities/*.json
  docs/fd-lesson.md
  maintenance/
    check_fd_design.py
    fd_probe.py, run_fd_engine.mjs, fd_browser.cjs, fd_lesson_browser.cjs
```

Extend the existing wheel builder, generated-worker check and conformance
workflow as needed. Keep original coordinate/distance, transaction-only and
relational scenarios isolated; add FD-only and combined-provider scenarios.
Do not weaken tests asserting an exact installed provider set. Use existing
SDK build helpers, not a new packaging system or provider-to-provider imports.

## F0 — freeze the finite contract

Review the supplied scope, symbolic examples, empty-set behavior, nonunique
proofs, minimality and completeness. Promote draft schemas into the package only
after freezing seed, result, commands and all audience view shapes. Treat a
later incompatible semantic change as a new version, not a silent format-1 edit.

Acceptance:

- Reproduce `python maintenance/check_fd_design.py`; inspect its explicit limits.
- Verify duplicate IDs/keys, unknown attributes, malformed numbers, masks outside
  the relation, wrong modes, invalid traces and invalid worked answers fail clearly.
- Check draft/result/view schemas against the current portable host profile and
  both real validators. A Python JSON Schema pass alone is insufficient.
- Demonstrate largest legal answer, engine facts and complete outcomes fit the
  host budgets without truncation. Include Unicode authoring and ASCII escaping.
- Freeze proposed names/style exports with no conflicts against installed providers.

## F1 — independent engine

Implement named-source compilation and Python closure/key/witness logic, then
an independently structured pure JavaScript engine. Use cached closures for
bounded exact key enumeration; implement replayable derivations and two-row
counterexamples. Implement actual start/load/evaluate/dispose, fresh submissions,
strict parsing, operation accounting, stable identities and typed facts.

Acceptance:

- Agreement between independently implemented models, hand-derived expected
  cases and tiny exhaustive checks. Cover multi-attribute determinants and right
  sides, cycles, empty/trivial/redundant FDs, differently sized keys, empty keys,
  all-keys omissions, alternative proof orders and alternative counterexamples.
- Malformed input is distinct from a mathematically wrong answer and from
  resource exhaustion. Operation limits and dispose/reuse failures are exercised.
- Build wheel and sdist with resource parity; test only installed artifacts in
  a clean environment. Record exact provider/host wheel and payload identities.
- Engine-only probe uses the actual host evaluator in Chrome, Firefox and
  WebKit, with the unchanged CSP and generated self-contained worker entry.
  Include active blocked-network/child-worker probes with controls, bad-result
  rejection, timeout and clean recovery. Do not count a Node import as this gate.

Interim delivery is explicitly engine-only. It is not a classroom activity.

## F2 — complete closure lesson slice

Add prepared authoring, static fragments, style, phase state, participant closure
editor and presenter/projector controls for one workshop exercise. Verify the
worked answer independently and bind evaluation to the compiled seed. Produce
public/private material and all projections from the same validated source.

Acceptance:

- A new user installs and explicitly enables a pinned wheel, builds the example,
  joins from a phone, submits a derivation, sees a useful result after reveal,
  and can reopen/reset without losing or misapplying responses.
- The same source builds live slides, handout, solutions, static PowerPoint and
  local direct-pdfLaTeX exports. Visual inspection of both exercise and solution
  PDFs catches clipping, unreadable arrows and insufficient writing space.
- Source/asset/style freshness and directory confinement pass. Solutions and
  reference tables do not appear in public bundles, initial slides or views.
- Reducer validates result identity and every trace fact before accepting it;
  mathematical correctness never depends on equality to one reference trace.

Do not advertise keys or implication UI until F3 is complete. Other modes can
remain engine capabilities during this slice; authoring rejects unsupported ones.

## F3 — keys and implication classroom modes

Add the key-set editor and same/different witness editor, with shared set widgets
and consistent language. Support one-key and all-keys tasks as separate author
policies. Add the complete workshop sequence, differently sized keys and empty
key examples to the source deck. Keep UI-selected demonstration state separate
from the immutable task and participants' saved answers.

Acceptance:

- Alternative correct keys/proofs/witnesses pass; missing keys and nonminimal
  superkeys receive different feedback. An empty key is visible and editable.
- Positive implication only needs to derive its target; closure mode must reach
  a fixed point. Negative witnesses must satisfy every premise FD.
- Bilingual user guide explains installation, what FDs mean, one/all key tasks,
  authoring, feedback timing, solutions and operational failures. It does not
  imply a style file installs code or that sample uniqueness proves a key.
- Keyboard, touch and 320 px layouts work for all modes in all three browsers.
  Test enabled controls through real interaction, draft/focus preservation,
  two devices for one actor, reset within an existing mount and teardown.

## F4 — privacy, races and load

Exercise close-with-pending, replacement/result races, reset/late results,
two presenters, replayed requests, queue-full replacement, new-actor capacity,
evaluator disconnect/replacement and reconnect. Validate full serialized actor
slots, state, effects and projections, reserving feedback space at submission.
Use private inspection and deliberate anonymous sharing; never broadcast all
answer records as presenter state to the projector.

Acceptance:

- 64 synthetic participants with proposed 2 KiB slots and 160 KiB state fit
  provider and host budgets; replacements remain possible at both actor and
  queue capacity. Store compact feedback, not full result histories.
- An actual 64-answer burst records queue age, p95/worst evaluation latency,
  UI latency, memory and serialization sizes on named hardware. Provisional
  targets: input p95 below 100 ms, feedback p95 below 10 s and worst below 30 s;
  the host's per-job two-second deadline is unchanged. Revise targets explicitly
  if measurements show otherwise; storage fit is not a throughput result.
- Physically test a phone over ordinary LAN HTTP; browser emulation is separate
  evidence. The lesson keeps useful pending/unavailable status without a presenter
  evaluator, and never labels service failure as a wrong answer.
- Inspect actual transmitted public JSON/bundle routes for withheld answers,
  other students' records, identities, private tables and binding leakage.

## F5 — reproducible release

Run installed-wheel host regressions and provider conformance on Windows and
Linux. CI builds once, hands the same wheels/bundles to the browser matrix, and
installs TeX, fonts and both language dependencies before authoring tests. Verify
that authoring tests actually execute rather than silently skip. Format and
check source before freezing artifact hashes; generated worker freshness is a gate.

Document exact host compatibility, immutable artifacts, licenses, resource
inventory, isolated installation/enable/lock/build commands and known limits.
Retain existing provider and no-plugin behavior. Add a reviewed catalog entry
only when immutable release artifacts and matching published host pins exist.
Publishing, commits, pushes and course migration are separate requested actions.

## Recommended next step

Complete the remaining F4 gates: investigate WebKit's measured 64-answer queue
latency and test a physical phone over LAN HTTP. Retain the 10-second feedback
p95 target until an explicit reviewed capacity decision changes it; do not
equate a successful completion with a performance pass. Recheck timing on the
intended lecture hardware and network.

F4 added generic host schema caching, coalesced projections, busy-queue polling
and disconnect lease release. The provider remains byte-identical at 0.3.0.
Combined FD/relational/transaction engine checks and the F1-F3 regression gates
are recorded in the F4 evidence. F5 still requires a published immutable host
pin, identical-artifact Linux/Windows evidence and an explicit release request.

# Query-plan Challenge: implementation plan

Current storage/scalability extension: [600-student plan](query-plan-600-plan.md)
and [validation](query-plan-600-validation.md). Earlier milestone bounds below
record their original scope.

Status: Q0–Q4 implemented locally, 2026-11-07. Version 0.4.0 adds selectors,
local cost inspection and presenter controls to the frozen classroom protocol.
See the [classroom protocol](query-plan-classroom-contract.md),
[Q3 validation](query-plan-state-validation.md), [engine contract](query-plan-challenge-contract.md),
[Q1 record](query-plan-engine-validation.md) and [Q2 record](query-plan-authoring-validation.md).
[Q4 validation](query-plan-ui-validation.md) records installed interface checks.
The [classroom guide](../query-plan-lesson.md) covers the complete interaction.
Overlays retain the static exercise until a plan is shared or a solution revealed.
No host extension, catalog release or course migration is included.
The [authoring guide](../query-plan-authoring.md) describes current use.

## Repositories and intended files

All domain code belongs in the active texstage-plugins repository. Texstage's
mirrored code repositories remain one codebase; they need changes only if a
generic contract gap is demonstrated. The original lecture-tools, course
repositories, lecture-tools-next and private media are outside this work.

```text
texstage-plugins/
  docs/design/query-plan-challenge.md
  docs/design/query-plan-challenge-plan.md
  docs/design/query-plan-challenge/
    README.md
    exercise.schema.json
    answer.schema.json
    exercises.json
    expected-cases.json
    validation.json
  maintenance/check_query_plan_design.py
  plugins/query-plan/
    pyproject.toml
    MANIFEST.in
    LICENSE
    README.md
    texstage-plugin.json
    texstage_query_plan/
      __init__.py
      model.py                 # independent Python per-plan model/enumerator
      authoring.py
      state.py
      schemas/
        exercise-v1.json
        answer-v1.json
        lesson-v1.json
        analysis-result-v1.json
        commands/
        views/
      latex/texstage-queryplan-challenge.sty
      templates/
      locales/en.json
      locales/de.json
      web/
        validation.mjs
        model.mjs
        identity.mjs
        engine.mjs
        engine.worker.mjs      # generated, self-contained
        plan-editor.mjs
        cost-inspector.mjs
        participant.mjs
        presenter-controls.mjs
        lesson-overlay.mjs
    tests/
  examples/query-plan/
    lesson.tex
    lesson.activities.json
    activities/
  docs/query-plan-lesson.md
  maintenance/
    run_query_plan_engine.mjs
    query_plan_probe.py
    query_plan_browser.cjs
```

The package now contains the engine, independent Python model/enumerator,
four frozen schemas, fixtures and installed-wheel tests. The three engine probes
and worker-bundler entry are present; build_wheels.py discovers the new package
without a source change. The original distance/coordinates test scenario still
requires exactly those two providers. Q2 adds authoring.py, prepared-view-v1.json,
the namespaced style and read-only overlay, four source examples, authoring tests
and authoring/browser probes. Q3 adds state.py, generated command/audience schemas,
state tests and the authenticated protocol browser probe. Q4 adds the bounded
selector model, shared UI/localization helper, cost inspector, participant,
presenter and overlay modules, plus selector and real-UI browser tests. Locales
are contained in lesson-ui.mjs; no separate templates/locales are needed. Q5
adds release CI and physical-device/load evidence.

## Q0 — engine/source contracts frozen; live contracts move to Q3

Depends on review of the design and examples.

- Freeze teaching-cost-v1, fixed query grammar, canonical postorder, typed filter
  values, index eligibility, connected-subset coverage and legal plan family.
- Source/answer schemas, strict semantic validators, the separate lesson
  envelope/goals, typed valid/invalid results and identity payloads are frozen.
  Classroom command and role schemas were frozen in Q3; Q2 had only read-only views.
- Seed, answer, result and lesson-envelope budgets are measured with ASCII JSON,
  escaped text and all node facts. Reject excess; do not truncate facts or
  increase host caps. Actor slots, shared state, transitions and role views are
  still design targets and move to Q3 with their actual contracts.
- Prove the 864-candidate/4,320-node enumeration bound and safe-integer bound;
  document that memory means per-operator hash workspace.
- The portable result schema passes both installed host validators. Future
  Q3 view schemas must pass the same gate. Source schemas use a broader profile;
  do not copy pattern/$id into portable result/view schemas.
- Record exact host wheel, commit and resource identity. Confirm typed results,
  prepared authoring, structured dispatch errors, atomic queue replacement,
  reset and mount lifecycle against that artifact.

Exit: machine-checked contract fixtures (including malformed/invalid boundaries),
measured sizes and a short Q0 validation record. No unspecified data used for
grading; no hidden statistics.

## Q1 — cost engine implemented and verified

Implement the Python model/enumerator and independently written JS model.
The design checker remains an oracle for its finite examples, not runtime code
to import or the only correctness test.

- Validate shape before semantics. Reject duplicate keys, NaN/Infinity, booleans
  as integers, unknown fields/methods, oversized/deep input, forward edges,
  shared children, unreachable nodes, wrong leaf coverage and disconnected joins.
- Test filters/types/projection, statistics coverage/consistency, empty inputs,
  unavailable indexes, hash equality at the limit, and one byte over.
- Test all legal plans for the supplied small exercises against the independent
  model; cost facts must agree, but tied plans need not have equal canonical keys.
- Separately execute small duplicate-containing relation fixtures with a simple
  nested-loop bag oracle. Every legal plan shape must preserve the fixed query's
  bag output. Also cover multiple matches, empty inputs and filters.
  A finite oracle is regression evidence for the restricted-construction argument,
  not a general SQL equivalence prover.
- Metamorphic checks: swapping children plus the hash build designation preserves
  costs; enlarging the memory limit cannot worsen the optimum; changing the
  baseline cannot change costs/optimum; changing only labels cannot change identity.
- Test alternative optima and feasible-but-expensive answers. Never use canonical
  matches as correctness.
- Implement fresh-per-submission engine lifecycle, bounded typed facts and
  portable semantic hashing (known vectors, LAN HTTP).
- Add the engine to the existing pinned worker bundler; check generated source
  matches editable modules and contains no remaining imports.

Exit: independently installable engine capability in a portable wheel; wheel/sdist
resource parity, Python/JS domain checks, both host contract validators and
an installed-wheel probe pass. It is still an engine, not a usable lesson.

## Q2 — prepared authoring and static materials implemented

Depends on Q1's fixed engine contract.

- Implement PreparedAuthoring from the separate lesson envelope. Validate the
  baseline and worked answer; exhaustively compute minimum/goal reachability
  once at preparation. Bound work and measure against the existing prepare
  timeout; optimize or reduce scope before considering a generic host change.
- Separate public exercise/constraints/baseline from private reference/goal
  facts and teacher explanation. Public best/budget goal remains visible.
- Generate exercise/solution fragments and live facts together; style command
  \queryplanchallenge delegates to \texstageprepared.
- Add a compact example deck: index choice, join order, and a reduced-memory
  variant. The handout must be solvable using the printed statistics/formulas.
- Verify live build, handout PDF, solutions PDF, static PowerPoint and direct
  pdfLaTeX exports. Check fresh preparation after source changes, path confinement,
  missing providers and useful static fallbacks. Visually review generated pages.
- Explain the bag/set distinction when linking the relational-algebra example.

Exit achieved locally: installed-wheel prepared authoring and consistent static
editions, including English/German PDF checks, static PowerPoint and direct
pdfLaTeX exports. The read-only bridge is necessary because the current host
requires state hooks and presenter/projector views for every content type; it
exposes only a mode marker and declares no messages or participant surface.
No core API extension was needed. No claim of a phone activity until Q3/Q4.
See the [Q2 evidence](query-plan-authoring-validation.md).

## Q3 — lesson state and authoritative feedback implemented

Reuse the SDK mechanisms demonstrated by the relational lesson, independently
implementing this provider's state/projections.

- Introduce/open/closed/revealed, separate phase/control/answer versions,
  one answer per actor, explicit select/share/clear and host-epoch reset.
- Declared analysis binding; actor/request/slot correlation; cancellation and
  replacement; late results must match all current identities and node facts.
- Goal policy accepts every eligible tied optimum or within-budget answer.
  Invalid plans, target misses, pending and operational failures are distinct.
- Keep full traces out of per-actor state. Reserve feedback capacity before
  saves; measure 64 full slots plus shared state/effects. Reject a new actor
  at capacity, while preserving existing-actor replacement.
- Test retries, two devices/one actor, two presenters, simultaneous answers,
  close with pending jobs, reveal with partial results, reset, navigation,
  evaluator loss/recovery and atomic replacement at the host queue ceiling.
- Assert role leakage at JSON projection/transport boundaries, including
  anonymous sharing, answer replacement, unrevealed optima and reset.

Exit achieved locally: installed reducer/runtime tests, independent per-plan
fact checks, measured state/view bounds and real-host browser protocol checks.
The frozen protocol makes reveal terminal until reset, closes an open phase
on navigation, and uses stable roster numbers across persistence/replacements.
See the [Q3 validation](query-plan-state-validation.md). UI is not the security
boundary and remains the separate Q4 milestone.

## Q4 — phone/presenter interaction implemented

A JSON debug form may help development; it does not satisfy this milestone.

- Build labeled scan/join/build-side controls and bounded join-order choices.
  Use the same provider's pure model for explicit local preview, never the
  private binding or optimizer enumeration.
- Numbered tree and node inspector: local vs cumulative cost, output rows,
  arithmetic, hash workspace and infeasibility explanations.
- Baseline/draft comparison, undo, reset to baseline, explicit submit, useful
  pending/error feedback and presenter open/close/reveal/share controls.
- Preserve drafts/focus/selection on unrelated updates; handle newer same-actor
  saves and reset with explicit keep/reload choices. Clean up mounts/callbacks.
- Keyboard, touch, narrow phones, zoom/resize, screen-reader names and EN/DE
  strings; static problem remains visible before an overlay is needed.

Exit achieved locally: complete installed-wheel classroom flow for all four
examples, numbered tree/arithmetic, keyboard and 320px touch input, 200% text
enlargement, EN/DE labels, focus/draft conflicts and receipt/reset races.
The bounded selector offers all feasible ordered trees; disconnected subtrees
are excluded. Hash choices show workspace requirements even for an infeasible
draft. See the [Q4 record](query-plan-ui-validation.md) and screenshots.
Actual screen-reader and physical-phone/LAN checks remain Q5.

## Q5 — automated classroom validation implemented; manual and publication gates remain

- Use Chrome/Chromium, Firefox and WebKit with the actual evaluator policy.
  Cover valid/invalid results, timeout cleanup/recovery and active restrictions
  on same/cross-origin fetch, XHR, WebSocket, EventSource, child/blob workers,
  external imports, eval and Function. A timeout is not proof of blocking.
- Recheck relational and transaction engine probes and the isolated original
  pair when changing shared builders/host components. No relaxed-CSP success.
- Verify on an actual phone over classroom LAN HTTP, not only desktop emulation.
  Check preview hashing and operation without secure-context APIs.
- Measure 64 synthetic participants, replacements, sustained submissions,
  queue fairness/latency and evaluator absence. Publish observed capacity,
  browser/OS versions and precise artifacts; serialized size alone is not load evidence.
- Run isolated installed-wheel and sdist parity checks on Windows and Linux;
  add hosted CI with compatible immutable host artifacts.
- Write docs/query-plan-lesson.md: installation/enablement/pinning, authoring,
  model/formulas, all LaTeX commands, classroom workflow, privacy, static output,
  troubleshooting and explicit limitations. Link it from the collection README.
- Record validation evidence and remaining limitations before adding a reviewed
  catalog entry. Sign/publish immutable releases only when separately authorized.
  No automatic installation through decks/styles.

Local automated evidence now includes Windows/Linux installed artifacts,
cross-platform source-distribution parity, the real three-browser UI/security
matrix and a measured 64-participant workload. The measurements exposed repeated
schema validation and projection work in the generic host. The tested combined
host uses bounded schema-check caching with isolated error schemas, coalesced
audience projections, prompt draining of busy evaluator queues and requeueing
after observed evaluator disconnects. Silent failure still uses the production
120-second lease. These changes preserve role filtering, per-value validation,
worker security and durable receipts.

The separate Query-plan release workflow requires a full published host commit
and verifies identical artifacts in its consumers. It has not been run on hosted
CI. See [Q5 evidence](query-plan-release-validation.md) and the
[release/manual check procedure](../query-plan-release-checks.md).

Exit remains conditional: physical-phone/LAN and real screen-reader checks,
a published compatible host pin and successful hosted jobs are still required.

## Host impact and sequencing

No Texstage source modification is planned initially. Its current generic
contracts cover this design; verify that claim in Q0. If measurement reveals a
gap, record the failing case and fix the generic mechanism with regression
coverage in the active host. Do not add plugin-specific branches to core.

The relational visual editor can proceed independently. A common tree widget
is a later extraction based on two tested implementations, not a prerequisite
for this bounded selector UI. Do not block on the transaction lesson or start
migrating existing courses.

**Next concrete step: complete the manual and publication gates** — test physical
phones on classroom LAN HTTP and real screen readers using the recorded procedure;
review/commit the host and collection changes, publish a compatible immutable
host commit, then run the prepared hosted workflow. No course migration or catalog
publication has occurred.

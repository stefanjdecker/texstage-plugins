# Transaction-schedule plugin: completion plan

> Implementation update: the classroom package, prepared authoring, four views,
> actor records, private feedback and generic host archive integration are now
> implemented and merged. Classroom release preparation continues on
> `codex/classroom-release`. See the
> [release validation record](classroom-release-validation.md) for measured results
> and remaining classroom/release gates. The planning text below preserves the
> original acceptance criteria; it is not a claim that every gate has passed.


Revised 2026-11-07 against TeXStage
[`f612a366ddde07b79a6d5f70160d7ac9db8bd880`](https://github.com/stefanjdecker/texstage/commit/f612a366ddde07b79a6d5f70160d7ac9db8bd880)
and collection `604b515d10ca5f27fc2398d7caade1b071379226`.
Planning baseline: the analysis engine existed when this plan was written;
the classroom implementation described below was still outstanding. The status
notice above and validation record describe the implementation now available.

The deliverable is an installable, bilingual lesson in which students predict
an execution, inspect remembered reads, explain direct conflicts and submit
different valid repairs. A lecturer can run the whole lesson from LaTeX, collect
answers from phones, control feedback and export the material and session.
The [activity design](transaction-schedules.md) supplies the teaching model;
this plan supersedes its former 200-participant implementation budget.

## Scope and completion criteria

Retain the existing bounded model: two or three transactions, one to three
integer objects, up to twelve reads/writes plus one terminal commit per
transaction. Writes use a constant or an earlier own read plus an increment.
Keep prediction, stepped inspection, conflict diagnosis and schedule repair.
Locks, aborts, recovery, MVCC and SQL isolation levels remain future activities.

Version 1 retains the agreed formative-feedback policy. It gives component
feedback without automatic scoreboard points. Optional numeric scoring and a
partial-credit rubric are a separate follow-up using the existing host points
API; they are not prerequisites for this lesson. Speed bonuses would reward
different behavior from the reasoning task and are outside this plan.

Target 600 answering students with a hard ceiling of 1,000 stored participants
per activity. Both sizes require transaction-specific measurements. The B+
capacity results do not establish transaction capacity, particularly for diverse
repairs that require separate browser evaluations. A failed 1,000-student run
must remain visible; a tested 600-student candidate can be labelled accordingly.

| Completion level | Required evidence |
| --- | --- |
| Working classroom activity | Installed engine/activity wheels, one complete lesson, all phases and views, privacy/race tests, working static editions |
| Validated classroom candidate | Full synthetic example set, three-browser checks, Windows/Linux artifact checks, measured 600/1,000 workloads, physical-phone and accessibility rehearsal |
| Released plugin pair | Successful hosted checks, reviewed immutable artifacts and host pin, installation/rollback documentation and catalog entries |

Keep those statuses separate. A passing engine test or a buildable activity
wheel is not completion of the classroom or release gates.

## What is already available

- `plugins/transaction-engine/` supplies `texstage-transaction-engine` 0.1.0,
  provider `io.github.stefanjdecker.transactionengine`, engine `.schedule`.
  Its manifest revision is 2; API and engine API are 1.
- The engine returns bounded typed analysis, direct-conflict witnesses and
  cycle/topological certificates. Preserve its public seed and result contracts.
- [M2 evidence](transaction-engine-m2-validation.md) and the
  [collection validation](plugin-collection-validation-2026-11-07.md) record
  67 engine tests, all 1,742 legal interleavings of six small programs, wheel/sdist
  parity and actual-host checks in Chrome, Firefox and WebKit.
- Current TeXStage already provides prepared authoring, closed view schemas,
  durable receipts, epoch reset, cancellation/replacement, renderer lifecycle,
  bounded actor records, paged presenter rosters and batched projections.
- The host has a 1,000-job session queue, adaptive evaluation batches and an
  opt-in result cache. The current transaction engine does not declare caching;
  plan measurements must include uncached diverse submissions.

Use the exact published host commit above as the starting compatibility pin.
It is a development revision, not a package release. If host changes are needed,
publish and test their replacement pin before claiming hosted compatibility.

## Repository ownership and files

Implementation should start on `codex/transactions-classroom` in isolated
worktrees based on the validated source pair. This planning change does not
create that branch. Preserve the scoring work, original lecture-tools,
lecture-tools-next, existing courses and their environments, and private media.
All new exercises and test participants are synthetic.

Keep two installable distributions. The existing engine remains reusable; add
`texstage-transaction-activity`, provider
`io.github.stefanjdecker.transactionactivity`, content type `.schedule`.
The lesson's `analysis` evaluation binding names
`io.github.stefanjdecker.transactionengine.schedule`. Both providers must be
explicitly installed, enabled and pinned. Missing/disabled engines fail the
build; neither a deck nor a style installs code.

| Repository | Files and responsibility |
| --- | --- |
| texstage-plugins | New `plugins/transaction-activity/` package: authoring, independent model, feedback, state, storage, schemas, LaTeX, views and tests |
| texstage-plugins | Existing `plugins/transaction-engine/`: retain semantics and standalone conformance; change only for a demonstrated defect or reviewed optional optimization |
| texstage-plugins | New `examples/transactions/`, lesson guide, installed-wheel/browser/load probes and transaction-specific CI |
| TeXStage | Generic archive completion and any measured host scheduling/lifecycle gaps; regression tests for affected mechanisms |
| Existing courses and original tools | No changes; course adoption is a separate task after a disposable rehearsal |

Proposed activity layout (these files do not exist yet):

```text
plugins/transaction-activity/
  pyproject.toml, MANIFEST.in, LICENSE, README.md, texstage-plugin.json
  texstage_transaction_activity/
    __init__.py, model.py, authoring.py, feedback.py, storage.py, state.py
    schemas/lesson-v1.json
    schemas/actor-value-v1.json, actor-summary-v1.json
    schemas/command-*.json, *-view-v1.json
    latex/texstage-transactions-schedule.sty
    locales/en.json, de.json
    web/participant.mjs, presenter-controls.mjs
    web/presenter-overlay.mjs, projector-overlay.mjs, layout.mjs
  tests/test_model.py, test_authoring.py, test_state.py
  tests/test_feedback.py, test_privacy.py, test_storage.py
examples/transactions/
  lesson.tex, lesson.activities.json, README.md
  activities/*.lesson.json
docs/transactions-lesson.md
maintenance/transaction_lesson_probe.py
maintenance/transaction_lesson_browser.cjs
maintenance/transaction_load_server.py, transaction_load_browser.cjs
.github/workflows/transaction-conformance.yml
.github/workflows/transaction-capacity.yml
```

Reuse the SDK builder and the structure of relational-lab's prepared authoring,
B+'s actor records and the existing worker-security harness. Providers own their
runtime resources; avoid imports of sibling provider internals or collection
maintenance scripts from an installed package. `build_wheels.py` already
discovers package directories and needs no hard-coded package registration.

## M0: freeze the remaining contracts

Deliver a `transaction-lesson-contract.md` alongside executable schema/fixture
tests before connecting a renderer. Cover:

- A lesson envelope around the unchanged exercise seed: checked worked repairs
  and bounded bilingual explanations. Keep source JSON, public problem data,
  private reference facts and live answer records distinct.
- Activity manifest revision **3**, with `actor_records`, four closed view
  schemas, `participant_updates: "actor"` and explicit `broadcast_fields`.
  The engine stays revision 2. Manifest, API, state and exercise versions have
  distinct meanings. The formative release has no scoring declaration.
- Message shapes and stable reason codes; separate global revision,
  `control_version`, `phase_token` and each actor's per-phase `answer_version`.
  Derive prediction-value bounds from the engine's integer model.
- Result identity: actual persisted binding including engine, exercise digest,
  submitted order, epoch, actor/slot correlation and current answer version.
- Bounds for every field and worst-case encoded records, effects and views.
  Use the host's restricted portable schema profile for result/view/record
  resources, rather than copying the broader author-source schema unchanged.

Exit: maximum-size fixtures pass both host validators; malformed/wrong-identity
fixtures fail at the intended boundary. The published host pin, exact engine
wheel/payload and selected installation scenarios are recorded.

## M1: reuse and close generic host gaps

Most of the original M1 prerequisites are implemented. Recheck them through the
new provider instead of introducing another storage, evaluation or UI framework.

| Area | Current mechanism | Remaining work and owner |
| --- | --- | --- |
| Typed facts and preparation | API 1, result contract 2, `PreparedAuthoring` / `PreparedItem` | Collection integration tests; no new transaction transport |
| Classroom storage | `SaveActor`, capacity 1,000, 25-row summaries, selected-record reads | Activity schema/budget tests; no full-class answer array in shared state |
| Editable views | Persistent mounts, `ctx.dispatch`, structured errors, `ctx.signal` | Four activity renderers and tests for drafts, focus, reset and teardown |
| Evaluation under load | `Evaluate`, `CancelEvaluation`, leases, adaptive batches and bounded queue | Transaction measurements, same-actor replacement and mixed-item fairness; generic host changes only if a reproducible gap fails the gate |
| Archives | Private `/api/archive/<session>/plugins.json` includes actor records | Generic inclusion in the lecturer's archive ZIP and a distinct sanitized projector-summary export |

For host performance fixes, start with `src/texstage/plugins/runtime.py`,
`src/texstage/server/plugins.py` and the presenter evaluator. Extend existing
classroom, actor-record, broadcast, view-batch and evaluator-poll tests.
Keep authenticated roles, per-view validation, worker isolation and deadlines.
Retain no-plugin, built-in SQL/SPARQL and legacy-provider regression coverage.
An optional `result_cache: "by-input"` optimization would change the engine
payload and needs fresh-state, namespace, privacy and artifact evidence. It must
not substitute for the uncached capacity test or make a cache hit an answer key.

Archive work is a generic host deliverable, independent of the first lesson
slice. Extend `server/app.py`'s archive path and `server/archive.py`, with runtime
support as needed. Include the existing private snapshot with its pins, records
and jobs in the authorized lecturer ZIP. Define a separate versioned summary
from schema-validated **projector** projections at the exported phase; never
derive it by deleting a few keys from the private archive. Keep export creation
presenter-authorized. Exclude actor IDs, receipts, job text and unrevealed facts
from the public summary. This proposed export is not an existing SDK hook.
Test no-plugin sessions, both archive paths and cross-session authorization.

M3/M4 can proceed with the current host. Host changes needed for M5 must be
landed and pinned before the final cross-repository conformance run.

## M2: retain the completed engine gate

Keep the standalone engine installation and its 67 current tests. Preserve
the independent design checker, hand-derived cases and exhaustive small-program
comparisons. A new Python activity model must agree with those fixtures without
using the JavaScript engine as its own oracle. Do not import the maintenance
checker into production; keep the test oracle independently reviewable.

Accept repairs by semantic facts: exact operation permutation, preserved program
order and an acyclic direct-conflict graph. Different valid schedules, cycle
rotations and topological orders must not be rejected merely because they differ
from one deterministic reference. Equal final values do not establish conflict
serializability. Retain this rule in feedback, tests and teaching material.

## M3: implement authoring, state and feedback

### M3a: one source and a first installed lesson

Implement the bounded Python model and `authoring.py`. Preparation independently
checks the original trace and every supplied worked repair; an invalid worked
solution fails the build. Generate public prompt/program/schedule data, private
original analysis and explanations, and the fixed `analysis` binding with no
reference-equality grading. Escape authored text with `latex_escape`.

Keep the designed LaTeX interface:

```tex
\usepackage{texstage-transactions-schedule}
\begin{transactionsschedule}[id=counter]{.96\linewidth}{5.5cm}
\end{transactionsschedule}
```

The environment wraps `\texstageprepared`; declare its namespace and export in
the manifest. A source such as `activities/counter.lesson.json` is mapped by
`lesson.activities.json` to the qualified activity type. Use current `build`,
`pdf --handout`, `pdf --solutions` and `prepare` commands with `--activities`
and explicit provider locks. Test confined sources, freshness and direct
pdfLaTeX entry points. All editions derive from the same checked source.

Start with the lost-update counter. Then add independent-object/read-read,
write-write, three-transaction-chain and cyclic-blind-write lessons. The last
must demonstrate that matching a serial execution's final values does not prove
conflict serializability. Include both serial and interleaved valid repairs,
maximum-size layouts and English/German variants. The synthetic database deck
may link these examples; existing course decks remain unchanged.

Exit: an installed activity wheel builds a usable unanswered slide and matching
worked solutions, live bundle, handout and static PowerPoint. Public artifacts
contain no private fragments; rendered pages are legible at the maximum bounds.

### M3b: phased classroom protocol

Use the monotonic sequence below. Navigation suspends input; returning preserves
the phase and saved answers, and requires an explicit presenter resume for a
paused answer phase. It must not reopen a phase whose answers were revealed.
Reset starts Ready in a new host epoch. No saved answer is automatically resubmitted.

Keep a monotonic `prediction_revealed` flag: reaching the final inspection step
or advancing to Diagnose releases final-value feedback for this epoch. Moving
the cursor backwards cannot make previously released feedback private again.

| Phase | Accepted activity | Feedback released |
| --- | --- | --- |
| Ready | Presenter opens prediction | Model and problem only |
| Predict | Own final-value prediction and replacements | Receipt and structural errors |
| Inspect | Presenter moves the original execution cursor | Trace prefix and remembered reads; final-value feedback only at the final step |
| Diagnose | Directed edges, one direct witness per edge, cycle or serial-order certificate | Receipt and structural errors |
| Repair | Own proposed operation order and replacements | Receipt, legal-order errors and analysis status; correctness withheld |
| Reveal | Presenter inspection/sharing and delayed accepted results | Own feedback, aggregate categories, original graph and checked worked repairs |

Define presenter commands `advance-phase`, `seek-step`, `resume-phase`,
`roster-page`, `select-answer`, `share-answer` and `clear-share`, plus the core
reset. Participant commands are `submit-prediction`, `submit-diagnosis`,
`submit-repair` and `retry-analysis`. Use `latest` host policy and compare the
relevant semantic guards inside the reducer. Presenter selections use
`record_actor_field`; participant payloads never choose an actor.

`retry-analysis` retries only that actor's unchanged accepted repair after an
operational failure, including after closure. It cannot change the answer or
bypass a phase. Track the new correlation separately from the answer version;
old results remain obsolete. Queue-full refusal leaves the whole submission
uncommitted and preserves the local draft for explicit retry.

Store one record per actor containing the latest prediction, diagnosis and
repair, their versions and compact feedback/status. Use `SaveActor` with
`Evaluate`/`CancelEvaluation` in the same transition for atomic replacement.
Correlations use `evaluation_correlation(actor, request_id, "repair")`.
Apply results only to the current saved correlation/binding/exercise/order.
Accepted work can finish after phase closure or navigation; reset and replacement
invalidate obsolete results. An unavailable evaluator produces pending or
unavailable status, never an incorrect-answer verdict.

Keep shared state to phase/control tokens, active/paused flags, inspection cursor,
prediction-release flag, bounded counters, roster page and explicitly
selected/shared snapshots. Update
aggregate categories by subtracting the old contribution and adding the new one;
do not enumerate all actors during a submission or view. Histograms use a finite
set of feedback categories, not unbounded maps of arbitrary guesses.

| Budget | Planned activity target | Host ceiling to preserve |
| --- | ---: | ---: |
| Stored actors | 600 tested target; 1,000 ceiling | 1,000 |
| Complete actor value, with feedback reserved | 3 KiB | 4,096 canonical JSON bytes |
| Roster summary | 256 bytes; 25 rows/page | 512 bytes; 25 rows/page |
| Shared state | 32 KiB | Within the existing 256-KiB complete transition |
| Complete transition | 64 KiB | 256 KiB |
| Any role view | 64 KiB | 128 KiB |
| Engine input / typed data / outcome | Existing bounded engine contract | 2,000 characters / 8 KiB / 12 KiB |

These are proposed budgets to prove with worst-case fixtures, not measurements.
Encode with the host's ASCII-escaped canonical JSON, including keys and version
fields. Keep full traces out of every actor record; retain small repair facts
and certificates. Reserve space before accepting work so completion fits.

Declare broadcast fields for `phase`, `phase_token`, `active`, `paused`,
`cursor`, `prediction_revealed` and `shared`. Participant views omit class counts,
roster and presenter selection; those remain presenter/projector-only. A peer answer must leave
every other participant's projection unchanged. Phase/reveal/cursor changes
reach the class. Add a regression for the FD actor-notification failure that
the current host fixed, rather than relying on a successful small-class demo.

### M3c: explain correctness and validate delivered facts

Prediction feedback identifies correctly predicted objects and remembered-read
mistakes. Diagnosis feedback distinguishes missing/extra direct edges, invalid
witnesses and invalid certificates. Require the complete true edge set, one
valid direct witness per submitted edge, and a certificate checked against the
actual graph. Accept any valid certificate, including isolated vertices in a
topological order; a self-consistent but wrong student graph is insufficient.
Incorrect conflict witnesses or certificates are semantic feedback to withhold
until Reveal; immediate structural errors must not disclose the correct graph.

For repairs, verify returned identities and bounded facts against an independent
Python replay/check of this submission before accepting the verdict. Check final
values, captured reads, direct conflicts and certificate invariants; schema
validity alone is insufficient. Do this on completion, never for every audience
view. Explain valid permutation, program order and acyclicity separately, with
no minimum-edit requirement. Use neutral reason codes localized by the views.

Exit: tests cover closure/submit ordering, lost acknowledgements, two devices,
two presenters, queue-full replacement, repeated retries, navigation, reset,
restart and late results. Role projections and worst-case record budgets pass;
changing one actor cannot invalidate another's edit or publish private facts.

## M4: implement and inspect the four views

Build the usable phone flow alongside the first counter lesson, then extend it
to every fixture. JSON entry is not the finished classroom interface.

- Phone: labelled numeric prediction fields; edge matrix and operation-witness
  selectors; cycle/order builder; operation cards with Move up/down and Insert
  before controls. Dragging may supplement those controls. Expose saved, draft,
  pending, conflict and unavailable states and an explicit retry action.
- Presenter controls: guarded phase transitions/resume, previous/next/jump
  execution steps, counts, pending status, 25-row roster, private selection,
  deliberate anonymous sharing in Reveal, clear sharing and reset.
- Presenter overlay: original problem, shared database, transaction-local reads
  and highlighted current operation; private inspection is clearly separate.
- Projector: readable problem/trace, phase-appropriate aggregates, and only
  explicitly shared anonymous snapshots or revealed worked explanations.

Preserve drafts, focus, text selection and scroll on unrelated updates. Same-actor
device conflicts offer keep/reload choices; reset clears the old-epoch draft.
Use native keyboard controls, 44-CSS-pixel targets, non-color labels, bilingual
messages and reduced motion. Test 320-pixel phones, landscape, zoom, resize,
screen-reader announcements, module failure and static fallback. Inspect actual
screenshots and exercise/solution PDF pages, not only DOM assertions.

Exit: Chrome, Firefox and WebKit complete the full installed-wheel lesson on
ordinary LAN HTTP without relaxing worker CSP. Test real mount/update/dispose,
late imports, peer updates, both conflict paths, sharing/reveal and navigation.

## M5: conformance, scale and operational handoff

Use isolated environments for host-only, coordinate/distance, transaction engine
alone, transaction engine/activity pair, and the full collection. Adding the
activity produces **ten packages, eight engines and eight slide types** from
the current nine-package baseline. Preserve the exact-two-provider smoke tests.

Add dedicated transaction conformance and capacity workflows. Reuse
`maintenance/plugin_worker_security.cjs`, installed-wheel probes and common
server/browser helpers. Record exact host/provider commits, wheel hashes,
payload/schema identities, lockfiles, OS and browser versions. Run authoring
on Windows and Linux with required TeX/font/language dependencies; transfer
identical wheels between platforms and distinguish artifact consumption from
an actual authoring run. Keep engine-only CI independent of lesson failures.

Capacity workloads must include all three answer phases, varied diagnoses and
distinct repairs, then 10% answer replacements, reconnects, two-device conflicts,
presenter loss/replacement, reveal/reset during pending work and a competing
plugin item. Run both a 30-second human-paced wave and a synchronized burst at
600 and 1,000 actors; exercise a full queue and the 1,001st new-actor refusal.
Existing actors must still replace their records at capacity. Include cold and
warm resources; do not turn many copies of one cached repair into a throughput claim.

Proposed acceptance budgets, to freeze before measuring on recorded hardware:

| Measure | 600 students | 1,000-student ceiling |
| --- | ---: | ---: |
| Saved-answer acknowledgement, p95 / maximum | 2 s / 5 s | 3 s / 10 s |
| Phase/cursor/navigation response, p95 / maximum | 1 s / 3 s | 2 s / 5 s |
| Repair feedback after the last submission, healthy evaluator | All current jobs within 60 s | All current jobs within 120 s |
| Correctness and isolation | Every accepted latest answer accounted for; zero lost, duplicate or cross-actor results | Same |

Report p95 and worst-case completion latency, oldest queue age, retries, hook
time, browser/server memory, worker IPC bytes and projection bytes as well.
The completion budgets above are classroom targets, not changes to the host's
two-second per-evaluation or 250-ms hook limits. Record failures with exact
conditions; investigate a host or provider fix before changing a target.
Run the browser/OS matrix explicitly: B+'s Windows WebKit failure near 1,000 is
a risk to reproduce here, not proof that this different workload passes or fails.

Complete the private ZIP/projector-summary checks from M1. Record a short
synthetic screen/window take through TeXStage's existing recording flow and
verify projector overlays, cursor and phase changes in playback. Keep videos,
video scripts, narration and private session archives out of public Git repositories;
commit only the sanitized validation record. No event-replay subsystem is needed.

Finish with real Android and iPhone participation over the intended classroom
network and a keyboard/screen-reader rehearsal. Automated emulation covers
neither those devices nor campus connectivity; retain unrun checks as open gates.

Exit: a dated validation record lists passes, failures and unrun checks against
the final artifacts, with 600-student readiness and 1,000-student support stated
separately. Revalidate affected behavior if any packaged resource changes.

## M6: documentation and reviewed release

Write `docs/transactions-lesson.md` and the package/example READMEs. Explain
installation of the host and both wheels, explicit enablement/locks, authoring,
all phases, feedback meaning, privacy, exports, evaluator failure and recovery.
Include phone/presenter/projector screenshots and the tested browser/capacity
matrix. Update the collection README, database examples and release workflow.
Keep screenshots synthetic; private recordings stay in the media repository.

Run hosted CI against the published exact host commit. Freeze versions and
artifacts before collecting final evidence; retain the independently useful
engine release when its payload is unchanged. Prepare immutable releases and
catalog entries for both providers only after their dependency/compatibility
closure is tested. Preserve older pins and document fresh-environment rollback.
Actual publication follows the user's release instructions; this planning task
does not publish, merge, update courses or replace installed environments.

## Recommended implementation order

1. **Contract and authoring:** M0 and M3a, with the independent model, prepared
   counter and installed-wheel live/static checks. This is the next concrete task.
2. **Classroom protocol:** M3b/M3c, actor records, private feedback and race tests.
3. **Complete user interface:** M4, all five synthetic lessons and both languages.
4. **Scale and archive integration:** M1's remaining generic work plus M5 load,
   recovery, privacy and recording checks; re-pin the host if it changes.
5. **Release candidate:** final hosted matrix, real-device rehearsal and M6 docs,
   immutable artifacts and catalog preparation.

Each step should produce a reviewable commit with its evidence. Completing the
first counter slice establishes a working foundation; the full lesson, measured
capacity and publication gates remain explicit until their own checks pass.

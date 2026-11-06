# Transaction-schedule plugin: implementation plan

This is the implementation backlog for the
[activity design](transaction-schedules.md). M2's independent analysis engine
is implemented; the transaction lesson package is not yet implemented.

Progress: the matching local host branch now implements typed engine results,
revision-2 result/view schemas, epoch-guarded reset and actor-scoped evaluation
correlations. Generic contract tests exercise phase/control/answer guards.
The H2 follow-up now implements preparation before TeX and local static exports.
M2 now provides a portable engine wheel, typed results and installed-wheel
checks against the independent oracle. The lesson package, editable interfaces
and capacity work remain open. Publishing and pinning a compatible host/collection pair in CI remains an
M0 gate; local test evidence does not substitute for that hosted run.

## Delivery boundaries

Keep work on feature branches in the active Texstage code checkout and this
collection. GitHub and GitLab mirror that one code history; the legacy checkout
is archived. Private narration and video belong in the separate private
texstage-media repository. Do not edit lecture-tools,
lecture-tools-next, existing course sources, submodules, tool pins or installed
course environments. Course adoption is a later, separately rehearsed change.

New examples are synthetic. Course chapter/frame references below identify
possible insertion points without redistributing existing lecture material.
Do not add either transaction package to the catalog until a reviewed wheel is
published and the acceptance checks pass.

## M0: specification and compatibility baseline

Deliverables in this design change:

- The interaction/state model and host review TS-01 through TS-09.
- An exercise schema, newly authored counter example, expected conformance cases,
  and an independent mathematical design checker.
- Explicit boundaries between host mechanisms and transaction-specific behavior.

Next implementation work:

- Publish the compatible host branch, pin its exact commit for collection CI,
  and record the actual host/fixture wheels used by each run.
- Keep the existing coordinate/distance installed-wheel tests and legacy
  no-plugin checks as regression gates.
- Define the complete manifest-revision-2 and engine-result schemas before
  implementing a renderer against them.

Exit: the current prototype has a reproducible green baseline, and schema
fixtures distinguish existing revision-1 providers from new revision-2 providers.
The design checker passing alone does not satisfy this exit.

## M1: implement the host prerequisites

| Work | Texstage files/components | Required test |
| --- | --- | --- |
| Typed result facts | `plugins/schemas/`, `plugins/manifest.py`, `plugin_api/v1/`, `web/stage/plugin-evaluator*.js`, `plugins/runtime.py` | Data survives all boundaries; undeclared, malformed, mismatched and oversized data is rejected |
| Preparation before compilation | `build/builder.py`, a generic authoring-preparation module, `build/plugins.py`, `build/latex.py`, `cli.py`, `latex/texstage.sty`, SDK/worker contracts | One exercise produces matching live, handout, solutions and PowerPoint artifacts; stale inputs and private leaks fail |
| Semantic concurrency and reset | `plugins/runtime.py`, SDK documentation and contract fixtures | Unrelated submissions do not stale presenter controls; same-answer conflicts do; reset replay increments epoch once |
| Editable renderer contract | `web/shared/plugins.js`, SDK examples | Focus/drafts survive ordinary updates; obsolete mounts disappear; terminal receipts remain inspectable |
| Capacity and status | `server/plugins.py`, publication scheduling, `plugins/runtime.py`, `plugins/worker.py`, presenter dispatcher | Fair bounded queues, pending status, batch projections and responsive navigation under load |
| Worker module compatibility | `server/app.py` static worker policy and `web/stage/plugin-evaluator-worker.js` | The real evaluator starts in Chromium, Firefox and WebKit while preserving network and worker restrictions |

Worker module compatibility is now verified locally for both database engines
and the original example pair; see the [compatibility record](worker-browser-compatibility.md).
Other classroom host gates remain open.

Paths in the table are relative to `src/texstage/`, except the LaTeX file.
Extend existing mechanisms; no transaction-specific core modules or routes.
Preserve API facade laziness, built-in SQL read-only behavior, formats 1/2,
existing revision-1 provider discovery, and explicit enablement.

The reset behavior and typed-data transport are implemented in the matching H1
host checkout. Its runtime fingerprint includes the changed contract revision.
Build and install that wheel in a new environment; a package-version constraint
alone does not identify unpublished changes sharing a development version.
H2 now supplies `--activities`, `PreparedAuthoring`, source/asset identity
checks and direct-pdfLaTeX exports. A synthetic installed-wheel fixture
verifies matching live, handout, solutions and static PowerPoint outputs;
it is not a transaction implementation. Capacity and editable-view work
still require implementation. M2 is implemented below; M3 is the next package milestone.

## M2: implement the independent analysis engine

Implemented files:

```text
plugins/transaction-engine/
  pyproject.toml
  MANIFEST.in
  texstage-plugin.json
  texstage_transaction_engine/
    __init__.py
    web/schedule.mjs
    web/identity.mjs
    schemas/exercise-v1.json
    schemas/analysis-result.json
    schemas/order-input.json
    fixtures/
  tests/
```

The engine parses bounded JSON orders, validates them against its fixed seed,
simulates captured reads and writes, derives direct conflicts, and produces a
cycle or topological certificate. It has no network access, native binary,
LaTeX style, student identity or session-state authority.

Canonicalize object keys, edge/witness ordering and certificate selection.
Include exercise identity and normalized submitted order; omit UI language,
actor IDs, timestamps and job IDs from canonical output. Different valid repairs
may have different canonical results.

Exit: installed portable wheel and source-distribution parity; all expected
cases; every small legal interleaving; read/write and write/write edge cases;
invalid permutations, unknown IDs and program-order violations; bounded
oversized-input behavior; fresh-state and timeout checks.

Local evidence: 67 installed-engine tests cover nine hand-checked cases, all
1,742 legal interleavings of six programs, seed/answer validation, independent
trace replay, maximum-size result budgets and semantic identity without
WebCrypto. The portable wheel's resource inventory matches its sdist rebuild.
The engine runs through the actual installed host evaluator and result
validators. The original coordinate/distance exact-provider test suite remains
unchanged and passes in a separate installation scenario.

See the [engine README](../../plugins/transaction-engine/README.md) for commands
and [M2 validation record](transaction-engine-m2-validation.md) for artifact
identities and the scope of local evidence. The next step is M3 authoring and
lesson state, followed by M4 interfaces. No transaction LaTeX command or phone
activity is available from this engine-only wheel.

## M3: implement authoring and lesson state

Proposed files:

```text
plugins/transaction-activity/
  pyproject.toml
  MANIFEST.in
  texstage-plugin.json
  texstage_transaction_activity/
    __init__.py
    authoring.py
    model.py
    state.py
    schemas/
    latex/texstage-transactions-schedule.sty
    templates/
    locales/de.json
    locales/en.json
    web/
  tests/
examples/transactions/
  lesson.tex
  lesson.activities.json
  activities/counter.exercise.json
```

The Python model prepares a static oracle for the original schedule; the
independent browser engine evaluates repair candidates. Compare both against
hand-checked expected facts and exhaustive small cases. Do not call one
implementation's output an independent oracle for the other.

Implement phase/control/answer versions, one saved answer per actor per phase,
canonical answer normalization, durable evaluation correlations and staged
privacy. A closed phase retains accepted pending work. Superseded answers and
old epochs cannot receive late feedback.

Exit: state-machine tests for closure, retries, same-actor/device conflicts,
two presenters, reset, navigation away/back and out-of-order completions.
The state-size budget holds for the declared participant limit.

## M4: implement the four interfaces

Use separate `presenter-overlay.mjs`, `presenter-controls.mjs`,
`projector-overlay.mjs` and `participant.mjs`, sharing only pure layout/formatting
helpers. Modules may be consolidated later if independent mount tests still pass.

Build the phone interaction first: numeric prediction, edge/witness selectors,
certificate input and accessible operation reordering. Then implement the shared
trace and projector summaries. Test ordinary updates while editing before
polishing animation; they must not destroy the student's draft or focus.

Exit: Chromium, Firefox and WebKit on actual installed wheels; 320-pixel phone,
keyboard-only and touch operation, German/English labels, resize/zoom,
reduced motion and useful fallback after renderer failure. Record exact browser
versions. Browser emulation does not by itself prove physical-phone usability:
rehearse on at least one real phone over ordinary classroom LAN HTTP.

## M5: conformance, capacity and export

Extend collection tests rather than weakening the original two-package fixture
gate. Update the wheel builder and CI to use isolated installation scenarios:
host alone, coordinate/distance pair, transaction pair, and all four providers.
Do not make the existing exact-provider-set test pass by silently disabling it.
The combined scenario must check namespace collisions and explicit profile pins.
Verify at least:

1. Two different valid repairs succeed; an interleaved acyclic repair succeeds.
   Matching a final database state never substitutes for the CSR criterion.
2. One direct edge with multiple conflict witnesses is represented once; an
   unsupported transitive edge is rejected. Isolated graph vertices remain.
3. One user's stale replacement cannot overwrite another device's newer answer.
   Other users' updates do not invalidate the presenter's phase/cursor action.
4. Close/submit, reset/result and completion/replacement races have reproducible
   results; a lost acknowledgement never creates another logical attempt.
5. Unrevealed answers and participant identifiers stay out of projector/public
   views. A participant cannot forge presenter commands or evaluator results.
6. No evaluator and evaluator replacement produce pending/retry behavior, not
   incorrect-answer feedback. One actor cannot monopolize the queue.
7. The proposed 200-participant workload meets measured limits or has an explicit
   revised capacity limit before a pilot. Record p95 and worst-case latency,
   memory, queue age, state bytes and worker IPC volume.
8. Build on Windows and serve on Linux, then reverse, using identical provider
   wheel bytes. Check handout, solutions, live browser and static PowerPoint.
9. Private archive and sanitized public summary retain the intended facts.
   A real screen/window recording includes the selected projector's plugin
   overlay and cursor/phase changes; no new event-replay subsystem is required.
10. Disabled providers are never imported; schema/asset changes invalidate pins;
    old environments remain available for rollback.

Publish a conformance report tied to exact host and plugin artifacts. Only then
prepare reviewed per-package releases and immutable catalog entries.

## Course adoption after the package gate

| Candidate DBIS2027 location | Use |
| --- | --- |
| Chapter 7, around frames 012 and 018–024 | Predict and inspect a lost update; distinguish final values from a structural test |
| Chapter 7, around frames 030–039 | Build direct conflict edges and a cycle/topological certificate |
| Chapter 7, around frame 042 | Discuss what a negative CSR result does and does not establish |
| Later sessions on locking and recovery | Separate future activities; not additional modes hidden inside this first release |

First rehearse a newly authored demonstration deck, then a disposable course
copy with unchanged source originals. Lecture-tools may forward the generic
authoring option once the host exposes it; it must not copy plugin styles into
its verified core-style snapshot. Adoption into the actual course remains a
separate requested change.

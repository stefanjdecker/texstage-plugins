# ER Modelling Decisions: implementation plan

Status: registration slice of E0/E1 implemented, 2026-11-06. Four frozen
schemas, a browser engine, independent Python oracle, portable wheel and
installed-host browser checks now exist. See the
[runtime contract](er-registration-engine-contract.md) and
[validation record](er-registration-engine-validation.md).
The registration slice of E2 now adds prepared authoring, a thin style, bilingual
exercise/solution material and a static live fallback. See the
[authoring guide](../er-decisions-authoring.md) and
[E2 validation](er-prepared-authoring-validation.md).
The registration E3 state protocol is also implemented; see the
[state contract](../er-decisions-state.md) and [validation](er-lesson-state-validation.md).
The registration E4 pilot is implemented in provider 0.4.0; see the
[classroom guide](../er-decisions-lesson.md) and [E4 validation](er-lesson-ui-validation.md).
The 0.4.1 patch adds field-error/focus handling, stable live messages and
English/German keyboard/accessibility-tree checks; see the
[accessibility record](er-accessibility-validation.md). The engine profile and
state schema are unchanged.
E5 now includes synthetic classroom/recovery measurements, portable consumers
and an isolated CI workflow; the measured pilot is 32 simultaneous answers.
Physical-device and screen-reader checks, hosted CI and release approval remain
open, as does the broader engine scope (identification and assumptions).
The [design](er-modelling-decisions.md) and
[target lesson contract](er-modelling-decisions-contract.md) retain the full scope.

## Scope and sequence

Implement in the active `texstage-plugins` repository. Integrate against the
active `texstage-public` host checkout and an isolated plugin profile. Keep
original lecture-tools, existing courses, their pins/environments and private
media unchanged. Do not change lecture-tools-next to install this plugin.
Do not publish a catalog entry or push a release as part of design work.

The first implementation slice is **workshop registrations end to end**:
cardinality, status ownership and relationship/association-entity choice.
It must accept both intended alternatives and explain a concrete failure.
Then extend the same mechanism to scoped room identity and the ambiguous
mentoring requirement. Neither transaction-lesson completion nor relational
visual-editor completion is a prerequisite.

`E0 → E1 → E2 → E3 → E4 → E5`. Pure model/schema work precedes UI.
An engine-only E1 is not a usable classroom plugin; E4 supplies the usable
pilot, and E5 provides release evidence.

## File ownership

The engine package, its model/answer/exercise/analysis schemas, Python oracle,
browser modules, fixture, tests, probe, browser harness and bundler entry now
exist. The prepared lesson-v1 envelope, authoring module, style, transparent
overlays and bilingual example deck also exist. The versioned registration state protocol and four audience projections now
exist. Interactive renderers now exist; release/CI work remains pending.

| Repository/path | Work |
| --- | --- |
| Collection `docs/design/er-modelling-decisions*.md` | Design, contract, plan (created for design) |
| Collection `docs/design/er-modelling-decisions/` | Three synthetic fixtures, hand expectations and finite validation record (created for design) |
| Collection `maintenance/check_er_design.py` | Independent trusted-fixture checker (created for design) |
| Collection `plugins/er-decisions/pyproject.toml`, `MANIFEST.in`, `LICENSE`, `README.md`, `texstage-plugin.json` | Independently buildable provider, manifest revision 2 |
| `plugins/er-decisions/texstage_er_decisions/__init__.py` | Factory registering authoring/state hooks |
| Same package: `model.py`, `authoring.py`, `state.py` | Independent Python model; source compilation; lesson state/projections |
| Same package: `schemas/lesson-v1.json`, `model-v1.json`, `answer-v1.json`, `analysis-v1.json`, `commands/`, `views/` | Source/semantic, answer, typed-result and all role contracts |
| Same package: `web/model.mjs`, `validation.mjs`, `identity.mjs`, `engine.mjs`, `engine.worker.mjs` | Pure browser evaluator and committed self-contained worker |
| Same package: `web/decision-editor.mjs`, `diagram.mjs`, `participant.mjs`, `presenter-controls.mjs`, `lesson-overlay.mjs` | Accessible cards, diagram/text view and four renderer surfaces |
| Same package: `latex/texstage-er-decisions.sty`, `templates/`, `locales/en.json`, `locales/de.json` | Prepared wrapper, static output and language resources |
| `plugins/er-decisions/tests/` | Model, authoring, state, privacy and boundary tests |
| Collection `examples/er-decisions/lesson.tex`, `lesson.activities.json`, `activities/` | Synthetic demonstration deck from the same source |
| Collection `maintenance/er_probe.py`, `er_browser.cjs`, `er_lesson_browser.cjs` | Installed-wheel evaluator, security and classroom harness |
| Collection `maintenance/build_worker_modules.cjs` | Register owned engine entry; existing locked bundler generates bundle |
| Collection `maintenance/build_wheels.py`, `.github/workflows/` | Isolated ER build/conformance scenario; retain existing exact-provider scenarios |
| Collection `docs/er-decisions-lesson.md`, `docs/design/er-decisions-validation.{md,json}`, `README.md` | Install/author/use guide and exact-artifact evidence |
| Host `docs/plugins.md` / architecture design | Optional link/status update once usable; no ER semantics |

No host code change is currently planned. Reuse SDK prepared authoring, typed
facts/view schemas, structured errors, receipts/epochs and renderer lifecycle.
If integration exposes a generic defect, record it with a minimal failing
case, fix it in the host separately and test the existing providers too.

## E0 — freeze the model and evidence contract

Registration status: complete for the bounded engine profile. Four schemas
pass the portable profile; malformed-source/answer and serialized result gates
are covered. This does not close the later lesson/view/state budgets or the
fourth identification slot/open-requirement design.

Inputs: the attached draft contract and finite fixtures.

1. Freeze source, model, answer and fact schemas, with the four typed slots
   and one optional open requirement. Specify reification/attribute placement
   composition exactly; no ad hoc executable predicates.
2. Implement semantic validation of IDs, ownership, uniqueness, endpoints and
   all option combinations, with bounded work. Well-formed negative teaching
   snapshots must be retained.
3. Add formal constraints and diagram sentences generated from one compiled
   model. Make min/max endpoint orientation explicit in both representations.
4. Enumerate finite variants, check worked alternatives, and inspect each
   hidden example against the publicly stated facts. A contradictory fixture
   or alternative stops preparation.
5. Construct worst-case ASCII-escaped result/view/state/effect payloads and
   run both host schema validators. Retain or reduce the proposed provider
   caps based on measurements, without raising core limits.

Exit: schemas accepted by the matching installed host, reproducible independent
expected cases, all source options meaningful, documented static/layout rules,
and measured serialized caps. Today's design checker is only the starting
semantic evidence; it does not close E0.

## E1 — implement and package the model engine

Registration status: implemented and tested from an installed wheel. Both
intended models and the hand-derived failures agree with the independent oracle;
all three browsers retain the production worker restrictions. Room identity
and mentoring assumptions are explicitly rejected by this first profile.

Implement the pure JS model compiler/evaluator and an independent Python model.
Start with registrations, then rooms and mentoring. Verify uniqueness, role
degree including zero links, attribute functional dependencies, explicit
assumption profiles and exact witness coverage.

Use fresh-per-submission engine state. Return typed findings and deterministic
identities, not a reference-equality grade. Include malformed JSON/duplicates,
unknown IDs, invalid types, integer/boolean distinctions, NFC/non-BMP text,
excessive sizes and crafted incomplete result cases.

Build wheel + sdist; install only the intended provider into a fresh environment.
Register the engine with the locked worker bundler; ship generated bytes and
verify they match source. Record compatible host commit plus wheel/payload
hashes, rather than relying on its shared development version string.

Exit:

- Browser and independent Python results agree on all attached combinations.
- At least two different passing registration models and two room models
  retain distinct canonical identities.
- Wrong models produce reproducible allowed/forbidden witnesses.
- Assumptions cannot override fixed facts, and unresolved checks are not passes.
- Chrome, Firefox and WebKit evaluate through the actual host worker with
  unchanged production CSP and active blocked-network/child-worker probes.
- Timeout, invalid result, teardown and next-job recovery work.

## E2 — prepare authoring and static editions

Registration status: implemented in provider 0.2.0. The bounded lesson-v1
envelope wraps the unchanged registration engine seed; it is not the broader
target lesson schema. Read-only state and transparent mandatory overlays
satisfy the host content contract while retaining the exercise slide.
The declared style namespace is `er`, exporting `\erdecisions`.
Rooms and mentoring remain deferred until their engine profiles exist.

Add the authoring hook, declared style and example deck. One source generates
the live task, fixed private binding, exercise fragment and worked alternatives.
Check worked answers independently during preparation. Build public/private
projections before rendering; no private data becomes a public preview asset.

Use deterministic small-diagram layouts and a textual fallback. Verify changed
source/asset/profile freshness, plain-text escaping, source confinement and
missing/disabled plugin diagnostics. Document explicit installation/enablement
and separate profile/lock setup; no slide-triggered installation.

Exit: registration, rooms and mentoring render legibly in live material,
handout, solutions and static PowerPoint. Inspect rendered exercise and solution
pages, including long German labels and min/max orientation. Direct-pdfLaTeX
exports follow the existing local-export contract. No raw preparation folder
is advertised as a public student bundle.

## E3 — implement lesson state and role projections

Registration status: implemented in provider 0.3.0, state schema 2. Authenticated
commands, per-actor versions, pinned selection/sharing, explicit rationale
release, paged summaries and compact independently checked feedback are tested.
64-slot storage and serialized budgets are measured; this is not classroom
throughput or phone-UI evidence. Rationale also has a 1,280-byte ASCII-JSON cap.

Add introduce/open/closed/revealed phases, actor answer versions and separate
phase/control versions. Use host effects and correlation helpers. Store
compact selected option IDs/findings, not repeated models or full traces.

Cover concurrent participants, two tabs for one actor, stale controls,
duplicate receipts, lost ACK/retry, replacement at a full pending queue,
close while pending, reveal while pending, reset and stale result delivery.
Retain drafts on structured operational errors. New-actor capacity refusals
must not block an existing actor replacing their answer.

Exit: closed schemas for all four views, no leakage before/after reveal or
through anonymous sharing, exact result-coverage checks, and measured
worst-case transition/view sizes within E0 caps. Record whether old UI drafts
are retained or explicitly discarded on navigation; never auto-submit them.

## E4 — deliver the complete phone/presenter pilot

Registration status: implemented in provider 0.4.0. Decision cards, preview,
explicit saving/repair, private inspection, paging, optional rationale release
and projected alternatives are present in English/German. Existing E3 guards
and state schema 2 are retained. The registration profile has no assumptions,
so its editor deliberately supplies no assumption controls. Browser emulation
does not establish physical-phone, screen-reader or class-load performance.

For the broader profiles, build decision cards, assumption controls, explicit submit and repair workflow,
live diagram plus accessible constraint list, and useful status/feedback.
Provide “View model” and “Back to decisions” without losing progress.
One response card should explain the consequence of a choice, not display
internal schema names.

Presenter controls need open/close/reveal/reset, option counts, paged inspection,
explicit anonymous sharing and clearing. Projector static fallback stays useful
when the renderer/evaluator is unavailable. Worked alternatives and approved
witnesses support the discussion; do not expose every private check.

Exit: real server + installed wheel + real presenter/projector/two-phone
workflow passes in Chrome, Firefox and WebKit at 320 CSS pixels. Verify
keyboard-only operation, tap controls after actionability checks, visible
focus, resize/zoom, dirty-draft conflicts and reset in an existing mount.
Inspect actual screenshots and static pages; DOM text checks alone are
insufficient. A new reader can explain which entity each bound describes.

## E5 — measure and release

Automated registration progress: a reproducible synthetic 64-actor load and
disconnect-recovery harness, identical-wheel Windows/Linux consumer checks,
an isolated, immutable-host-input CI workflow, and 0.4.1 keyboard/accessibility
regressions are implemented. Native 200% Chrome zoom now passes in both languages,
including scrolled inspection controls and projected alternatives. The newer
host snapshot also passes the local 64-actor latency target; the documented
pilot remains 32 pending deployment/hosted checks. See the
[release checklist](../er-decisions-release.md) and
[measurement record](er-release-readiness-validation.md) and
[current-host/zoom follow-up](er-native-zoom-validation.md). Physical phones,
screen-reader review, actual deployment measurements and a hosted workflow
run with a published compatible host commit remain open; E5 is not complete.

Run conformance with all existing example providers as regressions, retaining
their independent exact-provider fixtures. Run the host's relevant tests if
generic integration changed. Add an ER CI job using an explicit available host
artifact; a local unpublished dependency cannot be labelled a passing public CI
installation.

Measure on recorded hardware/browser versions:

- 64 nearly simultaneous responding actors, replacements and queue contention;
  warm target p95 feedback within 10 seconds and last feedback within 30 seconds.
  Report cold startup separately. These thresholds are release targets; see
  the measurement record for current results and the reduced 32-actor pilot.
- Actual state/result/view bytes and worst-case authoring/evaluation time.
- Fairness/recovery when a presenter disconnects or worker evaluation fails.
- At least one physical Android and iOS phone; keyboard and screen-reader
  review of cards, diagram alternative and feedback.
- Portable wheel installation on a clean Windows and Linux environment,
  source/wheel/sdist inventory parity, lock reproducibility and static outputs.

If a target fails, fix it or reduce and document the supported pilot size;
do not weaken security or silently expand core budgets. Publish a guide with
explicit finite-check limits and unmet gates.

Exit: reviewed immutable artifacts, released compatible host pin, reproducible
evidence and approved catalog metadata. Release publication is a separate
action; this plan does not perform it.

## Immediate next implementation step

Complete the remaining registration release gates: physical Android/iOS and
screen-reader review, deployment-hardware load measurements, and a hosted ER
workflow run after publishing a reviewed compatible host commit. Review the
recorded artifact hashes and unmet limits before any catalog/release publication.

Extend the engine to owner/scoped identity and open assumptions under explicit
new profiles when implementing those later scenarios. Do not quietly broaden
the frozen registration-v1 format or describe the current engine as the
complete ER classroom plugin.

## 600-student follow-up (2026-11-07)

ER 0.5.0 / state schema 3 replaces the 64-entry whole-class map with host-owned
bounded records and constant-size aggregates. TeXStage 0.2.1.dev4 supplies atomic
record effects, bounded record reads/pages, actor-scoped participant updates and
opt-in deterministic result reuse. The lesson admits 600 distinct answering
actors and still permits replacement at capacity. All 27 registration answer
combinations, a full replacement wave, reset, disconnected evaluator recovery,
receipt replay and 601st-actor refusal belong to the capacity gate. The warm
p95 ≤10 s / last answer ≤30 s targets and worker restrictions are unchanged.
See [current validation](er-600-validation.md); actual teaching host/LAN,
physical phones, screen-reader output and hosted CI remain separate gates.

## Points integration (2026-11-07)

ER 0.6.0 / state schema 4 connects verified whole-model outcomes to the host's
fixed points ledger. Optional source `points` (0–10000, default 0) selects the
maximum. Either accepted model earns full credit; contradictions earn zero;
unavailable or unverified evaluation receives no correctness award. Reveal
publishes credit, replacing an answer replaces private credit, and reset
withdraws this activity's previous contribution. Scored rounds require reset
after reveal; practice rounds retain reopening and repair.

Manifest revision 4 retains bounded item records, actor-scoped updates and
deterministic result reuse. The matching development host also avoids repeated
strict checks of unchanged prepared data and identical view JSON, while still
running each authenticated view hook and retaining bounded caches. The schema
generator now reproduces the 600-student and points contracts without downgrades.

The [points validation](er-points-validation.md) records exact artifacts, real
English/German phone flows, CSV/ranking checks and scored 600-actor measurements.
Capacity correctness and latency are separate gates: retain failed timing runs
in that record and do not claim deployment readiness from a passing rerun.

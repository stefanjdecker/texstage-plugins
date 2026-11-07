# Normalization Workshop: implementation plan

Status: N1–N3 and the N4 comparison/evidence slice implemented locally.
Version 0.4.0 adds bounded item records and paginated state/views v3 for a
600-student target and 1,000-answer ceiling. The nineteen old schemas remain
unchanged. See the [capacity record](normalization-workshop-600-validation.md)
for the exact host/provider artifacts and measured coverage.
See the [workshop guide](../normalization-workshop.md),
[N4 evidence](normalization-workshop-n4-validation.md),
[discussion contract](normalization-workshop-discussion-contract.md), earlier
[N3 evidence](normalization-workshop-n3-validation.md) and
[N1/N2 evidence](normalization-workshop-n2-validation.md).
Full usability, hosted CI and classroom/release gates remain open.

## Repository boundaries and dependency order

All normalization-specific work belongs in `texstage-plugins`. The active
Texstage code checkout is `texstage-public`; its GitHub/GitLab repositories mirror
one code history. Only demonstrated generic defects belong there. Existing
`lecture-tools`, `lecture-tools-next`, course repositories, installed course
environments, archived host checkouts and private media remain unchanged.

Use the existing host at the exact development revision recorded in the draft
contract for local work. Publish only against a reviewed compatible host artifact.
A package version such as `0.2.1.dev3` alone does not identify unpublished host
changes. Neither a new catalog entry nor course migration is part of this plan's
design delivery.

Dependency order: **N0 design -> N1 contracts -> N2 engine -> N3 authoring/state ->
N4 usable UI -> N5 artifact/browser verification -> N6 classroom pilot/release.**
N3's authoring and state work can be developed alongside each other after N2;
N4 requires their stable contracts. Pure-engine success does not close N4–N6.

## Intended files

| Repository location | Purpose / milestone |
| --- | --- |
| `docs/design/normalization-workshop.md` | Product and teaching design (N0) |
| `docs/design/normalization-workshop-contract.md` | Draft finite model, wire/state decisions (N0/N1) |
| `docs/design/normalization-workshop-plan.md` | This plan and release gates (N0) |
| `docs/design/normalization-workshop/` | Draft lessons, independent expected cases, validation record (N0) |
| `maintenance/check_normalization_design.py` | Standard-library specification aid (N0), not runtime engine |
| `plugins/normalization-workshop/pyproject.toml, MANIFEST.in, LICENSE, README.md` | Independent portable package (N1/N2) |
| `plugins/normalization-workshop/texstage-plugin.json` | Manifest v2, capabilities, resource inventory via SDK (N1) |
| `plugins/normalization-workshop/texstage_normalization_workshop/__init__.py` | Factory registration (N2/N3) |
| `…/model.py` | Independent Python semantics for preparation and tests (N2) |
| `…/validation.py, schemas/` | Seed, lesson, answer, analysis, command and four view schemas (N1/N2) |
| `…/authoring.py, state.py` | One-source preparation, bounded reducer and projections (N3) |
| `…/latex/texstage-normalization-workshop.sty, templates/, locales/en.json, locales/de.json` | Wrapper, static exercise/solution layout, localized text (N3/N4) |
| `…/web/fd.mjs, chase.mjs, identity.mjs, validation.mjs` | Owned pure engine modules (N2) |
| `…/web/engine.mjs, engine.worker.mjs` | API lifecycle and generated self-contained worker (N2) |
| `…/web/attribute-picker.mjs, relation-cards.mjs, participant.mjs` | Keyboard/touch workshop controls (N4) |
| `…/web/presenter-controls.mjs, lesson-overlay.mjs` | Presenter inspection, explicit share and reveal (N4) |
| `plugins/normalization-workshop/tests/` | Domain, state, installed-artifact and authoring tests (N2–N5) |
| `examples/normalization/lesson.tex, lesson.activities.json, activities/` | Executable synthetic workshop deck (N3/N4) |
| `maintenance/normalization_probe.py, normalization_browser.cjs` | Installed engine and classroom-flow probes (N5) |
| `maintenance/build_worker_modules.cjs`; `package.json` | Add owned worker to existing reproducible bundling (N2) |
| `docs/normalization-workshop.md`, `README.md` | User guide, installation and example navigation (N4/N5) |
| Existing CI and catalog files | Extend isolated scenario and reviewed release metadata only at N5/N6 |

The ellipsis means the `texstage_normalization_workshop` package directory, not
a second top-level path. Do not copy host private internals or import sibling provider browser modules.
The [FD Lab proposal](functional-dependencies.md) supplies the separate foundation
activities; this package assesses only classification and decomposition. Plan an
optional combined deck after both providers exist. Standalone warm-up slides
remain static, so FD Lab is not a hard implementation dependency.

## N0 — review the design (completed)

Deliver the public proposal, draft source examples and independent expected
facts. Run the finite checker for closures, all keys, forms, projected
dependencies, binary/multiway losslessness and counterexamples.

Exit: course-registration and trade-off scenarios have correct hand-derived
answers; cases distinguish coverage, normal form, losslessness and preservation.
The record says exactly what was checked. No placeholders masquerade as an
installable plugin. Link from the collection README.

The checker is deliberately a specification aid on trusted fixtures. It is not
the production parser, hostile-input validator, timing benchmark or browser test.

## N1 — freeze schemas and resource budgets (implemented)

Specify closed schemas and semantic validation for the author envelope, compiled
seed, two answer variants, typed facts, commands, state and four role views.
Validate result/view schemas with the actual host portable profile; source and
server command schemas have different capabilities.

Freeze symbol IDs, canonicalization, task acceptance criteria, failure statuses,
certificate representation, compact persisted feedback and actor limits.
Keep localized strings outside mathematical identities. Reject duplicate JSON
keys, non-finite values, implicit coercion, unknown IDs, contradictory mode
selection, oversized input and unexpected fields. Empty determinants and the
empty key need intentional UI/schema support.

Exit:

- Maximal schema-shaped answer, result/outcome, actor slots, full state, transition
  and views serialize below the draft limits using canonical ASCII escaping.
- A 70-key analysis result and an 8-component, 8-attribute, 56-merge certificate fit.
- There is a concrete bounded verifier for facts used by the reducer and a plan
  to fit the 250-ms hook deadline. No claim based only on schema-valid flags.
- Task policy prevents impossible required worked answers: preparation will reject
  them. BCNF without required preservation reports the trade-off explicitly.
- The engine-only manifest and coexistence with existing providers pass
  discovery/collision checks. Reserved lesson schemas do not advertise a working
  normalization content capability.

## N2 — implement and verify the engine (implemented)

Implement independent Python and JavaScript models. Reuse the fixtures and
mathematical expectations, not the design checker's implementation as both
oracles. Add deterministic work counters, portable content identities, fresh
evaluation state and disposal. Generate the self-contained worker using the
existing locked bundler. Never widen CSP for a module import.

Exit:

- Closures are extensive, monotone and idempotent; equivalent FD sets give the
  same mathematical facts. Attribute permutations preserve renamed semantics.
- Exhaustive three-attribute FD-set comparisons plus seeded larger cases cross-check
  Python/JS keys, forms and preservation; all keys are superkeys and minimal,
  and every superkey contains a reported key.
- Explicit projected-FD enumeration agrees with projected-closure preservation.
  Implied FDs absent from the written list are covered in component checks.
- Every binary chase agrees with the independent intersection criterion.
  Multiway fixtures include lossless and lossy outcomes. Every displayed losing
  tableau is separately verified as a legal counterexample.
- Include no FDs, trivial/redundant FDs, cycles, empty determinants/keys,
  multiple candidate keys, missing/duplicate components, contained components,
  order variations and alternate valid answers.
- Both installed Python and actual browser contract validators accept bounded
  facts and reject deliberately malformed/oversized/foreign-mode facts.
- Worst supported inputs complete within the 2-s deadline; operational refusal
  is separate from incorrect answers. No partial result is labeled a proof.

Deliver an engine-only usable capability and validation record. State explicitly
that this milestone supplies no phone lesson or LaTeX workshop yet.

## N3 — prepared authoring and classroom state (implemented)

Build the authoring hook, wrapper style and exercise/solution fragments. Start
with one decomposition item and expand to both task modes. Derive static
facts independently; reject a wrong worked answer. Reuse current confinement,
preparation identity and freshness checks.

Implement phases, actor-local answer versions, control guards, typed evaluation
effects, explicit reveal/share and compact state. Keep each workshop slide
independent. Choose a single selected-answer analysis path within measured hook
budgets; never recompute every student's chase in view generation.

Exit:

- Same source builds live, stage, handout, solutions, static PPT and local
  direct-pdfLaTeX exports. Changed source forces regeneration.
- Delayed feedback, private worked answer and other students' submissions are
  absent from unauthorized transport before release; inspect payloads.
- Retry, two devices for one actor, two presenters, close while pending, reopen,
  reset during evaluation, stale completion and missing evaluator are tested.
- Replacement at host queue capacity works atomically; actor 65 is refused
  gracefully while an existing actor can replace. Slot budgets reserve feedback.
- Dirty drafts and server-saved answers are distinct; saved work survives
  navigation, and old drafts never auto-submit after reset.
- Original coordinate/distance, transaction and relational scenarios still pass
  in their isolated environments.

## N4 — deliver a usable workshop, not a JSON prototype (partly implemented)

Delivered: native editing, private and explicitly shared two-answer comparison,
saved-version evidence, replayable chase, verified spurious tuple and lost-FD
tables. Schema v2 records sharing intent and bounded pairs; v1 remains frozen.
The 0.3.1 accessibility slice adds German keyboard flows, native 200% Chrome
zoom, language/attribute descriptions and focus recovery. Generic host fixes
supply phone language and leave keyboard events to interactive controls.
See [accessibility evidence](normalization-workshop-accessibility-validation.md).
Human screen-reader and learner acceptance remain open.

Implement attribute pickers, relation cards, witness selectors and readable
feedback. Build the seven-step example sequence described in the design,
including introductory/discussion slides around the two task modes. A short
guide must explain what this plugin teaches, installation/enabling/pinning,
author source format, all commands, how to run a session and how to export.

Exit: all interactions work with keyboard only and touch at 320 CSS pixels;
English and German labels fit; focus/drafts survive updates and reconnects.
Compare two valid decompositions side by side in presenter discussion. Show a
lost FD separately from a spurious joined tuple. Formula/table text remains
legible in actual rendered exercise and solution PDF pages. Neither color nor
dragging is necessary. The initial interface is already a workshop; advanced
visual arrows are optional later work.

## N5 — portable artifact and browser gates

Build wheel/sdist from finalized bytes, check resource inventory and sdist
rebuild parity, install into clean disposable environments. Record exact host
commit/artifact, plugin wheel/payload/schema hashes, dependency lock and commands.
Keep original two-provider discovery tests unchanged; add separate normalization
and combined-provider scenarios.

Run actual-host engine and UI probes in Chromium, Firefox and WebKit under the
unchanged production CSP. Run the existing active security probes for fetch,
XHR, sockets, external modules, dynamic evaluation and child workers. Check
invalid result rejection, timeout cleanup and subsequent recovery. Ordinary LAN
HTTP must work without requiring `crypto.subtle`.

Exit: installed-wheel tests, both modes, same-actor conflicts, reveal/share
privacy and lifecycle checks pass in all three engines. Inspect screenshots and
rendered PDFs. Record missing coverage candidly. Hosted CI requires a reproducible
compatible host pin; a local green run alone does not establish that.

## N6 — classroom pilot and release

Local synthetic measurements and the reproducible workloads are in the
[600-student validation record](normalization-workshop-600-validation.md).
The prior [64-actor record](normalization-workshop-webkit-validation.md) remains
historical evidence for 0.3.1.

The current target is 600 students and the per-item capacity ceiling is 1,000.
Separate bounded records replace the shared actor array. Presenter pages contain
16 answers and retain two-answer selection across pages. Per-actor updates and
deterministic successful-result reuse use existing generic host capabilities.
The normal feedback/acknowledgement targets remain 30/5 seconds. Report any
missed budget alongside correctness; do not turn a capacity test into a latency
claim. The load workload uses multiple distinct decompositions and covers
replacement, private projections, both active items and presenter recovery.
Whole-class bursts are staggered because the session queue still has 1,000 slots.
The final 600-student WebKit run misses the five-second ACK target at 5.43 s
p95; correctness and feedback timing pass. Keep this performance gate open and
measure the deployment before release. Physical phones and room networking
remain separate acceptance work.

Test a physical Android phone and iPhone over the actual classroom LAN, plus
keyboard and zoom. Review the lesson with a new learner: can they explain why
BCNF, losslessness and preservation are different properties from the feedback?

Exit: measured support limits, accessible UI, reproducible release artifacts,
compatible host pin, complete public guide and reviewed immutable catalog entry.
Only publish or migrate courses when separately requested. Video material stays
in the private media repository.

## Suggested next implementation slice

Keep the 600-student workload and 1,000-answer capacity checks and
its original budgets as regression gates, including evidence that both abandoned
presenter jobs completed after retry and that checked answers match the latest saves.
Complete human screen-reader and learner review of the N4 comparison/evidence
interface and physical Android/iPhone LAN testing. Establish N5 cross-platform
hosted checks against a published compatible host artifact. Local synthetic
load, desktop emulation and storage limits do not close those release gates.
Preserve exact acceptance criteria and independent verification; future
incompatible schemas receive new versions.

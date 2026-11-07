# ER registration lesson-state protocol

Provider 0.6.0 adds optional fixed points to the registration lesson and retains
support for 600 answering actors. The frozen engine is unchanged. State schema
**4** retains constant-size aggregates and host-owned item records, with
publication and reset rules for scored rounds.
Use the validated TeXStage 0.2.1.dev7 host with the matching record, notification and deterministic
cache contracts, a newly pinned bundle and a fresh session. Existing sessions
remain in their original environment; no existing course is migrated here.

E4 now connects these contracts to phone decision cards, a public-only model
preview and presenter controls. The [classroom guide](er-decisions-lesson.md)
explains the workflow and draft behavior. Commands retain their previous version
guards. Participant projections omit the class count; presenter/projector views
retain it. Presenter pages contain at most 16 answers (38 pages at capacity).

## Phases and commands

The host authenticates actors, validates command schemas and manages receipts,
epochs, jobs and persistence. All provider commands use the latest committed
state, with separate guards. The host envelope retains type, item, epoch,
expected_revision and a unique request_id; reuse that exact envelope on retry.

| Command | Role | Payload |
| --- | --- | --- |
| `submit` | Participant | `phase_version`, `answer_version`, `choices`, optional `rationale` |
| `open`, `close`, `reveal` | Presenter | `control_version` |
| `select-answer` | Presenter | `control_version`, `actor`, `answer_version` |
| `share-answer` | Presenter | Same selection fields plus required `include_rationale` boolean |
| `clear-share` | Presenter | `control_version` |
| `set-page` | Presenter | `control_version`, zero-based `page` |
| `_reset` | Presenter, host-owned | Empty payload; current epoch |

Every selection includes the answer version. Empty actor with version zero
clears private selection. Sharing is a separate action, allowed only after
closing. Rationale is omitted unless the presenter explicitly requests it:
free text can identify its author even when the model has no identity attached.

Phases are `introduce → open → closed → revealed`. Open can also start from
closed, or from revealed in practice mode; reopening hides feedback/teaching material and clears sharing. Scored rounds refuse reopening after reveal with `reset-required`.
Closing preserves already accepted pending work. Revealing while work is pending
keeps that status accurate and releases current feedback when it arrives.
Navigation deactivates submissions without deleting saved answers.

Unrelated responses do not invalidate presenter controls or another actor's
answer version. A stale device receives `stale-answer`; a stale presenter
receives `stale-control`; a previous round receives `stale-phase`. Reset advances
the host epoch and invalidates old work. Lost-ACK retries replay the receipt.
Operational refusals and unavailable evaluation never grade an answer incorrect.

## Evaluation and feedback

Submission requires every configured decision exactly once and a known option
for each. It contains no engine, seed, reference or grading rule. Rationale is
normalized plain text, excluded from engine input and semantic identity.
The reducer emits a cancellation when needed, an evaluation against the fixed
prepared `analysis` binding, and a `PutRecord` effect for the actor's answer.
Correlation includes actor, request ID and slot. The host commits the record,
compact aggregate state and receipt atomically. Only the own/selected/shared
records or the current bounded presenter page enter the relevant hook context.

The deterministic engine opts into successful-result reuse. Identical choices
in the same binding and epoch share a validated result; the registration exercise
has 27 combinations. Rationale is not engine input. Each actor still receives an
independent guarded completion. Different inputs execute in fresh restricted
workers. Reset, other exercises and sessions cannot reuse these cached results.

Completion must match actor, current pending correlation, binding and epoch.
The independent Python registration oracle verifies the returned exercise and
answer identities, exact coverage, admission, classifications and deterministic
witnesses. This inexpensive bounded check prevents incomplete or invented
shape-valid facts from becoming a pass. Only compact checked/contradiction
feedback is stored; raw private findings are not copied into actor slots.

This verification occurs inside the provider. TeXStage core contains no ER
semantics. Several valid models keep different semantic identities. A checked
answer remains consistency with the configured finite examples, not a general
equivalence proof.

## Fixed points

Manifest revision 4 combines `state_records`, actor-scoped participant updates,
deterministic result caching and `scoring: {policy: "fixed-v1", points_field: "points"}`.
Prepared public points always contains an integer 0–10000; omitted source
points becomes 0. Positive points activate these effects:

- Submission clears the superseded private credit with `SetCredit(None)`.
- A guarded and independently verified completion sets credit to 1000 for a
  fully correct model, 0 for a verified contradiction, or None when unavailable.
- The presenter's reveal emits `PublishPoints()`. The host owns totals,
  rounding, rankings, receipt idempotency and persistent projection.
- Reset withdraws this activity's contribution and advances the epoch. Navigation
  leaves it intact. Stale completions cannot award points in another round.

Practice emits no scoring effects. The participant's optional `own.points`
comes only from the host's released award, never from client claims. A scored
round cannot reopen after reveal; practice rounds can. Pending work accepted
before close/reveal may finish and publish its verified award afterwards.
Unverified or incomplete facts cannot become credit. State schema 4 requires a
new session; do not resume a schema-3 session against this provider.

## Audience projections

- Participants receive their own saved choices, rationale and processing status.
  Only after reveal do they receive compact feedback and approved teaching data.
- Presenter controls receive counts, option totals, a page of up to 16 actor
  summaries and one explicitly selected answer/rationale/diagnostic.
- Presenter overlay receives a selected model and teaching guidance, without
  the control view's actor listing.
- Projector receives the phase/count and only explicitly shared anonymous
  material; reveal adds both worked models and selected teaching examples.

Selection and sharing are pinned to actor plus answer version. Replacement
clears references to the superseded answer. Public teaching examples omit
private check IDs, classifications, bindings and evaluator digests. Unselected
private situations never enter public projections. Four separate closed
portable schemas are checked by the installed Python and JavaScript validators.

## Enforced bounds and draft handling

The registration authoring limits remain three decisions, one observed
attribute and the bounded worked/example sets. Rationale allows at most 160
Unicode scalar values **and** 1,280 ASCII-JSON bytes; highly escaped text may
reach the byte cap first. Invalid or oversized replacement never discards the
previous answer.

There are at most 600 responding actors, 2,560 serialized bytes per actor record
including its key and reserved feedback, 192 KiB aggregate state, 224 KiB per transition
including effects, and 96 KiB per role view. Existing actors may replace an
answer at capacity. The host atomically accounts for cancellation/replacement
at a full pending queue. Version exhaustion requires reset.

These are storage limits. The [original validation](design/er-lesson-state-validation.md)
retains the earlier schema-2 sizes and artifact identities. Earlier synthetic
throughput is recorded in the [600-student validation](design/er-600-validation.md);
physical-phone and screen-reader verification remains separate. The editor preserves dirty
drafts and focus on unrelated updates and explicitly offers reload/keep-draft
on newer own answers or reset. Returning after navigation restores only the
saved answer; it never submits a draft automatically. See the
[E4 validation](design/er-lesson-ui-validation.md) for the original browser
coverage, and the [0.4.1 accessibility record](design/er-accessibility-validation.md)
for historical keyboard/focus checks. The [600-student validation](design/er-600-validation.md)
records historical schema-3 artifacts, synthetic classroom measurements and the
remaining deployment checks. The [release checklist](er-decisions-release.md)
separates measured capacity from physical-device and hosted-CI validation.

The [points validation](design/er-points-validation.md) records the current schema-4 artifacts and scored classroom checks.

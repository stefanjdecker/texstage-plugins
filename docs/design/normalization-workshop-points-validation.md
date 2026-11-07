# Normalization Workshop: points on reveal

Local validation on Windows, 2026-11-07, with provider **0.5.0** and the
compatible experimental host **0.2.1.dev7**. This is a working-tree build;
nothing was committed, pushed or published by this task. Exact wheel, source
and evidence hashes are in the [machine-readable record](normalization-workshop-points-validation.json).

## Behavior

Each activity has a fixed maximum of 0–10,000 points. The example deck uses
1,000 per activity. The latest independently verified answer receives the full
award if it satisfies the task, otherwise zero. Pending or unavailable results
have no confirmed award. Alternative valid decompositions qualify; FD preservation
is required only when the authored task requires it.

Credits stay private until **Reveal answer**. Closing, inspecting and sharing
answers do not publish points. Reveal updates TeXStage totals, ranks and CSV.
Already accepted current evaluations may finish afterward. Accepting a newer
submission clears the previous credit immediately, so a superseded or failed
replacement cannot retain an obsolete correct award.

Repeated saves replace one contribution. Request replay, result replay,
reconnection, navigation and restart do not add another award. Reset withdraws
this activity's contribution before another round can earn a replacement.
There is no speed multiplier or streak bonus for this fixed policy. Other quiz
and activity contributions are preserved.

## Contracts and host integration

Manifest revision 4 opts into the host's fixed-v1 ledger. The provider emits
SetCredit and PublishPoints effects; it neither calculates totals nor chooses
another actor's credit. Independent server-side semantic verification is retained.

The host compatibility fix carries the existing bounded item-record,
actor-scoped update and by-input cache options into manifest revisions 3–5.
Declaring both record APIs is rejected. Worker CSP, authentication, queue,
record, hook and message limits are unchanged. Concurrent quiz-scoring work
was preserved in the tested host snapshot.

Authoring lesson v2 requires an integer points field. Old format-1 sources
remain practice. Participant view v3 adds nullable own points; all 25 previous
schema files remain byte-identical. The engine format, mathematical rules and
state v3 remain unchanged. Rebuild the bundle in a separately pinned environment
and start a fresh session; do not upgrade an ongoing session or a course environment.

## Verification

- 80 installed-provider tests pass. They cover all three example activities,
  legacy practice, strict configuration, alternative answers, hidden credits,
  replacement, stale jobs, forged facts, unavailable checks, late results,
  duplicate receipts, restart, reset and 1,000-credit capacity/replacement.
- 134 host tests pass, including fixed and quiz scoring, manifest revisions,
  storage contracts, cache delivery, broadcasting, evaluator polling and classroom
  integration. Fifteen load-evidence tests reject incomplete claimed workloads.
- Chrome, Firefox and WebKit pass the full native phone/presenter flow at a
  320-pixel phone width, with rankings and CSV assertions. A former correct answer
  replaced by an incorrect one exports zero; reset removes the published award;
  two other activities accumulate 2,000 points. Worker probes block forbidden
  network/evaluation/nested-worker behavior and verify timeout recovery.
- Wheel/sdist resource parity passes. The seven-slide deck compiles in presentation,
  stage, handout and solution editions. The handout and solution points notices,
  and phone score display, were visually inspected.
- The 600-student scored Chrome run passes correctness. All latest correct answers
  stay at zero total before reveal, then receive exactly 1,000 points; replay adds
  nothing and reset returns all totals to zero.

## Scope and timing

The new run uses 600 synthetic authenticated protocol clients, a real Chrome
presenter/evaluator and projector, staggered whole-class activity bursts, answer
replacement and recovery of two abandoned leases. It does not render 600 phones.
Native phone rendering is tested separately above.

The worst normal-phase acknowledgement p95 was **6.22 s** and feedback p95
was **14.03 s**. The unchanged targets are 5 s and 30 s; this run
missed at least one target. Recovery target pass: **true**.
The raw report retains correctness and timing as separate results.

This is not a new three-browser load matrix or a new 1,000-client benchmark.
The [historical 0.4.0 capacity record](normalization-workshop-600-validation.md)
retains its WebKit/1,000-client acknowledgement misses. Physical classroom
acceptance, network/hardware measurements, cross-platform CI and catalog
publication remain release work.

The guide documents installation, scoring and legacy behavior:
[Using the Normalization Workshop](../normalization-workshop.md#points).
Raw synthetic evidence is stored locally under artifacts/normalization-points;
profiles, authentication files and session databases are excluded.

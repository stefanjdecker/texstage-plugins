# FD Lab 0.5.0: common records and activity points

Date: 2026-11-07. The isolated `codex/fd-points-integration` branches integrate
FD Lab with TeXStage's shared actor-record and points APIs. This is a locally
validated development candidate; no branch, wheel or catalog entry was published.
The original repositories, shared working checkouts, courses and private media
were not modified.

## Compatible artifacts

Use host commit `7b9934d91f3affcc54e2ab6573c8c662cc87348a`, version
`0.2.1.dev5`, and FD Lab `0.5.0`. The host branch contains a verified snapshot
of the newer shared APIs (`b6c0edc`) and a tested compatibility correction:
manifest revisions 3 and 4 accept the existing `participant_updates: "actor"`
policy with its original strict value restriction. The shared uncommitted source
was preserved. The provider no longer uses `ActorTransition` or `actor-slots-v1`.

The accompanying `functional-dependencies-points/identity.json` records exact
wheel and source-distribution hashes, payload, host commit and test counts.
The local handoff contains the exact wheels, source distribution, locked host
dependencies, and English/German bundles, handouts and solutions. Its 42 files
were verified against their byte inventory and installed package resources.

Upgrading requires rebuilt bundles and fresh sessions. Neither the old storage
layout nor an old session's runtime fingerprint is migrated automatically.
The package version alone does not identify the compatible host. Publish the
host commit before attempting the updated collection CI pin; hosted CI for this
candidate has not been run.

## Behavior

- Optional top-level lesson `points` accepts integers from 0 to 10,000. Omitted
  or zero preserves unscored lessons. The synthetic example awards 100 on seven
  exercises and zero on `practice`.
- Domain-verified correct work emits full credit; verified incorrect work emits
  zero. Pending, unavailable and unverified results emit no grade. The reducer
  checks the engine facts against the exact saved answer before setting credit.
- Credits stay private until presenter reveal, even with immediate mathematical
  feedback. The host publishes each learner's own award, game total, ranking and
  CSV columns. Accepted submissions may finish and receive points after reveal.
- Replacement clears the old credit and eventually substitutes its new grade.
  Duplicate commands/results and reconnects cannot add another award. Reset
  withdraws the activity contribution, preserving other activities' points.
  Scored rounds must reset before reopening after reveal; unscored rounds retain
  their earlier reopening behavior.
- `SaveActor` stores one bounded typed answer and summary per authenticated
  learner. The 1,000-record limit and FD's 2 KiB reservation remain. Presenter
  pages contain 25 summaries; selected values arrive only through declared
  presenter commands. Aggregate class counts remain on presenter/projector views.
- Participant projections omit class counts and are independent of other
  learners' answers. The host can update the affected actor's devices and the
  presenter/projector without broadcasting every submission to all phones.
  Published totals/ranks still trigger the required global update.

The worker CSP, two-second evaluation deadline, queue limits, authentication,
schema/byte validation and fresh-worker isolation are unchanged. Result caching
is not enabled by FD Lab.

## Verification

- 141 FD and artifact tests passed against installed wheels, including 28 points
  tests, every mathematical mode, invalid point settings, forged results,
  replacements, late results, replay, reset, durable restart and actor isolation.
  Both language variants compiled their live, exercise, solution and direct-TeX
  outputs; neither authoring case was skipped.
- 220 distinct host regression tests passed across the related runs, including
  records, points, game totals/ranks, CSV, atomic failures, restart recovery,
  contracts, schema caches and evaluator polling. One Windows symlink creation
  check was skipped because this account cannot create the test symlink.
- The installed engine probe passed 30 cases. Chromium 151.0.7922.34, Firefox
  153.0 and WebKit 26.5 each passed 34 actual-worker samples and the security
  probes for blocked network, nested workers, dynamic code, timeout cleanup and
  recovery under the unchanged production policy. The harness also uses a
  permissive positive control to verify that the probes can detect access;
  those control results are not production passes.
- All three browsers passed the full English lesson with points, withheld
  totals, reset withdrawal, same-actor device conflicts, keyboard/touch controls,
  drafts, anonymous sharing and teardown. German controls/points also passed in
  English-locale browsers at 320-pixel phone and 800-by-500 presenter sizes.

Recorded browser reports are retained beside this document. The historical
0.4.0 capacity reports remain evidence for their original artifacts, not this
integration. Physical-phone and lecture-network checks remain deferred under
the user's automated-only scope.

## Classroom load

The final scored 600-participant run and its raw timing gates are recorded in
`functional-dependencies-points/600-chromium.json`. It uses synthetic protocol
participants plus one actual phone viewport and one actual presenter evaluator
on the local Windows machine. It is not a measurement of 600 physical phones.

All 2,400 submissions/completions passed: 600 actors, two scored modes and an
initial/replacement answer in each. Every actor received exactly 100 points per
activity (200 total), and every CSV row matched. Replayed reveal receipts added
nothing. Reset withdrew the second activity's 100 points for all 600 actors
while preserving the first award. The presenter inspected answer 600 through
24 pages. Evaluator replacement, same-actor resume and stale-result/reset races
also passed. Each burst deliberately used the same valid answer; no result
cache was enabled, so every accepted answer ran in a fresh worker.

| Activity | Answer version | Feedback p95 | Slowest feedback | Input p95 |
| --- | --- | --- | --- | --- |
| All candidate keys | 1 | 17.78 s | 18.30 s | 0.9 ms |
| All candidate keys | 2 | 19.09 s | 19.56 s | 0.6 ms |
| Counterexample | 1 | 18.37 s | 19.32 s | 1.8 ms |
| Counterexample | 2 | 17.23 s | 17.73 s | 1.8 ms |

The scoring and data-integrity checks pass, but the 10-second feedback p95
target fails. These timings are slower than the separate 0.4.0 capacity branch;
the common host retains its two-job evaluator. Further throughput work and
measurements on the intended lecture network are required before claiming that
latency target. The prior branch's 1,000-actor timing evidence was not rerun here.

The fixed response-time targets remain p95 below 10 seconds, maximum below
30 seconds and input-to-frame p95 below 100 milliseconds. Functional checks
continue collecting evidence when a timing target fails; CI's strict timing
enforcement remains available and unchanged. See the recorded per-burst results
before making a deployment capacity claim.

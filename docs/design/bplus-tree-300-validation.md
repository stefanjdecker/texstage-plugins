# B+ 300-student validation

Local Windows verification on 2026-11-07. Version **0.5.0** admits 300 student
answers per activity. The matching TeXStage host batches role-specific views,
avoids rewriting unchanged completion state and uses up to four fresh evaluator
workers when at least 64 jobs are eligible (otherwise two).

The [machine-readable record](bplus-tree-300-validation.json) identifies the exact
artifacts, source changes, byte bounds, test results and browser measurements.

## Measured classroom workload

All three presenter browsers passed with **300 authenticated synthetic students**.
Each run accepted 1,200 submissions, validated the 900 answers that must survive
replacement/reconnection, and preserved the latest answer for every student.
The 301st actor's submission was refused, existing students could still replace
answers, receipt retry was idempotent, a student resumed its saved answer and an
evaluator disconnect recovered outstanding leases without resetting retry counts.

| Presenter browser | First burst: p95 ACK / ready | Rapid replacement: p95 ACK / ready | Reconnect: slowest ready |
| --- | --- | --- | --- |
| Chromium 156.0.8078.80 | 1.83 s / 10.24 s | 3.56 s / 12.01 s | 12.75 s |
| Firefox 153.0 | 1.97 s / 11.92 s | 3.50 s / 13.45 s | 15.92 s |
| WebKit 26.5 | 1.62 s / 20.04 s | 3.51 s / 23.31 s | 25.10 s |

“Ready” measures when the phone connection receives the saved evaluation status.
The lesson uses `on-reveal` feedback: the mathematical result stays private until
the presenter reveals it. Tests then check all 300 released grades. They also
verify that private rosters, inspection and unrevealed feedback never reach
student views.

Normal p95 targets were ACK ≤5 s and evaluation ready ≤30 s; evaluator recovery
target was ≤150 s. Every final run met these targets. A deliberately superseded
submission need not receive a grade. The complete trace checks latest job IDs
against accepted, validated evaluator results rather than just counting messages.

Hardware: 11th Gen Intel(R) Core(TM) i9-11950H @ 2.60GHz,
16 logical CPUs, Windows
10.0.19045; server, Node clients and presenter
browser shared the machine. Networking was loopback. The real host worker policy,
fresh-per-submission isolation, authentication, schema checks, timeout and retry
limits remained active.

## Storage and privacy

State schema **3** stores each actor slot as a lossless compact JSON-array string:
version, bounded certificate, correlation, epoch, status and optional feedback.
The complete evaluation binding is pinned once per activity. Commands, engine
inputs and public views retain their documented object schemas. Incorrect but
syntactically valid predictions are preserved exactly and graded independently.

The 300-actor worst-case test includes maximal answer fields, long escaped actor
identities, maximum versions/epochs, selected/shared answers and long bilingual
author explanations. Reserved slot: **632 bytes**;
complete state: **179,534 bytes**; maximum transition:
**180,636 bytes**; largest view:
**67,590 bytes**.

The provider reserves 704 bytes per actor and keeps 16 KiB of shared headroom.
Its state/transition caps stay at 224/240 KiB; its view cap is 80 KiB for the
private 300-entry roster. The host's 256 KiB transition, 128 KiB per-view and
8 MiB IPC limits are unchanged. Streamed views are size-checked before entering
the batch, and each view retains its own 250 ms hook timeout. Fresh schema
validators are shared only within one synchronous batch and discarded on error.

## Verification and artifacts

- 125 plugin tests passed, including codecs, worst-case 300-actor storage,
  capacity replacement, binding identities, receipts, reset and grading.
- 225 host regression tests passed (one pre-existing skip); the final boundary
  suite passed 13 tests, including oversized streamed views, role/session/input
  isolation, schema-error poisoning, compare-and-swap and bounded adaptive leases.
- Chromium, Firefox and WebKit passed real phone/presenter UI scenarios for
  lookup, range, insert, delete, cascading split and root shrink, including
  keyboard/touch input, dirty drafts, conflicts, private inspection and reveal.
- All three browsers passed the production worker security probes, including
  blocked network/child-worker/dynamic-code operations, result validation and
  timeout cleanup. Generated worker bundles and all B+ schemas are current.
- Provider wheel/sdist payload parity passed. English/German prepared lesson
  bundles were rebuilt for this payload.

Host wheel SHA-256: `fd9457658dc1b5b012e968b69271d1e0323a255979625ba66a3856ba9d1965e2`. Provider wheel SHA-256:
`3372252e525822fd03254eee6cfb51102327f252029c5ccb5d294956cd819223`. Provider payload: `c25040697cc12e7e6f8d84b8caeb5be4b89b8d476eceda806aeb88d2b8830519`.

The files live on **`codex/bplus-300-students`** worktrees based on host
`34d0c537135f32b0690147dbb66dd8ff155987f8` and collection
`c05cc9e080b330cc2822a3bbc17ba80acb67de0d`. They are not committed, merged or
published. The existing active host checkout acquired concurrent manifest-3
actor-record changes during this task; those were preserved. This branch needs
reviewed integration with that separate work before a combined release.

## Use and remaining release checks

Install both matching feature builds, enable the exact provider payload, rebuild
the deck/lock and start a new session. The shared development version
`0.2.1.dev3` alone does not identify a compatible host. Existing sessions/course
environments are not migrated.

Reproduce the load probe with the commands in the
[classroom guide](../bplus-classroom.md#bounds-upgrades-and-verification).
The manual `B+ classroom capacity` workflow requires an explicit published host
commit; it has not been run on hosted CI. Ordinary B+ conformance is pinned to a
published API-compatible host instead of public `main`, which lacks the plugin API.

These measurements use synthetic WebSocket students and one active insertion
exercise, plus separate browser UI checks. They do not certify 300 physical
phones, campus Wi-Fi, multiple simultaneous activities, multiple active
presenters, memory use on another machine or Windows/Linux artifact transfer.
Run the classroom/LAN pilot before a lecture and complete the remaining release
gates before publication. Original lecture-tools, existing courses, catalog
publication and private media were not changed.

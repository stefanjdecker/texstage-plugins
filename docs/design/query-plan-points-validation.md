# Query-plan points validation

On 7 November 2026, Query-plan 0.6.0 and the combined TeXStage 0.2.1.dev5
development host passed local Windows validation. The [machine-readable record](query-plan-points-validation.json)
identifies the exact installed host resources, provider payload, wheels and source
distribution. These are uncommitted local artifacts, not a published release.

## Behavior checked

The four sample activities opt into 1,000 fixed points. Verified target-meeting
plans receive the reward on reveal. Missed/invalid plans receive zero; pending or
unavailable feedback remains distinct from a verified unsuccessful answer.
Credits stay private before reveal. The phone shows its award in both activity
feedback and the normal game total; the normal leaderboard and CSV include it.
Quiz speed and streak rules remain unchanged.

Tests cover latest-answer replacement, partial credit in the generic host API,
late verified results after reveal, exact receipt replay, real SQLite restart,
failure between the plugin ledger and game projection, transaction rollback,
reset withdrawal and repeated attempts without accumulating duplicate awards.
Points-triggered broadcasts refresh all rankings even with actor-scoped updates.
The combined build preserves the concurrent item-record and result-cache work.

## Automated and visual checks

- Host: 239 passed; one Windows symlink fixture skipped.
- Query-plan plus portable-handoff checks: 192 passed.
- Existing providers: transaction 67, relational 72,
  coordinate/distance 4 passed in isolated installations.
- Query-plan engine/security, actual presenter/phone controls, protocol and static
  authoring probes passed in Chrome, Firefox and WebKit. Existing providers also
  passed their actual-host browser/security probes in all three browsers.
- English/German LaTeX exports compile; wheel/sdist payload parity passes.
  Rendered handout/solution pages and the 320px phone/presenter reward UI were inspected.

## 600-participant scoring check

The final combined host served 600 real authenticated WebSocket clients and one
real Chrome presenter evaluator. Three replacement rounds and disconnected
evaluator recovery ran before reveal. All 600 latest answers received verified
feedback and correct game totals; reset withdrew every activity award.
The initial burst's acknowledgment p95 was 3.924 seconds,
and the last observed initial completion was 48.206 seconds.
The original acceptance thresholds remained 5 and 60 seconds respectively.
The JSON record includes each scenario's measured quantiles.

This run disabled the two long lease-loss scenarios. Their production 120-second
lease behavior remains covered by the historical [0.5.0 capacity record](query-plan-600-validation.md);
it is not relabeled as a new 0.6.0 result. Runtime tests also cover late results,
restart, stale generations and unavailable outcomes.

These are local loopback measurements, not a Wi-Fi/physical-phone capacity
guarantee. Linux, hosted CI and actual classroom deployment were not rerun for
these exact artifacts. See the [release checklist](../query-plan-release-checks.md).

Build the host wheel, then the provider with
`python maintenance/build_wheels.py --package query-plan`; install both in an
isolated environment. Run `plugins/query-plan/tests`, the host plugin/game/server
tests, and the `query_plan_*_browser.cjs` probes against a freshly prepared bundle.
See [points and authoring](../query-plan-points.md) for configuration and migration.
Original repositories, courses, private media and existing environments remain unchanged.

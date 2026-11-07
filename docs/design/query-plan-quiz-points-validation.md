# Query-plan quiz-points validation

On 7 November 2026, Query-plan 0.7.0 and TeXStage 0.2.1.dev6 passed local
Windows validation. The [machine-readable record](query-plan-quiz-points-validation.json)
identifies the installed host resources, provider payload, wheels and source
distribution. These are uncommitted local artifacts, not a published release.

## Behavior checked

The four sample activities use 1,000 base points and a 120-second speed window.
They reuse the quiz speed formula and shared streak bonus: correct plans earn
50–100% of the base plus up to 500 streak points. Scored quizzes and activities
share a timeline in reveal order. The host records accepted submission time;
evaluator delays cannot reduce the award. Closing pauses the clock; reopening
resumes it. Replacements use a new time; receipt retries preserve the old one.
The scoring window does not automatically close submissions.

Tests cover mixed quiz/activity sequences, bonus settings and caps, incorrect and
missing answers, pending/unavailable feedback, late results correcting subsequent
bonuses, reset withdrawal, receipt replay, restart and failed-write rollback.
The normal totals, leaderboard and CSV use the same released contribution.
The phone shows speed points and bonus separately. Credits stay private before
reveal. Fixed-v1 providers and the actor/item-record and result-cache APIs remain
compatible; production worker restrictions are unchanged.

## Automated and visual checks

- Host: 276 passed; one Windows symlink fixture skipped.
- Query-plan: 180 passed; portable handoff: 19 passed.
- Other providers: transaction 67, relational 72,
  coordinate/distance 4 passed in isolated installations.
- Total: **618 passed, one skipped** across these non-overlapping suites.
- Engine/security, presenter/phone UI, protocol and static-authoring probes passed
  in Chrome, Firefox and WebKit. UI checks include shared streaks across three
  successive activities, 320px touch layout, keyboard use and 200% text sizing.
  Existing providers also passed their browser/security probes in all three.
- English/German LaTeX exports compile, and wheel/sdist payload parity passes.
  The updated activity PDF, narrow phone and presenter scoring labels were inspected.

## 600-participant check

The host served 600 authenticated WebSocket clients and one real Chrome presenter
evaluator. It completed three replacement rounds and disconnected-evaluator
recovery. All 600 latest answers received verified feedback and correct speed
points in the normal total; reset withdrew every award. A fresh 600-student
attempt after reset also met the same latency limits, awarded points once and
withdrew all awards on another reset.
Initial receipt p95 was **4.618 seconds** and the last
observed initial completion was **53.778 seconds**.
The existing 5-second/60-second acceptance thresholds were unchanged. The JSON
record retains each scenario's quantiles and measured runtime/browser versions.

These are loopback measurements, not a physical-phone or Wi-Fi guarantee.
The 1,000-actor ceiling is unchanged and unit-tested; a new 1,000-client capacity
run was not performed. Long lease-expiry cases were not rerun; their evidence
remains the historical [0.5.0 capacity record](query-plan-600-validation.md).
No Linux or hosted CI result is claimed for these exact artifacts. Physical
devices, classroom LAN and screen readers remain [release checks](../query-plan-release-checks.md).

Build/install matching host and provider wheels in an isolated environment,
enable the new provider payload, rebuild the deck and start a fresh session.
See [points configuration](../query-plan-points.md). The original repository,
existing courses, private media and operator environments were not changed.

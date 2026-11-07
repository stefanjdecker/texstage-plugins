# Query-plan points, speed and streaks

Query-plan 0.7.0 uses the same speed formula and consecutive-answer bonuses as
TeXStage quizzes. It requires the matching TeXStage 0.2.1.dev6 host, manifest
revision 5 and state schema 5. Build and explicitly enable the new payload,
rebuild the deck and start a fresh session. Existing courses are not migrated.

Add these optional fields to an activity's JSON source:

```json
"points": 1000,
"time": 120
```

`points` is the base reward (0–10,000); omit it or use zero for unscored practice.
`time` is the speed window in seconds (1–3,600), defaulting to 120. All four
examples explicitly use a base of 1,000 and a 120-second window.

## Speed and consecutive correct answers

A valid plan meeting the best-cost or budget target earns between half and all
of the base points:

```text
speed points = round(base × (1 − 0.5 × min(answer time / window, 1)))
```

The host uses the quiz system's rounding and `speed_points` function. A correct
answer 30 seconds into a 120-second window earns 875 speed points from a base
of 1,000. Streak bonuses are 100 for the second consecutive correct answer,
200 for the third, and so on, capped at 500. The host's setting to disable
streak bonuses also applies here.

The streak is shared across scored quizzes and Query-plan activities, in reveal
order. For example, a correct quiz followed by that 875-point activity adds a
100-point bonus, for an activity award of 975. Verified incorrect answers and
missing submissions break the streak. Pending or unavailable evaluations are
neutral while unresolved; they are not treated as wrong answers. A late verified
result recalculates that activity and any later streak bonuses consistently.

## Timing and presenter controls

- **Open answers** starts the host's clock. **Close answers** pauses it.
  Reopening resumes the accumulated time. Leaving an open activity also pauses
  it when the activity closes.
- The latest accepted submission determines answer time. Replacing a plan
  records a new time; retrying the same accepted request preserves its time.
- The server records time before running the provider hook. Browser-supplied
  times, evaluator latency and result-delivery delays cannot change it.
- The window is a scoring window, not an automatic submission deadline.
  Answers remain open until the presenter closes them. After the window,
  a correct answer earns half the base, plus any streak bonus. Answer time is
  capped at the window for the quiz system's time-based tie breaker.
- **Reveal solution** releases points and updates the normal total and
  leaderboard. The phone shows speed points and streak bonus separately.
- **Reset activity** withdraws its award and recalculates later streak bonuses.
  It resets the activity clock. A new attempt earns a replacement contribution;
  repeated commands, reconnection and duplicate evaluations do not add it twice.

Every tied optimum qualifies. Invalid plans or plans above the target earn zero;
local estimates and merely saving an unevaluated plan earn no points. Practice
activities do not change points, streaks or tie-break times.

CSV export includes credit, total activity points, speed points, streak bonus
and answer time. Pending/unavailable results have blank score cells. Private
credits remain withheld until reveal.

This replaces Query-plan 0.6.0's fixed-award behavior. The host retains fixed-v1
support for older providers. Historical [fixed-points evidence](design/query-plan-points-validation.md)
and [capacity evidence](design/query-plan-600-validation.md) identify their old
artifacts; see [quiz-points validation](design/query-plan-quiz-points-validation.md)
for checks rerun on the new version.

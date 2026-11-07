# Query-plan activity points

Query-plan 0.6.0 can award TeXStage game points. It requires the matching
TeXStage 0.2.1.dev5 host, manifest revision 4 and state schema 4. Explicitly
enable the new payload, rebuild the deck and start a fresh session. Existing
course installations and sessions are not migrated automatically.

Add an optional field to the activity's JSON lesson source:

```json
"points": 1000
```

Use an integer from 0 to 10,000. Omit the field or use zero for an unscored
practice activity. The four example activities now specify 1,000 points.
The phone and presenter show the configured reward; the static exercise also
states it for scored activities.

- A valid plan meeting the configured best-cost or budget target earns the
  configured points. Every tied optimum qualifies; matching one worked answer
  is not required.
- A verified invalid plan or a plan above the target earns zero.
- A pending or unavailable evaluation earns no award and is not treated as a
  verified incorrect answer. A later verified result can still award points.
- Local estimates never award points. Saving a plan alone does not award points.
- **Reveal solution** publishes the awards and adds them to the normal TeXStage
  total and leaderboard. The phone shows its own awarded activity points.
- Replacements before reveal count only the latest accepted answer. Repeated
  commands, duplicate result delivery and reconnection cannot accumulate points.
- **Reset activity** withdraws that activity's award and clears its answers.
  A new attempt can earn a replacement award. Other quiz/activity points remain.

Points are fixed: thinking time, evaluator latency, network speed and quiz streaks
do not change the reward. Existing quizzes retain their usual speed/streak rules.
This is optional game scoring for learning activities, not a course-grade system.

CSV export includes the released activity's credit and points alongside the
combined total. Private answers and unrevealed credits remain private. Old 0.5.0
capacity measurements remain historical; see the [points validation record](design/query-plan-points-validation.md)
for checks actually rerun on this version.

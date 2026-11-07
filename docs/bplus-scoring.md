# B+ grading and scoreboard points

B+ Tree Operations Lab 0.7.0 gives partial credit for the **latest saved
answer**. It uses the fixed rubric below. There is no response-time multiplier,
attempt penalty or streak bonus. A different valid repair sequence can earn
full marks.

## Enable points

Add an optional integer field to the lesson JSON, beside **feedback**:

    "points": 1000

The range is 0–10,000. Omit the field or set it to 0 for practice: students
still receive a rubric grade, but the activity contributes nothing to the
scoreboard. Existing lesson sources therefore remain practice activities.
The six synthetic teaching examples explicitly set 1,000 points each; the
layout stress examples remain practice.

Build and run with the matching host that combines manifest-4 fixed points
and the actor-record/batched-view support. A version lower bound alone does
not identify the required host build. Use the exact host commit and provider
artifacts in the [rebase verification record](design/bplus-tree-rebase-validation.md).
Re-enable the new provider payload, regenerate the plugin lock, rebuild the
bundle and start a new session. Version 0.7.0 uses state schema 5; previous
sessions are not upgraded in place.

For a class approaching 1,000, use a Chrome or Firefox **presenter**. Both passed
the scored 600/1,000-student load checks. The tested Windows WebKit presenter
was reliable at 600 in these checks but crashed intermittently at 1,000; that
ceiling is not verified for WebKit. This concerns the presenter's evaluation
queue; the ordinary phone scoring UI passed in all three browser families.
See the verification record for measurements and the remaining physical-classroom pilot.

## Rubric: bplus-partial-v1

| Operation | Descent | Leaf scan | Returned keys | Repairs | Final separators | Height |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lookup | 40% | — | 60% | — | — | — |
| Inclusive range | 30% | 40% | 30% | — | — | — |
| Insert/delete | 20% | — | — | 50% | 20% | 10% |

The phone's **Grading rubric** explains the criteria before submission.
**Grade for the saved answer** shows the earned and available percentage for
each criterion after feedback is released. Presenter private inspection shows
the same breakdown. Editing a draft never changes the saved grade.

- **Descent:** credit the consecutive correct routing edges from the root,
  divided by the larger of submitted and required edge counts. The editor's
  supplied root earns no edge credit. An exact root-only path satisfies this
  criterion when the starting tree has no edges.
- **Leaf scan:** credit the consecutive correct leaf-page prefix, divided by
  the larger of submitted and required scan lengths. Extra leaves reduce credit.
  The scan starts at the lower-bound leaf and stops at the first leaf reaching
  the inclusive upper bound, or the end of the chain.
- **Returned keys:** credit the number of required keys supplied, minus
  unexpected keys, divided by the number required; clamp at zero. Unsorted or
  duplicate results earn zero for this criterion. An empty expected result
  earns full result credit only for an empty answer.
- **Repairs:** a complete legal replay earns all 50%, including correctly
  choosing no repair when none is needed. Otherwise each independently
  verified repair before the first problem earns **10 percentage points,
  capped at 20%**. Later unverified repairs earn nothing. Completion earns the
  remaining credit because leaving overflow or underflow unresolved has not
  produced a valid B+ tree.
- **Final separators:** available only after a complete legal replay. Credit
  correct keys at their exact (page ID, separator position), divided by the
  number required. Each extra position deducts one correct position; clamp
  at zero. Duplicate or unsorted page rows earn zero. An empty final set earns
  full separator credit only for no rows.
- **Height:** available only after a complete legal replay. Award all 10% for
  the exact height in edges; otherwise zero.

Reading criteria are independent: a correct returned result can earn credit
even when the descent or scan is wrong. For updates, a complete legal replay
is required for final-tree predictions. Separators and height are checked
against the result of **that student's repair choices**, not the author's
worked tree. The original tree is immutable.

Each component is rounded down to one credit unit (0.1 percentage point).
The sum is an integer from 0 to 1,000. TeXStage then awards
**floor((maximum_points × credit + 500) / 1000)** points.

### Examples with a 1,000-point maximum

| Saved answer | Credit | Points after reveal |
| --- | ---: | ---: |
| Correct insertion, wrong height | 90% | 900 |
| Correct descent; one verified repair, but another repair is missing | 30% | 300 |
| Correct range descent; first of two required leaves; all three returned keys | 80% | 800 |
| Correct range descent and scan; two of three keys, no extra keys | 90% | 900 |
| Any complete correct alternative repair | 100% | 1,000 |
| Evaluator failed, timed out, or returned inconsistent facts | Ungraded | No award |

With a maximum of 137 points, 90% credit gives 123 points.
Missing evaluation is not a mathematical zero; the feedback says unavailable
and the CSV credit/points cells remain blank.

Screenshots of the saved partial-credit panel: [English](images/bplus-partial-credit-en.png)
and [German](images/bplus-partial-credit-de.png). The insertion is correct except
for its final height, so it earns 900 of the available 1,000 points.

## When grades and points become visible

1. **Submit answer** saves an answer and replaces its previous credit with
   pending/ungraded. A retry of the same accepted request does not create
   another attempt or award.
2. The presenter evaluator returns facts. The installed lesson reducer
   independently replays the submitted answer and verifies exercise identity,
   answer identity and binding before calculating credit.
3. **on-reveal** feedback keeps the grade private to presenter inspection
   until reveal. **immediate** releases the saved grade to its owner when
   checked. **Both policies keep scoreboard totals and ranks unchanged
   until the presenter chooses Reveal solution.**
4. Reveal publishes the current credits through TeXStage's durable points
   ledger. Accepted answers that finish evaluating later update the same
   contribution. Closed/revealed rounds refuse new submissions.
5. Reset withdraws this activity's points, clears its answers and credits,
   and starts a new epoch. Old jobs and receipts cannot award points into it.
   Navigation and reconnect preserve the contribution. A new game starts
   without the old game's points.

The participant sees host-calculated **Scoreboard points: earned / maximum**.
The regular TeXStage phone total/rank, presenter scoreboard and results CSV
include these points alongside existing quizzes. Fixed B+ points do not change
quiz speed or streak rules. CSV exports include the activity's fractional
credit (0–1) and awarded integer points. A verified zero exports as zero;
pending/unavailable is blank.

Only the submitting actor's grade reaches their phone. Private inspection
does not broadcast it. Anonymous sharing shows predictions before reveal and
may show feedback after reveal. The host broadcasts published score changes
because they can change other students' ranks. Private grading continues to
use actor-targeted updates.

The local preview remains available and helps students investigate their
choices; scoring is designed for this formative classroom workflow.

## Implementation and verification

The provider owns grading.py, the documented rubric and the compact saved
breakdown. It emits SetCredit(None | 0..1000) and PublishPoints(). It never
accepts a student-supplied score or award identity. TeXStage authenticates the
actor, stores credits atomically with state/jobs/receipts, calculates points,
and projects absolute contributions into the game scoreboard and CSV.

Shared state remains bounded independently of class size. Each private answer
has a 704-byte ceiling including a 100-byte feedback reservation. Grades are
not stored in roster summaries. The matching host keeps its worker isolation,
CSP, deadlines, input budgets and 1,000-answer ceiling.

See [authoring](bplus-lesson.md), [classroom use](bplus-classroom.md) and the
[scoring verification record](design/bplus-tree-scoring-validation.md) for
tested artifacts, browser coverage and capacity measurements.

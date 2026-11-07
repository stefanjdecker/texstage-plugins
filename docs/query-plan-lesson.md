# Using Query-plan Challenge

Optional game points are described in [points and feedback](query-plan-points.md).
The four examples use 1,000 base points and a 120-second speed window, with quiz streak bonuses. Existing sources without
a `points` field remain unscored when rebuilt.

Query-plan Challenge lets students choose how a fixed database query is executed:
sequential or indexed access, join order, nested-loop or hash joins, and the hash
build input. Students compare estimates, explain their choices and submit a plan.
It uses a small, explicit teaching cost model, not a database optimizer or
measurements from a database server.

The experimental 0.7.0 provider includes a phone editor, presenter controls and
a projector view. The [authoring guide](query-plan-authoring.md) covers installation,
explicit enablement, all source fields, the LaTeX command and static exports.
The [quiz-points validation record](design/query-plan-quiz-points-validation.md) identifies
the tested artifacts and measured classroom load. A published compatible host,
successful hosted CI, physical-device checks and real screen-reader review
remain release gates.

## Try the example

Build the provider and [four-activity deck](../examples/query-plan/lesson.tex)
in a fresh environment using the authoring guide. Do not change a course's
existing environment or plugin pins.

For a disposable local demonstration, the collection supplies:

```powershell
python maintenance/serve_lesson.py --bundle artifacts/query-plan-lesson/lesson.bundle --data artifacts/query-plan-session --port 8765
```

This development helper uses the presenter key `plugin-demo-key`. Open the
presenter at `http://127.0.0.1:8765/stage`, supply that key when prompted, select
the example and advance to the first activity. Open the projector separately.
Students use the join address/PIN displayed by the presenter. Loopback is for
this computer; use the normal TeXStage server configuration for a classroom LAN.
The helper is a local test utility, not a production deployment configuration.

Use a new session data directory. The build profile enables the provider for
building; the server also needs its reviewed version/payload enabled. The helper
does this explicitly for the providers installed in its disposable environment.
Decks and style files never install or enable plugins.

## Student workflow

1. Read the goal. Expand **Query, statistics and cost rules** to see the fixed
   filters, joins, output columns, row estimates, indexes and cost formulas.
   You can change physical execution choices; the query and its estimates stay fixed.
2. Select **Join order**, then each numbered node's **Method**. For a hash join,
   select which input builds the hash table. There are at most three relations
   and five nodes. The two-input order is significant: the labels identify both.
3. Unavailable index and hash choices are disabled. The nearby explanation shows
   whether an index is absent or the required workspace exceeds the per-join limit.
   Changing the join order can make an existing hash method infeasible; the editor
   keeps that choice visible so you can understand and repair it.
4. Press **Estimate my plan**. This is a local calculation only. It shows baseline
   cost, draft cost and their difference, plus a numbered tree with output rows,
   operator cost and subtree cost. **Inspect node** shows the arithmetic, row width
   and hash-memory calculation. Editing makes this estimate stale; estimate again.
5. **Undo edit** restores the previous draft (up to 50 changes).
   **Reset draft to baseline** changes only your local draft.
6. When answers are open, press **Submit plan**. Only the latest submitted plan
   is retained. The presenter may anonymously share it. A saved plan can still
   be pending evaluation; neither pending nor unavailable means an incorrect answer.
   If evaluation is unavailable, retry while the activity is open.
7. After reveal, read the feedback and expand **Worked solution**. It includes
   the teacher's explanation, minimum cost and number of tied optimum plans.
   A budget task can use a nonoptimal worked example; when different, an additional
   **Optimal plan** section shows one minimum-cost plan.

The estimate is educational feedback, not an authoritative grade. Submitting
does not require a local estimate. Feasible plans that miss the goal and
infeasible plans receive distinct feedback. A plan's subtree cost already includes
its children: do not add their costs again.

The interface uses ordinary labeled selects and buttons. It supports keyboard
navigation, touch targets of at least 44 CSS pixels, narrow screens and enlarged
text. English/German follows the deck's activity-sidecar language.

## Drafts, two devices and resets

Classroom counts, evaluation results and other students' submissions preserve
your controls, draft and keyboard focus. You can continue editing during a save;
its acknowledgement applies to the submitted snapshot, not to newer edits.

If another device changes your saved plan while you have unsaved edits, or the
teacher resets the activity, choose **Load saved plan** or **Keep my draft**.
After a reset, loading uses the baseline because there is no saved answer.
Keeping a draft does not submit it. You must wait for a new open phase and submit
explicitly. A failed request also retains the draft.

Drafts and undo history live in the current page's activity mount. Save before
leaving the slide or reloading the page; unsent edits are not durable storage.
If an external client saved a malformed tree that the selectors cannot represent,
the interface reports this and lets you reset the draft to the baseline.

## Presenter workflow

Open **Query-plan challenge** in the presenter toolbar. The panel shows the phase
and aggregate counts. **Close controls** or Escape dismisses it.

- **Open answers** starts collection. You can close and reopen until reveal.
  Navigation away from an open activity closes it; returning requires opening again.
- Select a numbered submission and **Inspect privately**. This shows its plan,
  cost trace and feedback only in the presenter controls. The worked solution is
  also available in a separate private disclosure.
- **Share selected plan anonymously** displays the chosen plan on the projector.
  Neither student identity nor assessment is included in that projection.
  **Clear shared plan** returns to the exercise; if the activity was already
  revealed, it returns to the worked solution. A replacement answer invalidates
  the old selection and sharing.
- **Close answers**, then **Reveal solution** releases individual feedback and
  the worked solution. Reveal is terminal for this round. A shared submission
  remains visible until you clear it; reveal also makes the solution available
  to students.
- **Reset activity** asks for confirmation, clears answers and starts a new round.
  It changes the host epoch so late results cannot alter the new round.

Presenter controls wait for the committed view after a command receipt. This
prevents a quick second click from sending a stale control version. Other
presenters can still change the activity: a rejected stale action reports the
change and can be retried after checking the current state.

Before sharing/reveal, the projector retains the complete prepared exercise.
Shared/revealed overlays show a readable numbered plan and cost facts, with the
fixed query, statistics and rules available in the context disclosure. The
presenter slide mirrors this public display; private inspection stays in its panel.

## Model and limits

All costs use `teaching-cost-v1` and the source's integer statistics:

| Operator | Local cost |
| --- | --- |
| Sequential scan | 100 × base pages + base rows |
| Eligible equality index | 400 × (index height + filtered rows) + filtered rows |
| Nested loop | left rows × right rows + output rows |
| Hash join | 2 × build rows + probe rows + output rows |

A join's subtree cost adds both child totals once. Hash workspace is build rows
× (build row width + 16), bounded independently for each operator. Intermediate
widths add. Memory here excludes output materialization; there is no spilling,
parallelism, caching, sort/merge join or database-specific planner simulation.
Join predicates form a connected tree. Disconnected intermediate joins are not
offered; every feasible ordered tree and physical-method combination remains
reachable. Duplicate output rows are retained (bag semantics).

Version 0.7.0 stores up to 1,000 distinct student answers per activity, with
a 600-student classroom target. Storage capacity is separate from measured
throughput. The presenter uses Previous answers / Next answers to browse
25 summaries per page; a selected answer remains visible when changing pages.
The [points validation record](design/query-plan-quiz-points-validation.md) reports
checks on 0.7.0. The [earlier capacity record](design/query-plan-600-validation.md)
reports synthetic load and evaluator recovery on 0.5.0 artifacts.
This does not guarantee performance on classroom Wi-Fi or physical phones. Review the
[classroom contract](design/query-plan-classroom-contract.md) for protocol,
privacy and operational-failure details.

## Troubleshooting and verification

A static slide without controls can mean the provider is missing, disabled or
pinned to different bytes, or a renderer failed to load. Inspect the installed
provider and server profile; rebuild a deck against the intended payload rather
than hand-editing its pins. The static exercise and exports remain useful offline.

If a save is refused, retain the draft and read the message. Closed phases need
the presenter to reopen; after reveal, use reset for another round. Queue
saturation is retryable. A full session cannot admit additional actors.
An unavailable evaluator preserves the saved plan without assigning a false grade.

Maintainers can run the installed-wheel suite and actual UI browser probe:

```powershell
python -m pytest plugins/query-plan/tests -q
python maintenance/query_plan_authoring_probe.py --output artifacts/query-plan-editions
$env:PYTHON=(Get-Command python).Source
$env:BROWSER='chromium'
node maintenance/query_plan_ui_browser.cjs artifacts/query-plan-editions/out/lesson.bundle artifacts/query-plan-ui/chromium
```

Use the collection's locked Playwright package and installed browsers. Repeat
with Firefox and WebKit; clear any Chromium channel override. The separate
engine-security and classroom-protocol probes retain their checks. Desktop
emulation and text enlargement are not physical-phone or screen-reader testing.

# Run an ER modelling activity

ER Modelling Decisions asks students to choose a model that fits stated business
requirements. In the registration example they decide how many workshops a
person can join, where registration status belongs, and whether registrations
are a relationship or an association entity. Both intended alternatives are
accepted. The activity checks examples; it does not prove general equivalence.

Version 0.6.0 provides an English/German registration pilot. Use the matching
experimental TeXStage host, a newly built deck and a fresh session. The
[installation and authoring guide](er-decisions-authoring.md) gives the complete
build, explicit enablement and provider-lock commands. The
[validation record](design/er-points-validation.md) identifies the tested
host and provider bytes.

## Teach with the example

1. Present [lesson.tex](../examples/er-decisions/lesson.tex), or
   [lesson-de.tex](../examples/er-decisions/lesson-de.tex) with its German
   activity sidecar. Students join with the presenter’s PIN/QR code.
2. Discuss the fixed requirements and permitted example. The slide initially
   keeps the prepared exercise visible; the phones have no preselected answer.
3. Choose **Open answers**. Students select one option in each decision card.
   They can add a short reason and use **View model** to inspect their choices.
   **Back to decisions** keeps those choices and the reason.
4. Students choose **Save answer** explicitly. They may replace their answer
   while answers are open. A preview or change to a choice never submits it.
   TeXStage evaluates saved answers on the presenter’s computer.
5. Use the counts and **Choices across saved answers** to plan the discussion.
   Select an answer and choose **Inspect an answer privately**. The selection
   is separate from what the class sees. The list is paged in groups of 16;
   displayed numbers are current list positions, not permanent pseudonyms.
6. Choose **Close answers** before sharing. **Share selected answer anonymously**
   projects the inspected model. The reason is excluded unless you explicitly
   tick **Also share the reason with the class**. **Clear shared answer** removes
   it. A replaced answer clears the old inspection/share; inspect the new
   version before sharing again.
7. Choose **Reveal alternatives**. Phones receive their own feedback, the two
   checked alternatives and selected counterexamples. The projector shows the
   alternatives and counterexamples when no student model is currently shared;
   clear a shared model to see them.
8. In practice mode, reopen answers for repair. The revealed feedback disappears until the next
   reveal. Students keep their saved choices and explicitly save any repair.
   **Reset activity** asks for confirmation and starts a new answer epoch.
   Scored rounds require reset after reveal; see **Award points** below.

Keep the presenter open while evaluation runs. A pending answer is saved,
not graded wrong. Reopening a disconnected presenter resumes unfinished work;
if evaluation is unavailable, the saved answer remains. Queue or capacity
refusals preserve the draft; wait and retry. This version accepts **600 answering
students**, and existing students can still replace answers at capacity. Class
counts appear on the presenter/projector, while each phone receives its own
answer updates. See the [600-student measurements](design/er-600-validation.md) and
[load results and release limits](er-decisions-release.md).

## Read a model correctly

The bounds next to **Person** describe links for each individual person; those
next to **Workshop** describe links for each individual workshop. They do not
describe the opposite endpoint. `0..*` permits no links or any number of links,
`1..*` requires at least one, and `0..1` permits at most one. A question mark
means that a decision has not been made.

The schematic is accompanied by a **Constraints in words** list. It identifies
the attribute owner and whether the person/workshop pair is unique. An
association entity needs this pair uniqueness as well as any occurrence ID;
an ID alone does not prevent duplicate registrations. Status on Person cannot
represent different statuses for that person’s registrations in two workshops.

The preview is constructed exclusively from public choices. It does not run
private checks or tell students which choice to make. An optional reason is
plain text, at most 160 Unicode characters and 1,280 bytes after ASCII JSON
escaping. Long emoji-heavy reasons may need shortening. Reasons do not affect
the engine’s grade.

## Award points

The example is practice by default. To enable scoring, set `"points": 1000`
in the lesson source as described in the [authoring guide](er-decisions-authoring.md#optional-game-points).
The phone and presenter show the rule: a fully correct model earns all points,
with no speed bonus. Both accepted models receive equal credit.

**Reveal alternatives** publishes the awards in the normal game total and
rankings; the phone also shows its own activity award. Incorrect answers earn
zero. Pending or unavailable evaluations do not earn correctness points; an
accepted pending evaluation can still receive its award after reveal.

In a scored round **Open answers** remains disabled after reveal. Use **Reset
activity** to start again: its confirmation explains that this removes the
previous award from this activity. Other activity points remain intact.
Navigation preserves points, and reconnecting or retrying a receipt never
duplicates them. In practice mode the reopen-and-repair workflow above remains
available.

## Drafts, devices and access

An unrelated student’s answer or teacher update preserves your draft and focus.
If another device changes your saved answer, or the teacher resets the activity
while you are editing, choose **Reload saved answer** or **Keep my draft**.
Neither choice submits anything. Save explicitly once answers are open.

A response to an older request cannot replace edits made while saving. Navigating
away from the activity discards unsaved edits; returning restores the saved
answer. Keep notes separately if an unsaved draft must survive navigation.

Radio options, buttons and disclosure panels support keyboard input and touch.
**View model** moves keyboard focus to its heading, and **Back to decisions**
returns focus to the preview button. Text can be enlarged without horizontal
phone scrolling. The diagram’s information is repeated as text; physical-phone
and screen-reader testing remain release work.

Version 0.4.1 focuses the missing decision or invalid reason after a validation
error. Resolving a draft conflict returns to a visible editor/preview target.
Phase and answer status messages change only when their content changes.
See the [keyboard and accessibility guide](er-decisions-accessibility.md) for
the workflow, automated evidence and remaining manual checks.

Answers and reasons are visible to the teacher. Other students do not receive
your saved answer or reason through this plugin. The projected example is
anonymous; releasing its reason is a separate, explicit teacher choice. The
[state contract](er-decisions-state.md) describes the role projections.

## Reproduce the local checks

Build/install the wheel as in the authoring guide, with the host’s locked test
dependencies and the collection’s locked Node dependencies. Install Playwright’s
Chromium, Firefox and WebKit binaries for browser checks.

```console
python -m pytest plugins/er-decisions/tests -q
python maintenance/er_ui_bundle.py --output artifacts/er-ui
node maintenance/er_lesson_browser.cjs artifacts/er-ui/out/lesson.bundle artifacts/er-ui-browsers
```

The bundle helper creates a disposable copy of the example plus a discussion
frame for navigation checks. It does not change the example or any course.
Set `BROWSER=firefox` or `BROWSER=webkit` in your shell to select the other
families. On PowerShell use `$env:BROWSER='firefox'`. Set `PYTHON` to the
isolated environment’s interpreter when launching the Node harness.

The real classroom scenario uses a presenter, projector, two contexts for one
learner and another learner, including a wrong answer followed by a repair.
Separate installed-renderer probes cover operational errors, an old request
finishing after reset, in-flight edits, paging and German long labels. These
probes are not classroom load measurements.

The prepared slide remains useful if an overlay cannot mount. Static handout,
solutions, direct LaTeX and PowerPoint exports still derive from the same
source. Rooms, scoped identification and open assumptions are not offered in
this registration profile. Synthetic 600-actor load, identical-wheel Linux
consumption and an isolated release workflow now have dedicated checks. See
the [release checklist](er-decisions-release.md) for measured evidence and the
remaining physical-device, screen-reader, hosted-CI and publication gates.


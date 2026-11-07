# Using the Normalization Workshop

This experimental TeXStage plugin turns a normalization exercise into a live
classroom activity. Students either classify a relation and give a violating
functional dependency, or propose smaller relations. They use attribute
checkboxes, relation cards and normal-form selectors. They do not enter JSON.

The analyzer checks normal form, attribute coverage, lossless joins and FD
preservation separately. A correct answer can differ from the worked answer.
This is reasoning over the stated functional dependencies, assuming atomic
values (1NF); it does not infer dependencies from sample data or execute SQL.

The [seven-slide example](../examples/normalization/lesson.tex) contains three
activities: preserve course registrations, classify a tutor relation, then
explore a lossless BCNF decomposition that loses an FD. Its data are synthetic.

## Install and enable

Use Python 3.12+ and pdfLaTeX/latexmk. Start with an isolated environment and a
compatible experimental TeXStage wheel. The tested host revision and artifact
hashes are in the [600-student validation record](design/normalization-workshop-600-validation.md).
Version 0.4.0 requires the host's bounded item records, actor-scoped updates and
deterministic result reuse. The dependency version `texstage>=0.2.1.dev4`
alone does not identify unpublished
host changes. No catalog release of this workshop is published yet.

For development, install the matching host's locked development/build
requirements and host wheel first. From the plugin collection root:

```sh
python maintenance/build_wheels.py --package normalization-workshop
python -m pip install --no-deps dist/texstage_normalization_workshop-0.4.0-py3-none-any.whl
texstage plugins --data ./normalization-profile inspect io.github.stefanjdecker.normalizationworkshop
```

Review the provider and use its printed payload digest below:

```sh
texstage plugins --data ./normalization-profile enable io.github.stefanjdecker.normalizationworkshop --version 0.4.0 --payload <printed-payload>
texstage plugins --data ./normalization-profile lock --output ./normalization.lock.json
texstage present examples/normalization/lesson.tex --activities examples/normalization/lesson.activities.json --data ./normalization-profile --plugins-lock ./normalization.lock.json --no-tunnel
```

Installation and enablement are separate. Uploading slides or loading a style
does not install code. Rebuild and start a fresh session when changing provider
bytes. The example does not require FD Lab or any other provider.

## Run a workshop

1. Navigate to an activity and select **Open answers**. Students join using the
   presenter PIN. The introduction and discussion slides are static.
2. For decomposition, use **Add relation**, then select the attributes of each
   component. Each component must be nonempty and distinct; one to eight are
   allowed. To classify, choose the highest normal form and, below BCNF, a
   singleton FD that violates the next normal form. An empty left side is allowed.
3. Select **Save answer** explicitly. The current presenter browser evaluates
   saved answers in the restricted worker. Without an evaluator, the answer
   stays saved and pending. A failed check is shown as unavailable, not incorrect;
   students can save again while answers are open.
4. Select **Close answers**. Already accepted pending evaluations may finish.
   **Inspect privately N** shows one checked answer and its independently
   computed facts on the presenter's slide. The projector stays unchanged.
5. **Share with class N** displays only that saved answer version. **Share answer
   and checks N** also displays its verified facts. For two checked answers, choose
   **Answer A** and **Answer B**, then **Compare privately**. After inspecting the
   pair, **Share comparison and checks** displays both on the projector.
   The answer list has 16 entries per page. Use **Next page** and **Previous page**;
   Answer A and Answer B can come from different pages. A chosen off-page answer
   stays in its selector. The server checks that both versions are still current.
   Answer numbers stay stable for the round; page order may shift as answers arrive.
   The presenter controls scroll within their panel so the comparison slide stays
   readable. Tab into the panel or scroll it to reach lower answer rows.
   **Stop sharing** removes them. Names and actor handles are omitted.
6. **Reveal answer** releases the worked explanation, each student's own feedback
   and evidence for their saved answer. Clear the private selection or shared answer to display the worked
   answer on that surface. Reveal is final for this round: use **Reset activity**
   to clear answers and start over.
7. Before reveal, **Open answers** can reopen a closed round. It retains saved
   answers and clears the selected/shared answer. Navigation also retains saved
   answers. Unsaved drafts live only in the mounted page.

Typing, checking a box, reconnecting and choosing **Keep my draft** never submit
automatically. A newer save from another device or a reset requires **Load saved
answer** or **Keep my draft**. Unrelated updates preserve the draft and focus.
Use Tab, Space/Enter and the native select's arrow keys; dragging is unnecessary.

A saved version is checked independently on the server before feedback is
accepted. This remains formative assessment under TeXStage's presenter-evaluator
trust model. Each activity stores at most 1,000 pseudonymous answers.
Existing students can replace their answers at the ceiling. Capacity and measured
response time are separate; see the classroom-size guidance below.

## Keyboard and language

Use Tab and Shift+Tab to move, Space to toggle an attribute, and Enter to activate
a button or expand a proof. Native selectors support Home and arrow keys.
Adding a relation moves focus to its first attribute. Removing one moves focus
to the adjacent remaining relation. **Load saved answer** and **Keep my draft**
return focus to the editor and do not submit anything.

Chase controls remain focusable at the beginning/end, with an unavailable state
announced through `aria-disabled`. Activating an unavailable step does nothing;
focus stays on the control. A proof table is a separate keyboard-focusable
horizontal scroll region. Attribute checkboxes retain their short identifier
as the accessible name and describe its meaning in the selected language.

The presenter/projector use the deck's language. To author German material, use
`\usepackage[ngerman]{babel}` and `"language":"de"` in the activity sidecar.
These are separate settings: Babel sets the live deck language; the sidecar
selects generated static material and the prepared worked explanation.

Phone plugin controls follow the phone browser's language, like the built-in
phone interface (German for a German browser, otherwise English). This requires
the TeXStage phone-language fix identified in the accessibility validation
record. A provider version alone cannot fix an older host. The worked explanation
still follows the authored sidecar language.

Version 0.4.0 uses state v3 and paginated presenter/projector views.
Participant, engine and authoring formats are unchanged; all frozen v1/v2
schema resources remain available. Existing v2 sessions stay in their original
pinned environment; there is no automatic session migration.
Review/enable the new payload, update the lock and rebuild the bundle in an
isolated profile. Use a fresh session when changing the pinned environment.

## Discuss the results

Comparison accepts two different learners' current checked answers. It does not
compare unsaved drafts or two historical versions. A replacement invalidates
any selection that refers to that learner. Reopening clears comparison and
sharing; inspecting another answer privately does not change an existing share.

With a checked answer selected or shared, choose **Overview**, **Explain lossless
join** or **Explain FD preservation**. The projector receives checks only after
an explicit share-with-checks action. Sharing checks lets the class infer whether
that answer meets individual criteria, even before personal feedback is revealed.

After reveal, a phone shows **Evidence for saved answer** with its version.
Expanding a proof or moving through chase steps does not save an answer.
Editing the draft does not change the saved evidence.

### Lossless join: find the extra tuple

For the registration exercise, SN / CTI / IO meets BCNF and preserves all FDs
but loses the connection between a student and a course. The losing chase
tableau is a finite relation that satisfies every stated FD. The displayed
all-distinguished tuple is absent from it, yet each component projection contains
the tuple's corresponding values; joining the projections introduces it.

Expand **Every required projection is present** to see which row supplies each
piece. **Chase steps** has **Previous step**, **Next step** and **Final table**
controls. Each step names the FD and row pair that cause a symbol merge.
Symbols a_ID are the distinguished value for that column; bN_ID are initially
fresh values. Intermediate tables are proof construction, not yet a claimed
legal counterexample. A final all-distinguished row instead proves losslessness.

Compare SN / SC / CTI / IO with SN / SC / CT / CI / IO: both are valid despite
using different component sets. The workshop checks properties rather than
matching the teacher's chosen decomposition.

### Lost FD: a different kind of example

For the tutor exercise ST -> U and U -> T, decomposing into SU / TU is lossless
and BCNF, but loses ST -> U. The display computes the closure of ST using the
union of projected dependencies. U remains outside that closure.

Its two example rows agree on the closure and disagree elsewhere. Their
projections satisfy every component's projected FDs, but together they violate
the original lost FD. This is deliberately **not** a legal instance of the
original relation. It demonstrates why enforcing constraints in the components
alone is insufficient; it is not the lossy-join counterexample above.

Tables have row/column headings and keyboard-focusable horizontal scroll regions.
On narrow screens comparison cards stack; wide proof tables scroll inside the
card. The accessibility harness covers German keyboard flows at 320 CSS pixels and
native 200% Chrome zoom. Human screen-reader and learner review remain gates.

## Upgrading from 0.2.0

Version 0.3.0 changes persisted classroom state and role views to schema v2.
Install and explicitly enable the reviewed new payload in an isolated profile,
update the plugin lock, rebuild the bundle, and start a **fresh session**.
There is no in-place migration for saved 0.2.0 sessions. Keep their original
provider/lock if you need to continue them. The lesson JSON, LaTeX command,
mathematical answer/result schemas and acceptance policy are unchanged.

## Create an exercise

Add an entry to an explicit `lesson.activities.json` sidecar:

```json
{
  "format": 1,
  "language": "en",
  "items": [{
    "id": "registration",
    "type": "io.github.stefanjdecker.normalizationworkshop.workshop",
    "source": "activities/registration.json"
  }]
}
```

Copy one of the [activity sources](../examples/normalization/activities/registration.json).
Each contains `format:1`, `exercise`, `worked_answer` and bilingual `explanation`.
The exercise supplies a stable ID, bilingual title/prompt, ordered attribute
IDs/labels, named FDs and one of these tasks:

| Task | Configuration | Acceptance |
| --- | --- | --- |
| Classification | `{"mode":"classify"}` | Highest normal form and a valid next-form violation; BCNF needs a null witness |
| Decomposition | `{"mode":"decompose","target":"bcnf","preserve":true}` | Covers every attribute, all components meet the target, join is lossless, and all FDs are preserved |
| Trade-off | Same with `"preserve":false` | Coverage, target form and losslessness are required; preservation is still checked and reported |

`target` may be `3nf` or `bcnf`. Support is bounded to 1–8 attributes, at most 32
expanded singleton FDs and eight component relations. Duplicate/trivial FDs are
normalized with diagnostics. Identifiers are ASCII; labels and prose support
English and German. The sidecar language selects static text and the revealed
explanation.

Worked answers use compact attribute masks according to the declared order.
For `[S,N,C,T,I,O]` the bits are `[1,2,4,8,16,32]`. SN is 3, SC is 5, CTI is 28
and IO is 48:

```json
{"mode":"decompose","relations":[3,5,28,48]}
```

For `[S,T,U]`, the tutor classification is:

```json
{"mode":"classify","normal_form":"3nf","witness":[4,2]}
```

Here `[4,2]` means U -> T. The empty determinant is 0. BCNF uses
`"witness":null`. Students see names and controls, never these masks.
Preparation rejects an incorrect or impossible worked answer; it does not
silently turn it into an expected result.

## LaTeX command and exports

```tex
\usepackage{texstage}
\usepackage{texstage-normalization-workshop}
% Within a frame:
\normalizationworkshop{registration}{.96\linewidth}{.78\textheight}
```

The three arguments are the sidecar item ID, width and height. The optional
style exports this one command, a thin wrapper around `\texstageprepared`.
It contains no database rules. The authoring hook derives public content,
private checks, exercise fragments and solution fragments from the same source.
Plain prose is escaped before insertion into TeX.

From the collection root:

```sh
texstage build examples/normalization/lesson.tex --stage --activities examples/normalization/lesson.activities.json --data ./normalization-profile --plugins-lock ./normalization.lock.json
texstage pdf examples/normalization/lesson.tex --handout --activities examples/normalization/lesson.activities.json --data ./normalization-profile --plugins-lock ./normalization.lock.json
texstage pdf examples/normalization/lesson.tex --solutions --activities examples/normalization/lesson.activities.json --data ./normalization-profile --plugins-lock ./normalization.lock.json
texstage prepare examples/normalization/lesson.tex --activities examples/normalization/lesson.activities.json --data ./normalization-profile --plugins-lock ./normalization.lock.json
```

`build` also creates `lesson-static.pptx`. `prepare` prints local entry points
for direct pdfLaTeX compilation. Changing the source makes those exports stale;
run preparation again. Local preparation directories and the solution PDF
contain worked answers. Public bundle routes exclude private preparation data.

## Classroom size and presenter recovery

The design target is **600 students**, with a hard ceiling of **1,000 saved
answers per activity**. The host also defaults to 1,000 active participants per
session. A participant can update their existing answer at the ceiling.

Answers are separate transactional records. Shared activity state stores counts
and at most two selected/shared references. Presenter pages contain 16 summaries;
phones receive only their own saved answer and no class roster. A reset clears
the item records and invalidates previous jobs together.

The host can reuse a verified successful result for exactly the same prepared
input in the same session, item and round. Each answer still has its own durable
job, version checks and independent server verification. Unseen inputs use fresh
restricted workers. Result reuse never shares student state. The independent
server verifier also keeps at most 64 immutable analyses keyed by the full seed
and answer. It never caches supplied worker facts or skips the fact comparison.

Keep class-wide submission bursts to **one activity at a time**. Two activities
may remain visible, but two simultaneous 600-answer bursts can exceed the
unchanged 1,000-pending-job session queue. A queue-full refusal does not save the
new answer; keep the draft and retry after pending work drains. Do not raise
worker, state or queue safety budgets to hide overload.

The [600-student validation record](design/normalization-workshop-600-validation.md)
reports the exact tested artifacts, workloads and observed timings. All three
600-student runs preserved correct answers, with feedback p95 below 13.1 seconds.
The final WebKit run reached 5.43 seconds at acknowledgement p95, slightly over
the five-second target; this timing gate remains open. Synthetic
authenticated sockets on loopback do not measure 600 rendered phones, Wi-Fi
capacity, WAN latency or every worst-case FD exercise. Test the intended room,
network and presenter computer before using this as a teaching guarantee.
The 1,000 limit is a capacity ceiling, not a response-time promise.

Keep the presenter browser open while evaluations are pending. With the current
host, an observed presenter disconnect releases its outstanding leases for the
replacement presenter; saved answers remain intact. A connection that disappears
without an observed disconnect still relies on the existing 120-second expiry
fallback. Use **Reset activity** when you intend to clear a round.

Physical Android/iPhone testing on the classroom network remains necessary.

## Developer reference and remaining work

- Provider: `io.github.stefanjdecker.normalizationworkshop`.
- Engine: `io.github.stefanjdecker.normalizationworkshop.analyze`.
- Content: `io.github.stefanjdecker.normalizationworkshop.workshop`.
- Participant command: `submit` with phase, answer version and answer.
- Presenter commands: `open`, `close`, `reveal`, `select-answer`, `share-answer`,
  `share-analysis`, `compare-answers`, `share-comparison`, `show-evidence`,
  `unshare`, `clear-selection` and `page`. Each is guarded by control version;
  selections also pin answer version. `_reset` is host-owned and guarded by epoch.
- [Discussion contract](design/normalization-workshop-discussion-contract.md)
  specifies state/view v2 and the new command payloads.
- [Frozen v1 contract](design/normalization-workshop-contract.md) documents schemas,
  identities, mathematical rules and resource limits.
- [Package guide](../plugins/normalization-workshop/README.md) documents the analyzer
  and installed-wheel checks.

The native interface includes comparison and readable chase/counterexample
displays. The [accessibility record](design/normalization-workshop-accessibility-validation.md)
adds German keyboard and zoom evidence; human screen-reader and learner review
remain. The [current load record](design/normalization-workshop-600-validation.md)
measures queue latency, replacements, simultaneous items and presenter recovery,
and includes active worker security checks. The
[earlier record](design/normalization-workshop-load-validation.md) retains the
original bottleneck measurements.
N5/N6 retain cross-platform hosted CI, real classroom load and physical
Android/iPhone testing. Desktop browser emulation does not close those gates.

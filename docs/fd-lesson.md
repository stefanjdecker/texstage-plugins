# Using the Functional Dependencies Lab

This experimental TeXStage plugin lets students compute an attribute closure:
start with a given set of attributes, apply stated functional dependencies (FDs)
step by step, and select the complete resulting set. An FD `X -> Y` says that
two rows agreeing on every attribute in X must also agree on every attribute
in Y. The task uses declared constraints, not patterns guessed from sample rows.

The [example deck](../examples/functional-dependencies/lesson.tex) contains two
workshop exercises. In the first, a workshop determines its tutor and room, and
the room determines its building. In the second, students also start with a
person. Students use FD buttons and attribute toggles; no JSON editing is needed.
The presenter opens submissions, inspects answers privately, reveals feedback,
shares an anonymous response, or walks through one worked derivation.

Version 0.3.0 implements closure, one/all candidate keys and FD implication.
The deck continues with key sets, positive derivations, negative two-row witnesses,
keys of different sizes and the empty key. The [F3 validation record](design/functional-dependencies-f3-validation.md) identifies
the exact locally tested host and plugin artifacts. This is not a catalog release.

[Deutsche Anleitung](fd-lesson-de.md).

## Install and enable

Use Python 3.12+, a matching experimental TeXStage host wheel, and a TeX installation
with pdfLaTeX/latexmk, Beamer, Latin Modern fonts, and English/German Babel support.
The host must include prepared authoring, typed facts, structured command errors,
atomic replacement of queued evaluations, and renderer mount reconciliation.
Host commit `de33515` is the tested baseline; a development version string alone
does not identify a compatible build. Install into a fresh virtual environment,
leaving existing course environments intact.

For a source build, first install the matching host's hash-locked development
requirements and its wheel. The host SDK is also the provider build backend.
From the plugin collection root, with that environment activated:

```sh
python maintenance/build_wheels.py --package fd-lab
python -m pip install --no-deps dist/texstage_fd_lab-0.3.0-py3-none-any.whl
texstage plugins --data ./fd-profile inspect io.github.stefanjdecker.fdlab
```

Review the inventory and replace `<printed-payload>` below with its displayed
payload digest. Installation and explicit enablement are separate actions.

```sh
texstage plugins --data ./fd-profile enable io.github.stefanjdecker.fdlab --version 0.3.0 --payload <printed-payload>
texstage plugins --data ./fd-profile lock --output ./fd.lock.json
texstage present examples/functional-dependencies/lesson.tex --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile --plugins-lock ./fd.lock.json --no-tunnel
```

Neither a deck upload nor a style file installs or enables code. Start a fresh
session after replacing host or provider bytes. Phones must be able to reach the
presenter's server; keep the presenter browser open to evaluate saved answers.

## Run the exercises

1. Navigate to **What does a workshop determine?** Select **Open answers**.
   Students join through the usual TeXStage PIN/link and read the task and given FDs.
2. Students add the FDs in the order they use them. **Undo last step** removes
   the last choice. They toggle attributes in **Your final set**, then explicitly
   select **Save answer**. Editing alone does not submit. Keyboard users can tab
   to the native buttons and activate them with Enter or Space.
3. Each productive step must have all determinants already known and add at least
   one new attribute. The final set must match the reached set and the full closure.
   Any valid derivation is accepted; it need not match the author's step order.
4. The presenter can inspect a saved response privately and see pending, correct,
   incorrect and unavailable counts. **Close answers** stops further submissions;
   already accepted evaluations can still finish.
5. **Reveal solution** releases the worked answer and each student's own feedback.
   Only then can the presenter share a selected response anonymously. The projector
   receives no student identifier or roster. **Start walkthrough**, **Next step**
   and **Previous step** show how the known attribute set grows in the worked proof.
6. **Open answers** reopens the task and clears the shared demonstration. Saved
   answers remain available for revision. **Reset activity** clears responses and
   starts a new epoch after the host's confirmation. Reset cannot make a previously
   revealed answer unknown; use a fresh exercise for a new assessment.
7. On **Start with a person and a workshop**, feedback is immediate after each
   evaluation because this source chooses practice mode. The worked solution still
   stays withheld until reveal.

Incorrect derivations get specific feedback: a missing determinant, an unproductive
step, an incomplete closure, an overclaimed attribute, or an incorrect final set.
“Unavailable” is an operational failure, not a wrong answer. A pending response is
saved but awaits the presenter's evaluator. Responses can be revised while open.

If another device saves an answer for the same participant, the editor offers
**Reload saved answer** or **Keep my draft**. Keeping a draft never submits it
automatically. Unrelated updates preserve focus and edits. Navigation remounts the
editor from the saved answer; unsaved drafts are local to the current mount.

## Candidate keys

A superkey determines every attribute. A candidate key is a superkey with no
removable member: minimal by inclusion, not necessarily the smallest cardinality.
The author explicitly chooses **one** or **all** candidate keys.

Select attributes under **Build a proposed key**, then select **Use this key** for
one-key mode or **Add key** for all-keys mode. **Save answer** submits the proposed
keys, not the current set selector. Remove an entry with its **Remove key** button.
In one-key mode, using another set replaces the proposed key. Duplicate sets are
not added. With no selected attributes, adding a key proposes ∅ explicitly;
an empty list means no keys were proposed and is different from the empty key.

The workshop example accepts either `{person, workshop}` or `{email, workshop}`
for one-key mode, and requires both for all-keys mode. Feedback distinguishes a
set that fails to determine the relation, a nonminimal superkey and missing keys.
For a nonminimal set it shows members removable **individually**, not a license
to remove all of them together. The later examples show `{a}` and `{b,c}` as
equally valid inclusion-minimal keys, then a relation whose candidate key is ∅.
FDs are assumed business rules: accidental uniqueness in sample data proves none
of these claims.

## Implication and counterexamples

Choose **Follows** or **Does not follow**. For Follows, add FD steps starting with
the target's left-hand side. A valid proof only needs to reach every target
right-hand attribute; unlike closure mode, it need not reach the full closure.
A trivial implication can have an empty derivation. Irrelevant but productive
steps are allowed; invalid or unproductive steps are diagnosed.

For Does not follow, select which attributes have the **same value in both rows**.
The table shows Row 1 as all zeroes and Row 2 as zero for equal attributes and one
for differing attributes. It is displayed vertically so every column fits a phone.
These symbols represent equality, not real personal information. A counterexample
must satisfy **every given FD**, agree on the target's entire left side, and differ
on at least one target right-side attribute. The checker accepts any valid pair,
not only the author's example. Feedback distinguishes a violated premise from a
pair that does not actually violate the target.

The tutor need not determine the workshop: two rows can share a tutor and differ
elsewhere while satisfying the given FDs. Adding room equality without building
equality would instead violate the given `room -> building` rule.

All modes use the same feedback policy, private inspection, deliberate sharing,
reset and draft-conflict rules described above. Proof walkthrough controls appear
for closure and positive worked derivations. Key sets and negative witnesses are
shown in full after reveal; they do not offer a meaningless proof-step control.

## Author an activity

Copy the example deck and its sidecar. Each sidecar item names the content type
`io.github.stefanjdecker.fdlab.exercise`, a unique item ID, and a source path relative
to the master deck directory. Sources must stay within that directory. See
[closure.json](../examples/functional-dependencies/activities/closure.json) and the
[owned schema](../plugins/fd-lab/texstage_fd_lab/schemas/lesson-v1.json).

The source contains `format: 1`, an `exercise` with English/German title and prompt,
named attributes, named FD left/right sets and `task: {mode: "closure", start: [...]}`,
a `worked_answer` appropriate to the mode, a bilingual `explanation`, and
`feedback: "after-reveal"` or `"practice"`. Supported tasks and named answers are:

| Task | Worked answer |
| --- | --- |
| `{mode: "closure", start: ["workshop"]}` | `{mode: "closure", closure: ["workshop", "tutor", "room", "building"], steps: ["f3", "f4"]}` |
| `{mode: "keys", require: "one"}` (or `"all"`) | `{mode: "keys", keys: [["person", "workshop"]]}` (include all keys for `"all"`) |
| `{mode: "implication", lhs: ["workshop"], rhs: ["building"]}` | `{mode: "implication", implied: true, steps: ["f3", "f4"]}` |
| `{mode: "implication", lhs: ["tutor"], rhs: ["workshop"]}` | `{mode: "implication", implied: false, agree: ["tutor"]}` |

These object sketches omit JSON quotes around property names for readability;
the example source files contain complete valid JSON. After-reveal is the
assessment choice. Use meaningful short attribute IDs: these are also the names
shown in sets and printed proofs.

Preparation validates the envelope and independently verifies the worked answer,
then generates public data, private checking data and both TeX fragments from this
one source. A wrong worked answer stops the build. For keys it prepares a private
closure table and complete candidate-key list once; the reducer checks engine facts
using this table rather than repeating key search per student. For implication it
checks the derivation or the actual two symbolic rows. Exact exercise/answer identity
and certificate facts must match before grading. Neither tables nor withheld worked
answers are included in public projections. Duplicate dependencies with different IDs
are retained with a diagnostic.

Load the styles and place the item inside a frame:

```tex
\usepackage{texstage}
\usepackage{texstage-fd-lab}
% Item ID, width, height; the ID must match the activity sidecar:
\fdlab{closure}{.96\linewidth}{.78\textheight}
```

The wrapper calls the host's prepared-content command. It contains no separate
copy of the FD logic. Sidecar `language` selects English or German static fragments;
live controls use the host's UI language. Authored text is escaped as plain LaTeX.
Choose glyphs supported by the PDF fonts and review layout after enlarging tasks.

## Build print and slide editions

```sh
texstage build examples/functional-dependencies/lesson.tex --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile
texstage pdf examples/functional-dependencies/lesson.tex --handout --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile
texstage pdf examples/functional-dependencies/lesson.tex --solutions --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile
texstage prepare examples/functional-dependencies/lesson.tex --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile
```

`build` produces a live bundle and static PowerPoint. Ordinary slides, PowerPoint
and handouts show the exercise with writing space. The solution edition shows a
step table, key sets or a two-row witness, followed by the explanation. `prepare` prints direct-pdfLaTeX entry
points; compile those paths from the master deck's directory. Regenerate when a
source/provider changes rather than bypassing the freshness check.

Prepared build directories and bundle `keys.json` contain private material.
Distribute the intended PDF, or serve the bundle through TeXStage, which filters
private routes; do not publish the whole authoring/build directory. All given FDs
are public. Withholding feedback protects the answer release workflow, not the
ability of a student to solve a public mathematical task independently.

## Limits and development checks

The engine supports 1-8 attributes, 0-24 FDs, up to 256 proposed key sets and 8 productive proof steps,
including empty determinants, cycles and redundant/trivial FDs. Keep classroom
examples compact enough for the prepared slide box. The lesson stores one current
answer per actor, with a 64-actor pilot ceiling, 2 KiB reserved per actor slot and
160 KiB total state. The [performance follow-up](design/functional-dependencies-f4-performance.md)
tests 64 synthetic actors on one Windows computer. All three modes pass the
unchanged input and feedback targets in Chromium, Firefox and WebKit. WebKit
finishes the measured bursts in roughly 7 seconds after generic host caching
and scheduling fixes. The [initial F4 measurements](design/functional-dependencies-f4-validation.md)
retain the earlier failed runs. These loopback measurements do not guarantee
the same response times on a lecture network or physical phones.

Use the host changes pinned in that record for a classroom pilot. They preserve
the security limits while avoiding repeated schema checks and per-answer full
broadcasts. A replacement presenter can finish pending work when the old
connection closes. Without a presenter evaluator, answers remain pending;
service failure is never presented as a mathematically wrong answer.

In the isolated development environment:

```sh
python -m pytest plugins/fd-lab/tests -q --basetemp=artifacts/fd-tests
python maintenance/fd_probe.py
npm ci --ignore-scripts
npx playwright install chromium firefox webkit
node maintenance/fd_browser.cjs
node maintenance/fd_lesson_browser.cjs artifacts/fd-tests/test_installed_authoring_all_e0/out/lesson.bundle
node maintenance/fd_classroom_browser.cjs artifacts/fd-tests/test_installed_authoring_all_e0/out/lesson.bundle
```

Set `BROWSER=firefox` or `BROWSER=webkit` for the other engines (PowerShell:
`$env:BROWSER='firefox'`). Set `PYTHON` to the isolated interpreter. The export test
must actually execute with TeX installed to create the browser bundle. Tests check
installed wheels, both host validators, private transport, concurrent submissions,
reset, keyboard/touch controls at 320 px, and the unchanged restricted worker policy.
The classroom harness adds 64 protocol actors, one rendered participant and a real
presenter evaluator. Set `TEXSTAGE_CLASSROOM_RECONNECT=1` to include evaluator loss,
same-actor resume, receipt replay and reset/late-result checks. It records JSON
reports under `artifacts/fd-classroom/`, and exits nonzero when the provisional
timing targets fail. `TEXSTAGE_CLASSROOM_ENFORCE=0` is for collecting diagnostic
measurements only; it does not turn failed targets into passing evidence.

Desktop emulation does not establish physical-phone or full accessibility
coverage. English and German controls are supplied; the main browser
scenario currently exercises English.

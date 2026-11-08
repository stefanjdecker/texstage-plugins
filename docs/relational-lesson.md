# Using the Relational Algebra Lab lesson

This experimental plugin adds two prepared activities to TeXStage: construct a
query tree, and improve a supplied tree with checked rewrite rules. A presenter
opens submissions, inspects answers privately, optionally shares an anonymous
answer, and reveals the worked solution. Students build queries using labelled
operator controls, inspect intermediate tables, and apply rewrite rules by
selecting nodes. See the [visual editor guide](relational-editor.md).

The runnable example is [lesson.tex](../examples/relational/lesson.tex). It uses
a small library database, with one construction exercise and one rewrite
exercise. Its data and worked answers are synthetic public examples.

## Install in an isolated environment

Use Python 3.12+, the matching experimental TeXStage wheel, and pdfLaTeX/latexmk.
For development checks also use Node 24 and the host's hash-locked development
dependencies. Install the host requirements and wheel before building the
provider; the SDK is the package build backend.

The host must include prepared authoring, typed results, structured command
errors, atomic queue replacement and mount reconciliation. A version string
alone does not distinguish unpublished development builds. See the
[validation record](design/relational-editor-validation.md) for the exact
tested artifacts. Do not replace a course environment with this test environment.

The [classroom release handoff](transaction-relational-release.md) also covers
the unchanged 0.2.0 provider with the newer host candidate and supplies a
[physical-device checklist](classroom-device-checklist.md) for later acceptance.

From the collection root, with that environment activated:

```sh
python maintenance/build_wheels.py --package relational-lab
python -m pip install --no-deps dist/texstage_relational_lab-0.2.0-py3-none-any.whl
texstage plugins --data ./relational-profile inspect io.github.stefanjdecker.relationallab
```

Review the provider and copy the printed payload digest into the following command:

```sh
texstage plugins --data ./relational-profile enable io.github.stefanjdecker.relationallab --version 0.2.0 --payload <printed-payload>
texstage plugins --data ./relational-profile lock --output ./relational.lock.json
texstage present examples/relational/lesson.tex --activities examples/relational/lesson.activities.json --data ./relational-profile --plugins-lock ./relational.lock.json --no-tunnel
```

Installation and enablement are separate. Neither a slide upload nor a style
file installs a plugin. Start a fresh session after changing host/provider bytes;
existing experimental sessions retain their original runtime identity.

## Run the lesson

1. Navigate to **Who borrowed database books?** The slide and phones show the
   public task; phones expose the tables under **Example data**.
2. Select **Open answers**. Students choose a table, add operators, and apply
   typed node edits. **Result at this node** previews the selected operation on
   example data. **Save answer** submits explicitly; editing or previewing alone
   does not send an answer.
3. Keep the browser presenter open: its restricted worker evaluates saved
   answers. “Waiting for the presenter's computer” means saved but not yet
   evaluated. The presenter sees counts and can inspect one response privately.
4. Select **Close answers** before discussing results. Choose an answer and
   select **Share selected answer anonymously** to show it on the projector.
   Sharing is explicit; names and private check data are not projected.
5. Select **Reveal solution** to release the worked explanation and each
   student's own compact feedback. **Open answers** starts another round and
   clears the shared demonstration. **Reset activity** clears responses and
   starts a new epoch after confirmation.
6. On **Move filters earlier**, students select a node, choose a named rule and
   apply it. The tree and rule history update immediately. Undo/redo supports
   experimentation. The engine independently replays the saved rule sequence.

Two devices for the same student may create competing drafts. A newer saved
answer or reset prompts **Reload saved answer** or **Keep my draft**. Keeping
a draft never sends it automatically. Unrelated student updates preserve the
current typed fields, tree and focus. Returning after navigation starts from the saved answer;
unsaved drafts are local to the mounted activity.

Evaluation errors and capacity limits are operational problems, not wrong
answers. Existing saved answers remain available. The pilot ceiling is 64
responding actors per activity; replacements by existing actors are allowed.
This is a storage bound, not a measured classroom throughput claim.

Construction feedback means the answer passes the configured finite instances,
including private checks. It is not a general equivalence proof. Rewrite success
also requires a checked, nonempty rule sequence that reduces the public
intermediate-output-cell metric. That metric does not estimate database runtime.

## Internal answer format for authors and integrations

The visual editor produces this format automatically. Students need not read or
type JSON; source files and integrations keep their existing representation.

A construction answer contains postorder nodes. Child indices refer to earlier
nodes, and the last node is the root. For example, this returns the database-book
titles; it is a syntax example, not the answer to the borrower exercise:

```json
{
  "mode": "construct",
  "tree": [
    ["rel", "books"],
    ["select", 0, [["eq", ["a", "topic"], ["v", "db"]]]],
    ["project", 1, ["title"]]
  ]
}
```

`["a","topic"]` denotes an attribute and `["v","db"]` a literal. A predicate is
a conjunction of comparison triples. Supported nodes are relation (`rel`),
`select`, `project`, simultaneous `rename`, `product`, theta `join`, `union`
and `difference`. The
[frozen contract](design/relational-algebra-contract.md) specifies every form,
type, bound and error rule.

A rewrite answer contains checked rules and paths from the root. For example:

```json
{"mode":"rewrite","steps":[{"rule":"split-select","path":[0]}]}
```

A path uses `0` for a unary child or the left binary child, and `1` for the right
binary child. Each path applies to the tree resulting from earlier steps.
One step need not complete the optimization. The example source contains the
full worked sequence.

Answers allow at most 16 nodes or 8 rewrite steps and 1,800 characters in the
ASCII canonical JSON representation. The visual editor enforces those existing
bounds and reports an actionable error; it does not raise storage limits.
The host checks shape, lesson phase and actor version before accepting a command.

## Author another exercise

Each item in [lesson.activities.json](../examples/relational/lesson.activities.json)
selects `io.github.stefanjdecker.relationallab.tree` and a relative source path.
The source uses [lesson-v1.json](../plugins/relational-lab/texstage_relational_lab/schemas/lesson-v1.json):

- `format: 1`;
- `exercise`: the existing frozen engine exercise, with English/German title
  and prompt, typed relations, one public instance, optional private instances,
  task, and a reference tree or rewrite baseline;
- `worked_answer`: a construction tree or rewrite certificate in the frozen
  answer format;
- `explanation`: English/German plain text explaining the worked answer.

The authoring hook validates the source, independently computes expected
fixture digests in Python, and checks the worked answer before generating
public data, private checks and TeX fragments. An invalid worked answer stops
the build. Unicode is normalized for engine identity; source text is escaped
as plain LaTeX, never executed as supplied TeX. Use characters supported by your
pdfLaTeX fonts. Review layout when increasing tables, prompts or tree sizes.

Load and place the thin style wrapper:

```tex
\usepackage{texstage}
\usepackage{texstage-relational-tree}
% Inside a frame; "construct" must match an activity-sidecar item:
\relationaltree{construct}{.96\linewidth}{.72\textheight}
```

The three arguments are item ID, width and height. The wrapper delegates to
`\texstageprepared`; it owns no second copy of the exercise or grading rules.
The sidecar's `language` chooses the static fragment language. Live labels
follow the host's UI language.

## Generate the static editions

Run these from the collection root:

```sh
texstage build examples/relational/lesson.tex --activities examples/relational/lesson.activities.json --data ./relational-profile
texstage pdf examples/relational/lesson.tex --handout --activities examples/relational/lesson.activities.json --data ./relational-profile
texstage pdf examples/relational/lesson.tex --solutions --activities examples/relational/lesson.activities.json --data ./relational-profile
texstage prepare examples/relational/lesson.tex --activities examples/relational/lesson.activities.json --data ./relational-profile
```

`build` emits the live bundle and static PowerPoint. The ordinary/static slides
and handout contain the exercise; the solution edition contains the checked
answer and explanation. Native PowerPoint uses the static exercise fallback.

`prepare` prints local direct-pdfLaTeX entry points. Compile from the master
deck's directory using the printed path. These exports check input and provider
freshness and fail after source changes. Regenerate instead of bypassing the
check.

Prepared build directories and bundle `keys.json` contain private material.
Distribute the intended student PDF or serve the bundle with TeXStage; do not
publish the whole authoring/build directory. Reveal releases the worked answer
and compact feedback, not private fixtures, fixture digests or other students'
answers.

## Verify a development build

```sh
python -m pytest plugins/relational-lab/tests -q --basetemp=artifacts/lesson-tests
python maintenance/relational_probe.py
npm ci --ignore-scripts
npx playwright install chromium firefox webkit
node maintenance/relational_browser.cjs
node maintenance/relational_lesson_browser.cjs artifacts/lesson-tests/test_installed_authoring_all_e0/out/lesson.bundle
```

Set `BROWSER=firefox` or `BROWSER=webkit` in your shell for the other engines.
The lesson test requires pdfLaTeX and must actually run to provide that bundle.
The engine harness retains active CSP probes. The lesson harness checks the
real presenter, projector and two student devices, both modes, version
conflicts, privacy, sharing, reset and navigation at 320 pixels. These desktop
browser checks do not replace physical-phone, accessibility or classroom-load
validation.


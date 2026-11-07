# Authoring ER registration exercises

The experimental ER Modelling Decisions provider checks whether a proposed
model permits and excludes the situations described in an exercise. The
registration scenario asks about participation, the owner of registration
status, and a relationship versus an association entity. Both intended models
are accepted; finite examples do not prove general model equivalence.

Version 0.6.0 combines prepared LaTeX authoring with an interactive registration
lesson. One JSON source generates the public task, private evaluation binding,
exercise and checked solution material in English and German. Phone decision
cards and a model preview connect to presenter controls for inspection, sharing,
reveal and repair. See the [classroom guide](er-decisions-lesson.md) and
[lesson-state protocol](er-decisions-state.md).

## Install and enable

Use a separate Python 3.12+ environment, the matching experimental TeXStage
host, and pdfLaTeX with Beamer, Babel and TikZ. The
[validation record](design/er-points-validation.md) identifies the
tested host artifact; its development version alone is not a compatibility pin.
Install that host and its locked development/build dependencies first. From the
collection root, with this environment active:

```console
python maintenance/build_wheels.py --package er-decisions
python -m pip install --no-deps dist/texstage_er_decisions-0.6.0-py3-none-any.whl
texstage plugins --data ./er-profile inspect io.github.stefanjdecker.erdecisions
```

Copy the inspected payload digest into the enable command:

```console
texstage plugins --data ./er-profile enable io.github.stefanjdecker.erdecisions --version 0.6.0 --payload <printed-payload>
texstage plugins --data ./er-profile lock --output ./er.lock.json
texstage present examples/er-decisions/lesson.tex --activities examples/er-decisions/lesson.en.activities.json --data ./er-profile --plugins-lock ./er.lock.json --no-tunnel
```

Installation and enablement are separate. Neither the deck nor the style file
installs code. Re-enable the inspected payload and regenerate the lock after a
provider update. Keep this environment/profile separate from existing courses.
Node is needed for maintainer engine tests and worker regeneration, not for
ordinary installed-provider authoring.

## Use the example

The [English deck](../examples/er-decisions/lesson.tex) and
[German deck](../examples/er-decisions/lesson-de.tex) use the same
[source](../examples/er-decisions/activities/registrations.json).
The activity sidecar selects the item ID, content type, language and relative
source path:

```json
{
  "format": 1,
  "language": "en",
  "items": [{
    "id": "registrations",
    "type": "io.github.stefanjdecker.erdecisions.lesson",
    "source": "activities/registrations.json"
  }]
}
```

The thin style wrapper selects the prepared item:

```latex
\usepackage{texstage-er-decisions}
% Inside a Beamer frame:
\erdecisions{registrations}{.98\linewidth}{.87\textheight}
```

Arguments are item ID, width and height. The declared style namespace is `er`;
the exported command is `\erdecisions`. No exercise text or answer is duplicated
in the style. The sidecar chooses the fragment language; select the matching
Babel language in your deck. The examples use a 16:9 frame.

## Optional game points

Add `"points": 1000` at the top level of your lesson JSON (beside
`exercise`, `solutions` and `counterexamples`). The integer may be 0–10000.
Omitting it, or using 0, keeps the activity in practice mode.

A fully correct model earns the configured amount, including either accepted
registration representation. Wrong models earn zero; unavailable evaluation
does not count as an incorrect answer. Reasons and response speed do not affect
points. **Reveal alternatives** publishes awards to the normal game total,
rankings and results export. Until then, feedback and credit stay private.

Students can replace answers before reveal. After reveal a scored round stays
closed. **Reset activity** removes this activity's previous contribution and
allows another round; it does not accumulate repeated awards or erase points
from other activities. Practice rounds can still reopen for repair.

To try scoring without editing the tracked example:

```console
python maintenance/er_ui_bundle.py --output artifacts/er-scored --points 1000
```

Use `--language de` for the German version. The helper edits only its output
copy and prints the resulting bundle path. Both generated exercise and solution
PDFs state the maximum when points are enabled.

## Generate each edition

```console
texstage build examples/er-decisions/lesson.tex --activities examples/er-decisions/lesson.en.activities.json --data ./er-profile
texstage pdf examples/er-decisions/lesson.tex --handout --activities examples/er-decisions/lesson.en.activities.json --data ./er-profile
texstage pdf examples/er-decisions/lesson.tex --solutions --activities examples/er-decisions/lesson.en.activities.json --data ./er-profile
texstage prepare examples/er-decisions/lesson.tex --activities examples/er-decisions/lesson.en.activities.json --data ./er-profile
```

For German substitute `lesson-de.tex` and `lesson.de.activities.json`.
`build` emits the live bundle and static PowerPoint. The slide and handout
show a neutral diagram with unanswered decisions. Solutions show both checked
models, the explicit role bounds and two selected counterexamples. Bounds
labelled “Per Person” count registrations for each person, including people
with no registrations; they are not bounds on the opposite endpoint.

`prepare` prints local direct-pdfLaTeX entry points. Compile the printed path
from the master deck directory. These exports depend on the source, provider
and preparation inventory. Regenerate after changes; stale material fails.
Prepared directories and bundle `keys.json` contain private material. Serve
the bundle through TeXStage or distribute the intended PDF; do not distribute
the raw preparation directory as student material.

## Edit the source

The closed `schemas/lesson-v1.json` envelope contains:

| Field | Purpose |
| --- | --- |
| `exercise` | Frozen `er-registration-v1` engine seed: model, decisions, fixed requirements, public/private situations and worked answers |
| `title`, `labels` | English/German plain text for the task, entities, relationship and observed attribute |
| `requirements_de` | German wording keyed to every fixed requirement; English wording comes from the seed |
| `solutions` | An explanation in both languages for every configured worked answer |
| `counterexamples` | A candidate answer, a situation ID that contradicts it, and bilingual explanation |

Keep IDs stable when renaming labels. Preparation independently recompiles and
checks each worked alternative and confirms that each selected counterexample
contradicts its candidate. Explanatory prose remains an author's responsibility:
the engine checks the situations, not the meaning of arbitrary sentences.
All authored strings are escaped as plain text. Raw TeX, HTML, SVG and executable
predicates are not source fields.

The prepared layout is narrower than the engine: three decisions, one observed
attribute, at most four requirements, one public permitted example with at
most two links, and one or two solutions/counterexamples. Titles are limited
to 80 characters, labels to 40, brief text to 180, requirement text to 160,
and explanations to 150 per language. The complete source is limited to
128 KiB; the embedded engine retains its frozen limits. Always inspect your
rendered pages after editing, especially when using long labels or a different
frame size. Material taller than the command's height is scaled proportionally
to fit; short wording still gives the best readability. Character limits alone
cannot guarantee a good layout.

The public projection removes private situations, expected outcomes, worked
answers and evaluation seeds. Model properties controlled by a decision are
blank until answered; fixed model properties remain visible. Private data and
the evaluation binding are retained separately for the lesson workflow.
State schema 4 exposes four closed role projections and authenticated commands.
The interactive renderers preserve the static exercise until explicit sharing
or reveal. Public `interaction: decision-cards` identifies the phone editor.

## Verify changes

```console
python -m pytest plugins/er-decisions/tests -q --basetemp artifacts/er-tests
python maintenance/er_probe.py --output artifacts/er-engine
node maintenance/er_browser.cjs artifacts/er-engine
```

The authoring tests build both languages, all editions and direct-pdfLaTeX
exports using the installed wheel. They check public/private separation,
escaped text, invalid sources, source confinement, stale preparations and PDF
page bounds. See the validation record for rendered-page and browser evidence.
The existing engine security harness also supports `BROWSER=firefox` and
`BROWSER=webkit` with the corresponding installed Playwright browsers.
The static presenter/projector and lesson-protocol check is
`node maintenance/er_prepared_browser.cjs <built-lesson.bundle> <output-directory>`.
It uses the installed host/provider through a disposable loopback server and
authenticated protocol clients. The separate classroom harness described in
the [classroom guide](er-decisions-lesson.md) tests the actual editor and controls.
Set `PYTHON` to the test environment interpreter; use a different
`TEXSTAGE_TEST_PORT` when running browsers simultaneously.

Next: E5 physical-device, accessibility, capacity and release checks. Scoped
room identity and open requirements require later explicit engine profiles.

The 0.6.0 lesson requires the exactly tested TeXStage 0.2.1.dev5 host with bounded
item records and deterministic result reuse. See [600-student validation](design/er-600-validation.md).
Build a new bundle/profile/session; keep earlier sessions in their pinned environment.

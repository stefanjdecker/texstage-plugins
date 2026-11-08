# Authoring B+ tree exercises

The B+ Tree Operations Lab teaches how an index finds and changes entries.
Students follow page pointers, scan linked leaves, split full pages, borrow
from neighbours and merge underfull pages. Each exercise performs one operation
on a small tree with unique integer keys. Several different repair choices can
be correct.

Version 0.7.0 supplies the checked engine, **prepared LaTeX material** and
**interactive classroom views**. One JSON lesson produces the exercise, worked
solution, diagrams and live deck. Students build answers with structured phone
controls and local preview; presenters inspect, share and replay attempts.
See the [classroom guide](bplus-classroom.md) for the complete teaching workflow.

Use Chromium or Firefox as the presenter for large classes. The
[current capacity record](design/classroom-release-validation.md) includes
Linux WebKit crashes at 600 and 1,000; passing the ordinary UI checks does not
establish that browser's classroom-load reliability.

## Install and explicitly enable

Use a separate Python 3.12+ environment with the matching experimental
TeXStage host and its hash-locked build requirements. The
[scoring verification record](design/bplus-tree-scoring-validation.md) identifies the tested
host and plugin artifacts. The dependency `texstage>=0.2.1.dev6` alone does not
identify unpublished host changes.

The decks need pdfLaTeX, Beamer, TikZ/PGF, Babel English/German and Latin Modern
fonts. TeX Live supplies them. For a Debian/Ubuntu build environment the packages
are `texlive-latex-extra texlive-fonts-recommended texlive-lang-german lmodern`.
The provider style loads `texstage` and `tikz`; the examples select their language
and Latin Modern fonts.

After installing the compatible host in the fresh environment, run these
commands from the plugin collection root:

```console
python maintenance/build_wheels.py --package bplus-lab
python -m pip install --no-deps dist/texstage_bplus_lab-0.7.0-py3-none-any.whl
texstage plugins --data ./bplus-profile inspect io.github.stefanjdecker.bpluslab
```

Copy the printed payload digest into the enable command:

```console
texstage plugins --data ./bplus-profile enable io.github.stefanjdecker.bpluslab --version 0.7.0 --payload <printed-payload>
texstage plugins --data ./bplus-profile lock --output ./bplus.lock.json
texstage present examples/bplus/lesson.tex --activities examples/bplus/lesson.en.activities.json --data ./bplus-profile --plugins-lock ./bplus.lock.json --no-tunnel
```

Installation and enablement are separate. Loading a style or uploading a deck
never installs code. After a provider update inspect and enable its new
version/payload, regenerate the lock, rebuild the deck and restart the server.
Keep course environments and existing course pins separate.

## Start with the examples

The [English deck](../examples/bplus/lesson.tex) and
[German deck](../examples/bplus/lesson-de.tex) use the same six
[lesson sources](../examples/bplus/activities/lookup.json):

| Item | What it demonstrates |
| --- | --- |
| `lookup` | Equality at a separator routes right; records live in leaves |
| `range` | One descent followed by leaf links; both range endpoints are inclusive |
| `insert` | A leaf split copies the separator, preserving the entry |
| `delete` | Borrowing from the right sibling and updating the parent separator |
| `cascade` | Leaf, internal and root splits; height increases |
| `shrink` | Leaf/internal merges and automatic root contraction |

Each slide starts from its own printed tree. This is a progression of examples,
not six successive updates to one tree. Worked solutions are examples of legal
repairs, not the only acceptable answers.

The [layout stress deck](../examples/bplus/layout-stress.tex) includes an empty
tree, deletion of the last entry and a 40-entry input whose insertion produces
41 entries, 29 pages and height three. It uses a taller 4:3 page at 160 × 120 mm.
Its [German version](../examples/bplus/layout-stress-de.tex) uses the same data.

The six teaching sources set **points: 1000**; stress cases remain practice.
See the [grading rubric and scoreboard guide](bplus-scoring.md) for partial
credit, feedback release, replacement answers and reset behavior.

## Add a prepared item to a deck

Put the source JSON beneath the master deck directory. A sidecar binds the
source to the item and content type:

```json
{
  "format": 1,
  "language": "en",
  "items": [{
    "id": "insert",
    "type": "io.github.stefanjdecker.bpluslab.tree",
    "source": "activities/insert.json"
  }]
}
```

Source paths resolve relative to the master deck directory, including when the
sidecar is in a subdirectory. Traversal, absolute paths, symlinks and junctions
are rejected by the host. The provider must already be enabled.

Load the provider's declared style and place the item:

```latex
\usepackage{texstage-bplus-tree}
% Inside a Beamer frame:
\bplustree{insert}{.98\linewidth}{.90\textheight}
```

The three arguments are item ID, width and height. The `bplus` namespace exports
`\bplustree`. This thin wrapper calls the host's `\texstageprepared` and reserves
the box used by both static material and the live overlay. The style owns no
duplicate exercise data or independent answer.

Use the sidecar language `en` or `de` with matching Babel settings in the deck.
German variants such as `de-AT` select German. If a source has no German text,
its required English text is used and preparation emits a diagnostic.

## Edit a lesson source

Use [the insertion example](../examples/bplus/activities/insert.json) as a
complete template. The closed envelope has these fields:

| Field | Meaning |
| --- | --- |
| `format` | Integer `1` |
| `points` | Optional integer 0–10,000; omitted/zero means practice, positive values enable fixed scoreboard points |
| `title`, `prompt` | Plain-text `en` and optional `de` strings |
| `exercise` | The unchanged `bplus-operations-v1` engine seed |
| `worked.answer` | One complete path/read or repair certificate |
| `worked.explanation` | Plain-text English and optional German explanation |
| `feedback` | `on-reveal` withholds mathematical feedback until reveal; `immediate` releases it to its submitting student |

The envelope is limited to 20 KiB UTF-8 in canonical encoding. Titles allow
160 characters, prompts 800 and explanations 1,200 per language. Layout may
require shorter text. Author text is escaped as text, never executed as TeX.
Preparation checks the source tree, replays the worked certificate and requires
every applicable prediction to be correct. Wrong paths, incomplete repairs,
wrong returned keys, separators or height stop the build. Explanatory prose
still needs an author's mathematical review.

The engine seed specifies separate leaf-entry and internal-child capacities
from three through six, a flat initial tree rooted at page 0, and one task:
`lookup`, `range`, `insert` or `delete`. The
[engine guide](../plugins/bplus-lab/README.md) and
[contract](design/bplus-tree-contract.md) define the exact source/answer fields,
ID allocation, occupancy and separator rules.

## Read the diagrams

- `I` pages contain separator copies and downward child-page IDs.
- `L` pages contain the actual entries and an arrow to the next leaf.
- Small trees use connected diagrams. Wider trees use a page map in depth order;
  `d0` marks the root. Follow the explicit pointers rather than numeric page order.
- Blue borders in read solutions mark the descent/scan. Update solutions show
  the final tree; their descent text refers to the starting tree.
- A leaf split copies a key; an internal split promotes a separator.
  Height counts edges from root to leaf. An empty root leaf has height zero.

Leaf links always follow key order. In the insertion example the leaf sequence
is P1 → P2 → P4 → P3. Stable page IDs need not be sorted along the leaf chain.

The six teaching slides use a nearly full-frame box on 16:9 pages. Large trees
and long explanations need more space; use the taller stress-deck layout.
The style measures the content and allows at most an 18% excess over the
requested height before refusing the build. It does not silently shrink an
arbitrarily dense page. Give the box more height or shorten the prose when it
reports `Prepared B+ material is too tall`. Very narrow boxes are unsuitable
for a whole index; inspect the actual output at your intended display size.

## Generate the editions

```console
texstage build examples/bplus/lesson.tex --activities examples/bplus/lesson.en.activities.json --data ./bplus-profile --plugins-lock ./bplus.lock.json
texstage pdf examples/bplus/lesson.tex --handout --activities examples/bplus/lesson.en.activities.json --data ./bplus-profile --plugins-lock ./bplus.lock.json
texstage pdf examples/bplus/lesson.tex --solutions --activities examples/bplus/lesson.en.activities.json --data ./bplus-profile --plugins-lock ./bplus.lock.json
texstage prepare examples/bplus/lesson.tex --activities examples/bplus/lesson.en.activities.json --data ./bplus-profile --plugins-lock ./bplus.lock.json
```

For German use `lesson-de.tex` and `lesson.de.activities.json`. For the stress
deck use `layout-stress.tex` and `layout-stress.en.activities.json`.

`build` produces the live bundle and `*-static.pptx`. The live slide, handout
and static PowerPoint show the unanswered exercise. Solutions show the checked
result and repair explanation. All editions bind the same preparation identity.

`prepare` prints local handout, solutions and present entry points for direct
pdfLaTeX. Run from the master deck directory, using the actual printed path:

```console
pdflatex -output-directory=texquiz-out texquiz-out/prepared-XYZ/lesson-handout-prepared.tex
```

These entry points depend on the local source, installed provider and prepared
files. Regenerate after changes; changed source, fragments or approved style
bytes are rejected. No plugin code runs from the direct TeX entry point.

## Privacy and troubleshooting

The public item contains the title, prompt and starting exercise. The worked
answer, facts, explanation and evaluation binding remain private. Generated
fragments and raw source JSON are not public bundle routes. Four audience views
have live phone, private-control and overlay renderers. Students receive
their own saved answer and permitted feedback. Presenter inspection is private.
An explicitly shared answer is anonymous and contains submitted predictions only
before reveal. Reveal releases the worked answer and mathematical feedback.
Reset starts a new epoch and clears submissions; it is required after reveal
before starting another round.

Local preparation directories and the bundle's private `keys.json` contain
solutions. Serve bundles through TeXStage or share the intended exercise PDFs
and static PowerPoint. Do not give students the raw preparation directory or a
raw bundle directory containing private files.

| Symptom | Action |
| --- | --- |
| Provider not enabled or identity mismatch | Inspect and enable the exact installed payload; rebuild with a matching lock |
| Style missing | Use the enabled profile with `--data`; do not copy the style into a course |
| Worked certificate rejected | Check the path, bottom-up repairs and every final separator/height claim |
| Stale prepared input | Run `texstage prepare` again after source/provider changes |
| Prepared material too tall | Increase the box/page height or shorten the prose |
| No phone answer controls | Install/enable the 0.7.0 payload, rebuild the bundle and start a fresh session with the matching host |
| Submit is disabled | Finish the required fields, resolve any device/reset conflict, and wait for the presenter to open answers |
| Saved feedback stays pending | Keep an authenticated presenter evaluator open; check the host's operational status |
| Draft differs from saved feedback | Submit explicitly to replace the saved version; local preview and saved grade are separate |

## Maintainer checks and remaining work

Use the isolated installed-wheel engine tests and probes from the engine guide.
The additional authoring and real-deck checks are:

```console
python -m pytest plugins/bplus-lab/tests -q --basetemp=artifacts/bplus-tests
python maintenance/bplus_authoring_probe.py --output artifacts/bplus-prepared
node maintenance/bplus_prepared_browser.cjs <tested-lesson-bundle> artifacts/bplus-prepared-browser
node maintenance/bplus_classroom_browser.cjs <tested-lesson-bundle> artifacts/bplus-classroom
node maintenance/bplus_ui_browser.cjs <tested-lesson-bundle> artifacts/bplus-ui
```

The authoring probe requires a new output directory and pdfLaTeX. It runs both
languages and layouts, saves rendered PDF/PPT images, verifies edition identity,
checks public/private separation and rejects a changed source. Its report
prints the bundle path for the browser command. Use `BROWSER=firefox` or
`BROWSER=webkit` (PowerShell: `$env:BROWSER='firefox'`) for the other browsers.

See the [B4 validation record](design/bplus-tree-b4-validation.md) for actual
local evidence and the exact matching host artifact, including unpublished host
changes needed for locale and keyboard handling. Run the UI probe with the
German bundle and `BPLUS_LANGUAGE=de` as well. Physical-phone tests, measured
classroom capacity, hosted CI/Windows-Linux transfer and publication remain gates.

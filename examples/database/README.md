# Campus database activity lab

**A campus database, many ways to reason** extends the original library deck.
It contains **70 logical slides and 53 interactive examples**: ten quizzes covering
all nine built-in quiz types, twelve SQL/SPARQL/Turtle/shared-graph activities,
and 31 plugin activities. All data is fictional.

Start with the [master LaTeX source](database.tex), [coverage map](COVERAGE.md),
and [teaching notes](TEACHING.md), or the [German master](database-de.tex).
Each frame or quiz has a separate file in [slides/](slides/) (English) and
[slides-de/](slides-de/) (German). The [activity sidecar](database.activities.json) binds 30
prepared exercises to local JSON sources; the coordinate example uses inline
LaTeX. The [provider list](required-plugins.json) records all ten package versions.

This is a collection for several lessons. Use the short route in TEACHING.md
for an instructor-led tour, or choose a topic and allow several minutes per
activity. Each section declares its own data and rules; the plugin examples do
not share mutable state with the SQL/RDF seed.

## Activity families

| Area | Examples |
| --- | --- |
| Quizzes | Choice, multiple choice, true/false, numeric slider, text, ordering, sketch, open response and poll |
| Queries and graphs | SQL filter/join/count/anti-join/bags; SPARQL SELECT/ASK/CONSTRUCT; Turtle; both shared-graph input forms |
| Coordinates | Choose a point and distinguish location from distance |
| ER decisions | Multiplicities, attribute ownership, relationship or association entity |
| Relational algebra | Construct a tree, inspect intermediate tables, apply checked rewrite rules |
| Physical plans | Scan/index, selectivity, join order/method and hash memory |
| B+ trees | Lookup, range, insertion, deletion, cascading split and root shrink |
| Dependencies | Closure, one/all keys, proofs, counterexamples, key sizes and empty key |
| Normalization | Classify normal form; check decomposition, losslessness and FD preservation |
| Transactions | Predict, inspect, diagnose and repair six schedules |

The original freehand ER sketch remains a discussion task. ER Decisions checks
its constrained registration choices, not arbitrary drawings. Maximum-size
stress fixtures remain in the focused example directories.

## Install

Use Python 3.12+, Node 24 for the reference checker, and pdfLaTeX/latexmk with
Beamer, English/German Babel, Latin Modern, booktabs and TikZ. Use a fresh virtual
environment, not a course environment. See the
[host installation guide](https://github.com/stefanjdecker/texstage/blob/main/docs/installation.md).

Use TeXStage commit
[79d5f3d76b6dd9f6348e65672867d00e40a70ef0](https://github.com/stefanjdecker/texstage/commit/79d5f3d76b6dd9f6348e65672867d00e40a70ef0)
on **codex/database-activity-examples**, or a later compatible revision. It includes
the WebKit worker fix, lets plugin input replace retained SQL/Turtle feedback,
and makes the phone follow the deck language from PIN entry onward. The development
version string alone does not identify these fixes. From that matching host checkout:

    python -m pip install --require-hashes -r requirements/dev.txt
    python -m build --wheel --no-isolation
    python -m pip install --no-deps dist/texstage-0.2.1.dev7-py3-none-any.whl

With the same environment active, from this plugin collection's root:

    python maintenance/build_wheels.py
    python -m pip install --no-deps dist/texstage_example_distance-0.1.0-py3-none-any.whl dist/texstage_example_coordinates-0.1.0-py3-none-any.whl dist/texstage_transaction_engine-0.1.0-py3-none-any.whl dist/texstage_transaction_activity-0.1.0-py3-none-any.whl dist/texstage_relational_lab-0.2.0-py3-none-any.whl
    python -m pip install --no-deps dist/texstage_bplus_lab-0.7.0-py3-none-any.whl dist/texstage_er_decisions-0.6.0-py3-none-any.whl dist/texstage_query_plan-0.7.0-py3-none-any.whl dist/texstage_fd_lab-0.6.0-py3-none-any.whl dist/texstage_normalization_workshop-0.5.0-py3-none-any.whl

The build helper expects one artifact version per package; use a clean checkout.
No catalog release is assumed. Inspect the installed identities and digests:

    python examples/database/configure.py

After reviewing these trusted packages, explicitly enable this example's ten
providers and write their lock:

    python examples/database/configure.py --enable-reviewed

The helper checks versions before making changes. It never installs code and
refuses an example profile containing unrelated providers. Its disposable profile
and portable plugin lock live under examples/database/texquiz-out, ignored by Git.
Opening a slide or uploading a bundle does not install or enable plugins.

## Build and present

Run from the collection root with the same environment active:

    texstage build examples/database/database.tex --activities examples/database/database.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json --stage --deck database-activities
    texstage pdf examples/database/database.tex --handout --activities examples/database/database.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json
    texstage pdf examples/database/database.tex --solutions --activities examples/database/database.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json
    texstage present examples/database/database.tex --activities examples/database/database.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json --deck database-activities --port 8767 --no-tunnel

Use a free port. Keep the presenter open while its workers evaluate answers.
Open the projector window and have students join using the displayed address and
PIN. Loopback works only on the same computer; phones need the reachable LAN
address. Use the [device checklist](../../docs/classroom-device-checklist.md)
for physical-device and classroom-network rehearsal.

The explicit activities argument is required. Changed JSON sources need a
rebuild; present with that argument rebuilds them. One source produces live data,
exercise fragments and checked worked solutions.

## Language

Choose a matching master and sidecar. Both editions have 70 slides and 53 examples,
with translated questions, explanations and presenter notes:

| Edition | Master | Sidecar language | Babel |
| --- | --- | --- | --- |
| English | [database.tex](database.tex) | [database.activities.json](database.activities.json): `en` | `english` |
| German | [database-de.tex](database-de.tex) | [database-de.activities.json](database-de.activities.json): `de` | `ngerman` |

Babel selects live plugin labels on presenter, projector and phone. The sidecar
selects generated exercises and solutions. Keep both aligned. All eight classroom
plugin interfaces support both languages, including the coordinate warm-up.

After installation and explicit enablement, use these German commands from the
collection root:

    texstage build examples/database/database-de.tex --activities examples/database/database-de.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json --stage --deck database-activities-de
    texstage pdf examples/database/database-de.tex --handout --activities examples/database/database-de.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json
    texstage pdf examples/database/database-de.tex --solutions --activities examples/database/database-de.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json
    texstage present examples/database/database-de.tex --activities examples/database/database-de.activities.json --data examples/database/texquiz-out/profile --plugins-lock examples/database/texquiz-out/plugins.lock.json --deck database-activities-de --port 8767 --no-tunnel

Phone joining, waiting messages, quizzes, built-in activities and plugin
controls follow the deck language, even when the browser uses another language.
The language is selected as soon as a valid PIN is known, including from a QR
link. Before then, the browser language is the fallback. There is no
per-student plugin language switch. See the [language guide](../../docs/languages.md).

Both editions share [database-common.tex](database-common.tex) for layout,
[database-sequence.tex](database-sequence.tex) for order, and all exercise data
and answers. SQL names, book titles and RDF identifiers retain their original
spelling so the checked problems stay identical. Selecting a language does not
translate arbitrary authored text automatically.

German output names use `database-de`; English uses `database`.

## Generated files

| Output under texquiz-out | Use |
| --- | --- |
| database.bundle/ and database.bundle.zip | Browser presentation and uploadable bundle |
| database-static.pptx | Static PowerPoint; plugin controls are not live here |
| database.pptx | PowerPoint with supported built-in quiz add-ins |
| database-handout.pdf | Exercise edition; built-in quizzes use neutral handout placeholders |
| database-solutions.pdf | Worked solutions, quiz answers and reference code |
| build/database-stage.pdf | Browser-stage PDF; TeXStage supplies live controls separately |
| profile/ and plugins.lock.json | Local session data and explicit provider pins |

Give students the intended handout, not a generated preparation directory
containing worked material. Public browser routes exclude private keys and answers.

## Run a section

Explain the printed data. For most plugin lessons, open answers, allow thinking
time, ask for an explicit save, wait for checking, close answers, inspect privately,
share anonymously if useful, and reveal the evidence. Transactions have Predict,
Inspect, Diagnose, Repair and Reveal phases. Coordinates use Send point,
Reveal point and Reset responses.

SQL/SPARQL/Turtle activities have no quiz timer. Use two independent participants
for the shared graph's agreement threshold, or set Minimum to one for solo
rehearsal. Approve contributed labels in the three-field graph.

B+ and normalization use fixed points; FD includes scored and practice variants;
query-plan examples use 120-second quiz rounds. Other plugin examples are
formative. Built-in quizzes award no points. See
[the scoring table](TEACHING.md#facilitation-and-scoring) before teaching this mixed
deck; it is not a balanced graded examination.

## Edit and verify

1. Edit one slide file and its translation, keeping the activity ID stable.
2. Change prepared sources under activities/. Paths are relative to database.tex
   and must stay beneath that directory.
3. Add a new prepared item to both sidecars and update database-sequence.tex,
   COVERAGE.md and activity-index.json. Keep the worked answer with the exercise
   so preparation checks it.
4. Rebuild, inspect exercise and solution pages, and rehearse the affected
   presenter/phone interaction.

The built-in reference checker uses the installed host's actual browser engines:

    node examples/database/verify.mjs

PYTHON selects the environment's interpreter; TEXSTAGE_WEB can explicitly choose
another host web directory. The checker covers all ten code references, valid
alternatives, plausible errors, duplicates, NULL, RDF identifiers and refused SQL
mutations. Finite example checks are not general query-equivalence proofs.

[VALIDATION.md](VALIDATION.md) records the combined build, coverage, PDF review
and browser checks actually run. Focused package tests remain the deeper
engine/runtime evidence.

After building both editions, the reproducible browser smoke check uses the
collection's pinned Playwright and the installed host/provider wheels. It starts
and stops a disposable loopback server and enables the installed providers only
in its temporary test profile. Use it with the trusted example environment above.
For example, in PowerShell:

```powershell
npm ci --ignore-scripts
npx playwright install chromium firefox webkit
$env:PYTHON = (Get-Command python).Source
foreach ($language in @('en', 'de')) {
    $env:LANGUAGE = $language
    foreach ($browser in @('chromium', 'firefox', 'webkit')) {
        $env:BROWSER = $browser
        node examples/database/browser-smoke.cjs
        if ($LASTEXITCODE -ne 0) { throw 'Browser check failed' }
    }
}
```

The checker intentionally uses the opposite browser locale by default:
English deck/German browser and German deck/English browser. `BROWSER_LOCALE`
overrides that choice; `TEXSTAGE_TEST_PORT` selects a free port (default 18811).
Reports and screenshots stay under ignored `texquiz-out/browser-tests/`.

## Source provenance

The built-in material extends the earlier local TeXStage database example.
Prepared JSON sources are adapted copies of the focused examples listed in
activity-index.json. They stay local because authoring paths cannot escape the
master directory; transaction headings/prompts identify the individual scenarios.
This combined copy can be edited independently.
No original repository, course or private media is required or changed.

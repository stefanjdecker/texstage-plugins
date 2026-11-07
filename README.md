# Texstage plugins

Independent example packages and the starting point for a reviewed plugin
collection. This is the experimental
[GitHub collection](https://github.com/stefanjdecker/texstage-plugins); the catalog has no published
releases yet. Install packages separately from Texstage and explicitly enable them
in a disposable operator profile. Uploading a lecture never installs code.

| Package | Capability | LaTeX |
| --- | --- | --- |
| `texstage-example-distance` | Browser engine `org.example.distance.euclidean` | None |
| `texstage-example-coordinates` | Slide type `org.example.coordinates.plane`, using the distance engine | `texstage-coordinates-plane.sty` |
| `texstage-transaction-engine` | Independent schedule analysis engine | None |
| `texstage-transaction-activity` | Prepared prediction, diagnosis and repair lesson | `texstage-transactions-schedule.sty` / `transactionsschedule` |
| `texstage-relational-lab` | Set-algebra engine and prepared query-tree lesson (R3/R4) | `texstage-relational-tree.sty` |
| `texstage-bplus-lab` | B+ operations, prepared lessons and up to 1,000 student answers | `texstage-bplus-tree.sty` / `\bplustree` |
| `texstage-er-decisions` | ER registration activity: phone decisions, model preview and discussion | `texstage-er-decisions.sty` / `\erdecisions` |
| `texstage-query-plan` | Query-plan selectors, cost inspection and classroom activity (Q0–Q4) | `\queryplanchallenge` |
| `texstage-fd-lab` | Closure, candidate-key and implication lessons (F1-F3) | `\fdlab{id}{width}{height}` |
| `texstage-normalization-workshop` | Normalization, comparison and evidence | `texstage-normalization-workshop.sty` / `\normalizationworkshop` |

The [collection validation record](docs/design/plugin-collection-validation-2026-11-07.md)
records the previous nine-package baseline. The [transaction validation](docs/design/transaction-classroom-validation.md) adds the tenth package and the compatible host changes.

The coordinate slide accepts a phone response, displays class points on the
projector, gives distance feedback from the presenter browser, and supports reveal
and reset. Distance is supplementary: `(0,5)` and `(3,4)` have the same distance,
but correctness compares both coordinates. PDFs and PowerPoint retain a static
diagram. The two packages have their own manifests, versions and portable wheels.

## Normalization Workshop

The [workshop guide](docs/normalization-workshop.md) explains installation,
checked LaTeX authoring, native phone editing and presenter-led discussion.
Students classify relations or propose decompositions; the analyzer checks
normal form, lossless joins and FD preservation independently. Valid answers
need not match the worked example. Presenters can compare two saved answers,
share checked evidence and reveal the solution.
Chase playback and concrete counterexamples explain lossless joins and lost FDs.

Start with the [seven-slide example](examples/normalization/lesson.tex).
Version 0.5.0 adds configurable fixed activity points, published on reveal.
Only the latest verified answer counts; repeated saves never accumulate points
and reset withdraws the activity's award. The examples award 1,000 points each;
older lessons remain practice. Use TeXStage 0.2.1.dev7 or newer with these contracts.
The [points validation](docs/design/normalization-workshop-points-validation.md)
and [capacity record](docs/design/normalization-workshop-600-validation.md)
separate correctness for 600 students and a 1,000-answer ceiling from measured
latency and classroom acceptance.
No catalog release is published.

The [discussion contract](docs/design/normalization-workshop-discussion-contract.md),
[N4 validation record](docs/design/normalization-workshop-n4-validation.md) and
[implementation plan](docs/design/normalization-workshop-plan.md) describe the
discussion workflow and remaining usability, classroom and release gates.
The independent design checker remains available:
`python maintenance/check_normalization_design.py`.

## Transaction schedules: classroom activity

The [lesson guide](docs/transactions-lesson.md) covers installation of the engine
and activity wheels, prepared LaTeX, the six bilingual examples, and the phone,
presenter and projector flow. Students predict values, inspect remembered reads,
diagnose direct conflicts with witnesses and certificates, and reorder operation
cards to repair a schedule. Different valid repairs are accepted. Feedback is
released in stages; version 1 awards no scoreboard points.

The [contract](docs/design/transaction-classroom-contract.md) describes actor
records, privacy, guarded commands and recovery. The [validation record](docs/design/transaction-classroom-validation.md)
distinguishes implemented behavior, measured capacity and remaining release gates.
The [completion plan](docs/design/transaction-schedules-plan.md) remains the
acceptance checklist. The standalone engine still works without the activity.

```sh
python maintenance/check_transaction_design.py
```

## Relational algebra: prepared lessons and checked answers

The [Relational Algebra Lab design](docs/design/relational-algebra.md) covers
building query trees, inspecting intermediate relations and applying verified
rewrite rules. The package now supplies the engine, prepared authoring,
lesson state, presenter controls and a basic JSON answer editor on phones.
The visual tree editor and public-data preview are the next milestone.
Matching example datasets is explicitly distinguished from proving
equivalence through checked rules.

The [implementation plan](docs/design/relational-algebra-plan.md) lists the
package files, shared host prerequisites and acceptance gates. The
[worked library examples](docs/design/relational-algebra/README.md) include
exercise sources and checked expected results. Reproduce their finite
checks with `python maintenance/check_relational_design.py`.

The [relational engine](plugins/relational-lab/README.md) now implements the eight
operator forms and checked rewrite certificates in an installable wheel. The
[v1 contract](docs/design/relational-algebra-contract.md) and
[validation record](docs/design/relational-algebra-r2-validation.md) document the
independent Python model, installed-wheel checks and browser limits.
The [lesson guide](docs/relational-lesson.md) explains installation, the
[\relationaltree example deck](examples/relational/lesson.tex), answer syntax,
phases, anonymous sharing and static exports. The
[R3/R4 validation record](docs/design/relational-algebra-lesson-validation.md)
records installed-wheel authoring and browser checks. Physical-phone testing
and measured classroom load remain release gates.

## Query-plan Challenge: interactive physical plans

The [Query-plan package](plugins/query-plan/README.md) lets students select scans,
join order, join methods and hash build inputs for a fixed query. It offers
phone selectors, local cost comparison and node arithmetic, undo and explicit
submission. Presenter controls support collection, private inspection, anonymous
sharing, reveal and reset. Drafts survive unrelated updates and same-user
conflicts require an explicit keep/reload choice.

Version 0.7.0 adds [quiz speed points and shared streak bonuses](docs/query-plan-points.md), contributing
to the normal total, leaderboard and CSV export. It retains bounded per-student storage and a presenter roster with 25
answers per page. See the [quiz-points validation](docs/design/query-plan-quiz-points-validation.md)
for current checks and the [600-student validation](docs/design/query-plan-600-validation.md)
for the earlier 0.5.0 measurements and recovery scenarios.

The [classroom guide](docs/query-plan-lesson.md) explains how to run it.
[Prepared authoring](docs/query-plan-authoring.md) generates exercises, private
worked answers and static exports from the
[four-activity example](examples/query-plan/lesson.tex).
The [Q4 evidence](docs/design/query-plan-ui-validation.md) supplements the
[engine](docs/design/query-plan-engine-validation.md),
[authoring](docs/design/query-plan-authoring-validation.md) and
[state](docs/design/query-plan-state-validation.md) records.

The historical [Q5 validation record](docs/design/query-plan-release-validation.md) adds
Windows/Linux artifact checks, measured 64-participant load and evaluator recovery.
The [release procedure](docs/query-plan-release-checks.md) covers the dedicated CI
workflow and remaining manual checks. Costs are teaching units, not database timings.
This remains an experimental local candidate: physical-phone LAN and screen-reader
checks, a published compatible host pin and successful hosted jobs are still
[release gates](docs/design/query-plan-challenge-plan.md).

## Functional dependencies and keys: classroom lessons

The [FD Lab design](docs/design/functional-dependencies.md) proposes guided
attribute closure, one/all candidate keys, and FD implication with checked
derivations or two-row counterexamples. The [implementation plan](docs/design/functional-dependencies-plan.md)
separates engine, prepared lessons, phone interfaces and classroom release gates.
The [draft contract](docs/design/functional-dependencies-contract.md) and
[synthetic examples](docs/design/functional-dependencies/README.md) make the
semantics reviewable. The [FD Lab package](plugins/fd-lab/README.md) supplies closure, candidate-key
and implication reasoning plus prepared lessons for all three modes (F1-F3).
Students choose FD steps, assemble one/all keys or construct a two-row counterexample;
presenters control feedback release, anonymous sharing and worked-proof walkthroughs. The [lesson guide](docs/fd-lesson.md) covers
installation, authoring and static editions. See the [F1 engine record](docs/design/functional-dependencies-f1-validation.md)
and [F2 closure record](docs/design/functional-dependencies-f2-validation.md), followed
by the [F3 classroom record](docs/design/functional-dependencies-f3-validation.md) and
[F4 load/reconnect measurements](docs/design/functional-dependencies-f4-validation.md).
A [German guide](docs/fd-lesson-de.md) is also available. The
[performance follow-up](docs/design/functional-dependencies-f4-performance.md)
records earlier passing 64-answer runs. The
[F5 report](docs/design/functional-dependencies-f5-validation.md) records passing
hosted CI with English/German authoring and identical artifacts on Windows and
three browsers, plus unresolved local input-latency and WebKit setup checks.
FD Lab 0.6.0 uses the common typed actor records and points APIs, with 25-answer
presenter pages and a 1,000-student storage ceiling. Optional fixed points are
released on reveal and appear in totals, rankings and CSV exports. It requires
the matching integration host; rebuild bundles and start fresh sessions.
Prepared lessons now grade from private, bounded reference data in the provider
hook; feedback no longer waits for a presenter browser worker. The standalone
engine remains available. See the [600-student performance record](docs/design/functional-dependencies-prepared-validation.md),
[publication merge validation](docs/design/functional-dependencies-publication-validation.md)
and [release procedure](docs/fd-release.md). Earlier capacity reports retain their
own artifact identities and timing limits.
The security policy is unchanged. Physical-phone checks and catalog publication
remain separate gates.

```sh
python maintenance/check_fd_design.py
```

The checker needs `jsonschema` from the compatible host's development lock.
It verifies design fixtures and tiny theories; it is not plugin conformance.

## ER Modelling Decisions: interactive registration pilot

The [ER provider](plugins/er-decisions/README.md) combines the registration
engine, [bilingual prepared authoring](docs/er-decisions-authoring.md) and an
interactive [classroom workflow](docs/er-decisions-lesson.md). Students make
modelling decisions, preview the constraints, save and repair their answers.
Presenters inspect privately, share anonymously with optional reasons, and
reveal both accepted models and selected counterexamples.

Version 0.6.0 supports 600 answering students with [bounded records and guarded
lesson state](docs/er-decisions-state.md), retaining field-error focus, visible
conflict recovery and stable status messages. It requires the matching TeXStage
0.2.1.dev5 or newer, with these contracts and a fresh session; the current
validation covers 0.2.1.dev6 and the compatible 0.2.1.dev7 handoff.
The [keyboard/accessibility guide](docs/er-decisions-accessibility.md) and
[validation record](docs/design/er-accessibility-validation.md) cover both
languages in Chromium, Firefox and WebKit, with the worker restrictions intact.
The [600-student validation](docs/design/er-600-validation.md) records earlier
artifacts and synthetic load results; the [release checklist](docs/er-decisions-release.md)
distinguishes these from deployment validation. Physical phones, screen-reader speech output, deployment tests
and hosted CI remain open. Room identity and open assumptions require later
engine profiles; see the [implementation plan](docs/design/er-modelling-decisions-plan.md).

Optional `"points": 1000` awards a fully correct model on reveal, using the
normal game total and rankings. Practice remains the default. See the
[scoring guide](docs/er-decisions-authoring.md#optional-game-points) and
[current points validation](docs/design/er-points-validation.md).

## B+ tree operations: interactive classroom activities

The [B+ provider](plugins/bplus-lab/README.md) version 0.7.0 combines its checked
lookup/range/insert/delete engine with [prepared LaTeX authoring](docs/bplus-lesson.md)
and [phone and presenter views](docs/bplus-classroom.md).
One JSON source generates English/German exercises, diagrams and checked solutions.
The [example decks](examples/bplus/README.md) cover all four operations,
cascading splits, root shrink and layout boundaries.

Students build answers with structured fields, undo/redo and local replay
preview, then submit explicitly. Presenters inspect privately, share anonymously,
reveal/reset and step through attempts or worked solutions. Saved feedback stays
separate from local preview; drafts survive peer updates and expose device/reset
conflicts. Version 0.7.0 supports 1,000 saved student answers with the matching
manifest-4 host with actor records. For classes approaching 1,000, use Chrome or
Firefox for the presenter: the Windows WebKit presenter intermittently crashed
at that load. See the [current measurements](docs/design/bplus-tree-scoring-validation.md).
The [partial-credit rubric](docs/bplus-scoring.md) now connects optional fixed
points to TeXStage's scoreboard and CSV on reveal. Sources without **points**
remain practice activities. The [scoring record](docs/design/bplus-tree-scoring-validation.md)
identifies the 0.7.0 artifacts and capacity measurements. The
[rebase integration record](docs/design/bplus-tree-rebase-validation.md) gives
the current compatible host commit and CI pin.
The physical-phone/campus-network pilot and publication gates remain open.

See the [B1 engine record](docs/design/bplus-tree-b1-validation.md),
[B2 authoring record](docs/design/bplus-tree-b2-validation.md),
[B3 classroom record](docs/design/bplus-tree-b3-validation.md),
[B4 visual UI record](docs/design/bplus-tree-b4-validation.md),
[contract](docs/design/bplus-tree-contract.md) and [plan](docs/design/bplus-tree-plan.md).
The [original 30 design examples](docs/design/bplus-tree/README.md) remain
independent finite evidence alongside installed-wheel and real-browser checks.

## Worker browser compatibility

The transaction and relational engines now use generated, self-contained ES module
entries. The matching Texstage worker fix loads them in Chrome, Firefox and WebKit
without widening its security policy. See the
[validation and reproduction record](docs/design/worker-browser-compatibility.md)
for exact artifacts, active security checks and remaining classroom gates.
When changing engine source modules, run `npm ci --ignore-scripts` followed by
`npm run build:workers`; commit the generated files. `npm run check:workers`
verifies they match source. No bundler is needed by someone installing the wheels.

## Build and try

First install the experimental Texstage branch's wheel and locked development
dependencies into a fresh Python 3.12+ virtual environment. This repository uses
its `texstage.plugins.sdk` build backend; the older development candidate lacks it.
You also need pdfLaTeX and latexmk for the authoring checks.

```sh
python maintenance/build_wheels.py --package distance --package coordinates
python -m pip install --no-deps dist/texstage_example_distance-0.1.0-py3-none-any.whl dist/texstage_example_coordinates-0.1.0-py3-none-any.whl
texstage plugins --data ./plugin-profile list
texstage plugins --data ./plugin-profile inspect org.example.distance
texstage plugins --data ./plugin-profile inspect org.example.coordinates
```

Review the code and manifests, then enable each package with its exact displayed
payload digest:

```sh
texstage plugins --data ./plugin-profile enable org.example.distance --version 0.1.0 --payload <distance-payload>
texstage plugins --data ./plugin-profile enable org.example.coordinates --version 0.1.0 --payload <coordinates-payload>
texstage plugins --data ./plugin-profile lock --output ./plugins.lock.json
texstage build examples/plane.tex --data ./plugin-profile --plugins-lock ./plugins.lock.json
texstage serve examples/texquiz-out --data ./plugin-profile --present
```

Start on the second slide and join from a phone. Reveal and reset are presenter
controls. The teacher's browser must remain open to evaluate queued jobs. The
reference coordinates stay private until reveal. See [the source example](examples/plane.tex)
and Texstage's `docs/plugins.md` for the SDK contracts and operational limits.

## Verify

Keep the coordinate/distance pair and transaction engine in separate test
environments. The original tests deliberately require exactly the two example
providers. For engine-only installation and tests, follow the
[engine README](plugins/transaction-engine/README.md).

```sh
python -c "from pathlib import Path; Path('artifacts').mkdir(exist_ok=True)"
python -m pytest tests -q --basetemp=artifacts/checks
npm ci
npx playwright install chromium
node maintenance/browser_conformance.cjs artifacts/checks/plugins-installed0/out/plane.bundle
```

Use `BROWSER=firefox` or `BROWSER=webkit` with the corresponding installed Playwright
browser. On PowerShell use `$env:BROWSER='firefox'`. `PYTHON` selects the virtual
environment interpreter; `TEXSTAGE_BROWSER_CHANNEL=chrome` or `msedge` selects a
local Chromium browser. All browser checks launch a temporary loopback server and
use synthetic identities. Results and screenshots go under `artifacts/`.

The build helper verifies that a source-distribution rebuild produces the same
provider manifest and resource hashes. The Python tests use installed wheels,
check role separation and private data, and exercise the independent engine
binding. The browser tests cover presenter/projector/phone screens, keyboard and
touch input, reset, teardown, blocked evaluator network access and timeouts.
`TEXSTAGE_TEST_BUNDLE` selects a bundle built on another machine for the portability
test, instead of compiling it locally.

The CI workflows require a full reviewed host commit in `texstage_ref`. The
default is `6b64828b98e9908fc67c265cab31a71a216308d5`, merged into TeXStage `main`
on GitHub and its GitLab mirror. The FD capacity job is opt-in with the
`capacity` workflow input. Local checks do not establish a passing hosted run. Transaction CI has a
separate engine-only Linux job (including Chromium, Firefox and WebKit) and a
Windows job consuming the identical Linux-built wheels. A compatible H1/H2 host
commit is included in the newer capacity host; release evidence still needs
the actual hosted run for the selected revisions.

## Collection layout

`plugins/` contains independently buildable packages. `examples/` contains the
synthetic lecture. `catalog/index.json` lists only reviewed, published wheel
releases; an empty index is intentional during development. `maintenance/` builds
and validates packages and prepares catalog changes. Nothing is loaded from GitHub
while a lecture is running.

After the API's release gates pass, publish a wheel under an immutable per-plugin
release tag, then prepare a catalog entry:

```sh
python maintenance/catalog_entry.py dist/texstage_example_distance-0.1.0-py3-none-any.whl --url https://github.com/OWNER/texstage-plugins/releases/download/distance-v0.1.0/texstage_example_distance-0.1.0-py3-none-any.whl
```

The helper changes the local index only. Review and commit it separately. Never
replace release bytes or reuse a version. Mark a broken release as withdrawn and
publish a new version. Operator refresh pins the index to a complete GitHub commit
SHA; offline installations use verified cached wheels and never enable them.

Python hooks and browser renderers are trusted code, with the operator's privileges.
They are not a way to run unreviewed third-party code safely. The API remains
experimental until the full Texstage design's conformance and release gates pass.

Licensed under [Apache-2.0](LICENSE). These examples contain no course material.

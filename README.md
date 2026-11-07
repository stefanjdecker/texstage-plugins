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
| `texstage-transaction-engine` | Schedule analysis engine `io.github.stefanjdecker.transactionengine.schedule` (M2) | None; lesson package pending |
| `texstage-relational-lab` | Set-algebra engine and prepared query-tree lesson (R3/R4) | `texstage-relational-tree.sty` |
| `texstage-query-plan` | Query-plan selectors, cost inspection and classroom activity (Q0–Q4) | `\queryplanchallenge` |
| `texstage-fd-lab` | Closure, candidate-key and implication lessons (F1-F3) | `\fdlab{id}{width}{height}` |
| `texstage-normalization-workshop` | Normalization, comparison and evidence | `texstage-normalization-workshop.sty` / `\normalizationworkshop` |

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

Start with the [seven-slide example](examples/normalization/lesson.tex).
Version 0.4.0 supports bounded records for a 600-student target and a 1,000-answer
ceiling. The [capacity record](docs/design/normalization-workshop-600-validation.md)
separates correctness from measured latency and classroom acceptance.
No catalog release is published.

## Transaction schedules: implemented engine, planned lesson

The [transaction-schedule design](docs/design/transaction-schedules.md) specifies
prediction, stepped execution, conflict-graph construction and schedule repair.
The [implementation plan](docs/design/transaction-schedules-plan.md) identifies
package files, host prerequisites and acceptance gates. A draft exercise schema,
nine synthetic expected cases and an independent design checker accompany it:

```sh
python maintenance/check_transaction_design.py
```

Run the checker after installing the compatible host's locked development
dependencies. The [independent transaction engine](plugins/transaction-engine/README.md)
is now implemented as a third installable wheel. It computes remembered reads,
final values, direct conflict witnesses, and cycle or serial-order certificates.
Its installed-wheel tests cover all 1,742 legal interleavings of the six small
exercise programs. An isolated probe writes results for a lost update and repairs.
The lesson package, LaTeX command, staged feedback and phone/presenter interfaces
remain pending.

The matching local host branch now implements typed results, revision-2 view schemas
and epoch-guarded reset. Its H2 follow-up now prepares explicit activity JSON
before LaTeX, generates live/static editions together, and exports local
direct-pdfLaTeX entry points.
Use its updated wheel: the coordinate example now uses the SDK's
`evaluation_correlation` helper to keep different participants' jobs separate.

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
passes the unchanged 64-answer targets in Chromium, Firefox and WebKit, with
fresh isolated workers and the same security policy. Physical-phone checks are
deferred; compatible published host pins and release CI remain separate gates.

```sh
python maintenance/check_fd_design.py
```

The checker needs `jsonschema` from the compatible host's development lock.
It verifies design fixtures and tiny theories; it is not plugin conformance.


## B+ tree operations: interactive classroom activities

The [B+ provider](plugins/bplus-lab/README.md) version 0.4.0 combines its checked
lookup/range/insert/delete engine with [prepared LaTeX authoring](docs/bplus-lesson.md)
and [phone and presenter views](docs/bplus-classroom.md).
One JSON source generates English/German exercises, diagrams and checked solutions.
The [example decks](examples/bplus/README.md) cover all four operations,
cascading splits, root shrink and layout boundaries.

Students build answers with structured fields, undo/redo and local replay
preview, then submit explicitly. Presenters inspect privately, share anonymously,
reveal/reset and step through attempts or worked solutions. Saved feedback stays
separate from local preview; drafts survive peer updates and expose device/reset
conflicts. The physical-phone pilot and release/load measurements remain open.

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

The CI workflows require a host revision containing the experimental API. Until
that revision reaches Texstage's default branch, run the workflow manually with
its compatible branch or commit in `texstage_ref`. The default-branch CI runs
become usable once the host implementation is published. Transaction CI has a
separate engine-only Linux job (including Chromium, Firefox and WebKit) and a
Windows job consuming the identical Linux-built wheels. A compatible H1/H2 host
commit still needs publishing and pinning; local passes do not mean hosted CI ran.

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

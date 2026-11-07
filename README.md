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
| `texstage-fd-lab` | Closure, candidate-key and implication lessons (F1-F3) | `\fdlab{id}{width}{height}` |

The coordinate slide accepts a phone response, displays class points on the
projector, gives distance feedback from the presenter browser, and supports reveal
and reset. Distance is supplementary: `(0,5)` and `(3,4)` have the same distance,
but correctness compares both coordinates. PDFs and PowerPoint retain a static
diagram. The two packages have their own manifests, versions and portable wheels.

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
FD Lab 0.5.0 uses the common typed actor records and points APIs, with 25-answer
presenter pages and a 1,000-student storage ceiling. Optional fixed points are
released on reveal and appear in totals, rankings and CSV exports. It requires
the matching integration host; rebuild bundles and start fresh sessions.
See the [integration record](docs/design/functional-dependencies-points-validation.md)
and [release procedure](docs/fd-release.md). Earlier capacity reports retain their
own artifact identities and timing limits.
The security policy is unchanged. Physical-phone checks and catalog publication
remain separate gates.

```sh
python maintenance/check_fd_design.py
```

The checker needs `jsonschema` from the compatible host's development lock.
It verifies design fixtures and tiny theories; it is not plugin conformance.


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

The CI workflows require a full reviewed host commit in `texstage_ref`. This
integration branch pins `7b9934d91f3affcc54e2ab6573c8c662cc87348a`; publish that host
commit before pushing this collection branch. Local checks do not establish a
passing hosted run. Transaction CI has a
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

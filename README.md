# Texstage plugins

Independent example packages and the starting point for a reviewed plugin
collection. This is an experimental local repository; the catalog has no published
releases yet. Install packages separately from Texstage and explicitly enable them
in a disposable operator profile. Uploading a lecture never installs code.

| Package | Capability | LaTeX |
| --- | --- | --- |
| `texstage-example-distance` | Browser engine `org.example.distance.euclidean` | None |
| `texstage-example-coordinates` | Slide type `org.example.coordinates.plane`, using the distance engine | `texstage-coordinates-plane.sty` |

The coordinate slide accepts a phone response, displays class points on the
projector, gives distance feedback from the presenter browser, and supports reveal
and reset. Distance is supplementary: `(0,5)` and `(3,4)` have the same distance,
but correctness compares both coordinates. PDFs and PowerPoint retain a static
diagram. The two packages have their own manifests, versions and portable wheels.

## Build and try

First install the experimental Texstage branch's wheel and locked development
dependencies into a fresh Python 3.12+ virtual environment. This repository uses
its `texstage.plugins.sdk` build backend; the older development candidate lacks it.
You also need pdfLaTeX and latexmk for the authoring checks.

```sh
python maintenance/build_wheels.py
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
become usable once the host implementation is published.

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

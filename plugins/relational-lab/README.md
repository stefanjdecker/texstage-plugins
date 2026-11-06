# Relational Algebra Lab

Experimental, independently installable engine and prepared lesson for named
set relational algebra and checked rewrite certificates. The lesson includes
phased submissions, private checks, anonymous sharing, reveal/reset controls
and a basic JSON answer editor. The graphical tree editor and cooperative
local preview remain the next milestone.

Start with the [lesson guide](../../docs/relational-lesson.md) for installation,
the example deck, LaTeX authoring, answer syntax and classroom workflow.

The Python model and browser engine evaluate the same finite contract through
independent implementations. Returned relation digests are facts, not grades:
matching finite instances is not a proof of general equivalence.

## Supported behavior

The eight forms are relation, selection, projection, simultaneous rename,
product, theta join, union and difference. Relations have named, typed attributes
and set semantics. Values are bounded integers, NFC text or booleans; there is
no NULL, implicit coercion or SQL bag behavior.

Rewrite submissions contain rule names and paths. The engine derives each
successor and checks its side conditions. It supports splitting selections,
pushing selections into either join/product input, converting a filtered product
to a theta join, and collapsing nested projections.

Inputs, intermediates, total work and outputs are bounded. Malformed submissions
return `syntax`; well-formed invalid queries return typed reason facts; exhausted
resource budgets return `refused`. A failed evaluation is never an incorrect grade.
Each loaded engine state accepts one submission and can then be disposed.

See the [frozen v1 contract](../../docs/design/relational-algebra-contract.md),
[design](../../docs/design/relational-algebra.md), and
[validation record](../../docs/design/relational-algebra-r2-validation.md).

## Build and check an isolated installation

Use Python 3.12+ and Node 24 with the matching experimental Texstage wheel and
its hash-locked development dependencies already installed in a fresh virtual
environment. The host must include H1 typed contracts and H2's current SDK;
`texstage>=0.2.1.dev3` alone does not identify those unpublished changes.
Use the host wheel/payload recorded with the validation evidence.

From the collection root:

The checked-in worker entry is built from the modular sources using pinned
esbuild. Before packaging edited JavaScript, run `npm ci --ignore-scripts` and
`npm run build:workers`. CI checks freshness with `npm run check:workers`.
Python wheel/sdist builds and end-user installs consume the committed output;
they do not invoke Node. Do not edit the generated `*.worker.mjs` files by hand.
Both the source modules and bundle remain hashed provider resources.

```sh
python maintenance/build_wheels.py --package relational-lab
python -m pip install --no-deps dist/texstage_relational_lab-0.1.0-py3-none-any.whl
python -m pytest plugins/relational-lab/tests -q
python maintenance/relational_probe.py
```

The probe loads the installed provider resources, evaluates the library examples
in Node without WebCrypto, and checks actual JavaScript and Python host result
contracts. It writes outcomes, artifact identities and browser inputs under
`artifacts/relational-lab/`.

For the actual host evaluator:

```sh
npm ci
npx playwright install chromium firefox webkit
node maintenance/relational_browser.cjs
```

Select `BROWSER=firefox` or `BROWSER=webkit` using the current shell. On PowerShell,
use `$env:BROWSER='firefox'`. For an installed Chrome/Edge browser, set
`TEXSTAGE_BROWSER_CHANNEL` to `chrome` or `msedge`. The harness serves the installed
host modules with the actual worker policy; it does not relax that policy.
The [worker compatibility record](../../docs/design/worker-browser-compatibility.md)
supersedes the earlier Firefox/WebKit startup failures: both now pass with the
fixed matching host and bundled engine, without widening the worker policy.
The probe actively checks blocked connections, nested workers and dynamic code,
invalid typed results, timeout termination and recovery.

Keep these tests separate from the original coordinate/distance pair's exact
provider tests. The workflow has independent domain/package, browser and Windows
artifact-consumer jobs. Hosted runs still require a published compatible host.

## Engine binding and independent Python model

Provider: `io.github.stefanjdecker.relationallab`.
Engine: `io.github.stefanjdecker.relationallab.algebra`.
Content type: `io.github.stefanjdecker.relationallab.tree`.
Style: `texstage-relational-tree.sty`, providing
`\relationaltree{item-id}{width}{height}` around the host's prepared box.
The lesson envelope in `schemas/lesson-v1.json` adds a checked worked answer
and bilingual explanation around the unchanged engine seed.

The UTF-8 seed is a validated exercise source, with empty options. A construction
input is `{"mode":"construct","tree":[...]}`; a rewrite input is
`{"mode":"rewrite","steps":[...]}`. The seed fixes the task mode. A client cannot
switch modes to bypass checks. Keep evaluation references empty; canonical
equality is not construction correctness.

The installed fixtures contain a complete seed for each mode and worked answers:

```python
from importlib.resources import files
from texstage_relational_lab import model

raw = files("texstage_relational_lab").joinpath(
    "fixtures/construct.exercise.json"
).read_text(encoding="utf-8")
exercise = model.source(model.parse(raw))
submission = {"mode": "construct", "tree": exercise["reference_tree"]}
facts = model.analyze(exercise, submission)
diagnostics = model.source_diagnostics(exercise)
```

`evaluate_tree` additionally returns a relation and public-sized trace for
preparation tools. `source_diagnostics` identifies duplicate source tuples that
normalize to a set. This model is independently implemented from the browser
engine. The supplied examples and tests are synthetic and public.

Installation does not enable a provider. Inspect and explicitly enable a reviewed
payload in an isolated Texstage operator profile before using the lesson
binding. Deck uploads never install or enable code.

## Remaining classroom work

Prepared authoring, static exports, bounded lesson state, independent grading
policy and role-filtered views are implemented and covered by
[the R3/R4 checks](../../docs/design/relational-algebra-lesson-validation.md).
The JSON editor makes that workflow executable; it is not the planned visual
tree editor. Cooperative preview, intermediate-result inspection, physical-phone
interaction checks and measured 64-participant load remain release gates.

No catalog release is published by this milestone.

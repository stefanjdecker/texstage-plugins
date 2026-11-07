# TeXStage Functional Dependencies and Keys Lab

Experimental engine and prepared classroom lessons (F1-F3), version 0.3.0. This wheel computes attribute
closures, checks derivation steps, enumerates candidate keys exactly and checks
FD implication using derivations or two-row counterexamples. It returns typed
mathematical facts, not grades. The lesson adds LaTeX exercise/solution editions,
phased classroom state, phone editors for closure, one/all keys and implication,
plus presenter walkthrough/sharing. The counterexample editor shows two symbolic
rows and checks all premise FDs. [English](../../docs/fd-lesson.md) and
[German](../../docs/fd-lesson-de.md) guides explain the complete workflow.

Provider: `io.github.stefanjdecker.fdlab`.
Engine: `io.github.stefanjdecker.fdlab.dependencies`.
The distribution is `texstage-fd-lab`; Python module `texstage_fd_lab`.
Use the matching experimental host with manifest revision 2 and typed result
contracts. The package's development version constraint is not a release pin.

## Build and verify in isolation

Install the compatible host wheel and its locked development dependencies in
a fresh Python 3.12+ environment. Never modify an existing course environment.
From the collection root:

```sh
npm ci --ignore-scripts
npm run check:workers
python maintenance/build_wheels.py --package fd-lab
python -m pip install --no-deps dist/texstage_fd_lab-0.3.0-py3-none-any.whl
python -m pytest plugins/fd-lab/tests -q --basetemp=artifacts/fd-tests
python maintenance/fd_probe.py --output artifacts/fd-lab
npx playwright install chromium firefox webkit
node maintenance/fd_browser.cjs artifacts/fd-lab
node maintenance/fd_lesson_browser.cjs artifacts/fd-tests/test_installed_authoring_all_e0/out/lesson.bundle
```

Set `BROWSER=firefox` or `BROWSER=webkit` to run the other browsers; PowerShell
uses `$env:BROWSER='firefox'`. Set `PYTHON` to this environment's interpreter
when a harness needs it. The original example pair and other engines have their
own isolated test environments; keep their exact-provider assertions intact.
`npm run build:workers` regenerates the self-contained engine entry after edits.
Installing the wheel does not require Node or a bundler.

The lesson export test requires pdfLaTeX, Beamer, Latin Modern and English/German
Babel support and must execute to supply the lesson browser bundle.

The build helper checks wheel/sdist resource parity. Tests use installed files,
the independent Python model, both real host validators, hand-derived cases,
tiny exhaustive theories, strict parsing and lifecycle failures. The browser
probe uses installed host evaluator modules and the unchanged worker CSP,
including active network/worker restrictions, invalid-result rejection,
timeouts, cleanup and recovery. Local success does not establish hosted CI,
physical-phone usability or classroom throughput.

## Inputs and mathematical facts

The engine seed is compact JSON with `format`, `id`, ordered attribute IDs,
ordered FD records `{id,lhs,rhs}` and a task. The integer masks denote sets in
the declared attribute order; teachers use named authoring and students use FD/set controls in the closure
lesson. Options must be `{}`.

```json
{"format":1,"id":"example","attributes":["a","b","c"],
 "fds":[{"id":"f1","lhs":1,"rhs":6},{"id":"f2","lhs":6,"rhs":1}],
 "task":{"mode":"keys","require":"all"}}
```

An answer `{"format":1,"mode":"keys","keys":[1,6]}` proposes `{A}` and
`{B,C}`. Both are minimal by inclusion despite their different sizes. Facts
contain the full candidate-key list and `[submittedMask,closure,removableMask]`
checks. A set with no removable members is only a candidate key if its closure
is the entire relation.

Closure answers contain `closure` and FD-index `steps`. Implication answers
contain either `implied:true` with `steps`, or `implied:false` with `agree`.
The latter selects the columns on which two symbolic rows agree; the engine
checks every premise FD and whether the target is violated. Different valid
proofs, keys and counterexamples can have different canonical identities.

See the [lesson guide](../../docs/fd-lesson.md) and
[example deck](../../examples/functional-dependencies/lesson.tex), plus the [v1 contract](../../docs/design/functional-dependencies-contract.md),
[design](../../docs/design/functional-dependencies.md) and
[implementation plan](../../docs/design/functional-dependencies-plan.md).
Owned schemas and synthetic fixtures ship inside the wheel. Python
`model.compile_lesson(named_lesson)` validates the proposed named envelope and
its worked answer, returning `(seed, answer)`; the separate `authoring.prepare_lesson` hook generates the prepared classroom
activity and TeX fragments. `model.analyze(seed, answer)` is an independent oracle.

Bounds: 1–8 attributes, 0–24 FDs, at most 8 productive proof steps, 256 proposed
keys, 1,800 canonical answer bytes and 65,536 FD checks. Empty determinants,
empty keys, composite right sides, cycles and trivial/redundant FDs are supported.
Malformed answers return `syntax`; mathematical mistakes return analysis facts;
resource limits return `refused`. Each loaded state accepts one evaluation.
The host supervises startup, the two-second execution deadline and disposal.

The [F4 classroom record](../../docs/design/functional-dependencies-f4-validation.md)
measures 64-answer bursts and evaluator replacement using this unchanged 0.3.0
provider and a newer host build. It documents the remaining WebKit latency gate;
physical-phone validation is still pending. Use its exact host artifact pin for
a pilot rather than relying on the development version string alone.

To use an engine in an operator profile, inspect it and explicitly enable the
exact displayed payload with `texstage plugins --data ./fd-profile enable` and
its ID, `--version` and `--payload`; then create a plugin lock. An uploaded deck
or style never installs or enables code. Do not add this prototype to the public
release catalog until immutable artifacts and host compatibility are published.

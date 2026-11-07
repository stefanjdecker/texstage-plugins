# TeXStage Normalization Workshop

Experimental analyzer and prepared classroom workshop with an independent
Python verifier. Version 0.4.0 targets 600 students with a ceiling of 1,000 saved
answers per activity, transactional answer records and 16-entry presenter pages.
Private two-answer comparison works across pages. Engine, participant and
authoring formats remain unchanged; state and presenter/projector views use v3.
Start with the [workshop guide](../../docs/normalization-workshop.md)
and [seven-slide example](../../examples/normalization/lesson.tex).

It checks normal forms (1NF assumed; 2NF, 3NF and BCNF diagnosed), candidate keys,
attribute coverage, dependency preservation and lossless decomposition under
functional dependencies. These are separate properties. Distinct valid
decompositions are accepted by the published task policy, not by equality with
a teacher's answer.

The model has 1–8 attributes, up to 32 singleton FDs, and at most eight component
relations. It uses all implied projected FDs. Multiway losslessness uses an FD
chase; a saturated losing tableau is a checked finite counterexample. No SQL
execution, sample-based FD inference, NULLs, MVDs or higher normal forms.

## Build and install

Use the experimental host artifact identified in the
[600-student validation record](../../docs/design/normalization-workshop-600-validation.md).
The minimum dependency is `texstage>=0.2.1.dev4`; it must include bounded item
records, actor-scoped updates and deterministic successful-result reuse.
A development version alone does not identify these unpublished contracts.
Create a disposable environment; do not upgrade a course environment.

From the collection root, after installing that host wheel and its locked
development/build dependencies:

```sh
python maintenance/build_normalization_schemas.py --check
npm ci --ignore-scripts
npm run check:workers
python maintenance/build_wheels.py --package normalization-workshop
python -m pip install --no-deps dist/texstage_normalization_workshop-0.4.0-py3-none-any.whl
python -m pytest plugins/normalization-workshop/tests -q
python maintenance/normalization_probe.py --output artifacts/normalization
node maintenance/normalization_browser.cjs artifacts/normalization
```

The browser probe also accepts `BROWSER=firefox` or `BROWSER=webkit` in the
environment; on PowerShell use `$env:BROWSER='firefox'`. Install the matching
locked Playwright browsers first. It checks the actual installed host worker
and unchanged CSP, not a substitute evaluator.

Providers remain disabled until explicitly enabled. Inspect the installed
provider and use the exact reported version/payload when enabling it:

```sh
texstage plugins --data ./normalization-profile inspect io.github.stefanjdecker.normalizationworkshop
texstage plugins --data ./normalization-profile enable io.github.stefanjdecker.normalizationworkshop --version 0.4.0 --payload <reviewed-payload>
texstage plugins --data ./normalization-profile lock --output ./normalization.lock.json
```

The engine ID is `io.github.stefanjdecker.normalizationworkshop.analyze`.
The content type is `io.github.stefanjdecker.normalizationworkshop.workshop`.
Its optional style exports `\normalizationworkshop{item}{width}{height}`.
No catalog release has been published.

## Compiled engine input

Attribute order gives bits: A=1, B=2, C=4. FDs are sorted, distinct,
nontrivial singleton pairs; the empty determinant is 0.

```json
{
  "format": 1, "id": "chain", "attributes": ["A","B","C"],
  "fds": [[1,2],[2,4]],
  "task": {"mode":"decompose","target":"bcnf","preserve":true}
}
```

Submit `{"mode":"decompose","relations":[3,6]}` for AB,BC.
The analyzer reports BCNF components, coverage, losslessness and preservation.
AB,AC (`[3,5]`) is also lossless and BCNF, but loses B -> C.

For classification, the seed task is `{"mode":"classify"}`; an answer is
`{"mode":"classify","normal_form":"2nf","witness":[2,4]}`. That witness explains
the chain's 3NF violation. A BCNF claim uses `"witness":null`. Full schemas and
semantic rules are in `texstage_normalization_workshop/schemas/` and the
collection contract document.

Results contain facts, identities and replayable evidence. `status:"ok"` means
analysis succeeded, not that the answer satisfies the lesson policy. Missing
coverage leaves join/preservation facts null. Malformed answers return
`syntax`; deterministic resource limits return `refused`; the host owns
timeouts and authentication. No reference equality binding is needed.

## Python verification and author source

```python
from texstage_normalization_workshop import model
checked = model.check_lesson(lesson_json_object)
facts = model.analyze(checked["seed"], checked["answer"])
assert model.verify_analysis(checked["seed"], checked["answer"], facts)
assert model.accepted(checked["seed"], checked["answer"], facts["facts"])
```

The named lesson envelope is compiled by `compile_lesson` / `check_lesson`.
It validates and checks a worked answer. `authoring.prepare_lesson` uses that
checked source to generate live data and escaped exercise/solution TeX.
The independent verifier checks exact facts for the submitted answer, including
identities and certificates. The host must additionally verify the binding
namespace, lease, epoch and current answer version.

The content capability declares versioned command/view schemas. Version 0.4.0
requires a newly built bundle and fresh session; it does not migrate v1/v2 state.
All nineteen frozen v1/v2 schema files remain unchanged. The reducer
stores at most 1,000 pseudonymous records outside the small shared state, checks
evaluation facts independently,
and withholds personal feedback until reveal. Handouts, solutions and local
direct-pdfLaTeX exports derive from the same checked source.

See [N4 evidence](../../docs/design/normalization-workshop-n4-validation.md) and
the [discussion contract](../../docs/design/normalization-workshop-discussion-contract.md).
The guide explains answer-only sharing versus sharing checks, and the difference
between a legal lossy-join counterexample and an instance that violates a lost FD.
Keyboard-only German browser flows and native Chrome 200% zoom are covered by
the accessibility harness. Human screen-reader/learner review, physical phones
and classroom load remain gates.

At most 16 roster entries plus four selected/shared records are read for a
presenter control view; a participant reads only their own record. Counts update
incrementally. Successful identical inputs may reuse the host's bounded result
cache, while every actor retains a separate guarded job and verification.
Do not submit two whole-class activities at once: the session queue remains
bounded at 1,000 pending jobs. See the guide for overload, restart and migration
instructions and the validation record for measured limits.

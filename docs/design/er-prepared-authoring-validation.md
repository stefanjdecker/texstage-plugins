# ER registration prepared-authoring validation

Validated on 2026-11-06. This records the registration slice of E2 in
provider **0.2.0**: prepared authoring, bilingual static material and useful live
fallback. The frozen registration engine is unchanged. Stateful classroom
interaction remains E3/E4; this is not a complete classroom or release claim.

The [machine-readable record](er-prepared-authoring-validation.json) contains
browser results, sizes and output hashes. The earlier
[E1 record](er-registration-engine-validation.md) remains historical evidence
for the 0.1.0 engine artifact.

## Exact artifacts

- Host commit: `de3351550f3553ca63023554521fbe84806ec94e`, version `0.2.1.dev3`.
- Host wheel SHA-256: `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`.
- Installed host payload SHA-256: `e41e8bbb8463111ee7d62f8c0b92c4dda736bc5df9ce558b9d7e813d06efcb23`.
- Provider wheel: `texstage_er_decisions-0.2.0-py3-none-any.whl`.
- Provider wheel SHA-256: `ff3a3b1562ade858368839dae1cfc0a4b9821a0fffbdc151122469ca9d1d7ce3`.
- Provider payload: `a44f87ecd753ccdeb75b885e7088185818fc7674d2a30763b4b7dc4cf6252b47`.
- Collection base: `5f00b62f6292de01e4eca067c8acd96dddf67eb9` on `codex/plugin-system`,
  with the ER authoring changes tested before commit.

The portable wheel and source distribution were rebuilt with the existing
SDK backend; manifest/resource payload parity passed. Tests imported the
installed provider from an isolated environment, not the source directory.
The matching host's locked development/build requirements were used. Runtime:
Windows, Python 3.14.4, Node v24.15.0, TeX Live 2026.

## Checks completed

**77 tests passed, none failed or skipped (84.72 s).** These retain all engine
checks and add prepared-source semantics, both worked models, genuine selected
counterexamples, masked unanswered properties, private/public separation,
plain-text escaping, invalid source rejection, source confinement, disabled
provider diagnostics and stale source/provider/fragment detection.

Real host builds covered English, German and long German labels: live stage,
handout, solutions, static PowerPoint and direct-pdfLaTeX exports. Solutions
are absent from exercise/stage text and public deck data; `keys.json` is not
available through the public bundle file API. Direct exports reject changed
source bytes. PDF character bounds and overfull-box checks pass.

Rendered exercise/solution pages were visually inspected. Review found and
fixed vertical clipping, attribute/diamond overlap, first-word German
hyphenation and overlap between a long relationship diamond and entity boxes.
Diagrams now place endpoints relative to the relationship boundary; the
fragment fits the command's requested height proportionally when necessary.
The four final example PDFs have hashes in the JSON record. Long-label pages
were inspected separately. Authors must still preview their own wording.

Real installed-host presenter/projector checks passed in Chromium 151.0.7922.34,
Firefox 153.0 and WebKit 26.5. Both transparent overlay modules loaded, the PDF
slide remained visible, role views were empty, private evaluation/solution data
was absent, and no page errors occurred. The browser check also caught and
fixed the required overlay `place` lifecycle method.

All three browser families reran the actual host evaluator against this
provider payload: 27 model combinations plus malformed-input/options/binding
and recovery cases, 31 samples per browser. The independent Python/Node
comparison agrees. Production worker CSP remains:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Active probes confirm that network requests, child/blob workers, external
modules, eval and Function construction are blocked, while the corresponding
unrestricted control probes work. Invalid results fail, a busy loop times out,
the next evaluation succeeds, and no workers remain after each evaluation.

## Measured scope and remaining work

The standard English/German preparation response is at most 16,134 bytes in
ASCII JSON, with a largest UTF-8 fragment of 3,127 bytes. Public data is 2,588
bytes; private teaching data 3,329 bytes; the evaluation binding 4,229 bytes.
Observed in-process preparation was under 30 ms. These are sample measurements,
not maximum-envelope capacity or authoring-worker startup benchmarks.

The new authoring envelope is deliberately narrower than the frozen engine:
three decisions, one observed attribute, four requirements and small example
sets. Full lesson state/view/effect capacities remain unmeasured. There is no
phone editing, submission, open/close/reveal/reset workflow, actor queue or
classroom-load claim. Rooms and open requirements require future profiles.
Public CI/release, Linux installation, physical phones and screen-reader checks
remain later gates. No host changes were needed.

## Reproduce

Follow the [authoring guide](../er-decisions-authoring.md) using the exact
host artifact above in a separate environment. Build/install the provider,
then run:

```console
python -m pytest plugins/er-decisions/tests -q --basetemp artifacts/er-tests
python maintenance/er_probe.py --output artifacts/er-engine
node maintenance/er_browser.cjs artifacts/er-engine
node maintenance/er_prepared_browser.cjs <built-lesson.bundle> artifacts/er-prepared
```

The test creates the built bundle in its English edition's `out` directory.
Set `PYTHON` to the environment interpreter. Repeat browser checks with
`BROWSER=firefox` and `BROWSER=webkit` after installing those Playwright binaries.
Use separate `TEXSTAGE_TEST_PORT` values for simultaneous static-browser runs.
Keep output profiles, preparations and bundle private keys outside public
student material.

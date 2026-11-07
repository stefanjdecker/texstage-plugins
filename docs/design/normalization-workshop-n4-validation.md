# Normalization Workshop: N4 comparison and evidence validation

Local Windows evidence, 2026-11-06. Version 0.3.0 adds private comparison,
explicit sharing of checks, chase playback and concrete lossless-join and lost-FD
explanations. This completes the discussion/evidence slice, not every N4–N6 gate.
The [machine-readable record](normalization-workshop-n4-validation.json) contains
the exact artifact, schema, dependency and test identities.

## Results

- **52 installed-wheel tests passed, no skips.** Includes all prior analyzer,
  state, privacy and authoring checks, plus five discussion tests.
- **243 independently checked display cases**, including 88 lossy and 93
  lost-FD cases. Python checks the JavaScript-presented tableau, trace and
  projection witnesses. Every losing tableau satisfies all original FDs and
  excludes the extra tuple, while every component projection contains its part.
  Lost-FD rows violate the original FD but satisfy all implied component FDs.
- **Chrome 156.0.8078.80, Firefox 153.0 and WebKit 26.5 passed** against the
  installed host/provider, using 320 CSS-pixel phone views and separate actors.
  Both task modes, two valid alternative decompositions, private comparison,
  answer-only versus explicit checks sharing, lossy replacement, reveal,
  own saved-version evidence, chase previous/next/final controls, focus and
  chase-position retention, reset, navigation and teardown were exercised.
- Projector and participant socket payloads were checked, not only visible
  elements. No handles on projector; personal analysis absent before reveal;
  sharing an answer alone has null analysis.
- PDF stage, handout, solutions, direct pdfLaTeX, static PowerPoint, public bundle
  separation and stale-export refusal passed. The seven-slide source and static
  authoring code did not change; N3 retains the earlier rendered-page review.
- Wheel/source-distribution rebuild payload parity passed. Runtime code was
  imported from the installed wheel in a disposable environment.

State/view v2 supports bounded pairs and explicit checks sharing. All **12 frozen
v1 schemas** and all eight analyzer/worker modules remain byte-identical. There
are 19 schemas in the package. Existing state/transition/view byte caps are
unchanged. Largest schema-shaped v2 state: 119,863 bytes; replacement transition:
120,645; participant view: 51,830; presenter controls: 56,316; presenter overlay:
55,233; projector overlay: 55,231.

## Exact artifacts

Host commit: `de3351550f3553ca63023554521fbe84806ec94e`.
Host wheel SHA-256: `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`.

Provider: `io.github.stefanjdecker.normalizationworkshop==0.3.0`.
Payload: `192103429f8541bd0b090d12a9aa31153ea0b0c8ff3fa21e98e4e889a0b2d48c`.
Wheel SHA-256: `450739bdfef1fb78a3cb0afd211c947e037e2fdae870ac27f2091cc7e8268daa`.
Sdist SHA-256: `6182990baaa86ff948ea37d0d644338ad10fea23acdac2a2c4045875a051ce7c`.

The compatible host wheel was installed with its hash-locked development/build
requirements. Python 3.14.4, Node 24.15.0 and locked Playwright 1.62.1 were used.
Browser profiles and server data are disposable; no course environments changed.

## Reproduce

From the collection root in an isolated environment with the compatible host
and locked build/test dependencies:

```sh
python maintenance/build_normalization_schemas.py --check
python maintenance/build_wheels.py --package normalization-workshop
python -m pip install --no-deps dist/texstage_normalization_workshop-0.3.0-py3-none-any.whl
python -m pytest plugins/normalization-workshop/tests -q --basetemp ./artifacts/normalization-tests --junitxml ./artifacts/normalization-tests.xml
node maintenance/normalization_lesson_browser.cjs <built-lesson.bundle>
```

Pass the bundle produced by the authoring test. Repeat the browser command with
`BROWSER=firefox` and `BROWSER=webkit` (PowerShell: `$env:BROWSER='firefox'`).
Set `PYTHON` to the environment's Python executable. Install matching locked
Playwright browsers first. A local Chrome channel can be selected only for
Chromium using `TEXSTAGE_BROWSER_CHANNEL=chrome`; clear it for the other engines.
Use separate `TEXSTAGE_TEST_PORT` values for concurrent runs. Reports/screenshots
are written below `artifacts/normalization-discussion/<browser>/`.

Review the [user guide](../normalization-workshop.md) and
[v2 discussion contract](normalization-workshop-discussion-contract.md) before
upgrading: rebuild the bundle, review/enable the payload, refresh its lock and
start a fresh session. There is no in-place saved-state migration from 0.2.0.

## Limits and remaining gates

The example interactions and focused keyboard/touch checks passed in desktop
browser emulation. Comprehensive German, screen-reader, browser-zoom and learner
review remains. Physical Android/iPhone classroom LAN testing and measured
classroom throughput remain; a 64-actor storage cap is not a load result.
Hosted cross-platform CI against a reproducible published host artifact is open.

No host/CSP/worker changes were made. N2 retains the active forbidden-operation
probe evidence; those probes were not repeated for this renderer/state slice.
Other providers' test suites were not rerun; their N3 results remain historical.
No catalog publication, commit, push, original-repository or course changes
are part of this delivery.

# Relational visual editor: local validation

Date: 2026-11-08. Relational Algebra Lab 0.2.0, on
`codex/relational-editor`. Validation ran from an uncommitted working tree;
the commit containing this record preserves that tested implementation. These
are local Windows results, not a completed classroom release. The
[machine-readable record](relational-editor-validation.json) identifies every
wheel, provider payload, schema, browser and combined-installation provider.

## Tested identities

- Host source: `3b290c2108d060652c07a21638f886f075b0d02d`, unchanged by this work.
- Host wheel: `texstage-0.2.1.dev7-py3-none-any.whl`.
- Host wheel SHA-256: `ae3ecd26094a9b626e59975327e7eaa6293c16e8d1765de318371503b18aa000`.
- Relational wheel SHA-256: `2bd57540b745abc146458d0f269fee8809bd527d41089139afc0abc8fbfc2e4a`.
- Provider payload: `5acef0f596bf61c7442f7ae3be940430b18ef3efe4f793871e6a430676e8b89f`.
- Result schema: `ab27323b0097cf341ac9c7e5ba0bd91266e060b24e796caf1df7f203a5a36ebe`.
- Python 3.14.4; Node v24.15.0; Playwright 1.62.1; locked esbuild 0.28.2.

The collection source base is `5ead891866e239de00b0128a1ea06af2551e0dad`; the changed
provider is identified by its payload and wheel above. No host or course
environment was upgraded.

## Checks executed

| Check | Result |
| --- | --- |
| Installed relational package suite | 74 passed; no skips |
| Wheel rebuilt from sdist | Same package and metadata bytes, excluding RECORD |
| Generated worker freshness | Rebuilt with the locked toolchain; other provider workers unchanged |
| English and German prepared material | Stage bundle, static PowerPoint, handout, solutions, direct exports and stale-source rejection |
| Actual classroom workflow | English and German in Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5 |
| Worker restrictions and recovery | All three browsers passed the unchanged production CSP checks |
| Combined installed catalog | 10 providers, 8 engines, 8 slide types; 7 domain probes passed |
| Preservation | Original tools, courses, private media and prior worktrees matched the baseline snapshot |

Browser workflows use installed modules, an authenticated local TeXStage server
and the actual presenter evaluator. Construction and rewriting use labelled
controls rather than answer injection. Checks cover all eight operators,
integer and projection errors, incompatible union inputs and repair, empty
results, branch removal, undo/redo, saving, private inspection, anonymous sharing
and reveal. They also cover partly edited fields and focus across updates,
two devices saving as one actor, explicit reset recovery, keyboard/touch input,
320-pixel and landscape layouts, reduced motion and navigation teardown.

The cooperative preview matches the independent Python oracle for all operator
forms, the worked examples, empty output and a bounded larger product. Its
cancellation and tree/history limits are exercised. Preview is explicitly
public-data feedback; hidden-fixture grading remains in the restricted worker.

The browser security probe actively attempts same-origin/cross-origin fetch,
XHR, WebSocket, EventSource, child/blob workers, external modules, eval and
Function. All are blocked by the production worker policy. A separate diagnostic
control demonstrates the attempts would otherwise execute. Invalid results,
deadline expiry, recovery and zero remaining workers are also checked.

The shared/revealed projector and phone screenshots were visually reviewed.
Static tree serialization was replaced with readable algebra notation, and tall
prepared content fits its declared height. Grading, command/state schemas,
privacy boundaries, engine budgets and the 64-actor pilot ceiling are unchanged.

## Reproduce

Use a fresh environment with the exact compatible host wheel and this provider
wheel. The existing dependency lockfiles and build helper are retained:

```sh
python maintenance/build_wheels.py --package relational-lab
python -m pip install --no-deps dist/texstage_relational_lab-0.2.0-py3-none-any.whl
RELATIONAL_TEST_EXPORTS=artifacts/relational-exports python -m pytest plugins/relational-lab/tests -q
python maintenance/relational_probe.py
BROWSER=chromium node maintenance/relational_browser.cjs
BROWSER=chromium RELATIONAL_LANGUAGE=en node maintenance/relational_lesson_browser.cjs artifacts/relational-exports/en/lesson.bundle
BROWSER=chromium RELATIONAL_LANGUAGE=de node maintenance/relational_lesson_browser.cjs artifacts/relational-exports/de/lesson.bundle
```

Repeat browser commands for Firefox and WebKit. The environment-variable syntax
above is for Bash; use `$env:NAME='value'` in PowerShell. Install the locked npm
dependencies and Playwright browsers first. Both language authoring cases require
pdfLaTeX and the German language package. CI now passes both exported bundles to
each browser consumer instead of depending on pytest's temporary folder names.

## Remaining release checks

Hosted Linux/Windows CI was updated but has not been run for this branch.
Physical-phone/LAN use, screen-reader acceptance, zoom coverage beyond the
tested viewport sizes, measured preview/UI latency, classroom burst/reconnect
budgets, cross-platform artifact transfer and an actual recording remain open.
This work does not claim the R6 latency targets or 600/1,000-student support.
The provider remains an experimental 64-actor pilot.

The source-status fields in the machine-readable record describe the validation
snapshot before commit and push. No package release or catalog entry was created.
See the [illustrated editor guide](../relational-editor.md) for the user workflow.

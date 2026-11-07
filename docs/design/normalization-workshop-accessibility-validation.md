# Normalization Workshop: keyboard, German and zoom validation

Local Windows evidence, 2026-11-07. Provider **0.3.1** retains the 0.3.0 state/view
v2 contracts and all nineteen schemas. The [machine-readable record](normalization-workshop-accessibility-validation.json)
identifies the exact wheels, provider payload, host changes and test reports.

## Fixed behavior

- Relation removal returns focus to an adjacent remaining relation. Explicit
  load/keep choices after a draft conflict return focus to the editor without
  saving. Chase boundary controls remain focusable, announce unavailability and
  refuse movement beyond the first/final step.
- Plugin regions declare their language. Attribute checkboxes keep their short
  identifier and describe its localized meaning. Table headers do not wrap
  into individual letters; wide tables scroll inside named keyboard regions.
- The generic host passes the phone's browser-selected language to plugin views.
  Ordinary server pushes without a language field keep the mount and draft.
- Presenter/projector shortcuts leave native controls and plugin surfaces alone.
  Enter no longer also advances a slide; the projector leaves Tab available.
- At narrow, short viewport sizes, the presenter workspace scrolls vertically.
  Notes and activity controls retain usable height rather than overlap.

The host changes belong in **texstage-public**; the normalization controls,
examples for testing and guide belong in **texstage-plugins**. Original tools,
existing courses and their environments were not changed. No commits or pushes.

## Verification

**52 provider tests passed.** Host checks: **80 browser-module tests passed**;
**76 Python tests passed and one skipped** because creating symlinks is not
permitted in this Windows environment. The parameterized JS contract runner is
invoked by the Python tests, not launched without its required fixture argument.

Actual installed-host/provider flows passed in Chrome 156.0.8078.80, Firefox
153.0 and WebKit 26.5:

- German keyboard-only learner input and presenter actions at 320 CSS pixels.
- Add/remove focus, both draft-conflict choices, no automatic submission,
  classification with native selectors, the empty candidate key, chase boundary
  focus, keyboard-scrollable tables and projector proof controls.
- Accessible names snapshot, language markup and attribute-description checks.
- The existing English comparison/share/reveal/privacy/reset/navigation workflow
  in all three browsers.

Chrome additionally passed **native 200% browser zoom**, with a measured 711 ×
452 CSS-pixel viewport, DPR 2 and visual viewport scale 1. This is not simulated
device scaling or pinch zoom. Layout assertions verify separate presenter panes
and a vertically scrollable workspace. Direct compositor screenshots avoid
incorrect clipping by the standard screenshot helper at native page zoom.
The final host CSS adjustment was followed by another complete native-zoom
flow; other tested Python/JS implementation bytes remained unchanged.

All four German exercise pages and all four solution pages were rendered with
Poppler and visually reviewed. The fixture uses existing bilingual activity
sources plus a synthetic constant-FD example. It does not alter the public
seven-slide example or any course. No text clipping was found.

The controls were tested through actual role-filtered transport and the
production evaluator. This is automated keyboard/semantic and visual evidence,
not a screen-reader usability certification or physical-phone test.

## Artifacts and compatibility

Host base: `de3351550f3553ca63023554521fbe84806ec94e` **plus the working-tree fixes in this record**.
Host wheel SHA-256: `730b6f76e8c263f19e9410e6baac5d9bdb93b5d417c1790233f84411b8ed26f7`.

Provider payload: `8b97cd83a1cb0130762ac18cb195dc3147c221fe7390f93306f92ba5cfad94a1`.
Provider wheel SHA-256: `d6594541e56cb9c1c21e87c2f3d63330a8d2df04bb3848069a560ba1b24bbecc`.
Source distribution SHA-256: `41faf6d1f6aa74f143ae6268627f5cf1fca404c177a25bb5c05dfd1cc95799e4`.
The SDK's source-distribution rebuild has identical provider inventory/payload.
The tests imported the installed portable wheel in a fresh isolated environment.

The host still carries development version `0.2.1.dev3`; that version or the
baseline commit alone does not identify this fixed artifact. Use the recorded
wheel or a verified successor. Provider 0.3.1 does not fix an older host by itself.
Review/enable the new payload, refresh the lock, rebuild and start a fresh session
when changing the pinned environment.

The analyzer, reducer, authoring rules and all schemas are unchanged. No worker
or CSP relaxation was made. Active forbidden-operation probes were not repeated;
the earlier security records remain applicable to their unchanged code.

## Reproduce

In an isolated environment with the recorded host and locked build dependencies:

```sh
python maintenance/build_wheels.py --package normalization-workshop
python -m pip install --no-deps dist/texstage_normalization_workshop-0.3.1-py3-none-any.whl
python -m pytest plugins/normalization-workshop/tests -q
python maintenance/normalization_accessibility_probe.py --output ./artifacts/normalization-accessibility-fixture --language de
node maintenance/normalization_accessibility_browser.cjs ./artifacts/normalization-accessibility-fixture/build/accessibility.bundle
```

The probe generates its disposable lesson from repository sources and records the
built bundle. Set `PYTHON` to that environment's Python. Run the browser command
with `BROWSER=chromium`, `firefox` and `webkit`, using installed locked Playwright
browsers. PowerShell uses `$env:BROWSER='firefox'`.

For Chrome native zoom use `BROWSER=chromium`, `TEXSTAGE_BROWSER_CHANNEL=chrome`
and `NORMALIZATION_ZOOM=2`. Clear the channel for Firefox/WebKit and reset the
zoom variable for ordinary runs. Each run uses a temporary server/browser profile;
parallel runs require distinct `TEXSTAGE_TEST_PORT` values. Reports, screenshots
and semantic snapshots live under `artifacts/normalization-accessibility/`.
Use `maintenance/normalization_lesson_browser.cjs` for the existing English flow.

In the host, run the Python plugin tests and the standalone `web*.test.*` suite.
`web-plugin-contracts.test.mjs` takes fixture input and runs through the Python
contract tests. The new focused regression is `web-keyboard-controls.test.cjs`.

## Remaining gates

Human screen-reader and learner review, physical Android/iPhone tests on the
classroom LAN, measured class throughput, and hosted cross-platform CI against
a published compatible host pin remain. No catalog release was made.

# Normalization Workshop: N3 validation

Local Windows evidence, 2026-11-06. Version 0.2.0 adds prepared authoring,
classroom state and an initial native interface to the N1/N2 analyzer.
The [machine-readable record](normalization-workshop-n3-validation.json) gives
artifact hashes, locked dependency identities and exact test/browser results.

## Delivered and checked

- One author source produces private worked material, public task data, escaped
  exercise/solution fragments and the bound evaluation seed. Wrong worked answers
  are refused. Both task modes are available.
- The optional style exports `\normalizationworkshop{item}{width}{height}`.
  The [seven-slide example](../../examples/normalization/lesson.tex) builds live,
  stage, handout, solutions and static PowerPoint editions. Direct pdfLaTeX
  exports compile and reject a changed source as stale.
- Native attribute checkboxes, relation cards and normal-form/FD selectors;
  no participant JSON editor. Presenter inspection, version-pinned sharing,
  reveal, reopen-before-reveal and reset work through the actual host.
- At most 64 pseudonymous actor slots. A 65th actor is refused while an existing
  actor can replace. Feedback space is reserved before submission.
- Actor-local answer and presenter-control guards; receipt replay; changed
  envelope rejection; atomic cancel/replace at host queue capacity; close while
  pending; unavailable checks; navigation and reset; stale completion rejection.
- Independent fact verification before acceptance. Detailed inspection computes
  only one selected answer. Equivalent valid answers are not compared to the
  worked answer.
- Own feedback is absent before reveal, and another student's answer is absent
  from participant transport. The projector receives no private facts or actor
  handles; sharing and reveal are distinct explicit actions.

The twelve frozen schemas and all analyzer/worker modules are byte-identical to
N1/N2. No host code, security policy or original/course files changed.

## Exact artifacts

Host commit: `de3351550f3553ca63023554521fbe84806ec94e`.
Host wheel SHA-256:
`d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`.

Provider: `io.github.stefanjdecker.normalizationworkshop==0.2.0`.
Payload:
`281ecd7a8739b936ba38eac2092075ca19b105dd57e0c6c89ea08050c1a6d1fe`.

Wheel SHA-256:
`7985f5a9304dbabad5227bbcfed12bbe01a0e42790469c924e3a3845e3d0aab7`.

Sdist SHA-256:
`6594a62d4b0191d29b83b1271d4904993d5d5d4f91169893770ac61d801c4515`.

The SDK built an independent portable wheel and sdist. Rebuilding the sdist
produced identical provider inventory/payload. Tests imported the installed
wheel in a fresh disposable environment, not provider source.

Python 3.14.4, Node 24.15.0, Playwright 1.62.1; the matching host's hash-locked
development/build requirements and collection Node lock were used. The original
coordinate/distance, transaction and relational tests ran in their separate
existing installed-wheel environments. Their exact-provider assertions remain
unchanged.

## Automated results

| Suite | Passed | Failed / skipped |
| --- | ---: | ---: |
| Normalization analyzer/contracts/authoring/state/runtime/exports | 47 | 0 / 0 |
| Original coordinate/distance conformance | 4 | 0 / 0 |
| Transaction engine | 67 | 0 / 0 |
| Relational algebra engine/lesson | 72 | 0 / 0 |

The normalization suite includes the existing 53,248 three-attribute
Python/JavaScript differential analyses and larger seeded cases. The new tests
exercise privacy and lifecycle through the installed host runtime, not merely
schema-shaped objects. Five-provider discovery, resource verification and
catalog collision checks also passed with normalization, relational,
transaction, coordinates and distance. Concurrent ER/FD/query-plan projects
were preserved; this record does not claim their full regression coverage.

The original pair produced one existing Starlette/httpx deprecation warning.

| Browser | Actual version | Result |
| --- | --- | --- |
| Chromium via installed Chrome | 156.0.8078.80 | Pass |
| Firefox | 153.0 | Pass |
| WebKit | 26.5 | Pass |

All three ran the real installed host/provider against a disposable loopback
server at a 320-CSS-pixel participant viewport. The flow covers both modes,
the registration and tutor cases, keyboard submission, touch submission,
two devices for one actor, unrelated updates preserving focus/drafts,
explicit share/unshare, reveal, reset, navigation/restoring the saved answer,
teardown and private payload checks. No page errors were recorded.

The production evaluator CSP is unchanged. The engine bundle is also unchanged.
Active forbidden-network/dynamic-code/child-worker probes were run in
[N1/N2](normalization-workshop-n2-validation.md); they were not rerun for this
authoring/UI change.

Rendered exercise and solution pages 1–7 were visually inspected. Browser
screenshots were inspected for narrow phone layout and presenter/projector
readability. A cramped presenter overlay was compacted before the final build
and final three-browser run. The relation and written FDs remain visible above
an inspected/shared/revealed answer.

## Reproduce

Use the compatible host wheel and locked development environment described in
the [workshop guide](../normalization-workshop.md). From the collection root:

```sh
python maintenance/build_normalization_schemas.py --check
python maintenance/build_wheels.py --package normalization-workshop
python -m pip install --no-deps dist/texstage_normalization_workshop-0.2.0-py3-none-any.whl
python -m pytest plugins/normalization-workshop/tests -q --basetemp artifacts/normalization-tests
node maintenance/normalization_lesson_browser.cjs <built-lesson.bundle>
```

Set `PYTHON` to the selected environment's Python for the browser harness.
It requires the locked Playwright package and matching browser installation.
Select `BROWSER=firefox` or `BROWSER=webkit` for those runs; a Chromium
`TEXSTAGE_BROWSER_CHANNEL` override must not be carried into them.
`TEXSTAGE_TEST_PORT` selects a separate loopback port when running concurrently.

Local evidence is in the ignored `artifacts/normalization-lesson/` directory:
three browser reports/screenshots and `evidence/` with test reports, build log,
reviewed PDFs and static PowerPoint. The portable wheel/sdist are in ignored
`dist/`. Test profiles and private preparation directories are not publication
artifacts.

## Remaining gates

This closes N3 and supplies a first usable part of N4. It does not close the
whole release plan. Side-by-side comparison, a readable chase/spurious-tuple
display, comprehensive German/zoom/keyboard and learner review remain. Desktop
emulation does not establish physical Android/iPhone usability. No classroom
load/queue latency claim, hosted cross-platform CI result, catalog publication,
commit, push or course migration is made by this record.

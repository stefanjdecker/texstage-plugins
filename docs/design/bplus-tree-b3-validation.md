# B+ B3 classroom verification

Local Windows verification on 2026-11-07. Version 0.3.0 implements classroom
submissions and feedback with content state schema 2. The engine semantics and
prepared LaTeX layout/style remain unchanged. The visual phone editor and
presenter buttons remain B4 work.

The [machine-readable record](bplus-tree-b3-validation.json) contains exact
identities, schema hashes, test counts and browser results. The
[classroom guide](../bplus-classroom.md) documents commands, feedback and privacy.

## Tested artifacts

- Portable wheel: `texstage_bplus_lab-0.3.0-py3-none-any.whl`
- Wheel SHA-256: `565fe7b6e1030db65e13cf4cdbb347e6d90f3d92b5ee7ad378874078070d1a86`
- Provider payload: `3f6864fe3f4c07753e76a3a1ea79e82a4eed890d18e62d0728e061614e8d0e16`
- Host wheel SHA-256: `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`
- Host baseline: `de3351550f3553ca63023554521fbe84806ec94e`; 119 installed runtime/style files
  matched that artifact. Concurrent host working-tree edits were excluded and
  are listed in the JSON record.
- Collection baseline: `5f00b62f6292de01e4eca067c8acd96dddf67eb9` plus these local changes.
- Python 3.14.4, Node v24.15.0.
  The SDK verified source-distribution/wheel payload parity.

The final wheel contains the tested runtime payload. Documentation/metadata
were refreshed before freezing its recorded wheel hash. This is local evidence,
not a hosted CI run, published compatibility pin or Windows/Linux transfer.

## Results

All **122 tests passed**: 30 engine, 32 authoring and 60 classroom-state tests.
There were no failures, errors or skips. Coverage includes:

- Alternative correct certificates, specific path/scan/repair/prediction feedback,
  and independent verification of typed facts for the submitted answer.
- Immediate/on-reveal feedback, operational failure without an incorrect grade,
  independent actors, same-actor devices, control conflicts and unchanged input state.
- Receipts and retries, replacement at both the full 48-actor ceiling and full
  job queue, old result rejection, close/reveal/reset/navigation and restart.
- Exact persisted binding identity, including the engine key; malformed/foreign
  commands, role enforcement and closed projections in both installed validators.
- Private inspection, anonymous prediction-only sharing before reveal,
  version invalidation and a bounded shared/worked replay cursor.

| Browser | Version | Classroom protocol | Static privacy/lifecycle | Worker restrictions |
| --- | --- | --- | --- | --- |
| Chromium (Chrome) | 156.0.8078.80 | Passed | Passed | Passed |
| Firefox | 153.0 | Passed | Passed | Passed |
| WebKit | 26.5 | Passed | Passed | Passed |

The classroom probes drove authenticated presenter/projector/student clients
through lookup, range, insertion and deletion using the actual host evaluator.
They verified two actors, a second device for one actor, replacements, private
transport, sharing, feedback, reset and return-to-slide closure with no page errors.
They do not claim interaction with a completed phone editor.

The worker policy remained `default-src 'none'; script-src 'self'
'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'`. All ten active
network/child-worker/dynamic-code probes were blocked after positive controls.
Invalid results were refused; the two-second deadline terminated stalled work
and a subsequent evaluation recovered with no workers remaining.

Firefox failed before creating its first page under the Windows process sandbox.
The unchanged probe passed with scoped process escalation. No CSP changes were made.

The English seven-page lesson rebuilt successfully: live bundle, static
PowerPoint, handout/solutions/stage PDFs and direct pdfLaTeX editions. Privacy,
item identity, freshness and PDF text-bound checks passed. English/German
authoring unit tests passed; layout/style bytes match B2.

## Measured storage

| Measurement | ASCII-escaped canonical bytes |
| --- | ---: |
| Largest structural answer used | 752 |
| Actor slot including reserved feedback | 2169 |
| Complete 48-actor state | 59397 |
| Complete transition including effects | 60499 |
| Participant view | 33211 |
| Presenter controls | 38860 |
| Presenter overlay | 32300 |
| Projector overlay | 32300 |

The scenario uses 256-character non-BMP authenticated actors, maximal answer
arrays, maximum version tokens, escaped bilingual explanations and eventual
feedback reservations. The private actor map uses fixed 64-character digests.
All measured projections fit the 48 KiB target. Even 48 slots filled to their
4 KiB admission ceiling plus 16 KiB shared state fit the 224 KiB state ceiling.
These are storage checks, not classroom throughput or physical-phone measurements.

## Remaining gates

B4 supplies visual editing, draft/conflict handling, accessible localized
feedback and presenter controls. Physical phones, classroom load/fairness,
hosted CI, cross-OS identical-artifact transfer and publication remain open.
CI now runs the state tests in the isolated Linux/Windows jobs and adds the
classroom probe to the prepared-bundle browser matrix.

Original repositories, existing courses, course environments and private media
were outside the edited paths. No commit, push, catalog entry or publication was
part of this task.

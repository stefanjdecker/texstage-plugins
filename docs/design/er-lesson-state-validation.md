# ER registration E3 validation

Validated 2026-11-06: provider 0.3.0, state schema 2. This closes the registration
lesson-state milestone, not the phone/presenter UI milestone. See the
[protocol contract](../er-decisions-state.md) and
[machine-readable evidence](er-lesson-state-validation.json).

## Artifacts

- Collection base `5f00b62f6292de01e4eca067c8acd96dddf67eb9`, branch `codex/plugin-system`;
  ER changes tested before commit.
- Host `de3351550f3553ca63023554521fbe84806ec94e`; wheel SHA-256
  `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`; installed payload
  `e41e8bbb8463111ee7d62f8c0b92c4dda736bc5df9ce558b9d7e813d06efcb23`.
- Provider wheel `texstage_er_decisions-0.3.0-py3-none-any.whl`; SHA-256 `39e3d9b014ea234d364c332880db596664ae6aa8cb16c4626d2be25c762ee23d`.
- Provider payload `ff1d171bc77d66ae55f04b3c94574c8a9e6e8bb54ff2fc9b5baf662a4081bdf8`.

Built portable wheel and source distribution with payload parity, then installed
into a separate environment containing only this provider and the matching host
with hash-locked test/build dependencies. Windows, Python 3.14.4,
Node v24.15.0, TeX Live 2026. Engine/model schemas, worker bytes, LaTeX
rendering functions and style remain unchanged from E2; no host change was needed.
Earlier [E1](er-registration-engine-validation.md) and
[E2](er-prepared-authoring-validation.md) records identify their historical artifacts.

## Completed checks

**109 tests passed, zero failed or skipped, in 127.25 seconds.** Coverage
includes all prior engine/authoring tests and 32 state tests: both valid models,
incorrect versus unavailable feedback, identity/coverage/classification/witness
tampering, stale actor/phase/control versions, actor-separated correlations,
late completion, cancellation/replacement, pending close/reveal, navigation,
explicit anonymous sharing, rationale release, paging and serialized bounds.

Real installed-host Runtime tests cover receipt replay, changed-envelope
rejection, two-device conflicts, full-queue replacement, genuine Node engine
results, duplicate delivery, restart before delivery, persistence, reset retries,
two-presenter epoch conflict and stale leases. Invalid payload fields, boolean
version coercion, foreign seeds and wrong-role commands fail at the host boundary.
Schema checks exercise all four role projections through both installed validators.
Page order is independent of JSON object insertion order.

The complete static authoring regression rebuilt English, German and long-label
editions, live bundles, static PowerPoint and direct-pdfLaTeX outputs, including
private-data and page-bound checks. The initial isolated copy omitted an existing
hand-derived engine fixture; that copy error was corrected before the clean
full-suite result recorded here.

Real loopback-server checks passed in Chromium 151.0.7922.34, Firefox 153.0 and
WebKit 26.5. They use authenticated protocol clients to open, submit, receive
actual presenter-worker evaluation, inspect privately, share without identity or
rationale, reveal both worked alternatives and reset the epoch. This is **protocol
testing**, not testing an implemented phone editor. The static presenter/projector
screens remain visible; no page errors or private role leaks were observed.

All three browsers also reran 31 evaluator samples and active security probes:
network access, external modules, child/blob workers, eval and Function remain
blocked under the production CSP, with working unrestricted control probes.
Invalid results fail, runaway evaluation times out, workers are cleaned up and
the next job succeeds. No security restriction or host budget was relaxed.

## Capacity evidence and limits

The 64-actor test uses 256-character actor keys, maximum-length decision/option
IDs, near-limit ASCII-escaped rationale, large versions/epochs and escaped
teaching explanations. Measured largest slot: 2032 bytes;
state: 130643 bytes; transition with effects:
130468 bytes. Largest tested view:
26505 bytes. All stay within the enforced
2,560-byte slot, 192-KiB state, 224-KiB transition and 96-KiB view limits.
There are 24 positive/negative view-validator cases.

These are storage and correctness measurements, not classroom throughput.
The phone editor, presenter buttons, dirty-draft interaction, touch/keyboard
and screen-reader workflows are E4. Physical phones, load/fairness, Linux
installation and public CI/release evidence remain later gates.

## Reproduce

Follow the [authoring guide](../er-decisions-authoring.md) with the exact host
artifact above, build/install the provider and run:

```console
python -m pytest plugins/er-decisions/tests -q --basetemp artifacts/er-tests
python maintenance/er_probe.py --output artifacts/er-engine
node maintenance/er_browser.cjs artifacts/er-engine
node maintenance/er_prepared_browser.cjs <built-lesson.bundle> artifacts/er-protocol
```

Set `PYTHON` to the isolated environment, install the locked Playwright browsers,
and repeat with `BROWSER=firefox` / `BROWSER=webkit`. Use different
`TEXSTAGE_TEST_PORT` values for simultaneous local-server runs.
`maintenance/build_er_lesson_schemas.py` reproduces the owned schemas/manifest.
Use fresh sessions and pins after updating provider bytes; existing courses and
their environments were not changed.

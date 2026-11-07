# ER fixed points validation

Local Windows validation on 2026-11-07, with ER **0.6.0**, state schema **4**,
manifest revision **4** and the compatible TeXStage **0.2.1.dev6** development
wheel. [Machine-readable evidence](er-points-validation.json) records exact wheel,
sdist, provider-payload and installed-host hashes. Version numbers alone are
not compatibility pins. Both source repositories still contain uncommitted work;
this is not a published release or hosted CI result.

## Compatibility handoff: TeXStage 0.2.1.dev7

The delivered source includes a concurrent compatibility update for manifest
revisions 3–5. The final 0.2.1.dev7 wheel passed **144 host tests**, **57 focused
ER points/state/artifact tests**, the scored English/German phone and CSV flows,
and worker-security checks in all three browsers. Its hash and results are in
the handoff section of the machine-readable record.

Compared with the fully measured dev6 wheel, only the package version constant
and manifest schemas 3, 4 and 5 differ. All runtime code and browser resources
are byte-identical, and normalized revision-4 schema comparison confirms the
same ER contract. All 156 installed resources match the final wheel and source.
The 600-client timings below were measured on dev6; they were not rerun merely
for this version/schema handoff. Fresh sessions are required for either version.

## Behavior and checks

The optional source `points` integer (0–10000; omitted means 0) uses the host's
fixed game-points ledger. Both accepted registration models earn full credit;
a verified contradiction earns zero. Unavailable, stale, incomplete or invented
evaluation facts cannot earn correctness points. There is no speed/streak bonus.
Credits remain private until reveal; late accepted evaluations can then award
points. Replacements replace credit, exact retries do not duplicate it, and
reset withdraws this activity's contribution. Scored rounds require reset after
reveal; practice retains reopening and repair.

- **132 host tests passed**, including ledger persistence, replay, mixed quiz
  totals, CSV/rank projection, record compatibility, actor-scoped notifications,
  strict schema checks and bounded immutable-data validation caches.
- **135 provider/artifact tests passed**, covering both accepted models,
  incorrect/unavailable/forged outcomes, replacement, reveal, late completion,
  reset, authoring and source/wheel/sdist parity. Regenerating schemas preserves
  the packaged points and 600-student contracts with normalized line endings.
- Concurrent quiz speed/streak work was preserved and its regression tests pass.
  ER still uses fixed-v1. All 156 installed host resources match the clean-built
  wheel and corresponding source resources.
- Real 320px phone and presenter flows passed in **English and German** in
  Chromium, Firefox and WebKit. Each run compares two accepted models and one
  contradiction, checks withheld feedback, own points, game totals, CSV/ranks,
  navigation and reset withdrawal.
- Practice workflows and actual restricted-worker security checks passed in all
  three browsers. Network access, nested workers and timeout restrictions remain
  in force. Static exercise/solution PDFs in both languages were rendered and
  inspected; their points notices fit.

## 600-participant measurements

The recorded i9-11950H Windows machine connects 600 authenticated protocol
clients, with one real presenter evaluator. It exercises all 27 choice
combinations, a full replacement wave, two scored publications, reset withdrawal,
disconnected-evaluator recovery, receipt replay and refusal of a 601st answer.
Every expected total and own award matches; both publications award 1000 points
to 46 correct models and zero to the other verified models. The synthetic load
uses no optional rationales. It is not a measurement of 600 rendered phones,
classroom Wi-Fi or a hosted service.

Times below are seconds from each send until observed evaluated/saved state.
The unchanged warm gate is p95 ≤10 s and last answer ≤30 s; cold evaluation is
reported separately.

| Run | Cold p95 | Warm p95 | Warm last | Warm gate |
| --- | ---: | ---: | ---: | --- |
| chromium | 10.79 | 6.90 | 6.98 | Pass |
| firefox | 13.25 | 8.27 | 8.37 | Pass |
| webkit | 12.56 | 7.53 | 7.61 | Pass |

Earlier development-host runs ranged from 7.72 to 11.02 seconds warm p95;
Chromium missed the 10-second target before a repeat passed at 8.46 seconds.
The machine-readable record retains both observations and their earlier wheel
identity. Scored 600-actor correctness and recovery are verified; reliable latency
on the intended deployment hardware remains an open release gate. Do not treat
these runs as a guaranteed response time. Initial integration runs also exposed
redundant checks and repeated unpublished-round score projection; the final host
bounds validation caches and avoids re-ranking unchanged private rounds without
reusing authorization or role projections.

## Reproduce and release limits

Use the [authoring guide](../er-decisions-authoring.md) and
[release checklist](../er-decisions-release.md). Build a disposable scored deck:

```console
python maintenance/er_ui_bundle.py --output artifacts/er-scored --points 1000
node maintenance/er_points_browser.cjs artifacts/er-scored/out/lesson.bundle artifacts/points
```

Add `--language de` for the German build. For the classroom harness set
`ER_LOAD_ACTORS=600`, `ER_LOAD_RECOVERY=1`, `ER_REQUIRE_LOAD_TARGETS=1`
and the selected `BROWSER`; use the scored bundle with
`maintenance/er_load_browser.cjs`. CI retains these gates and the identical
artifact handoff. A compatible published immutable host commit, Linux/Windows
hosted consumers, stable deployment load measurements, physical Android/iOS
phones and screen-reader speech checks remain release work.

The original lecture-tools repository, existing courses and private video
material were not changed. No commit, push or release publication was performed.

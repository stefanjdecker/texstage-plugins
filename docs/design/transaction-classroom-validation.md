# Transaction classroom validation

This is the historical 2026-11-07 record. See the
[2026-11-08 classroom release validation](classroom-release-validation.md) for
published compatibility pins, corrected burst processing, hosted CI and the
prepared physical-device checklist. The measurements below are preserved as
recorded; later fixes do not turn earlier failures into passes.

The complete classroom activity is implemented and passes local functional checks.
It is **not yet a released or fully classroom-validated plugin pair**. Human-paced
600/1,000-student simulations pass; synchronized bursts retain every answer but
miss the planned acknowledgement p95 targets. Physical-device, accessibility,
recording and hosted cross-platform checks remain open. No capacity target or
security restriction was relaxed to obtain a pass.

This record covers local validation on 2026-11-07 from isolated
`codex/transactions-classroom` worktrees. Original tools, courses and media
were not migrated. See the [lesson guide](../transactions-lesson.md),
[contract](transaction-classroom-contract.md), [acceptance plan](transaction-schedules-plan.md)
and [sanitized measurements](transaction-classroom-validation.json).

## Artifacts and compatibility

Local source pairing: TeXStage `3b290c2108d060652c07a21638f886f075b0d02d` and the collection commit
containing this record, on `codex/transactions-classroom`. These commits have
not been published as compatibility pins.

Host base: `f612a366ddde07b79a6d5f70160d7ac9db8bd880`, plus the generic archive and
bounded audience-broadcast changes in this branch. Collection base:
`604b515d10ca5f27fc2398d7caade1b071379226`. Both provider versions are 0.1.0.
The host version is 0.2.1.dev7; that version alone is **not** a compatibility pin.
No catalog entry, release, merge or course adoption is made by this work.

| Artifact | SHA-256 |
| --- | --- |
| `texstage_transaction_activity-0.1.0-py3-none-any.whl` | `027afc7b7e31e6717a66e937c1268bb6fde5ba4036e92a885a5f9a12dd892a51` |
| `texstage-0.2.1.dev7-py3-none-any.whl` | `ae3ecd26094a9b626e59975327e7eaa6293c16e8d1765de318371503b18aa000` |
| `texstage_transaction_engine-0.1.0-py3-none-any.whl` | `6f06262b52b81b447ac3c650e07c231cc6b34826f2af627ccae5b20358405bbc` |

| Provider | Payload identity |
| --- | --- |
| `io.github.stefanjdecker.transactionactivity` | `df8eb3738ef8f821b226e3ed54d7aa5fae1f1d67823e9127e3c765a0434ac2c3` |
| `io.github.stefanjdecker.transactionengine` | `145300b39001a99777a87a9f824928441a8c7eb457db317d8fa6750eccb8aacc` |

The independent engine payload is unchanged. The new activity wheel and a wheel
rebuilt from its source distribution have identical complete provider manifests.
Packaged modules pass JavaScript syntax checks; generated closed schemas are
checked against the generator and both host validators. Exact schema digests
and prepared item identities are included in the JSON record.

## Functional evidence

| Check | Result |
| --- | --- |
| Installed activity suite | 44 passed; independent model, authoring, feedback, state, privacy, lifecycle, capacity and real runtime |
| Standalone transaction engine | 67 passed, unchanged independent installation |
| Original coordinate/distance environment | 4 passed, exactly two providers |
| Complete collection | 10 packages, 8 engines, 8 types verified; all 7 database engine probes passed |
| Actual isolated worker/CSP checks | Chromium, Firefox and WebKit passed with unchanged restrictions |
| Classroom browser flow | All six examples and all phases passed in each browser, English and German |
| Prepared authoring | English/German lesson and maximum-size stress case passed all six PDF editions and static PowerPoint |
| Host broad suite | 593 passed, 1 outdated mock failed, 1 skipped, 2 subtests |
| Host affected regressions after mock correction | 30 passed; no further host production changes |

The activity model is checked against an independent oracle over 1,742 legal
interleavings. Different valid repairs, certificates and witness choices are
accepted by their semantics. Browser facts are rechecked independently before
feedback is saved; operational failure never becomes an incorrect verdict.

Browser checks use installed wheels, an actual presenter evaluator and ordinary
loopback HTTP. They cover peer edits/focus, 320-pixel and landscape layouts,
native labels and Space-key controls, both same-actor conflict choices, late
acknowledgements, disposal, unavailable/retry, navigation pause/resume, staged
feedback, private selection, anonymous sharing, worked alternatives and reset.
Projector screenshots were visually reviewed, including all three counter
repairs. Automated labels and keyboard actions are not a screen-reader audit.

The host broad-suite failure was a test double that did not accept the new
`players=False` argument; its expectation was corrected to check deferred
audience delivery. The affected tests passed afterward. The broad suite was
not rerun and is not reported as an all-green run. Archive checks cover
lecturer-only ZIP/private records, projector-only public snapshots, schema
failure without private fallback, session authorization and no-plugin sessions.

## Capacity measurements

Windows, Intel Core i9-11950H (2.60 GHz), about 63.2 GiB reported RAM, Python
3.14.4 and Node 24.15.0. Browser versions: Chromium 151.0.7922.34, Firefox 153.0,
WebKit 26.5. One actual presenter browser evaluates uncached repairs; students
are authenticated synthetic WebSocket clients on the same computer. These
measurements include local CPU contention and do not simulate campus Wi-Fi.

Each run exercises prediction, varied diagnosis, distinct program-order-preserving
repairs, 10% replacements, receipt replay, reconnect, same-actor conflict, held
leases and replacement presenter, reveal while work remains, roster/export and
reset. At 1,000 records the next new actor is refused while existing actors can
replace answers. Full-queue/mixed-item contention also has runtime regression
coverage. All accepted latest answers were accounted for, with no lost,
duplicated or cross-actor feedback and no scoreboard points.

The 30-second wave spreads each phase's saves over that interval. A burst sends
all saves together. Repair drain is measured after the last submission with
a healthy evaluator; acknowledgements represent durable acceptance, not a grade.

| Browser | Students | Wave | Worst phase ack p95 / max | Control p95 / max | Repair drain | Gates |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| Chromium | 600 | Burst | 2.95 / 2.95 s | 0.30 / 0.30 s | 15.47 s | Ack p95 fails |
| Firefox | 600 | Burst | 2.89 / 2.89 s | 0.28 / 0.28 s | 16.84 s | Ack p95 fails |
| Webkit | 600 | Burst | 2.80 / 2.80 s | 0.28 / 0.28 s | 24.46 s | Ack p95 fails |
| Chromium | 1000 | Burst | 4.98 / 4.98 s | 0.14 / 0.14 s | 25.96 s | Ack p95 fails |
| Firefox | 1000 | Burst | 5.07 / 5.07 s | 0.29 / 0.29 s | 30.38 s | Ack p95 fails |
| Webkit | 1000 | Burst | 5.29 / 5.33 s | 0.28 / 0.28 s | 39.90 s | Ack p95 fails |
| Chromium | 600 | 30 s | 0.36 / 0.36 s | 0.29 / 0.29 s | 0.44 s | Pass |
| Chromium | 1000 | 30 s | 0.56 / 0.56 s | 0.29 / 0.29 s | 1.06 s | Pass |

Frozen goals: at 600 students, acknowledgement p95/max 2/5 s, control p95/max
1/3 s, repair drain 60 s; at 1,000 students, 3/10 s, 2/5 s and 120 s respectively.
The harness gates acknowledgement p95 across all submissions; the table reports
the worst per-phase p95 as well. Maximum, control, drain and correctness gates
passed in these runs. Burst p95 failed at both sizes. This prevents an
unqualified 600-student or 1,000-student readiness claim.

The initial test also found expensive whole-class projection delaying presenter
controls. The generic host fix acknowledges controls after projecting lecturer
windows and sends audience views through the existing bounded flusher. Closed
schemas retain all constraints while avoiding repeated reference traversal.
Those changes fixed control responsiveness, but the synchronous command path
still needs profiling/optimization for a large simultaneous burst. Do not
disable durability, role filtering, schema checks or worker limits to meet it.

The JSON record retains per-phase completion/acknowledgement percentiles, observed
queue wait, retry leases, hook and worker timings, IPC and projection sizes,
and memory measurements where available. Server memory is sampled OS peak RSS;
the browser metric is only coarse JavaScript heap, not browser-process RSS.
Firefox/WebKit do not expose that heap API. Missing measurements are `null`.
The capacity size counters used JavaScript string lengths, so they are size
proxies rather than exact UTF-8 bytes. The committed probe corrects this for
future measurements; it does not retrospectively relabel those counters.
A final 20-actor smoke run passed with the corrected byte counters and sampled
server memory. It verifies the probe, not an additional capacity claim.
Batched-view duration can exceed one hook's deadline because it measures a batch;
no provider hook or worker deadline has been raised.

## Reproduction and remaining gates

Build/install the exact host and two providers using the lesson guide. Run:

```sh
python maintenance/build_transaction_schemas.py --check
python -m pytest plugins/transaction-activity/tests -q
python maintenance/transaction_authoring_probe.py --output artifacts/prepared
BROWSER=firefox TRANSACTION_LANGUAGE=de node maintenance/transaction_ui_browser.cjs artifacts/prepared/lesson-de/out/lesson-de.bundle artifacts/ui
BROWSER=chromium TRANSACTION_ACTORS=600 TRANSACTION_WAVE_SECONDS=30 node maintenance/transaction_load_browser.cjs artifacts/prepared/lesson-en/out/lesson.bundle artifacts/load
```

These shell examples use POSIX environment assignments; in PowerShell set
`$env:BROWSER`, `$env:TRANSACTION_LANGUAGE`, `$env:TRANSACTION_ACTORS` and
`$env:TRANSACTION_WAVE_SECONDS` before the corresponding `node` command.
Use fresh output directories and disposable operator profiles. Keep raw
session records and recordings private. Only synthetic screenshots and
sanitized aggregate evidence are included here.

The new `transaction-conformance.yml` workflow builds on Linux, preserves the
standalone engine checks, transfers identical wheels/bundles to Windows/Linux
browser jobs, and optionally runs both load sizes and waves in all three
browsers. Dispatch requires a published exact host SHA with the new archive API.
It is prepared but has not been run on hosted runners. Local Windows authoring
is tested; Linux authoring and cross-platform artifact consumption remain open.

Before classroom/release acceptance: improve and remeasure burst p95; run the
hosted matrix after publishing the host branch; rehearse physical Android and
iPhone participation over the intended LAN; perform a human keyboard and
screen-reader review; and verify a short private screen/window recording in
playback. Actual release/catalog publication and course migration follow
separate user instructions. Version 1 remains formative without numeric scores.

# FD Lab F4: performance follow-up

All unchanged automated timing gates pass on 2026-11-07. This record supersedes
the open WebKit performance gate in the [initial F4 record](functional-dependencies-f4-validation.md),
which is retained with its original measurements. Physical-phone validation
remains deferred at the user's request. This is local evidence, not a release.

## Changes and restrictions

The host caches only immutable provider asset bytes by complete pinned URL,
sharing downloads and retaining at most 64 entries / 16 MiB. Each fresh worker
receives a structured clone. Failed downloads are evicted; oversized assets are
usable without retention; destruction clears the cache, including late arrivals.
No engine instance, answer, reference or result is shared between jobs.

Full-class projections now coalesce according to their measured cost. The
post-broadcast interval is `min(1.0, max(0.2, 3 * render_seconds))` seconds for
that session, checked by the ordinary flusher. This gives socket replies, module
requests and evaluation results time to progress. Presenter phase, selection
and sharing controls remain immediate. Commands and durable receipts do not wait
for a broadcast. This bounds the deliberate delay, not total delivery latency.

The final host includes the concurrently reviewed schema-cache isolation fix:
cache successful safety checks, then create a fresh validator snapshot per value.
Mutating a schema exposed by an exception cannot poison subsequent validation.

Worker CSP, URL approval, fresh workers, two-job leases, the two-second execution
deadline and result validation are unchanged. Cache tests cover failed downloads,
payload changes, bounds/eviction, worker-buffer independence, destruction and
late completion. Server tests cover cost bounds, coalescing and ended sessions.

## Measurements

The final matrix uses Windows 10.0.19045, Intel i9-11950H (16 logical CPUs),
approximately 63 GiB RAM and Node 24.15.0. Browser versions are
chromium 156.0.8078.80, firefox 153.0, webkit 26.5.
Each run uses 64 synthetic protocol actors, an additional rendered 320 px
participant connection for actor 1, and a real presenter evaluator over loopback.
Browsers ran sequentially. These are not 64 physical phones or LAN measurements.

| Browser | Activity | Feedback p95 (s) | Worst feedback (s) | All 64 complete (s) | Input p95 (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| chromium | practice | 3.75 | 3.77 | 3.80 | 1 |
| chromium | keys_all | 3.79 | 3.80 | 3.83 | 1 |
| chromium | refuted | 2.99 | 2.99 | 3.01 | 2 |
| firefox | practice | 3.87 | 3.88 | 3.92 | 2 |
| firefox | keys_all | 3.27 | 3.27 | 3.30 | 1 |
| firefox | refuted | 3.11 | 3.12 | 3.15 | 1 |
| webkit | practice | 6.94 | 6.95 | 7.01 | 9 |
| webkit | keys_all | 6.47 | 6.48 | 6.52 | 6 |
| webkit | refuted | 5.85 | 6.88 | 6.91 | 10 |

Targets remain input p95 below 100 ms, feedback p95 below 10 seconds and worst
feedback below 30 seconds. All modes meet all targets. Queue order matches
acceptance order; all final persisted states have 64 actors and zero pending jobs.
The [JSON record](functional-dependencies-f4-performance.json) includes receipt
latency, queue age, leased-to-result time, serialized views/state, server RSS and
final per-actor slot sizes. RSS measures the server only, not the browser or
whole process tree. Input statistics contain 24 real keydown-to-frame samples per
mode. Capacity should be remeasured on the intended lecture hardware and network.

## Diagnosis and regression evidence

Instrumented WebKit key-activity runs isolate the two host costs. They are
diagnostic comparisons; the final matrix above runs without that instrumentation.

| Diagnostic run | All 64 complete (s) | Feedback p95 (s) | Median before worker init (ms) | Median engine evaluation (ms) |
| --- | ---: | ---: | ---: | ---: |
| startup-profile | 22.56 | 21.87 | 44 | 16 |
| asset-cache-profile | 12.65 | 12.12 | 0 | 15 |
| scheduled-profile | 6.75 | 6.71 | 0 | 15 |

The small engine computation did not explain the queue latency. Repeated asset
requests and expensive full-class broadcasts delayed progress. Sharing immutable
bytes and reserving time between broadcasts improved throughput without reusing
workers or raising limits.

- Final host regression: **154 passed, one skipped** (Windows symlink permission).
- All three browsers pass absence/pending, same-actor resume, identical receipt
  replay, close-with-pending, evaluator replacement, stale-generation rejection
  and reset/late-result checks. Replacement preserves retry and owner safeguards.
- Full FD phone/presenter/projector sequences pass in all three browsers: all
  seven lesson variants, privacy, alternative answers, draft/focus retention,
  keyboard/touch controls, anonymous sharing, reset and teardown.
- FD, relational and transaction engines pass active security probes in all three
  browsers. Network/child/blob-worker/external-import/eval restrictions, invalid
  result rejection, timeout, cleanup and recovery remain enforced.
- Linux Python 3.12 consumer: **96 passed,
  1 skipped**, including the exhaustive tiny-theory regression.
  The TeX authoring test is explicitly skipped because this isolated environment
  has no TeX installation. The installed FD engine probe passes. Dependencies
  came from the host's hash lock; Node's archive matched its official SHA-256.

## Exact artifacts and evidence boundary

FD remains version 0.3.0, payload
`d7cdd50ed7f1c79a8ac6501cc62d544a4bc0ada935c86c4f904a87952aba1f4c`, with byte-identical provider code.

| Artifact | SHA-256 |
| --- | --- |
| Final host wheel | `968c94b5fb9334887904c1ad9831ee1dea617451be491602789eeb3363439cb7` |
| Unchanged FD wheel | `85978a68ccc8be9f4831fd3f287efbe922cedee9192d4cdfe3bbaf3d34909c94` |
| UI/security host wheel | `888677b3e95a4da55644fa78c2a844016ddb5f4f12cbce6926257db2724d3b66` |

Windows and Linux resource-byte checks verify installed contents against the
final wheel files. The final host differs from the UI/security wheel only in
`texstage/plugins/manifest.py`; evaluator/worker/contracts and all browser bytes
are identical. The final cache isolation is covered by host regressions, Linux
installed-provider tests and the final load/reconnect matrix.

The host wheel includes existing renderer/language working-tree changes as well
as these classroom fixes. The JSON records every packaged source hash. Neither
`0.2.1.dev3`, baseline `de33515` nor a partial local commit alone identifies this
tested artifact. The reviewed final host wheel is retained locally under
`texstage-public/dist/fd-webkit/`; generated artifacts are not committed.

The committed sources use the repository's LF line-ending rules. Rebuilding
from a clean checkout can produce different wheel/payload hashes from these
earlier Windows artifacts. Release CI must generate and verify new immutable
artifacts; use the recorded wheel bytes for reproducing these measurements.

## Reproduce and remaining release work

Install the exact host/FD wheels in a disposable environment and prepare the
[example lesson](../fd-lesson.md). Install the collection's locked browser tools.
Set `PYTHON` to that interpreter, `BROWSER` to one of `chromium`, `firefox` or
`webkit`, and `TEXSTAGE_CLASSROOM_RECONNECT=1`, then run:

```sh
node maintenance/fd_classroom_browser.cjs path/to/lesson.bundle
```

The default run enforces unchanged targets. `TEXSTAGE_EVALUATOR_PROFILE=1` adds
worker timing diagnostics only; it does not relax CSP or deadlines. Leave it
unset for final timing measurements. The harness uses its own loopback port,
profiles and synthetic identities, and stops only its owned server process tree.

Next, finalize and publish a compatible immutable host commit including the
renderer context, pin it in FD CI, and run the existing Linux producer, browser
consumers and Windows consumer on identical artifacts. Linux authoring and Linux
browser checks remain untested locally. A published catalog entry requires those
release artifacts and checks. No push, catalog publication, original-repository
change or existing-course migration is included in this round.

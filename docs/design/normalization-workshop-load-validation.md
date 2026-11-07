# Normalization Workshop: synthetic load validation

The [WebKit follow-up](normalization-workshop-webkit-validation.md) supersedes
this record's capacity limit for the newer tested host. This file preserves
the original measurements and exact older artifacts.

Date: 2026-11-07. Local experimental evidence; no release, commit, push or
course migration. The companion JSON records exact wheels, source inputs,
dependency locks, fixture inventory, test reports and raw evidence hashes.

## Result

The current integrated host passes 64-student single-item bursts in Chrome,
Firefox and WebKit. All latest answers are retained and checked, including
replacement bursts and presenter reconnect. **WebKit still fails the 30-second
target for two simultaneous items at 64 participants**: the slower item's p95
is 38.91 s. Chrome and Firefox pass that workload.

The WebKit 32-student workload passes. Use at most **32 submitting groups as a
provisional multi-item pilot**. These are desktop loopback measurements of the
two included synthetic exercises, not a classroom-network, worst-case FD set
or physical-phone guarantee. The 64-actor storage ceiling is unchanged.

The shared host now caches checked schemas, coalesces audience/result broadcasts,
continues draining a busy evaluator queue without idle polling delays, and
requeues an observed disconnected presenter's leases. Presenter controls stay
immediate. The cache owns exact-content snapshots and retains at most 128
schemas of at most 64 KiB; every value is still validated. Generation/owner/epoch
checks, retry counts, hook/worker deadlines and worker restrictions remain.

Earlier cache-only measurements exposed the broadcast/reconnect bottlenecks.
While this probe was being developed, the shared checkout gained the complete
host fixes through the FD Lab work. They were preserved and retested here;
the parallel cache prototype was not copied over them. The exact final wheel
below supersedes the earlier baseline/cache-only artifacts.

## Workload and budgets

The fixture is generated from the existing synthetic registration and tutor
sources through the installed authoring/build pipeline. It has one single-item
frame and one frame with both items active. Authenticated WebSocket students
join normally. An actual presenter page evaluates through the production worker;
a projector and separately authenticated control connection are also present.

1. One submission per student.
2. A burst of wrong replacements followed immediately after each ACK by the
   correct replacement. Pending work may be cancelled; the latest version
   must become checked. Stale outcomes must not overwrite it.
3. At 64 actors, a 65th actor is refused with the domain capacity receipt.
4. Every student submits to both simultaneously active items.
5. Close the presenter, reopen with its worker response deliberately held,
   submit a new batch, observe a real lease, then close/reopen normally.
   A second generation is observed for both abandoned jobs. The current host
   releases them on observed disconnect; the 120-second expiry fallback remains.

Budgets were selected before the runs: p95 command acknowledgement <= 5 s,
p95 latest-answer checked latency <= 30 s, and maximum reconnect recovery <=
150 s. They are probe targets, not existing product promises. The
WebKit 64-actor run exits unsuccessfully because its latency fails, even though
correctness checks pass. Both items eventually finish; this is bounded completion evidence,
not a proof of scheduler fairness for arbitrary workloads.

Participant state is inspected throughout: worked answers, feedback and
analysis stay private before reveal. The probe checks current answer versions,
receipts and checked status. Mathematical correctness and replacement/reset
races also have independent installed-provider regression coverage.
There is no change to workshop math, schemas, state or renderers.

## Measurements

All numbers below are seconds from the synthetic sender's monotonic clock.
“Checked” includes queueing, evaluator work, result handling and delivery to
that student. Replaced obsolete versions are intentionally excluded.

| Run | Batch | ACK p95 | Checked p95 | Checked maximum |
| --- | --- | ---: | ---: | ---: |
| current-chromium64 | initial | 0.26 | 3.41 | 3.81 |
| current-chromium64 | replacement-latest | 0.57 | 3.72 | 3.74 |
| current-chromium64 | multi-registration | 0.43 | 5.93 | 5.96 |
| current-chromium64 | multi-classify | 1.01 | 11.77 | 11.78 |
| current-chromium64 | reconnect | 0.49 | 8.42 | 8.43 |
| current-firefox64 | initial | 0.42 | 4.53 | 4.93 |
| current-firefox64 | replacement-latest | 0.67 | 4.73 | 5.10 |
| current-firefox64 | multi-registration | 0.48 | 7.16 | 7.73 |
| current-firefox64 | multi-classify | 1.09 | 13.19 | 13.80 |
| current-firefox64 | reconnect | 0.50 | 8.78 | 9.48 |
| current-webkit64 | initial | 0.28 | 10.72 | 11.13 |
| current-webkit64 | replacement-latest | 0.85 | 11.28 | 11.72 |
| current-webkit64 | multi-registration | 0.50 | 18.23 | 18.84 |
| current-webkit64 | multi-classify | 1.24 | 38.91 | 39.92 |
| current-webkit64 | reconnect | 0.47 | 20.20 | 20.85 |
| current-webkit32 | initial | 0.13 | 4.00 | 4.01 |
| current-webkit32 | replacement-latest | 0.25 | 3.84 | 3.86 |
| current-webkit32 | multi-registration | 0.22 | 5.57 | 5.58 |
| current-webkit32 | multi-classify | 0.42 | 9.99 | 10.01 |
| current-webkit32 | reconnect | 0.18 | 5.83 | 5.84 |

Server queue time is measured separately from durable command completion to
the first lease. Browser worker timings observe actual postMessage exchanges;
they are not the server queue time. Hook timings include serialization and IPC,
and the first initialization includes subprocess startup. Raw traces and the
JSON record retain p50/p95/p99/max, outcomes, re-leases and hook failures.

The historical cache-only 64-actor run generated more than 75,000 view-hook
calls, took up to 176.55 s for the two-item burst, and up to 172.49 s for
reconnect. The integrated host reduces the Chrome maxima to 11.78 s and 8.43 s.
Its Firefox maxima are 13.80 s and 9.48 s; WebKit remains slower at 39.92 s and
20.85 s. The remaining failure is retained as a capacity gate.

These are single local runs on an ordinary Windows desktop, with instrumentation
and no claim of an isolated benchmark machine. A host test run overlapped part
of the historical cache-only 64-actor run. The final browser matrix ran
sequentially without our regression tests running. This is not a calibrated
hardware comparison or a universal classroom maximum.

## Validation and artifacts

- Current host regression: 112 passed, 1 skipped (Windows symlink creation privilege), including schema-cache, broadcast,
  evaluator polling, disconnect and role-isolation checks.
- Installed workshop suite: 52 passed. The unchanged 0.3.1 wheel retains its
  earlier source-distribution payload-parity evidence.
- Full 64-actor load/reconnect matrix: Chrome 156.0.8078.80, Firefox 153.0 and
  WebKit 26.5. Additional WebKit 32-actor run. Historical four-/16-actor
  runs remain separately identified in the JSON; they used earlier host artifacts.
- Full normalization lesson UI regression in all three browsers: comparison,
  explicit sharing, reveal, classification/decomposition, replacement/conflict,
  reset/navigation, draft/focus and private transport.
- Locked runtime/development dependencies in a fresh disposable environment.
  Both host and provider imports resolve to installed wheels.
- The first host test invocation hit the Windows default-temp ACL; the rerun
  used an explicit disposable base directory and passed.
- Original repository, courses and their environments are unchanged.

The final host is the existing development commit plus the shared working-tree
classroom and accessibility fixes. This task adds the normalization workload and
documentation; it does not overwrite those host changes. Final wheel SHA-256:

`6a6e0a5cb9da1f448f4dcfea7fecb7096dd5b0a3eec594922de26765338c4bad`

Provider 0.3.1 payload:
`8b97cd83a1cb0130762ac18cb195dc3147c221fe7390f93306f92ba5cfad94a1`

Provider wheel SHA-256:
`d6594541e56cb9c1c21e87c2f3d63330a8d2df04bb3848069a560ba1b24bbecc`

The development version alone is insufficient to identify this host. A published
compatible pin is still needed before hosted CI/catalog release. Active worker
network/dynamic-code probes were not rerun in this workload. CSP and restricted
worker bytes are unchanged; the evaluator's polling change is covered by the
host tests and actual browser runs. Earlier active security evidence remains
separately dated.

## Reproduce

Install the matching host/provider wheels and the host's locked dependencies
into a disposable environment. In the collection, install its locked Playwright
dependencies/browser. Then run:

```sh
python maintenance/normalization_load_probe.py --output artifacts/normalization-load-fixture
node maintenance/normalization_load_browser.cjs artifacts/normalization-load-fixture/build/load.bundle
```

Set `PYTHON` to that environment's Python, `NORMALIZATION_ACTORS` to 4, 16, 32 or 64,
and `NORMALIZATION_LOAD_OUTPUT` to a fresh output directory. The default is
64 and an unsuccessful latency gate is intentional evidence, not an ignored
error. Use `NORMALIZATION_SKIP_RECONNECT=1` only for smoke runs.
`BROWSER=firefox` or `BROWSER=webkit` selects those engines; use
`TEXSTAGE_BROWSER_CHANNEL=chrome` only for Chromium. `TEXSTAGE_TEST_PORT` selects
a free loopback port. No existing presenter profile or course is used.

The loopback probe server observes calls without altering their results. It
writes timing events without authentication tokens or answers and shuts down
through the server's normal lifespan, including its provider subprocess.
Profiles contain synthetic credentials and are not publication artifacts.
Local evidence is retained under ignored `artifacts/normalization-load/`.

## Remaining work

Investigate WebKit's two-item queue/worker startup latency at 64 actors.
Measure per-session fairness and repeat the same budgets before raising the
provisional multi-item pilot size. Do not increase deadlines or skip validation
to turn a failed gate green.

Physical Android/iPhone LAN testing, human screen-reader and new-learner review,
a compatible published host pin, hosted cross-platform CI and immutable catalog
publication remain open. No tested desktop size replaces those gates.

# FD Lab F4: classroom load and recovery

Automated checks completed locally on 2026-11-07. F4 is **not fully accepted**:
the WebKit 64-answer burst misses the provisional 10-second feedback p95 target.
The physical-phone check is deferred at the user's request; this round covers
automated checks only. See the [plan](functional-dependencies-plan.md),
[lesson guide](../fd-lesson.md) and [machine-readable record](functional-dependencies-f4-validation.json).

## What changed

The FD provider remains 0.3.0 with unchanged runtime resources and payload
`d7cdd50ed7f1c79a8ac6501cc62d544a4bc0ada935c86c4f904a87952aba1f4c`.
The load tests exposed generic host costs, fixed in the active Texstage checkout:

- Cache checked validators by complete schema content in owned snapshots,
  bounded to 128 entries of at most 64 KiB. Every instance remains validated.
- Coalesce student submissions and evaluation-result projections at the normal
  200 ms update interval. Presenter phase/selection/sharing controls remain immediate.
- Continue draining a busy queue without the idle 750 ms delay between batches.
  Preserve two-job leases, fresh workers, the two-second evaluation deadline and CSP.
- Requeue a disconnected evaluator's leases without resetting the retry count.
  Preserve generation/owner/epoch checks and the 120-second expiry fallback.

A full UI regression caught stale presenter controls when all commands were
initially coalesced. The final implementation keeps those human controls
immediate; the final UI sequence verifies private selection followed by sharing.

## Exact artifacts and evidence boundary

| Artifact | SHA-256 |
| --- | --- |
| Final `texstage-0.2.1.dev3-py3-none-any.whl` | `3a73b26003c8ffbc0cf3cad1ad851fd84b6bf726d87cceddf13abc8195763b2a` |
| `texstage_fd_lab-0.3.0-py3-none-any.whl` | `85978a68ccc8be9f4831fd3f287efbe922cedee9192d4cdfe3bbaf3d34909c94` |
| Earlier host used by broad regression/security runs | `a52ec15b34533a3cfab111a48afe115455e9c1ebc95049533982cf238cf9bf51` |

The host starts at commit `de33515` plus uncommitted classroom changes. Its
development version alone is not a release pin. The final wheel is verified
against its installed runtime and the changed source files. Between the earlier
host and final wheel, runtime differences are the presenter-command immediate-
push fix and concurrent language, keyboard and presenter-scroll improvements,
which were preserved during integration. The machine record names every changed
resource. Worker security code, evaluator, validator, durable runtime and provider
resources are byte-identical. The final merged host received the
focused server/plugin tests, full lesson UI matrix, and load/reconnect matrix.

No original repository, existing course, course environment or private media was
changed. No commit, push or publication was performed.

## Measured 64-answer bursts

Hardware: 11th Gen Intel Core i9-11950H at 2.60 GHz, 16 logical CPUs, about
63.2 GiB RAM, Windows 10 build 19045. Browsers: Chromium 156.0.8078.80,
Firefox 153.0, WebKit 26.5. Python 3.14.4 and Node 24.15.0.

Each run uses 64 synthetic WebSocket actors, one additional 320 px rendered
participant connection for actor 1, an actual presenter/evaluator browser, and
a protocol controller. The three bursts submit correct closure, all-key and
negative-implication answers from the unchanged example deck. Each finishes with
64 checked answers and no pending jobs. FIFO lease order matches acceptance order.
These are loopback development measurements on a shared workstation, not a
controlled benchmark or 64 physical browsers/phones.

| Browser | Activity | ACK p95 (s) | Feedback p95 (s) | Worst feedback (s) | Queue p95 (s) | Input p95 (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| chromium | practice | 0.35 | 5.76 | 6.22 | 5.07 | 3.1 |
| chromium | keys_all | 0.44 | 4.13 | 4.55 | 3.39 | 6.1 |
| chromium | refuted | 0.33 | 3.58 | 4.00 | 3.00 | 3.1 |
| firefox | practice | 0.47 | 7.86 | 8.37 | 7.00 | 1.0 |
| firefox | keys_all | 0.45 | 8.01 | 8.54 | 7.22 | 1.0 |
| firefox | refuted | 0.40 | 5.44 | 5.46 | 4.60 | 2.0 |
| webkit | practice | 0.49 | 14.79 | 15.25 | 13.64 | 12.0 |
| webkit | keys_all | 0.46 | 13.66 | 14.10 | 12.56 | 11.0 |
| webkit | refuted | 0.59 | 14.88 | 15.77 | 13.14 | 12.0 |

Targets remain input p95 below 100 ms, feedback p95 below 10 s, and worst
feedback below 30 s. The machine record retains every final target result.
The original host needed about 391 seconds for the key burst; the first partial
optimization still needed about 32 seconds. An earlier contended Chromium run
also recorded 123.2 ms input p95 on closure. Those results are retained, not
reclassified as passes. Rerun the harness on the intended lecture hardware.

Quantiles use nearest rank. ACK and feedback are measured from protocol send
to receipt and first received checked own-answer view, respectively. Queue time
starts after durable command acceptance and ends at the first lease. Lease-to-
result includes worker startup and transport, not just mathematical evaluation.
Input timing uses 24 trusted Enter-key events per mode, from browser event
timestamp to the next animation frame; it is not physical touch-to-screen latency.

Reports include whole transmitted participant/presenter state sizes, final exact
stored actor/state sizes, queue exhaustion, and sampled main-server RSS. RSS
excludes browser and provider subprocess memory. The earlier sampled state-byte
maximum is recorded separately from the final read-only SQLite snapshot. Worst-
case storage tests with 256 proposed keys per actor remain in the F3 record.

## Recovery, privacy and regressions

Replacing a presenter after disconnecting its socket while it held a job took
chromium: 0.73 s, firefox: 1.98 s, webkit: 1.15 s. These timings include starting the replacement page.
Actual host checks cover pending status without an evaluator, same-actor resume,
identical receipt replay, close-with-pending, reassignment from generation 1 to 2,
rejection of an old result, and reset followed by a late result. Failed service
work never becomes an incorrect mathematical answer.

- Broad host regression: 414 passed, one skipped. Six registry-dependent checks
  initially hit sandbox access failures; all six passed in a unique disposable
  test registry subtree, which was verified removed afterward.
- Final focused host/server/plugin/language regression: 123 passed,
  one skipped because this Windows host disallows symlink creation; the
  keyboard-shortcut Node regression also passed.
- Installed FD regression: 96 passed, one deliberately deselected exhaustive
  tiny-theory test. Its F3 pass is retained against byte-identical provider code.
- Full phone/presenter/projector sequences pass in all three browsers, including
  privacy, reveal, anonymous sharing, alternative answers, draft/focus preservation,
  same-actor conflicts, keyboard/touch interaction, reset and teardown.
- FD, relational and transaction providers coexist in a separate test environment.
  All three engines pass their active security probes in all three browsers:
  network access, child/blob workers, external module imports, eval and Function
  remain blocked, with positive controls and timeout/recovery checks. This is
  engine coexistence evidence, not complete classroom coverage of every provider.

## Reproduce and remaining work

Use an isolated environment with the pinned host and FD wheels and the collection's
locked browser tools. Build the example bundle as described in the lesson guide.
Set `PYTHON` to that interpreter, `BROWSER` to `chromium`, `firefox` or `webkit`,
and `TEXSTAGE_CLASSROOM_RECONNECT=1`, then run:

```sh
node maintenance/fd_classroom_browser.cjs path/to/lesson.bundle
```

The runner reserves its own loopback port and creates its own profile. Reports
go under `artifacts/fd-classroom/`. Timing misses cause a nonzero exit. Optional
`TEXSTAGE_CLASSROOM_ENFORCE=0` collects diagnostic data without making a failed
target a pass. Optional `TEXSTAGE_CLASSROOM_PROFILE=1` profiles one broadcast;
do not treat that instrumented run as the final timing gate. Only owned server
process trees are stopped afterward.

Next: investigate WebKit's remaining queue latency without relaxing isolation,
then make a reviewed capacity decision. Physical LAN-phone validation remains
deferred. Linux, hosted CI and an immutable compatible public host release have
not been established by these local checks. F5 publication remains a separate step.

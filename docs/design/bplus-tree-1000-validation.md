# B+ capacity: 600 students, 1,000 ceiling

Local Windows verification on 2026-11-07. B+ **0.6.0** and the matching TeXStage
host implement a normal-class target of **600 students** and a hard limit of
**1,000 saved answers per activity**. All six browser/size combinations preserved
every latest answer and recovered interrupted evaluation. Five met all latency
targets; WebKit at 600 narrowly missed its 30-second replacement target. This
is evidence for a classroom pilot, not certification of campus Wi-Fi or 1,000
physical phones. The [JSON record](bplus-tree-1000-validation.json) retains every
final measurement, including that miss.

## Workload and results

Each run used authenticated synthetic student WebSockets and the real presenter
browser, fresh evaluation workers, installed wheels and production security
policy. It exercised simultaneous initial submissions, immediate wrong-to-correct
replacement, duplicate receipt retry, student resume, outstanding evaluator leases,
presenter disconnection/recovery, private inspection, sharing, reveal, and roster
paging. At 1,000 the host refused student 1,001. Separate runtime tests enforce
the provider's record cap and replacement at capacity.

Each 600-student run accepted 2,400 submissions and validated all 1,800 required
latest results; each 1,000-student run accepted 4,000 and validated all 3,000.
Superseded wrong submissions need not be graded. Every revealed latest grade
was correct; private rosters, inspection and unrevealed feedback stayed private.
All runs shut down gracefully, with no hook errors or missing final results.

| Students | Presenter browser | Initial p95 ACK / ready | Replacement p95 ACK / ready | Recovery: slowest ready | Latency target |
| --- | --- | --- | --- | --- | --- |
| 600 | chromium 156.0.8078.80 | 3.59 s / 17.27 s | 4.69 s / 18.20 s | 18.44 s | Pass |
| 600 | firefox 153.0 | 3.01 s / 15.37 s | 3.99 s / 16.66 s | 17.49 s | Pass |
| 600 | webkit 26.5 | 2.79 s / 22.61 s | 4.59 s / 30.78 s | 26.47 s | **Miss** |
| 1000 | chromium 156.0.8078.80 | 5.11 s / 23.99 s | 8.21 s / 31.69 s | 30.36 s | Pass |
| 1000 | firefox 153.0 | 4.78 s / 25.81 s | 8.13 s / 33.39 s | 30.82 s | Pass |
| 1000 | webkit 26.5 | 4.94 s / 38.79 s | 8.58 s / 48.09 s | 43.99 s | Pass |

ACK measures receipt of the durable acknowledgment. Ready measures receipt of
the saved evaluation status, not immediate disclosure of mathematical feedback:
the example uses `on-reveal`. Recovery includes reconnection and the queued work.
Targets remain ACK/ready p95 ≤5/30 s at 600, ≤10/60 s at the 1,000 peak ceiling,
and recovery maximum ≤150 s. Misses were retained rather than relaxing thresholds:

- webkit at 600: replacement-latest ACK 4.59 s, ready 30.78 s

The runs were sequential on an Intel Core i9-11950H @ 2.60GHz, 16 logical CPUs,
Windows 10.0.19045. Server, synthetic clients and browser shared one computer over
loopback. Python 3.14.4, Node v24.15.0, Playwright 1.62.1 and
esbuild 0.28.2 were used. Firefox needed normal OS subprocess permissions in the
runner; no browser-security flags or application CSP exceptions were added.

## Implementation and bounds

Manifest revision 3 adds generic host-owned actor records. Each student's answer,
summary, shared-state revision, job/cancellation and receipt commit atomically.
The host chooses the authenticated actor; effects cannot choose another identity.
Presenter-only record lookup stays scoped to the same session, item and epoch.
The roster has 25 entries per page and stable response numbers. Shared state
contains controls/counts and at most two explicitly selected snapshots.

Participant updates target the affected student's devices. Phase, sharing,
replay, reset and late feedback for a shared answer still invalidate the whole
class. Phones omit whole-class answer counts. Existing providers retain default
full updates. Batched projections use fresh per-audience inputs, schema checks
and bounded output/deadlines; whole-class background sends yield after 16 sockets.
SQLite read snapshots keep state, records and roster pages consistent.

The evaluator leases two fresh workers normally, four with at least 32 eligible
jobs, and eight at 128. Lease batches commit once before delivery. SQLite FULL
durability, the 1,000-job ceiling, result/identity validation, deadlines, retry
limits, fresh workers and restricted worker CSP are unchanged.

The worst-case storage test admitted 1,000 records with bounded escaped actor
identities, large answers and maximal bilingual explanations, and checked all
40 roster pages through Python and JavaScript validators:

| Measurement | Canonical bytes |
| --- | ---: |
| Largest tested answer | 752 |
| Reserved compact slot, including feedback | 563 |
| Shared state | 3372 |
| All private record values combined | 529001 |
| Transition including effects | 4473 |
| Participant view | 33200 |
| Presenter controls | 59878 |

Provider limits are 704 bytes per encoded slot, 16 KiB shared state, 24 KiB
transition and 80 KiB per view. Host limits remain 4 KiB per record, 512 bytes per
summary, 256 KiB transition, 128 KiB view and 8 MiB IPC frame. Large storage tests
establish byte bounds; the load measurements use the synthetic insertion example.

## Regression, UI and artifact evidence

- **126 provider tests passed**; **186 host tests passed, 1 skipped**. Coverage
  includes capacity/replacement, persistence/reset, receipts, transaction rollback,
  actor privacy, read-snapshot consistency, yield-safe membership changes, multiple
  devices per actor and global notification precedence. The JSON names the skip.
- Thirty engine cases and 34 browser samples per family passed. Active fetch,
  XHR, WebSocket, EventSource, child/blob worker, external-module, `eval` and
  `Function` probes were blocked; invalid results, timeout and cleanup checks passed.
- Real UI flows passed for all six example operations in Chromium, Firefox and
  WebKit in English, plus Chromium in German. They cover phone touch/keyboard,
  preview, undo/redo, dirty drafts, same-actor/reset conflicts, private inspection,
  sharing, replay, reveal, navigation and a 320-pixel viewport. These are desktop
  browser emulations, not physical-device results.
- Visual inspection confirmed the settled presenter roster at page 40/40 with
  1,000 saved answers and readable private inspection. The 320-pixel phone editor
  fits its viewport with labeled fields and 44-pixel minimum touch targets;
  the accessibility snapshot exposes those labels. This is not a screen-reader
  or physical-projector certification.
- English/German bundles were rebuilt with the exact provider payload. Generated
  schemas/workers and wheel/sdist parity were checked. The final source-package
  bytes match the wheels. Hosted CI has not run for these uncommitted changes.

Provider payload: `87ffc31f4ea9ea1b507532faf7d468c0280c310b63182a13c71ece5c75242c83`. Result schema:
`7e5ae204c3226b03ed4ca1250b5f1aa5d63b808256ec14f13b16e826a5fdd6c2`.

Final wheel SHA-256:

- host `texstage-0.2.1.dev3-py3-none-any.whl`: `be1870986f88fbcbd7d67de4b9c4ec6df07ffde48c3b9f7d28f1d9ba864bde79`
- provider `texstage_bplus_lab-0.6.0-py3-none-any.whl`: `0ef1487ef301b1e0d9c2133cb514048e5d7609498f9239feead0e0de9ffa6ab4`

The capacity/unit/security runs used provider wheel SHA-256
`6103505c5f8a5d68963f949dd8f125847ed0de335e67453cc4890cfb2c05fda1`. A final package README correction
changed only wheel METADATA/RECORD; every runtime and resource byte, including
the provider payload, remained identical. The real UI runs used the final wheel.
Both identities and the member comparison are retained in the JSON record.

## Use and remaining gates

The local changes are on `codex/bplus-1000-capacity` in the isolated
`texstage-bplus-1000` and `texstage-plugins-bplus-1000` worktrees. They are not
committed or pushed. Host base: `34d0c537135f32b0690147dbb66dd8ff155987f8`;
collection base: `c05cc9e080b330cc2822a3bbc17ba80acb67de0d`. The code includes the earlier
300-student adaptation and the actor-record prerequisite, with scoped capacity
changes; it still needs reviewed integration with concurrent host development.

Use matching host/provider builds, explicitly enable the exact payload,
regenerate the lock, rebuild the bundle and start a new session. Existing
state-schema sessions are not migrated. Keep the presenter browser active.
The [classroom guide](../bplus-classroom.md) provides commands and controls.

Before publication, publish the compatible host commit and set the immutable
`TEXSTAGE_BPLUS_HOST_REF` CI pin (or the manual `bplus_texstage_ref` input).
The manual `bplus-capacity.yml` runs all three browser families at 600 and 1,000
against an explicit host SHA. Missing host pins fail clearly.

Repeat on the intended classroom server, using physical phones and campus Wi-Fi.
Measure device UI latency, memory and queue fairness; add mixed-provider,
multiple-presenter peak load and identical-wheel Windows/Linux transfer checks.
The local WebKit 600 latency miss remains open. No physical-phone, hosted-CI or
published-compatibility claim is made. Original repositories, existing courses,
course environments/pins, private media and the earlier 300-student worktrees
were preserved.

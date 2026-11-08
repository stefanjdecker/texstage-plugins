# Classroom release validation — 2026-11-08

The transaction engine/activity and Relational Algebra Lab remain experimental
release candidates. This record separates installed-package tests, synthetic
classroom measurements and physical acceptance. The phone/network/accessibility
rehearsal is **not performed**: the maintainer requested the
[checklist](../classroom-device-checklist.md) for later.

## Reproducible source and artifacts

- Host: `cdf20af0fa53e284b7a49c1a4cbd18245599c6a9`, published on the
  [GitHub branch](https://github.com/stefanjdecker/texstage/tree/codex/classroom-release)
  and [GitLab code mirror](https://gitlab.git.nrw/rwth-dbis/infrastructure/texstage/-/tree/codex/classroom-release).
- Collection implementation/harness: `c04887bd4729c4ceca1f850e173124c9176834b9`,
  on [codex/classroom-release](https://github.com/stefanjdecker/texstage-plugins/tree/codex/classroom-release).
  Later documentation commits do not change the provider payloads.
- Host version: `0.2.1.dev7`. Use the commit and artifact hash, not this reused
  development version string alone.

| Local candidate wheel | SHA-256 |
| --- | --- |
| `texstage-0.2.1.dev7-py3-none-any.whl` | `e0716492508ec893df859d0dd87fdf2ba0a93a14ce8cf23244e19380e13f9da8` |
| `texstage_transaction_engine-0.1.0-py3-none-any.whl` | `6f06262b52b81b447ac3c650e07c231cc6b34826f2af627ccae5b20358405bbc` |
| `texstage_transaction_activity-0.1.0-py3-none-any.whl` | `027afc7b7e31e6717a66e937c1268bb6fde5ba4036e92a885a5f9a12dd892a51` |
| `texstage_relational_lab-0.2.0-py3-none-any.whl` | `2bd57540b745abc146458d0f269fee8809bd527d41089139afc0abc8fbfc2e4a` |

The [machine-readable record](classroom-release-validation.json) includes source
archive hashes, provider payloads, test identities and sanitized measurements.
All three plugin wheels were rebuilt from their source distributions with
matching provider manifests. The final host wheel and its source rebuild have
byte-identical uncompressed members; those members also match the wheel used in
the final local scheduling probes. The CI archives differ from the local
archives in `METADATA` line endings and the corresponding `RECORD` digests;
every runtime file and plugin manifest was byte-compared equal. Hosted checks
record their own producer hashes and consume exactly the same producer wheels
on Windows and Linux. Keep the two sets of archive hashes distinct.

## Host changes and invariants

Participant commands now use a 64-entry queue and durable groups of at most
eight saves. Each save retains authentication, actor privacy, schema checking,
epoch/revision guards and its own retry receipt. Rejected commands roll back
individually; a failed outer commit acknowledges none. SQLite WAL remains
`synchronous=FULL`.

Immutable schema predicates and checked specification text avoid repeated
parsing. Unsupported schema keywords and failures use the authoritative
validator. Every input is still checked, and hooks receive fresh objects.

Receipt writers and presenter controls get event-loop turns between batches.
Audience refreshes may defer for one extra second during a burst. New evaluator
leases yield during the first second of a busy submission queue, using the
existing idle poll; this preference cannot restart during continuous traffic.
The adaptive evaluator uses two fresh workers for small queues and at most four
for large queues. No worker pooling, relaxed CSP, larger hook deadline or
reduced durability was introduced.

The load harness now waits for server-confirmed slide navigation. Empty timing
samples fail their gates, and presenter startup failures preserve diagnostics.
The B+ workflow creates its pytest artifact parent before testing. A Windows
host test now sets explicit build timestamps and verifies access to an older
uploaded build separately from the newest-build library listing; lecturer
isolation assertions remain in place.

## Tests and measured capacity

The local installed-wheel host suite passed **635 tests**, with one unavailable
Windows symlink-creation check skipped and two subtests. That full run used
`0f2389c`; the final scheduling changes subsequently passed **51 targeted host
regressions**. The deterministic lecturer test suite passed seven tests.
Independent installed plugin suites passed: transaction engine **67**, activity
**44**, and relational lab **74**. Final hosted runs below recheck the exact
candidate, including all six transaction lessons in both languages and the
general collection's engines, authoring, browser interfaces and sandbox checks.

<!-- CI-RESULTS-START -->

| Final candidate check | Observed result |
| --- | --- |
| [Host CI](https://github.com/stefanjdecker/texstage/actions/runs/42458697864) | All five jobs pass: Linux Python 3.12/3.13/3.14, Windows 3.14 and container startup |
| [Plugin conformance](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42458732389) | 31 jobs pass; one optional FD capacity job intentionally skipped |
| [Transaction classroom](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42458730616) | Producer and all six Windows/Linux browser jobs pass; 20 of 24 capacity jobs pass |
| [B+ capacity](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42458734214) | Chromium/Firefox pass at 600/1,000, including scoring and recovery; Linux WebKit crashes at both sizes |

The transaction capacity matrix is **not all green**. All 30-second waves pass.
Synchronized bursts have the following results; a timing value from a crashed
run is only a partial measurement:

| Runner | Presenter | Students | Ack p95, ms | Burst result |
| --- | --- | ---: | ---: | --- |
| ubuntu-24.04 | chromium | 600 | 1294.95 | Pass |
| ubuntu-24.04 | chromium | 1000 | 3216.45 | p95 exceeds 3,000 ms |
| ubuntu-24.04 | firefox | 600 | 1247.78 | Pass |
| ubuntu-24.04 | firefox | 1000 | not measured | No samples: slide-acknowledgement setup timeout |
| ubuntu-24.04 | webkit | 600 | 1265.69 | Presenter crash; repair incomplete |
| ubuntu-24.04 | webkit | 1000 | 1827.61 | Presenter crash; repair incomplete |
| windows-2025 | chromium | 600 | 1337.39 | Pass |
| windows-2025 | chromium | 1000 | 2875.82 | Pass |
| windows-2025 | firefox | 600 | 1321.68 | Pass |
| windows-2025 | firefox | 1000 | 2773.82 | Pass |
| windows-2025 | webkit | 600 | 1361.58 | Pass |
| windows-2025 | webkit | 1000 | 1186.82 | Pass |

The Linux Chromium/1,000 burst preserves answers and passes correctness, control
and repair-drain gates but misses acknowledgement p95 at **3.216 seconds**.
The Linux Firefox/1,000 burst times out waiting for a slide acknowledgement
before students join, so it supplies no capacity evidence. Linux WebKit crashes
during 600/1,000 burst repairs; the successful earlier runs do not establish
reliable operation. These gates remain open, with no threshold relaxed and no
failed job silently retried into a pass.

<!-- CI-RESULTS-END -->

Load checks use authenticated synthetic student WebSockets, a real presenter
browser and fresh isolated evaluators on loopback HTTP. They cover varied
answers, replacements, receipt retry, reconnect, conflicts, full capacity,
evaluator failover, archives and reset. Transaction activities award no points.
Relational activities remain a **64-participant pilot**; transaction or B+
measurements do not widen that claim.

Frozen transaction gates remain: acknowledgement p95/max **2/5 seconds** at 600
and **3/10 seconds** at 1,000; repair drain **60/120 seconds**; control p95/max
**1/3 seconds** at 600 and **2/5 seconds** at 1,000. The existing acknowledgement
p95 gate aggregates the run's submissions; individual phase timings are retained
separately. A single pass is a measurement on that runner, not a hardware- or
network-independent guarantee.

## Earlier failures remain part of the evidence

The [original validation](transaction-classroom-validation.md) recorded slow
bursts. With durable batching, the first
[hosted matrix](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42456022374)
still had three navigation setup timeouts, a presenter recovery timeout and two
Linux WebKit crashes. A local WebKit/1,000 burst missed p95 at 3.146 seconds.

After navigation waits and the four-worker ceiling, all 24 hosted transaction
loads completed their correctness/control/drain checks. Windows Firefox/1,000
and WebKit/1,000 bursts still missed p95 at **3.003** and **3.081 seconds** in
[that run](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42457555117).
Local Chromium/1,000 measurements also missed p95 at 3.450 and 3.230 seconds;
two restricted-process Firefox attempts failed before opening a page. Firefox
passed with normal browser process permissions. These attempts are retained,
not relabelled as passes.

The final bounded lease deferral reduced the following local 1,000-student
burst measurements to **2.672 seconds** p95 in Chromium and **2.677 seconds** in
WebKit, with correctness, control and repair-drain gates passing.

The four-worker B+ capacity run passed Chromium and Firefox at 600/1,000 but
Linux WebKit crashed at both sizes during sustained fresh-worker execution.
The failure is visible in the
[B+ run](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42457860031).
This is a remaining capacity limitation; ordinary three-browser UI conformance
does not establish WebKit classroom-load reliability. Its cause is not proven
by these measurements. Use Chromium or Firefox for large B+ sessions.

## Remaining acceptance and publication

- Complete the physical phone, intended classroom network and human screen-reader
  checks using the prepared checklist. Do not mark unchecked rows as passes.
- Retain browser/capacity restrictions and failed measurements in release notes.
  Investigate the transaction Firefox setup timeout before treating that case
  as measured; diagnose the WebKit page crashes in both workloads; improve or
  establish deployment constraints for the Chromium/1,000 burst latency miss.
  Re-run the affected scenarios with the same unchanged gates after fixes.
- Resolve the inherited PowerPoint converter's publication license, explicitly
  left open in the host's `NOTICE`, before distributing a host package release.
- Review the prepared wheels, source archives, hashes and draft catalog entries
  through the [release handoff](../transaction-relational-release.md). There are
  no release tags, public release assets, PyPI upload or activated catalog entries
  from this preparation. Proposed asset URLs are not live download links.

The work uses isolated release worktrees and disposable profiles. Original
tools, existing courses, prior working copies and private media are outside
this change.

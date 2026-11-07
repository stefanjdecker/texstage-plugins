# Query-plan 0.5.0: 600-student validation

Implemented and tested locally on Windows, 2026-11-07. The activity now stores
answers separately by authenticated student and pages the presenter roster.
All 600 synthetic students saved answers, received feedback for their latest
version and cleared their answers on reset. This is a measured development
candidate, not a guarantee for 600 physical phones on classroom Wi-Fi.

## Compatible artifacts

- Query-plan 0.5.0, manifest revision 3, content API 1, state schema 3.
- TeXStage 0.2.1.dev4 with the opt-in actor-record contract and batched broadcasts.
- Provider payload: `52a0109da9c688fe6b05db41ea5311cf8c47fdcd844363e0f67e5bfb0666fa9c`.
- Host resource inventory SHA-256: `d6b64b94756b5ec521dcdac2800ffa77b49eb37f1ef512efe8e8ee620ee14ff1`.
- [Machine-readable evidence](query-plan-600-validation.json) records final wheel
  and source-distribution hashes, tests, browser versions and workload results.

The full load run and final packages use the same inventoried runtime resources.
The provider README/metadata was finalized afterward; the final rebuilt wheel
then passed the Python and browser checks. No runtime security setting, deadline
or evaluation implementation changed between those checks.

Use the matching reviewed host, explicitly enable the new provider payload,
rebuild the deck and start a new session. Old sessions remain in their original
environment; there is no automatic migration. The compatible host changes are
local and still need a published commit before hosted release CI can run.

## Measured workload

One real Chromium presenter evaluator and 600 separately authenticated synthetic
WebSocket participants used the actual server on loopback. Chrome
156.0.8078.80, Node v24.15.0, Windows 10.0.19045,
16 logical CPUs. No fabricated evaluation results or relaxed CSP.

| Scenario | Acknowledgment p95 | Latest observed completion maximum |
| --- | ---: | ---: |
| burst | 3.50 s | 43.98 s |
| paced replacements | 10.95 s | 64.86 s |
| absent evaluator replacements | 19.09 s | 82.76 s |
| disconnected evaluator lease | 0.32 s | 7.20 s |
| silent evaluator lease | 0.28 s | 123.97 s |

The initial burst met the targets of acknowledgment p95 within 5 seconds and
all 600 initial evaluations within 60 seconds. Replacement bursts take longer:
the measured acknowledgment p95 reached 10.95–19.09 seconds. The UI retains the
draft and waits for confirmation; this is a concrete latency limitation, not a
claim of uniformly instant responses for large classes.

Three replacement rounds were separated by one second after acknowledgments.
Superseded intermediate versions need not appear on coalesced client views.
The absence scenario saved and replaced plans with the presenter closed, then
completed them after collection closed and the presenter returned. The final
two scenarios abandoned two leased jobs: observed disconnection requeued work;
a silent socket exercised the unchanged 120-second lease. All 600 final answers
had the correct latest feedback; none was marked unavailable.

All 24 roster pages contained at most 25 summaries, covered each actor once in
stable order and supported selecting the last page's answer. No participant
received a roster, private selection or pre-reveal feedback. Reset cleared all
600 answers. Received participant traffic was about 434 MiB over this finite
seven-minute stress run; this is not an hours-long soak or Wi-Fi capacity test.

## Bounds and regression coverage

- 1,000 maximum-shaped saved slots and refusal beyond capacity. Existing actors
  can replace at capacity. This proves storage bounds, not 1,000-client throughput.
- Stress shared state: 3,134 bytes against a 16-KiB limit;
  largest presenter view: 77,010 bytes against 128 KiB.
  Per-record schema/byte checks, scoped reads and 25-row pages remain enforced.
- Atomic state/record/jobs/receipt rollback on queue, storage and CAS failures;
  replay, restart, reset, old epochs and evaluation identity checks.
- 178 Query-plan/release-helper tests and 197 host/server tests passed. One host
  symlink test skipped because Windows did not permit symlink creation.
- Chromium, Firefox and WebKit passed actual UI controls (including pagination),
  role privacy, protocol races, exports, evaluator execution and production-CSP
  security probes. Firefox required normal local browser permissions outside the
  automation sandbox; the application restrictions remained enabled.
- Transaction: 67 tests; relational algebra: 72; coordinate/distance pair: 4.
  All three legacy scenarios also passed Chromium, Firefox and WebKit checks.
- Portable wheel/source-distribution parity and real LaTeX preparation/export
  checks passed. The cost engine and original teaching examples are unchanged.

The host yields between batches of 16 connections rather than blocking socket
replies for a full-class render. Membership, role and current state are rechecked;
new mutations retain a fresh broadcast marker. Existing manifest-1/2 providers
retain their storage contracts. Actor-record support is opt-in and generic.

Physical-phone/classroom-network and screen-reader checks remain manual gates.
This milestone has not yet been revalidated on Linux or in hosted CI. Previous
0.4.0 Linux evidence is historical and is not relabeled as a 0.5.0 pass. The
[release procedure](../query-plan-release-checks.md) now defaults to 600 actors.
The original repository, courses and private media were not changed.

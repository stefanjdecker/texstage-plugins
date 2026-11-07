# ER registration release-readiness evidence

Recorded 2026-11-07. The [machine-readable record](er-release-readiness-validation.json)
contains artifact identities, browser results, hardware and per-actor timings.
The [release checklist](../er-decisions-release.md) explains reproduction and
remaining gates. This is local evidence, not a hosted-CI or release claim.

## Result and limits

The documented pilot is **32 simultaneous responding learners**. At 64 the
current host completed every answer, but warm p95 was 12.01 seconds, exceeding
the planned 10-second target. The 64-actor storage cap remains unchanged.

| Synthetic load | Cold evaluation p95 / last | Warm replacement p95 / last | Warm target |
| --- | --- | --- | --- |
| 32 actors | 2.66 s / 2.66 s | 3.08 s / 3.09 s | Pass |
| 64 actors | 9.90 s / 9.92 s | 12.01 s / 12.73 s | Fail: p95 above 10 s |

The harness sends each wave within about two milliseconds after all learners
join. It measures send-to-observed-evaluated/saved status, before correctness
feedback is revealed. No unavailable outcomes or premature feedback appeared.
The 65th new answer was refused, replacements remained accepted, and receipt
replay did not create another answer version.

After disconnecting a presenter connection with two leased jobs, all 32
replacement answers recovered within 3.74 seconds; the 64-actor case recovered
within 12.72 seconds. The current host requeues an observed disconnect's
unfinished work while retaining generation/retry guards. No lease or worker
budget was increased; the 120-second expiry remains an unobserved-disconnect
fallback. These cases check progress in a finite queued wave, not fairness
under an endless adversarial request stream.

Hardware: Windows, Intel Core i9-11950H at 2.60 GHz, 16 logical CPUs, about
63.2 GiB RAM; Node 24.15.0 and Chromium 151.0.7922.34. Participants are protocol
clients and evaluation uses the real presenter worker. These results do not
establish physical-phone, internet or classroom Wi-Fi performance.

## Artifacts and platform checks

The unchanged ER 0.4.0 wheel has SHA-256
`8d1d18b690879e326d957c7f4b14b18d15f894ae4505a9184368144c3e633490`.
Its provider payload is
`fefb99982fc201506a41ed7a5ee6013b6dba73e46016936aaabe4a1056614ab1`.
The E4 source/wheel/sdist parity record remains applicable; no provider
implementation or distributed resource changed in E5.

The measured host wheel has SHA-256
`e90ac2e4d808d92e39c4a73f3bc2966cb9957e29d996bf9bace156016a0f44f4`.
It includes uncommitted classroom and compatibility changes on top of host
commit `de3351550f3553ca63023554521fbe84806ec94e`. This commit alone does not
reproduce that wheel. Its installed payload hash on both platforms is
`4e3e19d1b549fc7bbe5c24e4fdbe0646b2f8eefb5091f4d0af604a7d4569870a`;
the JSON record includes the per-file hashes.

Windows Python 3.14.4 produced the wheels. Ubuntu 24.04 under WSL2, Python
3.12.3, installed the identical files with Linux dependencies from the host's
hash-locked requirements. Both platforms passed the independent 27-model
registration oracle. Linux did not perform TeX authoring in this local run.

| Check | Result |
| --- | --- |
| Installed ER tests on Windows, including three real TeX builds | 110 passed, no skips |
| Identical ER/host wheel consumer on Linux | 107 passed; three TeX cases explicitly deselected |
| Focused current host tests | 119 passed; one existing Starlette/httpx warning |
| Artifact handoff integrity tests | 9 passed |
| Distance/coordinates exact two-provider environment | 4 passed |
| Transaction-only environment | 67 passed |
| Relational-only environment | 72 passed |

Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5 passed ER engine/security,
English lesson and native German lesson checks. They cover 320-pixel phones,
touch, keyboard/focus, preview, same-actor conflicts, draft preservation,
repair, privacy, sharing, reveal, reset, navigation and text zoom. Screenshots
of the current phone model and presenter view were also inspected. Emulation
does not establish physical-device accessibility.

The transaction and relational engines also passed their browser/security
regressions in all three families. Worker connection attempts, nested workers,
external module loading and dynamic code remained blocked. The deliberate
timeout test recovered and left no worker running.

## Development findings

The initial baseline stalled while repeatedly validating identical schema
definitions. It was aborted and has no valid percentile measurement. Caching
checked schemas and draining busy evaluator batches reduced that cost, but
eager full-classroom broadcasts still produced a 45.89-second warm p95 in an
intermediate run. Coalescing audience/result projections removed that
quadratic broadcast work.

Concurrent host work supplied compatible content-keyed schema caching,
immediate presenter controls, coalesced audience updates, prompt evaluator
polling and disconnect requeueing. Those implementations were retained and
the checks rerun against their combined wheel. An earlier staged variant
passed 64 actors at 8.82 seconds p95; it is superseded by the current-host
measurement above and is not the basis for the pilot limit.

The ER workflow is structurally parsed and its handoff verifier is tested,
but the hosted workflow has not run. Its Linux producer, identical-artifact
consumers, isolated legacy regressions and three-browser checks require a
published compatible immutable host commit. The 32-actor latency gate is
enforced; the 64-actor stress result is explicitly reported. Physical
Android/iOS, screen-reader review, deployment measurement and release/catalog
approval remain open.

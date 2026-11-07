# ER registration: 600-student validation

Date: 2026-11-07. ER **0.5.0**, state schema **3**, with the exactly identified
TeXStage **0.2.1.dev4** host below. The [machine-readable record](er-600-validation.json)
contains artifact hashes, full timing summaries, browser checks and independent
regression identities. Older 0.4.x records remain historical, not evidence for
these artifacts.

## What changed

The lesson now accepts 600 distinct answering actors and keeps replacements
available at capacity. Full answers live in bounded, transactional item records;
shared state contains counts, option totals and selection/share references.
Presenter pages contain 16 answers, up to 38 pages. The host commits record
writes, state, jobs and receipts atomically, resets their epoch together and
provides only bounded requested records to the trusted provider hooks.

Phones receive their own answer updates. Class counts remain on the presenter
and projector. The deterministic registration engine explicitly opts into
successful-result reuse for identical prepared inputs in the same item/round.
All 27 answer combinations are represented in the test. Each student retains a
separate durable job and guarded completion, including cache hits. New inputs
execute in fresh restricted workers. SQLite FULL durability, command/result/view
validation, worker isolation/CSP, two fresh jobs per poll, the 1,000-pending-job
limit, retries and the 120-second lease fallback remain unchanged.

The combined host preserves concurrent revision-3 actor-record support and
cooperative broadcasting. Existing providers remain uncached and use their
original broadcast behavior unless they explicitly opt into the new contracts.

## Measured capacity

600 Node protocol clients used the installed host's actual WebSocket client and
authenticated as separate students. A real presenter browser evaluated the
answers. Joining was sequential and completed before the timed bursts. The first
wave used cold evaluation, then all students replaced their answers. Timings run
from each send to that student's observed evaluated/saved state; correctness
feedback remained withheld until reveal. The unchanged warm gate is p95 ≤10 s
and last answer ≤30 s. Cold timing is reported separately.

| Presenter browser | Cold p95 | Replacement p95 | Last replacement | All recovered |
| --- | ---: | ---: | ---: | ---: |
| chromium 151.0.7922.34 | 10.19 s | 7.16 s | 7.24 s | 7.61 s |
| firefox 153.0 | 10.63 s | 7.46 s | 7.54 s | 8.51 s |
| webkit 26.5 | 10.97 s | 6.59 s | 6.68 s | 8.49 s |

All runs passed: 600 answers saved, no unavailable evaluations, private results
withheld, exact receipt replay, and refusal of a 601st distinct answering actor.
After reset, 600 fresh-epoch answers were queued while the real presenter was
closed. Two jobs were leased by a synthetic presenter that disconnected; the
real presenter resumed and all answers recovered, including requeued work.

Machine: Windows, Intel Core i9-11950H, 16 logical CPUs, approximately 63.2 GiB
RAM; Python 3.14.4, Node v24.15.0. Runs used loopback and ran
sequentially without concurrent test suites. These are not 600 rendered physical
phone browsers or measurements of classroom Wi-Fi. Repeat the gate on the actual
teaching host/LAN before relying on its latency in a lecture.

Each final database contained 600 answer records. For this no-rationale workload,
the largest record was 409 bytes and the aggregate state was 211 bytes. Separate
state tests exercise all 600 actors with 256-character IDs, unique heavily escaped
rationales, reserved feedback, replacements, all 38 pages and the 601st refusal.
They preserve the 2,560-byte actor-record allowance, 192 KiB aggregate-state cap,
224 KiB transition cap and 96 KiB role-view cap. These byte limits were not raised.

## Verification

| Test group | Passed | Skipped |
| --- | ---: | ---: |
| host | 197 | 1 |
| provider_and_handoff | 119 | 0 |
| pair | 4 | 0 |
| transaction | 67 | 0 |
| relational | 72 | 0 |

The host count combines its focused suite with the added cache-restart test,
deduplicating shared cases. It includes record atomicity, malformed/bounded
reads/writes, item/session/epoch isolation, cache identity and mutation isolation,
cancelled/stale ownership, bounded work batches, rollback and durable restart.
ER tests include all 27 engine combinations, portable Python/JavaScript schema
validation, source/wheel/sdist parity and real English/German LaTeX generation.
Existing example, transaction and relational providers were installed and tested
one group at a time in a disposable environment using the identical host wheel;
their exact-provider fixtures were unchanged.

Chromium, Firefox and WebKit passed the installed-worker confinement probes and
the real presenter/projector/phone workflow: two devices for one actor, distinct
learners, drafts, repair, explicit sharing, reset and navigation. English and
German keyboard/accessibility-tree checks passed at 320 px and doubled CSS text.
Native 200% Chrome page zoom passed in both languages. Representative English
phone and German presenter screenshots were visually reviewed. Physical-device
interaction and screen-reader speech output remain unverified.

## Exact artifacts and deployment

| Artifact | SHA-256 |
| --- | --- |
| ER wheel | `2f2844bcdc2c4e80feef3e6e8cad3ed610d4058573ab66944b033987adc8e16d` |
| ER sdist | `c1d5f4dbadd07f2437902c31554d78f63fec00a4cedbe1973d885b729b7ec69e` |
| TeXStage host wheel | `ba6c78c6e0b0d70c6e982d61ec9c08f1f4cdfe57d0b9fa416d42319f79034f41` |
| Installed host payload | `ad4136bef0e7e2c29494a8f72573b9463ecc8b3035666ad8e5874ff353078b39` |

Provider payload: `37c35929aa258dbdf05353778cd857a496f7c01773e5c50b1a443dbc17ef3437`.
Host base commit: `34d0c537135f32b0690147dbb66dd8ff155987f8` plus uncommitted
changes; that commit or the development version alone does not reproduce this
host. A [manually dispatched CI workflow](../../.github/workflows/er-conformance.yml)
now requires the 600-actor gate in all three browsers and an immutable compatible
host commit. It has not run on GitHub for this change. Linux execution of these
new artifacts and catalog/package publication are also pending.

Build/install the matching host and provider wheels in a fresh environment,
enable the exact provider payload, rebuild the lesson and start a new session.
Earlier pinned sessions stay in their original environment. See the
[release checklist](../er-decisions-release.md) for commands and deployment checks.
The original lecture-tools repository, existing courses and private media were
not changed. This work is not committed or pushed.

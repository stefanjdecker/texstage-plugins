# B+ tree engine: B0/B1 validation

Local validation: 2026-11-06. The engine is implemented; the classroom lesson
is not. See the [machine-readable record](bplus-tree-b1-validation.json),
[contract](bplus-tree-contract.md) and [next milestones](bplus-tree-plan.md).

## Tested artifacts

| Artifact | Identity |
| --- | --- |
| Host source baseline | `de3351550f3553ca63023554521fbe84806ec94e` |
| Host wheel SHA-256 | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| B+ wheel | `texstage_bplus_lab-0.1.0-py3-none-any.whl` |
| B+ wheel SHA-256 | `9d5a20462866c7f8fb9473330074345bcf107cfbe63e32257d7896a3c4173ad5` |
| B+ provider payload | `f6d91fe6d4e6c3e1f1c899ea0ab07c58e11719ec56dd345c08466e6653b8a73b` |
| Host result-schema digest | `7e5ae204c3226b03ed4ca1250b5f1aa5d63b808256ec14f13b16e826a5fdd6c2` |

The host wheel's 119 runtime text/style files match the active checkout with
line endings normalised. This plugin required no host-code change.
The host is a local development baseline, not a verified published release pin.

The SDK-built wheel is portable `py3-none-any`; rebuilding its sdist produces
the same provider manifest/resource payload. All four owned schemas pass the
host's portable-profile validation. Schema generation and self-contained worker
bundle freshness checks pass. Tests import the installed wheel, not its source.

## Mathematical and boundary checks

The final installed engine suite passed **30 tests**, with no failures or skips,
using Python 3.14.4 and Node 24.15.0 on Windows. The suite includes:

- All 30 hand-specified lookup/range/update examples, including exact final
  snapshots for splits, both borrow directions, internal repair, separator-only
  changes, root contraction and a three-level cascade.
- 1,800 operation cases from every insertion permutation of five keys and every
  deletion permutation from the two resulting shapes.
- 1,440 seeded operations across all 16 leaf/internal-capacity combinations.
- Exhaustively enumerated legal choices at selected boundaries: both split
  partitions, either donor/merge neighbour, and a valid borrow-versus-merge
  choice that produces different final heights.
- Incorrect paths/scans, missing/extra repairs, wrong pending page, wrong copied
  separator, underflowing donor, nonadjacent/cross-parent sibling and illegal
  merge. Incomplete/invalid facts omit fictitious final-tree/operation metrics.
- Legal replays with incorrect final separators, coverage/order or height;
  malformed/duplicate-key JSON, bool/int and decimal/exponent distinctions;
  invalid source graphs/leaf links/occupancy; result corruption and wrong binding.
- Fresh submission lifecycle, immutable sources, deterministic identity without
  WebCrypto, explicit work refusal and parser/result byte bounds.

The Python model uses nested pages; JavaScript uses a flat page map. Generated
certificates use the Python model to prune candidates, so that generator alone
is not an independent oracle. Expected key sets and the pre-existing snapshot
validator additionally check every generated stable tree, and the 30
hand-specified fixtures independently constrain exact structures.

A large valid case starts with 40 entries, performs three splits and ends
with 41 entries, 29 pages and height three. Typed facts measure 2,162 canonical
ASCII bytes; the complete host outcome measures 2,375 bytes. An inclusive full
range on that starting tree also passes. These are measured valid examples,
alongside the design's conservative shape encodings; they are not classroom
capacity measurements.

## Actual host worker in three browsers

| Browser | Version | Samples | Result |
| --- | --- | ---: | --- |
| Chromium through local Chrome | 156.0.8078.80 | 34 | Passed |
| Firefox | 153.0 | 34 | Passed |
| WebKit | 26.5 | 34 | Passed |

Each run uses the installed host evaluator, contract module and provider assets.
The 30 worked exercises are followed by malformed input, oversized input,
invalid seed and a successful fresh evaluation. The worker policy remains:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

The shared security harness first proves its unrestricted control can perform
each action, then verifies that all ten forbidden connection/worker/dynamic-code
probes are blocked under the production policy, with no forbidden requests.
Invalid typed results are rejected; a non-cooperative synthetic engine is
terminated at the host's existing two-second evaluation deadline, and the real
B+ engine succeeds afterwards. No workers remain.

Firefox initially failed while creating its first page inside the process
sandbox, before a plugin module loaded. The unchanged test passed when retried
outside that process sandbox. No browser policy or engine workaround was added.

This is engine/worker evidence. There is no B+ phone interface yet, and no
physical-phone, presenter overlay or projector-recording claim.

## Coexistence and existing behaviour

A separate environment keeps exactly the original coordinate/distance pair;
all **four** existing conformance tests pass, including build/static outputs,
style integrity and authenticated phone/evaluator/projector transport.
Its exact-provider assertion remains intact. The run emitted the existing
Starlette/httpx deprecation warning; dependencies were not changed to suppress it.

A second disposable environment contains nine independently installed providers:
coordinates, distance, transaction, relational, functional dependencies,
query plans, normalization, ER decisions and B+ trees. Metadata-only discovery,
resource integrity and the enabled catalog pass without capability/style
collisions; no factory is imported by discovery. The B+ probe's 30 examples
also pass there. This uses the local source snapshot of the other providers,
including concurrent uncommitted work, and does not replace their domain tests.

## Reproduction and remaining work

Use the build, installed-test and three-browser commands in the
[engine README](../../plugins/bplus-lab/README.md). The original
`maintenance/check_bplus_design.py` remains a small snapshot checker; its
historical JSON flags correctly do not claim runtime conformance.

CI now has isolated B+ engine/packaging, browser-matrix and Windows-consumer
jobs. Hosted execution and transfer of identical wheels between Linux and
Windows were not run in this local check. The compatible host commit must be
published/pinned before those jobs establish release evidence.

Next are prepared LaTeX exercise/solution diagrams and a synthetic deck,
then lesson state/privacy, structured phone/presenter controls, real-device
checks and measured classroom workload. The proposed 48-actor/state budgets
remain unmeasured. No package release, catalog entry or course migration
is part of this milestone.

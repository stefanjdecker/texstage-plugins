# Normalization Workshop: N1/N2 validation

Local Windows evidence, 2026-11-06. The [machine-readable record](normalization-workshop-n2-validation.json)
contains exact artifact hashes, schema byte measurements and browser/security
results. This delivers an analyzer and frozen contracts, not a classroom lesson.

## Delivered

- One portable `texstage-normalization-workshop==0.1.0` wheel and matching sdist,
  using the current host SDK. Sdist rebuild has identical provider payload.
- Manifest revision 2 / engine API 1, engine
  `io.github.stefanjdecker.normalizationworkshop.analyze`.
- Twelve schemas: author envelope, compiled seed, two answer variants, typed
  facts, reserved lesson state, commands and four role views.
- JavaScript analyzer and generated self-contained worker; independent Python
  model and bounded result verifier; named-source compiler/worked-answer checker.
- Package guide, reproducible schema/worker checks, installed-wheel tests and
  actual-host worker probes. No normalization content capability is advertised.

The package and instructions are in [plugins/normalization-workshop](../../plugins/normalization-workshop/README.md).
The [contract](normalization-workshop-contract.md) documents the frozen format,
and the [plan](normalization-workshop-plan.md) identifies N3 as the next step.

## Exact environment

Host commit `de3351550f3553ca63023554521fbe84806ec94e`, unchanged by this work.
Host wheel SHA-256:
`d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`.

Provider payload:
`b42b55309c59fa41ce2d603c8edae723280d7b1197c04afaa1d3e9b6c5653761`.

Wheel SHA-256:
`25234126a5175a22e8aa2dc40c0e85e40c16258d97c625360c98c7d98cbb1347`.

Sdist SHA-256:
`54c2acff94543bb76616cf2e99015502840e2a489602861eb5b1831d17861b3f`.

Result-schema digest:
`c3e255f57f5104bdbd61cf5de0276a0a99cdc62ccfd3716e099625088cddbffd`.

Python 3.14.4, Node 24.15.0, Playwright 1.62.1, esbuild 0.28.2.
Python build/test dependencies came from the host's hash-locked requirement files.
The matching locked maintainer Node installation was reused. Tests imported the
installed wheel from a fresh disposable environment, not provider source.

## Domain and contract checks

**31 tests passed; no failures or skips.** Within those tests:

- 17 hand-derived cases and two checked named worked lessons.
- Every subset of the 12 nontrivial singleton FDs over three attributes:
  4,096 classifications plus 49,152 covered binary decomposition analyses,
  totaling **53,248 Python/JavaScript differential analyses**.
- Binary chase results independently compared with the intersection-closure
  criterion. Losing tableaux verified as legal relations with a missing tuple
  in the join. Multiway fixtures include lossless and lossy outcomes.
- Python closures use intersections of closed sets; JavaScript uses forward
  chaining. Python preservation enumerates projected FDs; JavaScript iterates
  projected closures. Chase implementations use union/find versus direct
  replacement. Evidence/identities are compared, not just success flags.
- 120 deterministic larger cases, 4–8 attributes and up to 32 FDs, including
  coverage failures and varied component sets. Independent verification took at
  most 9.14 ms in this run, below the host hook's 250-ms limit; maximum measured
  Python work was 67,114 of the 1,000,000 budget.
- Alternative valid decompositions, empty/multiple/differently sized keys,
  constants, cycles, no FDs, projected implications, equivalent FDs and attribute
  permutation. Closure extensivity, monotonicity and idempotence checked.
- Malformed JSON, duplicate/NFC-colliding keys, floating/exponent values,
  booleans as masks, invalid IDs/bits, wrong mode, duplicate relations,
  oversized/deep input, bad seeds/options and exhausted work budget rejected.
- Both host result validators exercised. Corrupted identities, keys, flags,
  witness facts and chase evidence are rejected by the independent verifier.
  Fresh-state reuse/disposal and namespace rejection are checked.

Schema-shaped worst cases include astral Unicode escaping, all 70 key slots,
eight components and 56 merge slots. Measured sizes:

| Envelope | Canonical ASCII bytes | Limit |
| --- | ---: | ---: |
| Typed data | 3,391 | 8,192 |
| Complete outcome | 3,669 | 12,288 |
| Reserved 64-actor state | 118,209 | 229,376 provider target |
| Replacement transition | 118,991 | 262,144 |
| Largest reserved role view | 54,662 | 131,072 |

These are structural upper-bound samples, not real 64-participant throughput or
implemented lesson transitions. State uses hashed actor handles, preventing raw
Unicode actor identifiers from consuming the slot budget. Disclosure/phase
invariants still need runtime implementation and tests in N3.

## Browser and coexistence checks

The final wheel passed the installed host's actual evaluator/worker path in:

| Browser | Version | Result |
| --- | --- | --- |
| Chrome (Chromium channel) | 156.0.8078.80 | Passed |
| Firefox | 153.0 | Passed |
| WebKit | 26.5 | Passed |

Each run checks both task modes, eight normal/error/recovery samples, result
agreement with Python, cleanup and deterministic recovery. It uses the unchanged
policy:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Active security probes verify blocked same/cross-origin fetch, XHR, WebSocket,
EventSource, child/blob workers, external module loading, eval and Function.
Unrestricted control probes establish that the attempts actually work without
the policy. Invalid-result rejection, deadline termination, worker cleanup and
recovery also pass. Ordinary HTTP identity hashing does not require SubtleCrypto.

The default Chromium headless download was absent; Chrome was explicitly
selected as the supported Chromium channel. Firefox ran with scoped permission
to launch its disposable test process. Neither adjustment changed host CSP.

A separate installation scenario verifies discovery of all five providers:
coordinate, distance, transaction, relational and normalization. Disabled
discovery does not import provider factories; capabilities are unique and all
inventoried resource bytes verify. Existing transaction/relational generated
workers remain byte-for-byte unchanged. Their domain suites were not rerun
because no implementation changes were made to them.

## Remaining work and limits

N3 must implement prepared LaTeX authoring, durable classroom state, authorized
commands and role-filtered projections. N4 adds accessible phone/presenter
controls. No generated PDFs, UI screenshots or physical-phone evidence are
claimed for this engine milestone. Queue fairness, class-size throughput,
cross-platform artifact transfer and hosted CI remain unmeasured here.

Artifacts are local development results, not a published catalog release.
Original repositories, courses, environments and private media were not changed.

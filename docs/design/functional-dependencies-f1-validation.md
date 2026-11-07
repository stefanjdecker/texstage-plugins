# FD engine F1: local validation

Implemented and checked on 2026-11-06. This is an engine milestone, not a
finished classroom activity. See the [package guide](../../plugins/fd-lab/README.md),
[contract](functional-dependencies-contract.md), [plan](functional-dependencies-plan.md)
and [machine-readable evidence](functional-dependencies-f1-validation.json).

## Exact artifacts

| Artifact | SHA-256 |
| --- | --- |
| `texstage-0.2.1.dev3-py3-none-any.whl` | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| `texstage_fd_lab-0.1.0-py3-none-any.whl` | `391bfea19c27da18ada4da04da9ab7ee711c8920c1bb9212edb4b72685c36735` |
| `texstage_fd_lab-0.1.0.tar.gz` | `7e0f451a5247db137cd28d1cbeb7a5ba80d7d842603f813a7b86f39f25655680` |

Provider payload: `1a45adefd8163af466666a792bc3a25078139ae07d1b68e99d25cbc62d9827c2`.
Result schema: `26c603131bdfe4d0aebcfa99e9742a80637291114f6f8eb270d370e2b0596f0a`.

The host runtime files were compared byte-for-byte with the recorded wheel.
Its source is local commit `de33515`; the development version alone is not
a release pin. The FD wheel and sdist produce identical provider manifests
and resource hashes. Generated workers match the pinned esbuild output;
the existing transaction and relational worker bytes are unchanged.

## Evidence

- 39 installed-wheel tests passed, with no skips.
- Nine named lessons and 21 hand-derived correct/incorrect answers agree
  between the independent set-based Python model and bit-mask JavaScript engine.
- All 4,096 three-attribute singleton-FD theories passed, including 32,768
  closure comparisons against an independent closed-set-intersection model.
- Composite dependencies, empty/trivial/cyclic constraints, differently sized
  keys, alternative derivations, target-prefix proofs and two-row witnesses pass.
  Additional checks cover 32 eight-attribute theories and 100 witness cases.
- Strict syntax, duplicate IDs, final-newline identifiers, float/exponent tokens,
  oversized input, wrong modes, unknown references, malformed results, namespace
  binding, work limits and fresh-state/disposal behavior are exercised.
- Both real host validators accept the actual bound results and reject the
  tested malformed facts. Large 256-set submissions fit the nested output budgets.

| Browser | Version | Evaluator samples | Result |
| --- | --- | --- | --- |
| chromium | 156.0.8078.80 | 34 | Passed |
| firefox | 153.0 | 34 | Passed |
| webkit | 26.5 | 34 | Passed |

Each browser used the installed host evaluator and installed provider at a
temporary loopback server. The worker policy stayed exactly:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Ten active restrictions were checked against an unrestricted control, covering
network access, child workers, external imports and code generation. Restricted
probes reached no forbidden endpoints. Invalid results were rejected, an
infinite loop was terminated by the host, workers were cleaned up and a fresh
real-engine evaluation recovered. This is engine integration, not phone UI testing.

## Reproduce and remaining work

Follow the isolated build/test/probe commands in the package guide. The
environment used Python 3.14.4, Node 24.15.0, Playwright 1.62.1 and esbuild 0.28.2.
Dependencies were copied into a fresh test environment from the earlier isolated
host test environment and their versions checked against the host development lock.

CI now has an FD-only Linux producer, a three-browser matrix and a Windows
consumer of the same built wheels. These jobs have not been run on the hosted
service. Linux and cross-OS results, a published compatible host pin and the
new combined-provider scenario remain unverified. No host code was changed.

F2 is the complete closure lesson: prepared LaTeX/static material, state,
role projections and participant/presenter controls. Other lesson modes,
physical phones and classroom-load measurements follow. No course files,
original tools, installed course environments or private media were changed.

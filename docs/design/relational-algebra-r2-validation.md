# Relational Algebra Lab: R0/R2 validation

This historical record retains the original artifact hashes and browser failures.
The subsequent [worker compatibility fix](worker-browser-compatibility.md) records
passing Firefox/WebKit results for new host and plugin wheels under the same CSP.

Local Windows validation, 2026-11-06. This is an implemented engine slice,
not a released classroom activity. The [machine-readable record](relational-algebra-r2-validation.json)
contains artifact/source hashes, exact host identity and browser diagnostics.

## What is implemented

- Versioned exercise, answer and portable result schemas, with semantic validators.
- An independent Python model and browser engine for all eight operator forms.
- Checked certificates for the four rewrite-rule families.
- Deterministic Unicode-aware relation/answer/exercise identities without WebCrypto.
- Work/row/input/output limits, fresh-state lifecycle and typed facts.
- Portable wheel/sdist, installed-artifact probes and independent CI jobs.

See the [contract](relational-algebra-contract.md),
[package instructions](../../plugins/relational-lab/README.md) and
[remaining plan](relational-algebra-plan.md).

## Evidence

| Check | Result |
| --- | --- |
| Installed relational tests | **48 passed** |
| Original coordinate/distance pair, exact two-provider installation | **4 passed** |
| Selected tiny-domain algebra and rewrite cases | **272 checked**, in addition to hand examples |
| Hand construction/operator examples | 14 checked; library query cross-checked with SQLite on four instances |
| Worked rewrite | Five steps checked, including intermediate states and a refused invalid push |
| Source-distribution rebuild | Identical provider manifest/resource payload |
| Host result boundary | Actual installed JavaScript and Python validators; real binding namespace |
| Hashing | Independent SHA-256 vectors with WebCrypto unavailable |
| Coexistence | Four providers discovered/resources verified; both engine probes passed |
| Near-limit transport | Unicode derived tree plus maximum fixture/trace dimensions fit below 4/5 KiB |
| Hosted CI / Linux / cross-OS transfer | Configured, **not run** |

The tiny-domain cases enumerate subsets of fixed small domains. They are useful
regression evidence, not a proof of the implementation for arbitrary programs.
The resource tests distinguish refusal from mathematical invalidity and check
that the work budget spans all fixtures. Schemas do not independently prove
the truth of supplied domain facts.

## Actual host evaluator

| Browser | Observed result |
| --- | --- |
| Chrome 156.0.8078.80 (Chromium) | **8 samples passed**, including malformed input, refusal, bad seed, repeat evaluation and worker cleanup |
| Firefox 153.0 | Failed before the engine module loaded; sample 0 timed out |
| WebKit 26.5 | Failed before the engine module loaded; reported worker-policy rejection of `/static/stage/plugin-contracts.js` |

Chrome's maximum observed sample time was 35.2 ms
with the actual 2,000-ms host deadline. This is a small local engine check,
not a phone-response or 64-participant latency measurement.

The harness uses the installed host's evaluator modules and verifies that the
served worker policy matches the current host source. The Firefox/WebKit failures
reproduce the shared startup boundary previously seen by the transaction engine;
WebKit explicitly identifies `worker-src`. No relaxed policy is counted as a pass,
and no host code was changed. These remain real release gates.

## Exact artifacts and scope

Wheel: `texstage_relational_lab-0.1.0-py3-none-any.whl`

SHA-256: `b66ce2495193f95c4c9c1c17082cf8c114ba32164d5ba04de80fab43f300960d`

Provider payload: `30b1d4d9c83ec213943270f8833624a938e32087273b83919180a5f4ec154b0f`

Host wheel: `texstage-0.2.1.dev3-py3-none-any.whl` with SHA-256
`ee86bcb875bd6cc042fd01991c25dbe335e2aba40c3dc1ccc1173281d2d91437`. The active host has local H1/H2 changes;
its development version alone does not identify the compatible API.
145 packaged files matched corresponding active host source files.
The JSON record identifies source HEAD, wheel and full installed payload.

Run the commands in the package README to reproduce these checks in an isolated
environment. CI adds separate package, browser-matrix and Windows artifact-consumer
jobs without changing the original pair's exact-provider tests. No hosted CI pass
is claimed while a compatible published host pin remains pending.

Authoring, style, static editions, classroom reducer/graded feedback, audience
projections, responsive phone preview/editor and capacity measurements remain
R3–R6 work. There is no catalog release, course migration, commit or push in
this milestone.

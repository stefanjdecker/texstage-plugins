# Transaction engine M2: local validation

Recorded on 2026-11-06. The independent engine is implemented; the transaction
lesson package and its interfaces are still pending. This is local engineering
evidence, not a classroom or release approval.

The [machine-readable record](transaction-engine-m2-validation.json) contains
exact wheel, provider, schema and host hashes, environment versions and results.
The installed host wheel contains the unpublished H1/H2 work from the active
Texstage checkout. All 145 corresponding host package source files matched that
checkout byte for byte. Its shared development version alone does not identify
the required contracts.

## Passing checks

- 67 installed-engine tests. Nine hand-written cases and all 1,742 legal
  interleavings of six small exercise programs agree with the independent
  Python oracle. Compact traces replay to the same complete states.
- Multiple valid repairs, direct edge witnesses, isolated vertices,
  read/read and write/write cases, and equal final values with a cyclic graph.
- Malformed seeds and answers, duplicate JSON keys, invalid permutations,
  bounded input/output, maximum-size exercises, fresh states and deadlines.
- Semantic SHA-256 identity with browser cryptography unavailable, compared
  against Python's implementation, and actual JavaScript/Python host contracts.
- Portable wheel packaging and matching resource inventories after rebuilding
  from its source distribution.
- All four original coordinate/distance tests pass in their unchanged
  exact-two-provider installation scenario, including live phone/evaluator
  transport and static exports.
- Chromium (Microsoft Edge 156.0.4314.58) passes eight cases through the actual
  installed host evaluator with its unchanged CSP and two-second evaluation
  deadline. Every worker is cleaned up after evaluation.

## Open compatibility gate

Firefox 153.0 and WebKit 26.5 fail before the transaction engine module loads.
The current host sends `worker-src 'none'` on the evaluator worker. WebKit
explicitly reports that it blocks the worker's import of
`/static/stage/plugin-contracts.js`; Firefox also fails to initialize.

A disposable Firefox diagnostic allowing same-origin worker sources confirmed
the cause, but **the host policy has not been relaxed or changed**. That
diagnostic is not counted as a passing browser gate. A core fix must preserve
the intended network/worker restrictions and gain cross-browser regression
coverage before classroom use.

The new CI browser matrix retains this failing check, with separate jobs so it
cannot mask the engine tests or prevent Linux-to-Windows wheel handoff testing.
No hosted CI run is claimed. Publishing and pinning a compatible host remains
an M0 prerequisite.

## Reproduce and continue

Follow the [engine README](../../plugins/transaction-engine/README.md) to build
the wheel, run installed-package tests and generate JSON/browser probe reports.
Use the host's locked development requirements and a fresh virtual environment.
Keep the engine-only and coordinate/distance environments separate.

The next work is the shared host compatibility fix and M3 lesson authoring/state:
one exercise source, static exports, classroom phases, actor-local answers and
durable evaluation correlations. Phone, presenter and projector interfaces
follow in M4. Participant capacity and physical-phone rehearsal are still
unmeasured; the engine checks do not establish them.

No existing course, tool pin, original lecture-tools checkout, archived Texstage
checkout or private media is changed by M2. No wheel has been published and the
public catalog remains empty.

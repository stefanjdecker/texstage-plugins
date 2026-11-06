# Transaction schedule engine

This experimental Texstage plugin computes what a small transaction schedule
does and whether it is **conflict serializable**. It evaluates a student's
proposed order against fixed transaction programs: remembered read values,
final database values, direct conflict edges with operation witnesses, and
either a cycle or a compatible serial transaction order.

This is milestone M2, the independent analysis engine. It is usable through the
probe below. The transaction lesson plugin, LaTeX command, staged feedback and
presenter/phone interfaces are subsequent milestones; this wheel does not
provide those interfaces.

## Build and try it

Use a new Python 3.12+ environment with Node.js 24 and an **installed wheel of
the matching Texstage H1/H2 host**. Install the host's locked development
dependencies first. The host must implement manifest revision 2 and typed
engine result contracts. A version such as 0.2.1.dev3 alone does not identify
those unpublished changes; record the exact host wheel hash.

From the collection root:

```console
python maintenance/build_wheels.py --package transaction-engine
python -m pip install --no-deps dist/texstage_transaction_engine-0.1.0-py3-none-any.whl
python -m pytest plugins/transaction-engine/tests -q
python maintenance/transaction_engine_probe.py --output artifacts/transaction-engine
```

The probe writes JSON for a lost update, two valid repairs and an invalid
program order, plus installed artifact fingerprints. It uses Node and both
the installed host's JavaScript and Python contracts. No course, running
lecture, or persistent plugin profile is changed.

The wheel is portable Python packaging; its computation is browser JavaScript
with no native binary, network, database server or WebCrypto requirement.
Wheel and source-distribution rebuild payloads must match.

Installation does not enable a plugin. For a future lesson using this engine,
explicitly enable and pin provider
`io.github.stefanjdecker.transactionengine` in that lecture's Texstage profile.
Its engine ID is `io.github.stefanjdecker.transactionengine.schedule`.
Do not publish a catalog entry until the compatible host and tested wheels
have been reviewed and released.

## Model and input

The packaged `fixtures/counter.exercise.json` is a complete example.
`schemas/exercise-v1.json` describes the seed. Semantic checks additionally
require unique transaction/operation IDs, known objects, references to an
earlier read in the same transaction, exactly one terminal commit per
transaction, and a legal original schedule.

- Two or three transactions, one to three integer objects.
- At most twelve reads/writes, plus one commit per transaction.
- A write stores either a constant or a remembered read plus an increment.
  It can write a different object from the one read.
- Initial values and constants are within ±1,000,000; increments within ±10,000.
- No abort, recovery, locks, SQL isolation levels or MVCC are simulated.

An evaluation receives only JSON containing the proposed operation order:

```json
{"order":["a1","a2","a3","b1","b2","b3"]}
```

Reordering must preserve each transaction's program. Missing, duplicate,
unknown or out-of-order operations produce an `ok` analysis with
`valid: false` and reason codes, without simulated or graph facts.
Malformed JSON, duplicate JSON keys and invalid input shapes yield
`syntax`; answers exceeding 2,000 characters yield `refused`.
A malformed or oversized seed fails initialization. Seeds are limited to
32 KiB UTF-8. Each evaluation requires a fresh loaded state.

## Results

`schemas/analysis-result.json` defines bounded typed facts. A valid analysis
contains the proposed order, vertices (including isolated transactions),
remembered reads, final values, an operation trace, direct edges with all
conflicting operation-pair witnesses, and a deterministic certificate.

Trace rows contain the operation ID and its read/written value; commits
contain only their ID. Starting from the seed's initial values, apply write
rows to database objects and read rows to the remembered-read map to recover
every complete state. This compact representation stays within Texstage's
8 KiB data budget, including the largest supported exercises.

The graph contains no inferred transitive edges and no read/read conflicts.
An acyclic graph has a serial order; a cyclic graph has a closed cycle.
The latter means **not conflict serializable**, not necessarily not
view serializable. Equal final values alone never establish serializability.
Different valid repairs can have different canonical results; the future
lesson must assess the facts rather than compare against a single answer key.

Canonical output includes a SHA-256 digest of the semantic seed and the
submitted order. Presentation language, wording, object-key order,
transaction-list order, actor IDs, clocks and evaluation IDs do not affect it.
Changing the original schedule or program does affect it. Provider payload
pins and host namespaces remain the authority for compatibility; this digest
does not replace them.

## Verification and limits

Tests run the **installed wheel**, compare it against the independent design
checker and hand-written expectations, and enumerate all 1,742 legal
interleavings of the six small exercise programs. They also check malformed
seeds/answers, bounds, fresh-state isolation, result budgets, identity and
certificates. Run these collection tests from a collection checkout.

The browser worker probe uses the installed host evaluator and its actual
result validator. It is an engine integration check, not a transaction UI,
physical-phone rehearsal or 200-participant capacity claim.

After running the Python probe, run the browser check from the collection root:

```console
npm ci
npx playwright install chromium firefox webkit
node maintenance/transaction_engine_browser.cjs
```

Select the other engines with `BROWSER=firefox` or `BROWSER=webkit` (PowerShell:
`$env:BROWSER='firefox'`). `TEXSTAGE_BROWSER_CHANNEL=msedge` or `chrome` selects
an installed Chromium browser. JSON reports include the actual browser version,
provider/schema identities, worker policy, deadlines and outcomes.

Known host compatibility gate: the current H1/H2 worker policy blocks module
imports in Firefox and WebKit before this engine starts. Chromium passes the
same check. The probe reports this as a failure; it does not relax the policy.
Resolve that host issue before a cross-browser classroom release.

License: [Apache-2.0](LICENSE).

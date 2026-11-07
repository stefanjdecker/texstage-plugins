# Query-plan engine: Q0/Q1 validation

Local Windows evidence, 2026-11-06. The
[frozen contract](query-plan-challenge-contract.md) covers the engine and future
lesson source. The [machine-readable record](query-plan-engine-validation.json)
contains artifact identities, measured bounds and browser/security results.

## What is implemented

The independent texstage-query-plan wheel provides the cost capability,
strict source/answer validation, deterministic typed facts, an independent Python
model and bounded reference enumeration. The future lesson envelope has a frozen
schema and a pure prepare_reference helper which checks baseline/goal/worked
answer. There is no authoring hook, lesson state, phone UI or LaTeX command yet.

No TeXStage core source was changed. No original tools, courses, course pins,
private media or installed course environments were modified. Other in-progress
plugin designs and the host's existing database-example changes were preserved.
No package or catalog release has been published.

## Exact artifacts

| Item | Identity |
| --- | --- |
| Provider | io.github.stefanjdecker.queryplan 0.1.0 |
| Provider payload | f77808bde14ac20c08769bd3b37b5f21cecf1d4a429b4472f6f19f3d110ea335 |
| Portable wheel | texstage_query_plan-0.1.0-py3-none-any.whl |
| Wheel SHA-256 | 742b950c8dd9e03d23df4941c117d8fc72f4fea27235f8148e43cad17dff5d53 |
| Host development commit | de3351550f3553ca63023554521fbe84806ec94e |
| Host wheel SHA-256 | d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6 |
| Collection base commit | 5f00b62f6292de01e4eca067c8acd96dddf67eb9 |

Source-distribution rebuild produces the same provider inventory/payload.
Final source/resource files use the repository's required LF line endings;
the JSON record also identifies the final source archive. The final wheel was
reinstalled and all engine/browser checks rerun. Tests import it in
an isolated environment, not the provider source directory. Metadata-only
discovery was checked in a clean interpreter without importing the factory.
Python 3.14.4 and Node v24.15.0 were used with the host's locked dependencies.

## Domain, contracts and bounds

**86 installed-wheel tests passed**, with no failures or skips, including the
enhanced exact-memory-boundary test in the final normalized-artifact run.

Coverage includes:

- 20 hand-derived examples and all 446 raw candidates across seven supplied
  exercises; Python and browser facts agree for valid and infeasible plans.
- A further 864-candidate maximum family, including wide identifiers, escaped
  Unicode literals, maximum statistics, exact safe-integer costs and denied hashes.
- Tied optima, empty scans/joins, zero-cost goals, memory equality/one byte over,
  monotonic memory feasibility, unreachable goals and invalid worked answers.
- Strict parsing, duplicate/escaped keys, floats/exponents/non-finite values,
  booleans as integers, array/string coercion, Unicode/NFC, malformed topology,
  missing/duplicate relations and inconsistent statistics.
- Source normalization and SHA-256 identities, including operation without
  crypto.subtle; fresh state and repeated disposal.
- Both installed host validators, actual binding namespaces, result-schema
  mutations and source/answer/lesson schema fixtures.
- An independent nested/hash row interpreter compared with a SQLite bag query
  for all 144 feasible library plans on each of four data variants. Duplicate
  names occur three or six times as appropriate; empty/filtered variants agree.
  This supports the restricted-construction argument; it is not general SQL
  equivalence testing.

| Measurement | Observed | Enforced budget |
| --- | --- | --- |
| Maximum-shaped engine seed | 4,764 ASCII bytes | 32,768 |
| Long-identifier candidate answer | 315 ASCII bytes | 1,024 |
| Actual maximum-family typed data | 851 ASCII bytes | 8,192 |
| Actual maximum-family complete outcome | 1,073 ASCII bytes | 12,288 |
| Result-schema maximum-width data witness | 2,318 ASCII bytes | 8,192 |
| Complete outcome carrying that witness | 2,533 ASCII bytes | 12,288 |
| Maximum-shaped lesson envelope | 53,474 ASCII bytes | 98,304 |

The schema witness deliberately permits non-hex Unicode identity strings and
repeated maximum node facts to exercise the portable schema's representation
bound. It is not a semantically possible engine trace; the full outcome figure
is a witness, not the maximum of every generic host summary form. A future lesson
must still verify identities and meaning. Typed-data and outcome caps are nested.

Reference enumeration over the maximum family took about 0.013 seconds locally;
five maximum-shaped lesson preparations took about 0.017–0.036 seconds. These are
local pure-model timings, not a host-hook deadline test or classroom capacity claim.
State/actor/view budgets remain unmeasured until the lesson exists.

## Real worker and security checks

| Browser | Version | Result |
| --- | --- | --- |
| Chrome | 156.0.8078.80 | Passed |
| Firefox | 153.0 | Passed |
| WebKit | 26.5 | Passed |

Each browser exercised eight samples through the installed host evaluator,
including valid costs, domain-invalid memory, malformed/oversized answers,
invalid seed, fresh-state recovery and zero remaining workers.

The installed worker policy remained:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Each unrestricted disposable control proved all ten probe operations worked.
Under the actual host worker, same/cross-origin fetch, XHR, WebSocket,
EventSource, child/blob workers, external imports, eval and Function were blocked,
with no forbidden fixture requests. Invalid typed results were rejected;
an infinite loop hit the host's two-second execution timeout; a fresh real
engine recovered. No restrictions were weakened.

Reported elapsed times include worker startup: the final maxima were about
28 ms (Chrome), 155 ms (Firefox) and 104 ms (WebKit). The host's separate
30-second startup allowance and two-second evaluation deadline are unchanged.
These local samples do not guarantee cold-start latency, physical-phone
usability or classroom capacity.

## Regression scope and reproduction

The original isolated distance/coordinates suite passed all four tests, using
its existing validated static bundle. The relational and transaction installed
engine probes each passed their four cases. Their generated worker bytes are
unchanged. Shared README/build-list merges preserved concurrent plugin work.
The pinned bundler's freshness check passed for Query-plan, FD, relational and
transaction workers; the Query-plan bundle was checked again after LF
normalization. Concurrently added normalization work was preserved; no other
provider files were changed.

From the collection root, in the isolated matching-host environment:

```sh
npm ci --ignore-scripts
npm run check:workers
python maintenance/build_wheels.py --package query-plan
python -m pip install --no-deps dist/texstage_query_plan-0.1.0-py3-none-any.whl
python -m pytest plugins/query-plan/tests -q
python maintenance/query_plan_probe.py --output artifacts/query-plan
node maintenance/query_plan_browser.cjs artifacts/query-plan
```

Select BROWSER=firefox or BROWSER=webkit and install the matching locked
Playwright browsers for those runs. On PowerShell use $env:BROWSER='firefox'.
TEXSTAGE_BROWSER_CHANNEL=chrome selects an installed Chrome only for Chromium
runs; clear it for the other engines. Reports/logs belong under artifacts/,
not public lecture assets.

Not claimed: hosted CI, Linux consumption of the identical wheel, a published
compatible host pin, prepared live/static exports, lesson state/role privacy,
phone interfaces, physical-phone checks or measured classroom load. Those
remain the [next implementation milestones](query-plan-challenge-plan.md).

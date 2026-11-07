# ER registration engine: validation record

Local validation, 2026-11-06. Scope: frozen registration engine only.
The [runtime contract](er-registration-engine-contract.md) is implemented;
the [complete ER activity plan](er-modelling-decisions-plan.md) is not complete.
The [machine-readable record](er-registration-engine-validation.json) contains
exact artifact identities, schema hashes, browser probes and remaining gates.

## Tested artifacts

- Host commit: `de3351550f3553ca63023554521fbe84806ec94e`.
- Host wheel SHA-256: `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`.
- Provider wheel: `texstage_er_decisions-0.1.0-py3-none-any.whl`.
- Provider wheel SHA-256: `452a21ef9aeb74b32bc85523ce23533027ca18fb3048993d1692cf742bf83e24`.
- Provider payload: `ce846ab75fdbff8375ce3c728e1dbf904f0d36ff33ac59c8be3ce3716d1d398f`.
- Portable wheel and source-distribution rebuild have identical provider payloads.
- Python 3.14.4; Node v24.15.0; locked esbuild/Playwright tools.

These identify local development artifacts, not a published compatible host or
catalog release. The final rebuild retained the identical wheel bytes used in
the browser checks. The final installed-wheel tests and probe used that wheel.

## Semantic and contract evidence

**56 tests passed; none failed or skipped.** Tests import the installed ER wheel
in an isolated environment containing exactly this provider. Disabled discovery
does not execute its factory. The package supplies no content-type capability.

- All 27 registration models agree with the independent design checker and
  Python oracle. Exactly two agree with the five intended snapshots.
- The two passing representations retain different canonical identities.
  Wrong cardinality, endpoint-owned status and missing pair uniqueness have
  hand-derived counterexamples.
- All 81 small status-assignment worlds (absent/confirmed/waitlisted over four
  person/workshop pairs) agree across 27 models: **2,187 model/snapshot checks**.
- Empty populations expose no false participation evidence. Positive boundary
  inputs cover 12 snapshots, 32 occurrences, four attributes, four slots and
  144 composed models. Malformed and oversized inputs fail explicitly.
- Four closed schemas pass the host portable profile. JavaScript results pass
  both the installed browser and Python host validators.
- Tests cover malformed JSON, duplicate keys, type coercions, unsupported
  assumptions, semantic references, contradictory worked answers, NFC/non-BMP
  data, generic renamed IDs, deterministic order, raw/escaped byte limits,
  invalid result branches, full binding namespaces and fresh-state lifecycle.

The original 37-case ER design checker still passes. Its room/mentoring cases
remain **design evidence**, not implemented runtime capabilities.

## Actual browser worker evidence

| Browser | Evaluator samples | Slowest sample on this machine | Security probes |
| --- | ---: | ---: | --- |
| chromium 151.0.7922.34 | 31 | 28.0 ms | Pass |
| firefox 153.0 | 31 | 152.0 ms | Pass |
| webkit 26.5 | 31 | 80.0 ms | Pass |

Each run exercised the installed host evaluator with 27 models plus malformed
answer, oversized answer, invalid seed and recovery. No worker remains after
each sample. Production policy is unchanged:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Active probes block same/cross-origin fetch, XHR, WebSocket, EventSource,
child/blob workers, external modules, eval and Function. An unrestricted
disposable control proves those probes can execute. Invalid results are
rejected, an infinite loop is terminated at the host deadline, and a subsequent
ER job succeeds. A timeout is not counted as a successful network block.
Initial Firefox/WebKit attempts found missing binaries; installing the pinned
test binaries resolved that environment prerequisite. All recorded runs pass.

These are desktop worker tests on Windows, not phone-interface, hosted-server
transport, accessibility or classroom-load measurements.

## Bounded payload evidence

The 27 teaching models produced at most 797 typed-data
bytes and 1037 complete-outcome bytes.
A synthetic maximum result-schema shape measured
2841 / 3081
bytes through both host validators. These are below the provider's 6/10 KiB
targets and host's 8/12 KiB ceilings. The synthetic shape tests transport size;
it is not falsely reported as a valid evaluation against the registration seed.
Oversized ASCII-escaped seeds are rejected even when their record counts fit.

No core limit was expanded. Authoring/view/state byte budgets, participant
capacity and throughput remain later lesson work. Existing transaction and
relational worker bundles are byte-identical after the bundler extension;
their runtime implementations and exact-provider tests were not changed.

## Reproduce

Use a fresh environment with the exact compatible host wheel and its locked
build/development requirements, then follow the
[package guide](../../plugins/er-decisions/README.md):

```console
npm ci --ignore-scripts
npm run check:workers
python maintenance/build_wheels.py --package er-decisions
python -m pip install --no-deps dist/texstage_er_decisions-0.1.0-py3-none-any.whl
python -m pytest plugins/er-decisions/tests -q
python maintenance/er_probe.py --output artifacts/er-decisions
node maintenance/er_browser.cjs artifacts/er-decisions
```

Set `BROWSER` to `firefox` or `webkit` for the other browser runs; install the
pinned binaries first. `ER_TEST_TMP` and pytest's `--basetemp` can select a
writable isolated temporary directory. Keep course environments unchanged.

Still pending: other ER profiles; prepared LaTeX/static material; lesson state
and privacy projections; phone/presenter UI; physical-device/accessibility/load
checks; cross-platform artifact transfer; hosted CI and release/catalog work.
No commit, push or publication is performed by this implementation task.

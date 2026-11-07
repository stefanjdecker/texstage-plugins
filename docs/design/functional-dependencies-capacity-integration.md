# Reconcile the parallel host storage work before release

During the final 2026-11-07 comparison, the shared TeXStage checkout acquired
additional uncommitted work based on `34d0c537135f32b0690147dbb66dd8ff155987f8`.
It reports version `0.2.1.dev5` and includes manifest revisions 3/4, typed actor
records, result caching and points. That work was not present in the capacity
branch's base and has not been changed or included in these measurements.

The isolated FD candidate works with host `a67229a353b5b7bd3e058618ae71dfef619b0f81`.
Its `ActorTransition` / `actor-slots-v1` extension overlaps the newer host's
`SaveActor` / `actor_records` API. Do not merge the two implementations blindly
or publish both as competing record APIs. Keep these branches as a tested
comparison until their storage contracts are reconciled.

## Recommended integration

Use the typed manifest-3 actor-record mechanism as the common API after its
owner has committed a stable revision. It validates both record values and
roster summaries and reads selected answers through a declared presenter field.
The FD domain reducer, aggregate counters and correctness tests can be retained.

| This candidate | Common actor-record API |
| --- | --- |
| Manifest-2 `state_model: actor-slots-v1` | Manifest-3 `actor_records` with value/summary schemas |
| `ActorTransition(state, slot, effects)` | `Transition(state, effects + [SaveActor(value, summary)])` |
| `ctx.actor_state` / `ctx.actor_count` | `ctx.records.value` / `ctx.records.count` |
| Presenter `ctx.actors` with full slots | `ctx.record_page.rows` with bounded summaries |
| Selection from the current full-value page | Presenter command `record_actor_field`, then the host-supplied selected value |
| 100 answers per page | Declared page size up to 25; update page schemas and navigation tests |

Pin the combined host revision and use a new FD payload/version. Rebuild bundles
and start fresh sessions; neither storage representation promises automatic
migration. Existing courses and their environments remain untouched.

Review the overlapping host files individually: plugin SDK, manifest schemas,
runtime commit/lease/result paths, server bridge/broadcasts, evaluator scheduling
and corresponding tests. Preserve the actor's authenticated identity, epoch and
receipt guards, schema/byte limits, atomic cancellation and reset behavior.
Retain the measured benefits of bounded sends, targeted notifications and avoiding
whole-queue scans where they fit the common implementation. Do not replace its
new points or record code with this branch's older whole-file versions.

The new host also has opt-in `result_cache: by-input`. FD analysis is deterministic,
so that may help repeated classroom answers, but review the complete cache key,
version/seed/options identity and permitted outcome policy first. Keep per-student
grading and receipts independent. Report repeated-input and varied-input bursts
separately: the current all-correct synthetic bursts must not become the sole
capacity evidence after enabling a result cache.

Repeat host and all-provider regression checks, exact installed-wheel and sdist
checks, restricted-worker probes, all FD modes/languages, 600-student replacements
and reconnects, and the separate 1,000-student headroom scenario. Keep the existing
latency targets. Publish the integrated host before updating/publishing the
collection CI pin. The present local branch has no hosted CI or production
capacity claim.

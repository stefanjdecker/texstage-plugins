# ER Modelling Decisions: target lesson contract

Status: target lesson contract, 2026-11-06. The registration engine subset is
now frozen and implemented in the [runtime contract](er-registration-engine-contract.md).
Its four owned schemas accept a narrower profile with three slot kinds and no
assumptions. The broader source/commands/views described below are not yet
accepted by an installed content provider. The original design JSON examples
remain trusted fixtures; the runtime package owns its versioned registration seed.
Provider 0.3.0 accepts a separate bounded `lesson-v1.json` authoring envelope
around that seed, described in the [authoring guide](../er-decisions-authoring.md).
The registration [E3 state contract](../er-decisions-state.md) now implements
phases, submissions and privacy projections. The broader multi-profile design
below remains a target; the phone/presenter UI is not implemented yet.

## Sources, models and choices

A production lesson envelope has `format`, `id`, `mode` (`decide`/`repair`),
localized `brief`, `requirements`, `model`, `decisions`, `assumptions`,
`public_examples`, `private_checks` and `worked_alternatives`.
Every requirement has an ID, visible prose, and `fixed` or `open` status.
Each check cites one or more visible requirement IDs. Interpretation choices
can specialize only open requirements. All records use stable ASCII IDs
(1–24 characters, letters/digits/underscore/hyphen); semantic validation also
checks uniqueness and references. Labels are not identities.

The model has flat entity and binary relationship arrays. Entity definitions
declare identity and scalar attributes; relationships declare two named roles,
endpoint entities, per-role minimum/maximum, and scalar attributes.
Identification is either a nonempty unique attribute set, owner plus local
discriminator, or a surrogate with separately declared business uniqueness.
The occurrence IDs used to name fixture records are bookkeeping, not an
implicit answer to an identification question.

The target lesson design has four typed slot kinds:

| Slot | Option payload | Compilation |
| --- | --- | --- |
| `role-bounds` | role ID, `min: 0/1`, `max: 1/"many"` | Participation and degree constraints |
| `attribute-owner` | attribute ID, entity/relationship target | Attribute location and functional dependency |
| `relationship-form` | relationship or association-entity; preserve-pair-unique flag | Pair identity, or occurrence identity plus declared uniqueness; required endpoint roles |
| `identification` | owner/discriminator, global attributes, or surrogate plus uniqueness | Key, owner existence and uniqueness constraints |

Slots own disjoint model properties. A compiler-defined expansion handles
association entities and ownership; it does not accept arbitrary patch paths,
expressions, executable predicates or external code. If two slot expansions
conflict, preparation must reject the author source rather than produce a
partly functional card. E0 must freeze the exact field schema and conversion
rules, including how attribute placement interacts with reification.

The compiler produces the diagram's semantic graph and three bounded kinds of
snapshot constraints: uniqueness, per-role degree and functional dependency.
It also enforces fixed referential integrity and required scalar values.
Graph rendering/layout is separate from semantic identity.

Snapshots use the exercise's fixed **observation vocabulary**, independent of
the selected diagram. For example, registration status is observed per
person/workshop occurrence even when a candidate proposes storing it on Person.
The typed compiler supplies that mapping; authors do not write arbitrary
mapping programs. Moving status to Person adds the dependency person -> status;
it does not make the original status observations disappear.

Snapshots explicitly list entity occurrences and link occurrences; empty sets
are permitted. Observed attributes have bounded scalar values: integer, boolean
or text, with no NULL or coercion. Text is NFC and case-sensitive. Required
observed values cannot be missing. Snapshots are complete in this vocabulary;
omitted records do not mean unknown observations. A candidate-only attribute
on an entity with no related observations can take any value in its nonempty
domain: it cannot create a contradiction without an observed value. This is
representability of the stated observations, not direct comparison of two
candidate table layouts.

**Validity layers:** malformed author structure, dangling references and bad
scalar types fail preparation. A negative teaching snapshot may deliberately
violate a business rule (for example pair uniqueness), but must remain a
well-formed observation. The source explicitly declares its forbidden status
and the relevant requirement; the compiler must not discard it as malformed.

At most one open requirement per exercise in v1, with two interpretations
and an unresolved state. For each interpretation, relevant witnesses have
explicit expected admission. Checks on fixed requirements always remain active.
Unresolved checks are reported as unresolved, not counted as passed.

## Answer and evaluation binding

The phone submits only option IDs, selected interpretation, optional plain
rationale (maximum 160 Unicode scalar values), and concurrency guards:

```json
{
  "answer_version": 2,
  "phase_version": 1,
  "choices": [
    ["person-links", "zero-many"],
    ["status-owner", "registration"],
    ["registration-form", "entity-pair-key"]
  ],
  "assumption": null,
  "rationale": "The status belongs to a particular registration."
}
```

Every required decision appears exactly once. Unknown, missing or duplicate
IDs, an interpretation for a closed requirement, and extra fields are refused
with a bounded code. Rationale is stored as discussion text and excluded from
the engine input. It is not HTML, TeX, or a claim of correctness.

The authoritative reducer sends a normalized answer to its fixed `analysis`
binding using `Evaluate` and `evaluation_correlation(actor, request, "model")`.
The binding holds the approved exercise model, fixed requirements, assumption
profiles and witness suite. No message may select another engine, seed, expected
answer or exercise. Public preview uses a separate public-only projection.

Canonicalization sorts choices and semantic IDs deterministically, ignores
layout/localized labels/rationale, and preserves different selected models
even if they pass identical finite checks. Proposed format is `er-decisions-v1`.
Bind results to the source/semantic format and answer digests; the host also
namespaces the **complete persisted binding**, provider payload, engine and
result schema. A deterministic portable digest implementation must work on
ordinary LAN HTTP without requiring WebCrypto.

## Typed engine facts

The engine returns `status: "ok"`, a deterministic `canonical`, a standard
`summary: {kind: "text", text: "..."}` and schema-validated `data`. The proposed
data shape is:

```json
{
  "format": 1,
  "exercise_digest": "<sha256>",
  "answer_digest": "<sha256>",
  "model_valid": true,
  "structural_issues": [],
  "checks": [
    {"id": "two-workshops", "expected": "allow", "admits": true},
    {"id": "duplicate-pair", "expected": "forbid", "admits": false}
  ],
  "unresolved": []
}
```

This is an abbreviated example, not an installed schema. A valid model returns
exactly the expected check IDs for its interpretation, once each, in stable
order. A failed admission can include one bounded reason code, constraint ID
and up to two occurrence IDs. Never duplicate entire snapshots in the result.
A structurally invalid model has issues and no fabricated snapshot findings.

The lesson verifies exact coverage, exercise/answer identities, selected
interpretation, actor, current answer version, correlation and epoch before
using facts. It derives contradiction/conditional/checked/discussion feedback.
A forged partial result must not become “all checks passed”.
Operational failure remains pending/retryable or failed, never “incorrect”.

Malformed engine input yields `syntax`; well-formed invalid combinations yield
`ok` with `model_valid: false`. Operational failures use only existing supported
failure statuses (`error`/`refused`/host `timeout`). No new host status is needed.

## State, messages and privacy

State stores phase, phase/control versions, bounded actor answer slots,
evaluation correlations/status and compact finding IDs. It stores no duplicate
diagram per participant. Instructor selection references actor + answer version;
sharing uses a separate explicit action and omits identity.

Messages: participant `submit`; presenter `open`, `close`, `reveal`,
`select-answer`, `share-answer`, `clear-share`. Use `revision_policy: "latest"`
with provider phase/control and actor guards. Host reset advances the epoch;
old leases/results cannot revive the earlier state. Closing still accepts
results for earlier saved answers. Revealing while results are pending shows
pending accurately; later current results can update released feedback.
Replacements cancel obsolete pending work with `CancelEvaluation` atomically.

| Projection | Permitted contents |
| --- | --- |
| Participant | Public task and own saved answer/status; own compact released feedback |
| Presenter controls | Counts, bounded paged answer summaries, one selected answer/rationale and diagnostics |
| Presenter overlay | Public task, selected model and presenter-only teaching guidance |
| Projector overlay | Public task/counts; explicitly shared anonymous model; approved reveal material |

Do not send private bindings/check classifications/answer keys to phones or
projector. Ordinary projector data excludes actor IDs, unshared answers and
rationales. Sharing rationale requires a separate presenter choice; it can
contain identifying text even when the model is anonymous.
On reveal release only marked teaching witnesses and worked alternatives.
Unreleased diagnostic fixtures remain private, including their identifiers
and constraint details. Keep view schemas closed for all four surfaces.

## Proposed bounded budgets

These are initial provider limits, not changes to host defaults. Enforce both
counts and serialized ASCII-JSON byte caps, including keys and escaping.

| Item | Initial cap |
| --- | --- |
| Decisions/options | 4 cards × 4 options; at most 256 composed models |
| Assumption profiles | 2 interpretations plus unresolved; at most 768 combinations |
| Compiled graph | 8 entities, 8 binary relationships, 24 scalar attributes |
| Witness suite | 12 snapshots, each at most 32 total entity/link occurrences |
| Source / prepared seed | 128 KiB / 64 KiB, separate from each view |
| Engine input | 1 KiB (normalized IDs, no rationale) |
| Engine facts / complete outcome | 6 KiB / 10 KiB, below host 8/12 KiB ceilings |
| Actor slot | 2,560 bytes including actor key, full answer, rationale and reserved feedback |
| Pilot responding actors | 64; new actors refused when full, existing actors may replace |
| Shared state / total state | 24 KiB / 192 KiB |
| Transition including effects | 224 KiB, below host 256 KiB; at most cancel + evaluate |
| Each role view | 96 KiB, below host 128 KiB; never all full answers |

64 × 2,560 + 24 KiB = 184 KiB, leaving 8 KiB of the state target for
container overhead. This arithmetic is a proposed allocation, not measured
capacity. E0/E3 must construct worst-case escaped payloads, include reserved
feedback/keys/effects and verify actual host limits before retaining these caps.
Preparation work is bounded by all combinations and snapshots; runtime
evaluates only the submitted model. Long author text must fail validation
clearly rather than overflow static slides or be silently truncated.

Schemas for results/views use the host's portable profile: bounded closed
objects/arrays, finite numbers and acyclic local references. Do not rely on
`pattern`, `propertyNames`, `$id` or remote references there. Semantic ID and
cross-reference checks belong in validators as well as source schemas.
Independent Python/JavaScript validators must agree before integration.

## Implemented registration capacity amendment (2026-11-07)

The broader target contract above is historical design, not the complete current
registration API. ER 0.6.0 implements the live phone/presenter workflow and
600-answer capacity with optional points and state schema 4. The original 64-actor design bound is
superseded for this registration version by separate bounded actor records,
constant-size counts/option totals and 16-answer presenter pages. See the
[current state contract](../er-decisions-state.md) and [validation](er-points-validation.md).
The prepared source and engine schemas remain unchanged; old pinned sessions
are not migrated. Other proposed profiles remain future work.

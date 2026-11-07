# ER registration engine: frozen v1 contract

Status: implemented registration-profile contract, 2026-11-06. This freezes the
engine subset of the [ER design](er-modelling-decisions.md). The broader
[lesson contract](er-modelling-decisions-contract.md) remains a target design.
No authoring hook, style, state reducer or phone/presenter renderer is supplied.
See the [validation record](er-registration-engine-validation.md).

## Identity and scope

| Component | Frozen identifier |
| --- | --- |
| Distribution / provider | `texstage-er-decisions` / `io.github.stefanjdecker.erdecisions` |
| Engine | `io.github.stefanjdecker.erdecisions.model` |
| Seed profile | `er-registration-v1` |
| Answer / facts format | Integer `1` |
| Canonical format | `er-decisions-v1` |
| Manifest / plugin API | Revision 2 / API 1 |

One portable wheel owns the Python oracle, browser modules, generated worker,
schemas and synthetic seed. Its manifest declares only the engine. An empty
factory is intentional: there are no content or authoring hooks yet.
No course or original lecture-tools installation is changed.

The profile is deliberately narrower than the eventual ER model:
exactly two distinct entity types and one binary relationship; endpoint
entities have fixed opaque occurrence identities. There is no selectable
entity-key/owner-identification slot, recursive role, open assumption, arbitrary
diagram or executable predicate. Unknown fields and unsupported profiles are
rejected. Extending those semantics requires a new explicit profile/version,
not silently interpreting existing v1 files differently.

The authoritative structural schemas are:

- [Exercise](../../plugins/er-decisions/texstage_er_decisions/schemas/exercise-v1.json):
  brief, fixed requirements, model, decision slots, snapshots and worked answers.
- [Model](../../plugins/er-decisions/texstage_er_decisions/schemas/model-v1.json):
  endpoint entity IDs and the binary relationship.
- [Answer](../../plugins/er-decisions/texstage_er_decisions/schemas/answer-v1.json):
  format and selected decision/option ID pairs only.
- [Analysis](../../plugins/er-decisions/texstage_er_decisions/schemas/analysis-v1.json):
  bounded typed facts, with distinct valid/invalid branches.

All four are closed, bounded JSON Schema 2020-12 in the host's portable
vocabulary. They additionally require the semantic checks below; accepting
structural JSON alone does not validate an exercise. The JavaScript seed
validator uses a non-executable interpreter of the owned frozen schemas.
The Python oracle uses `jsonschema`. Both are checked against malformed and
valid examples. The independent host validators validate results again.

## Model and typed composition

`model.entities` is the two entity IDs. `model.relationship` contains its ID,
two roles, one to four observed scalar attributes, representation `form` and
`pair_unique`. Each role declares ID, endpoint entity, `min` and `max`.
Each attribute declares ID, type and owner (`"relationship"` or a role ID).

The two roles have distinct IDs, point to different declared entity types and
cannot be named `relationship`, which is the attribute-owner sentinel.
Relationship ID differs from entity IDs. An ordinary relationship always has
`pair_unique: true`; disabling pair uniqueness requires `association-entity`.
For both forms, every link has exactly one existing occupant per role.

Each decision has ID, kind, target and two to four named options. The three
supported kinds have these exact payloads:

| Kind | Target | Option `value` |
| --- | --- | --- |
| `role-bounds` | Existing role ID | `{"min":0,"max":"many"}`; min 0/1, max 1/`"many"` |
| `attribute-owner` | Existing attribute ID | `"relationship"` or an existing role ID |
| `relationship-form` | Relationship ID | `{"form":"association-entity","pair_unique":true}` |

No two decisions own the same (kind, target). Duplicate option IDs or identical
option meanings within a card fail loading. All bounded combinations are
compiled and validated at load time.

The compiler applies selected bounds, owners and form to one normalized model.
These writes are disjoint. Reification changes the relationship's representation,
not its observation vocabulary: an attribute owned by `relationship` moves
onto the association entity; an endpoint-owned attribute remains there.
Pair uniqueness is the explicitly selected flag; a new occurrence identity
does not imply it.

The compiled model is the semantic input for a future diagram renderer. An
ordinary form maps to a relationship node; reified form maps to an association
entity with required links to both endpoints. There is no layout or SVG
implementation in this engine milestone.

## Observations and finite evidence

A snapshot has ID, public/private visibility, expected `allow`/`forbid`,
visible requirement IDs, two endpoint occurrence sets and link observations.
Every link has its own occurrence ID, exactly two role/occupant pairs and
exactly one typed value for every declared observed attribute.
The [registration seed](../../plugins/er-decisions/texstage_er_decisions/fixtures/registrations.json)
is a complete example. It retains the original five design situations.

Occurrence IDs must be unique within their entity set or link set, but may
repeat in different sets. They identify records for evaluation and witnesses;
they do not constitute a student choice of a business key. References must
resolve. Missing values, dangling occupants, repeated fields and wrong scalar
types are malformed sources. A duplicated person/workshop pair with distinct
link occurrence IDs is a **well-formed negative business example**, not
malformed JSON.

For each candidate, the engine checks:

1. **Pair uniqueness**, if selected, across both role occupants.
2. **Role bounds**, counting incident link occurrences for every entity,
   including entities with no links. `many` is unbounded within the finite
   snapshot; an empty entity set satisfies a lower bound vacuously.
3. **Attribute ownership.** Endpoint ownership requires all observations of
   that endpoint to agree on the scalar value. Relationship ownership permits
   one value per occurrence. An endpoint with no observations does not
   fabricate a missing-value conflict.

The result lists all snapshots once. `admits` says whether the candidate
represents that snapshot. It is independent of the author's `expected` label.
The lesson will compare these two values; the engine supplies no overall grade.
Finite agreement is not proof of general ER equivalence.

Each worked answer must compile and agree with every expected label. A source
with a contradictory worked answer is rejected before evaluation. This is a
consistency check, not proof that the author's business requirements are true
or that the witness suite is complete.

Witness selection is deterministic: check pair uniqueness, then roles by ID
and endpoint occurrences by ID, then attributes by ID. Within each check,
inspect link occurrences by ID. Report the first violated constraint only.
`role-minimum` identifies the unlinked entity; `role-maximum` identifies two
incident links; `pair-unique` and `attribute-dependency` identify two conflicting
links. Witness occurrence IDs are scoped by the reason's target/code.
If a model admits a forbidden snapshot, its reason is null: it violated no
constraint of that candidate, which is precisely the missing restriction.

## Parsing, canonicalization and result identity

Both implementations reject duplicate object keys, including keys that collide
after NFC normalization, unknown fields, fractional/exponent number tokens,
unsafe integers, non-finite values and lone surrogate code points. Strings are
NFC and case-sensitive. Scalar types are integer (±1,000,000), boolean or text
(0–64 Unicode scalar values); no implicit coercion or NULL.
Semantic IDs are 1–24 ASCII letters, digits, underscores or hyphens.

All semantic lists are normalized by ID; pair lists use their first then second
ID. Choices are ordered independently of submission order. Schema prose,
requirement wording, snapshot visibility and worked-answer ordering are not
part of the semantic exercise digest. Requirement IDs, the entire normalized
model/decisions and complete snapshots with expected admission are included.

Use ASCII-escaped JSON with sorted object keys, compact separators and finite
integer values, matching `model.canonical` and `web/identity.mjs`:

- Exercise digest: SHA-256 of `semantic_seed(exercise)`.
- Answer digest: SHA-256 of `["er-answer-v1", normalized_answer]`.
- Canonical result: `"er-decisions-v1:" + SHA-256(canonical(facts))`.

The portable owned SHA-256 implementation works on ordinary LAN HTTP without
WebCrypto. Hash vectors include non-BMP text. It provides identity, not
authentication. Distinct acceptable models retain distinct canonical results.
Host equality uses its result key **and namespace**; the namespace binds the
full persisted engine binding, including engine ID, provider payload and
contract/schema. Rewording a seed can retain the semantic result key while
changing the host namespace.

An answer has integer `format:1` and one pair for every decision, with no
rationale, phase token or assumption fields. Those belong to future lesson
commands. Known-shaped answers with unknown, missing or duplicate decision IDs
or unknown option IDs return `status:"ok"` with `model_valid:false`, one bounded
structural issue and no snapshot claims. Malformed answers return `syntax`;
size excess returns `refused`. Invalid seeds fail load; the host reports the
operational error. A wrong but well-formed model remains a successful analysis.

Successful valid facts have format, exercise/answer digests, `model_valid:true`,
no structural issues, all checks and `unresolved:[]`. The invalid branch
requires one issue and zero checks. Schemas enforce branch consistency;
exact exercise/check coverage is a semantic responsibility of a future reducer,
not something the generic host can infer from the result schema.

## Limits and lifecycle

| Boundary | Frozen registration-profile limit |
| --- | --- |
| Entities / relationships / observed attributes | 2 / 1 / 1–4 |
| Decisions / options / combinations | 1–4 / 2–4 per card / at most 256 |
| Fixed requirements / worked answers | 1–8 / 1–4 |
| Snapshots / occurrences | 1–12 / at most 32 total entity and link occurrences each |
| Seed bytes | 64 KiB, both raw UTF-8 and normalized ASCII JSON |
| Answer bytes | 1 KiB raw UTF-8 and normalized ASCII JSON |
| JSON nesting / values visited | At most 16 / 8,192 |
| Typed facts / complete result target | 6 KiB / 10 KiB; host ceilings remain 8/12 KiB |

Counts and byte limits apply together. Each source needs at least one public
example. No payload is silently truncated. Loading enumerates only the bounded
option combinations; evaluation checks only the submitted candidate against
the bounded snapshots.

Engine functions are `start`, `load`, `evaluate` and `dispose`. Load options must
be an empty object. Every submission requires a newly loaded state; reuse and
evaluation after disposal fail. Invalid input consumes that state too.
Disposal is idempotent. The host owns worker deadlines, cleanup and subsequent
job recovery.

The generated worker is self-contained and retains the production CSP:
`default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'`.
Modular sources and schemas remain owned, inventoried resources; installation
does not invoke a bundler or fetch code. No host policy or core schema was
changed to accommodate the ER engine.

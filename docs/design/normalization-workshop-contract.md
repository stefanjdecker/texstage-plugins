# Normalization Workshop: frozen v1 contract

This records the frozen 0.2.0/N3 contract. Version 0.3.0 retains its engine and
authoring formats; see the [discussion contract](normalization-workshop-discussion-contract.md)
for the new state/view v2 resources and upgrade procedure.

Status: N1–N3 implemented locally, 2026-11-06. The provider is
`io.github.stefanjdecker.normalizationworkshop`, engine
`io.github.stefanjdecker.normalizationworkshop.analyze`, distribution
`texstage-normalization-workshop==0.2.0`. Manifest revision 2 / engine and content API 1.
See the [package guide](../../plugins/normalization-workshop/README.md),
[design](normalization-workshop.md), [delivery plan](normalization-workshop-plan.md)
and [N3 validation record](normalization-workshop-n3-validation.md).
The content type, authoring hook, style and initial native interfaces are implemented.
The twelve v1 schema files are unchanged from N1/N2.
Host reference: `de3351550f3553ca63023554521fbe84806ec94e`, unchanged for this work.

## Frozen resources

Files belong to `plugins/normalization-workshop/texstage_normalization_workshop/`:

| Resource | Meaning |
| --- | --- |
| `schemas/lesson-v1.json` | Named bilingual author envelope |
| `schemas/seed-v1.json` | Canonical compiled engine seed |
| `schemas/answer-v1.json` | Classification/decomposition answers |
| `schemas/analysis-result-v1.json` | Typed facts and certificates |
| `schemas/state-v1.json` | Bounded lesson state |
| `schemas/commands/{submit,control,select}-v1.json` | Command payloads |
| `schemas/views/{participant-input,presenter-controls,presenter-overlay,projector-overlay}-v1.json` | Role projections |

Run `python maintenance/build_normalization_schemas.py --check` to detect drift.
Version resources deliberately for incompatible changes. Source/seed schemas can
use identifier patterns; all other schemas also pass the host portable profile
and both host validators. Cross-field/order/mathematical invariants require
semantic checks. N3 declares and implements the lesson capability using these contracts.

`compile_lesson` validates and compiles the named envelope; `model.check_lesson`
also checks the worked answer independently. These functions do not generate
TeX or register a prepared-authoring hook.

## Source, canonical representation and limits

An author envelope has `format:1`, `exercise`, `worked_answer` and bilingual
`explanation`. The exercise has `format:1`, an ID, title/prompt, ordered
attributes with stable ASCII IDs and English/German labels, FDs, and task.
Attribute IDs use 1–12 ASCII letters/digits/underscores, starting with a letter; they are
unique and case-sensitive. Exercise IDs use the same syntax with a 48-character
cap. The displayed attribute order is fixed per item. Text normalizes to NFC.
A source FD uses named arrays `{"lhs":["C"],"rhs":["T","I"]}`. Empty lhs is
supported and means a constant; rhs is nonempty. Reject unknown/repeated
attributes within a side. Split rhs into singleton dependencies, discard trivial
ones and deduplicate equal pairs with an author diagnostic. Sort pairs by
numeric determinant mask, then dependent bit. Redundant dependencies are legal.

Attribute order is authored and semantic: bit i represents the i-th attribute.
The compiled seed contains `format,id,attributes,fds,task`; attributes are just
the ordered IDs, and FDs are integer pairs `[lhsMask,rhsBit]`. Labels, prompts,
worked answer and prose stay outside the engine. Options are `{}`.
A mask is an integer subset of `R=(1<<n)-1`; a dependent bit has exactly one bit.
Do not accept booleans, floats, exponent tokens, negative masks or coercion.
Negative zero canonicalizes to zero.
Mask 0 is valid for determinants and the possible empty key, not a relation.

| Frozen provider bound | Limit / reason |
| --- | --- |
| Attributes | 1–8; at most 256 subsets |
| Input FDs after singleton expansion, before deduplication | 0–32 |
| Decomposition | 1–8 distinct nonempty component masks |
| Computed candidate-key list | 1–70 distinct masks (maximal antichain bound for eight attributes) |
| Answer | <=512 canonical ASCII bytes; also enforce raw <=2,000 characters |
| Bounded parser / canonical seed and author envelope | <=64 KiB raw UTF-8 / canonical ASCII; depth <=16; <=8,192 visited values/keys |
| Labels and explanations | Labels <=48 code points; title <=120; prompt <=1,000; explanation <=4,000 per language, within source total |
| Typed result | <=8 KiB, full host outcome <=12 KiB |
| Reserved actor slot including hashed handle | <=3,072 canonical ASCII bytes, including reserved compact completion |
| Session pilot | <=64 actors; shared target <=24 KiB, state target <=224 KiB |
| Host envelopes | Transition <=256 KiB; individual view <=128 KiB |
| Host deadlines | Evaluation 2 s; preparation 2 s; state/view hook 250 ms |

These are frozen caps, not classroom throughput claims. The validation record
measures maximal schema-shaped values and 120 larger analyses/verifications.
Raw caps apply when using `parse`; object callers have no raw whitespace to
measure. Classroom queue/hook measurements remain N3/N6 work.
If a valid input exceeds work/time bounds, return operational refusal, never a
negative mathematical result. Do not silently truncate keys, evidence or answers.

Canonical JSON uses sorted object keys, compact separators and ASCII escaping;
arrays with mathematical set semantics are unique and sorted numerically.
Attribute order remains fixed. An answer includes the author-selected `mode`.
Canonicalize card order but preserve distinct contained components: redundancy
alone does not invalidate a decomposition. Duplicate cards and unknown attributes
are actionable input errors. Do not silently remove an essential student choice.

SHA-256 identities use `["normalization-exercise-v1", compiledSeed]` and
`["normalization-answer-v1", canonicalAnswer]`. The exercise includes fixed task
policy and attribute order. Text-only labels/explanations are not semantic.
The host namespace additionally binds the actual persisted binding, provider
payload, engine and contract/schema digest. Use that binding verbatim, including
its engine key. Hashes identify content; they do not authenticate it.

## Task and answer variants

| Task in seed | Answer | Acceptance policy in lesson |
| --- | --- | --- |
| `{"mode":"classify"}` | `{"mode":"classify","normal_form":"1nf|2nf|3nf|bcnf","witness":null|[lhsMask,rhsBit]}` | Correct highest form; for a failure, one valid witness as described below |
| `{"mode":"decompose","target":"3nf|bcnf","preserve":boolean}` | `{"mode":"decompose","relations":[mask,...]}` | Covers R, lossless, all components reach target; additionally preserved if required |

`normal_form` is one enum value, not the literal pipe-separated string.
The witness is null for BCNF. For highest 1NF it witnesses a 2NF violation;
for highest 2NF a 3NF violation; for highest 3NF a BCNF violation.
Any true witness meeting those conditions is accepted, whether or not written
explicitly in F. Empty determinants are allowed and explained as constants.
A missing, trivial or non-implied witness gets specific feedback.

For decomposition, `preserve:false` means preservation is reported but is not an
acceptance requirement; it does not require the answer to lose a dependency.
A 3NF target accepts a BCNF result. No minimum number of tables or equality to a
worked answer is imposed. `[R]` is valid when it already meets the policy.

## Exact finite algorithms

These are provider algorithm choices implementing the mathematical model in the
[design](normalization-workshop.md#mathematical-decisions-that-prevent-misleading-feedback).

1. **Closure:** initialize C=X; scan canonical FDs, add rhs if lhs is contained
   in C, repeat to fixed point. At most eight successful attribute additions.
   Cache all 256 possible closures when useful; no sampling.
2. **Keys of U:** enumerate all X subset U in cardinality then numeric order.
   Keep X when `closure_F(X) & U == U` and no retained key is a subset of X.
   This includes the empty key. Prime attributes are the union of all keys.
3. **Forms of U:** enumerate X subset U and each bit a in
   `(closure_F(X) & U) - X`. A BCNF violation has closure within U != U.
   A 3NF violation additionally has a non-prime rhs. A 2NF violation has a
   non-prime rhs and X a proper subset of at least one key of U.
   Pick the first witness in cardinality/numeric lhs, numeric rhs order.
   Use projected implications even when their derivation goes outside U.
4. **Preservation:** for each original canonical pair X -> a, start Z=X.
   Repeatedly visit each component U and extend Z by
   `closure_F(Z & U) & U` until unchanged. The FD is preserved iff a is in Z.
   All original FDs preserved implies their closure preserved. Report the
   first failure plus the saturated closure; an independent implementation
   should cross-check using an explicitly enumerated union of projections.
5. **Losslessness:** first require coverage of R. For m components build an
   m-by-n tableau: a_j in column j if j belongs to that component; a fresh
   b_ij otherwise. Scan canonical FDs and row pairs; if the determinant
   symbols agree, unify the rhs symbols throughout that column. Prefer a_j,
   otherwise the smaller symbol ID. Continue until no changes. Lossless iff
   some row is all a_j. Record each effective merge (FD index, row i, row k).
   At most n*(m-1) <=56 effective merges. Saturate even after finding a row,
   so certificate selection is deterministic. Never merge across columns.
6. **Counterexample:** a saturated losing tableau, with equal symbols mapped
   to equal synthetic values, satisfies F. Its distinguished all-a tuple
   occurs in the join of its component projections but not in the relation.
   Validate all FDs, absence of this tuple, and membership of each of its
   projections before displaying it. These tests avoid enumerating an
   unbounded Cartesian join. An unsuccessful/incomplete computation is not
   such a certificate.

For two components, independently compare the chase against the condition that
their intersection closes to at least one component. A constructive sequence of
valid BCNF splits is useful explanatory evidence but is not the only allowed
answer. Arbitrary covered decompositions use the general chase.

N2 uses a 1,000,000 elementary-work-unit guard (FD applicability checks,
subset comparisons, tableau pair tests and cell replacements). Closure caching and monotone unions bound the finite work; explicit
counters and deadline tests are still required. Python preparation and browser
evaluation must agree, but must not share the same algorithm implementation
wholesale. Reducers do not recompute all closures/chases on every submission.

## Engine facts and independent verification

Data has exactly `format:1, exercise, answer, mode, facts`. A successful engine
result has `status:"ok"`, canonical JSON of that data and a bounded neutral text
summary. The host supplies outcome key/namespace. Successful analysis is not a
student grade or equality to a worked answer.

Classification facts are `normal_form, prime, keys, witnesses, witness_valid`.
Keys are all minimal superkeys in numeric order, including the possible empty
key. Witnesses has `2nf`, `3nf`, `bcnf` fields, each a pair or null. Pick the first
witness by lhs cardinality, numeric lhs, then numeric rhs. `witness_valid` tests
the role for the submitted claim; acceptance also compares the claimed form
with the actual highest form.

Decomposition facts are `covered,missing,components,preservation,join`.
Components are ordered `{relation,normal_form,prime,witnesses}` records.
Missing coverage makes preservation and join **null**; component diagnostics
remain available. This replaces the provisional omitted-field representation.
Preservation is `{preserved,fd,closure}`: first lost canonical FD index and its
saturated projected-union closure, or fd=-1/closure=0 on success.
Join is `{lossless,rows,columns,merges,tableau}` with <=56 merge triples and
an <=8-by-8 final tableau. Symbols are a_j=j and b_ij=n+i*n+j. The chase scans
canonical FDs then row pairs i<k in order; merges prefer the smaller symbol.
Saturate even after finding a distinguished row. Include exact dimensions and
canonical component order. Do not return all projected FDs or component keys.

Python's independent oracle computes closures by intersection of all FD-closed
attribute sets, enumerates projected singleton FDs for preservation, and uses
union/find for the chase. JavaScript uses forward chaining, iterated projected
closures, and physical column replacement. Both use the finite rules above.
`verify_analysis` bounds supplied facts and compares all identities and evidence
with an independent analysis of that **same submitted answer**. This rejects
forged booleans, missing keys/witnesses, changed tableaux and extra/missing merges.
It does not require equality to a teacher's preferred decomposition. The helper
fits the measured 250-ms hook budget on the tested cases; the record states its
limits. Host lease/binding/epoch/correlation validation remains the caller's job.

Malformed answers return `syntax`; exhausted input/work/output budgets return
`refused`; unexpected failures become host `error`; the host owns `timeout`.
Bad seeds/options fail load. Mathematical failures remain `ok` with facts.
Each loaded state permits one evaluation; disposal is idempotent. No equality
reference binding is needed. `model.accepted` is the task-policy helper; callers
must verify untrusted facts first. This remains formative assessment under the
existing presenter-evaluator trust model.

## Commands, state and views (N3 implemented)

`submit` carries phase guard, actor-local version and bounded answer.
Presenter commands `open, close, reveal, select-answer, share-answer, unshare, clear-selection`
carry a control guard and explicit answer version where relevant. Declare
authorized roles and closed server command schemas. Use latest host revision
policy with these domain guards; global revisions must not reject unrelated
students' work. Epoch, identity and role come from host context.

State is `{phase,phase_version,control_version,active,actors,selected,shared}`.
Actors is an array of <=64 unique-handle slots:
`{handle,version,answer,correlation,status,feedback}`. Handle is SHA-256 of
`["normalization-actor-v1", authenticatedActor]` in canonical JSON; raw actor IDs
are not persisted. This replaces the draft raw-key map and avoids Unicode
escaping growth. Never accept a client-chosen identity. Correlation is the SDK
hash or null. Status is pending/checked/unavailable. The reducer maintains
handle uniqueness, status consistency, and byte caps; checked slots alone have
feedback, pending slots alone have a correlation.

Compact feedback is <=256 bytes, with fields
`accepted,normal_form,missing,lossless,preserved,witness,lost_fd`; use null where
a task has no corresponding property. Selected/shared references contain
handle/version. Replacing an answer clears sharing of the obsolete version.
Reserve completion space before accepting work. Actor 65 receives capacity
feedback; existing-actor replacement remains possible. Detailed inspection is
one selected answer, not every participant on every view call.

Submit carries phase/version/answer. Controls carry a control guard; select/share
also carry handle/version. Role authorization and context actor/epoch remain
host-owned. Message declarations use latest revision policy plus domain
guards, so unrelated global revisions do not reject valid edits.

`Evaluate` uses the author's single analysis binding; replacing a pending answer
emits `CancelEvaluation` and the new effect atomically. Use SDK
`evaluation_correlation(actor,request_id,slot)` with slot
`analysis:{hostEpoch}:{newAnswerVersion}`. This prevents a reused request ID after
reset from colliding with old work without adding an epoch field to frozen state.
Same request retry is idempotent.
Different envelope under an existing request ID is refused. Accept completion
only for the current epoch, binding, correlation and answer version.
Operational errors retain the saved answer and expose retry/recovery status.

Public view: task, own saved answer/version and pending status; release own
feedback only at reveal. Projector: task, anonymous counts and explicit shared
answer; worked solution only at reveal. Presenter: bounded counts and one
selected answer/analysis. Never transport an all-answers map to the projector.
Changing the shared answer version requires a deliberate presenter action;
clear sharing if its referenced version is replaced. Renderers preserve dirty
drafts across updates and destroy listeners/work on teardown.

N1 checks schema-shaped worst-case views, state, transition and compact feedback
with ASCII escaping, including astral Unicode. N3 tests actual transitions and
transport privacy. A presenter overlay recomputes at most one checked selected
answer; detailed facts are not duplicated into each actor slot. The projector
receives only the explicitly shared answer/version, not its handle or private
analysis. Participant feedback is released only at reveal. Reveal cannot reopen;
reset is required. Reopening a closed round clears both selected/shared references.

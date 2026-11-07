# FD Lab: v1 contract

Engine v1 implemented locally, 2026-11-06. See the
[package](../../plugins/fd-lab/README.md), [F1 validation](functional-dependencies-f1-validation.md),
[design](functional-dependencies.md) and [plan](functional-dependencies-plan.md).
The owned [seed](../../plugins/fd-lab/texstage_fd_lab/schemas/seed-v1.json),
[answer](../../plugins/fd-lab/texstage_fd_lab/schemas/answer-v1.json) and
[result](../../plugins/fd-lab/texstage_fd_lab/schemas/analysis-result-v1.json) schemas
define the implemented engine. The Python model also validates named lessons
against its [envelope schema](../../plugins/fd-lab/texstage_fd_lab/schemas/lesson-v1.json).
F2 now implements the closure content capability, style, state, command schemas
and four audience view schemas in the package. Its commands include a guarded
`demonstrate` step selector; explicit anonymous sharing is allowed only after reveal.
See the [lesson guide](../fd-lesson.md) and [F2 validation](functional-dependencies-f2-validation.md).
F3 adds keys and implication to the same content capability and frozen answer
variants. See the [F3 record](functional-dependencies-f3-validation.md). Owned package
schemas define all implemented command/view variants. FD Lab 0.4.0 uses state
schema 2 and the host's `actor-slots-v1` storage contract. Engine seed, answer
and result formats remain v1. See the
[capacity record](functional-dependencies-600-validation.md) for exact artifacts
and the still-open feedback latency gate. Upgrades require a new bundle/session.

## Capability identities

| Field | Engine value / planned content value |
| --- | --- |
| Distribution / Python namespace | `texstage-fd-lab` / `texstage_fd_lab` |
| Provider | `io.github.stefanjdecker.fdlab` |
| Engine | `io.github.stefanjdecker.fdlab.dependencies` |
| Content type | `io.github.stefanjdecker.fdlab.exercise` |
| Manifest / plugin API / engine API / content API | 2 / 1 / 1 / 1 |
| Authoring hook / state hook / state schema | `exercise` / `exercise` / 2 |
| Binding / canonical format | `analysis` / `fd-analysis-v1` |
| Style / exported command | `texstage-fd-lab.sty` / `\fdlab` |

The engine is independently usable even though it shares a distribution with
the lesson. An interim engine-only manifest declares no unimplemented content
capability. No catalog release is added until conformance passes. Do not treat
the host's development version alone as a compatible immutable pin.

## Named authoring and compact engine input

A lesson envelope has `format:1`, `exercise`, `worked_answer`, bilingual
`explanation`, and `feedback` (`after-reveal` or `practice`). The exercise has
`format:1`, `id`, bilingual `title` and `prompt`, an ordered `attributes` array,
ordered `fds`, and `task`. An attribute has an ASCII `id` and bilingual `label`.
An FD has a unique ASCII `id`, `lhs` and `rhs` arrays of attribute IDs.
Tasks are closed variants:

- `{"mode":"closure","start":["workshop"]}`.
- `{"mode":"keys","require":"one"}` or `"all"`.
- `{"mode":"implication","lhs":["workshop"],"rhs":["building"]}`.

Attribute and FD IDs use 1–16 lower-case ASCII letters/digits/underscores,
starting with a letter. All named sets have unique members from this relation.
Source JSON rejects duplicate object keys, non-finite values and unpaired
surrogates. Normalize text to NFC, bound labels to 64 code points and title,
prompt and explanation to 1,600 each. Source bytes and normalized compact UTF-8
are each at most 32 KiB. Text is plain text, never executable TeX or HTML.
Repeated equivalent FDs with distinct IDs may be retained, with an author warning.

The worked answer uses attribute and FD names. Preparation compiles sets to
integer bit masks using the declared attribute order, and proof steps to FD
indices. This mapping is part of the exercise identity and cannot change under
a saved answer. The engine seed contains only `format`, `id`, ordered attribute
IDs, ordered FD records `{id,lhs,rhs}` with masks, and the compiled task.
Engine options are exactly `{}`; the lesson supplies no equality references.
Labels, worked answers and feedback policies do not enter the engine seed.
Named source and compiled seed get separate validators and depth limits.

For n attributes, masks range from 0 through `(1 << n) - 1`. Zero denotes the
empty set. Reject booleans, fractional/exponent number tokens, unknown fields,
out-of-range bits and references to nonexistent FDs; do not coerce them. The
wire uses small numbers only; the UI and static output always display names.

## Answers

All answers are closed objects with `format:1` and a mode matching the seed:

```json
{"format":1,"mode":"closure","closure":60,"steps":[2,3]}
{"format":1,"mode":"keys","keys":[5,6]}
{"format":1,"mode":"implication","implied":true,"steps":[2,3]}
{"format":1,"mode":"implication","implied":false,"agree":8}
```

These use the workshop order `person,email,workshop,tutor,room,building`.
The named worked-answer counterparts are in [examples.json](functional-dependencies/examples.json).
Key arrays normalize to numeric order and contain no duplicates. In one-key
mode exactly one entry is required. All-keys mode permits an empty list as an
incomplete answer, and `[0]` denotes the empty key. Step order is significant.
At most eight steps or 256 proposed keys; compact canonical ASCII JSON must fit
1,800 bytes and raw input must fit the host's 2,000-character limit.

The client cannot choose a different task, FD set, engine, feedback policy,
actor identity or evaluation binding. The seed is authoritative.

## Analysis facts and certificates

Successful engine output has `status:"ok"`, canonical identity, a bounded
neutral text summary and typed `data`. It does not carry a student grade or use
`matches` as correctness. The host converts canonical identity into its compact
`key` and adds `namespace` for the transported outcome; the engine does not
supply either field. Data has `format:1`, exercise and answer SHA-256
identities, `mode`, and exactly one mode-specific `facts` object:

| Mode | Facts |
| --- | --- |
| Closure | Complete `closure` mask and checked `trace` |
| Keys | Complete `candidate_keys` list, and one check tuple `[mask,closure,removable]` for each submitted key, in normalized order |
| Implication | Complete determinant `closure`, mathematical `implied` boolean, and a checked derivation or pair witness matching the submitted claim |

`removable` contains exactly those members whose removal still leaves a
superkey. A non-superkey has no such members. The reducer separately tests
closure equals the universe and `removable == 0`; an empty removable set alone
does not establish a key. It compares exact key-set collections only in all-keys
mode. Extra, missing, repeated or reordered check tuples invalidate the result.

A trace contains `reached`, productive steps `[fdIndex,addedMask]`, and `error`.
Error is null or `{kind,step,missing}`; kinds are `unmet-lhs` and `no-progress`.
Replay starts from the task's determinant and stops at the first bad step. The
error index and prefix must match the submitted steps exactly. No hidden or
extra steps are accepted. Closure mode requires an error-free replay reaching
the complete closure and a final-set claim equal to it. Positive implication
requires an error-free replay containing the target right side, not necessarily
the entire closure. Trivial implications can have an empty proof.

A pair witness contains the submitted `agree` mask, the exact list of violated
premise FD indices, and `violates_target`. The corresponding two rows are derived
from the mask. A negative answer succeeds only if mathematical `implied` is
false, the premise-violation list is empty and `violates_target` is true.
All valid agreement sets are accepted; comparison to one worked witness is wrong.

Well-formed mathematical mistakes return facts with `status:"ok"`. Malformed
answers return `syntax`; exhausted work/byte limits return `refused`; unexpected
engine failures return `error`; timeout remains host-owned. Invalid seeds/options
fail load. Do not put arbitrary exception messages or private answers in summaries.

Identity uses SHA-256 of canonical ASCII JSON, with sorted object keys, compact
separators and lower-case hex: `["fd-exercise-v1", compiledSeed]` and
`["fd-answer-v1", normalizedAnswer]`. The canonical result identifies
`["fd-analysis-v1", exerciseDigest, answerDigest]`; a digest is identity, not
authentication or a grade. The host namespace additionally covers the complete
persisted binding, engine, provider payload and result schema. Use a portable
hash implementation so ordinary classroom LAN HTTP does not require WebCrypto.

## Validation and resource bounds

The Python model computes closures and candidate keys independently and validates
the named worked answer. Preparation stores a complete private closure table for
key tasks, or the fixed determinant closure and implication truth for proof tasks.
The state reducer verifies engine facts against those tables and replays the
small certificates before grading. Schema validation alone is insufficient.
Do not re-run an expensive search per participant inside a state hook.

Enumerating all closures uses at most `256 × 9 × 24 = 55,296` FD tests: each
closure has at most eight productive passes plus one final pass. Every FD
applicability check costs one unit; trace/witness checks share the same counter.
Memoized closure lookups and single-removal key checks need no additional FD
tests. Proposed hard work cap: 65,536 units. The host's two-second engine limit
still applies, and byte parsing, set enumeration and output assembly are bounded
separately. This is an operation bound, not measured runtime.

The maximal structural key-answer envelope has at most 256 masks; facts have
at most 256 three-number check tuples and 256 candidate masks. A conservative
synthetic full-size encoding must pass 8 KiB for typed data and 12 KiB for the
complete outcome, using the host's ASCII escaping. No truncation of facts.
Portable schemas use closed bounded objects/arrays and acyclic local references,
without `pattern`, `$id`, remote references or other unsupported keywords.

Storage limits: 1,000 actors, 2 KiB per actor including actor key and reserved
compact feedback, and 160 KiB shared state. Shared state stores phase/control
versions, incremental counts, a bounded selected snapshot, an explicitly shared
demonstration and the reserved `actor_page` cursor. Actor slots are separate
durable records, not an `answers` map inside shared state.
Store neither full key-check arrays nor trace histories per actor. The selected
inspection view can derive details from the private table and one saved answer.
Include effects in the 256 KiB host transition limit; every view stays below
128 KiB. These provider limits must pass worst-case serialization tests before
being advertised. The presenter receives at most 100 slots per context/page;
participant/evaluation hooks receive only their authenticated actor's slot.
`ActorTransition(..., audience="actor")` atomically replaces that slot and shared
state, and targets the actor's devices plus hosts. Global controls use `Transition`.
Replacement remains possible at capacity. A full classroom
is an operational refusal, not an incorrect mathematical answer.

## Messages, lifecycle and views

The lesson declares participant `submit` with `{phase,version,answer}`;
`phase` is the phase version and `version` is the actor's answer version.
Presenter `open`, `close` and `reveal` take `{control}`; `select-answer` and
`select-demonstration` take `{control,actor}` (empty actor clears the selection);
`demonstrate` takes `{control,step}` for a prefix of a closure or positive
implication worked proof. Key tasks and negative worked witnesses refuse this
operation with `no-derivation`; their controls are hidden. A walkthrough projection
includes its bounded `known` attribute mask separately from the answer. Use the host's
`latest` transport policy plus explicit phase/control and actor-version guards;
global snapshot revision alone must not reject unrelated concurrent answers.
Use the existing epoch-guarded `_reset`. Message schemas and role allowlists
are closed; selected answers/shares refer to server-known slots and versions.
Public `select-demonstration` and `demonstrate` require the revealed phase. Private
presenter selection may occur earlier. Practice mode releases only the actor's
own permitted feedback; it does not open public solution projections.

`roster-page` takes `{control,page}`, with page in 0–9 and below the current page
count. Presenter views include `roster_page`, `roster_pages` and at most 100
participants; class totals cover all pages. Selection/share commands resolve
only actors on the current page. Selected private snapshots follow later answer
replacements and results even if the presenter browses another page.

One correlation per actor/request/analysis slot via SDK `evaluation_correlation`.
Cancel a superseded evaluation and submit its replacement atomically. Preserve
pending answers through evaluator absence; retries must not duplicate attempts.
Check the authenticated actor, epoch, correlation, binding and exercise/answer
identity on completion. Domain refusals and operational dispatch error codes
remain distinct. Render no grade when transport or evidence is invalid.

Declare all four surfaces with exact matching portable view schemas:
participant input, presenter controls, presenter overlay and projector overlay.
Demonstration state is a bounded public projection, not a copy of inspection
state. Ordinary updates preserve drafts; reset/newer same-actor answers require
explicit reconciliation even when the mount is retained. Dispose listeners,
timers and pending preview tasks using the host abort signal. Do not introduce
a client-owned worker that would conflict with the current host security policy.

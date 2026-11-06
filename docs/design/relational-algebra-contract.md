# Relational algebra v1: engine contract

Implemented local contract, 2026-11-06. The package is
`texstage-relational-lab`; provider `io.github.stefanjdecker.relationallab`;
engine `io.github.stefanjdecker.relationallab.algebra`.
See the [design](relational-algebra.md), [package instructions](../../plugins/relational-lab/README.md)
and [validation evidence](relational-algebra-r2-validation.md).

## Sources and schemas

The owned, versioned resources are:

- [Exercise schema](../../plugins/relational-lab/texstage_relational_lab/schemas/exercise-v1.json).
- [Answer schema](../../plugins/relational-lab/texstage_relational_lab/schemas/answer-v1.json).
- [Result schema](../../plugins/relational-lab/texstage_relational_lab/schemas/analysis-result-v1.json).

The ordinary exercise schema can use property-name patterns. Answer and result
schemas use the host's portable profile. Structural schema acceptance does not
replace semantic checks: earlier child indices, single parents, canonical
postorder, unique headers, attribute types, allowed operations and rule conditions
are validated by the model/engine.

The JSON source is the engine seed; options are an empty object. Sources contain
format 1, an ID, English/German title and prompt, named relation schemas, instances
and task policy. Exactly one instance is public; the other zero to three are
private. Instance IDs are unique; every instance has exactly the declared tables.

Construction adds `initial_tree` and `reference_tree`, and the task adds
`expected_header`. The starter is either empty or a complete valid tree; partial
editor drafts are not seed trees. The reference must have the expected header.
Rewriting instead adds `baseline_tree` and the task's allowed rules and
`reduce-public-materialization` goal. A submitted mode cannot override seed policy.

Preparation must evaluate references against the fixtures within the work/row
budget. Source validation verifies shape and typing; it does not promise every
possible evaluation fits. The independent Python model performs those evaluations.
Duplicate source rows normalize to a set; `source_diagnostics` reports their
instance/relation and count for the future authoring hook.

## Scalar, tree and identity rules

Values are integers in ±1,000,000, booleans or NFC strings of at most 24 Unicode
scalar values. Booleans are not integers. JSON numbers use integer tokens:
`1.0` and `1e0` are refused as syntax rather than coerced. Duplicate keys,
unpaired surrogates, non-finite numbers and implicit type conversions are refused.

Relation/attribute IDs use 1–12 lower-case ASCII letters/digits/underscores,
starting with a letter. Headers have at least one column; projection is nonempty.
Base headers have at most six columns; intermediates at most twelve.
Attribute names must be disjoint across product/join inputs; rename first.
The [design](relational-algebra.md#flat-tree-format) lists all eight tuple forms.

Trees have 1–16 nodes, depth at most eight, and left-to-right postorder indices.
Each non-root node has exactly one parent. Separate leaves can read the same
relation; a shared AST node is not permitted. Predicates have 1–3 comparisons
joined with AND. Ordered comparisons accept integers only.

Canonical JSON has sorted ASCII object keys, no insignificant whitespace,
lower-case JSON booleans and ASCII escaping of non-ASCII UTF-16 units using
lower-case hex. Text is normalized before serialization. Negative zero is zero.
Within relations, headers sort by name; rows are unique and lexicographically
ordered by that header: integers numerically, booleans false before true, text
by Unicode scalar value. Row order is not a query-result ordering guarantee.

SHA-256 is applied to the ASCII bytes of these canonical JSON values:

| Identity | Payload |
| --- | --- |
| Header | `["header-v1", canonicalHeader]` |
| Relation | `["relation-v1", canonicalHeader, canonicalRows]` |
| Answer | `["relational-answer-v1", normalizedAnswer]` |
| Exercise | `["relational-exercise-v1", semanticExercise]` |

The semantic exercise includes ID, normalized schemas/instances, task mode,
allowlists, expected header or improvement goal, and reference/baseline tree.
Instances sort by ID; allowlists sort; table rows and headers canonicalize as
above. Title, prompt, feedback-release label and starter tree do not affect it.
The host's binding namespace additionally binds the actual seed/options, provider
payload and schema. These hashes are identities, not authentication.

## Answers and facts

Construction: `{"mode":"construct","tree":[...]}`.
Rewriting: `{"mode":"rewrite","steps":[{"rule":"...","path":[0,1]}]}`.
Paths count child positions from the current root. At most eight rules are
allowed. Each rule derives its successor; no supplied replacement is accepted.

The answer's canonical JSON must fit 1,800 ASCII bytes. The same tree limit is
applied to source trees and derived trees using the construction-answer envelope.
The wire sender should send canonical ASCII; the host/browser's raw 2,000-character
limit also applies. Source raw UTF-8 and normalized compact UTF-8 each fit 64 KiB.
Parsing is bounded to depth 16 and 8,192 JSON values.

A valid analysis carries `format, exercise, answer, mode, valid, fixtures, public`.
Fixture entries contain IDs and header/relation digests only. Public facts contain
`trace` rows `[nodeIndex, tupleCount, columnCount]` and the intermediate-cell sum.
No private rows, expected digests or full intermediate tables are returned.

Rewrite facts additionally contain `proof` with `verified, steps, tree,
baseline_cells, improved`. Empty certificates verify equivalence to the unchanged
baseline but cannot satisfy improvement. Improvement is measured on public data,
not real database execution time. Construction facts deliberately contain no
`correct` or `matches` flag.

Well-formed invalid queries produce `valid:false` with a bounded reason, node
index and step index; unused locations are -1. They contain no fixture/trace
facts. Malformed answers return only `{"status":"syntax"}`; resource exhaustion
returns only `{"status":"refused"}`. Bad seeds/options fail load. Every state accepts
one evaluation; reuse after evaluation or disposal is refused.

The future lesson must verify exercise/answer identity, mode, exact fixture
coverage and expected outputs or certificate/goal facts. Shape-valid fabricated
facts are not mathematical evidence merely because a schema accepts them.
No result field authorizes its own release to participants.

## Work and transport bounds

Each visited input tuple, candidate pair and comparison atom consumes one work
unit. Charge input sides once per operator, then candidate pairs and visited
comparison atoms; short-circuit conjunctions. Relation leaves charge source rows,
including duplicates. The 100,000-unit budget spans all fixtures, baseline and
derived trees in one job. It does not reset per fixture or step.

Intermediates stop before exceeding 256 distinct rows. Products/joins stream
candidates. The host's two-second worker deadline remains the ultimate execution
bound. The planned phone controller has a separate 25,000-unit public preview
budget and cooperative scheduling; that controller is not delivered here.

Typed facts fit 8 KiB and the complete host outcome fits 12 KiB. The implementation
keeps the derived tree within the 1,800-byte envelope and transports at most
four digest entries and sixteen three-integer trace rows. Together these have a
conservative bound below 4 KiB of facts and 5 KiB of outcome; tests exercise a
near-limit Unicode tree with maximum fixture/trace dimensions through both host
validators. The schema alone does not express a tree's encoded byte bound.

No class-state, participant-count or UI-response-time claim follows from these
engine bounds. Those remain R4–R6 measurements.

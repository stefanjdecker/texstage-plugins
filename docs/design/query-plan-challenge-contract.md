# Query-plan Challenge v1: frozen engine and lesson-source contracts

Current storage/scalability extension: [600-student plan](query-plan-600-plan.md)
and [validation](query-plan-600-validation.md). Earlier milestone bounds below
record their original scope.

Status: implemented locally, 2026-11-06. Scope: frozen Q0/Q1 engine/source
contracts, plus Q2 authoring and Q3 classroom state in package 0.3.0. See the
[design](query-plan-challenge.md), [plan](query-plan-challenge-plan.md),
[Q1 evidence](query-plan-engine-validation.md) and [Q2 evidence](query-plan-authoring-validation.md).
The engine/source v1 schemas are unchanged. The separate
[classroom v1 contract](query-plan-classroom-contract.md) freezes Q3 commands,
state and audience views. Interactive controls remain Q4.

## Owned package and authoritative schemas

Distribution: texstage-query-plan 0.3.0; provider:
io.github.stefanjdecker.queryplan; engine:
io.github.stefanjdecker.queryplan.cost. Manifest revision 2, plugin API 1,
engine API 1, host result contract revision 2.

The authoritative schemas live under
[texstage_query_plan/schemas](../../plugins/query-plan/texstage_query_plan/schemas):

| File | Meaning |
| --- | --- |
| exercise-v1.json | Engine seed shape; semantic invariants below are also mandatory |
| answer-v1.json | Submitted plan shape; topology/feasibility are domain checks |
| analysis-result-v1.json | Closed portable typed-result schema |
| lesson-v1.json | Prepared lesson's source envelope |
| prepared-view-v1.json | Historical Q2 mode marker; no longer referenced |
| commands/*-v1.json, views/*-v1.json | Frozen Q3 commands and closed audience projections |

Python model.py and independent browser validation.mjs/model.mjs enforce the
same source/answer semantics. The production package does not import the design
checker or any other provider. Schema validation alone does not establish
semantic correctness, identity or plan feasibility.

## Parsing, normalization and identity

Accept only plain JSON values and integer numeric tokens; floats/exponents,
NaN/Infinity, unsafe integers, duplicate object keys (including escaped spellings),
unpaired surrogates and unknown properties are rejected. Integers cannot be
booleans. Both parsers cap nesting at 16 value levels and 2,048 values; object
keys do not count as separate values. Raw seed input is at most 32,768 UTF-8 bytes.
Raw answer input is at most 2,000 UTF-8 bytes and host characters; its canonical
ASCII representation is at most 1,024 bytes.

Identifiers match [a-z][a-z0-9_]{0,15} exactly, including at the end of a line.
Text literals are NFC Unicode scalar strings, at most 64 code points, with
case-sensitive equality. They are rejected rather than silently normalized.
Integer literals are within -1,000,000..1,000,000. There is no NULL/coercion.

Normalize valid sources by sorting relations and each relation's columns by ID,
orienting join endpoints lexically and sorting join records by canonical JSON.
Sort base statistics by relation ID; sort each cardinality's relation IDs and
then cardinality records by subset mask. Projection order and repeated projection
columns are preserved. Subset bit i belongs to the ith relation in sorted ID order.
There are no labels/prose in the engine source.

Canonical JSON sorts object keys, uses no whitespace, escapes non-ASCII/DEL
characters in the same form as Python ensure_ascii=True (including surrogate
pairs), and uses ordinary bounded integer tokens. Source/answer inputs are copied;
normalization never mutates caller-owned data.

SHA-256 identities are:

- exercise: canonical JSON of ["query-plan-exercise-v1", normalized_exercise].
- answer: canonical JSON of ["query-plan-answer-v1", shape_valid_answer].

Answer node order remains significant, even for infeasible answers. Object key
order/whitespace do not. Changing statistics, query, limits or model changes the
exercise identity. Lesson explanations and goals are not engine identity inputs.
The engine canonical result is the canonical JSON of its complete typed data.
This identity is not a grade or authentication mechanism.

The browser implementation includes an owned portable SHA-256 implementation
and works without crypto.subtle on LAN HTTP. The host namespace additionally
binds the provider payload, engine, schema contract and complete actual evaluation
binding. The probes include the binding's engine key; a placeholder seed's
namespace cannot validate a different request.

## Fixed query and statistics

One to three distinct relations, each with one to eight unique typed columns.
Types: int, text, bool. A relation has at most one equality-to-literal filter,
and optionally one equality index on exactly that filter's column. Index height
is 1..8. No self-joins, arbitrary SQL, join-index probing or mutable data.

The query graph is a connected tree with n-1 distinct inner equijoin edges.
Each edge references existing columns of equal type in different relations.
The fixed projection contains one to eight valid qualified columns. All operators
retain duplicates; projection is bag projection, not DISTINCT. All fixed base
filters and crossing join predicates are implicit in every legal plan.

There is exactly one base-statistics record per relation. Base rows and pages
are 0..1,000,000; nonempty relations require a nonzero page count. Base row width
is 1..1,024 bytes. There is exactly one estimated cardinality for every nonempty
connected subset, with no extra or duplicate subset. Each count is 0..1,000,000.
A filtered singleton has at most its base rows; an unfiltered one has exactly
its base rows. For every connected split of a subset, its count cannot exceed
the product of the two input counts.

These are necessary consistency constraints on estimates, not proof that they
come from one real database. Costs never iterate over, fetch or execute rows.
Intermediate row width is the sum of base widths. Node facts describe inputs
before the final, uncosted projection; the bag row count survives projection.

## Legal plan and cost facts

An answer has format=1 and one to five nodes. Scans have op, relation and method
(seq/index). Joins have op, left, right and method
(nested/hash-left/hash-right). Child indices are integers 0..3.

Require a proper tree: children precede parents, every non-root has exactly one
parent, root is last, and left-to-right postorder is exactly array order.
Each relation occurs exactly once. A join connects disjoint connected subsets
along the fixed query graph; the crossing predicate is supplied by the engine.
An index scan requires the declared index. A hash join must fit the public
per-operator workspace limit (0..16,777,216 bytes).

Model teaching-cost-v1 has fixed integer coefficients:

| Operation | Local teaching cost |
| --- | --- |
| Sequential scan of N rows, P pages | 100P + N |
| Index scan, height H, R matching rows | 400(H + R) + R |
| Materialized nested join, L/R input rows, O output rows | LR + O |
| Hash join, B build rows, Q probe rows, O output rows | 2B + Q + O |

Hash workspace is B*(build row width+16). Empty builds require zero workspace.
Total node cost adds local work and both children's totals once. Memory is a
per-hash workspace feasibility check, not total plan memory. Caching,
materialization storage costs, spills, parallelism and elapsed time are outside
the model. An empty result still pays the stated scan/descent/probe costs.

All arithmetic is exact and below 2^53-1. The conservative declared cost ceiling
is 3,000,000,000,000. The maximum raw candidate family is 864:
12 labeled ordered trees * 8 scan assignments * 9 join assignments. Each costs
at most five nodes. Feasibility removes disconnected, unavailable or non-fitting
candidates; the browser evaluates only one submitted plan.

## Validity, failure and lifecycle

A successful analysis result uses the standard text summary and typed data:

- Common: format=query-plan-analysis-v1, model=teaching-cost-v1,
  exercise/answer SHA-256 strings and valid.
- Valid: cost and one to five node facts containing node, subset, rows,
  row_bytes, local_cost, total_cost and hash_bytes.
- Domain-invalid: reason and node; no cost or nodes array.

Stable domain reasons are invalid-tree, unknown-relation, duplicate-relation,
missing-relation, disconnected-join, unavailable-index and hash-memory.
Topology is checked first: a forward/self-reference identifies its parent;
global parent-count/postorder errors use node=-1. Then nodes are checked in
postorder (unknown/duplicate relation before index availability; connectivity
before hash feasibility). Missing leaf coverage is checked last with node=-1.

Malformed answer shape/JSON produces status=syntax. Input/output byte-budget
violations produce status=refused. These failure results contain only status.
Invalid seeds/options reject load and are handled as operational errors by the
host. An unknown exception is not turned into a wrong answer. Typed data is
bounded by 8 KiB inside the host's 12-KiB complete outcome limit.

start returns an empty library handle; load accepts a seed JSON string and an
empty options object. Every loaded state supports one evaluate call, including
syntax/refused submissions. A second call or evaluation after dispose fails.
dispose clears the seed and is repeatable. No state persists between students
or reference/submission runs.

The engine emits facts, not grades, optimum searches or matches-based correctness.
A future lesson must verify epoch/correlation/binding and exact semantic identities,
node coverage and arithmetic. Portable schema acceptance alone is insufficient.

## Python reference and prepared lesson source

The public helpers are source, answer, analyze, candidates, optimum and
prepare_reference. The reference enumerator returns cost, count of tied optimal
plans, one deterministic lexically smallest canonical representative, candidates
examined and feasible count. It never stores an unbounded list of all optima.

lesson-v1 has format, exercise, baseline, goal, worked_answer and explanation.
Goal is either {"kind":"best"} or {"kind":"budget","max_cost":integer}; explanation
has en/de NFC strings of 1..2,000 code points. The whole envelope is capped at
96 KiB, separately from the 32-KiB engine source and 1-KiB answers.

prepare_reference validates this envelope, calculates the finite optimum and
checks both authored plans. Baseline must be feasible; budget must be reachable;
worked answer must satisfy the goal. It returns owned normalized source plus
baseline/worked facts and reference facts for later authoring. Any tied optimum
can satisfy best; canonical equality is never the goal criterion.
The pure helper remains independent of the host. The authoring hook calls it once
and produces PreparedAuthoring from that result; it does not produce a grade.

## Prepared content and classroom bridge

Content ID is io.github.stefanjdecker.queryplan.challenge, content API 1.
Authoring hook challenge emits format-1 PreparedAuthoring with exercise/solutions
fragments and no assets. Public fields are format, exercise, baseline,
baseline_analysis and goal. Private fields are exercise (semantic identity),
reference (minimum, ties, deterministic representative, candidate/feasible counts)
and worked (answer, analysis, en/de explanation). The analysis evaluation binding
uses the normalized exercise as its seed and no references/options.

The style texstage-queryplan-challenge.sty exports only
\queryplanchallenge{id}{width}{height}, delegating to \texstageprepared. A
namespaced local height is used to fit rendered content inside that rectangle.
Text is escaped; unsupported explanation Unicode uses explicit code-point
notation while the private original stays intact.

Q2's state hook prepared, empty state schema 1, mode-marker views and empty
messages map are historical. Version 0.3.0 declares state hook lesson, state
schema 2 and the [Q3 classroom contract](query-plan-classroom-contract.md).
The mandatory presenter/projector overlays and participant-input module share
a no-op mount/place/update/destroy renderer until Q4. The host requires that
input declaration before accepting participant commands; no editable UI is
claimed. Explicitly enable the reviewed 0.3.0 payload and start a new session.

## Compatibility and remaining scope

The worker entry is generated by the collection's pinned bundler and is
self-contained. Q2 adds prepared content and style without changing the engine
contracts. The host worker policy stays unchanged; no network, child worker or
dynamic-code permission was added.

Current development host baseline is de3351550f3553ca63023554521fbe84806ec94e.
Version 0.2.1.dev3 alone does not identify a compatible wheel; use the exact
validation record. Prepared authoring and bounded classroom state are implemented.
Published host pins, hosted/Linux CI, phone/presenter controls and classroom
load/accessibility tests remain separate gates. Existing courses and original tools are
unaffected.

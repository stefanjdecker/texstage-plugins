# Query-plan Challenge: plugin design

Current storage/scalability extension: [600-student plan](query-plan-600-plan.md)
and [validation](query-plan-600-validation.md). Earlier milestone bounds below
record their original scope.

Status: Q0–Q4 implemented locally in 0.4.0, 2026-11-07. The [frozen v1 contract](query-plan-challenge-contract.md) and
[Q0/Q1 validation record](query-plan-engine-validation.md) cover the independent
cost engine and Python enumerator. The [Q2 record](query-plan-authoring-validation.md)
and [authoring guide](../query-plan-authoring.md) cover generated exercises,
solutions and exports introduced in 0.2.0. The [Q3 protocol](query-plan-classroom-contract.md)
and [state validation](query-plan-state-validation.md) cover storage, verified
feedback, privacy and concurrency. The [Q4 interface record](query-plan-ui-validation.md)
covers selectors, cost inspection and real classroom controls; the
[classroom guide](../query-plan-lesson.md) explains their use.
See the [implementation plan](query-plan-challenge-plan.md) and
[worked examples](query-plan-challenge/README.md).

## Purpose and relationship to the existing activities

Students improve the **physical execution plan for a fixed query**. They explain
when an index helps, why join order matters, which input to hash, and how a
memory limit changes the available choices. Every exercise exposes the statistics,
cost rules and constraints needed to solve it.

| Activity | Student changes | Evidence and feedback |
| --- | --- | --- |
| SQL/SPARQL | Query text | Query execution/results in that activity's engine |
| Relational Algebra Lab | Logical operators or checked rewrites | Relations, intermediate output cells, rewrite certificates |
| Query-plan Challenge | Access paths, join order, join algorithm and hash build side | Legal plan, per-node estimated work, total teaching cost and target attainment |
| Transaction schedules | Operation interleaving | Reads, conflicts and serializability certificates |

Keep these capabilities independent. Relational Lab's set semantics and
intermediate-cell metric are not this plugin's semantics or costs. Its planned
visual logical-tree editor remains useful; this plugin must not silently replace
that milestone. No conversion between their answer formats is implied.

The first library task asks: **Return one row for each open loan of a database
book, showing the member's name.** Names can repeat: the fixed query has bag
semantics. The prepared slide lists fixed outputs, joins and filters in explanatory
notation, never executable student input. Its meaning cannot change when a student
selects an algorithm. A future SQL-like display must preserve that fixed meaning.

This is a deliberately small teaching model, not PostgreSQL's optimizer, a
benchmark, or a prediction of milliseconds. PostgreSQL's documentation distinguishes
estimated rows from rows processed and explains that plan costs are relative
units; parent totals include child totals. Those distinctions inform the UI.
The particular formulas, bounds and materialization assumptions below are our
design choices. See [PostgreSQL 18: Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html)
(accessed 2026-11-07). No PostgreSQL cost values are imported.

## Classroom experience

1. **Introduce:** show the fixed question, generated query, schema, filtered row
   estimates, available index, memory limit, cost-rule card and baseline plan.
   The teacher asks students to predict its expensive step.
2. **Open:** students change a scan, join order, join algorithm or hash build
   side. An explicit **Estimate my plan** action previews only their current
   plan and its public statistics. It does not search for the optimum.
3. **Inspect:** select a node to see input/output row estimates, local cost,
   cumulative subtree cost and the arithmetic producing them. Compare baseline
   and draft side by side on wide screens or in tabs on phones. Show the change
   in cost; do not add cumulative node costs together.
4. **Submit:** save the plan and show saved/pending/checked status. Authoritative
   evaluation is separate from local preview. Withhold target feedback until
   reveal; no silent submissions on editing or preview.
5. **Close and discuss:** retain evaluation of already accepted submissions.
   The presenter can inspect one answer and deliberately share an anonymous
   plan. Closing is not reveal.
6. **Reveal:** release each student's validity, cost and goal feedback, plus a
   worked optimal plan and explanation. Accept ties and alternative equivalent
   tree layouts. No speed leaderboard or grade based on response time.

Phases are introduce/open/closed/revealed. Reopening a closed exercise retains
answers; starting over uses the host epoch-reset path. A revealed activity cannot
become secret again: another attempt requires reset. Initial inactive surfaces
remain useful static material.

On a 320-CSS-pixel phone, use a vertical numbered tree and labeled controls:
choose the first pair, choose which input appears left, select a scan, select a
join method, and select a hash build side. No drag-only interaction or JSON
editing in the classroom UI. Show unavailable choices with a reason (for example,
"Build input needs 240,000 bytes; limit is 1,024 bytes"). Offer undo and reset to
baseline. Labels, numbers and focus states convey meaning without relying on color.
Provide English/German labels and keyboard/touch operation.

## V1 query and plan semantics

An exercise fixes:

- One to three distinct relation IDs; each has one to eight typed columns.
  IDs are ASCII identifiers of at most 16 characters. Types are int, text and
  bool; there is no NULL or implicit coercion. Text literals are NFC,
  case-sensitive and at most 64 characters; integer literals are within
  -1,000,000..1,000,000. Semantic validation enforces these rules.
- At most one equality-to-literal filter per relation. Every scan applies its
  relation's filter. The student cannot drop or relocate predicates.
- A connected, acyclic graph of inner equijoins: exactly n-1 typed column
  equalities, no parallel edges or self-joins.
- A nonempty fixed projection of at most eight qualified columns. Projection
  preserves duplicates and is applied at the root without a separate cost.
- At most one unclustered B-tree access path per relation, usable only for that
  relation's fixed equality filter. There is no join-index probing in v1.
- Base statistics, authored estimates for every connected subset, and a
  per-join hash workspace limit. The lesson envelope adds a legal baseline plan.

A plan contains each relation exactly once. It is a binary tree in canonical
left-to-right postorder, at most five nodes; all child indices point backward,
every non-root node has exactly one parent, and the root is last. A join connects
disjoint subsets along the fixed query graph. The engine automatically applies
the fixed predicate on that crossing edge. There are no Cartesian products.

Scans return all matching occurrences, and both join algorithms retain every
matching pair, including duplicates. Neither algorithm adds duplicate removal.
Thus all legal plans implement the same fixed conjunctive inner-join query under
bag semantics. This is justified by the restricted construction and the
associativity/commutativity of these joins, not by matching a finite example's
output or a preferred serialized plan. Feasibility still depends on index
availability and the workspace limit. Q1 must independently check construction
semantics using small duplicate-containing row fixtures.

Plan encoding (draft):

```json
{"format":1,"nodes":[
  {"op":"scan","relation":"books","method":"index"},
  {"op":"scan","relation":"loans","method":"seq"},
  {"op":"join","left":0,"right":1,"method":"hash-left"},
  {"op":"scan","relation":"members","method":"seq"},
  {"op":"join","left":2,"right":3,"method":"hash-left"}
]}
```

Join methods are nested, hash-left and hash-right. Left/right identify the build
input only for hash joins. Nested means a tuple nested loop over already
materialized children, not an index nested loop or repeated disk scan. Both
children are costed once. Swapping a nested join's children therefore costs the
same in this model; changing the first joined pair can change intermediate rows.

Outside v1: arbitrary SQL parsing/execution, logical rewrites, DISTINCT, NULL,
outer/semi/anti joins, aggregation, sorting/merge joins, ORDER BY/LIMIT, bushy
plans over four or more relations, caching, parallelism, spills, actual database
timings and importing EXPLAIN plans. A later read-only EXPLAIN importer would
need a separately designed format/model; uploading a plan must never execute SQL.

## Statistics and deterministic cost model

Model ID: teaching-cost-v1. All arithmetic uses bounded integers, with no
floating-point thresholds, randomness or dependence on a browser's clock.

The source supplies N base rows, P base pages and W row bytes for each relation,
and R(S), the estimated output row count for every nonempty connected subset S.
Singleton estimates include base filters. Larger estimates include all fixed
filters and joins inside that subset. These are explicit estimates, not measured
results or values inferred by multiplying independent selectivities.

Require exactly that connected-subset coverage; no duplicates/extra subsets.
For a singleton, 0 <= R <= N (and R=N without a filter). For every legal split
S=A union B, require R(S) <= R(A)*R(B). Zero inputs imply zero join output.
These checks are necessary consistency conditions, not proof that arbitrary
statistics arise from one real database. All widths in an intermediate subset
are the sum of its base widths; columns are retained until final projection.

| Operation | Local cost in teaching units |
| --- | --- |
| Sequential scan | 100*P + N |
| Unclustered equality index scan | 400*(H + R) + R |
| Materialized tuple nested loop | L*R + O |
| Hash join | 2*B + Q + O |

Here H is index height; L/R are child row estimates; O is the join's output
estimate; B/Q are build/probe row estimates. Hash workspace is
B*(build-row-bytes + 16). It must be <= the public limit. Empty builds require
zero hash workspace. A tree's cumulative cost is the local cost plus its
children's cumulative costs; compare root totals.

The index formula charges H descent fetches plus one random heap fetch per
qualifying row, and one unit of row work per match. It omits cache reuse,
clustering, separate leaf-page costs and index-only scans. Repeated heap fetches
may revisit a page; R is not a count of distinct pages. Even an empty index
result pays descent cost. Sequential scan work covers all base rows.
Hash work charges two units per build row, one per probe row and one per output
row. Nested work charges one per candidate pair and one per output row.

Children are materialized abstractly. Their storage and transfer costs are
omitted consistently. The workspace limit is **per hash operator**, not a claim
about the complete plan's peak memory: intermediate materialization storage is
outside this model, and operators are evaluated sequentially. The display must
say "hash workspace", not "query memory". A non-fitting hash join is unavailable;
v1 does not secretly choose a spill algorithm. Neither hashing nor indexes are
always better.

Fixed coefficients belong to the model version, not editable teacher parameters.
A new cost formula requires a new model identity and new expected examples.
A statistics change creates a new prepared exercise identity. Demonstrate bad
statistics with two openly labeled exercise variants; never grade using hidden
replacement statistics after students have answered.

### Bounds and exhaustive reference calculation

| Resource | V1 design limit |
| --- | --- |
| Relations / columns per relation / plan nodes | 3 / 8 / 5 |
| Connected cardinality records | At most 7 |
| Base/output rows and base pages | 0..1,000,000 |
| Row width / index height | 1..1,024 bytes / 1..8 |
| Hash workspace limit | 0..16,777,216 bytes |
| Seed / canonical answer | 32 KiB / 1,024 ASCII-escaped bytes |
| Candidate evaluations during preparation | At most 864 (5 costed nodes each) |
| Typed data / full host outcome | 8 KiB / 12 KiB, nested host limits |

Nonempty tables require at least one page. Empty tables may still have pages.
For three relations there are at most 12 ordered binary tree shapes with labeled
leaves, 8 scan combinations and 9 join-method combinations: 864 raw candidates.
Remove disconnected, unavailable-index and non-fitting candidates. Enumeration
is complete **only for this declared family**. It does not prove a production
DBMS plan globally optimal. At least an all-sequential/nested plan is feasible.

All intermediate integer calculations stay below 2^53-1: at most two joins
multiply row estimates bounded by 10^6, and fixed scan charges are much smaller.
Q0/Q1 must measure transport and work bounds with worst-case sources, not only
the supplied examples. Do not enumerate plans in a reducer or on every preview.

## Assessment and result contract

The authoring envelope adds a baseline, a worked answer, bilingual explanation,
and one public goal to the engine exercise:

- **best:** any feasible plan with cost equal to the exhaustive minimum passes.
- **budget:** any feasible plan with cost <= the public max_cost passes.
  Preparation rejects an unreachable budget.

The Python preparation model computes the optimum, baseline facts and worked
facts. It verifies that the baseline is feasible and that the worked answer
satisfies the goal (and is optimal for best). Cost equality, not identity with
the worked tree, determines success. A feasible plan above the target receives
"Valid plan; target not reached." A memory violation receives feasibility feedback,
not invented execution output.

The engine analyzes one submitted plan, never chooses a goal or emits a grade.
Declare manifest revision 2 and a closed portable result-data schema with:

- format/model plus SHA-256 identities of the semantic exercise and canonical
  answer; labels and prose are excluded from semantic identity.
- Valid analysis: total cost and at most five node facts (node index, subset mask,
  output rows, row bytes, local/cumulative cost and hash workspace).
- Domain-invalid analysis: a bounded reason code and offending node, with no
  fabricated cost/trace. Reasons include invalid-tree, unknown-relation,
  duplicate-relation, missing-relation, disconnected-join, unavailable-index,
  hash-memory.
- Malformed JSON or shape errors use the supported syntax failure; operational
  failure/timeout uses host-supported status, never a failing grade.

Canonicalize using the host-compatible ASCII JSON rules; forbid duplicate keys,
non-finite values, unknown properties and booleans in integer fields. SHA-256
implementation must work on classroom LAN HTTP without crypto.subtle.
The complete actual host binding supplies namespace identity; do not rebuild an
incomplete seed-only namespace. Engine canonical equality/matches is not grading.

The lesson checks epoch, correlation, binding, model and exercise/answer identity,
plus exact node coverage, masks, costs and feasibility before using facts. These
small checks may use the independently implemented Python per-plan model; the
expensive reference enumeration is preparation-only. Invalid/unavailable output
cannot improve the student's grade.

## Packaging and ownership

| Proposed identifier | Purpose |
| --- | --- |
| Distribution / directory | texstage-query-plan / plugins/query-plan |
| Provider | io.github.stefanjdecker.queryplan |
| Engine | io.github.stefanjdecker.queryplan.cost |
| Content type | io.github.stefanjdecker.queryplan.challenge |
| Python package | texstage_query_plan |
| Style / namespace | texstage-queryplan-challenge.sty / queryplan |
| Command | \queryplanchallenge{item-id}{width}{height} |

The distribution, provider and engine identifiers are implemented in a portable
wheel. The content type, style and command remain design reservations; there is
no catalog release. The target wheel will later add lesson/UI modules and style.
Other lessons can already bind to the engine independently of the planned UI.

Reuse generic TeXStage SDK contracts: PreparedAuthoring/PreparedItem,
Evaluate/CancelEvaluation, evaluation_correlation, epochs, receipts, authenticated
context and audience views. Use the relational lesson as a pattern, without
importing its private modules, cost rules or mutable state. Do not require the
unfinished transaction lesson.

Texstage owns authentication, persistence, transport, job supervision, mounting,
asset serving and capability validation. The provider owns query semantics,
cost model, reference enumeration, lesson grading, controls and LaTeX content.
No query-plan route, database table, grade field or optimizer belongs in core.
No change to lecture-tools-next or course pins is needed.

The current host supports this design at de3351550f3553ca63023554521fbe84806ec94e
and the collection at 5f00b62f6292de01e4eca067c8acd96dddf67eb9.
These are local development baselines, not public release dependencies.
Q0 must verify the exact installed artifacts. A published compatible immutable
host pin remains a release gate.

### Review of the plugin system

No new plugin API is currently justified. Existing typed results, prepared
authoring, declared evaluation bindings and four role surfaces cover the activity.
Shared opportunities are a renderer-owned tree outline and a prepared reference
calculation pattern. Extract a versioned shared library only after two concrete
consumers establish the same interface; cross-provider browser imports are not
the shortcut. Keep teaching cost formulas out of generic tree widgets.

Test public cost-preview code without giving it private bindings or optimal-plan
lists. Public statistics make the answer derivable by a determined student; this
is a formative activity, not a secure high-stakes exam. Role filtering still
prevents accidental answer disclosure.

Use a self-contained generated engine entry, following the current worker
bundler. Preserve the actual policy:
```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```
Do not fetch a DB service, spawn evaluator child workers, add dynamic-code
permissions or relax CSP for Firefox/WebKit. Phone preview is a bounded direct
calculation of at most five nodes, not a separate worker or exhaustive search.

## Lesson state, privacy and lifecycle

Use separate phase/control versions and own-answer versions, not global revision
as a student's save guard. Submit carries the plan and expected own-answer
version; the host supplies actor identity. One current answer per actor; no
unbounded attempt history. A replacement cancels its previous pending evaluation
and queues a fresh one atomically with actor/request/slot correlation.
Retried requests preserve receipts. Late completions from older answers or epochs
have no effect. Queue-full and evaluator-unavailable preserve the draft and
produce an actionable status; they do not mean "wrong plan".

Target a 64-participant pilot, with <=2 KiB per actor slot including key and
reserved feedback, <=32 KiB shared state and <=176 KiB total persisted state.
These are design budgets to measure, not a capacity claim. Keep full node traces
out of all actor slots; store the compact plan and cost/status, recomputing at
most five nodes for one inspected/shared plan. Reserve feedback space before
accepting an answer. The 65th new actor is refused clearly while existing actors
may replace answers. All transitions must remain inside the host's 256-KiB cap
and each view inside 128 KiB, including ASCII escaping and effects.

| Surface | Before reveal | After reveal |
| --- | --- | --- |
| Participant | Public problem, baseline, own answer/status and local preview | Own goal feedback and worked explanation |
| Presenter controls | Counts, bounded roster, one inspected answer and private worked facts | Same plus aggregate goal results |
| Presenter overlay | Public problem; intentionally shared anonymous plan | Worked solution or selected plan |
| Projector overlay | Public problem; intentionally shared anonymous plan | Worked solution; no actor IDs or roster |

Private optimum/reference facts and explanations stay in private preparation/state,
not hidden HTML or public assets. Sharing identifies an actor and answer version
privately, projecting only an anonymous sanitized plan. Replacement/reset clears
a stale shared reference. Reset removes shared/feedback state. Revealing must not
publish the entire author source or evaluation binding.

Preserve local drafts, focus and tree selection through unrelated class updates.
For a newer save from the same actor's second device, offer keep draft/reload.
A reset/new epoch can arrive without a remount: mark the draft obsolete and require
explicit action; never resubmit automatically. Respect ctx.signal on teardown;
late imports and preview callbacks cannot revive removed items. Navigation need
not persist unsaved drafts, but should clearly show the saved version on return.

## Authoring and static editions

The frozen lesson envelope is format 1 with exercise, baseline, goal,
worked_answer and explanation fields. Its schema and the prepare_reference
helper validate the source and worked goal; see the
[v1 contract](query-plan-challenge-contract.md). The declared challenge
PreparedAuthoring hook generates all editions. The original draft schemas remain
design-history artifacts.

Use an explicit sidecar item with type
io.github.stefanjdecker.queryplan.challenge, and a JSON source below the master
deck directory. Preserve existing path confinement and dependency freshness.
Preparation validates the fixed query/statistics, enumerates the bounded family
once, checks both authored plans and generates all editions from that source.

The thin declared style wraps \texstageprepared. Exercise/handout/PPT material
shows the task, statistics, rule card, baseline and room for an answer. Solutions
show an optimal plan, arithmetic and a statement that ties are accepted. Live
reveal uses those same facts. Escape plain author text; do not execute author
strings as TeX or SQL. Test direct-pdfLaTeX exports and changed-source freshness.
Do not distribute private preparation directories as student packages.

## Worked evidence and remaining decisions

The [worked examples](query-plan-challenge/README.md) and checker exercise
selective/broad/empty scans, tied scan costs, small-input nested loops, library
join order, constrained hash workspace and invalid plans. Their exact values
are specification examples, not measurements of installed plugin behavior.

The engine/source schemas, canonicalization and identity payloads are frozen.
Q1 supplies the independent implementation, bag-semantics fixtures and actual
worker checks in three browsers. Q2–Q4 add prepared authoring, reducer/role
contracts, measured state/view budgets and accessible controls. Actual-phone
checks, classroom load evidence and cross-platform/hosted release checks remain Q5.

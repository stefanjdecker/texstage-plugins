# B+ Tree Operations Lab: v1 engine and classroom contracts

Status: engine, prepared authoring, classroom protocol and visual UI implemented
locally, 2026-11-07. Provider version 0.4.0 retains the B1 source/answer/result
semantics and content state schema 2. See the [B4 record](bplus-tree-b4-validation.md)
and [classroom guide](../bplus-classroom.md).

Public preparation contains format/title/prompt/exercise/interaction, with
interaction set to `classroom`. Worked answer, facts, explanation,
feedback policy and evaluation binding remain private in preparation. The
reducer projects authorized feedback and releases worked material only after
reveal. It never projects the full persisted state. Schema-1 sessions must be
replaced with a rebuilt bundle and a new session after the provider update.

## Exercise seed and page encoding

The fixed binding supplies this engine seed. The participant cannot replace
its task, capacities, tree or semantics through an answer.

```json
{
  "format": 1,
  "semantics": "bplus-operations-v1",
  "leaf_capacity": 3,
  "internal_capacity": 4,
  "tree": {
    "root": 0,
    "nodes": [
      {"id": 0, "kind": "internal", "keys": [20, 40], "children": [1, 2, 3]},
      {"id": 1, "kind": "leaf", "keys": [5, 10], "next": 2},
      {"id": 2, "kind": "leaf", "keys": [20, 25, 30], "next": 3},
      {"id": 3, "kind": "leaf", "keys": [40, 45], "next": null}
    ]
  },
  "task": {"kind": "insert", "key": 27}
}
```

All objects are closed. Task variants are `lookup/insert/delete` with `key`,
or `range` with `lower` and `upper` (inclusive, lower ≤ upper).
No other policy or client-selected mode is accepted in v1.

A leaf has exactly `id, kind, keys, next`; an internal page has exactly
`id, kind, keys, children`. The page list is sorted by ID, not leaf order.
In author sources, IDs are consecutive integers starting at zero in preorder,
and root is zero. This gives predictable labels without relying on dictionary
order. After operations, surviving IDs stay stable: never renumber a student's
in-progress diagram.

The next allocated ID is one greater than every previously allocated ID in
this operation. Split retains the original page as the left page, allocates
the right page, then (for a root split) allocates a new root. Merge retains the
left sibling and retires the right; IDs are not reused. Root collapse retires
the old root and preserves its sole child's ID. Consequently a final root need
not be zero and final IDs need not be consecutive.

Preparation/engine loading checks every invariant in the design: exact
separator minima, strict sorted unique leaf keys, one parent per nonroot page,
ordered disjoint child ranges, occupancy, equal leaf depth, exact leaf chain,
reachability, dimensions and numeric bounds. Traversals are iterative/bounded;
a cycle is an error, not recursion until a timeout. Reject duplicate JSON
object keys, booleans in integer positions, unknown properties, non-finite
numbers and values outside the declared range.

## Student answers

Answers have `format: 1` and no operation selector. Their shape is selected
by the bound task. IDs and keys are integers, not strings.

Point lookup:

```json
{"format":1,"path":[0,2],"keys":[20]}
```

For a lookup of 20 in the tree above, this is complete. An absent lookup returns
`"keys":[]`. An internal separator alone is not evidence of a found entry.

Range scan:

```json
{"format":1,"path":[0,2],"leaves":[2,3],"keys":[25,30,40]}
```

This answers the inclusive range [22,40] on the same tree.
Descend on the lower bound using equality-right routing. The first scanned
leaf is the last path node. Follow its `next` pointers until reaching the
first scanned leaf whose largest key is ≥ the upper bound, or the last leaf.
An empty root stops immediately. Return precisely the entries within the
inclusive interval, in order. Do not skip a visited leaf just because it
contributes no entries.

This is an intentionally specified scan procedure. It may inspect a leaf
whose first key exceeds the upper bound when the preceding leaf ended below
that bound. Do not claim it is the only possible database implementation.
Count logical index-page visits as `len(path) + len(leaves) - 1`; for point
lookup count `len(path)`. The root is not cached, and heap/data pages, prefetch,
physical I/O and elapsed time are outside this metric.

Insert/delete:

```json
{
  "format": 1,
  "path": [0, 2],
  "repairs": [{"op": "split", "node": 2, "left_count": 2, "separator": 27}],
  "separators": [{"node": 0, "keys": [20, 27, 40]}],
  "height": 1
}
```

The example inserts 27. Final leaves in link order are pages 1,2,4,3, holding
[5,10], [20,25], [27,30], [40,45]. The `separators` list covers **every** final
internal page, in ascending ID order, exactly once. For a leaf root it is empty.
The height is the number of edges from root to leaf. No final tree or user
declared “correct” flag is accepted.

## Update certificate state machine

1. Validate the whole answer's shape/budget. Check its exact root-to-leaf path
   against the bound key. A wrong path stops replay without mutating a different
   leaf and produces a domain-invalid path result.
2. Apply the single bound operation to that leaf. Duplicate insertion or absent
   deletion changes nothing and permits no repairs.
3. Recompute affected separator minima for routing. There may now be one pending
   overflow/underflow on the update path. Other occupancy exceptions are illegal.
4. Consume one repair for that pending page. It must name that page and satisfy
   the action's preconditions. Update parent pointers, separator minima and leaf
   links atomically; propagate at most one occupancy obligation upwards.
5. Finish only when the tree is stable and all repairs are consumed. Missing
   repairs mean incomplete; additional repairs mean invalid. Check global
   invariants and the exact operation key-set effect once more.
6. Compare the submitted final separator arrays and height to the replayed tree.
   These are prediction checks, not permission to mutate the tree.

Transient occupancy is part of this private replay state, not a valid submitted
source tree. Overflow is exactly one entry/child above maximum; nonroot
underflow is exactly one below minimum. Root contraction is handled immediately
after a merge leaves one child; an empty leaf root is valid. Never search using
a temporarily stale separator or expose a transient tree as a stable result.

| Repair encoding | Preconditions and effect |
| --- | --- |
| `{"op":"split","node":N,"left_count":c,"separator":k}` | N is the pending overflowing page. Split its ordered entries (leaf) or child pointers (internal) after c. Both resulting sizes must be legal. k must equal the right group's minimum key. Attach its new right page beside N in the parent, or create a root. |
| `{"op":"borrow","node":N,"sibling":S}` | N is the pending underfull nonroot page. S is an immediate left/right sibling under the same parent and has more than its minimum. Move the donor's adjacent boundary entry/child; both pages must then be legal. |
| `{"op":"merge","node":N,"sibling":S}` | N is the pending underfull nonroot page. S is an immediate same-parent sibling and the combined contents fit in one page. Concatenate in tree order into the left page, repair leaf links if needed, and remove the right child from the parent. |

For an internal split, recompute the two groups' internal separators.
The boundary promoted to the parent is not an internal separator inside either
group. For internal borrow/merge, move/concatenate child lists and derive all
separators, including the parent boundary that becomes an internal separator
on merge. For a leaf split, the copied boundary remains a record entry.

Both legal split sizes and either legal donor/merge neighbour are accepted.
There is no mandatory “borrow left first” grading policy. The suggested worked
solution uses the smallest legal left split, left donor before right donor,
then left merge before right merge; an explicitly authored different legal
solution is also allowed.

An incorrect split separator is an invalid repair at that position. Incorrect
final separator/height predictions on an otherwise legal replay have a complete
certificate with failed claim checks. This distinction gives useful feedback
without silently correcting an invalid student step.

## Engine facts, identity and lesson acceptance

Use `start/load/evaluate/dispose` with fresh submission state and a single
host-owned evaluation binding named `analysis`. No equality references are
needed. Engine options are empty in v1; the seed includes all semantics.

Keep the plain-text summary at most 160 ASCII characters; localisation belongs
in the lesson's renderer, using structured reason codes.
Successful analysis uses the existing host envelope:

```json
{
  "status": "ok",
  "canonical": "bplus-v1:<exercise-sha256>:<answer-sha256>",
  "summary": {"kind": "text", "text": "Complete repair certificate; predictions checked."},
  "data": {
    "format": 1,
    "exercise": "<64 lowercase hex characters>",
    "answer": "<64 lowercase hex characters>",
    "operation": "insert",
    "replay": {"state": "complete", "checked_repairs": 1},
    "claims": {"path": true, "keys": null, "separators": true, "height": true},
    "final": "<the bounded flat tree object>",
    "metrics": {
      "height_before": 1, "height_after": 1, "leaf_count": 4,
      "splits": 1, "borrows": 0, "merges": 0
    }
  }
}
```

Angle-bracket values above are illustrative placeholders, not literal valid
results. The closed portable result schema has separate complete-read,
complete-update and incomplete/invalid variants:

- Complete reads have `read: {path, leaves, keys, page_visits}` with exact
  visits/results. A point lookup lists its single leaf. `claims.keys` compares
  the submission; update-only claims are null.
- Complete updates return the final flat tree and bounded structural counts.
  No sequence of full tree snapshots crosses the result boundary.
- Incomplete/invalid replay returns `checked_repairs`, a bounded reason enum,
  and the first failing action/path index or pending node when applicable.
  It must omit final-tree and complete-operation metrics. Reasons include
  `wrong-path, wrong-scan, missing-repair, extra-repair, wrong-pending-node,
  illegal-split, wrong-separator, illegal-donor, illegal-merge`.
- Malformed participant answer JSON/shape uses `syntax`; invalid seed/options
  fail during engine loading and become host `error`. Answer/work-budget refusal uses
  `refused`; internal engine failure uses `error`. The host owns `timeout`.
  Failure envelopes contain only `status`. Missing evaluators and queue failures
  are operational states, not any of these domain claims.

The lesson accepts exactly: a complete certificate, all applicable claim checks
true, matching task/exercise/answer identity and the correct current binding,
epoch and correlation. It checks result coherence (node/repair counts and
bounds, identities and required claims); it does not trust summary prose or
`matches`. A well-formed result schema alone is not an answer-binding check.

Exercise identity hashes canonical ASCII JSON containing only the complete
semantic seed. Answer identity hashes the closed parsed answer with sorted
object keys and significant array order. Labels, explanation language, actor,
time, request ID and layout coordinates are excluded. Do not renumber action
page IDs or sort path/repair/key arrays to make an invalid answer valid.
Semantic format and provider/result namespace prevent cross-version reuse.
Use the actual persisted binding, including its engine key when present.
Do not require `crypto.subtle` on ordinary classroom HTTP.

Schema files for engine data and audience views must use the actual host's
restricted portable profile: closed bounded objects/arrays, enums and acyclic
local references; no `pattern`, `$id` or remote references. Validate digest
syntax and cross-field invariants semantically. Source/command schemas are a
separate profile. Both installed host validators must accept real results,
including the largest allowed successful and failed analyses.

## Bounds

Engine and classroom slot/state/view limits below are enforced in B3.
The [B3 evidence](bplus-tree-b3-validation.md) measures serialized storage and
actual protocol views; these are not classroom-performance claims.

| Resource | Limit / rule |
| --- | --- |
| Key / page ID | Integer −9999…9999 / integer 0…63 |
| Initial tree | At most 40 entries, 31 pages, height 0…2 |
| Stable result | At most 41 entries, 35 pages, height 0…3 |
| Capacities | L and F independently 3…6 |
| Update | One bound operation, at most 3 repairs |
| Answer arrays | Path ≤3; range leaves ≤20; final internal separator records ≤10 |
| Canonical answer | ≤1800 ASCII bytes after normalisation; host effect ceiling is 2000 characters |
| Engine seed | ≤12 KiB canonical ASCII JSON; strict finite tree validation |
| Lesson envelope | ≤20 KiB, independent validation/depth budget; no arbitrary assets in v1 |
| Typed facts / complete outcome | Target ≤6 KiB / ≤8 KiB; hard host limits 8 KiB / 12 KiB |
| Shared persisted state | ≤16 KiB including selections and counts; no copied class-wide tree traces |
| Actor slot | ≤4 KiB including the 64-character actor digest key, saved answer, versions, pending identity and reserved feedback |
| Admitted actors | Initial ceiling 48; replacement still possible at capacity |
| Whole state / transition | Provider targets ≤224 KiB / ≤240 KiB including effects; host transition ceiling 256 KiB |
| Surface view | Target ≤48 KiB; host ceiling 128 KiB; one selected attempt rather than every answer |
| Replay computation | 20,000 charged work units across browser load/evaluation; all loops also bounded by pages/entries/3 repairs |

A valid starting tree of height two can grow to height three through at most
three splits and a new root. Source limits and resulting topology, not just
per-field schema maxima, enforce these bounds. A valid update cannot contain
10 arbitrary maximal internal nodes independently of the leaf/page limits.
An authored checkpoint starting at height three is refused in v1 even when a
preceding item produced it; long sequences must stay within the input bounds.

Key the provider's actor-slot map by SHA-256 of canonical ASCII JSON
`["bplus-actor-v1", authenticated_actor]`, not by the potentially much longer
escaped actor string. Keep this digest private; it remains a pseudonymous
identifier. Compute it again from the authenticated event/view context, never
from a participant payload. The host retains the real actor for receipts/jobs;
the SDK correlation helper still receives that original actor. The private
presenter selection uses this bounded slot key and answer version.

Count bytes with the host's ASCII-escaped canonical JSON, including quoting a
saved answer string, digest keys, feedback, effect records and all envelope
fields. Reserve feedback space **before** accepting an answer. Refuse at the
provider capacity without changing limits or truncating facts. B3 tests measure the
reserved slot and complete state/views, including non-ASCII authenticated actors. A smaller
certificate cap or actor ceiling is preferable to widening the host transport.

The work counter and browser deadline are different safeguards. Each page
inspection charges one unit plus its keys and (for internal pages) child
pointers. Rebuilding/routing charges one plus entries/children visited; minimum
descent charges visited pages; repairs charge one plus the items they move or
repack. Browser loading and analysis share a 20,000-unit budget. The independent
Python traversal can charge a different total, with the same cap. These are
bounded logical work units, not CPU instructions or database costs.

Raw seed JSON is capped at 32 KiB before parsing, then 12 KiB canonical ASCII.
Answer text is capped at 2,000 JavaScript characters, then 1,800 canonical ASCII
bytes. Both parsers cap nesting at 16 and JSON structure at 8,192 visits, reject
duplicate keys and accept integer number tokens only (no decimals/exponents).
The Python model independently rejects booleans in integer fields. Result
facts are capped at 6 KiB and the engine result at 8 KiB, within the host's
8/12-KiB limits. Parser/serialization/hashing costs have these separate size
bounds; the work counter is not a complete instruction counter.

The result's `replay.at` is a zero-based failing path/scan/action index;
`replay.node` is the expected/pending page or null when no page applies.
Incomplete/invalid variants never include a final tree or completed-operation
metrics. The installed probes test work refusal, real result limits and the
unchanged host timeout/worker recovery. A storage calculation is not a
throughput test.

## Authoring envelope

A lesson source such as [the insertion example](../../examples/bplus/activities/insert.json) wraps the seed above:

```json
{
  "format": 1,
  "title": {"en": "Make room for catalogue entry 27"},
  "prompt": {"en": "Insert 27. Choose repairs, then predict all separators and the height."},
  "exercise": "<the exercise object above>",
  "worked": {
    "answer": "<the insert answer object above>",
    "explanation": {"en": "Split the full leaf; 27 is copied into its parent and stays in the right leaf."}
  },
  "feedback": "on-reveal"
}
```

Replace placeholder strings with objects; the checked fixture contains a real
[example envelope](bplus-tree/insert-leaf.lesson.json).
The required feedback field accepts `on-reveal` and `immediate`. Mathematical
feedback follows that policy for the submitting student. Operational feedback
is visible immediately; it never labels an answer incorrect.
The authoring hook independently checks the worked answer and derives fragments,
rather than accepting an unchecked expected final tree.

Activity sidecar and placement:

```json
{
  "format": 1,
  "language": "en",
  "items": [
    {"id": "insert-leaf", "type": "io.github.stefanjdecker.bpluslab.tree",
     "source": "activities/insert-leaf.json"}
  ]
}
```

```tex
\usepackage{texstage-bplus-tree}
% Within a frame, after normal TeXStage setup:
\bplustree{insert-leaf}{.94\linewidth}{.65\textheight}
```

The sidecar and sources stay below the master deck directory; current host
confinement, explicit profile enablement and lock/payload checks apply.
Public preparation includes the task/tree/capacities and UI policy. Private
preparation includes the worked certificate, explanation and derived results.
The evaluation seed needs only the public mathematical exercise, not a hidden
reference or copied worked answer. Synthetic source examples are public in the
repository; that does not justify leaking a teacher's unrevealed solution in
a built presentation.

## Commands and view contracts

Implemented `submit-answer` for participants (current phase token, own base
answer version, structured answer). The reducer uses the authenticated actor,
not a payload identity. Presenter messages are `open, close, reveal,
select-answer, share-answer, clear-share, replay-step` guarded by control
version; selected answers also carry their version. All use the host's latest
revision policy with explicit domain guards. Host `_reset` provides epoch reset.

`replay-step` selects a bounded step in the revealed worked solution or current
explicitly shared answer. It cannot mutate an answer, expose a private selection
or submit work as a participant. Public aggregates contain counts only; saved
feedback and solution detail follow phase/policy. Before reveal, sharing shows
the submitted predictions without correctness labels or silently replacing
them with the computed answer. Private inspection remains separate.
Command schemas cap IDs,
indices and answer shape before reducers execute.

There are exactly four surface/view schemas: `participant-input`,
`presenter-controls`, `presenter-overlay` and `projector-overlay`. The phone gets
its own saved answer/status; controls get bounded counts and at most one
selected inspection; projector gets no actor keys, private inspection data,
correlation IDs or unshared attempts. The full state is never a view.

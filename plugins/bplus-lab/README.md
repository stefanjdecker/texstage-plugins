# B+ Tree Operations Lab

Experimental engine and prepared LaTeX lessons (B0–B4) for point lookup, inclusive
range scans, insertion and deletion. It verifies each search path and
split/borrow/merge, including internal repairs and root growth/contraction.
Alternative legal repairs can have different correct final trees.

The engine returns typed facts. It does not use reference equality as a grade.
Version 0.4.0 adds structured phone editing, undo/redo and a local replay preview,
English/German feedback, private presenter inspection, anonymous sharing and
stepwise projector replay. Students submit explicit answers; drafts and previews
do not send classroom commands. See the [classroom guide](../../docs/bplus-classroom.md).
The physical-phone pilot and release measurements remain open.
See the [author guide](../../docs/bplus-lesson.md) and
[example decks](../../examples/bplus/README.md).

| Component | Identity |
| --- | --- |
| Distribution / Python module | `texstage-bplus-lab` / `texstage_bplus_lab` |
| Provider | `io.github.stefanjdecker.bpluslab` |
| Engine | `io.github.stefanjdecker.bpluslab.operations` |
| Prepared content type | `io.github.stefanjdecker.bpluslab.tree` |
| Style / command | `texstage-bplus-tree.sty` / `\bplustree` |
| Contract / semantics | `bplus-operations-v1` |

Use the matching experimental TeXStage host with manifest revision 2 and typed
result contract revision 2. The development dependency lower bound is not a
published compatibility pin. Uploading a source file never installs or enables
this provider.

## Build and verify

Use a fresh Python 3.12+ environment with the compatible host wheel and its
hash-locked development requirements. From the collection root:

```sh
npm ci --ignore-scripts
python maintenance/build_bplus_schemas.py --check
python maintenance/build_bplus_lesson_schemas.py --check
npm run check:workers
python maintenance/build_wheels.py --package bplus-lab
python -m pip install --no-deps dist/texstage_bplus_lab-0.4.0-py3-none-any.whl
python -m pytest plugins/bplus-lab/tests -q --basetemp=artifacts/bplus-tests
python maintenance/bplus_probe.py --output artifacts/bplus-lab
npx playwright install chromium firefox webkit
node maintenance/bplus_browser.cjs artifacts/bplus-lab
```

The default browser is Chromium. Use `BROWSER=firefox` or `BROWSER=webkit` for
the other families; PowerShell uses `$env:BROWSER='firefox'`. A local Chrome
channel may be selected with `TEXSTAGE_BROWSER_CHANNEL=chrome` for Chromium
only. Clear that override for Firefox/WebKit.

Regenerate schemas with `python maintenance/build_bplus_schemas.py` and workers
with `npm run build:workers` after their sources change. Commit generated
resources with their sources. End-user installation needs neither Node nor a
bundler.

The build checks wheel/sdist payload parity. Tests use installed files and the
actual host validators. Browser checks retain the production worker CSP and
active connection/child-worker/dynamic-code restrictions, invalid-result
rejection, timeout cleanup and recovery. Local passes do not establish hosted
CI, cross-platform transfer or classroom capacity.

## Example operation

The seed is one immutable exercise; options must be `{}`:

```json
{
  "format": 1,
  "semantics": "bplus-operations-v1",
  "leaf_capacity": 3,
  "internal_capacity": 4,
  "tree": {"root": 0, "nodes": [
    {"id": 0, "kind": "leaf", "keys": [5, 10, 20], "next": null}
  ]},
  "task": {"kind": "insert", "key": 15}
}
```

A root-leaf split answer is:

```json
{
  "format": 1,
  "path": [0],
  "repairs": [{"op": "split", "node": 0, "left_count": 2, "separator": 15}],
  "separators": [{"node": 2, "keys": [15]}],
  "height": 1
}
```

The result has leaves 0=[5,10] and 1=[15,20], with new root 2=[15].
The copied separator remains an entry in leaf 1. Facts include the completed
replay, prediction checks, final tree and structural counts.

An unfinished repair sequence produces `incomplete` replay; an illegal donor
produces `invalid` replay with a reason. An incorrect height on a legal replay
is a failed height claim. These differ from operational worker failure.

The independent Python model accepts the same seed and answer:

```python
from texstage_bplus_lab.model import analyze
facts = analyze(seed, answer)
```

This does not submit a classroom answer. The prepared hook checks a worked
answer with this model. The classroom reducer checks complete replay, applicable
claims, exercise/answer identity and the entire persisted job binding. Independent
replay verifies the facts for the submitted answer, including alternative repairs.

## Model and limits

Leaf capacity counts entries; internal capacity counts child pointers.
Both range from three through six. Nonroot minimum occupancy is the ceiling
of half that capacity. A root is a leaf (possibly empty) or has at least two
children. All leaves have equal depth.

Keys are unique integers −9999…9999. Separators are exact minima of right
subtrees, so equality routes right. Leaves are linked in key order.
Duplicate insertion and missing-key deletion are no-ops. Only immediate
same-parent siblings can borrow/merge. Both legal split partitions and donor
directions are accepted.

V1 supports at most 40 initial entries, initial height two, one operation and
three repairs. A terminal result may have 41 entries and height three, but
cannot become another source outside the input bounds. Inputs use integer
JSON tokens; booleans, decimal/exponent tokens, duplicate object keys, unknown
fields and invalid trees are rejected.

Ranges have inclusive bounds. Follow leaves until the first leaf whose maximum
meets/exceeds the upper bound or the chain ends. Logical page visits exclude
heap pages, caches and physical disk behaviour.

See the [contract](../../docs/design/bplus-tree-contract.md),
[design](../../docs/design/bplus-tree.md),
[implementation plan](../../docs/design/bplus-tree-plan.md),
[B1 engine record](../../docs/design/bplus-tree-b1-validation.md) and
[B2 authoring record](../../docs/design/bplus-tree-b2-validation.md) and
[B3 classroom record](../../docs/design/bplus-tree-b3-validation.md) and
[B4 visual UI record](../../docs/design/bplus-tree-b4-validation.md).
Tests cover the 30 hand-specified cases, small-domain permutations, seeded
capacity combinations, alternative repairs, malformed inputs, large valid
results, work refusal and binding identities.

Duplicate-key buckets, variable-size pages, bulk loading, concurrency and
recovery are outside this model. The content type now uses state schema 2 and
four closed audience views, with structured phone and presenter renderers.
Feedback releases immediately or on reveal, as authored. Worked answers remain
private until reveal; explicitly shared attempts show only submitted predictions
before reveal. A provider update requires a rebuilt bundle and a new session;
schema-1 sessions are not migrated in place.

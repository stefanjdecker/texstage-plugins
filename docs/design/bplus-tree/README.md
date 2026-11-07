# Worked design examples: B+ tree operations

These are the original public synthetic design fixtures. The
[prepared example decks](../../../examples/bplus/README.md) now turn selected
cases into usable LaTeX exercises and solutions. The
[engine](../../../plugins/bplus-lab/README.md) now checks their complete repair
certificates; interactive classroom state and interfaces remain planned. The [design](../bplus-tree.md),
[draft contract](../bplus-tree-contract.md) and
[implementation plan](../bplus-tree-plan.md) explain the proposed activity.

[fixtures.json](fixtures.json) contains 13 starting models, 30 worked cases
and eight invalid trees. [insert-leaf.lesson.json](insert-leaf.lesson.json)
is a complete authoring envelope for one of those cases, including
English/German text. Its shape now has a shipped lesson-envelope schema;
the hook and `\bplustree` command now implement it. See the
[author guide](../../bplus-lesson.md).

## The library example

Index catalogue entries 5, 10, 20, 25, 30, 40 and 45:

```text
                       page 0 [20 | 40]
                        /      |      \
     page 1 [5,10] → page 2 [20,25,30] → page 3 [40,45] → end
```

Leaf capacity is three entries; internal capacity is four child pointers.
Separators are the exact minimum of the right subtree. Key 20 therefore takes
the right branch from separator 20 and is found in leaf 2.

For range [22,40], descend through pages 0 and 2, then follow leaf 2→3.
Return 25,30,40; count three logical index-page visits. For range [11,19],
visit 0→1 and then leaf 2 even though the answer is empty. The plugin's scan
rule makes that stopping check explicit; this is not a physical disk-I/O estimate.

Insert 27: leaf 2 overflows. Split it into [20,25] and [27,30], allocate page 4
for the right half and copy 27 into the parent. Root separators become
[20,27,40], and the leaf chain becomes 1→2→4→3. Numeric page order is not leaf
order. That distinction catches a common rendering and validation mistake.

Delete 20 instead: leaf 2 becomes [25,30] and still meets its minimum occupancy.
No borrowing or merging occurs, but the root separator changes from 20 to 25
under this model's exact-minimum convention.

## What the cases cover

| Case group | Main examples |
| --- | --- |
| Point/range reads | Separator equality, missing key, cross-leaf range, gap with an extra visited leaf, upper endpoint at the last entry, beyond-tree range, empty tree |
| Simple updates | Insertion with space, duplicate insertion, absent deletion, empty-root insertion, last-entry deletion |
| Leaf balancing | Nonroot split, root-leaf split, borrowing from both directions, merging to either neighbour, root collapse |
| Internal balancing | Internal/root split with two legal partitions; three-level split; internal borrowing from both directions; internal merge and root shrink |
| Separator predictions | Leaf-minimum change without underflow; change propagated to an ancestor through a first child |
| Capacity/alternative answers | L=4 root-leaf split as 2+3 or 3+2; F=4 internal overflow as 2+3 or 3+2 |

The three-level insertion starts with root separators [5,9,13].
Inserting 22 requires splits at leaf 14, internal page 10 and root 0;
new root 18 has separator 9 and height three.
The internal-merge deletion starts at height two, removes 5, merges leaves
and their underfull internal parent, and contracts to root page 1 at height one.

Alternative cases deliberately have different valid final shapes. Runtime
grading must accept them based on checked repairs and predictions, not canonical
equality to one worked tree.

The eight invalid snapshots test an inexact separator that would still route
searches correctly, a skipped leaf link, underfull leaf, boolean key, repeated
child, cycle, orphan and unequal leaf depths.

## Reproduce the design checks

From the collection root, with ordinary Python 3.12+ and no installed provider:

```console
python maintenance/check_bplus_design.py
```

After intentionally changing reviewed fixtures/checker, regenerate the record:

```console
python maintenance/check_bplus_design.py --write
```

The checker verifies starting and expected tree invariants, source preorder
IDs, exact search/scan expectations, update key-set effects, predicted final
separators/heights and rejection reasons for invalid snapshots. It also checks
that the lesson envelope matches the worked insertion. A check without
`--write` rejects a stale [validation record](validation.json).

The checker does **not** replay split/borrow/merge certificates. Their hand-specified action
lists are now additionally verified by the installed engine suite, documented
in the [B1 validation record](../bplus-tree-b1-validation.md). A correct final snapshot does not prove a legal update.
The checker also does not validate production JSON schemas, load an installed
wheel, exercise the host, open a browser or establish classroom capacity.

## Encoding checks

The checker constructs conservative **shape-only** byte probes; those intentionally
use repeated IDs/keys and are not valid trees. They bound common representation
fields without masquerading as semantic examples.

| Probe, canonical ASCII JSON | Bytes |
| --- | ---: |
| Maximal draft answer shape | 752 |
| Update facts with 35 maximal internal-page objects | 3,861 |
| Complete engine result with 160-character summary | 4,233 |
| Actor slot including digest key and 768-byte feedback reserve | 2,005 |
| Forty-eight full 4-KiB slots plus 16-KiB shared-state budget | 212,992 |

A 256-character non-BMP actor string alone encodes to 3,074 bytes. The proposed
provider therefore uses a private 64-character digest as its state-map key,
while host receipts/jobs and SDK correlations retain authenticated identity.
Do not assume one character is one JSON byte.

These numbers support the proposed small representation. Maximum **valid**
runtime outputs, actual full state/effects/views and both host validators
remain B0/B3 gates. They do not prove that 48 simultaneous participants will
receive feedback quickly.

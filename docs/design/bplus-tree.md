# B+ Tree Operations Lab: plugin design

Status: B0–B4 software implemented locally, 2026-11-07. Version 0.4.0 supplies
the engine, bilingual prepared lessons, authoritative submissions/feedback and
structured phone/presenter views. The physical-device pilot and release gates
remain open. See the [author guide](../bplus-lesson.md),
[classroom guide](../bplus-classroom.md), [B4 evidence](bplus-tree-b4-validation.md),
[contract](bplus-tree-contract.md) and [plan](bplus-tree-plan.md).

## 1. What students and lecturers can do

Students see a small database index and carry out one operation: find a key,
scan a key interval, insert an entry or delete an entry. They choose the search
path, repair overflowing or underfull pages, and explain the resulting
separator keys. The lecturer can collect attempts, inspect misconceptions,
share an anonymous attempt and step through a worked solution.

The activity teaches why an index avoids a table scan, why a range query
follows linked leaves, and how balancing preserves a shallow search tree.
It is a bounded teaching model, not a storage engine, SQL executor or database
performance simulator. Point/range lookup and insert/delete with split/merge
are standard B+ tree operations; production implementations add choices such
as buffering and concurrency. See the
[CMU database project overview](https://15445.courses.cs.cmu.edu/fall2026/project2/).

The first classroom release covers all four operations. Each item has one
immutable starting tree and one task. A longer insertion/deletion sequence is
authored as several checkpoint items, so students do not inherit someone else's
answer or need to finish one item to understand the next.
A terminal cascade example may grow to height three; chaining another operation
from that result is outside v1's initial-height bound.

| Task | Student contribution | Main learning check |
| --- | --- | --- |
| Point lookup | Root-to-leaf path; key found or absent | Separator equality routes right; internal copies are not records |
| Inclusive range scan | Initial descent; consecutive leaf visits; returned keys | Boundary handling, leaf links and stopping condition |
| Insert | Descent; split choices; final internal separators and height | Leaf copy-up, internal promotion and root growth |
| Delete | Descent; borrow/merge choices; final separators and height | Occupancy, adjacent siblings, cascading repair and root shrink |

The examples use integer catalogue numbers for a fictional lending library.
A key stands for one index entry with an implicit record reference. No real
student records, existing lecture files or private media are needed.

## 2. An explicit teaching model

Different books and systems use “order” differently and may choose different
deletion policies. Display the actual capacities on every exercise:

- `leaf_capacity = L`, between 3 and 6: at most L entries per leaf.
- `internal_capacity = F`, between 3 and 6: at most F child pointers per
  internal page, hence at most F−1 separator keys.
- A nonroot leaf has at least `ceil(L/2)` entries; a nonroot internal page
  has at least `ceil(F/2)` children.
- An internal root has 2 through F children. An empty tree is a single empty
  leaf root. All leaves are at the same depth; height counts edges.
- Keys are unique integers from −9999 through 9999. Every record entry occurs
  in exactly one leaf, in increasing order.
- Children partition increasing, disjoint key ranges. Separator i is **exactly
  the minimum key in child i+1's subtree**. Equality takes the right branch.
- Leaves form one forward chain in tree order, ending in `null`. Every page
  is reachable exactly once; cycles, shared children and orphan pages are invalid.

Default demonstrations use L=3 and F=4. Separate capacities avoid presenting
leaf entries and internal child pointers as the same thing. The model uses
immediate rebalancing after deletion. The
[textbook's indexing chapter](https://www.db-book.com/slides-dir/PDF-dir/ch14.pdf)
illustrates redistribution, merging and root contraction. Berkeley's
[course notes](https://cs186berkeley.net/notes/note4/) instead simplify deletion
by allowing underfull pages; this plugin deliberately does not use that policy.

The exact-right-minimum rule is also an explicit choice: other B+ tree variants
may retain a separator that still partitions the key ranges after deletion.
A stale separator is wrong **under this exercise's convention**, not proof
that every real index using it is broken.

Duplicate insertion and deletion of an absent key are successful no-ops.
Their search path still matters, and any proposed structural repair is wrong.
V1 does not support duplicate-key buckets, composite/text keys, NULLs,
variable-size disk pages, B-link trees, concurrent transactions, WAL/recovery,
bulk loading, fill factors or a buffer cache. Those require explicit later
semantics, not extra controls on this model.

## 3. Concrete classroom experience

The projector first shows the task, capacities, starting tree and a short
legend distinguishing entries, separators, child pointers and leaf links.
A larger root does not conceal the exercise beneath an opaque overlay.
The presenter introduces the example, opens submissions and later closes them.
Revealing the answer is separate from closing.

On a phone, students first tap a child or use an equivalent labelled list to
build the path. They can backtrack locally. For updates, the chosen operation
is applied to the reached leaf once the draft path is submitted to the local
stepper. The student chooses a repair for the highlighted pending page:
split at a boundary, borrow from an adjacent sibling, or merge with one.
They then enter/check the final separators and predict the height.
Point/range tasks ask for the found entries and, for a range, the visited leaves.

The editor is a structured activity, not a JSON form. Each repair has a short
explanation area and an inspectable before/after view. The local visualisation
shows the consequences of the student's choices; it does not automatically
select a correct repair or fill in the final separator answers. Syntactic
constraints and draft preview are available before submission. Authoritative
saved feedback is separately labelled and follows the lesson's release policy.

A worked insertion illustrates the intended interaction:

```text
Before, L=3 / F=4:
             [20 | 40]              root 0
            /    |     \
     [5,10]  [20,25,30]  [40,45]     leaves 1,2,3

Task: insert 27.
Path: 0 → 2.
Leaf 2 temporarily contains [20,25,27,30].
Choose a split after two entries; copy separator 27 to the parent.

After:
          [20 | 27 | 40]
         /    |     |    \
    [5,10] [20,25] [27,30] [40,45]
```

The solution explains why 27 remains in the new right leaf. A later internal
split contrasts this with promoting a boundary between child groups; that
boundary is not retained as an internal separator in either new group.

No automatic timed animation is required. Presenter and student can advance,
go back and inspect each step; optional animation respects reduced motion.
A projector replay cursor is presenter-controlled. Phone draft cursors remain
local so a lecturer's navigation cannot destroy an unfinished attempt.

The presenter sees saved/pending counts and a compact distribution of errors
(e.g. wrong branch, missing repair, stale separator). Inspect one attempt at a
time. Sharing requires an explicit action and removes actor identity.
If that attempt changes, clear the share rather than displaying a different
answer under the old selection.

## 4. Verify legal operations, not a reference tree's shape

An update answer is a short **replayable certificate**, not a submitted picture
or arbitrary final tree. It contains the descent, repair choices, final internal
separator predictions and final height. The engine replays the permitted
actions against the fixed starting tree.

After the initial insert/delete, precisely one page may need occupancy repair.
Repair proceeds upwards. A split repairs that page and can overflow its parent;
a merge repairs it and can underfill its parent. Borrowing resolves underflow
without changing the parent's child count. Root creation/contraction is
automatic within the corresponding action and is shown as an explicit
explanatory checkpoint. The height prediction assesses its consequence.

Only immediate siblings with the same parent may lend or merge. Borrow exactly
one boundary entry/child from a sibling that remains above its minimum.
A merge is legal when the pair fits; it keeps the left page's identity.
A split partitions contiguous entries/children into two legal sizes; the
student supplies the predicted promoted/copied separator. No redistribution
before insertion splits, arbitrary subtree moves or proactive merges are in v1.

Several choices can be correct. For example, an internal overflow of five
children at F=4 can split 2+3 or 3+2; both are accepted. Either adjacent donor
can be used if it can lend. A legal merge can be accepted even if a different
sibling could have lent. The worked solution picks a reproducible choice but
does not define the only valid answer.

The engine checks each action's preconditions, key conservation, page links,
occupancy obligations and termination. Completing the final key set alone is
insufficient: an invalid intermediate repair must not be rescued by a plausible
final picture. Conversely, a valid alternative must not fail because its page
layout differs from the example.

Separators are maintained internally as derived routing metadata during replay.
Students predict all final internal separator arrays; they do not manipulate
temporarily stale routing pointers. This deliberately scopes v1 to **choosing
structural repairs and understanding separator changes**, rather than emulating
every low-level pointer assignment. A deletion that changes a subtree minimum
without causing underflow is still assessed.

Report malformed input, incomplete certificate, illegal action, incorrect
prediction and evaluator failure separately. A complete legal certificate can
have an incorrect separator/height claim. The engine reports these facts;
the lesson applies the acceptance rule. Do not use the host's `matches` flag:
it denotes reference canonical equality, which is inappropriate here.

## 5. Ownership and package identity

The distribution, engine, prepared content type and style below are implemented.
The content type currently has state schema 1, an empty read-only state and
transparent presenter/projector overlays. Classroom phases, submissions and
controls remain planned and require a new state-schema revision.

| Component | Identity |
| --- | --- |
| Distribution/directory | `texstage-bplus-lab` / `plugins/bplus-lab/` |
| Python package | `texstage_bplus_lab` |
| Provider | `io.github.stefanjdecker.bpluslab` |
| Engine | `io.github.stefanjdecker.bpluslab.operations` |
| Content type | `io.github.stefanjdecker.bpluslab.tree` |
| Style / command | `texstage-bplus-tree.sty` / `\bplustree{id}{width}{height}` |
| Versioned semantics | `bplus-operations-v1` |

One distribution contains two capabilities and the optional thin style.
The pure engine has no classroom state or grading policy. The lesson owns
authoring, feedback policy, phases, actor answers and audience views.
TeXStage continues to own authentication, receipts, epochs, job supervision,
validated transport, mount lifecycle and resource/pin enforcement.

Use plugin API 1, manifest revision 2 and the existing typed-result contract.
An uploaded deck, style or JSON file must never install or enable code.
No provider is added to the catalog until an immutable reviewed release exists.

The worker is generated as a self-contained ES module from owned source
modules. Keep the existing CSP unchanged:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Do not import the relational plugin's private modules or add a B+ tree route
to the host. Similar lifecycle code is an implementation pattern, not permission
to couple the providers. Extract a generic helper only if a demonstrated
cross-provider need warrants a separate reviewed change.

## 6. Authoring, static outputs and accessibility

An author writes a lesson envelope: title/prompt, the engine exercise,
one worked certificate, explanation and feedback policy. Preparation validates
the starting tree and worked answer, then derives public live data, private
solution material and exercise/solution fragments from that one source.

An explicit activity sidecar binds item/type to source. The provider's style
wraps `\texstageprepared`. The [contract examples](bplus-tree-contract.md#authoring-envelope)
show the supported JSON and LaTeX. The [author guide](../bplus-lesson.md)
provides installation, enablement, examples and output commands.

Handouts show the task, starting tree and answer space. Solutions show the
checked operations, final tree and explanations. Static PowerPoint retains
the exercise diagram. Long traces belong in separate worked-solution pages
or explicit checkpoint slides, not illegible miniature diagrams. Build live,
handout, solutions, static PowerPoint and local direct-pdfLaTeX from the same
preparation identity; reject stale input/assets.

Use a shared deterministic layout model with a browser SVG renderer and a
LaTeX/TikZ renderer. Neither renderer executes user-supplied markup. Package
the required style resources and document the TeX dependencies. Graphviz,
a remote drawing service and arbitrary shell escape are unnecessary.

A 320-pixel phone cannot display 30 pages legibly at once. Show the focused
page, parent context and possible siblings, with a separate overview.
Provide a labelled outline/table alternative with entries, child ranges and
next-leaf links. Every action is possible with keyboard buttons/forms; dragging
is optional. Use visible focus, adequate touch targets, text labels in addition
to colours, zoom/reflow, reduced motion and English/German strings. Test
screen-reader announcements for changed pages and pending feedback.

## 7. State, privacy and bounded work

Use introduce/open/closed/revealed phases, phase/control versions and per-actor
answer versions. Unrelated submissions must not invalidate a student's draft
or presenter control. A same-actor update on another device prompts “load saved
answer” or “keep draft”; it does not auto-submit. A reset can arrive on an
existing mount, so epoch change must clear obsolete feedback and offer explicit
draft handling. Navigation away disposes listeners and preview work.

By default save during open, assess asynchronously, and release correctness
when revealed. Authors may choose immediate practice feedback; that is part of
the prepared lesson policy, not a participant override. Closing accepts no new
submissions but can finish already accepted work. Reopen preserves answers and
hides revealed material again only if it was not already released; therefore
v1 permits closed→open but **requires reset after revealed**.

Use the SDK's actor/request/slot correlation, `Evaluate` and `CancelEvaluation`.
Keep one latest answer and compact feedback per actor; ignore superseded,
wrong-binding, wrong-exercise, wrong-answer and old-epoch results.
A new attempt cancels the previous pending job. Preserve the draft on queue,
worker or capacity errors and label them operational failures, never “wrong”.

Public/phone transport contains the exercise and only the recipient's saved
answer/status. Presenter inspection is private. Projector output has the
exercise, aggregates and an explicitly shared anonymous attempt or intended
worked solution. Do not embed an unrevealed solution/trace in initial JS,
HTML, public assets or view JSON. All answer information is mathematically
derivable from the public exercise, so this is a teaching feedback boundary,
not secure examination or anti-cheating protection.

Budgets in the [contract](bplus-tree-contract.md#bounds) are deliberately small:
40 initial entries, initial height at most two, one operation and at most
three repairs. They still cover a cascading split through an internal root.
Persist compact certificates, not every intermediate tree.

Propose 48 admitted actors with at most 4 KiB per serialized slot including
its private actor digest key and reserved feedback, plus 16 KiB shared state. This leaves
headroom under the host's transition limit. It is a storage design, not a
measured classroom capacity. The pilot must measure bursts, replacements,
reconnects and fairness before advertising a supported class size.

## 8. Host review and evidence boundary

The local host at `de3351550f3553ca63023554521fbe84806ec94e` already has prepared
authoring, typed facts/views, structured dispatch errors, mount reconciliation
and atomic queue replacement. The transaction and relational worker fixes
already have local Chrome/Firefox/WebKit evidence. These are usable foundations,
not B+ tree conformance results or published compatibility guarantees.

No new core API is justified by this design. B+ tree capacity, separator
semantics, replay, diagrams and grading belong entirely in the provider.
The implementation must still test the actual full evaluation binding,
portable result/view schemas, installed wheels and real browser flow.
Measured queue fairness and a published compatible host pin remain release
gates shared with the other experimental providers.

The installed engine suite additionally verifies complete repair certificates,
strict inputs, alternative answers and the real host result boundary.
The attached design checker continues to validate worked tree snapshots, lookup/range
expectations and operation key-set effects. It is intentionally not a
certificate replay engine, schema suite, browser test or performance result.
The [plan](bplus-tree-plan.md) identifies the first runtime slice and all
remaining gates.

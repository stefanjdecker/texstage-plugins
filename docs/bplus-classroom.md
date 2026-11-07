# B+ classroom activities: phone and presenter guide

Version 0.4.0 lets students solve B+ tree operations on their phones while the
lecturer collects, inspects and discusses their answers. The activity covers
point lookup, inclusive range scans, insertion and deletion, including cascading
repairs and root changes. English and German use the same mathematical model.

Screenshots: [phone editor](images/bplus-phone.png) and
[projector solution](images/bplus-projector.png), using the synthetic insertion example.

First follow [installation and LaTeX authoring](bplus-lesson.md). Start the
example deck in the matching TeXStage environment, open its presenter view and
have students join the session using the displayed PIN/QR code. Keep the
presenter browser open: it runs the host's authoritative evaluation jobs.
The projector receives only public classroom material.

## Run an activity

1. Navigate to an example slide and expand **B+ tree controls**. The printed
   exercise remains visible until you explicitly share or reveal an answer.
2. Choose **Open answers**. Students can edit, preview and submit. The counts
   distinguish pending, saved and unavailable evaluations.
3. Choose an answer from **Choose an answer**, then **Inspect privately**.
   This panel contains one anonymous response, its status and permitted
   feedback. **Preview inspected attempt** is also private.
4. **Close answers** before discussion. **Share inspected answer anonymously**
   shows its predictions on the projector and phones. Before reveal it does
   not display correctness, corrections or a computed replacement tree.
5. Use **Replay source**, **Next step** and **Previous step** to discuss descent,
   scanned leaves, repairs and final predictions. **Clear shared answer** removes
   the shared attempt. **Reveal solution** releases the worked solution and
   delayed feedback; select the worked replay source to walk through it.
6. **Reset activity** asks for confirmation, clears saved responses and starts
   a new round. It is required before reopening a revealed activity.

The controls can be dismissed with **Close controls** or Escape. Presenter
inspection never appears on the projector just because it is selected.

## Solve an operation on a phone

The task, capacities and starting tree appear above the answer fields.
**Focused page** and **Keyboard page outline** work without dragging or reading
a miniature diagram. A page card lists its entries or separators, child pointers,
next leaf and same-parent siblings. **Page overview** supplies the connected SVG;
wide trees scroll within that box.

- **Descent:** the root is already the first page in a fresh draft. Focus a child
  and choose **Add page to descent** for each remaining page through the leaf.
  **Remove last descent page** corrects a mistaken step.
- **Lookup:** enter the returned key, or leave **Returned keys** blank if absent.
  A separator copy in an internal page is not a returned record.
- **Range:** add the consecutive leaves visited to **Scanned leaves**, using the
  next-leaf pointer. Enter all returned keys in ascending order, including both
  endpoints when present.
- **Insert/delete:** add repairs in execution order, working upwards from the
  changed leaf. A split names the affected page, entries/child pointers kept on
  the left, and the copied/promoted separator. Borrow and merge name the affected
  page and the chosen adjacent sibling. The left page survives a merge.
- **Final predictions:** enter every remaining internal page and its separators
  in ascending page-ID order, then choose the final height in edges. A root leaf
  has height zero and no internal-page rows. A no-op may need no repairs.

Page inputs contain numeric IDs, for example `2` for the displayed page `P2`.
Keys are comma-separated integers; blank key lists mean empty. Newly allocated
page IDs follow the [contract](design/bplus-tree-contract.md). The local preview
helps inspect these pages, including after a split or root change.

**Undo** and **Redo** affect the local draft, with up to 50 history entries.
**Start a fresh draft** clears the local attempt and is itself undoable.
**Submit answer** explicitly saves or replaces your answer while the round is
open. Only the latest submitted answer is stored.

## Preview, saved feedback and conflicts

**Preview my attempt** simulates the draft locally and lets you inspect the
starting tree, leaf edit and each repair. It may expose the mathematical
consequences of your choices before reveal; this is a practice activity, not a
closed assessment. It does not consult the private worked answer, submit a
response or supply the authoritative saved grade. Changing a field invalidates
the preview. A stopped simulation explains an illegal or missing repair.

**Saved feedback** belongs to the saved version, which can differ from the
unsubmitted draft. A saved response may still be pending, correct, in need of
revision, or operationally unavailable. Author-selected `on-reveal` feedback
withholds the saved mathematical feedback until reveal; `immediate` releases it
to its owner as soon as checked. Preview remains available under either policy.

Peer submissions and presenter updates preserve your dirty fields, focus,
selection and undo history. If another device using your identity replaces the
answer, or the activity resets, the editor asks you to **Load saved answer** or
**Keep my draft**. Keeping a draft does not submit it automatically. Queue or
capacity refusal keeps the draft so you can retry. Edits made while a save is
pending also remain local until you submit them.

Unsubmitted drafts and undo history live in the current browser mount only.
They are not recovered after reloading, disconnecting with a reload, changing
the deck language or navigating away. Saved answers are restored from the host.
A reset offers the explicit choice only while the editor remains mounted.

## Accessibility and replay layout

Controls use native buttons, labels and selects, visible keyboard focus, and
touch targets at least 44 CSS pixels high. The UI supports a 320-pixel viewport,
reflow and reduced motion. English/German follow the deck language, with English
fallback for missing author text. Local replay yields between bounded work chunks;
obsolete previews and delayed receipts cannot revive a disposed view.

The projector shows the current replay step instead of a long full answer.
For large trees it enlarges a region around the focused page and lists that
page's pointers; the notice identifies this as a partial view. Phones retain
the complete page selector and overview. Keep author explanations concise and
check the chosen slide box on the actual projector.

The [B4 verification record](design/bplus-tree-b4-validation.md) separates local
desktop/browser emulation from the still-pending physical-phone and classroom
load tests. The following sections document the protocol behind the UI.

## Round lifecycle

1. The item starts in `introduce`. Activating the slide does not open answers.
2. The presenter opens it. Students may submit and replace their own answer.
3. Closing prevents new submissions but keeps accepted evaluations running.
   Leaving an open slide also closes it; returning keeps it closed.
4. The presenter may reopen a closed round, or reveal it. Reveal releases the
   worked answer and each student's mathematical feedback.
5. After reveal, reopening requires the host's `_reset`. Reset creates a new
   epoch, clears answers, selections, sharing and replay, and cancels old jobs.

The host persists state and receipts. A reconnect or renderer remount does not
start another round. A pending result may arrive after close/reveal; it still
belongs to the saved answer if its binding, epoch and correlation match.

## Answer and feedback policy

A submission contains the current phase version, the student's base answer
version and a closed answer object. The host supplies authenticated identity.
Students cannot choose a different exercise, seed, engine or another actor.

The reducer saves one latest answer per actor and uses the SDK's `Evaluate`.
Replacing pending work emits `CancelEvaluation` followed by a new evaluation.
A replacement at a full queue uses the space freed by cancellation. The reducer
reserves feedback storage before admission. New actors beyond 48 are refused;
an admitted actor may still replace an answer.

The result must match the exercise and answer digests, task and complete
persisted binding, including its engine key. Independent bounded replay checks
all typed facts before grading. The criterion is complete replay and every
applicable claim true. It does not compare against the author's worked answer:
different legal split partitions or donor choices can both be correct.

| Saved status / feedback | Meaning |
| --- | --- |
| `pending` | Answer accepted; no evaluator result yet |
| `saved` / `correct` | Complete replay and all applicable predictions correct |
| `saved` / `revise` | Incorrect path, scan, repair or prediction; compact reason and relevant location/checks |
| `unavailable` | Operational failure or mismatched/incoherent facts; no incorrect-answer grade |

`feedback: "on-reveal"` withholds mathematical feedback from the submitting
student until reveal. `"immediate"` releases it to that student as soon as checked.
Operational feedback is always visible to its owner. Missing evaluators leave
work pending; failed/repeatedly expired leases become unavailable. A presenter
must keep an evaluator browser open. Queue refusal does not acknowledge or save
a new answer: retain the local draft and retry after space becomes available.

Never treat `matches`, engine summary text or equality with a reference
certificate as a grade.

## Audience and sharing boundaries

| Surface | Authorized data |
| --- | --- |
| Participant input | Phase/count, own answer/version/status and permitted feedback |
| Presenter controls | Phase/control tokens, bounded counts, private actor handles/version/status, at most one selected answer/feedback |
| Presenter overlay | Public classroom material; no private selected inspection |
| Projector overlay | Public classroom material; no actor handles, own answers or private inspection |

All views receive an explicitly shared anonymous answer and, after reveal, the
worked answer/explanation/result. Before reveal, a shared answer contains only
submitted predictions, even if feedback policy is immediate. It has no
correctness labels or substituted computed tree. Private selections do not
appear in overlays or other students' transport. Sharing is allowed only while
closed or revealed. Replacement clears a selection/share that referred to the
old answer version.

`replay-step` moves a focus cursor through a shared answer or a revealed worked
answer. Steps are: starting tree; each descent page; each scanned range leaf;
each repair; final prediction. The cursor is zero based, bounded by the answer,
and cannot reveal the worked solution early or expose a private selection.
The UI consumes this focus metadata. Before reveal it shows the initial tree
and submitted predictions only. Revealed replay uses the shared engine semantics
to reconstruct bounded intermediate snapshots; they are not persisted per actor.

The public item and every view use closed schemas. Correlations, binding hashes,
actor keys and full engine facts remain in their private domains. The private
actor map uses SHA-256 of canonical ASCII JSON
`["bplus-actor-v1", authenticated_actor]`; these handles remain private
pseudonymous identifiers, not public labels.

## Protocol reference for renderer developers

All commands use `revision_policy: "latest"`. Domain versions, not unrelated
global revisions, decide conflicts. All presenter commands include
`control_version`. Selected/shared answers additionally include `answer_version`.

| Operation | Role | Payload fields beyond common presenter control version |
| --- | --- | --- |
| `submit-answer` | Participant | `phase_version`, `answer_version`, `answer` |
| `open`, `close`, `reveal` | Presenter | None |
| `select-answer` | Presenter | `actor` private digest handle, `answer_version`; empty handle/version zero clears selection |
| `share-answer` | Presenter | `actor` private digest handle, `answer_version` |
| `clear-share` | Presenter | None |
| `replay-step` | Presenter | `source: "shared" \| "worked"`, `step` |
| `_reset` | Presenter | Host command: empty payload, epoch guarded |

Example participant payload for a root-leaf insertion:

```json
{
  "phase_version": 1,
  "answer_version": 0,
  "answer": {
    "format": 1,
    "path": [0],
    "repairs": [{"op": "split", "node": 0, "left_count": 2, "separator": 15}],
    "separators": [{"node": 2, "keys": [15]}],
    "height": 1
  }
}
```

The usual host envelope supplies type, item, epoch, expected revision and a new
request ID. Retry a lost acknowledgment with the **same complete envelope and
request ID**. Changing a payload under an existing request ID is rejected.
Two devices sharing one actor cannot both overwrite the same answer version.

Handle structured refusal codes (`stale-answer`, `stale-phase`, `stale-control`,
`reset-required`, `closed`, `capacity`) and host operational codes
(`queue-full`, `session-capacity`) without discarding drafts. Accept authoritative
receipt epoch/revision, then wait for the corresponding view before deriving a
new control token. The visible interface implements these receipt and conflict choices.

## Bounds, upgrades and verification

State schema is now **2**. Rebuild the bundle, enable the new exact payload,
regenerate its lock and start a new session. Existing schema-1 sessions remain
tied to their old environment; this release does not rewrite course pins or
migrate running sessions.

The provider limits actors to 48, reserves at most 4 KiB per actor slot including
its key and eventual feedback, and caps state at 224 KiB, transitions at 240 KiB,
and each view at 48 KiB. Counts and one selected/shared pointer are bounded;
there is no attempt history or saved class-wide set of computed trees.
Storage limits are not a throughput or physical-device capacity claim.

In a fresh B+-only installed-wheel environment:

```console
python maintenance/build_bplus_schemas.py --check
python maintenance/build_bplus_lesson_schemas.py --check
python maintenance/build_wheels.py --package bplus-lab
python -m pip install --no-deps dist/texstage_bplus_lab-0.4.0-py3-none-any.whl
python -m pytest plugins/bplus-lab/tests -q --basetemp=artifacts/bplus-tests
python maintenance/bplus_authoring_probe.py --output artifacts/bplus-prepared
node maintenance/bplus_prepared_browser.cjs <tested-lesson-bundle> artifacts/bplus-prepared-browser
node maintenance/bplus_classroom_browser.cjs <tested-lesson-bundle> artifacts/bplus-classroom
node maintenance/bplus_ui_browser.cjs <tested-lesson-bundle> artifacts/bplus-ui
```

Set `BPLUS_REPORT_DIR` to retain `budgets.json` from the state tests. Use
`BROWSER=firefox` or `BROWSER=webkit` to repeat the browser probes.
`PYTHON` selects the installed-wheel interpreter. Separately run the existing
engine/browser probe for active worker security, result rejection, timeout
cleanup and recovery under the unchanged host CSP.

Set `BPLUS_LANGUAGE=de` and pass the German lesson bundle for localized UI
coverage. The UI probe drives actual controls; its companion lifecycle fixture
controls delayed promises to check reset, destruction and obsolete previews.
The engine probe remains a separate security and evaluator regression.

Physical phones, classroom throughput, hosted CI, cross-OS artifact transfer
and publication remain separate gates. See the [implementation plan](design/bplus-tree-plan.md).

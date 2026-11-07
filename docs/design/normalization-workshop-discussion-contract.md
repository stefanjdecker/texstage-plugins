# Normalization Workshop: discussion contract (0.3.0)

This extends the [frozen v1 contract](normalization-workshop-contract.md).
Provider, engine, content IDs, manifest revision 2 and APIs 1 stay unchanged.
All twelve v1 schemas and mathematical engine modules remain byte-identical.
The distribution version is 0.3.0; no catalog release is published.

## Version boundary

Persisted state is now schema 2. The four content views use new v2 resources.
Old schema resources remain in the wheel for reference, but are not the
manifest's current state/view contracts. Lesson, seed, answer, analysis,
submission and existing control/selection payloads remain v1.

There is no automatic migration of 0.2.0 sessions. Review and enable the new
payload, refresh the provider lock, rebuild the bundle and start a fresh session.
The host's environment fingerprint guards existing sessions. Keep a matching
old provider environment to continue an old session; do not edit persisted JSON.

New resources under `texstage_normalization_workshop/schemas/`:

- `state-v2.json`.
- `views/{participant-input,presenter-controls,presenter-overlay,projector-overlay}-v2.json`.
- `commands/compare-v1.json` and `commands/topic-v1.json`.

Schemas remain closed and bounded. Run
`python maintenance/build_normalization_schemas.py --check` to verify the files.

## State and commands

An answer reference is `{"handle": "<64 hex characters>", "version": 1}`.
`selected` and `shared` are arrays of zero, one or two references, replacing v1's
nullable single reference. `share_checks` records explicit publication of facts.
`topic` is `summary`, `lossless` or `preservation`. No analysis tableau is persisted.

Each presenter operation requires the current `control` version and active item.
Selection references must resolve to the exact current answer version.

| Operation | Payload beyond control | Effect |
| --- | --- | --- |
| `select-answer` | handle, version | One private selection; pending answers yield no private analysis |
| `share-answer` | handle, version | One answer on projector, no analysis |
| `share-analysis` | handle, version | One checked answer and its facts on projector |
| `compare-answers` | answers: exactly two references | Two checked answers from distinct actors, privately |
| `share-comparison` | answers: exactly two references | Two checked answers from distinct actors and their facts on projector |
| `show-evidence` | topic | Select overview, join or preservation explanation |
| `clear-selection` | none | Clear private selection |
| `unshare` | none | Clear projector answer(s) and sharing intent |

Sharing requires closed/revealed phase. The native comparison control additionally
requires the chosen pair to match the privately inspected pair before sharing.
Server authorization relies on the explicit presenter command, not this UI step.
A private selection does not silently update an existing public share.

A replacement clears any entire pair referencing that actor. Reopening clears
selected/shared arrays, sharing intent and topic; answers remain saved. Reset is
host-owned and creates a new epoch. Existing pending-evaluation cancellation,
correlation, phase guards and final reveal behavior are unchanged.

## Role projections and privacy

- Participant: before reveal, no analysis or personal feedback. After reveal,
  only their own current checked answer's analysis; no peer references. Evidence
  is tied to the saved version, not the unsaved draft.
- Presenter controls: bounded answer references/statuses, selection/share intent
  and topic. No full class analysis map.
- Presenter overlay: at most two selected checked answers and analyses.
- Projector overlay: at most two deliberately shared answers. Analysis is null
  for answer-only sharing. Neither actor handles nor names appear.

Worked explanations follow the existing reveal policy. Sharing checks makes the
criteria visible before reveal by explicit presenter choice; this is documented.
The content hook independently recomputes analysis from already checked, current
answers, at most two analyses per overlay and one for a revealed participant.
It does not accept arbitrary browser HTML or unverified certificate assertions.

The existing 64 actors, 224 KiB state, 256 KiB transition and 128 KiB view caps
remain. Maximal schema-shaped sizes and artifact identities are recorded in
[N4 validation](normalization-workshop-n4-validation.md).

## Displayed evidence

`evidence.mjs` reconstructs the verified chase from its initial symbols and merge
trace. It checks determinant agreement, nonredundant merges and equality with the
final tableau. Intermediate frames are explicitly labeled proof construction.
An all-distinguished final row proves losslessness.

For a losing chase, the saturated tableau is a legal finite relation satisfying
all original FDs. The distinguished tuple is absent, but each component projection
contains its corresponding tuple. Joining those projections therefore adds it.
The UI shows the table, extra tuple and a supplying row for every projection.

For a lost FD X -> A, the closure C of X under the union of projected FDs omits A.
Two rows agree exactly on C and differ elsewhere. Every component projection
satisfies all its implied FDs, while X -> A fails. The UI explicitly says this
relation violates an original FD; it is not the legal lossy-join counterexample.

Native details, buttons and tables provide phone proof expansion, previous/next/
final chase steps and keyboard-scrollable wide tables. Unrelated updates retain
the phone's expanded proof, chase position and focus. A changed saved version or
epoch replaces the corresponding evidence. No proof action submits a draft.

The state and evidence tests exercise semantic guards, role privacy, bounded
projection and independent mathematical checks. Installed-host browser tests
exercise actual evaluator results, controls and role-filtered socket payloads.
No host route, CSP relaxation or additional network capability is introduced.

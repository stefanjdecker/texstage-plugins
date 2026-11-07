# B+ scoring: local verification record

For the rebased source pairing and current CI host pin, see the
[rebase integration record](bplus-tree-rebase-validation.md). The measurements
below describe the original pre-rebase artifacts.

Date: 2026-11-07. B+ Tree Operations Lab 0.7.0 implements the
[published partial-credit rubric](../bplus-scoring.md) and optional fixed
TeXStage scoreboard points. This record covers the exact local artifacts below.
It does not claim a published release, a hosted CI pass or a physical classroom trial.

**Use a Chrome or Firefox presenter for classes approaching 1,000.** The final
Windows WebKit 1,000-student run failed when its presenter page crashed. Its
ordinary UI/security checks and 600-student load run passed; a single earlier
1,000-student pass does not establish reliable capacity. Student phones need
not use the presenter's browser.

## Artifacts and source bases

Local source pairing: TeXStage `9fa798715a8971ae649d0ca794a52a257b7ed2b7` and the collection commit
containing this record, both on `codex/bplus-scoring`. These source commits
are not published compatibility pins.

Validation ran from uncommitted, unpushed worktrees on
`codex/bplus-scoring`. The commits containing this record preserve that tested
implementation; the working-tree status below describes the validation snapshot. Original lecture-tools, existing courses and earlier worktrees
are preserved by a baseline HEAD/status/content check during delivery.
The active host and collection checkouts advanced through unrelated commits
during testing. They are preserved separately; this work retains the frozen
source bases below and has not been merged into those newer branches.

- Host base: `77ddd9537f23827f6da99068d0a8d00c85f71ea5` (generic fixed/quiz points), combined
  with the pending capacity implementation based on `34d0c537135f32b0690147dbb66dd8ff155987f8`.
- Collection base: `c05cc9e080b330cc2822a3bbc17ba80acb67de0d`, plus the pending
  600/1,000-student implementation and this scoring extension.
- Provider payload: `b8a8b36d52004ed7baaa610bb7855a4e2b1c095118c0ceb4cc8714a0cbd78b27`.
- Manifest 4, state schema 5, typed result contract 2, rubric `bplus-partial-v1`.

Exact wheel SHA-256 values:

- `texstage-0.2.1.dev6-py3-none-any.whl`: `79f67704191881204a95f6e2bdb7bfb92b809c2cf11fd841766dc97d4001f636`; 156 package files matched source and installation.
- `texstage_bplus_lab-0.7.0-py3-none-any.whl`: `a971432e5dc88a100f75c633516d73cbcb9c61e99ce65b705d3f4d66b8e99221`; 38 package files matched source and installation.

Wheel/sdist provider payload parity passed. Source, installed runtime and wheel
package bytes match; the manifest was checked against the source declaration.
After testing, the final README was repackaged to include the observed WebKit
limit. Only METADATA and RECORD changed from tested provider wheel
`b1c364d958743c62d8595a308c60397b7fee9e23c5bbc917df9c94ae66a0d9be`; every runtime/resource byte and the
provider payload are identical. The final metadata matches the delivered README.
Schema and file hashes are in the [machine-readable record](bplus-tree-scoring-validation.json).
A development version lower bound is not a published compatibility pin. Re-enable
this payload, regenerate locks, rebuild bundles and start a new session; earlier
persisted B+ sessions are not migrated in place.

## Correctness, UI and security

- **145 provider tests passed** using installed wheels, including
  legal alternative repairs, independent partial criteria, extra-answer penalties,
  rounding, packed grade bounds, verified evaluator facts, latest-answer replacement,
  replay/late results, reveal, practice, unavailable feedback and reset.
- **196 host regressions passed** after the final optimization: fixed and quiz
  points, atomic rollback, authenticated credits, private batch snapshots,
  scoreboard/CSV projection, capacity admission/replacement, records and broadcast.
  The earlier broad run had 556 passes and one platform skip; six registry-access
  failures/errors were cleared by a scoped nine-test rerun outside the filesystem
  sandbox. Worker/browser security restrictions were retained.
- Chromium, Firefox and WebKit passed the final actual-control UI flow for all
  six examples. Chromium also passed German. Tests cover partial/full grades,
  private-before-reveal behavior, published phone totals/ranks, authenticated CSV,
  reset withdrawal, touch/keyboard controls, draft conflicts, focus, navigation,
  late promises, 320-pixel reflow and 44-pixel touch controls. No page errors.
- All three browser families passed the installed engine cases and active
  connection, child-worker and dynamic-code restrictions, invalid-result rejection,
  timeout cleanup and subsequent recovery. The evaluation deadline remains 2 s.
- Generated schemas and all worker bundles match their sources. English/German
  lessons and layout-stress decks build with the new rubric; direct LaTeX,
  exercise/solution separation, static exports and clipping checks pass. Rendered
  rubric and cascade-solution pages were inspected. Scoring-panel screenshots are
  linked from the grading guide.

The CI definition now includes `test_grading.py` in Linux/Windows conformance
and requires a compatible manifest-4 scoring/actor-record host SHA. It has not
been dispatched for these uncommitted artifacts.

## Synthetic class-size checks

Sequential local runs used the final installed wheels, 600 or 1,000 independent
student WebSocket clients, and a real presenter browser. The workload includes initial
submissions, overlapping replacements, reveal/publication, reset/withdrawal and
evaluator disconnect/recovery. All five successful runs assessed every accepted
latest answer, matched all published awards and ranks, and removed every
contribution on reset. WebKit at 1,000 failed during recovery before publication.

Worst p95 values across initial/latest replacement phases are shown below;
recovery is the maximum answer latency during evaluator recovery. Publication is
the time until all synthetic students observed their published points and ranks.

| Presenter | Students | Ack p95 | Feedback p95 | Recovery max | Publication | Correctness/budgets |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| chromium 156.0.8078.80 | 600 | 4.16 s | 15.84 s | 14.33 s | 2.59 s | Pass |
| chromium 156.0.8078.80 | 1000 | 7.54 s | 28.41 s | 25.65 s | 4.86 s | Pass |
| firefox 153.0 | 600 | 4.02 s | 17.13 s | 19.21 s | 2.61 s | Pass |
| firefox 153.0 | 1000 | 5.98 s | 26.21 s | 28.02 s | 4.72 s | Pass |
| webkit 26.5 | 600 | 4.70 s | 25.21 s | 26.43 s | 2.89 s | Pass |
| webkit 26.5 | 1000 | 7.19 s | 39.92 s | Incomplete (392/1000) | Not reached | Failed: presenter crash |

Existing budgets are unchanged: at 600 students, p95 acknowledgement 5 s and
feedback 30 s; at the 1,000 ceiling, 10 s and 60 s; recovery at both sizes 150 s.
The 1,000-actor admission ceiling remains enforced. Replacement and grade updates
reuse an existing actor slot, avoiding redundant class-wide count queries.
Private grades do not trigger whole-class reranking or private-data broadcasts.

These are loopback measurements on Windows, an i9-11950H with 16 logical CPUs.
They are not measurements of 600 physical phones, campus Wi-Fi or a remote server.

## Preliminary findings and remaining gates

The first Chromium 600 run missed the 5-second replacement-ack target (5.26 s);
the final run passed after removing redundant class-wide count queries.
The first WebKit 1,000 run stalled during replacements after 545 latest answers
were assessed. A diagnostic repeat passed, but the final matrix run's presenter
page crashed after assessing 392 of 1,000 recovery answers. All 1,000 submissions
were saved. A six-worker trial also crashed during replacement. Four workers
completed correctly at 600 but missed the 30-second feedback target (30.62 s).
Neither concurrency experiment is shipped; the host retains its 2/4/8 policy.
The underlying WebKit cause is **not established**. This remains a failed load
gate for the Windows WebKit presenter, not a verified capacity claim. The harness
saves worker/connection/pulse diagnostics and now fails promptly on a page crash.
The machine-readable record retains failures and the successful diagnostic repeat.
No pass thresholds, CSP rules or worker isolation were relaxed.

Remaining release work is publication with an exact compatible host pin, hosted
Linux/Windows conformance, cross-OS artifact transfer and a physical-phone/campus
network pilot. Resolve WebKit's presenter crash before claiming its 1,000-student
ceiling; use Chrome/Firefox for that load meanwhile. B+ scoring remains a
formative activity with local previews, not a secure examination mechanism.

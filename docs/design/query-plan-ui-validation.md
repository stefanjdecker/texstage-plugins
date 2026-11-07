# Query-plan Q4 validation

Local Windows validation of provider 0.4.0, 2026-11-07. This completes the phone
selector editor and presenter controls. It is a development milestone, not a
hosted CI result or published classroom release.

The [machine-readable record](query-plan-ui-validation.json) contains exact
identities, schema hashes, browser checks and screenshot hashes.
The [classroom guide](../query-plan-lesson.md) explains the workflow.

## Frozen artifacts

| Artifact | Identity |
| --- | --- |
| Provider | `io.github.stefanjdecker.queryplan` 0.4.0 |
| Wheel SHA-256 | `46d5c4b8e695d43afddb752b8c6f56d0606d84345679e93b409308261d00a4da` |
| Provider payload | `c8bbe936f167fb47db93156b78ea00848420ce4d364246373eb93d9119ad732e` |
| sdist SHA-256 | `70c0ff8ad3c5302a5167795987722225134b52b570ba756a794f027f0a80881c` |
| Host development commit | `de3351550f3553ca63023554521fbe84806ec94e` |
| Host wheel SHA-256 | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| Host runtime resource inventory | `e41e8bbb8463111ee7d62f8c0b92c4dda736bc5df9ce558b9d7e813d06efcb23` |

The wheel is portable py3-none-any; its sdist rebuild has identical manifest and
resource bytes. Runtime sources/resources have LF line endings. Installed
imports resolve inside the isolated Python 3.14.4 environment with
only this provider enabled. Node was v24.15.0; worker freshness checks
passed. No host source or CSP change was needed.

The frozen engine/cost rules, state schema 2, commands and audience projections
remain compatible with Q3. The additional presenter-controls surface uses the
existing presenter schema. Version/payload enablement still requires a new
reviewed pin; this work did not migrate course profiles.

## Results

**158 tests passed**, no failures/skips, in 98.91 seconds on the final wheel.
This comprises the existing 149 engine/authoring/state checks plus nine selector
checks. Selector coverage is compared with the independent Python enumerator:
every feasible plan in the four examples is reachable, canonical plan round trips
are preserved, and geometry agrees with cost facts. The three-relation chain
offers eight connected ordered shapes; the 864-candidate upper bound also
includes infeasible/disconnected candidates that the interface excludes.

The final wheel regenerated the live bundle, handout, solutions, static
PowerPoint and direct pdfLaTeX editions. All five PDF editions have identical
extracted teaching text to Q3. German PDF generation and direct-export freshness
also passed. UI-only changes did not alter the static LaTeX layout.

| Browser | Version | Real UI | Protocol | Static exercise | Worker/security |
| --- | --- | --- | --- | --- | --- |
| chromium | 156.0.8078.80 | passed | passed | passed | passed |
| firefox | 153.0 | passed | passed | passed | passed |
| webkit | 26.5 | passed | passed | passed | passed |

The real UI scenario uses authenticated presenter, projector and participant
connections with the installed provider and actual evaluator. It covers:

- All four activities: selective/broad scans, three-table join order and limited
  hash workspace, with actual selects/buttons and a real evaluation after submission.
- Private inspection, explicit anonymous sharing/clearing, role-transport privacy,
  close/reveal/reset, terminal reveal, and teardown on leaving an activity.
- Touch at 320 CSS pixels, keyboard submission, visible labels and 44-pixel
  controls, resize and 200% text enlargement. Tests bound the page to the configured
  viewport after selecting a long inspector label; they also check that select
  text really enlarges. WebKit's native select-face overflow was fixed locally
  while keeping native select semantics.
- Focus/draft preservation under unrelated updates, same-actor conflict choices,
  undo and reset recovery. Focused mounts loaded through actual installed module
  URLs cover receipt-before-view, view-before-receipt, editing during a save,
  queue rejection, late acknowledgements after reset, teardown and German labels.
  These focused delivery-order probes use a controlled dispatch promise; grading
  and the main classroom flow use the real host.

The separate protocol probe retains replay, stale control/epoch/answer,
replacement, navigation and privacy checks. The static smoke probe confirms that
the exercise remains visible before sharing/reveal and input is disabled while
closed. The engine probe passes eight samples in each browser, invalid-result
rejection, timeout cleanup/recovery and ten active security restrictions.
Unrestricted positive controls prove the probes execute; the real policy blocks
forbidden requests, network/child workers/external imports and dynamic evaluation.
No relaxed-policy run is counted as a pass.

## Visual evidence

Screenshots contain synthetic example-session data only. The normal phone,
presenter controls and full three-table projector solution were inspected.
The projector shows the complete plan and explanation within its activity box;
the phone uses a scrolling vertical layout.

- [Phone selectors and node arithmetic](../images/query-plan-phone.png)
- [Presenter controls and private inspection](../images/query-plan-presenter.png)
- [Projector worked plan](../images/query-plan-projector.png)

## Remaining Q5 gates

Desktop touch emulation is not an actual phone/tablet or LAN check. Full browser
zoom and screen-reader testing remain separate from text enlargement and labeled
control checks. No claim is made about concurrent classroom throughput: Q3's
64-slot serialized-size checks remain storage-budget evidence only.

Measure concurrent submissions/replacements, queue fairness, latency and
evaluator loss/recovery under load. Run the same immutable artifacts on Linux,
add hosted jobs against a published compatible host artifact, and review the
release/catalog before publication. The current host version string alone is
not an immutable compatibility pin.

The original repository, existing courses, course environments, private media
and unrelated plugin work remain outside this milestone. Changes are not
committed or pushed by this task.

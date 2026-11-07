# Query-plan classroom state: Q3 validation

Local Windows evidence, 2026-11-06, for provider 0.3.0. The
[classroom contract](query-plan-classroom-contract.md) defines the frozen protocol.
The [JSON record](query-plan-state-validation.json) identifies the exact artifacts,
resource hashes, measured payloads and browser results. Historical
[Q1](query-plan-engine-validation.md) and [Q2](query-plan-authoring-validation.md)
records remain unchanged.

## Implemented boundary

The lesson now stores bounded per-actor plans, guards concurrent saves/controls,
cancels replaced jobs, verifies returned facts independently, assesses best/budget
goals, supports private inspection and explicit anonymous sharing, and releases
feedback/solutions only after reveal. Reveal cannot be reversed without reset.
Navigation closes submissions while retaining pending results and saved answers.
Stable roster numbers survive canonical persistence and replacements.

The phone selector editor, cost inspector and presenter controls remain Q4.
Required overlay/input modules render no new controls. Browser tests issue
authenticated host commands directly; passing them does not mean a classroom UI
has been implemented. Prepared exercises and static exports remain usable.

No host code or security policy changed. Original tools, existing courses,
course environments/pins and private media were not modified. Other in-progress
plugin work was preserved; there is no catalog/package publication.

## Artifacts

| Item | Identity |
| --- | --- |
| Provider | io.github.stefanjdecker.queryplan 0.3.0 |
| Provider payload | 4fe7ed711e531b08117428de2fd6902441605068d66306e51f8405bdeda879af |
| Wheel SHA-256 | 81c0aafd510a5cd9f29a3fd334377ee6943cb0e824289fcd0956cf7646044755 |
| Host commit | de3351550f3553ca63023554521fbe84806ec94e |
| Host wheel SHA-256 | d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6 |

Wheel/source-distribution payload parity passed. Every packaged source/resource
uses LF and matches the tested wheel bytes. The engine/model, original four
schemas, fixtures and style are byte-identical to 0.2.0. State schema is now 2;
start a new profile/session rather than upgrading an existing Q2 session.
The exact host artifact matters: 0.2.1.dev3 alone is not a sufficient pin.

## Tests and bounded storage

**149 installed-wheel tests passed**, no failures or skips, in 106.18 seconds:
86 engine tests, 22 authoring cases and 41 Q3 cases. Python 3.14.4,
Node v24.15.0, the matching host wheel and locked dependencies were used.

Q3 evidence includes:
- All four distinct tied optimal library plans pass; budget-satisfying nonoptima,
  target misses and exact invalid-plan reasons remain distinct.
- Independent canonical fact comparison rejects changed identity/model/format,
  missing/duplicate/reordered nodes, forged costs/masks/rows/widths/workspace,
  booleans/floats, extras and fabricated invalid results. A schema-valid false
  cost passes the generic transport schema but is rejected by the installed
  reducer as unavailable, without a grade.
- Actor-local saves, stale controls, actor/request correlations, cancellation,
  old/wrong binding/epoch/actor completions, immutable inputs and counter limits.
- Private selection, explicit anonymous sharing, clearing on replacement/reopen/
  navigation, irreversible reveal and privacy before/after reset.
- Real runtime receipt replay, two-device conflict, two actors, queue-full
  rollback and exact-request retry, atomic replacement at a queue ceiling of one,
  reset races, late leases, restart delivery, lost evaluator lease generations,
  partial reveal and timeout without grading.
- Maximum-shaped exercise/plan and bilingual Unicode explanations, 64 escaped
  actor IDs, replacement at capacity, role schemas through both installed host
  validators, and actual worker projections.

The measured fixture used 106219 state bytes, at most
1628 bytes per completed/pending slot, and
104689 bytes for an observed submit
transition. The revealed state with an empty effects list serializes to
106242 bytes.
Views measured 49142 participant,
118132 presenter and 49110
projector bytes. Caps remain 208 KiB state, 256 KiB transition and 128 KiB per view.
Slots reserve 3072 bytes before accepting work. Oversized actor IDs are refused
rather than truncated. These are serialized-storage checks, not measured
64-device throughput, latency or fairness.

## Exports and browsers

The final provider rebuilt the seven-slide/four-activity bundle, static PowerPoint,
handout/solutions PDFs and direct pdfLaTeX editions. Preparation ran four times
total for all four items across build modes. English/German PDF tests passed.
Exercise/solution PDF text matches Q2 exactly; no layout changes were introduced.

Chrome 156.0.8078.80, Firefox 153.0 and WebKit 26.5 passed:
- Eight installed cost-worker samples, invalid-result/timeout recovery and
  active restrictions on fetch, XHR, WebSocket, EventSource, child/blob workers,
  external modules, eval and Function. Positive controls were included.
- Authenticated presenter/projector and two participant sessions, a second device
  for one actor, actual worker evaluation, receipt replay, stale saves/controls,
  private inspection/sharing, target/invalid feedback, reveal/reset and navigation.
- All four prepared slides, static-background preservation, role boundaries and
  mount teardown, with no page errors.

The protocol test driver now waits for the committed view revision after a receipt;
WebKit exposed that the next state push may arrive later. The harnesses allocate
free loopback ports by default and await server shutdown, avoiding collisions
with parallel development tests. Firefox required native process launch outside
the execution sandbox; application worker restrictions were unchanged.

Remaining gates are Q4's usable selectors/presenter controls, accessible interaction,
physical phones, measured classroom load, hosted/Linux evidence and a published
compatible host pin. No release-ready or physical-device claim is made.

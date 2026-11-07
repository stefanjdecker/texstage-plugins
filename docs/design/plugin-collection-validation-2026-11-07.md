# Plugin collection validation

Date: 2026-11-07. All nine provider packages are present, build as portable wheels,
and work together with the compatible host described below. This is local
Windows validation of the implemented features; it is not a release or hosted CI result.

The current `codex/bplus-scoring` branches include TeXStage `main` at
`6b64828b98e9908fc67c265cab31a71a216308d5` and the collection's new
`main` at `10ae0b4d4627c9fe916b108deeb1c262857fe152`. The collection's
`main` currently matches its former `codex/plugin-system` default.

| Package | Version | Implemented scope | Tests |
| --- | --- | --- | ---: |
| Coordinate slide + distance engine | 0.1.0 each | Phone coordinates, presenter/projector and engine | 4 together |
| Transaction engine | 0.1.0 | Schedule analysis; no classroom interface yet | 67 |
| Relational algebra | 0.1.0 | Engine and prepared lesson with JSON answer editor | 72 |
| B+ tree operations | 0.7.0 | Structured operations, partial credit and scoreboard | 145 |
| Functional dependencies | 0.6.0 | Closure, candidate keys, implication and points | 153 |
| ER decisions | 0.6.0 | Model decisions, preview, discussion and points | 135 |
| Normalization workshop | 0.5.0 | Normal forms, decompositions, evidence and points | 80 |
| Query-plan challenge | 0.7.0 | Physical plans, cost inspection, editing and points | 199 |

The 855 tests include provider and artifact/handoff checks. The coordinate/distance
pair was tested in its original strict two-provider environment; each remaining
provider had an isolated environment, followed by a nine-provider installation.

## Host compatibility correction

The first full collection run found an FD regression in the rebased host:
presenter-only answer counters caused a full-class refresh even though FD
declares `participant_updates: "actor"`. Peer submissions leave another
student's projection unchanged, so these updates should remain actor-scoped.

The host now retains the established actor-only contract when `broadcast_fields`
is absent. An explicit field list still causes a full broadcast when one of those
shared fields changes. Presenter commands, reset and navigation remain full
broadcasts. Authentication, role-filtered data, worker isolation, result validation
and evaluation deadlines are unchanged. All nine provider payloads are unchanged.

The tested host is commit
[`f612a366ddde07b79a6d5f70160d7ac9db8bd880`](https://github.com/stefanjdecker/texstage/commit/f612a366ddde07b79a6d5f70160d7ac9db8bd880),
published to the TeXStage GitHub and GitLab `codex/bplus-scoring` branches. It
contains the compatibility fix in `src/texstage/plugins/runtime.py`, its regression
test and documentation, based on `9fa37afda69f1cacc0d12ff2933214cf4598f79f`.
The version number `0.2.1.dev7` alone does not identify it.

- Fixed host wheel SHA-256: `a8fd533abf3e2261dcf26e400a56fd849a3254544681bb49209fffe2dc377ace`.
- Runtime source SHA-256: `7a4195700dc9ce3d6865948c01799d5b27065c0b448b3739d639ecf904d7b4ea`.
- Source patch SHA-256: `f4634dcf14a7e2044fabc8d86d3d66849340b36238214d26b60c8a11675a32c8`.

## Verification

- Full host baseline: 590 passes, one platform skip and two passing subtests.
  After the fix: 241 relevant host regressions and all 28 FD points tests pass,
  including the previously failing actor-notification case. Together with the
  unchanged passing provider cases, all 855 collection tests have passing results.
- Every wheel rebuilds from its source distribution with the same provider
  payload. All 156 host runtime/resource files and 241 provider files match source
  and installed wheel bytes. Disabled discovery does not import provider factories.
- All eight engines pass through the actual host evaluator in Chrome, Firefox
  and WebKit. The seven database engines additionally pass the full active worker
  security probes, invalid-result rejection, timeout cleanup and recovery.
- Classroom flows pass in Chromium for all seven slide types: real presenter,
  projector and phone controls, saving, privacy, sharing, reveal/reset and grading
  where supported. ER additionally passes both valid scored models, totals,
  ranks and CSV checks. The coordinate/distance flow also passes Firefox/WebKit.
- A single synthetic deck compiles all seven slide types with all nine providers
  enabled. All 28 initial role projections validate. Real presenter, projector and
  phone mounts switch between every type and tear down cleanly, with no page errors.
- Existing authoring tests build live, PDF and static PowerPoint artifacts and
  check direct LaTeX exports, language variants, private-answer separation and
  stale-source rejection. Representative mixed-deck and phone screenshots were inspected.

The [machine-readable record](plugin-collection-validation-2026-11-07.json)
identifies all provider versions, payloads, wheel hashes, browsers and evidence.
Chrome 156.0.8078.80 was used for most UI checks; ER's harness used the pinned
Chromium 151.0.7922.34. Firefox was 153.0 and WebKit 26.5.

The transaction engine still needs a lesson/phone interface, and relational algebra still
needs its graphical answer editor. This run did not repeat the class-size matrix
or a physical-phone/campus-network pilot. The existing Windows WebKit B+ presenter
limit near 1,000 students remains open. Original lecture-tools, existing courses,
private media and the other working checkouts remain unchanged.

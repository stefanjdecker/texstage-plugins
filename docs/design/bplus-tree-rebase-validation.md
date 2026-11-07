# B+ scoring: rebase integration

Date: 2026-11-07. The scoring branches now include TeXStage `main` at
`6b64828b98e9908fc67c265cab31a71a216308d5` and the plugin collection's default
`codex/plugin-system` at `10ae0b4d4627c9fe916b108deeb1c262857fe152`. At the time of this rebase, the collection had no `main` branch. Its new `main` now points to the same base; see the [collection validation](plugin-collection-validation-2026-11-07.md) for the subsequent compatibility correction.

The compatible host commit is [`9fa37afda69f1cacc0d12ff2933214cf4598f79f`](https://github.com/stefanjdecker/texstage/commit/9fa37afda69f1cacc0d12ff2933214cf4598f79f).
B+ conformance uses this immutable pin by default; an explicit dispatch input or
repository variable can override it. Other providers retain their upstream CI
jobs and host pins. This records local checks, not a hosted CI result or release.

## Compatibility resolution

Manifest revisions 3–5 retain `state_records: true`, actor-only participant updates
and their existing strict values. Actor-record providers may declare explicit
`broadcast_fields`. Without that list, changing shared state refreshes the entire
class; unchanged shared state still allows actor-only updates. B+ retains its
explicit field list. Tests cover both paths and reject mixing the two record APIs.
Worker isolation, role filtering, result validation and deadlines are unchanged.

## Installed artifacts and checks

- Host: `texstage-0.2.1.dev7-py3-none-any.whl`, SHA-256
  `4db8b8379fbd8db81d785c549b6ce614c3255f6f0daf9b1ca4c693f093b171b3`.
- Provider: `texstage_bplus_lab-0.7.0-py3-none-any.whl`, SHA-256
  `a971432e5dc88a100f75c633516d73cbcb9c61e99ce65b705d3f4d66b8e99221`. It is byte-identical to the previously tested wheel.
- Provider payload: `b8a8b36d52004ed7baaa610bb7855a4e2b1c095118c0ceb4cc8714a0cbd78b27`.
- 156 host files and 38 provider files match their committed source and installed
  wheel bytes. Provider wheel/source-distribution payload parity passes.
- 241 host regressions and all 145 provider tests pass. An initial temporary-parent
  setup error was corrected; the two affected provider tests passed on targeted rerun.
- Chrome, Firefox and WebKit pass the engine/security probes and the complete
  six-example phone/presenter scoring UI checks, including publication, CSV,
  reset and private feedback. The two-second evaluation deadline is unchanged.
- The English lesson rebuild passes live-bundle privacy, static PowerPoint,
  direct LaTeX editions, source freshness, page-count and clipping checks.
- Dependency locks, maintained documentation/manual checks and the public-content
  history guard pass. The original repository and courses remain unchanged.

The [machine-readable record](bplus-tree-rebase-validation.json) includes artifact
identities, browser versions and evidence hashes. The earlier
[scoring and capacity record](bplus-tree-scoring-validation.md) remains historical
evidence for its exact artifacts. The 600/1,000-student load matrix was not repeated
for this rebase; the documented Windows WebKit presenter limit at 1,000 remains open.

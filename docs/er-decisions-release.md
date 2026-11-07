# ER registration: 600-student release checks

Version 0.6.0 supports up to **600 distinct answering students** in the frozen
`registration-v1` lesson. It includes prepared LaTeX authoring, persistent lesson
state and English/German phone, presenter and projector interfaces. This is an
experimental plugin, not general ER modelling. See the [lesson guide](er-decisions-lesson.md)
and [current validation](design/er-points-validation.md) for exact artifacts,
measurements and limits. Earlier E5, accessibility and native-zoom validation
records remain historical evidence for their original artifacts.

Install the matching TeXStage 0.2.1.dev7 host and ER 0.6.0 wheel in a fresh
environment/profile, enable the exact provider payload, build the lesson and
start a new session. State schema 4 uses host-owned answer records, bounded
16-answer presenter pages and constant-size counts/option totals. Old sessions
remain in their original pinned environments. Existing courses are unchanged.

## Current automated gate

The harness connects 600 authenticated protocol clients before measurement.
They submit all 27 answer combinations in a burst, then every student replaces
their answer. A real presenter browser runs the restricted evaluator. The
deterministic engine explicitly permits reuse of accepted successful results
with the identical binding/input in the same item and epoch. Each student keeps
an independent saved job, answer, receipt and guarded completion. Fresh inputs
still execute in fresh restricted workers.

The unchanged warm target is **p95 ≤10 seconds and last answer ≤30 seconds**,
measured from each send until that client's observed evaluated/saved state.
Cold evaluation and receipt timings are reported separately. Correctness feedback
remains private until reveal. Sequential joins and browser startup precede the timed waves.
The real presenter/evaluator is in Chromium, Firefox or WebKit; the 600 students
are Node WebSocket clients using the installed host's actual client protocol,
not 600 rendered phone browsers. This avoids a single browser's per-origin
WebSocket connection limit. Results measure the recorded machine on loopback,
not classroom Wi-Fi, physical devices or a remote service guarantee.

Scored runs additionally reveal both waves, verify every total and own award,
replay publication without duplicates, refuse reopening after reveal and check
that reset withdraws all awards. Correct and incorrect models are both present.

Recovery mode resets the lesson into a new epoch, pauses the real presenter,
queues 600 new answers, leases two jobs through a synthetic presenter connection,
disconnects it and resumes the real presenter. It verifies progress and all
saved outcomes without changing the 120-second lease fallback or retry budget.
Receipt replay must not append another answer, and a 601st answering actor must
be refused while existing students can still replace their answers. Separate
browser tests check worker timeout, network/nested-worker restrictions and UI
privacy, keyboard access and bilingual layout.

```console
python maintenance/er_ui_bundle.py --output artifacts/er-load-deck --points 1000
node maintenance/er_load_browser.cjs artifacts/er-load-deck/out/lesson.bundle artifacts/er-load
```

Use an isolated environment with the matching host/provider wheels, the host's
hash-locked Python dependencies and the collection's locked Node dependencies
(`npm ci --ignore-scripts`). Install the chosen Playwright browser; set `PYTHON`
to the isolated interpreter. Use Node 24.15.0 or the pinned CI version, which
provides the native WebSocket API used by the protocol clients.

| Variable | Meaning |
| --- | --- |
| `ER_LOAD_ACTORS` | 1–600; default 600 |
| `ER_REQUIRE_LOAD_TARGETS=1` | Fail on a missed warm p95/last-answer target |
| `ER_LOAD_RECOVERY=1` | Add reset, presenter disconnect and job recovery |
| `BROWSER` | `chromium` by default, or `firefox` / `webkit` |
| `TEXSTAGE_TEST_PORT` | Dedicated loopback port; default 18802 |

For the full gate set `ER_LOAD_ACTORS=600`, `ER_LOAD_RECOVERY=1` and
`ER_REQUIRE_LOAD_TARGETS=1`. PowerShell uses `$env:ER_LOAD_ACTORS='600'`;
POSIX shells can prefix the command with `ER_LOAD_ACTORS=600`. A missed latency
target is a failed measurement, not a reason to silently relax budgets.

## Identical artifacts and CI

The separate [ER workflow](../.github/workflows/er-conformance.yml) is manually
dispatched with a full, published 40-character compatible host commit. It has
no floating `main` fallback. The producer builds that host wheel and the ER
wheel/sdist, checks payload parity, runs host/ER tests and real English/German
TeX builds, then creates an inventory of SHA-256 hashes for the handoff.

Linux and Windows consumers verify the inventory before installing the exact
same wheels. Their checks deliberately exclude the three TeX-authoring cases;
those belong to the Linux producer. Separate Chromium, Firefox and WebKit
jobs use the handed-off bundles for live lesson, native German and worker
security checks. A separate Chrome job uses disposable profiles at native 200%
page zoom in both languages and checks keyboard access to scrolled controls and
projected alternatives. The load job records runner hardware and requires the
**600-actor** scored warm latency gate, all 27 answer combinations, a full replacement
wave, reset and evaluator-disconnect recovery. A 32-actor run remains a smaller
regression. Semantic, privacy and recovery failures fail the job. Logs and reports
are uploaded even on failure. Hosted results still need deployment validation.

`maintenance/er_artifacts.py` binds the handoff to the host commit and rejects
missing, additional or changed files and nonportable manifest paths. These
hashes detect accidental artifact changes; they are not a signing system.

The published compatible host source is
[TeXStage `ffb90eb`](https://github.com/stefanjdecker/texstage/commit/ffb90eba8f698ae73b209841edf309820bc13ed0).
The workflow defaults to this immutable commit, including the bounded validation
caches and private-score projection optimization used by ER points. A development
version string alone does not identify these changes.

After rebasing onto the current shared host, local verification passed 206 host
tests, 135 installed ER provider/artifact tests and all seven plugin worker
freshness checks. The installed ER payload remains
`bd5f433f3eb845a519568f7d74574c0f35b9372a73391e82e54a0503eeaa65a6`.
This is a source-publication check, not a new 600-client browser run. Historical
wheel identities, browser measurements and their exact limits remain in the
[points validation](design/er-points-validation.md) and
[600-student validation](design/er-600-validation.md).

The ER workflow has not yet run on GitHub. Dispatch it with the pinned host,
then record its run URL and the newly built artifact hashes before a release.
No ER catalog entry or package release has been published by this work.

## Checks still requiring people and deployment hardware

- On one physical Android phone and one physical iPhone, record model, OS,
  browser and network. Join, choose every card, edit a reason, preview the
  model, save, repair after reveal, enlarge text, reconnect and reset.
- With a screen reader, verify names, group labels, focus movement, the
  textual constraint alternative and status/feedback announcements. Record
  the reader/browser versions and any inaccessible operation.
- Repeat the intended class size on the actual teaching host and LAN. Record
  other workloads and include presenter reconnects; laptop loopback results
  are not a deployment guarantee.
- Run the hosted immutable-artifact workflow and review its output. Retain
  the independent distance/coordinates, transaction and relational regression
  environments; their exact-provider fixtures must not be broadened.
- Review the immutable provider/host artifacts and collection metadata before
  approving a catalog release. Keep the original repository and courses intact.

Browser emulation, keyboard tests and successful TeX builds do not substitute
for the physical-device and screen-reader checks.

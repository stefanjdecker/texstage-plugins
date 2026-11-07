# FD Lab 0.6.0: prepared grading and the 600-student target

Date: 2026-11-07. **The 10-second feedback p95 target passes in all 18 measured
bursts across Chromium, Firefox and WebKit.** The run checked 10,800 submissions
and replacements from 600 synthetic participants. Every observed feedback
response arrived within 7.39 seconds. This is local automated evidence for
these exercises and hardware, not a claim about an unmeasured lecture network.

## Implementation and security

The prepared FD lesson now checks each answer in its enabled provider hook.
Authoring already computes private closure tables, candidate keys and worked
proofs. The live check uses those bounded data and replays at most eight proof
steps. It performs the same independent verification previously used to check
browser-engine certificates, without repeating the full browser round trip.

The generic host commits the answer, feedback, private credit and receipt in one
transaction. An unsuccessful hook or save accepts no new answer; retry remains
safe. Students cannot supply a grade, credit, private reference or analysis facts.
Replacement changes the existing credit; reveal publishes it; reset withdraws it.
No pending browser evaluation job is created by a prepared FD lesson. Feedback
continues when the presenter browser disconnects while the activity remains open.

The standalone FD analysis engine remains independently usable, with unchanged
v1 formats, fresh workers, two-second execution deadline and CSP restrictions.
The trusted provider hook retains the host's 250 ms deadline and killable process.
No host code, worker limit, CSP, database durability setting, original repository,
course, installed course environment or private media was changed. The final
candidate uses the existing host commit `7b9934d91f3affcc54e2ab6573c8c662cc87348a`.

The provider is version 0.6.0, manifest revision 4 and state schema 4. Rebuild
bundles, explicitly enable the new payload and start new sessions when upgrading.
Existing pinned courses have not been migrated. The prior
[points integration record](functional-dependencies-points-validation.md) remains
historical evidence for 0.5.0 and its failed feedback timing gate.

## Measurements

Windows 10.0.19045, Intel i9-11950H, 16 logical CPUs, approximately 64 GiB RAM;
Python 3.14.4, Node 24.15.0, Playwright 1.62.1. Browsers ran sequentially on
loopback. Each run used 600 authenticated protocol participants, one additional
320-pixel rendered phone sharing student 1's identity, and an actual presenter
window. This does not simulate 600 browser renderers, physical phones or Wi-Fi.

Each browser tested closure practice, all candidate keys and implication
counterexamples. Each mode submitted 600 distinct valid answer envelopes with
expected correct and incorrect outcomes, then changed every student's answer in
a replacement burst. The test oracle derives expected grades from Python
analysis rather than the production feedback function. All answers and awards
were checked; no answer-result cache was involved.

| Presenter browser | Feedback p95 over six bursts | Slowest feedback | Highest phone input p95 |
| --- | ---: | ---: | ---: |
| Chromium 151.0.7922.34 | 4.87–5.30 s | 5.36 s | 3 ms |
| Firefox 153.0 | 4.46–7.26 s | 7.39 s | 2 ms |
| WebKit 26.5 | 3.22–6.56 s | 6.66 s | 20 ms |

Feedback is measured from sending the submission to receiving its checked state.
Percentiles use nearest rank. Trusted keyboard-to-next-frame timings are sampled
throughout each burst. Targets remained p95 <10 s for feedback, worst <30 s,
and input p95 <100 ms. The displayed p95 ranges are per-burst values, not an
average hiding a slower burst. All observed feedback also stayed below 10 s.

Every browser verified hidden pre-reveal credits, each student's published award,
all CSV rows, replacement, receipt replay, preserved awards from other activities,
and reset withdrawal. The presenter traversed all 24 pages and inspected student
600; private rosters, selected answers and references stayed off other phones.
Reconnect scenarios verified feedback with no presenter, same-student resume,
unchanged replay receipts, rejection of forged results and stale commands after
reset. The class harness creates no FD evaluation jobs.

Raw reports: [Chromium](functional-dependencies-prepared/600-chromium.json),
[Firefox](functional-dependencies-prepared/600-firefox.json),
[WebKit](functional-dependencies-prepared/600-webkit.json).

## Artifact and regression evidence

[identity.json](functional-dependencies-prepared/identity.json) records exact host,
provider payload, wheel/sdist hashes, the 42-file artifact handoff inventory,
and source hashes for the local uncommitted implementation/test changes.
The installed host source is unchanged. The plugin wheel is portable and its
source-distribution rebuild has the same provider payload. English/German bundles
match that installed payload; the handoff verifies all installed resource bytes.

- 151 installed-package/artifact tests passed, plus both LaTeX authoring/export
  tests. Coverage includes bounded large answers, all modes, privacy, replacement,
  restart, transaction rollback, failed hooks, forged grade fields, and 1,873
  distinct-answer comparisons between prepared checks and full analysis.
- 30 standalone Node engine cases passed. Each browser passed 34 engine samples
  and real CSP probes: fetch, XHR, WebSocket, EventSource, nested/blob workers,
  external modules, eval and Function remained blocked. Deadline, invalid-result,
  teardown and recovery checks passed with the production restrictions.
- Full English presenter/phone workflows passed in all three browsers, including
  drafts/focus, keyboard/touch, alternative keys and counterexamples, sharing,
  walkthroughs, points and reset. German UI checks passed with English browser
  locales, an 800×500 presenter and a 320×740 phone viewport.
- Generated worker files are current. Workflow YAML and whitespace checks passed.

The engine, lesson and German UI JSON reports are retained alongside the raw
capacity reports. There is no new hosted CI result or catalog release. The
collection workflow retains strict 600-student timing gates and now uses distinct
answers and changed replacements. The separate 1,000-student headroom timing is
informational; its correctness/privacy/points assertions still fail on errors.
No new 1,000-student latency result is claimed here.

## Reproduce

Install the exact wheels from the verified handoff in a fresh FD-only environment;
see the [release procedure](../fd-release.md). Use the rebuilt English bundle and
run each browser separately:

```text
BROWSER=chromium                     # repeat with firefox and webkit
TEXSTAGE_CLASSROOM_ACTORS=600
TEXSTAGE_CLASSROOM_MODES=practice,keys_all,refuted
TEXSTAGE_CLASSROOM_DIVERSE=1
TEXSTAGE_CLASSROOM_REPLACE=1
TEXSTAGE_CLASSROOM_RECONNECT=1
TEXSTAGE_CLASSROOM_ENFORCE=1
```

Run `node maintenance/fd_classroom_browser.cjs <English lesson.bundle>` with
`PYTHON` pointing to the isolated interpreter and the browser binaries installed.
PowerShell uses `$env:NAME='value'` for the settings above. Physical-phone checks
remain deferred under the requested automated-only scope.

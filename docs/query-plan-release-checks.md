# Query-plan classroom and release checks

The classroom guide is [query-plan-lesson.md](query-plan-lesson.md). These are
maintainer checks for its release candidate, not instructions to migrate courses.
Use an isolated environment with exactly the Query-plan provider and a compatible
installed TeXStage wheel. API 1 is experimental: the host version alone does not
identify its code. Record the host wheel hash, provider payload and source commit.

## Automated release workflow

Run **Query-plan release conformance** in GitHub Actions with the full, reviewed,
published TeXStage commit SHA. There is deliberately no default branch or tag.
The producer verifies the checkout, installs hash-locked dependencies, builds
portable wheels, checks source-distribution parity and compiles English/German
LaTeX editions. Its tests must have no skips.

Windows and three independent browser jobs consume those exact wheels and the
Linux-authored bundle. The handoff helper rejects missing, added or changed files,
checks the expected host commit and verifies the installed host resource inventory
and provider payload. A fourth consumer measures 600 synthetic participants.
The existing other-provider conformance workflow remains separate.

An available workflow file is not evidence of a successful hosted run. Record its
run URL after publishing the reviewed code and choosing a compatible immutable
host commit. Do not use an older public host merely because its version matches.
The local validation record lists the remaining publication gates.

## Reproduce the load probe

Build the prepared example once in a new output directory:

```powershell
python maintenance/query_plan_authoring_probe.py --output artifacts/query-plan-editions
$env:PYTHON=(Get-Command python).Source
$env:BROWSER='chromium'
$env:QUERY_PLAN_LOAD_ACTORS='600'
$env:QUERY_PLAN_LOAD_ROUNDS='3'
$env:QUERY_PLAN_LOAD_LEASE_LOSS='1'
node maintenance/query_plan_load_browser.cjs artifacts/query-plan-editions/out/lesson.bundle artifacts/query-plan-load
```

Install the selected Playwright browser first. The probe uses real authenticated
WebSockets, a disposable host profile and one real presenter evaluator. It never
fabricates results or weakens the worker policy. It records:

- A simultaneous 600-answer burst, with receipt p95 at most 5 seconds and
  final completion at most 60 seconds on the measured machine.
- Every presenter roster page and selection from the last page. The default
  workload does not fill storage; a separate 1,000-actor run checks refusal of
  actor 1,001. Unit tests also verify replacement at storage capacity.
- Three rounds of replacements, separated by one second after each round's
  acknowledgements. This is a finite burst workload, not a fixed arrival-rate
  or hours-long soak test.
- Replacements while the evaluator is absent, followed by feedback after close.
- Two abandoned jobs after an observable disconnect, then a silent evaluator
  that leaves its socket open; the latter exercises the unchanged 120-second lease.
- Latest-answer feedback, role privacy and reset across all connected actors.
- With the scored example: zero totals before reveal, the correct fixed award
  in each phone's activity feedback and normal total after reveal, and withdrawal
  of all these awards on reset. See [points](query-plan-points.md).

`report.json` includes acknowledgement/completion quantiles, completion order,
actor quartiles, traffic, versions and bounded deadlines. Intermediate versions
without an observed completion are marked superseded: host state coalescing can
also hide an intermediate projection. Completion order is observed evidence,
not a proof of scheduler fairness. Loopback synthetic clients do not establish
Wi-Fi, phone-battery, rendering or Internet capacity. A silent evaluator's lease
legitimately adds roughly two minutes; an observable disconnect can requeue work
earlier. Do not reduce the production lease to make a test pass.

## Physical phone and classroom LAN gate

Use a disposable session of the prepared example on the intended classroom
network. Record server/browser/phone OS versions and the bundle/provider hashes.
Serve through the normal TeXStage CLI/profile, choose its LAN interface and join
using the displayed phone URL/PIN. This must include plain LAN HTTP; localhost
desktop emulation does not test an insecure mobile origin.

1. On an actual iPhone/Safari and an Android/Chrome device, join under distinct
   nicknames. Open Library joins, change scan/join/build-side controls, inspect
   node costs, preview, undo and submit. Confirm preview hashing works over HTTP.
2. Rotate and zoom; operate with touch and the software keyboard. Check labels,
   scrolling, focus and submit feedback without clipped controls.
3. Save from both phones, close, select/share anonymously, clear sharing and
   reveal. Neither phone should see the other's answer or an unrevealed solution.
4. Temporarily disconnect one phone, edit its draft, reconnect and reconcile it.
   Use another device for the same actor to exercise the keep/reload choice.
5. Close/reopen the presenter while answers are pending, then reset and navigate.
   Confirm that no previous answer/solution survives the new activity epoch.

Keep the session URL, PIN and participant identifiers out of public evidence.
This gate needs actual devices and access to the intended network.

## Assistive-technology gate

Use a real screen reader (for example VoiceOver/Safari and NVDA/Firefox), not only
an accessibility-tree assertion. Work through join, plan editing, node inspection,
preview, submission, a stale-answer conflict and reveal without a mouse. Confirm
announced labels/status, sensible focus order, no focus trap and readable cost
arithmetic in both English and German. Record screen-reader/browser versions,
the exact steps, issues found and retest results.

## Evidence record

For each manual gate record date, tester, versions, artifact identities, pass/fail
per step and issue links. Leave unchecked steps explicitly pending. Only after
these checks and successful hosted jobs should a reviewed catalog entry and
immutable release be prepared. Publication is a separate authorized action.

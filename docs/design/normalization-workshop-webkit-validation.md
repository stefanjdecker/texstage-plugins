# Normalization Workshop: WebKit follow-up

Date: 2026-11-07. This record supersedes the capacity finding in the
[earlier load validation](normalization-workshop-load-validation.md). It is
local evidence, not a public release or a physical-classroom acceptance test.

## Outcome

The 64-student, two-activity workload now passes the unchanged responsiveness
budgets in Chrome, Firefox and WebKit. The slower WebKit item's p95 fell from
38.91 seconds on the earlier artifact to 14.63 and 14.98 seconds in two runs.
No additional host or provider runtime change was needed in this follow-up.

The tested host includes commit `9d663cfc4940fac624143b20a2338ab5429bc2c8` plus
the existing language/accessibility working-tree changes. Its immutable asset
cache avoids repeated downloads while cloning bytes into a fresh worker for
every job. Cost-aware broadcasts leave time for job delivery and socket replies.
Schema safety checks are cached by exact content, while instance validation owns
a fresh snapshot, including any schema exposed by a validation error.

Worker state is not shared. Two-job leases, owner/generation/epoch checks,
evaluation deadlines, result validation and the production worker CSP remain.
The provider stays at 0.3.1, with identical schemas, engine, reducer, authoring
and renderer resources.

## Measured workload

The exact prepared fixture from the previous test was reused. It contains the
registration decomposition and tutor classification examples. Synthetic students
join through authenticated sockets; the presenter uses the real installed
evaluator. The test includes initial submissions, immediate replacements,
capacity refusal for actor 65, two simultaneously active items, and a presenter
reconnect with two deliberately abandoned leases.

Targets remain ACK p95 <= 5 s, checked-answer p95 <= 30 s, and reconnect maximum
<= 150 s. Each required final batch finishes with 64 checked latest answers;
obsolete replacements are excluded from latency acceptance. Values below are
seconds; all timing runs were sequential, before the regression suites.

| Browser/run | Initial checked p95 | Replacement checked p95 | Slower two-item checked p95 | Reconnect maximum |
| --- | ---: | ---: | ---: | ---: |
| WebKit, reproduction | 5.80 | 6.46 | 14.63 | 8.52 |
| WebKit, strengthened repeat | 6.09 | 7.51 | 14.98 | 8.62 |
| Chrome | 2.75 | 4.27 | 5.88 | 5.60 |
| Firefox | 5.57 | 5.47 | 10.06 | 8.65 |

Both abandoned jobs were re-leased and successfully completed in generation 2.
All latest answers completed, before-reveal private fields stayed withheld, and
no page or hook errors were recorded. This establishes bounded completion for
these workloads, not fairness or a capacity guarantee for arbitrary exercises,
64 real mobile browsers or a classroom network.

The 64-slot storage bound is unchanged. The previous 32-group WebKit guidance
applied to the older host artifact; the new provisional synthetic pilot bound
is 64 for these exercises on the measured setup. Physical phones, screen-reader
users and a real teaching-host pilot remain required.

## Stronger regression evidence

The load harness now checks that a checked answer equals the latest submitted
answer. Its report also fails if a required phase or actor is missing, a latest
job lacks an accepted successful result, or both abandoned reconnect jobs were
not demonstrably retried and completed. Merely reopening the presenter is
insufficient. Reports use format 2.

A separate pure evidence checker has 13 tests, including missing phases,
duplicate actors, refused submissions, missing/failed/rejected completions,
wrong generations and unrelated retries. Explicit smoke runs record that
abandoned-job coverage was not performed.

The existing engine probe's obsolete “engine only, no content capability” label
was corrected to describe its actual verification scope. The plugin capability
itself is unchanged.

## Verification

- Host suite: 127 passed, 1 skipped (Windows symlink privilege).
- Installed Normalization Workshop suite: 52 passed.
- Evidence-checker suite: 13 passed.
- Full classroom UI sequence passed in all three browser engines: both modes,
  sharing/comparison, reveal, conflict handling, reset, navigation, focus/drafts,
  evidence playback and private transport.
- Active security probes passed in all three engines: fetch, XHR, EventSource,
  sockets, external modules, dynamic code and child workers were blocked by the
  actual production policy. Unrestricted controls first demonstrated that the
  fixtures work. No forbidden request reached the test endpoints.
- Invalid typed results were rejected, looping engines were terminated at the
  two-second deadline, workers were cleaned up, and a fresh real engine recovered.

The full security results and per-browser status/timings are in the companion
JSON. The existing PDF/LaTeX export regression ran as part of the provider suite;
no authoring source or style changed. No new human accessibility review or
physical-phone test is claimed.

## Artifact identity and reproduction

Host wheel SHA-256:
`a8c8370c0ba2b95c62d20bad83d994e484138669a67fcff2cc5f31d66eef108a`

Provider wheel SHA-256:
`d6594541e56cb9c1c21e87c2f3d63330a8d2df04bb3848069a560ba1b24bbecc`

Provider payload:
`8b97cd83a1cb0130762ac18cb195dc3147c221fe7390f93306f92ba5cfad94a1`

The companion JSON records the host source snapshot, dependency locks, exact
fixture inventory, reports and tested harness hashes. The version
`0.2.1.dev3` alone does not identify this host. The original N2/N4 records retain
provider build/sdist evidence; this follow-up reuses that unchanged 0.3.1 wheel.

Using the matching installed host/provider wheels and the locked dependencies:

```sh
node --test maintenance/normalization_load_checks.test.cjs
python maintenance/normalization_load_probe.py --output artifacts/normalization-load-fixture
node maintenance/normalization_load_browser.cjs artifacts/normalization-load-fixture/build/load.bundle
python maintenance/normalization_probe.py --output artifacts/normalization-engine
node maintenance/normalization_browser.cjs artifacts/normalization-engine
```

Set `PYTHON` to the selected environment's Python and `NORMALIZATION_ACTORS=64`.
The full load test leaves `NORMALIZATION_SKIP_RECONNECT` unset or set to `0`.
Use a fresh `NORMALIZATION_LOAD_OUTPUT` directory for each run and a free
`TEXSTAGE_TEST_PORT`. Select `BROWSER=webkit`, `firefox` or `chromium`;
`TEXSTAGE_BROWSER_CHANNEL=chrome` applies only to Chromium.

Local reports, synthetic timing traces, UI screenshots and the final host wheel
are retained under ignored `artifacts/normalization-webkit/`. Synthetic server
profiles and their authentication tokens are not copied as release artifacts.
Original repositories, existing courses and their environments remain unchanged.

## Remaining release gates

The automated WebKit capacity gate is closed for this workload. Keep the same
budgets and fresh-worker restrictions in future regressions. Remaining gates
are physical Android/iPhone LAN testing, human screen-reader and new-learner
review, a published compatible host pin, hosted cross-platform CI and reviewed
catalog publication. No commit, push, publication or course migration is
performed by this follow-up.

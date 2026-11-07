# Query-plan Q5: local release validation

Validated on 7 November 2026 (Europe/Berlin), using installed portable wheels.
The provider remains **0.4.0**: this milestone adds release tooling, measured
classroom evidence and host hardening. It does not change its teaching model,
authoring contract or package payload.

The [machine-readable record](query-plan-release-validation.json) contains exact
artifact identities, OS/browser versions, test counts, load quantiles and
remaining gates. The [reproduction and manual-check procedure](../query-plan-release-checks.md)
describes how to repeat the checks.

## What was measured

The load probe connects 64 synthetic students through real authenticated host
WebSockets. One actual presenter page evaluates their plans under the production
worker policy. It covers an initial burst, three rounds of replacements, an
absent evaluator, grading after close, observable disconnects, a silent evaluator,
private/latest-answer feedback and reset. A 65th actor is refused while existing
actors can replace answers. Engine outcomes are never fabricated.

| Combined-host scenario | Acknowledgement p95 | Maximum observed completion |
| --- | ---: | ---: |
| 64 simultaneous submissions | 0.58 s | 7.47 s |
| Three rounds of 64 replacements | 1.69 s | 9.55 s |
| Replacement while evaluator absent | 2.43 s | 13.34 s |
| Six submissions, two leases lost on disconnect | 0.10 s | 2.38 s |
| Six submissions, two leases held by a silent evaluator | 0.10 s | 121.30 s |

An observable disconnect recovered in 1.74 seconds after loss; a silent evaluator
recovered in 120.66 seconds. The latter still uses the real 120-second lease.
All 64 actors received feedback for their latest saved plan; none remained pending
or unavailable. Reset removed all previous answers. The final six deliberately
submitted baseline plans correctly missed the target; this is not an operational
failure.

These are measurements on one Windows workstation with 16 logical CPUs and
loopback networking; other verification jobs shared the machine. They are not
capacity guarantees for phones or Wi-Fi, nor an isolated hardware benchmark.
The replacement workload is finite and acknowledgement-paced, not a fixed
arrival-rate soak test. Completion order and actor quartiles are recorded, but
general scheduler fairness is not proven.

## Host findings and integration

The original host repeatedly checked the same JSON schemas while generating
every audience projection. Its initial 64-answer burst had a 121.02-second p95
acknowledgement and a 272.70-second maximum completion; evaluator-return recovery
later exceeded the probe deadline. That failed baseline is retained in the record.

A focused 100-call measurement of one actual participant view took 21.62 ms per
validation with repeated schema checks and 0.86 ms with a warm cache. Cache-only
host validation then completed the full earlier workload. The final integration
also preserves concurrent generic host improvements: coalesced audience
projections, immediate durable receipts, busy evaluator draining and requeueing
after an observed disconnect.

The cache hardening added here stores only successful checks of immutable schema
content. Every data value is still validated against a fresh schema snapshot.
Mutating a schema exposed through a validation error cannot alter future checks.
External references/scopes remain forbidden; the cache has bounded entries and
key sizes. Worker CSP, view/message limits, authorization and lease expiry remain
in force. No Query-plan-specific logic was added to the host.

## Verification

- Windows: **158 Query-plan tests and 19 release-tooling tests passed**, including
  actual English/German LaTeX authoring and static exports.
- Windows host regressions: **122 passed, one skipped** because the sandbox could
  not create a symlink. Linux runs that symlink check.
- Linux (Ubuntu 24.04 under WSL2, Python 3.12): **174 passed, three skipped**
  across Query-plan and release tooling. Those three need TeX, which was absent
  from this Linux environment; they passed on Windows.
- Linux host regressions: **122 passed, one skipped** for its TeX-dependent test.
- Chromium/Chrome 156, Firefox 153 and WebKit 26.5: real evaluator/security,
  actual phone/presenter controls, lifecycle/protocol and static-exercise checks.
  Firefox required execution outside the automation sandbox to create pages;
  the host's worker restrictions were unchanged.
- Independent regressions: transaction engine **67 passed**, relational lab
  **72 passed**, original coordinate/distance pair **four passed**; their real
  browser checks run separately in all three browsers.
- The identical provider wheel passed on Windows and Linux. Rebuilding its source
  distribution on Linux reproduced the provider manifest and resource payload.
  Archive hashes may differ because a rebuild is not byte-for-byte reproducible.
- The dedicated workflow's YAML, immutable action/host pins, artifact consumers
  and locked-dependency requirements were checked locally. Handoff tampering,
  missing/extra files, unsafe paths and identity drift are regression-tested.

The Windows pair tests emitted an existing Starlette/httpx deprecation warning.
No test assertions or security policy were weakened to obtain these results.

## Artifact and publication status

Provider wheel SHA-256:
`46d5c4b8e695d43afddb752b8c6f56d0606d84345679e93b409308261d00a4da`.
Provider payload:
`c8bbe936f167fb47db93156b78ea00848420ce4d364246373eb93d9119ad732e`.

The recorded wheel is the frozen Q4 runtime artifact reused for these checks.
Q5 updates to repository documentation, including the package README, are
outside that captured wheel's metadata. The provider code and resource payload
are unchanged; the hosted producer will build and record fresh release archives.

The final host is an **uncommitted development snapshot**, based on
`de3351550f3553ca63023554521fbe84806ec94e`, plus the recorded classroom work and
cache hardening. Its installed resource inventory is
`c71f83d1af25f6b6446ab2c66e4820f73d8abe0e6103c8ccac58ce702ba06592`;
the exact wheel hash is in the JSON record. The base commit and version
`0.2.1.dev3` alone do not reproduce this artifact.

The new **Query-plan release conformance** workflow requires a full published
compatible host SHA, creates one Linux producer handoff and installs identical
artifacts in Windows, browser and load jobs. It has **not run on GitHub Actions**.
No catalog entry or release was published.

Remaining gates are physical iPhone/Android testing over classroom LAN HTTP,
real screen-reader review, a reviewed published host commit and successful hosted
jobs. Existing courses, their environments, the original repository and private
video material were not changed.

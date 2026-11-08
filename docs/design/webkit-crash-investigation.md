# WebKit classroom crash investigation — 2026-11-08

The reproduced Linux presenter crash is a native WebKit Inspector failure in
HTTP cache revalidation. It is not a plugin scoring error or a memory-exhaustion
failure. A focused TeXStage host workaround is on `codex/webkit-load-crash`;
the plugin algorithms and classroom limits are unchanged.

## Cause and evidence

The original transaction and B+ probes were run against the exact candidate
wheels and synthetic decks from the earlier CI artifacts. A Linux diagnostic
wrapper records browser stderr, descendant process resources and native core
backtraces. It preserves the original probe exit status and all performance
and correctness gates.

In the [browser comparison](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42465030983),
10 of 12 runs crashed: each browser build failed two of three transaction runs
and all three B+ runs. Playwright 1.62.1 uses WebKit 26.5/build 2336;
the 1.64.1 comparison uses WebKit 27.2/build 2370. Updating to that comparison
build did not solve the problem. Each workload ran 1,000, 600, then 1,000 students.

All ten native traces show `SIGSEGV` in `libWPEWebKit-2.0.so.1` with a null `rdi`
at `mov 0x8(%rdi),%eax`. For build 2336 the library-relative fault offset is
`0x2c4351e`. Disassembly identifies the shared-buffer iteration operation; its
caller checks HTTP status 304, obtains a potentially null previous response
buffer, and then iterates it. This matches
[WebKit's upstream fix](https://github.com/WebKit/WebKit/commit/4103f690caccac6199a3dd6f59409668d584ecc6)
for bug 328941, committed 2026-10-27. The shipped library is stripped, so this
function identification uses disassembly and matching source, not full debug
symbols.

The crashing processes peaked at 445–497 MiB RSS with 39–45 open descriptors;
the runners retained more than 13.68 GiB of available memory during those failing
runs. There is no out-of-memory signature in the captured failures. Four local
Linux-container runs passed before CI reproduced the fault, illustrating its
timing dependence. Those local passes alone were insufficient evidence.

## Controlled HTTP experiment

The [A/B run](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42465856190)
kept Playwright 1.62.1, the original installed host and plugin wheels, fresh
workers, browser flags and deadlines fixed. It changed only whether conditional
request headers reached the server for:

- `/static/stage/plugin-evaluator-worker.js`
- `/static/stage/plugin-contracts-worker.mjs`

| Workload, three runs each | Original conditional requests | Full bootstrap responses |
| --- | --- | --- |
| Transactions: 1,000 / 600 / 1,000 students | 3 native crashes | 3 passes, all original gates |
| B+: 1,000 / 600 / 1,000 students | 3 native crashes | 3 passes, all original gates |

The HTTP observations captured repeated 304 responses for exactly these two
paths in the failing controls. The experimental wrapper is opt-in and exists
only in the synthetic load server. `observe` records responses without changing
them; `worker-200` is an experiment, not a passing production configuration.

## Host workaround and regression validation

Host commit `ee9cdf1752ae01f623bcef8bb93df13e3773073c` sends those two small files
with `Cache-Control: no-store` and a full response even when an older cached copy
supplies validators. Ordinary UI files retain their revalidation, and provider
assets retain immutable caching. Worker CSP, per-job isolation, validation,
timeouts, four-worker ceiling and SQLite FULL durability remain intact.

The installed-wheel HTTP/server suite passed 28 tests locally; one recording
remux test was skipped because that container lacks ffmpeg. New regressions cover matching ETags, Last-Modified validators,
wildcard validators and HEAD requests, including preserved security headers.

The [host CI](https://github.com/stefanjdecker/texstage/actions/runs/42466372269)
and [installed candidate validation](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42466498513)
are the authoritative final checks. The latter builds the host once and uses
that identical wheel in six workload/browser jobs. It runs both language UIs,
active worker confinement probes, and the unmodified classroom gates. WebKit
repeats 1,000 / 600 / 1,000; Chromium and Firefox each run 1,000. HTTP diagnostics
use observation mode only, so no test-side workaround substitutes for the host
change.

All final jobs completed successfully:

| Check | Result |
| --- | --- |
| Host CI | 5/5 jobs pass: Ubuntu Python 3.12/3.13/3.14, Windows 3.14 and container startup |
| Candidate producer and workload/browser jobs | 7/7 jobs pass |
| Installed-engine worker security | 6/6 probes pass; all ten forbidden operations blocked, invalid results rejected, infinite loop timed out and subsequent evaluation recovered |
| English/German plugin UIs | 12/12 runs pass |
| WebKit classroom loads | 6/6 pass at 1,000 / 600 / 1,000 per plugin; zero native crashes |
| Chromium/Firefox classroom loads | 4/4 pass at 1,000 students; all original gates |

The final transaction WebKit acknowledgement p95 values were 1.919 seconds
(1,000), 0.986 seconds (600), and 2.258 seconds (1,000). B+ scoring, replacements,
score withdrawal and evaluator recovery passed. No final load produced a 304
for either bootstrap path. These are synthetic runner measurements, not a
hardware-independent capacity guarantee.

All six consumers installed the identical host wheel with SHA-256
`279bd3ef70ab636973c8d6afac4b3ac1d8cf6a03ed51b08d7a98c9043d8567a8`.
The [machine-readable record](webkit-crash-investigation.json) retains all 34
comparison/load cases, including failures, provider wheel hashes, native trace
digests and the final security/UI results. The final validation uses collection
revision `3528cc7fc3deb8dc3b34cddb7db53d47eb038c7b`; later documentation-only
commits do not change its runtime or harness.

The main-branch merge also updates the general conformance and B+ capacity
defaults, and supplies a transaction-workflow default, to the verified host
revision `ee9cdf1752ae01f623bcef8bb93df13e3773073c`. Explicit host inputs remain
available for compatibility comparisons.

## Reproduction and limits

The diagnostic workflow pins the host revision and consumes the earlier
transaction and B+ artifact handoffs. Its `identity` artifacts retain wheel
hashes, collection commit, browser build, CPU and system-package versions.
The native runs retain `browser.log`, `processes.jsonl`, load reports and GDB
backtraces. Raw cores are not uploaded. Hosted artifacts expire after 14 days;
archive them before expiration to reproduce the exact wheel bytes later.

Run the wrapper on Linux after installing matching wheels, locked Node/Python
dependencies and the browser:

```sh
TEXSTAGE_DIAGNOSTIC_HTTP=observe python maintenance/webkit_diagnostics.py \
  transaction /path/to/lesson.bundle artifacts/native-1000 --actors 1000
```

Use `bplus` with the B+ lesson bundle for the other workload. Outputs must be
new directories. The wrapper has a ten-minute process deadline and preserves
failed gates. Core configuration in CI is limited to its disposable hosted
runner; do not overwrite a developer workstation's crash handler.

This investigation establishes the cause and workaround for the captured
automated WebKit failures. It does not establish behavior on physical Safari
devices or classroom networks. The deferred
[device checklist](../classroom-device-checklist.md), unrelated acceptance
issues, and the host's unresolved publication license remain separate gates.
No release tags, package publication or catalog activation are part of this
investigation. Original tools, courses, prior worktrees and private media are
kept unchanged.

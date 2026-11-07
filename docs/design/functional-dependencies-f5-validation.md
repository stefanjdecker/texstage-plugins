# FD Lab F5: hosted release conformance

Date: 2026-11-07. The experimental candidate passes hosted functional,
packaging and browser conformance. Classroom capacity is still an open gate:
the additional local load checks below did not reproduce all earlier targets.
No catalog release or merge to `main` is included.

## Published source and CI

- Host: [`34d0c537135f32b0690147dbb66dd8ff155987f8`](https://github.com/stefanjdecker/texstage/commit/34d0c537135f32b0690147dbb66dd8ff155987f8),
  on `codex/plugin-system`, mirrored to the GitLab code repository.
  [Host CI](https://github.com/stefanjdecker/texstage/actions/runs/42351229078)
  passed all five jobs: Linux Python 3.12/3.13/3.14, Windows Python 3.14 and container startup.
- Collection: [`d5c40160fe9dcb07491b86e04e0b96c8c7ccf1d2`](https://github.com/stefanjdecker/texstage-plugins/commit/d5c40160fe9dcb07491b86e04e0b96c8c7ccf1d2),
  on `codex/fd-release-conformance`.
  [Collection CI](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42351969530)
  passed all 19 jobs, including the existing coordinate/distance, transaction
  and relational checks. The release branch keeps concurrent provider development
  out of this candidate. This record is a subsequent documentation-only change.

The [first collection run](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42351704342)
failed before affected tests could run because the FD and relational jobs did
not create the parent of their pytest temporary directories. The tested commit
creates those directories; no assertions, security policies or timing targets
were relaxed.

The host changes finalize keyboard handling inside plugin controls, deck-language
propagation with browser fallback, and presenter scrolling at small viewports.
The FD workflow now pins the published host, requires both authoring languages,
and verifies artifact identity before and after installation in every consumer.

## Tested artifacts

The Linux producer built FD Lab 0.3.0 once, verified sdist resource parity and
passed the exact host/provider wheels and English/German bundles to Windows
and all three browser jobs. The downloaded `fd-lab-wheels` artifact (ID
`13565928578`) passed all 42 file inventory, size, SHA-256 and host-pin checks.

| Artifact | SHA-256 |
| --- | --- |
| `texstage-0.2.1.dev3-py3-none-any.whl` | `5ad3eb2371e7490a8345e3453e4067407027c7c774b3118e6917762a4e3fdcbc` |
| `texstage_fd_lab-0.3.0-py3-none-any.whl` | `7de1be2353fcda693ba61d5b697a6b1af4220d27aebd68fd463ec6d35b644dad` |
| `texstage_fd_lab-0.3.0.tar.gz` | `7bf8a7daf24ce061f078426514e8b90dc8164336df107e288cf1f6d0e9a6c26b` |

Provider: `io.github.stefanjdecker.fdlab`, version `0.3.0`, payload
`ea2c7777c6c3580a1011ad17fcc6a2571a92e4ed8b1cc4d784ac369208556420`.
The [machine-readable record](functional-dependencies-f5-validation.json) retains
the full handoff inventory, CI job/artifact IDs, schema hash, reports and local
artifact identities. Independent local and Linux builds have distinct wheel
hashes; cross-platform conformance uses the identical Linux-built wheels.

Source-normalized resources have a different payload from the older F3/F4
artifacts. Do not reuse those pins for this candidate. A development version
string alone identifies neither the host commit nor the tested provider payload.

## Coverage

| Check | Result |
| --- | --- |
| Linux Python 3.12 FD and handoff-helper tests | 112 passed, no skips |
| Windows Python 3.14, identical Linux wheels | 110 passed; only two TeX authoring cases skipped |
| English and German authoring on Linux | Slides, handouts, solutions, direct-pdfLaTeX exports and freshness checks executed |
| Chromium 151.0.7922.34, Firefox 153.0, WebKit 26.5 on Ubuntu 24.04 | Engine/security, full English lesson and German UI passed |
| Local Windows host regression selection | 155 passed, one symlink-permission skip |
| Local Windows FD and helper suites | 98 + 14 passed, including both TeX authoring cases |

The English lesson covers closure, one/all keys, positive implication,
counterexamples, differently sized keys and the empty key. It checks private
transport, feedback phases, drafts/focus, two devices for one actor, sharing,
reset, keyboard/touch interaction and teardown. German UI tests use an English
browser locale and exercise real evaluation, keyboard submission, touch,
an 800×500 presenter and a 320-pixel phone viewport. Surrounding example slide
titles remain English; this is provider localization coverage.

The worker policy remains
`default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'`.
Active probes verify blocked connections, child workers and dynamic code against
working unrestricted controls. Invalid results, timeout cleanup and subsequent
recovery pass; the two-second evaluation deadline is unchanged.

Local German exercise/solution pages and the Linux-generated German solution
page were rendered and visually inspected. The CI WebKit phone and presenter
screenshots are readable without horizontal clipping; the small presenter
workspace requires vertical scrolling.

## Local capacity follow-up: not a passing gate

These runs used the separately recorded local Windows artifacts on an Intel
Core i9-11950H, 16 logical CPUs, 64 GiB RAM and Windows 10. They use loopback,
64 protocol actors, one rendered participant and one actual presenter evaluator.
The unchanged targets are input p95 below 100 ms, feedback p95 below 10 s and
worst feedback below 30 s. Timing enforcement remained enabled.

| Run | Result |
| --- | --- |
| Initial Chromium 156.0.8078.80 | All feedback targets passed; all-keys input p95 was 108.3 ms, exceeding 100 ms |
| Confirmation Chromium 156.0.8078.80 | All-keys input p95 225.5 ms and counterexample input p95 158 ms exceeded 100 ms; all feedback targets passed |
| Confirmation Firefox 153.0 | All three modes passed; feedback p95 at most 3.67 s and input p95 at most 5 ms |
| Confirmation WebKit 26.5 | Timed out waiting for slide views before the first burst; no throughput or reconnect result |

Completed Chromium/Firefox runs retained 64 actors with zero pending jobs,
FIFO lease order, evaluator replacement, same-actor resume, receipt replay,
close-with-pending completion and rejection of stale/reset results. Causes of
the input delays and WebKit setup timeout have not been established. Earlier
[F4 performance results](functional-dependencies-f4-performance.md) remain valid
for their recorded runs; they are not a passing capacity claim for this candidate.

## Remaining work

Diagnose the input-latency misses and WebKit slide-view timeout before claiming
64-student readiness. Test on the intended lecture hardware/network when that
scope is authorized. Physical phones remain explicitly deferred; desktop
emulation does not establish iOS/Safari, LAN or full accessibility coverage.

CI artifacts expire after 14 days. A catalog release still needs reviewed,
immutable published assets and exact compatibility/license/ownership metadata.
No course environment, original repository or private media was changed.

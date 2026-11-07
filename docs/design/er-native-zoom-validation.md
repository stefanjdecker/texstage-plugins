# ER 0.4.1: native zoom and current-host validation

Recorded 2026-11-07. This follow-up adds native browser-zoom regression coverage
and rechecks the registration activity against the host's newer performance
and layout changes. The provider wheel is unchanged. This is local Windows
evidence, not a hosted-CI result or a published release. The
[machine-readable record](er-native-zoom-validation.json) contains artifact
identities, installed host file hashes, browser results and load timings.

## What changed

- `maintenance/er_accessibility_browser.cjs` accepts `ER_NATIVE_ZOOM=2` for
  Chrome. It creates disposable profiles, sets and verifies native 200% page
  zoom, records actual viewport/pixel-ratio measurements, and removes its
  browser profiles after closing them. It does not alter the user's browser.
- English and German checks cover the complete keyboard answer workflow,
  invalid-field focus, conflict recovery, private inspection, reaching the
  sharing button without sharing, and scrolling projected alternatives to the
  end. The presenter panes and toolbar must remain separate and scrollable.
- Screenshots use the browser's compositor at native zoom. Ordinary
  Chromium/Firefox/WebKit checks retain the 320-pixel participant viewport and
  separate doubled-text check. These are distinct measurements.
- The ER workflow adds a separate native-zoom job consuming the producer's
  verified host/provider wheels and both language bundles. Its YAML was
  parsed locally; the hosted job has not run.

No provider resources, schemas, grading, authoring commands, security policy,
worker limits or course locks changed in this follow-up. No host source was
edited here; existing concurrent host changes were copied into an isolated
test build and preserved in their repository.

## Exact artifacts

| Artifact | SHA-256 |
| --- | --- |
| ER 0.4.1 portable wheel | `3386caff13a282990731e4c5f5af8fb926c40625fb32132e17a393026dbf6635` |
| Current host wheel, 0.2.1.dev3 | `f5d4bf61411383f313e88763ad0af8b24ab8de5c0755990fbe7a557c69713bc9` |
| Installed host payload | `a2d32721acbae6a71dacd4c9a589dae62217c55f70af1cd88868f72ea1de1d27` |

ER payload:
`88c634e0aa7f1eb0a4067e4aeaef1b3c75898aed801a7034c17be3bfd8e72d99`.
Provider state schema remains 2. Its source/wheel/sdist parity and identical
Windows/Linux consumption were established in the
[previous artifact record](er-accessibility-validation.md). The newer host
wheel in this record was tested on Windows only; those earlier Linux results
must not be attributed to this newer host.

The host snapshot is based on
`9d663cfc4940fac624143b20a2338ab5429bc2c8`, including the asset-cache and
cost-aware broadcast changes, plus uncommitted language/lifecycle propagation
and short-window presenter-layout work. That commit alone, or the version
string alone, does not identify the tested wheel. A reviewed published host
commit containing the required changes is still needed for hosted CI.

## Results

| Check | Result |
| --- | --- |
| Windows ER engine/authoring/state/package tests | 107 passed; three real-TeX cases explicitly deselected |
| Artifact-handoff helper tests | 9 passed |
| Focused host contracts, schema-cache safety, classroom scheduling, asset cache, lifecycle and server tests | 124 passed; one existing Starlette/httpx deprecation warning |
| Independent Python/JavaScript model comparison | All 27 registration models passed |
| 320-pixel keyboard, focus, ARIA and doubled-text workflow | English and German passed in Chromium, Firefox and WebKit |
| Native 200% Chrome zoom | English and German passed, including private inspection and projector keyboard scrolling |
| Restricted-worker integration | Chromium, Firefox and WebKit passed, including blocked network/nested workers, invalid results, timeout termination and recovery |

Runtime: Windows, Python 3.14.4, Node 24.15.0, Playwright 1.62.1. Standard
browser versions were Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5.
Native zoom used installed Chrome 156.0.8078.80. The disposable Chrome windows
changed from 1422 x 904 CSS pixels at device-pixel ratio 1 to 711 x 452 at
ratio 2; visual-viewport scale stayed 1. The participant browser used the
opposite locale from the deck, checking that lesson language follows the deck.

Screenshots of English/German participant models, presenter controls and
German private inspection/projected alternatives were visually reviewed.
At 200% some content needs scrolling; the tests verify that the private
inspection controls and the final projected explanation remain reachable by
keyboard. This is not a claim that the whole activity fits on one screen.
Reproduction commands and remaining manual checks are in the
[accessibility guide](../er-decisions-accessibility.md). Reports, ARIA snapshots,
keyboard traces and screenshots are emitted to the chosen artifact directory;
disposable browser profiles are not included in the final native-zoom output.

## Classroom latency remeasurement

The existing load harness ran sequentially with no other ER browser tests
running. Hardware: Intel Core i9-11950H, 16 logical CPUs, about 63.2 GiB RAM.
The server and Chromium presenter were local; learners were authenticated
synthetic protocol clients. Timings measure send to observed evaluated/saved
status, before correctness feedback is revealed. They do not measure rendered
phones, classroom Wi-Fi or a remote teaching server.

| Actors | Cold p95 / last | Warm replacement p95 / last | Complete disconnect recovery |
| --- | --- | --- | --- |
| 32 | 1.89 / 1.89 s | 1.65 / 1.65 s | 2.45 s |
| 64 | 3.23 / 4.38 s | 3.97 / 3.97 s | 4.22 s |

Both runs met the warm targets (p95 at most 10 seconds; last at most 30
seconds). All answers were saved, private feedback remained withheld, duplicate
receipts did not create extra versions, and recovery preserved the host's
lease policy. The 64-actor run refused a 65th new answer as intended. Maximum
participant-item view was 8,140 UTF-8 bytes. Raw actor timings are retained in
the JSON record so percentile claims can be checked.

The earlier E5 64-actor latency failure remains valid for its older artifact;
it is superseded here only for this host snapshot and machine. The documented
pilot limit remains **32** until deployment and hosted checks are complete.
CI continues to enforce 32 actors and report 64 as a stress measurement.

## Remaining release gates

Physical Android/iPhone operation, screen-reader speech output, native
Firefox/Safari zoom and OS text enlargement, actual teaching-server load,
and the hosted workflow remain unverified. The same new host wheel has not
been re-consumed on Linux in this follow-up, nor have the other providers'
isolated regression suites been repeated here; those remain CI jobs. Review
the final immutable artifacts and catalog metadata before publication. No
package/catalog release, commit or push was performed by this follow-up.

# ER 0.4.1 accessibility and regression evidence

Recorded 2026-11-07. This patch improves the registration lesson's keyboard
and assistive-technology semantics. It is local development evidence; it does
not declare a screen-reader audit, hosted-CI pass or published release.
See the [keyboard guide and manual checklist](../er-decisions-accessibility.md)
and [machine-readable artifact record](er-accessibility-validation.json).

## What changed

- Incomplete choices expose a field-linked error and focus the first missing
  decision. Invalid reasons focus the reason field, including when saving
  from the model preview.
- Resolving a draft conflict restores focus to the visible preview heading
  or editor. Neither conflict choice automatically submits anything.
- Phase and answer messages use separate live regions. Unrelated revisions
  do not rewrite unchanged messages or recreate an unchanged model preview.
  Counts remain readable without announcing each classroom response.
- Activity regions have accessible names. Multiple mounts have independent
  radio groups and unique validation-description IDs.
- The bundle helper resolves relative output paths, fixing the documented
  command and CI's relative-path builds.

The engine, authoring semantics, state schema 2, grading, privacy policy and
worker security restrictions are unchanged. Rebuild example bundles and
enable the new inspected payload in a separate profile; existing course
locks and environments were not changed.

## Final artifacts

| Artifact | SHA-256 |
| --- | --- |
| ER 0.4.1 portable wheel | `3386caff13a282990731e4c5f5af8fb926c40625fb32132e17a393026dbf6635` |
| ER 0.4.1 source distribution | `acf111473ffc3e16b1c39278b1bdccaf1b05d132d65a2f1de6b84ff870264847` |
| Matching host wheel | `b9a8d5b5f08fbb2f21f0df763c414f5c03f090157270775ad7103350da9fdf38` |

Provider payload:
`88c634e0aa7f1eb0a4067e4aeaef1b3c75898aed801a7034c17be3bfd8e72d99`.
Source/wheel/sdist resource parity passed. Windows Python 3.14.4 and Ubuntu
24.04/WSL2 Python 3.12.3 consumed identical portable wheel files. Their installed
host payload hash matches:
`c71f83d1af25f6b6446ab2c66e4820f73d8abe0e6103c8ccac58ce702ba06592`.

The host includes existing uncommitted work on top of
`de3351550f3553ca63023554521fbe84806ec94e`, including the current schema-cache
safety fix. The commit or `0.2.1.dev3` version alone does not reproduce this
artifact; per-file hashes are in the JSON record. Concurrent host work later
added asset-cache and broadcast-scheduling refinements. Those source changes
are preserved; this record verifies the frozen wheel above, not those later
refinements. This ER patch changes host documentation only.

## Checks performed

| Check | Result |
| --- | --- |
| Windows ER tests, including real TeX editions | 110 passed; no skips |
| Linux consumer of identical wheels | 107 passed; three TeX cases explicitly deselected |
| Focused host contracts, schema safety, lifecycle and server tests | 119 passed; one existing Starlette/httpx warning |
| Independent Python/JavaScript registration oracle | All 27 models passed on both platforms |
| Package source/wheel/sdist resource parity | Passed |
| English and German disposable bundles with relative output paths | Built successfully |

Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5 passed:

- Both English and German keyboard/accessibility-tree workflows at 320 CSS
  pixels: field errors from preview, radio/Tab navigation, both conflict
  choices, phase/reveal feedback, named model text and doubled text size.
- Installed-renderer probes for independent radio groups, unique IDs, stable
  live-region messages, stable preview nodes, focus preservation and explicit
  submission boundaries.
- Existing presenter/projector/two-device lesson checks, privacy, repair,
  anonymous sharing, native German Unicode, reset and navigation.
- The actual evaluator worker's network, nested-worker and dynamic-code
  restrictions, invalid-result rejection, timeout cleanup and recovery.

The keyboard harness uses native radio behaviour: Shift+Tab may enter an
unselected group at its last option, and WebKit does not need to wrap at the
group boundary. The test moves toward its target with either arrow key;
the plugin does not replace the browser's keyboard handling.

Accessibility-tree snapshots and screenshots were saved for all six language/
browser combinations. The English validation focus and German WebKit model
preview were visually inspected. Live-region DOM observations show that the
correct messages change; they do not prove how assistive software speaks them.

## Pilot capacity recheck

The same final artifacts passed the 32-actor synthetic pilot: cold evaluation
p95/last 1.50/1.50 seconds; warm replacement p95/last 1.98/1.99 seconds. All
unfinished answers recovered after presenter disconnect within 2.58 seconds.
No unavailable outcomes or premature feedback appeared. Hardware was the
recorded Windows i9-11950H system, 16 logical CPUs and about 63.2 GiB RAM,
using Chromium 151.0.7922.34 and Node 24.15.0 on loopback.

These are protocol-client measurements, not 32 rendered physical phones or a
deployment guarantee. The conservative 32-actor pilot limit stays in place;
this patch does not reassess the historical 64-actor latency failure.

## Remaining gates

Physical Android/iPhone use, screen-reader speech output, native browser zoom
and OS text enlargement, and deployment/LAN measurements still need review.
The CI workflow now includes these automated accessibility cases but has not
run on GitHub. A reviewed, published compatible host commit is required before
that run; catalog/release publication remains a separate action. Historical
0.4.0 records are retained with their original artifact identities.

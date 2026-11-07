# B+ B4 visual classroom verification

Local Windows verification on 2026-11-07. Version 0.4.0 adds structured phone
editing, local replay preview and the presenter/projector workflow on the B3
classroom protocol. State schema 2 and the mathematical contract remain unchanged.

See the [classroom guide](../bplus-classroom.md) and
[machine-readable record](bplus-tree-b4-validation.json). This is local development
evidence. The physical-phone criterion and B5 release gates remain open.

## Exact artifacts

- Provider: `io.github.stefanjdecker.bpluslab`, version `0.4.0`.
- Portable wheel: `texstage_bplus_lab-0.4.0-py3-none-any.whl`.
- Wheel SHA-256: `f5d3b39c787eb4195c523dab54c15d619d90fc3778db8aa1c722f9d4bae1c26c`.
- Runtime payload: `250a44245e0a64750bcd002bda37de14352aa87205a2b7ea3b983a6115383bdb`.
- Host wheel SHA-256: `fcf39dae8e6304cdb4d713102d89145b7bcf3d32faf00b43b31fb1d22bb3feb9`.
- Host baseline: `de3351550f3553ca63023554521fbe84806ec94e` plus the frozen working-tree changes
  listed in the JSON record. All 150 installed host package files matched the snapshot.
- Collection baseline: `5f00b62f6292de01e4eca067c8acd96dddf67eb9` plus these uncommitted changes.
- Python 3.14.4, Node v24.15.0; wheel/sdist payload parity verified.

The host snapshot includes unpublished evaluator/broadcast, schema-cache,
language propagation, keyboard routing and layout changes from other work.
This task did not modify those host files. A dependency such as
`texstage>=0.2.1.dev3` does not identify this snapshot or establish a published
compatibility pin.

## Verified behavior

**123 tests passed**, with no failures, errors or skips: 30 engine, 32 authoring,
60 classroom state and one editor-helper test. Pytest reported one harmless
failure to write its optional scratch cache after completing the tests.

The editor helper checks 35 complete answer round trips and compares replay
facts against the independent Python model. It inspects 91 owned
snapshots, bounds geometry, checks strict integers, locale keys, cancellation
and input immutability. The largest measured synchronous replay chunk in that
finite Node run was 2.10 ms; this is not a worst-case
device or classroom-capacity claim.

| Browser | English and German actual UI | Worker security |
| --- | --- | --- |
| Chromium / Chrome 156.0.8078.80 | All six examples passed | All ten forbidden operations blocked |
| Firefox 153.0 | All six examples passed | All ten forbidden operations blocked |
| WebKit 26.5 | All six examples passed | All ten forbidden operations blocked |

Actual installed-host flows cover lookup, range, insert, delete, cascading
splits and root contraction. They use real touches/clicks, keyboard activation,
authenticated submissions and the presenter evaluator. Checks cover undo/redo,
preview without auto-save, focus/caret preservation during peer updates,
two-device conflicts, reset choices, private inspection, anonymous prediction-only
sharing, replay, feedback release and navigation/remounting. All runs reported
zero page errors.

Controlled promise completion additionally checks edit-while-saving,
view-before-receipt, late receipts after reset/destruction, queue refusal,
stale-answer choices, structural keyboard focus, cancelled previews, presenter
reset and hidden/disposed overlay behavior. These fixtures use the installed
modules; they complement, rather than replace, authenticated end-to-end flows.

The initial printed slide remains visible, private preparation stays out of
public transport, and all four views remount correctly. Separate protocol probes
retain duplicate/lost-ack receipts, stale controls, replacements and reset guards.
The prepared probe now allocates its own loopback port; all three families were
rerun after an initial parallel-test port collision.

The unchanged production evaluator policy is:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

Active probes test same/cross-origin fetch, XHR, WebSocket, EventSource, child/blob
workers, external modules, eval and Function. Invalid results remain rejected;
timeout cleanup and subsequent recovery pass with zero leftover workers.
Firefox required process escalation for the Windows browser sandbox, without
changing this CSP.

## Layout, authoring and CI

Phone emulation at 320 CSS pixels had no document-wide horizontal overflow,
minimum visible button height 44 pixels and no unlabeled form inputs. Both
languages use reduced motion. ARIA snapshots and English/German screenshots
were inspected. These are structural checks, not a physical-phone or assistive
technology usability study.

The phone retains readable page cards and a keyboard outline. The projector
shows the current replay step; large trees use an explicitly labelled enlarged
region around the focused page. The [phone screenshot](../images/bplus-phone.png)
and [projector screenshot](../images/bplus-projector.png) use synthetic data.

The six-example 16:9 and boundary-case 4:3 decks were rebuilt in both languages.
Live, handout, solutions, static PowerPoint and direct-pdfLaTeX checks passed
with the final provider payload. Source lessons, static layout and style bytes
remain unchanged; no course materials were migrated.

CI now includes the editor helper in Linux/Windows package tests and a
three-browser × two-language prepared UI matrix using identical handed-off
wheels and bundles. No hosted run or Windows/Linux artifact transfer was performed
in this task.

## Remaining gates

The implementation is ready for a physical-phone/LAN and real-projector pilot.
Measure the provisional 48-participant workload, replacements, fairness and
slow/failed evaluators before claiming classroom capacity. Complete a real
assistive-technology session, publish/pin the compatible host and run hosted CI
with identical artifacts across operating systems before release/catalog publication.

No commit or push was performed. Original repositories, existing courses, course
environments and private media were not changed.

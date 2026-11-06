# Relational Algebra Lab: R3/R4 lesson validation

Local Windows validation, 2026-11-06. The prepared lesson now runs end to end,
with a basic JSON answer editor. The visual tree editor and cooperative preview
remain R5 work. This is not a classroom release.

The [machine-readable record](relational-algebra-lesson-validation.json) contains
the exact wheel hashes, provider resource hashes, changed host code hashes,
browser results and serialized storage measurements. The earlier R2 and worker
compatibility records retain their historical artifact identities.

## Implemented behavior

One lesson envelope supplies the frozen engine exercise, a checked worked
answer and an English/German explanation. The authoring hook independently
computes expected facts in Python, rejects invalid worked answers, separates
public/private data and generates exercise/solution TeX. The thin
`texstage-relational-tree.sty` wrapper calls `\texstageprepared`.

The content type owns introduce/open/closed/revealed phases, presenter control
versions, actor-local answer versions, anonymous sharing and compact feedback.
Private fixtures and expected digests are withheld from audience views, including
after reveal. Evaluation completions must match the current answer, exercise,
mode, epoch and correlation and cover every configured fixture exactly once.
Rewrite feedback also checks the derived certificate and public metric.

The host now preserves structured refusal/operational codes, reconciles mount
identity and removal, and accounts atomically for cancelled jobs when replacing
an answer at queue capacity. These are generic mechanisms; no algebra-specific
server endpoint or relaxed worker policy was introduced.

## Checks performed

| Check | Result |
| --- | --- |
| Installed relational wheel | **72 tests passed**: 48 engine checks and 24 lesson checks |
| Host suite | **410 unique tests passed, 1 skipped** after scoped Windows registry rerun |
| Existing transaction engine, isolated installation | **67 tests passed** |
| Original coordinate/distance pair, exact-provider installation | **4 tests passed** |
| All four providers installed together | Discovery, resource integrity and collision checks passed |
| Wheel rebuilt from sdist | Same provider manifest/resource payload |
| Generated editions | Live/presenter, stage, handout, solutions and static PowerPoint built |
| Local direct pdfLaTeX | Handout and solutions built; changed source rejected as stale |
| Visual review | Both exercise pages and both solution pages rendered and inspected |
| Privacy | Public bundle/role projections exclude private checks; grades withheld until reveal |
| Runtime races | Two devices, competing presenter controls, replacements, stale results, replay and reset |
| Documentation/locks | Host documentation links and unchanged dependency lock consistency passed |

The full sandbox host run initially passed 404 tests, skipped one Windows
symlink test and hit six registry permission failures. A scoped rerun using
only the test registry key passed all nine selected tests, including those six.
The skipped symlink test remains unverified on this machine.

The runtime tests use the installed provider through the actual host worker and
validators. Engine result transport uses the real binding namespace. The old
exact-provider tests remain separate; they were not relaxed to admit the new
provider.

## Browser interactions and security

| Browser on Windows | Lesson | Existing coordinate example | Both database engines |
| --- | --- | --- | --- |
| Chrome 156.0.8078.80 | Passed | Passed | Passed |
| Firefox 153.0 | Passed | Passed | Passed |
| WebKit 26.5 | Passed | Passed | Passed |

The lesson harness runs the real presenter, projector and two devices sharing
one student identity. It checks both construction and rewrite submissions,
320-pixel width, keyboard save, touch save, draft/focus preservation, explicit
cross-device conflict resolution, private inspection, anonymous sharing,
reveal/reset and navigation teardown. Tested live labels are English; bilingual
authoring is checked in Python. These are desktop browser contexts, not physical
phone measurements.

Both database engine harnesses pass eight samples per browser and ten active
security probes. Fetch, XHR, WebSocket, EventSource, child/blob workers, external
modules, eval and Function construction are blocked in the real evaluator.
Separate unrestricted controls establish that each probe can execute. Invalid
results are rejected; infinite loops time out; subsequent evaluation recovers
with no workers left running.

The unchanged worker CSP is:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

## Storage evidence

A 64-actor storage probe used 256-character actor keys and 1,787-byte answer
shapes, with compact operational feedback:

| Serialized quantity | Measured bytes | Limit |
| --- | ---: | ---: |
| Largest actor slot, including its key | 2,314 | 2,560 |
| Shared state | 98 | 32,768 |
| Complete state | 148,142 | 196,608 |
| Transition including effects | 150,349 | 262,144 |
| Presenter view | 20,215 | 131,072 |
| Participant view | 1,899 | 131,072 |

The 65th new actor receives a capacity refusal; existing actors can replace an
answer. The provider reserves feedback space before accepting a slot and bounds
every transition and view. This checks storage, not burst throughput, queue
fairness or latency.

## Exact artifacts and reproduction

- Host wheel SHA-256:
  `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6`
- Relational wheel SHA-256:
  `5dff8fe63e3dff6727bedea60501f7b9fe217cb3c270567ba598181f6ab34edd`
- Provider payload:
  `4cd9606845da591de851f8bbaaf90889e3b569cdb6caa0a0a7067d2df0ce746d`

The host and collection are working-tree changes on `codex/plugin-system`,
based on host `06d808c5` and collection `35e6515f`. The development version
strings alone do not identify these artifacts. Source and payload hashes in the
JSON record identify the tested implementation.

Follow the [lesson guide](../relational-lesson.md) to install, enable, author,
build and test. The conformance workflow now installs TeX for the relational
authoring tests, passes the built lesson bundle to browser jobs, and runs both
engine/security and lesson harnesses. Hosted CI was configured, not run here.

## Remaining release gates

R5 still needs the visual editor, operator forms, tree outline, undo,
intermediate-result inspection and a cooperative/cancellable public-data
preview. R1/R6 still need fair scheduling/load measurements, a real phone over
LAN, broader accessibility and language review, Linux and cross-OS evidence,
an actual projector recording, and a published immutable compatible host pin.

No catalog release, push, course migration or media change is part of this
milestone. The original repositories and existing course environments are
preserved.


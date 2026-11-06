# Relational Algebra Lab: implementation plan

Status: engine and R3/R4 lesson implemented, 2026-11-06. The
[v1 contract](relational-algebra-contract.md) and
[validation record](relational-algebra-r2-validation.md) cover the R0 schemas and
R2 algebra/certificate engine. R1 worker startup is now fixed and tested under
the unchanged CSP; see [the compatibility record](worker-browser-compatibility.md).
Structured command errors, mount reconciliation and queue replacement now have
generic host regression coverage. R3/R4 supply the prepared exercise/solutions,
bounded state and role-filtered views, with a basic JSON entry interface for
end-to-end checks. See [the lesson validation record](relational-algebra-lesson-validation.md).
R5's visual editor/preview, remaining R1 scheduling gates and R6 measurements remain.
The [design](relational-algebra.md) specifies the teaching modes and target behavior.

## Delivery scope and dependencies

Maintain the provider in `texstage-plugins` and generic mechanisms in the
active Texstage code checkout. The host's GitHub/GitLab repositories mirror one
code history. Do not touch archived checkouts, original lecture-tools, existing
courses, pins, installed course environments or private media.

The transaction lesson remains unfinished. Share its generic host prerequisites;
do not duplicate a host fork, state framework or queue inside this plugin.
This proposal does not require the transaction activity package to exist.
The first relational implementation slice is pure algebra plus a construction
example; a classroom release additionally requires authoring, state, UI and
the gates below.

## Intended files

```text
texstage-plugins/
  docs/design/relational-algebra.md
  docs/design/relational-algebra-plan.md
  docs/design/relational-algebra/
    README.md
    construct.exercise.json
    rewrite.exercise.json
    expected-cases.json
    validation.json
  plugins/relational-lab/
    pyproject.toml
    MANIFEST.in
    LICENSE
    README.md
    texstage-plugin.json
    texstage_relational_lab/
      __init__.py
      model.py
      authoring.py
      state.py
      schemas/
        exercise-v1.json
        answer-v1.json
        analysis-result-v1.json
        commands/
        views/
      latex/texstage-relational-tree.sty
      templates/
      locales/en.json
      locales/de.json
      web/
        algebra.mjs
        rewrites.mjs
        identity.mjs
        engine.mjs
        preview.mjs
        tree-editor.mjs
        table-view.mjs
        participant.mjs
        presenter-controls.mjs
        presenter-overlay.mjs
        projector-overlay.mjs
    tests/
  examples/relational/
    lesson.tex
    lesson.activities.json
    activities/
  maintenance/
    check_relational_design.py
    relational_probe.py
    relational_browser.cjs
```

The package now contains the engine, Python model, schemas, fixtures and tests.
Authoring, state, styles and interface modules in this target tree remain planned.
The engine uses owned pure modules intended for reuse by the future local preview;
the Python model supplies an independently implemented static oracle.

## R0 — freeze the finite specification

Agree on named set semantics, the flat tree/predicate encoding, task modes,
source schema, typed result variants, rewrite rule side conditions and byte/
work/state budgets. The attached draft source examples and expected cases make
these decisions reviewable before writing UI code.

Write machine-checked JSON schemas and semantic validators. Separate ordinary
source validation from the host's restricted result/view schema profile.
Explicitly model canonical postorder, table headers/types, exact fixture
coverage, allowed operators, and the fixed task mode; a client may not choose
rewrite mode to bypass construction checks.

Exit:

- Hand-derived construction outputs and intermediate-cell counts agree with
  independent checks; the library example includes duplicate projected names.
- At least one wrong tree matches the visible dataset but fails a legal private
  counterexample. Explain why finite checks still cannot prove equivalence.
- The five-step worked rewrite is valid and preserves the result.
- Worst-case encodings are shown to fit, or limits are reduced before UI work.
- Initial schema drafts are examples of the actual host portable profile.

Run `python maintenance/check_relational_design.py` to reproduce the attached
finite example checks with the Python standard library. The checker is a small
specification aid, not a production parser, complete validator or plugin engine.

The original design checker covers finite examples. The separate R0/R2 record
adds installed-wheel and host-contract evidence; classroom gates remain open.

## R1 — close shared host prerequisites

| Generic work | Active host locations | Evidence required |
| --- | --- | --- |
| Module-worker startup and policy | `web/stage/plugin-evaluator-worker.js` and generated host/provider modules | Passed locally in Chrome, Firefox and WebKit with unchanged CSP; active connection/child-worker restrictions, result validation, timeouts and cleanup verified in the compatibility record |
| Structured command outcomes | `src/texstage/web/shared/plugins.js`, dispatch/server boundary | Closed/stale/capacity/unavailable outcomes remain distinguishable without parsing exception prose |
| Mount reconciliation | `src/texstage/web/shared/plugins.js` | Removed modules/descriptors destroy old mounts; replacements do not keep obsolete item context; asynchronous mounts cannot reappear |
| Fair bounded evaluation/status | `src/texstage/plugins/runtime.py`, `worker.py`, `server/plugins.py` and presenter dispatch | Measured pilot workload, bounded replacement jobs and useful pending/unavailable status |
| Reproducible compatibility | Host release metadata and collection CI | Published exact host commit and recorded matching wheel; existing providers/no-plugin behavior retained |

The table's `web/...` path in the first row is relative to `src/texstage/`.
Reproduce dated browser failures before changing policy. Do not count a relaxed
diagnostic policy as passing production conformance. Implement only generic
mechanisms; no algebra-specific server endpoint is required.

Pure-engine development can proceed alongside these fixes. Classroom/browser
release cannot pass while required host behavior remains unsupported.

## R2 — implement algebra and certificates

Implement the independent Python model and the pure browser algebra module:
headers, strict types, set normalization, all eight operator forms, deterministic
identity, explicit work accounting and bounded intermediate relations.
Implement the four named rewrite rule families and their side conditions.
The browser wrapper supplies start/load/evaluate/dispose with fresh submission
state and the actual host result contract.

Use hand-derived cases, small-domain exhaustive properties and an independently
structured oracle. Do not use one implementation's generated expectations as
the sole evidence for the other.

Exit:

- Selection, duplicate-eliminating projection, rename/collision handling,
  product, theta join, union/difference compatibility and empty relations pass.
- Incomplete/malformed/oversized answers, bad indices/order, DAGs, cycles,
  unknown attributes, incorrect operand types and resource limits are distinct.
- Different valid construction trees pass finite checks without canonical
  equality; wrong trees fail the intended counterexamples.
- Each rule has positive tests and a failing side-condition case. Verify all
  tiny instances in selected bounded domains, in addition to reviewing the law.
- Identity is independent of UI labels, actor and clock, but includes semantics,
  task and answer. It works on ordinary LAN HTTP without WebCrypto.
- Python/JavaScript agree on NFC, non-BMP text ordering/escaping and strict
  integer/boolean distinctions. Charge tuple/pair/atom work across the whole
  job, including rewrite steps; exercise bounded stop/cancellation behavior.
- Actual typed results, including derived rewrite trees, fit 8/12-KiB budgets
  through both installed host validators. Tests bind the real seed/options.
- Wheel/sdist resource parity and an engine-only installed-wheel probe pass.

Declare only completed capabilities in interim artifacts. An engine-only wheel
with this distribution name must not be advertised as the finished lab.

## R3 — implement prepared authoring and static material

Use revision 2 and an `authoring_hook`. Validate one exercise source, prepare
public and private material, derive expected relation/header digests with the
Python model, and create exercise/solution fragments. Supply the declared style
as a thin wrapper around `\texstageprepared`.

Construction publishes the prompt/schema/public instance and empty or partial
starter; the reference and private fixtures remain in private prepared data.
Rewrite publishes its baseline and allowed rules, while worked certificates
remain withheld until permitted. Build the explicit activity sidecar and a
synthetic deck with one item of each mode.

Exit: installed provider builds live, handout, solutions, static PowerPoint and
local direct-pdfLaTeX editions; all use the same source. Changed inputs and
missing assets fail freshness checks. Private fixtures/solutions do not leak
through public bundles, ordinary slides or artifact-directory packaging.

## R4 — implement lesson state and privacy

Implement introduce/open/closed/revealed phases, guarded presenter controls,
actor-local answer versions, idempotent receipts and correlated evaluation
effects. Validate returned exercise/answer identities and complete fixture
coverage. Compute construction correctness from domain facts, and rewrite
success from the checked certificate plus the configured public metric goal.

Keep one current answer slot per actor. Enforce 2.5 KiB per actor including its
key, 32 KiB shared state, the 192-KiB item target and a 64-actor pilot ceiling.
On capacity exhaustion give a useful operational refusal, never “incorrect”.
Replacing a saved answer must remain possible for an existing actor.

Exit: tests cover same-actor devices, unrelated students, two presenters,
replacement/close/reset/result races, lost acknowledgements, reopen/navigation
and evaluator replacement. Check audience-specific transport and the maximum
valid serialized state, not just Python object size. No private fixture results
appear before release, and reveal does not indiscriminately publish private data.
Include effects in the host's 256-KiB transition ceiling and keep each audience
view within 128 KiB. Store only compact feedback; select/paginate presenter
inspection instead of projecting all answers in one view.

## R5 — implement the editor and local preview

Build the participant interface first: relation picker, typed operator forms,
tree outline, branch replacement, undo, node inspection and rule application.
Local previews use owned pure code and only public data; cooperative work yields
to the UI and obsolete results are cancelled/ignored. Label preview separately
from saved authoritative feedback.

Then implement controls, presenter overlay and projector comparisons. Preserve
dirty drafts and focus during ordinary updates; expose cross-device conflicts
explicitly. Make comparison sharing deliberate and anonymous.

Exit: end-to-end interaction on installed wheels in Chromium, Firefox and
WebKit; 320-pixel layout, keyboard and touch, zoom/resize, German/English,
reduced motion, teardown and useful static fallback. Verify on a real phone over
ordinary LAN HTTP. Every supported example previews within its budget.

## R6 — measure, integrate and prepare a release

Test a 64-participant burst, two presenters, projector, answer replacements and
reconnects. Record p95/worst input latency, preview/evaluation latency, queue age,
memory, worker IPC and state/view bytes on named devices. Provisional pilot
targets: previews p95 under 200 ms, UI chunks under 16 ms, authoritative burst
feedback p95 under 10 s and worst under 30 s. Confirm or revise these targets
explicitly after measurement; do not claim them from node-level microbenchmarks.
The existing per-evaluation host deadline remains a hard constraint.

Run isolated installations for host alone, the original coordinate/distance
pair, relational lab alone, transaction engine plus relational lab, and all
completed providers. Preserve existing exact-provider tests. Check collisions,
pins, disabled-factory discovery and updates that change resource hashes.

Transfer identical portable wheels Windows-to-Linux and Linux-to-Windows.
Use independent CI jobs for domain/packaging, browsers and artifact consumers;
retain failing gates. Publish a conformance record tied to exact host/provider/
schema/wheel identities and actual hosted results.

Review public/private archives and an actual recording containing the selected
projector overlay. Only then prepare a reviewed immutable release and catalog
entry under the user's release authorization. No course migration is implicit.

## Next implementation task

Implement R5's visual query-tree editor and cooperative public-data preview.
Replace the basic JSON entry experience while preserving its explicit save,
draft/conflict handling, anonymous sharing and phase/version semantics.
Keep authoring, state and result contracts shared by both modes. Preserve the
worker policy and security probes, and complete the remaining R1/R6 gates
before a classroom release. Keep the transaction design and existing course
environments intact.

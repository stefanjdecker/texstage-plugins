# Query-plan prepared authoring: Q2 validation

Local Windows evidence, 2026-11-06. This record supplements the historical
[Q0/Q1 engine evidence](query-plan-engine-validation.md), which describes 0.1.0.
The [machine-readable record](query-plan-authoring-validation.json) identifies
the exact 0.2.0 artifacts, hashes, budgets and browser results.

## Implemented scope

One lesson JSON supplies public exercise/baseline/goal facts, private worked and
reference facts, and exercise/solution LaTeX fragments. The style command delegates
to the existing host preparation pipeline. The host requires state hooks and two
overlay surfaces: Q2 uses a minimal read-only bridge that preserves the static
slide. It has no classroom commands, learner storage, input UI or evaluation jobs.

The [seven-slide example](../../examples/query-plan/lesson.tex) contains four
activities. The [authoring guide](../query-plan-authoring.md) explains installation,
source fields, exports, freshness and privacy. English/German generated material
is supported; frame titles are authored independently.

No host API or security restriction changed. No original tools, existing courses,
course pins/environments or private media were edited. Unrelated plugin work was
preserved. No package/catalog release has been published.

## Exact artifacts

| Item | Identity |
| --- | --- |
| Provider | io.github.stefanjdecker.queryplan 0.2.0 |
| Provider payload | fd98799e74f43550e1e26db942de73d853d6b2696998622ea492ee7c7a4473e6 |
| Wheel | texstage_query_plan-0.2.0-py3-none-any.whl |
| Wheel SHA-256 | ebb9eb09b18ab102d183e8899aa7b5a50adc8663eeeb6811e69d03546229d632 |
| Host development commit | de3351550f3553ca63023554521fbe84806ec94e |
| Host wheel SHA-256 | d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6 |

The exact host wheel hash is also stored in the JSON record. Version 0.2.1.dev3
alone does not establish compatibility. Source-distribution rebuild matched the
wheel's provider payload/inventory. All packaged source/resources use LF and
match the final source bytes. The pure model, engine modules/worker, original
four schemas and fixtures are byte-identical to 0.1.0. The new factory,
authoring hook, style, read-only module and view schema change the provider pin.

## Verification

**108 installed-wheel tests passed**, no failures or skips (79.04 seconds).
The isolated environment used Python 3.14.4, Node v24.15.0,
the exact host wheel and locked host dependencies. Tests import the installed
provider, never the plugin source tree.

The 86 engine checks were retained, with metadata expectations updated for the
new capability. Twenty-two authoring cases cover:

- Single reference enumeration per preparation; exact Python analysis facts,
  source immutability and public/private separation.
- English/German output, literal TeX escaping and explicit Unicode fallback.
- Invalid baseline/worked plans, impossible goals and a budget-satisfying
  nonoptimal worked answer alongside the actual optimal reference.
- The maximum 864-candidate lesson through the real host worker: response
  105466 bytes, exercise fragment 12974
  bytes, solution fragment 40818 bytes; about
  0.391 seconds including process startup.
  Existing preparation timeout and JSON/fragment caps are unchanged.
- Real read-only runtime hooks, both portable views, rejection of undeclared
  commands and absence of evaluation jobs.
- Missing providers, traversal/absolute-source rejection before factory execution,
  source-change detection, changed facts/digests and unchanged sibling identities.
- Full live build, exercise-only seven-slide static PowerPoint without notes,
  handout/solutions PDFs and identical-text direct pdfLaTeX editions. Stale direct
  exports fail explicitly.
- German handout and solution PDF compilation.

Four preparation calls generated all four activities across the normal build's
modes. Timings were [438.926, 3.409, 10.282, 8.913] ms including first worker startup.
Handout/solution pages were rendered and visually inspected. The initial dense
layout clipped; the final style fits the content inside the registered rectangle.
Long prose still needs editorial review for readability; schema byte limits are
not layout recommendations.

## Browsers and security

Chrome 156.0.8078.80, Firefox 153.0 and WebKit 26.5 each passed eight cost-worker
samples and the active security harness. Same/cross-origin fetch, XHR,
WebSocket, EventSource, child/blob workers, external module imports, eval and
Function construction stayed blocked. Positive controls confirmed the probes
were effective; timeout/invalid-result recovery passed.

All three browsers also ran the actual installed host with the prepared bundle,
presenter, projector and 320-pixel participant viewport. They navigated all four
activities, confirmed empty transparent overlays preserve the static background,
checked role-filtered state for private/reference leakage, verified no input or
presenter controls appear, and observed teardown after navigation with no page
errors. Firefox needed a native browser launch outside the process sandbox;
the application worker CSP remained unchanged.

Phone answer interaction is not implemented or claimed by these checks.
Classroom state, open/close/reveal and bounded answer feedback are Q3; the editor
and controls are Q4. Hosted/Linux CI, release pins, accessibility, physical devices
and classroom load remain Q5 gates.

# B+ tree prepared authoring: B2 validation

Local validation: 2026-11-07. Version 0.2.0 adds prepared LaTeX material to the
unchanged B+ engine contract. The live content type is read-only; the interactive
lesson is not implemented. See the [author guide](../bplus-lesson.md),
[machine-readable evidence](bplus-tree-b2-validation.json) and
[next milestone](bplus-tree-plan.md#next-implementation-task).

## Tested artifacts

| Artifact | Identity |
| --- | --- |
| Host source baseline | `de3351550f3553ca63023554521fbe84806ec94e` |
| Host wheel SHA-256 | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| B+ wheel | `texstage_bplus_lab-0.2.0-py3-none-any.whl` |
| B+ wheel SHA-256 | `a759d29960d8aaf7558624426646422270fcd9c6123439b9eb60833f99ed5637` |
| Provider payload | `d4a28458d7ba11e82aa1d9656564813111d1e66bfc9b7a480cd4a61e4838b40a` |
| Engine result-schema digest | `7e5ae204c3226b03ed4ca1250b5f1aa5d63b808256ec14f13b16e826a5fdd6c2` |

Checks use portable installed wheels in a new environment with the host's
hash-locked dependencies: Python 3.14.4 and Node 24.15.0 on Windows. Wheel/sdist
payload parity and `pip check` pass. Metadata discovery does not import the
provider factory; the tests verify imports resolve to the installed package.

Eleven engine/model/source/answer/result/fixture files retain their B1 bytes.
The new preparation hook, geometry, style, read-only state and closed view
schema belong to the same independently installable distribution.

The 119 installed host runtime/style files match the exact baseline wheel.
A concurrent working-tree edit to `src/texstage/server/plugins.py` adds language
to audience projections; it is excluded from this tested host artifact and was
not changed or adopted by B2. This is evidence for the named local baseline,
not a claim about untested concurrent changes or a published host release.

## Semantics, authoring and boundary tests

**30 engine tests and 32 authoring tests pass**, with no failures or skips.

The engine suite retains its 30 hand-specified cases, 1,800 exhaustive operation
cases and 1,440 seeded operations across all capacity combinations. Its
alternative valid repairs, malformed input, lifecycle and result-binding
checks remain intact.

The authoring suite checks:

- Every original worked case through preparation, including both legal
  split partitions and alternative donors/merges. English preparation facts
  also pass the independent JavaScript engine and actual host validators.
- All nine synthetic example sources in English and German; language variants,
  English fallback, deterministic output and fragment/envelope byte bounds.
- Wrong paths/scans/returned keys, incomplete or extra repairs, incorrect
  separators/height, malformed trees, bool/float coercion, unknown fields and
  unsupported feedback values. Invalid worked material stops preparation.
- Escaped plain text, an unchanged input object and explicit public/private
  separation. The feedback policy and worked material never enter public data.
- Closed read-only state/view contracts, no commands/effects, no participant
  surface, exact style ownership and portable view-schema validation.
- Geometry coverage and non-overlap across the design trees and maximum-size
  example, independently of the order of node records.
- Disabled providers, confined source paths, modified prepared fragments,
  changed installed style bytes and direct-pdfLaTeX freshness.
- A deliberately undersized box fails instead of silently scaling too far.

## Real editions and visual review

| Scenario | Language | Format | Activities | Pages per edition |
| --- | --- | --- | ---: | ---: |
| Teaching progression | English | 16:9 | 6 | 7 |
| Teaching progression | German | 16:9 | 6 | 7 |
| Empty/last-entry/large tree | English | 160 × 120 mm, 4:3 | 3 | 3 |
| Empty/last-entry/large tree | German | 160 × 120 mm, 4:3 | 3 | 3 |

Each scenario passes the live bundle build, handout, solution PDF and static
PowerPoint export. Direct pdfLaTeX separately compiles handout, solutions and
present entry points. Every edition validates the same item/preparation digests;
the hook is called only once per item. Changed source bytes invalidate both
Python preparation reuse and the direct TeX entry point.

Public bundle data and public file lookup exclude worked answers, analysis,
explanations, evaluation bindings, raw sources and solution fragments.
The private bundle data retains the checked solution. Exercise PDFs and live
slides omit solution headings; solutions contain one checked result per item.

All PDF text stays inside its page, and direct builds have no Overfull warnings.
Rendered handout/solution pages and the actual embedded PowerPoint images were
visually reviewed in both languages. The large signed-key example begins with
40 entries and ends with 41 entries, 29 pages and height three. It uses the
documented taller page; arbitrary dense content on a small 16:9 box is not
claimed readable. The style rejects more than 18% excess natural content height.

## Installed host in three browsers

| Browser | Version | Engine/worker | Prepared live deck |
| --- | --- | --- | --- |
| Chromium through Chrome | 156.0.8078.80 | Passed, 34 samples | Passed |
| Firefox | 153.0 | Passed, 34 samples | Passed |
| WebKit | 26.5 | Passed, 34 samples | Passed |

The engine checks use the actual installed evaluator and unchanged worker CSP:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

All ten forbidden connection/child-worker/dynamic-code probes are blocked,
after proving unrestricted positive controls work. Invalid typed results are
rejected; the non-cooperative synthetic engine hits the host's two-second
deadline, no workers remain, and the next real evaluation succeeds.

The real prepared deck shows the exercise beneath transparent presenter and
projector overlays. Navigation removes and remounts the overlay without errors.
Authenticated presenter, projector and participant protocol clients receive no
private worked material. No participant editor or presenter controls are declared.
Screenshots were inspected; these checks do not simulate a physical phone.

Firefox failed at first-page creation inside the process sandbox, before loading
plugin modules. The unchanged checks passed outside that process sandbox.
An early prepared-browser harness nickname exceeded the host's 20-character
limit; correcting that synthetic test data resolved its login failure.
Neither issue required a host change or weaker browser restrictions.

## CI and remaining gates

CI now separates engine checks, prepared-authoring checks with real TeX/font/
German-language dependencies, and a three-browser prepared-deck matrix.
The prepared browser jobs consume the same wheel and tested bundle artifacts.
The existing original-pair scenario is unchanged.

Current source manifests for nine providers have unique IDs, capabilities,
style names and command exports. This is a metadata collision check, not a
new combined nine-wheel runtime scenario. B2 does not claim a fresh original-pair
or full host regression run; no host code was changed for this milestone.

The exact reproduction commands are in the
[author guide](../bplus-lesson.md#maintainer-checks-and-remaining-work).
Hosted CI and identical-wheel Windows/Linux transfer remain unrun locally.
B3/B4 must add authoritative submissions, grading, phase/reset races, sharing
and visual controls. Physical-phone tests, classroom capacity and release
publication remain later gates. No catalog entry, commit or push is implied.

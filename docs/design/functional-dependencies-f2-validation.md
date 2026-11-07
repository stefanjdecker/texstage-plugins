# FD Lab F2: closure lesson validation

Implemented and checked locally on 2026-11-06. The closure classroom activity is
usable with the matching experimental host. Keys and implication classroom modes
remain F3. See the [lesson guide](../fd-lesson.md), [plan](functional-dependencies-plan.md)
and [machine-readable record](functional-dependencies-f2-validation.json).

## Exact artifacts

| Artifact | SHA-256 |
| --- | --- |
| `texstage-0.2.1.dev3-py3-none-any.whl` | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| `texstage_fd_lab-0.2.0-py3-none-any.whl` | `cfa23960db9ced4af45c1dba65eb5cd8a88c8f66b4f9d1a5f51e40b24eeb23fb` |
| `texstage_fd_lab-0.2.0.tar.gz` | `1df742e9633061d11da7d58b407134859e0fc55e806be8e85004eec9a736e6f7` |

Provider payload: `421f64bbdda9fe101c9e1f9bfb95b30c309d416252c8079263b085fdd40af0b6`.
The installed host and provider runtime files matched the recorded wheels byte for byte.
The wheel and sdist have identical provider manifests and resource hashes. Host source
is local commit `de33515`; the development version alone is not a release pin.

## Verified behavior

- 61 installed-wheel tests passed without skips: 39 engine regressions and 22 lesson tests.
  The engine checks retain all 4,096 tiny FD theories, 32,768 closure comparisons,
  composite/empty/cyclic examples, strict parsing and both host validators.
- Prepared authoring independently checks the worked answer, escapes plain text,
  generates English/German fragments and rejects non-closure classroom sources.
- Live bundle, static PowerPoint, handout, solutions and direct-pdfLaTeX exports
  built successfully. Source changes invalidate exported prepared inputs.
  Both exercise/solution pages were visually inspected for readable sets, arrows,
  wrapping and writing space. Supplied English examples show no clipping.
- State tests check exact exercise/answer/trace facts before grading, alternative
  valid proofs, unavailable evaluations, both feedback policies and withheld fields.
- Real runtime checks cover receipts, stale presenter/actor versions, atomic
  replacement at queue capacity, reset epochs and late job completion. Reducer
  tests also cover pending results after close and 64 completed actor slots with
  reserved feedback, state/effect/view bounds, and replacement at actor capacity.
- Actual server/browser checks use presenter, projector and two devices for one
  participant: keyboard and touch FD/set controls at 320 px, preserved drafts and
  focus, explicit conflicts, assessment/practice feedback, private inspection,
  revealed-only anonymous sharing, walkthrough steps, reset and navigation teardown.

| Browser | Version | Engine policy / classroom lesson |
| --- | --- | --- |
| chromium | 156.0.8078.80 | Passed / passed |
| firefox | 153.0 | Passed / passed |
| webkit | 26.5 | Passed / passed |

All browsers consumed the same final provider wheel and prepared bundle. The
host worker policy remained unchanged:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

The engine probe retains ten active restrictions with unrestricted controls,
invalid-result rejection, deadline termination, zero remaining workers and recovery.
The lesson probe checks actual public socket projections; private worked data,
evaluation bindings, rosters and identifiers are not sent to unauthorized roles.

## Reproduction and remaining gates

Use the commands in the lesson/package guides with Python 3.14.4, Node 24.15.0,
Playwright 1.62.1, esbuild 0.28.2 and the matching host development lock. Local
test environments, synthetic bundles and screenshots were isolated from courses.

CI was extended to install TeX/fonts/German support, require the export test output,
and pass identical wheels and the prepared bundle to the three-browser matrix.
The Windows consumer uses the same Linux-built wheel; TeX exports are required in
the Linux producer. The hosted workflow and cross-OS handoff have not been run here.

Physical phones, measured classroom bursts/fairness/latency/memory, a full accessibility
audit, a German browser scenario, combined-provider conformance and immutable public
release artifacts remain separate gates. Storage fit is not classroom throughput.
No host code, original tools, courses, course environments or private media changed.

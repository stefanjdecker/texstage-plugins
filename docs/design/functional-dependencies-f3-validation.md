# FD Lab F3: candidate keys and implication validation

Implemented and checked locally on 2026-11-06. The package now provides all three
classroom modes: closure, one/all candidate keys, and implication through a proof
or a two-row counterexample. See the [English guide](../fd-lesson.md),
[German guide](../fd-lesson-de.md), [plan](functional-dependencies-plan.md) and
[machine-readable evidence](functional-dependencies-f3-validation.json).

## Exact artifacts

| Artifact | SHA-256 |
| --- | --- |
| `texstage-0.2.1.dev3-py3-none-any.whl` | `d7875af6ea1d27716cc11cb03a68b635fb28e8956983bff8482e7d7ea26e1ce6` |
| `texstage_fd_lab-0.3.0-py3-none-any.whl` | `85978a68ccc8be9f4831fd3f287efbe922cedee9192d4cdfe3bbaf3d34909c94` |
| `texstage_fd_lab-0.3.0.tar.gz` | `ba51385a3dc0fedecc94598d1a3f4c8f9d04633cde2974c003adff1bf51156af` |

Provider payload: `d7cdd50ed7f1c79a8ac6501cc62d544a4bc0ada935c86c4f904a87952aba1f4c`.
Installed host and provider runtime bytes matched these wheels. The wheel and
sdist rebuilt to identical provider manifests and resource hashes. Host commit
`de33515` is the tested experimental baseline; its version string is not a release pin.

## Checks run

- A 97-test installed-wheel regression passed with no skips: 39 engine, 22 closure
  lesson, and 36 new key/implication checks. After a CSS-only preview adjustment,
  96 tests were repeated on the final wheel. The exhaustive tiny-theory result
  was retained against byte-identical Python/engine resources; archive comparison
  verified that only two overlay CSS rules changed. CI still runs the full suite.
- Preparation verifies every worked answer and generates all editions from one
  source. Key tasks keep the full closure/key tables private; state checks use
  those tables instead of searching again for every submission. Result identities
  and every mode-specific fact/certificate are checked before grading.
- One/all key policies, differently sized minimal keys, the empty key versus no
  proposed keys, missing keys and nonminimal superkeys receive distinct treatment.
  Implication accepts target-prefix proofs and alternative valid witnesses, and
  distinguishes violated premises from failure to contradict the target.
- Real runtime tests validate every role projection, withheld feedback, deliberate
  sharing, and positive proof walkthrough. Closure receipt/race/reset regressions
  remain. New storage tests fit 64 completed 256-key submissions with feedback
  inside actor/state/effect/view budgets. This is not a throughput measurement.
- The synthetic ten-frame deck contains eight activities. Live bundle, static
  PowerPoint, handout, solutions and direct-pdfLaTeX exports pass. English/German
  preparation is checked; changed sources invalidate direct exports. New printed
  exercise and solution pages were visually inspected.

| Browser | Version | Engine policy / full classroom sequence |
| --- | --- | --- |
| chromium | 156.0.8078.80 | Passed / passed |
| firefox | 153.0 | Passed / passed |
| webkit | 26.5 | Passed / passed |

Each browser consumed the same final wheel and prepared bundle. The full sequence
covers closure, one/all keys, proof and counterexample, differing key sizes and
the empty key, using real keyboard/touch actions at 320 px. Checks include
focus/draft preservation, two devices for one actor, mode-specific feedback,
withheld private transport, anonymous sharing, walkthrough, reset and teardown.
Counterexamples render as aligned tables on phone, presenter and projector.

The shared examples also pass scroll-height checks in both presenter preview and
projector. The harness reserves an available loopback port and waits for its own
server readiness file; a separate occupied-port check verifies startup refusal.

The engine retained the unchanged host worker policy and active restrictions:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

The security harness checks ten restrictions with unrestricted controls, invalid
results, deadline termination, worker cleanup and successful recovery.

## Remaining gates

The existing FD CI pipeline automatically picks up the expanded tests and deck
and transfers identical wheels/bundle to its browser matrix. Hosted CI and the
Linux-to-Windows artifact handoff were not run locally. The evidence above is
Windows, Python 3.14.4, Node 24.15.0, Playwright 1.62.1 and esbuild 0.28.2.

Next is F4: real classroom bursts, queue/latency/memory measurements, reconnect
scenarios and physical phones on LAN HTTP. Full accessibility, a German browser
scenario, combined-provider conformance and immutable public release pins remain
separate gates. No host code, original tools, courses, course environments or
private media changed. Nothing was committed, pushed or published by this step.

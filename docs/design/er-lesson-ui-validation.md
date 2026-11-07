# ER registration E4 validation

Validated 2026-11-06: provider **0.4.0**, state schema **2**. The registration
pilot now has phone decision cards, public-only model preview, saving/repair,
presenter controls and projected discussion material. Read the
[classroom guide](../er-decisions-lesson.md) and the
[machine-readable evidence](er-lesson-ui-validation.json).

## Exact tested artifacts

- Collection base `5f00b62f6292de01e4eca067c8acd96dddf67eb9`, branch
  `codex/plugin-system`; ER changes remain uncommitted.
- Host base `de3351550f3553ca63023554521fbe84806ec94e` plus the uncommitted generic
  phone-language fix in `src/texstage/server/plugins.py`, its regression test
  and documentation. The installed host differs from the E3 host in that one
  runtime resource only.
- Host wheel SHA-256: `e5f07e8042db968486fe6411ddc84e91535fb3b63133ddb7dce7a9a591dfbf81`.
- Host installed-payload SHA-256: `191c38576fc772cfe4039b30782bdf66a708380846f7f14a7d41a0ba54807f04`.
- Provider wheel: `texstage_er_decisions-0.4.0-py3-none-any.whl`.
- Provider wheel SHA-256: `8d1d18b690879e326d957c7f4b14b18d15f894ae4505a9184368144c3e633490`.
- Provider payload: `fefb99982fc201506a41ed7a5ee6013b6dba73e46016936aaabe4a1056614ab1`.

The provider wheel and sdist have identical provider inventories/payloads on
rebuild. Tests import the installed portable wheel in a separate ER-only
environment with the host's hash-locked dependencies, refreshed with these
exact artifacts. This is local Windows evidence, Python 3.14.4,
Node v24.15.0 and TeX Live 2026; it is not a published compatibility pin.

## Passing checks

**110 ER tests** passed with no failures or skips. They retain the E1/E2/E3
engine, independent oracle, static editions, role schemas, state/race, budget,
receipt/restart, confinement and freshness checks. The new preview test compares
all 27 public decision combinations with the independent Python compiler and
checks that unanswered fields remain unknown and public data is not mutated.

**92 host regression tests** passed: plugin contracts, runtime behavior, server
HTTP/WebSocket paths, renderer lifecycle and the new role-filtered language
projection regression. One pre-existing Starlette TestClient/httpx deprecation
warning remains. The generic fix includes deck language in plugin state, so
German activities reach participant renderers in German; no ER-specific logic
was added to the host.

The installed-host English classroom workflow passes in Chromium
151.0.7922.34, Firefox 153.0 and WebKit 26.5. Each run includes a presenter,
projector, two contexts sharing one learner identity and another learner.
At 320 CSS pixels the tests cover:

- Empty initial choices; complete explicit submission; real worker evaluation.
- Public-only preview/back navigation, wrong ownership followed by repair, and
  two accepted model forms without reference-equality grading.
- Keyboard radio navigation, visible focus, tab/Enter submission, touch actions,
  resize and 200% text enlargement without horizontal overflow.
- Draft/focus preservation on unrelated updates, explicit keep/reload after a
  newer own answer or reset, and reset in the existing mount.
- Navigation teardown and restoration of saved data without auto-submission.
- Private inspection, default exclusion of reasons, explicitly approved reason
  sharing, share clearing, withheld feedback before reveal and reopening.
- Public transport privacy across captured states and full projected alternatives
  fitting the activity rectangle. Long German projection fits at about 16.7px
  in a 1200×680 activity rectangle.

Separate installed-renderer probes cover queue refusal, a late rejection after
reset, editing while a save is in flight, page command guards, long German
labels and cleanup. A separate **real German deck** runs in all three browsers:
German requirements survive native transport, a Unicode/emoji reason is saved,
and the accepted model is revealed. Synthetic fixtures use the original bundle
Unicode; they do not substitute for this native-language test.

All three browsers also pass the existing 31-sample engine/security harness:
production CSP, blocked network APIs and nested workers, rejected dynamic code,
invalid-result rejection, timeout termination and successful recovery. The
worker policy remains `default-src 'none'; script-src 'self' 'wasm-unsafe-eval';
connect-src 'none'; worker-src 'none'`.

Real screenshots were inspected for phone decisions/preview/feedback, presenter
inspection, projector alternatives and German long labels. Visual review led
to bounded scrolling for the presenter toolbar and fitted projector text.
Static LaTeX layout is unchanged; the full installed-wheel suite rebuilt
English/German/long-label editions with existing PDF overflow/page-bound checks.
The earlier [E2 visual record](er-prepared-authoring-validation.md) remains
the static-layout evidence.

## Limits and next work

This closes the bounded registration E4 pilot. It does not implement room
identity or open assumptions and does not prove every database model equivalent.
The existing 64-actor storage bound is not a measured class-size guarantee.

E5 still needs physical Android/iOS phones, screen readers, concurrent classroom
load/queue fairness, Linux consumption of identical artifacts, combined-provider
release CI and an immutable published host pin. No catalog entry, commit, push
or release publication was performed. Existing courses, original lecture-tools,
and private media were not changed.

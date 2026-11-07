# Normalization Workshop: 600 students and a 1,000 ceiling

Local validation on Windows, 2026-11-07. Provider **0.4.0** targets 600 students
and refuses a 1,001st saved answer per item. The host defaults to 1,000 active
participants per session. This is an experimental local implementation;
classroom acceptance and catalog publication remain separate.

## Implementation and compatibility

Shared state v3 holds counters, page and at most two selected/shared references.
Answers occupy item/epoch-scoped transactional records, with a 1,000-record
provider limit. Presenter pages contain 16 summaries and at most four pinned
summaries. Stable answer numbers survive replacement. At most 20 records are
read for a presenter control view; a phone reads only its own record. Page order
follows record keys and can shift as answers arrive.

Two checked answers can be compared across pages. Selection is version-checked;
replacement invalidates affected comparison/sharing. Reset clears records and
pending jobs atomically. Use a new bundle and fresh session; existing v1/v2
sessions stay in their original pinned environment. All nineteen old schema
files are byte-identical. Six new schemas bring the total to 25.
Participant, engine and authoring schemas and mathematical rules are unchanged.

The provider uses the host's existing item records, actor-scoped updates and
deterministic successful-result reuse. Every student retains a separate durable
job and independent semantic verification. The server verifier caches at most
64 immutable reference analyses keyed by the full seed and answer. It never
caches supplied worker facts as truth. Tests cover forged facts, changed seeds,
explicit computation budgets and eviction.

No worker CSP, network restriction, worker count, hook deadline, state/message
budget or queue ceiling was increased. No host runtime code changed in this task.

## Measured workload

Each run uses authenticated synthetic WebSockets, a real presenter evaluator
and projector, restricted workers and the installed portable wheel. The initial
burst has 32 variants (30 distinct decompositions). Further phases replace wrong
answers with current correct answers, exercise both active items, and disconnect
a presenter with two durable leases. Both abandoned jobs must finish in generation
2. Every latest checked answer must equal the submitted content. Successful
cached deliveries require a durable accepted success. Personal feedback stays
withheld before reveal.

The two visible activities receive **staggered** whole-class bursts. Two
simultaneous 600-answer bursts can exceed the unchanged 1,000-pending-job queue.
Queue-full refusal preserves the old answer and phone draft; retry later.
The example deck presents one activity at a time.

Values below are the worst p95 across initial, latest replacement and the two
active-item phases. Recovery is the maximum per-student time. The unchanged
targets are ACK p95 <= 5 s, feedback p95 <= 30 s, recovery maximum <= 150 s.

| Presenter | Students | ACK p95 | Feedback p95 | Recovery maximum | Timing targets |
| --- | ---: | ---: | ---: | ---: | --- |
| chromium 156.0.8078.80 | 600 | 4.96 s | 10.96 s | 11.96 s | pass |
| firefox 153.0 | 600 | 4.87 s | 13.09 s | 13.83 s | pass |
| webkit 26.5 | 600 | 5.43 s | 12.98 s | 13.60 s | ACK target missed |
| chromium 156.0.8078.80 | 1000 | 10.44 s | 21.89 s | 23.89 s | ACK target missed |

All four runs pass correctness and orderly shutdown. The final 600-student
WebKit burst missed the five-second acknowledgement target (5.43 s p95);
Chrome and Firefox passed. Feedback stayed below 13.1 s p95 in all three.
The earlier pre-layout 600-student runs met the timing targets, so the final
result is retained as evidence of limited timing margin, not called a green
performance gate. Classroom/network testing and consistent ACK latency remain
release work. The 1,000 run additionally checks refusal of another
join; its timings are separate from the 600-student target. Loopback measurements
do not guarantee Wi-Fi, WAN or presenter hardware performance. Students are
protocol clients here; separate UI tests render real phone-sized pages.

## Other verification

- 56 installed-provider tests pass, including real-runtime 1,000-record capacity,
  replacement with the queue full, privacy, last-page bounds, reset, receipts,
  cross-page comparison and cache tampering.
- 95 host record/cache/broadcast/classroom/contract/evaluator/lifecycle regressions
  pass. Fourteen evidence-check tests reject missing actors, false success,
  stale retries and invalid cached deliveries.
- Chrome, Firefox and WebKit pass the full native phone/presenter lesson flow
  and active worker security probes: forbidden network/evaluation/nested-worker
  behavior, invalid-result rejection, timeout termination and recovery.
- Wheel/sdist resource parity and frozen schema hashes pass. Maximum canonical
  schema-shaped sizes: state 3,458 bytes; record 1,833; presenter controls 20,292;
  analysis view at most 55,241. Host ceilings remain 256 KiB per transition
  and 128 KiB per view.

Earlier local attempts missed the five-second ACK target before adding the
bounded independent-reference cache. A probe also clicked its next presenter
action before the new control revision rendered. It now waits for the rendered
state while keeping all version guards. Those attempts remain diagnostic
evidence and are not counted as passing runs.

## Reproduce and identify artifacts

Install the exact host and provider wheels below in an isolated environment
with the host's locked development requirements. Enable only this provider.
From the collection root:

```sh
python -m pytest plugins/normalization-workshop/tests -q
python maintenance/normalization_load_probe.py --output <fixture-dir>
node --test maintenance/normalization_load_checks.test.cjs
```

Set `PYTHON` to the isolated interpreter, `BROWSER` to `chromium`, `firefox` or
`webkit`, `NORMALIZATION_ACTORS=600`, `NORMALIZATION_LOAD_OUTPUT` to a fresh output
directory, and `TEXSTAGE_TEST_PORT` to a free loopback port. Configure Playwright
and its browser cache; `TEXSTAGE_BROWSER_CHANNEL=chrome` selects installed Chrome.

```sh
node maintenance/normalization_load_browser.cjs <fixture-dir>/build/load.bundle
```

Use 1,000 actors for a separate ceiling experiment. The harness retains the same
numeric budgets and exits nonzero on a missed target even at the ceiling;
inspect correctness and timing separately. Missing phases/results cannot pass.

Host: `texstage-0.2.1.dev5-py3-none-any.whl`, SHA-256 `e017c73bfdf7410fd0dbfb3e4757fa7c1e796d748ebef51c110bce85057b1a6a`.

Provider: `texstage_normalization_workshop-0.4.0-py3-none-any.whl`, SHA-256 `361c02c0beeb229b4c34a66e73b399a4456e36daec9d325b43fb285378c79d8e`.

Source archive: `texstage_normalization_workshop-0.4.0.tar.gz`, SHA-256 `996ecbef26c13c3d74c179d76ae28281ad7a7efeec4e228650988daca7fee9e7`.

The [JSON record](normalization-workshop-600-validation.json) identifies the
host base commit, source snapshot, provider payload and test results.
A `texstage>=0.2.1.dev4` dependency alone does not identify unpublished contracts;
this measurement uses the recorded 0.2.1.dev5 wheel.

Ignored local evidence is under `artifacts/normalization-600/`: compressed
synthetic events, reports, screenshots, test logs and wheels. No personal browser
profile, real student submission, course content or private video is included.

Physical Android/iPhone tests on the classroom network, human screen-reader/
learner review, cross-platform hosted CI and a reviewed published host pin
remain release gates. Original repositories, courses and installed course
environments are unchanged. No commit or push is part of this task.

# FD Lab publication merge validation

Date: 2026-11-07. The prepared FD Lab 0.6.0 implementation was merged with the
collection's newer Query-plan and Normalization Workshop work. TeXStage uses
commit `6b64828b98e9908fc67c265cab31a71a216308d5` (`0.2.1.dev7`), published on
GitHub and the GitLab code mirror. The collection keeps its default branch,
`codex/plugin-system`.

## What the merge preserves

TeXStage already included actor records, fixed activity points, quiz speed/streak
scoring and bounded item records. The merge keeps that newer implementation and
adds the FD manifest-3/4 actor-update regression test. No security policy, worker
budget or storage-durability restriction was relaxed.

The collection keeps every existing non-FD conformance job and both newer
plugins. FD tests now use the immutable merged host pin. The optional capacity
job tests 600 students in three browsers and treats 1,000-student timings as a
separate headroom measurement.

## Installed artifacts and checks

The checks used a fresh isolated environment with the host's hash-locked build
and development requirements. The host wheel was rebuilt from its source
archive with byte-identical contents. The FD wheel/source archive had matching
provider manifests. The 42-file handoff, installed package bytes and newly built
English/German bundles were verified together.

- Host plugin, classroom, game and scoring checks: **269 passed, one skipped**
  because symlink creation is unavailable on this Windows host.
- FD engine, lessons, points, authoring and artifact checks: **153 passed**,
  including both LaTeX editions.
- Standalone FD Node engine: **30 cases passed**.
- All six generated provider worker bundles passed their freshness checks.
- Host documentation, LaTeX reference/manual consistency and public-history
  checks passed; no private video or narration was included.

The fresh Git checkout normalizes eight JSON schema files to LF. Their content
is unchanged, but the resource bytes and provider payload differ from the
previous local candidate. The current payload is
`17e3efd1a57c9500f6a2debfd36b2647d93e0b419817acc849559012920a6c63`.
Use a newly built bundle and explicitly enable this payload in a fresh session.
The earlier [three-browser performance record](functional-dependencies-prepared-validation.md)
retains its original host and artifact identities; those historical measurements
are not relabeled as measurements of this merge.

## Merged-host capacity regression

The Chromium run used 600 synthetic protocol participants, one rendered phone
and one presenter on local loopback, on the same machine as the earlier report.
It checked closure practice, all candidate keys and implication counterexamples,
with 600 distinct submissions and 600 changed replacements in each mode:
**3,600 checked submissions across six bursts**.

| Measurement | Result |
| --- | ---: |
| Feedback p95 over the six bursts | 3.55-4.41 s |
| Slowest feedback | 4.48 s |
| Highest phone input p95 | 2.1 ms |
| Feedback without a presenter browser | 0.25 s |

Every burst passed the feedback p95 <10 s, worst <30 s and input p95 <100 ms
gates. The harness also verified private pre-reveal credits, published points,
CSV awards, all 24 roster pages, the last student's answer, reset without
removing other activity awards, reconnect, receipt replay and forged-result
rejection. This is a Chromium regression check for these merged artifacts;
Firefox/WebKit capacity measurements remain in the earlier report. Physical-phone
and lecture-network measurements remain deferred.

Raw evidence: [Chromium report](functional-dependencies-publication/600-chromium.json)
and [artifact identity](functional-dependencies-publication/identity.json).
The [host CI run](https://github.com/stefanjdecker/texstage/actions/runs/42390962062)
passed all four OS/Python jobs and the container job after publication. Plugin
conformance CI runs separately after the collection push; local results do not
substitute for that hosted evidence.

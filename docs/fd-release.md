# FD Lab release conformance

FD Lab 0.4.0 uses the new `actor-slots-v1` host contract on the paired
`codex/600-participant-capacity` branches. The exact local host commit is
`a67229a353b5b7bd3e058618ae71dfef619b0f81`. Functional checks passed locally;
the feedback-latency gate remains open. This commit must be published before
the collection's CI can fetch it. Use the host and provider artifacts recorded in the
[capacity report](design/functional-dependencies-600-validation.md); do not use
the previous host pin for this version. Rebuild bundles and start new sessions.
The package version `0.2.1.dev3` alone does not identify a compatible host.

The **previous 0.3.0 candidate** used the published TeXStage `codex/plugin-system` commit:
[`34d0c537135f32b0690147dbb66dd8ff155987f8`](https://github.com/stefanjdecker/texstage/commit/34d0c537135f32b0690147dbb66dd8ff155987f8).
The same historical commit is mirrored to GitLab. It does not support 0.4.0.
This is an experimental candidate, not a catalog release or a stable API promise.

[Host CI](https://github.com/stefanjdecker/texstage/actions/runs/42351229078) and
[collection CI](https://github.com/stefanjdecker/texstage-plugins/actions/runs/42351969530)
passed for the earlier 0.3.0 source revisions recorded in the
[F5 validation report](design/functional-dependencies-f5-validation.md).
That report includes the tested wheel hashes, downloaded artifact verification,
and its local capacity checks. Those hosted results are not evidence for 0.4.0.

## Build and verify

The collection's [conformance workflow](../.github/workflows/conformance.yml)
uses that immutable capacity host pin. Publish the host before pushing this
collection branch, and retain the resulting hosted run evidence separately.
Manual runs accept another full reviewed host SHA; the FD producer rejects
floating refs and verifies that its checkout matches the requested commit.

The Linux FD producer installs the host's hash-locked tools and the required
TeX, font and English/German language packages. It checks generated workers,
builds the host and provider wheels, verifies provider sdist parity, and runs
all FD tests. Both language variants must compile slides, handouts, solutions
and direct-pdfLaTeX exports. A skipped producer test fails the job.

`FD_TEST_EXPORTS` selects a fresh output directory for the two test bundles and
PDFs. The German case translates provider-generated content and controls; the
surrounding example slide titles remain English. It is a localization test,
not a separately translated course.

```sh
python -c "from pathlib import Path; Path('artifacts').mkdir(exist_ok=True)"
FD_TEST_EXPORTS=artifacts/fd-exports python -m pytest plugins/fd-lab/tests maintenance/tests/test_fd_artifacts.py -q --basetemp=artifacts/fd-tests
```

On PowerShell set `$env:FD_TEST_EXPORTS='artifacts/fd-exports'` before the command.
Use a fresh FD-only environment with the matching installed host/provider wheels,
as described in the [lesson guide](fd-lesson.md); do not use an existing course
environment. The original coordinate examples and other engines retain their
separate installation scenarios.

## Identical artifact consumers

`maintenance/fd_artifacts.py create` packages the exact host wheel, FD wheel and
sdist, dependency locks, and both language bundles/PDFs. Its manifest records
the host commit, provider identity/payload, every file's size and SHA-256.
It verifies installed package resources against the wheels before upload.

Windows and the Chromium/Firefox/WebKit jobs download that same handoff. They
verify its file inventory and host pin before installation, then verify installed
resource bytes and provider payload afterward. They do not rebuild the wheels.
The Windows consumer may skip the two TeX authoring cases; Linux supplies the
required authoring evidence. Browser jobs run the restricted engine checks,
the full English lesson sequence and the German UI checks.

```sh
python maintenance/fd_artifacts.py verify handoff --host-commit a67229a353b5b7bd3e058618ae71dfef619b0f81
python -m pip install --require-hashes --only-binary=:all: -r handoff/requirements/dev.txt
python -m pip install --no-deps handoff/wheels/*.whl
python maintenance/fd_artifacts.py installed handoff --host-commit a67229a353b5b7bd3e058618ae71dfef619b0f81
```

The German UI test deliberately uses English browser locales. It exercises
presenter and participant keyboard actions, phone touch controls, real answer
evaluation, an 800Ã—500 presenter workspace and a 320-pixel phone layout.
Screenshots and JSON reports are retained in CI artifacts.

The manual workflow input `capacity` additionally runs 600-participant bursts in
all three browsers and a separate Chromium 1,000-participant headroom case.
Timing enforcement stays enabled and failed measurements are uploaded too.

The previous [F4 performance record](design/functional-dependencies-f4-performance.md)
remains evidence for its exact artifacts and named Windows hardware. Rebuilt
source-normalized artifacts have new hashes; do not reuse old wheel or payload
pins. The [F5 follow-up](design/functional-dependencies-f5-validation.md) records
Chromium input-latency misses and a WebKit setup timeout for 0.3.0. The new
[capacity record](design/functional-dependencies-600-validation.md) supersedes
those measurements for 0.4.0. CI timing on shared runners is not a
capacity guarantee for a lecture LAN.

## Release boundary

Successful local tests are not hosted CI evidence. Check the actual workflow
jobs and retain their artifact identities before publishing a release. CI
artifacts expire according to workflow retention; they are not permanent release
assets. A catalog entry requires immutable published wheels, ownership/license
review, tested host compatibility and exact hashes.

No catalog entry is added by these checks. Physical-phone validation remains
deferred under the requested automated-only scope. Original repositories,
course pins and private video/narration are outside this release preparation.

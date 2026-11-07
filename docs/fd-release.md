# FD Lab release conformance

The compatible host is published on the TeXStage `codex/plugin-system` branch:
[`34d0c537135f32b0690147dbb66dd8ff155987f8`](https://github.com/stefanjdecker/texstage/commit/34d0c537135f32b0690147dbb66dd8ff155987f8).
The same commit is mirrored to GitLab. Use this exact commit for the current
candidate; `main` and the version string `0.2.1.dev3` do not identify these fixes.
This is an experimental candidate, not a catalog release or a stable API promise.

## Build and verify

The collection's [conformance workflow](../.github/workflows/conformance.yml)
uses this immutable host pin by default, including automatic branch runs.
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
python maintenance/fd_artifacts.py verify handoff --host-commit 34d0c537135f32b0690147dbb66dd8ff155987f8
python -m pip install --require-hashes --only-binary=:all: -r handoff/requirements/dev.txt
python -m pip install --no-deps handoff/wheels/*.whl
python maintenance/fd_artifacts.py installed handoff --host-commit 34d0c537135f32b0690147dbb66dd8ff155987f8
```

The German UI test deliberately uses English browser locales. It exercises
presenter and participant keyboard actions, phone touch controls, real answer
evaluation, an 800×500 presenter workspace and a 320-pixel phone layout.
Screenshots and JSON reports are retained in CI artifacts.

The previous [F4 performance record](design/functional-dependencies-f4-performance.md)
remains evidence for its exact artifacts and named Windows hardware. Rebuilt
source-normalized artifacts have new hashes; do not reuse old wheel or payload
pins. CI timing on shared runners is not a capacity guarantee for a lecture LAN.

## Release boundary

Successful local tests are not hosted CI evidence. Check the actual workflow
jobs and retain their artifact identities before publishing a release. CI
artifacts expire according to workflow retention; they are not permanent release
assets. A catalog entry requires immutable published wheels, ownership/license
review, tested host compatibility and exact hashes.

No catalog entry is added by these checks. Physical-phone validation remains
deferred under the requested automated-only scope. Original repositories,
course pins and private video/narration are outside this release preparation.

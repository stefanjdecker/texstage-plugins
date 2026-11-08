# Transaction and relational release handoff

This handoff covers the independent transaction engine 0.1.0, transaction
activity 0.1.0 and Relational Algebra Lab 0.2.0. They remain experimental
candidates. The active [catalog](../catalog/index.json) has no published releases.

Use the [classroom release validation](design/classroom-release-validation.md)
for the exact host revision, artifact identities, CI runs and measured limits.
Do not identify a compatible host from `0.2.1.dev7` alone: several development
revisions have used that version string. Transaction lessons need the archive
and command-processing changes included in the tested host pin.

## Ready for a maintainer to review

Each candidate consists of its portable wheel, source archive, SHA-256 checksum,
provider payload and installed-wheel test evidence. The matching host candidate
has a wheel/source rebuild comparison. Transaction engine tests run independently
of the activity, and relational tests use a separate installation. Browser jobs
must consume the same producer artifacts rather than build replacements per OS.

The transaction activity remains formative: it provides prediction, diagnosis
and repair feedback without scoreboard points. The relational editor remains a
64-participant pilot; transaction load measurements do not widen that claim.
Physical-phone, classroom-network and human accessibility acceptance is pending;
use the [prepared checklist](classroom-device-checklist.md).

Capacity acceptance is also still open: the latest transaction matrix has
Linux WebKit burst crashes, a Chromium/1,000 acknowledgement p95 miss and a
Firefox/1,000 setup timeout before measurements. The shared host's B+ check
also reproduces WebKit load crashes. Keep the exact failed and successful
scenarios in the validation record; do not call this an unrestricted
600/1,000-student release.

The host's `NOTICE` still leaves the inherited PowerPoint converter's publication
license unresolved. Its `Private :: Do Not Upload` classifier remains in place.
Resolve that concrete attribution/license question before distributing the host
package. The existing source branches and CI artifacts are distinct from an
approved supported package release. No PyPI upload is configured or performed.

## Publish the reviewed bytes

After the applicable publication and acceptance gates are settled, choose the
release status and immutable tags. Proposed per-package tag names are
`transaction-engine-v0.1.0`, `transaction-activity-v0.1.0` and
`relational-lab-v0.2.0`; these names are proposals, not evidence of existing tags.
An explicitly experimental prerelease must retain its documented device/capacity
limits. Do not describe it as classroom-accepted while those checks are pending.

1. Verify that the source ref, wheel, sdist and recorded payload match the tested
   candidate. Rebuild/retest if package bytes change. Publish the compatible host
   code pin to both code remotes and include that pin in the release notes.
2. Create each release at the reviewed collection commit and attach its exact
   wheel, sdist, checksum and validation notes. Retain the tested engine/activity
   pair together in the installation instructions. Keep private recordings and
   production scripts in the private media repository.
3. Download each release asset through its immutable tag URL and verify its
   SHA-256. Then add the reviewed wheel to a temporary catalog using the helper:

   ```sh
   python maintenance/catalog_entry.py path/to/reviewed.whl --url https://github.com/stefanjdecker/texstage-plugins/releases/download/IMMUTABLE_TAG/EXACT_WHEEL_NAME --output path/to/staged-index.json
   ```

4. Check the staged entry's ID, version, distribution, payload, SHA-256, license
   and URL against the release asset. Merge the reviewed entries into
   `catalog/index.json`, preserving all existing entries. Never replace bytes
   under an already published version/tag. Use withdrawal metadata for a bad
   release and publish a new version for a fix.
5. Rehearse installation and explicit enablement in a new operator profile.
   Uploading a deck or importing a style must not install or enable plugins.
   Adopting the release in an existing course is a separate migration.

Before publication, candidate catalog entries belong in the local artifact
handoff, not the active index: their proposed asset URLs do not yet exist.

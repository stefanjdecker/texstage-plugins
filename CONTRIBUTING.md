# Contributing plugins

Start with an independently buildable directory under `plugins/`, a unique
qualified ID, an explicit license and a synthetic example. Use a separate Python
package namespace and a portable `py3-none-any` wheel. Declare every capability,
message schema, renderer surface and style export. The SDK generates the complete
resource inventory; do not edit installed hashes by hand.

Keep author data, private references, persisted state and role-filtered views
separate. Reducers are deterministic and have no I/O. Route evaluation through
declared bindings, use unique correlation IDs, and ignore obsolete results.
Renderers must support keyboard input, touch, resize and idempotent teardown.
Do not depend on global UI elements or import another provider's modules.

Before review, build the wheel and sdist, check payload parity, install into a
fresh environment and run the Python and real-browser conformance checks. Test
crashes, retries, resets and the private answer boundary. Attach platform/browser
versions and reproducible synthetic cases. A successful example is not proof that
all release gates pass.

Catalog-only external entries need the same review: ownership, license,
compatibility, immutable release URL, wheel and payload hashes, dependencies and
conformance evidence. Do not include credentials, personal submissions, private
lecture files or unpublished media. Catalog releases are immutable; withdrawals
preserve old entries and existing locks.

For richer activities, distinguish reference-output equality from validity of a
student's solution. Use schema-validated engine facts and explicit domain
criteria when several different answers are valid. Separate global snapshot
revision, activity-phase guards and actor-local answer versions; preserve a
student's draft and focus across unrelated updates. Do not hide a missing host
contract inside encoded text summaries or duplicated static solutions.

The [transaction-schedule design and plan](docs/design/transaction-schedules-plan.md)
provide a worked review case. Its checker verifies the proposed finite model;
it does not replace installed-wheel, browser, privacy or classroom-load testing.

Use `maintenance/build_wheels.py --package <directory>` to build a specific
installation scenario. The original coordinate/distance tests must still see
exactly those two providers. Run the transaction engine's tests in an
engine-only environment; its [README](plugins/transaction-engine/README.md)
documents the probe and typed result format. Do not weaken the original fixture
gate when adding another package.

The [relational engine](plugins/relational-lab/README.md) has its own isolated
installation, typed schemas and independent Python model. Its
[v1 contract](docs/design/relational-algebra-contract.md) distinguishes finite
construction checks from verified rewrite certificates. Run its package tests
and actual-host browser probe; a successful Node import does not close the
Firefox/WebKit worker-policy gate.

The [FD engine](plugins/fd-lab/README.md) provides a smaller finite reasoning
example: named-source compilation, set-based Python analysis, a bit-mask browser
engine and checked proof/counterexample facts. Its exact three-attribute tests
compare closures with all closed attribute sets, independently of either runtime.
Run its tests in an FD-only installed-wheel environment; the browser probe uses
the existing worker-security harness. Engine facts are not a lesson or grade.

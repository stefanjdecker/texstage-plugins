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

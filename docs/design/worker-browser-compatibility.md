# Worker browser compatibility

Validated locally on Windows, 2026-11-06. Both the transaction engine and relational
algebra engine run in the installed Texstage evaluator on Chrome, Firefox and
WebKit. This supersedes the startup failures in the earlier M2/R2 records.
The [machine-readable evidence](worker-browser-compatibility.json) records exact
wheel, provider, schema, host payload and source hashes.

## Fix and security boundary

Static dependency loading failed under the existing worker policy. Moving only
the root import to initialization resolved WebKit; Firefox still rejected deeper
static imports. The final host worker dynamically loads a self-contained contract
module, and each engine manifest points at its generated self-contained ES module.
The editable source modules remain in their packages.

The HTTP Content Security Policy is unchanged:

```text
default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'
```

No server policy, plugin API, result schema, resource-hash verification, explicit
enablement rule or evaluation deadline was relaxed. The bundled validator is
generated from the same source as the presenter validator. Host and collection
CI check generated output against source using pinned esbuild 0.28.2 and npm
lockfiles. Python builds, wheels and end-user installations need no bundler.

## Browser results

Each engine's eight real samples cover four domain cases, malformed input,
oversized input, invalid seed and a repeated fresh evaluation. Times are the
slowest sample in that local run, not a capacity claim.

| Browser | Transaction | Relational algebra | Security probes per engine |
| --- | --- | --- | --- |
| Chrome 156.0.8078.80 | 8/8; 23 ms | 8/8; 21 ms | 10/10 blocked; recovery passed |
| Firefox 153.0 | 8/8; 122 ms | 8/8; 141 ms | 10/10 blocked; recovery passed |
| WebKit 26.5 | 8/8; 49 ms | 8/8; 94 ms | 10/10 blocked; recovery passed |

The ten active probes cover same-origin and cross-origin fetch, XHR, WebSocket,
EventSource, a same-origin child worker, a blob child worker, cross-origin dynamic
module import, eval and Function construction. An unrestricted control worker
first proves every local fixture/API works. The real evaluator retains its
production CSP: all ten attempts are blocked and the test servers receive zero
forbidden requests. Separate checks reject invalid typed data, terminate an
infinite loop at the host's two-second deadline, remove all workers and run the
real plugin successfully afterward. A timeout in a policy probe is a failure,
not evidence of blocking.

Security fault injection replaces only an engine response in a disposable
loopback test server. It does not modify an installed package, the evaluator
worker or its CSP. The original pair's harness uses this server-side approach
because Firefox bypassed Playwright's worker-response interception.

## Regression and packaging evidence

- Transaction engine: 67 tests passed, including 1,742 small legal interleavings.
- Relational algebra: 48 tests passed, including bounded-domain and independent
  Python/SQLite comparisons.
- Texstage: 408 unique tests passed; one symlink-creation test skipped. The full
  suite initially had six registry-permission failures in the sandbox; those
  checks passed on retry using only their dedicated test registry key.
- Original coordinate/distance pair: four isolated-provider tests passed.
  Presenter/projector/phone interaction, touch, reveal/reset, mount cleanup,
  typed-result rejection, worker network policy and deadlines passed in all
  three browsers.
- Host wheel/sdist rebuild: all wheel members identical. Both database plugin
  sdists rebuild with identical provider manifests and resource payloads.
- Installed host and engine bytes match the tested final wheels. Bundle freshness,
  dependency locks, documentation links and existing manual consistency checks pass.

The exact host development wheel is `texstage-0.2.1.dev3-py3-none-any.whl`.
Its SHA-256 is `c320424765419189b78e885df034c765cd81af016ca074ecd02b0c3cbf5199d0`. A version constraint alone cannot identify the
unpublished changes sharing that version. Plugin wheel/provider hashes are in
the JSON evidence. This is local evidence; hosted CI and cross-OS artifact
consumer jobs were not run.

## Reproduce

Use isolated environments with the matching host wheel and its locked development
requirements. Keep the transaction, relational and original-pair Python suites in
separate provider environments; their exact-provider assertions remain intact.

After editing host or plugin JavaScript, run this in the relevant repository:

```sh
npm ci --ignore-scripts
npm run build:workers
npm run check:workers
```

Commit the generated modules with their source. In the collection, build the
selected plugin, install that wheel and run the package's tests and Python probe,
as documented in each package README. The probe generates the installed-host
browser configuration. Then run:

```sh
npx playwright install chromium firefox webkit
BROWSER=chromium node maintenance/transaction_engine_browser.cjs
BROWSER=firefox node maintenance/transaction_engine_browser.cjs
BROWSER=webkit node maintenance/transaction_engine_browser.cjs
BROWSER=chromium node maintenance/relational_browser.cjs
BROWSER=firefox node maintenance/relational_browser.cjs
BROWSER=webkit node maintenance/relational_browser.cjs
```

On PowerShell set `$env:BROWSER='firefox'` before the Node command.
For installed Chrome set `TEXSTAGE_BROWSER_CHANNEL=chrome` only for the
`chromium` runs. Browser reports include the actual version and policy.

Changing engine bytes changes provider payloads. Rebuild and approve new pins
explicitly in a disposable profile before any later course migration.
This work leaves original repositories, existing courses and their environments
unchanged. No pins, catalog release, commit or push are included.

Database lesson interfaces, physical-phone checks, scheduling/capacity gates and
a published compatible host remain separate work. Playwright WebKit validation
does not claim testing on an actual Safari/iPhone device.

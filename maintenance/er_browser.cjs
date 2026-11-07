// SPDX-License-Identifier: Apache-2.0
// Installed host evaluator + installed plugin, with the host worker's real CSP.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const {fileURLToPath} = require("node:url");
const {chromium, firefox, webkit} = require("playwright");
const output = path.resolve(process.argv[2] || "artifacts/er-decisions");
const config = JSON.parse(fs.readFileSync(path.join(output, "browser-config.json")));
const requests = JSON.parse(fs.readFileSync(path.join(output, "browser-requests.json")));
const goldens = JSON.parse(fs.readFileSync(path.join(output, "results.json")));
const workerCSP = "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'none'; worker-src 'none'";
assert(fs.readFileSync(path.join(config.host_root, "server/app.py"), "utf8").includes(workerCSP),
  "The host worker CSP changed; update this integration check.");
const prefix = "/plugins/" + config.payload + "/";
const files = new Map();
for (const name of ["stage/plugin-evaluator.js", "stage/plugin-evaluator-worker.js",
                    "stage/plugin-contracts.js", "stage/plugin-contracts-worker.mjs", "engines/common.js"]) {
  files.set("/static/" + name, path.join(config.host_root, "web", name));
}
files.set(prefix + config.job.engine.module, fileURLToPath(config.module));
for (const name of config.job.engine.assets) {
  files.set(prefix + name, path.join(config.provider_root, name));
}
const fetched = new Set();
const runInfo = {browser: process.env.BROWSER || "chromium", provider_payload: config.payload,
  host_result_schema: config.job.engine.result_contract.data_schema_digest, worker_csp: workerCSP};
const diagnostics = [];
const {securityFixtures, checkWorkerSecurity} = require("./plugin_worker_security.cjs");
const fixtures = securityFixtures();
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, "http://localhost").pathname;
  if (pathname === "/") {
    res.writeHead(200, {"Content-Type": "text/html; charset=utf-8"});
    return res.end("<!doctype html><meta charset=utf-8><title>ER registration engine worker check</title>");
  }
  if (pathname === "/favicon.ico") { res.writeHead(204); return res.end(); }
  if (fixtures.handle(req, res)) return;
  if (!files.has(pathname)) { res.writeHead(404); return res.end(); }
  fetched.add(pathname);
  const headers = {"Content-Type": "application/javascript", "Cache-Control": "no-store"};
  if (pathname.endsWith("/plugin-evaluator-worker.js")) headers["Content-Security-Policy"] = workerCSP;
  res.writeHead(200, headers);
  res.end(fs.readFileSync(files.get(pathname)));
});

server.on("upgrade", fixtures.upgrade);

(async () => {
  let browser;
  try {
    await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
    const base = "http://127.0.0.1:" + server.address().port;
    const family = process.env.BROWSER || "chromium";
    assert(["chromium", "firefox", "webkit"].includes(family));
    const options = {headless: true, timeout: 30000};
    if (family === "chromium" && process.env.TEXSTAGE_BROWSER_CHANNEL) options.channel = process.env.TEXSTAGE_BROWSER_CHANNEL;
    browser = await ({chromium, firefox, webkit}[family]).launch(options);
    runInfo.version = browser.version();
    const page = await browser.newPage();
    const external = [], errors = [];
    page.on("request", req => { if (!req.url().startsWith(base + "/")) external.push(req.url()); });
    page.on("pageerror", error => errors.push(error.message));
    page.on("requestfailed", request => console.error("Request failed:", request.url(), request.failure()));
    page.on("response", response => {
      if (response.status() >= 400) console.error("HTTP error:", response.status(), response.url());
    });
    page.on("console", message => {
      if (message.type() === "error") {
        diagnostics.push(message.text());
        console.error("Browser diagnostic:", message.text());
      }
    });
    await page.addInitScript(() => {
      const NativeWorker = window.Worker;
      window.Worker = class extends NativeWorker {
        constructor(...args) {
          super(...args);
          this.addEventListener("error", event => console.error(
            "Evaluator worker:", event.message, event.filename, event.lineno, event.colno));
        }
      };
    });
    await page.goto(base);
    const engine = {...config.job.engine, url: prefix + config.job.engine.module,
      assets: Object.fromEntries(config.job.engine.assets.map(name => [name, prefix + name]))};
    const samples = [
      ...requests,
      {...requests[0], text: "{"},
      {...requests[0], text: " ".repeat(1025)},
      {...requests[0], seed: "{}"},
      requests[0],
    ];
    const expected = [...requests.map(() => "ok"), "syntax", "refused", "error", "ok"];
    const rows = await page.evaluate(async ({samples, template, engine, expected}) => {
      const {PluginEvaluator} = await import("/static/stage/plugin-evaluator.js");
      const evaluator = Object.create(PluginEvaluator.prototype);
      evaluator.workers = new Set();
      evaluator.stopped = true; // No lease-poll loop; exercise the actual evaluate path.
      const rows = [];
      try {
        for (const [index, request] of samples.entries()) {
          const started = performance.now();
          const result = await evaluator.evaluate({...template, engine, text: request.text, namespace: request.namespace,
            binding: {...request.binding, seed: request.seed, options: request.options || {}}});
          rows.push({result, elapsed_ms: performance.now() - started, remaining_workers: evaluator.workers.size});
          if (result.status !== expected[index]) throw new Error("Unexpected evaluator status for sample " + index + ": " + result.status);
        }
      } finally { evaluator.destroy(); }
      return rows;
    }, {samples, template: config.job, engine, expected});
    assert.deepEqual(rows.map(r => r.result.status), expected);
    for (const [index, golden] of goldens.entries()) {
      assert.deepEqual(rows[index].result, golden.outcome);
    }
    const accepted = rows.slice(0, requests.length).filter(row =>
      row.result.data.model_valid && row.result.data.checks.every(c => c.admits === (c.expected === "allow")));
    assert.equal(accepted.length, 2);
    assert.notEqual(accepted[0].result.key, accepted[1].result.key);
    assert.deepEqual(accepted[0].result.data.checks, accepted[1].result.data.checks);
    assert.deepEqual(rows[0].result, rows.at(-1).result);
    assert(rows.every(r => r.remaining_workers === 0));
    assert(fetched.has("/static/stage/plugin-evaluator-worker.js"));
    assert(fetched.has(prefix + config.job.engine.module));
    assert(fetched.has(prefix + config.job.engine.assets[0]));
    assert.deepEqual(external, []);
    assert.deepEqual(errors, []);
    const security = await checkWorkerSecurity({page, base, fixtures, template: config.job, engine, request: requests[0]});
    const report = {...runInfo, security, passed: true, samples: rows.length, max_elapsed_ms: Math.max(...rows.map(r => r.elapsed_ms)),
      actual_host_deadline_ms: 2000, rows};
    fs.writeFileSync(path.join(output, "browser-" + family + ".json"), JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify({...report, rows: undefined}, null, 2));
  } catch (error) {
    console.error("Fetched modules:", [...fetched]);
    fs.writeFileSync(path.join(output, "browser-" + runInfo.browser + ".json"),
      JSON.stringify({...runInfo, passed: false, error: error.message, diagnostics, fetched: [...fetched]}, null, 2) + "\n");
    throw error;
  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

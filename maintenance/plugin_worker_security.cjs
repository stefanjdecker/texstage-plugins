// SPDX-License-Identifier: Apache-2.0
// Active CSP probes run through the installed host evaluator. The unrestricted
// control only proves that the local test endpoints and browser APIs work.
const assert = require("node:assert/strict");
const http = require("node:http");
const crypto = require("node:crypto");

function securityFixtures() {
  const requests = [], overrides = new Map();
  const handle = (req, res) => {
    const pathname = new URL(req.url, "http://localhost").pathname;
    if (overrides.has(pathname)) {
      res.writeHead(200, {"Content-Type": "application/javascript", "Cache-Control": "no-store"});
      res.end(overrides.get(pathname)); return true;
    }
    if (!pathname.startsWith("/__worker_probe__/")) return false;
    requests.push(pathname);
    const headers = {"Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"};
    if (pathname.endsWith("child.js")) {
      res.writeHead(200, {...headers, "Content-Type": "application/javascript"});
      res.end('postMessage("started");');
    } else if (pathname.endsWith("module.mjs")) {
      res.writeHead(200, {...headers, "Content-Type": "application/javascript"});
      res.end("export const reachable = true;");
    } else if (pathname.endsWith("events")) {
      res.writeHead(200, {...headers, "Content-Type": "text/event-stream"});
      res.end("data: reachable\n\n");
    } else {
      res.writeHead(200, {...headers, "Content-Type": "text/plain"}); res.end("reachable");
    }
    return true;
  };
  const upgrade = (req, socket) => {
    requests.push(new URL(req.url, "http://localhost").pathname);
    const accept = crypto.createHash("sha1")
      .update(req.headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest("base64");
    socket.write("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept + "\r\n\r\n");
    socket.on("data", () => socket.destroy());
    socket.on("error", () => socket.destroy());
    setTimeout(() => socket.destroy(), 1000).unref();
  };
  return {requests, overrides, handle, upgrade};
}

function probeModule(base, other) {
  return `
const base = ${JSON.stringify(base)}, other = ${JSON.stringify(other)};
export function start() { return {}; }
export function load() { return {}; }
export function dispose() {}
const ok = text => ({status: "ok", canonical: text, summary: {kind: "text", text}});
const attempt = start => new Promise(resolve => {
  let cleanup = () => {};
  const timer = setTimeout(() => finish("timeout"), 700);
  const finish = value => { clearTimeout(timer); cleanup(); resolve(value); };
  try { cleanup = start(finish) || cleanup; } catch { finish("blocked"); }
});
export async function evaluate(_state, text) {
  if (text === "loop") while (true) {}
  if (text === "invalid") return {...ok("invalid"), data: {unexpected: true}};
  const endpoints = "/__worker_probe__/";
  const checks = {
    fetch_same: attempt(done => {
      fetch(base + endpoints + "fetch").then(() => done("allowed"), () => done("blocked"));
    }),
    fetch_cross: attempt(done => {
      fetch(other + endpoints + "fetch").then(() => done("allowed"), () => done("blocked"));
    }),
    xhr: attempt(done => {
      const request = new XMLHttpRequest();
      request.onload = () => done("allowed"); request.onerror = () => done("blocked");
      request.open("GET", base + endpoints + "xhr"); request.send();
      return () => request.abort();
    }),
    websocket: attempt(done => {
      const socket = new WebSocket(base.replace("http:", "ws:") + endpoints + "socket");
      socket.onopen = () => done("allowed"); socket.onerror = () => done("blocked");
      return () => socket.close();
    }),
    eventsource: attempt(done => {
      const events = new EventSource(base + endpoints + "events");
      events.onmessage = () => done("allowed"); events.onerror = () => done("blocked");
      return () => events.close();
    }),
    child_worker: attempt(done => {
      const child = new Worker(base + endpoints + "child.js");
      child.onmessage = () => done("allowed");
      child.onerror = event => { event.preventDefault(); done("blocked"); };
      return () => child.terminate();
    }),
    blob_worker: attempt(done => {
      const url = URL.createObjectURL(new Blob(['postMessage("started")'], {type: "text/javascript"}));
      let child;
      try { child = new Worker(url); }
      catch (error) { URL.revokeObjectURL(url); throw error; }
      child.onmessage = () => done("allowed");
      child.onerror = event => { event.preventDefault(); done("blocked"); };
      return () => { child.terminate(); URL.revokeObjectURL(url); };
    }),
    external_module: attempt(done => {
      import(other + endpoints + "module.mjs").then(() => done("allowed"), () => done("blocked"));
    }),
    eval: attempt(done => { eval("1 + 1"); done("allowed"); }),
    function_constructor: attempt(done => { new Function("return 2")(); done("allowed"); }),
  };
  const values = await Promise.all(Object.values(checks));
  return ok(JSON.stringify(Object.fromEntries(Object.keys(checks).map((key, i) => [key, values[i]]))));
}
`;
}

async function checkWorkerSecurity({page, base, fixtures, template, engine, request}) {
  const external = http.createServer((req, res) => {
    if (!fixtures.handle(req, res)) { res.writeHead(404); res.end(); }
  });
  external.on("upgrade", fixtures.upgrade);
  await new Promise(resolve => external.listen(0, "127.0.0.1", resolve));
  const other = "http://127.0.0.1:" + external.address().port;
  const module = probeModule(base, other);
  const controlPath = "/__worker_probe__/control.mjs";
  fixtures.overrides.set(controlPath, module + '\nevaluate(null, "probe").then(result => postMessage(result.summary.text));');
  const run = text => page.evaluate(async ({template, engine, request, text}) => {
    const {PluginEvaluator} = await import("/static/stage/plugin-evaluator.js");
    const evaluator = Object.create(PluginEvaluator.prototype);
    evaluator.workers = new Set(); evaluator.stopped = true;
    const started = performance.now();
    try {
      const result = await evaluator.evaluate({...template, engine, text,
        namespace: request.namespace, binding: {...template.binding, seed: request.seed,
          options: request.options || {}, references: []}});
      return {result, elapsed_ms: performance.now() - started, remaining_workers: evaluator.workers.size};
    } finally { evaluator.destroy(); }
  }, {template, engine, request, text});
  try {
    const control = await page.evaluate(path => new Promise((resolve, reject) => {
      const worker = new Worker(path, {type: "module"});
      const timer = setTimeout(() => { worker.terminate(); reject(new Error("Control timed out")); }, 5000);
      worker.onmessage = event => { clearTimeout(timer); worker.terminate(); resolve(JSON.parse(event.data)); };
      worker.onerror = event => { clearTimeout(timer); worker.terminate(); reject(new Error(event.message)); };
    }), controlPath);
    assert(Object.values(control).every(value => value === "allowed"), "Probe fixtures must work without CSP: " + JSON.stringify(control));
    assert(fixtures.requests.includes("/__worker_probe__/socket"), "Control must exercise a real WebSocket handshake");
    const controlRequests = [...fixtures.requests];
    fixtures.requests.length = 0;
    // Synthetic engine only, served at the approved URL for this CSP test.
    fixtures.overrides.set(engine.url, module);
    const restricted = await run("probe");
    assert.equal(restricted.result.status, "ok");
    const checks = JSON.parse(restricted.result.summary.text);
    assert.deepEqual(Object.keys(checks), Object.keys(control));
    assert(Object.values(checks).every(value => value === "blocked"), "Worker CSP regression: " + JSON.stringify(checks));
    assert.deepEqual(fixtures.requests, [], "Restricted worker must not reach any network/child-module fixture");
    assert.equal(restricted.remaining_workers, 0);
    const invalid = await run("invalid");
    assert.equal(invalid.result.status, "error", "Typed result validation must still reject invalid data");
    assert.equal(invalid.remaining_workers, 0);
    const loop = await run("loop");
    assert.equal(loop.result.status, "timeout", "The host must terminate a non-cooperative engine");
    assert.equal(loop.remaining_workers, 0);
    fixtures.overrides.delete(engine.url);
    const recovered = await run(request.text);
    assert.equal(recovered.result.status, "ok", "A fresh real engine must work after failures");
    assert.equal(recovered.remaining_workers, 0);
    return {passed: true, checks, forbidden_requests: [...fixtures.requests], control, control_requests: controlRequests,
      invalid_result_status: invalid.result.status, loop_status: loop.result.status,
      loop_elapsed_ms: loop.elapsed_ms, recovery_status: recovered.result.status, remaining_workers: 0};
  } finally {
    fixtures.overrides.delete(engine.url); fixtures.overrides.delete(controlPath);
    external.closeAllConnections();
    await new Promise(resolve => external.close(resolve));
  }
}
module.exports = {securityFixtures, checkWorkerSecurity};

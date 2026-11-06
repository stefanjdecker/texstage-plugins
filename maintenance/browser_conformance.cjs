// SPDX-License-Identifier: Apache-2.0
// Real screens, mobile input, worker policy, timeouts, reset and mount teardown.
const fs = require("node:fs"), path = require("node:path"), { spawn } = require("node:child_process");
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, ".."), bundle = path.resolve(process.argv[2] || "artifacts/checks/plugins-installed0/out/plane.bundle");
const browserName = process.env.BROWSER || "chromium", output = path.join(root, "artifacts", browserName);
fs.mkdirSync(output, { recursive: true });
const profile = fs.mkdtempSync(path.join(output, "profile-"));
const port = Number(process.env.TEXSTAGE_TEST_PORT || 18747), base = `http://127.0.0.1:${port}`;
const server = spawn(process.env.PYTHON || "python", [path.join(__dirname, "serve_example.py"), "--bundle", bundle,
  "--data", profile, "--port", String(port)], { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
const log = fs.createWriteStream(path.join(output, "server.log")); server.stdout.pipe(log); server.stderr.pipe(log);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  let ready = false;
  for (let i = 0; i < 60; i++) {
    try { ready = (await fetch(`${base}/api/status`, { signal: AbortSignal.timeout(500) })).ok; } catch {}
    if (ready) break;
    if (server.exitCode !== null) throw new Error("Test server exited; see server.log");
    await delay(250);
  }
  if (!ready) throw new Error("Test server failed to start");
  const deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
  const browser = await playwright[browserName].launch({ headless: true,
    ...(process.env.TEXSTAGE_BROWSER_CHANNEL ? { channel: process.env.TEXSTAGE_BROWSER_CHANNEL } : {}) });
  const errors = [];
  try {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await ctx.addInitScript(() => localStorage.setItem("texquiz:presenter-key", "plugin-demo-key"));
    const presenter = await ctx.newPage(); presenter.on("pageerror", e => errors.push(e.message));
    await presenter.goto(`${base}/stage?bundle=${deck.bundle}`);
    await presenter.locator("#next").click();
    await presenter.getByRole("button", { name: "Reveal point", exact: true }).waitFor();
    const pin = (await presenter.locator("#pin").innerText()).replace(/\D/g, "");
    const projector = await ctx.newPage(); projector.on("pageerror", e => errors.push(e.message));
    await projector.goto(`${base}/stage/projector?bundle=${deck.bundle}`);
    await projector.locator(".projector-overlay svg").waitFor();
    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 },
      isMobile: browserName !== "firefox", hasTouch: true });
    const phone = await mobile.newPage(); phone.on("pageerror", e => errors.push(e.message));
    await phone.goto(`${base}/play?pin=${pin}`);
    await phone.locator("#nick").fill("Example participant"); await phone.locator("#join button[type=submit]").click();
    await phone.getByLabel("X coordinate").fill("3"); await phone.getByLabel("Y coordinate").fill("4");
    await phone.getByRole("button", { name: "Send point", exact: true }).click();
    await phone.getByRole("status").filter({ hasText: "Distance from the origin: 5.00" }).waitFor();
    await presenter.getByRole("button", { name: "Reveal point", exact: true }).click();
    await phone.getByText(/Correct point!/).waitFor();
    for (const [name, page] of [["presenter", presenter], ["projector", projector], ["phone", phone]])
      await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
    await presenter.getByRole("button", { name: "Reset responses", exact: true }).click();
    await phone.getByText("Tap the plane or enter coordinates, then send your point.").waitFor();
    // A touch at (0,5), mapped through the SVG viewport; it is equidistant but incorrect.
    const tap = await phone.locator(".participant-input svg").evaluate(svg => {
      const p = svg.createSVGPoint(); p.x = 200; p.y = 25;
      const s = p.matrixTransform(svg.getScreenCTM()); return { x: s.x, y: s.y };
    });
    await phone.touchscreen.tap(tap.x, tap.y);
    if (await phone.getByLabel("X coordinate").inputValue() !== "0" || await phone.getByLabel("Y coordinate").inputValue() !== "5")
      throw new Error("Touch coordinates do not match the plane");
    await phone.getByRole("button", { name: "Send point", exact: true }).click();
    await phone.getByRole("status").filter({ hasText: "Distance from the origin: 5.00" }).waitFor();
    await presenter.getByRole("button", { name: "Reveal point", exact: true }).click();
    await phone.getByText(/Reference: \(3, 4\)/).waitFor();
    if (await phone.getByText(/Correct point!/).count()) throw new Error("Incorrect equidistant point accepted");
    await presenter.locator("#next").click();
    await presenter.locator(".presenter-overlay").waitFor({ state: "detached" });
    await phone.locator(".participant-input").waitFor({ state: "detached" });
    // Fault injection changes only the browser response, never an installed package.
    const job = JSON.parse(fs.readFileSync(path.join(profile, "test-context.json")));
    const run = async (candidate = job) => presenter.evaluate(async job => {
      const { PluginEvaluator } = await import("/static/stage/plugin-evaluator.js");
      const evaluator = Object.create(PluginEvaluator.prototype); evaluator.workers = new Set();
      return evaluator.evaluate(job);
    }, candidate);
    const target = base + job.engine.url;
    const typed = structuredClone(job);
    typed.engine.result_data_schema = "synthetic/result.json";
    typed.engine.result_contract.data_schema = { type: "object", additionalProperties: false,
      required: ["valid", "order"], properties: {valid: {type:"boolean"},
        order: {type:"array", items:{type:"string"}, uniqueItems:true}} };
    const inject = async data => ctx.route(target, route => route.fulfill({contentType:"text/javascript",
      body: 'export const start=()=>({}),load=()=>({}),dispose=()=>{};export function evaluate(){return ' +
        JSON.stringify({status:"ok",canonical:"schedule",summary:{kind:"text",text:"Analyzed"},data}) + ';}' }));
    await inject({valid:true,order:["a","b"]});
    const facts = await run(typed);
    if (facts.status !== "ok" || !facts.data.valid || facts.data.order.join(",") !== "a,b" || "matches" in facts)
      throw new Error("Typed engine facts did not survive the real worker and transport");
    await ctx.unroute(target);
    await inject({valid:true,order:["a","b"],private:"unintended"});
    if ((await run(typed)).status !== "error") throw new Error("Worker accepted undeclared data fields");
    await ctx.unroute(target);
    await inject({valid:true,order:["a","b"]});
    if ((await run()).status !== "error") throw new Error("Revision-1 engine accepted undeclared data");
    await ctx.unroute(target);
    await ctx.route(target, route => route.fulfill({ contentType: "text/javascript", body:
      'export const start=()=>({}),load=()=>({}),dispose=()=>{}; export async function evaluate(){await fetch("/api/status");return {status:"ok",canonical:"x",summary:{kind:"text",text:"network"}};}' }));
    if ((await run()).status !== "error") throw new Error("Worker network policy did not block fetch");
    await ctx.unroute(target);
    await ctx.route(target, route => route.fulfill({ contentType: "text/javascript", body:
      'export const start=()=>({}),load=()=>({}),dispose=()=>{}; export function evaluate(){while(true){}}' }));
    if ((await run()).status !== "timeout") throw new Error("Evaluation budget was not enforced");
    await ctx.unroute(target);
    if (errors.length) throw new Error(errors.join("\n"));
    const report = { browser: browserName, interactions: true, touch: true, teardown: true, csp: true,
      timeout: true, typedResults: true, invalidResultsRejected: true, errors };
    fs.writeFileSync(path.join(output, "report.json"), JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(e => { console.error(e.stack); process.exitCode = 1; }).finally(() => { server.kill(); log.end(); });

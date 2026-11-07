// SPDX-License-Identifier: Apache-2.0
// Installed host/provider: static fallback plus authenticated E3 protocol clients.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn} = require("node:child_process");
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || "chromium";
const output = path.resolve(process.argv[3] || "artifacts/er-prepared", family);
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, "profile-"));
const port = Number(process.env.TEXSTAGE_TEST_PORT || 18762);
const base = "http://127.0.0.1:" + port;
const deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
const server = spawn(process.env.PYTHON || "python", [path.join(__dirname, "serve_lesson.py"),
  "--bundle", bundle, "--data", profile, "--port", String(port)],
  {windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log = fs.createWriteStream(path.join(output, "server.log"));
server.stdout.pipe(log); server.stderr.pipe(log);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  let browser;
  const errors = [], sockets = [], overlays = new Set();
  try {
    let ready = false;
    for (let i=0;i<100;i++) {
      try { if ((await fetch(base + "/api/status")).ok) { ready = true; break; } } catch {}
      await delay(100);
    }
    assert(ready, "server startup");
    browser = await playwright[family].launch({headless:true});
    const context = await browser.newContext({viewport:{width:1440,height:1000}});
    let presenter;
    await context.addInitScript(() => localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
    for (const role of ["presenter", "projector"]) {
      const page = await context.newPage();
      if (role === "presenter") presenter = page;
      page.on("pageerror", error => errors.push(error.message));
      page.on("response", response => {
        if (response.url().endsWith("/web/lesson-overlay.mjs") && response.ok()) overlays.add(role);
      });
      page.on("websocket", socket => socket.on("framereceived", ({payload}) => {
        try { const m = JSON.parse(String(payload)); if (m.t === "state") sockets.push({role,state:m}); } catch {}
      }));
      await page.goto(base + (role === "presenter" ? "/stage" : "/stage/projector") + "?bundle=" + deck.bundle);
      await page.locator(".texstage-plugin." + role + "-overlay").waitFor({state:"attached"});
      await page.waitForFunction(() => {
        const c = document.querySelector("canvas.tq-slide");
        if (!c || c.width < 100) return false;
        const pixels = c.getContext("2d").getImageData(0,0,c.width,c.height).data;
        let dark = 0;
        for (let i=0;i<pixels.length;i+=4) if (pixels[i+3] && pixels[i]<100) dark++;
        return dark > 1000;
      });
      assert(await page.locator(".er-overlay").isHidden(), "The static task is initially visible");
      if (role === "presenter") assert((await page.locator(".presenter-controls button").count()) >= 4);
      await page.screenshot({path:path.join(output, role + ".png"),fullPage:true});
    }
    assert.equal(overlays.size, 2, "both approved overlay modules loaded");
    assert(sockets.length > 0);
    for (const {role,state} of sockets) for (const item of state.plugins?.items || []) {
      const raw = JSON.stringify(item);
      for (const forbidden of ['"private":','"checks":','"evaluations":','duplicate-pair'])
        assert(!raw.includes(forbidden), "private material in role transport: " + forbidden);
      for (const view of Object.values(item.views || {})) {
        assert.equal(view.data.phase, "introduce");
        assert.equal(view.data.count, 0);
        if (role === "projector") assert(!view.data.teaching && !view.data.selected && !view.data.demonstration);
      }
    }
    const seed = JSON.parse(fs.readFileSync(path.join(__dirname,
      "../examples/er-decisions/activities/registrations.json")));
    const protocol = await presenter.evaluate(async ({deck, answers}) => {
      const {Client} = await import("/static/shared/client.js");
      const clients = [];
      const wait = async condition => {
        const deadline = performance.now()+15000;
        while (!condition()) {
          if (performance.now()>deadline) throw new Error("Protocol state timeout");
          await new Promise(r=>setTimeout(r,30));
        }
      };
      const assert = (ok, message) => { if (!ok) throw new Error(message); };
      const connect = async login => {
        const item = {state:null};
        item.client = new Client({onState:m=>{item.state=m;}});
        clients.push(item.client);
        item.welcome = await item.client.login(login);
        await wait(()=>item.state?.plugins?.items?.length);
        return item;
      };
      const projection = (client, surface) => client.state.plugins.items[0].views[surface];
      let counter=0;
      const send = async (client,surface,operation,payload) => {
        const current=projection(client,surface);
        const reply=await client.client.send({t:"plugin.command",command:{
          type:"io.github.stefanjdecker.erdecisions.lesson",item:"registrations",
          operation,payload,epoch:current.epoch,expected_revision:current.revision,
          request_id:"protocol"+String(++counter).padStart(8,"0")}});
        assert(reply.receipt?.accepted,JSON.stringify(reply));
        return reply;
      };
      try {
        const teacher=await connect({t:"hello",role:"stage",key:"plugin-demo-key",deck:deck.deck,bundle:deck.bundle});
        const pin=document.querySelector("#pin").textContent.replace(/\D/g,"");
        const phone=await connect({t:"join",pin,nickname:"ER test learner"});
        const display=await connect({t:"hello",role:"display",key:"plugin-demo-key",deck:deck.deck,bundle:deck.bundle});
        const controls=()=>projection(teacher,"presenter-controls").data;
        const own=()=>projection(phone,"participant-input").data;
        const projected=()=>projection(display,"projector-overlay").data;
        const control=async (op, extra={}) => {
          const version=controls().control_version;
          await send(teacher,"presenter-controls",op,{control_version:version,...extra});
          await wait(()=>controls().control_version>version);
        };
        await control("open"); await wait(()=>own().phase==="open");
        await send(phone,"participant-input","submit",{phase_version:own().phase_version,
          answer_version:0,choices:answers[0].choices,rationale:"Personal identifying explanation"});
        await wait(()=>controls().counts.correct===1);
        assert(!own().own.feedback,"Feedback released before reveal");
        assert(!projected().teaching && !projected().demonstration,"Private view before sharing");
        await control("close");
        const row=controls().participants[0];
        await control("select-answer",{actor:row.actor,answer_version:row.version});
        assert(controls().selected.rationale==="Personal identifying explanation","Private inspection");
        await control("share-answer",{actor:row.actor,answer_version:row.version,include_rationale:false});
        await wait(()=>projected().demonstration);
        assert(!JSON.stringify(projected()).includes("Personal identifying"),"Shared rationale without consent");
        assert(!JSON.stringify(projected()).includes(row.actor),"Shared actor identity");
        await control("reveal");
        await wait(()=>own().own.feedback?.correct);
        assert(own().teaching.worked.length===2,"Both alternatives released");
        const raw=JSON.stringify(projected());
        assert(!raw.includes('"expected":') && !raw.includes("duplicate-pair"),"Private fixture metadata");
        const before=projection(teacher,"presenter-controls").epoch;
        await send(teacher,"presenter-controls","_reset",{});
        await wait(()=>projection(teacher,"presenter-controls").epoch===before+1);
        await wait(()=>own().count===0 && own().phase==="introduce");
        return {open_submit_evaluate:true,private_until_reveal:true,anonymous_sharing:true,
          two_worked_alternatives:true,epoch_reset:true,method:"protocol clients; no editor UI"};
      } finally {
        for (const client of clients) client.close();
      }
    }, {deck,answers:seed.solutions.map(row=>row.answer)});
    assert.deepEqual(errors, []);
    const result = {browser:family,version:browser.version(),bundle:deck.bundle,
      static_slide_visible:true,transparent_overlays:2,private_role_leaks:0,page_errors:errors,protocol};
    fs.writeFileSync(path.join(output, "result.json"),JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify(result));
  } finally {
    await browser?.close();
    server.kill();
    log.end();
  }
})().catch(error => { console.error(error); process.exitCode=1; });

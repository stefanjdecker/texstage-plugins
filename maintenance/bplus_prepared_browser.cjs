// SPDX-License-Identifier: Apache-2.0
// Real installed host: static fallback, initially hidden overlays and private transport.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn} = require("node:child_process");
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const bundle = path.resolve(process.argv[2]), family = process.env.BROWSER || "chromium";
const output = path.resolve(process.argv[3] || "artifacts/bplus-prepared-browser", family);
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, "profile-"));
const deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
let server,log;
async function freePort() {
  const socket=require("node:net").createServer();
  return new Promise((resolve,reject)=>{
    socket.once("error",reject);socket.listen(0,"127.0.0.1",()=>{
      const port=socket.address().port;socket.close(error=>error?reject(error):resolve(port));
    });
  });
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  let browser;
  const errors = [], states = [], overlays = new Set(), urls = [];
  try {
    const port=process.env.TEXSTAGE_TEST_PORT?Number(process.env.TEXSTAGE_TEST_PORT):await freePort();
    const base="http://127.0.0.1:"+port;
    server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),
      "--bundle",bundle,"--data",profile,"--port",String(port)],{windowsHide:true,stdio:["ignore","pipe","pipe"]});
    log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
    let ready = false;
    for (let i=0;i<150;i++) {
      if (server.exitCode !== null) throw new Error("Server exited: " + server.exitCode);
      try { if ((await fetch(base + "/api/status")).ok) { ready = true; break; } } catch {}
      await delay(100);
    }
    assert(ready, "server startup");
    const launch = {headless:true};
    if (family === "chromium" && process.env.TEXSTAGE_BROWSER_CHANNEL) launch.channel = process.env.TEXSTAGE_BROWSER_CHANNEL;
    browser = await playwright[family].launch(launch);
    const context = await browser.newContext({viewport:{width:1440,height:1000}});
    await context.addInitScript(() => localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
    const presenter = await context.newPage(), projector = await context.newPage();
    const screens = [[presenter,"presenter"],[projector,"projector"]];
    for (const [page,role] of screens) {
      page.on("pageerror", error => errors.push(error.message));
      page.on("response", response => {
        urls.push(response.url());
        if (response.url().endsWith("/web/lesson-overlay.mjs") && response.ok()) overlays.add(role);
      });
      page.on("websocket", socket => socket.on("framereceived", ({payload}) => {
        try { const m=JSON.parse(String(payload)); if (m.t==="state") states.push({role,state:m}); } catch {}
      }));
      await page.goto(base + (role==="presenter" ? "/stage" : "/stage/projector") + "?bundle=" + deck.bundle);
    }
    await presenter.locator("#next").click(); // introduction -> first exercise
    const visible = async page => {
      await page.locator(".texstage-plugin").first().waitFor({state:"attached"});
      await page.waitForFunction(() => {
        const canvas=document.querySelector("canvas.tq-slide");
        if (!canvas || canvas.width<100) return false;
        const data=canvas.getContext("2d").getImageData(0,0,canvas.width,canvas.height).data;
        let dark=0;
        for (let i=0;i<data.length;i+=4) if (data[i+3] && data[i]<100) dark++;
        return dark>1000;
      });
      assert.equal(await page.locator(".bp-overlay:visible").count(),0,"initial overlay covered the exercise");
      assert.equal(await page.getByText("Plugin view unavailable.",{exact:false}).count(),0);
    };
    for (const [page,role] of screens) {
      await visible(page);
      await page.screenshot({path:path.join(output,role+"-lookup.png"),fullPage:true});
    }
    // Real lifecycle: navigate away, then return to a newly mounted exercise.
    await presenter.locator("#prev").click();
    await presenter.locator(".texstage-plugin").first().waitFor({state:"detached"});
    await presenter.locator("#next").click();
    await visible(presenter);
    assert.equal(overlays.size,2);
    const protocol = await presenter.evaluate(async ({deck}) => {
      const {Client}=await import("/static/shared/client.js");
      const clients=[];
      const wait=async predicate=>{
        const until=performance.now()+15000;
        while (!predicate()) {
          if (performance.now()>until) throw new Error("read-only protocol timeout");
          await new Promise(r=>setTimeout(r,30));
        }
      };
      const connect=async login=>{
        const row={state:null};
        row.client=new Client({onState:state=>{row.state=state;}});
        clients.push(row.client);
        try { await row.client.login(login); }
        catch (error) { throw new Error("login " + login.t + "/" + (login.role || "participant") + ": " + JSON.stringify(error)); }
        await wait(()=>row.state);
        return row;
      };
      try {
        const teacher=await connect({t:"hello",role:"stage",key:"plugin-demo-key",deck:deck.deck,bundle:deck.bundle});
        const pin=document.querySelector("#pin").textContent.replace(/\D/g,"");
        const phone=await connect({t:"join",pin,nickname:"Bplus learner"});
        const display=await connect({t:"hello",role:"display",key:"plugin-demo-key",deck:deck.deck,bundle:deck.bundle});
        await wait(()=>teacher.state.plugins?.items?.length && display.state.plugins?.items?.length);
        const clean=state=>{
          const raw=JSON.stringify(state.plugins || {});
          for (const field of ['"private":','"worked":','"analysis":','"explanation":','"evaluations":','"exercise_digest":'])
            if (raw.includes(field)) throw new Error("private transport: "+field);
          for (const item of state.plugins?.items || []) {
            for (const view of Object.values(item.views || {}))
              if (view.data.format!==1 || view.data.phase!=="introduce" || view.data.count!==0 || view.data.own || view.data.worked)
                throw new Error("unexpected initial classroom projection");
          }
          return true;
        };
        [teacher,phone,display].forEach(row=>clean(row.state));
        for (const item of phone.state.plugins?.items || [])
          if (!item.views["participant-input"] || !item.modules["participant-input"])
            throw new Error("missing classroom participant protocol");
        return {presenter:true,projector:true,participant:true,private_fields_absent:true,
          participant_protocol_declared:true, visual_controls_implemented:true};
      } finally {for (const client of clients) client.close();}
    },{deck});
    assert(states.length>0);
    for (const {state} of states) for (const item of state.plugins?.items || []) {
      const raw=JSON.stringify(item);
      for (const field of ['"private":','"worked":','"analysis":','"explanation":','"evaluations":'])
        assert(!raw.includes(field),"private transport field: "+field);
    }
    assert(!urls.some(url=>/solutions\.tex|activities\/.*\.json|keys\.json/.test(url)),"private file requested");
    assert.deepEqual(errors,[]);
    const report={browser:family,version:browser.version(),bundle:deck.bundle,
      static_slide_visible:true,initial_overlays_hidden:2,navigation_remount:true,
      private_role_leaks:0,page_errors:errors,protocol};
    fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report));
  } finally {
    await browser?.close();
    if(server&&server.exitCode===null){const exited=new Promise(resolve=>server.once("exit",resolve));server.kill();await exited;}
    log?.end();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});

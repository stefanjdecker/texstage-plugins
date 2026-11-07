// SPDX-License-Identifier: Apache-2.0
// Prepared exercise preservation and role privacy on the actual installed host.
// Full interaction is covered separately by query_plan_ui_browser.cjs.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn} = require("node:child_process"), playwright = require("playwright");
const root = path.resolve(__dirname, ".."), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || "chromium";
const output = path.resolve(process.argv[3] || path.join(root, "artifacts/query-plan-authoring", family));
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, "profile-")), deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
let base,server,log;
async function freePort(){
  const net=require("node:net"),socket=net.createServer();
  return new Promise((resolve,reject)=>{socket.once("error",reject);socket.listen(0,"127.0.0.1",()=>{
    const port=socket.address().port;socket.close(error=>error?reject(error):resolve(port));
  });});
}
async function until(fn, label) {
  for (let i=0;i<100;i++) { if (await fn()) return; await new Promise(r=>setTimeout(r,100)); }
  throw new Error("Timed out: " + label);
}
(async()=>{
  let browser;
  const errors=[], sockets={presenter:[],projector:[],phone:[]}, pages=[];
  try {
    const port=Number(process.env.TEXSTAGE_TEST_PORT)||await freePort();
    base="http://127.0.0.1:"+port;
server = spawn(process.env.PYTHON || "python", [path.join(__dirname, "serve_lesson.py"),
  "--bundle", bundle, "--data", profile, "--port", String(port)], {windowsHide:true});
log = fs.createWriteStream(path.join(output, "server.log"));
server.stdout.pipe(log); server.stderr.pipe(log);
    await until(()=>{if(server.exitCode!==null)throw Error("Test server exited before readiness");
      return fetch(base+"/").then(r=>r.ok).catch(()=>false);},"server startup");
    browser = await playwright[family].launch({headless:true,
      ...(process.env.TEXSTAGE_BROWSER_CHANNEL ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL} : {})});
    const desktop = await browser.newContext({viewport:{width:1440,height:1000}});
    await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
    function watch(page,role) {
      pages.push(page);
      page.on("pageerror",e=>errors.push(e.message));
      page.on("websocket",ws=>ws.on("framereceived",({payload})=>{
        try { const m=JSON.parse(String(payload)); if(m.t==="state") sockets[role].push(m); } catch {}
      }));
    }
    const presenter=await desktop.newPage(); watch(presenter,"presenter");
    await presenter.goto(base+"/stage?bundle="+deck.bundle);
    await presenter.locator("#next").click();
    await presenter.locator("#next").click();
    await presenter.locator(".presenter-overlay").waitFor();
    const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
    const projector=await desktop.newPage(); watch(projector,"projector");
    await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
    await projector.locator(".projector-overlay").waitFor();
    const mobile=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
    const phone=await mobile.newPage(); watch(phone,"phone");
    await phone.goto(base+"/play?pin="+pin);
    await phone.locator("#nick").fill("Reader");
    await phone.locator("#join button[type=submit]").click();
    const checkState = (role,item) => {
      const state=sockets[role].at(-1);
      return state?.plugins?.items?.some(d=>d.item===item);
    };
    for(const item of ["selective","broad","library","memory"]) {
      for(const role of ["presenter","projector","phone"]) await until(()=>checkState(role,item),role+" "+item);
      for(const role of ["presenter","projector","phone"]) {
        const descriptor=sockets[role].at(-1).plugins.items.find(d=>d.item===item);
        const serialized=JSON.stringify(descriptor);
        for(const forbidden of ['"private":','"reference":','"worked":','"evaluations":'])
          assert(!serialized.includes(forbidden),role+" leaked "+forbidden);
        if(role!=="presenter") assert(!serialized.includes('"solution":') && !serialized.includes('"explanation":'));
        assert.equal(Boolean(descriptor.modules["presenter-controls"]),role==="presenter");
        for(const v of Object.values(descriptor.views)) {
          assert.equal(v.data.phase,"introduce");
          assert.equal("solution" in v.data,role==="presenter");
        }
      }
      await phone.locator(".qp-participant").waitFor();
      const expected=sockets.phone.at(-1).plugins.items.find(d=>d.item===item).public.baseline;
      await until(async()=>{
        const selects=phone.locator("[data-qp-node]");
        if(await selects.count()!==expected.nodes.length)return false;
        for(const [i,node] of expected.nodes.entries())
          if(await selects.nth(i).inputValue()!==(node.method.startsWith("hash")?"hash":node.method))return false;
        return true;
      },"mounted baseline "+item);
      assert(await phone.getByRole("button",{name:"Submit plan",exact:true}).isDisabled());
      for(const [page,surface] of [[presenter,"presenter-overlay"],[projector,"projector-overlay"]]) {
        await page.locator("."+surface+" .qp-overlay").waitFor({state:"attached"});
        assert(await page.locator("."+surface+" .qp-overlay").isHidden());
        assert.equal(await page.locator("."+surface).evaluate(el=>getComputedStyle(el).pointerEvents),"none");
        assert(!await page.getByText("Plugin view unavailable.",{exact:false}).count());
      }
      if(item==="library") for(const [name,page] of [["presenter",presenter],["projector",projector],["phone",phone]])
        await page.screenshot({path:path.join(output,name+".png"),fullPage:true});
      await presenter.locator("#next").click();
    }
    await presenter.locator(".presenter-overlay").waitFor({state:"detached"});
    await projector.locator(".projector-overlay").waitFor({state:"detached"});
    assert.deepEqual(errors,[]);
    const report={browser:family,version:browser.version(),items:4,staticExercisePreserved:true,privacy:true,teardown:true,errors};
    fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report));
  } catch(error) {
    for(let i=0;i<pages.length;i++) await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
    throw error;
  } finally {await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
  if(server&&server.exitCode===null){const exited=new Promise(r=>server.once("exit",r));server.kill();await exited;}
  log?.end();
});

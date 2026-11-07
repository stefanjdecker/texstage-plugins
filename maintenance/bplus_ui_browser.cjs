// SPDX-License-Identifier: Apache-2.0
// Real clicks, keyboard/touch and authenticated host/evaluator from installed wheels.
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const {spawn}=require("node:child_process"),pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const lifecycle=require("./bplus_ui_lifecycle.cjs");
const root=path.resolve(__dirname,".."),bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||"chromium",language=process.env.BPLUS_LANGUAGE||"en";
const output=path.resolve(process.argv[3]||"artifacts/bplus-ui",family+"-"+language);fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json"))),profile=fs.mkdtempSync(path.join(output,"profile-"));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<240;i++){if(await fn())return;await delay(100);}throw Error("Timeout: "+label);}
async function port(){const s=require("node:net").createServer();return new Promise((resolve,reject)=>{s.once("error",reject);s.listen(0,"127.0.0.1",()=>{const p=s.address().port;s.close(e=>e?reject(e):resolve(p));});});}
function instrumentation(){
 const Native=window.WebSocket;window.bplusUIState=null;
 window.WebSocket=class extends Native{constructor(...args){super(...args);this.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.t==="state")window.bplusUIState=m;});}};
}
let item="lookup";
async function descriptor(page){return page.evaluate(item=>window.bplusUIState?.plugins?.items?.find(d=>d.item===item),item);}
async function data(page){const d=await descriptor(page);return d&&(d.views["presenter-controls"]||Object.values(d.views)[0])?.data;}
const action=(page,name)=>page.locator('[data-bp="'+name+'"]');
const input=(page,name)=>page.locator('[data-bp-field="'+name+'"]');
async function activate(page,name,{keyboard=false,touch=false}={}){
 const b=action(page,name);await b.waitFor({state:"visible"});
 if(keyboard){await b.focus();await b.press("Space");}else if(touch)await b.tap();else await b.click();
}
async function fillAnswer(page,answer){
 for(let n=0;await action(page,"remove-path").isEnabled();n++){assert(n<4,"remove descent did not update the draft");await activate(page,"remove-path");}
 for(const id of answer.path){await action(page,"focus").selectOption(String(id));await activate(page,"add-path");}
 if("keys" in answer)await input(page,"keys").fill(answer.keys.join(", "));
 if(answer.leaves){
  for(let n=0;await action(page,"remove-leaf").isEnabled();n++){assert(n<21,"remove scan did not update the draft");await activate(page,"remove-leaf");}
  for(const id of answer.leaves){await action(page,"focus").selectOption(String(id));await activate(page,"add-leaf");}
 }
 if(answer.repairs){
  for(let n=0;await action(page,"remove-repair").count();n++){assert(n<4,"remove repair did not update the draft");await action(page,"remove-repair").first().click();}
  for(const [i,r]of answer.repairs.entries()){
   await activate(page,"add-repair");await input(page,"repair-"+i+"-op").selectOption(r.op);
   for(const k of Object.keys(r).filter(k=>k!=="op"))await input(page,"repair-"+i+"-"+k).fill(String(r[k]));
  }
  for(let n=0;await action(page,"remove-separator").count();n++){assert(n<11,"remove separator did not update the draft");await action(page,"remove-separator").first().click();}
  for(const [i,r]of answer.separators.entries()){
   await activate(page,"add-separator");await input(page,"separator-"+i+"-node").fill(String(r.node));await input(page,"separator-"+i+"-keys").fill(r.keys.join(", "));
  }
  await input(page,"height").selectOption(String(answer.height));
 }
}
async function waitSaved(page,version){await until(async()=>{const own=(await data(page))?.own;return own?.version===version&&own.status==="saved";},"saved answer v"+version);}
async function panel(page){
 const summary=page.locator(".bp-controls>details>summary");await summary.waitFor();
 if(!await page.locator(".bp-controls>details").evaluate(n=>n.open))await summary.click();
}
async function geometry(page){
 const result=await page.evaluate(()=>{
  const root=document.querySelector(".bp-participant");
  const buttons=[...root.querySelectorAll("button")].filter(n=>n.getClientRects().length);
  return {viewport:innerWidth,width:document.documentElement.scrollWidth,
   minimumTouch:Math.min(...buttons.map(b=>b.getBoundingClientRect().height)),
   unlabeled:[...root.querySelectorAll("input,select")].filter(n=>!n.labels?.length&&!n.getAttribute("aria-label")).length};
 });
 assert(result.width<=result.viewport+1,JSON.stringify(result));assert(result.minimumTouch>=43,JSON.stringify(result));assert.equal(result.unlabeled,0);
 return result;
}
let server,log;
(async()=>{
 let browser;const pages=[],errors=[],timings=[],modules={};
 try{
  const base="http://127.0.0.1:"+await port();
  server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",new URL(base).port],{windowsHide:true});
  log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
  await until(()=>{if(server.exitCode!==null)throw Error("Server exited");return fetch(base+"/api/status").then(r=>r.ok).catch(()=>false);},"server");
  browser=await pw[family].launch({headless:true,...(family==="chromium"&&process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  async function context(options={}){const c=await browser.newContext(options);await c.addInitScript(instrumentation);return c;}
  function watch(p){pages.push(p);p.on("pageerror",e=>errors.push(e.message));
   p.on("response",r=>{for(const [name,file]of Object.entries({participant:"participant.mjs",controls:"presenter-controls.mjs",overlay:"lesson-overlay.mjs"}))
    if(r.url().endsWith("/texstage_bplus_lab/web/"+file))modules[name]=r.url();});return p;}
  const desktop=await context({viewport:{width:1440,height:1000},reducedMotion:"reduce"});
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const presenter=watch(await desktop.newPage());await presenter.goto(base+"/stage?bundle="+deck.bundle);
  await presenter.locator("#next").click();await until(async()=>!!await data(presenter),"lookup");
  const projector=watch(await desktop.newPage());await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const mobile=await context({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox",locale:language,reducedMotion:"reduce"});
  const phone=watch(await mobile.newPage());await phone.goto(base+"/play?pin="+pin);
  await phone.locator("#nick").fill("Alice");await phone.locator("#join button[type=submit]").click();
  await phone.locator(".bp-participant").waitFor();
  assert.equal(await phone.locator(".bp-participant").getAttribute("lang"),language);
  const same=await context({storageState:await mobile.storageState(),viewport:{width:390,height:844},locale:language});
  const second=watch(await same.newPage());await second.goto(base+"/play?pin="+pin);await second.locator(".bp-participant").waitFor();
  const other=await context({viewport:{width:390,height:844},locale:language});
  const bob=watch(await other.newPage());await bob.goto(base+"/play?pin="+pin);
  await bob.locator("#nick").fill("Bob");await bob.locator("#join button[type=submit]").click();await bob.locator(".bp-participant").waitFor();
  for(const name of ["lookup","range","insert","delete","cascade","shrink"]){
   console.log("UI "+family+"/"+language+": "+name);
   if(name!==item){await presenter.locator("#next").click();item=name;}
   await until(async()=>!!await data(phone)&&!!await data(presenter)&&!!await data(bob),"item "+name);
   await phone.locator(".bp-participant").waitFor();await panel(presenter);
   const source=JSON.parse(fs.readFileSync(path.join(root,"examples/bplus/activities",name+".json")));
   const answer=source.worked.answer,wrong=structuredClone(answer);
   if("height" in wrong)wrong.height=(wrong.height+1)%4;else wrong.keys=[];
   await activate(presenter,"open",{keyboard:true});
   await until(async()=>(await data(phone))?.phase==="open","open "+name);
   const slide=(await presenter.evaluate(()=>window.bplusUIState.slide));
   await fillAnswer(phone,answer);console.log("Filled "+name);
   const last=input(phone,"keys" in answer?"keys":"separator-"+Math.max(0,answer.separators.length-1)+"-keys");
   if(await last.count()){
    await last.focus();const value=await last.inputValue();
    await last.evaluate(n=>n.setSelectionRange(0,Math.min(1,n.value.length)));
    await fillAnswer(bob,wrong);await activate(bob,"submit");await waitSaved(bob,1);
    assert.equal(await last.inputValue(),value);assert(await last.evaluate(n=>document.activeElement===n),"focus lost on peer update");
    assert.deepEqual(await last.evaluate(n=>[n.selectionStart,n.selectionEnd]),[0,Math.min(1,value.length)]);
   }else{await fillAnswer(bob,wrong);await activate(bob,"submit");await waitSaved(bob,1);}
   assert(!(await data(phone)).own,"draft was submitted without Save");
   await activate(phone,"preview",{touch:true});console.log("Preview "+name);
   await until(async()=>await phone.locator('[data-bp="preview-frame"]').isVisible(),"preview "+name);
   const before=await data(phone);assert(!before.own);
   if(name==="insert"){
    await geometry(phone);
    await phone.screenshot({path:path.join(output,"phone-insert.png"),fullPage:true});
    fs.writeFileSync(path.join(output,"phone-insert-aria.yml"),await phone.locator(".bp-participant").ariaSnapshot());
   }
   if(name==="lookup"){
    const original=await input(phone,"keys").inputValue();
    await input(phone,"keys").fill("-9999");await activate(phone,"undo");assert.equal(await input(phone,"keys").inputValue(),original);
    await activate(phone,"redo");assert.equal(await input(phone,"keys").inputValue(),"-9999");await activate(phone,"undo");
    await fillAnswer(second,wrong);
   }
   const start=performance.now();await activate(phone,"submit",{touch:true});await waitSaved(phone,1);
   timings.push({operation:name,saveToFeedbackStateMs:Math.round(performance.now()-start)});
   assert.deepEqual((await data(phone)).own.answer,answer);assert(!(await data(phone)).own.feedback);
   if(name==="lookup"){
    await action(second,"conflict").waitFor({state:"visible"});await activate(second,"reload");
    assert.equal(await input(second,"keys").inputValue(),answer.keys.join(", "));
    await input(phone,"keys").fill("-9999");await activate(second,"submit");await waitSaved(second,2);
    await action(phone,"conflict").waitFor({state:"visible"});assert.equal(await input(phone,"keys").inputValue(),"-9999");
    await activate(phone,"keep");await activate(phone,"submit");await waitSaved(phone,3);
    await fillAnswer(phone,answer);console.log("Filled "+name);await activate(phone,"submit");await waitSaved(phone,4);
   }
   assert.equal((await presenter.evaluate(()=>window.bplusUIState.slide)),slide,"keyboard advanced the slide");
   const roster=(await data(presenter)).participants;
   for(const row of roster){
    await action(presenter,"roster").selectOption(row.actor);await activate(presenter,"inspect");
    await until(async()=>(await data(presenter))?.selected?.actor===row.actor,"private inspection");
    if((await data(presenter)).selected.feedback?.correct===false)break;
   }
   assert.equal((await data(presenter)).selected.feedback.correct,false);
   const partial=name==="lookup"?400:name==="range"?700:900;
   assert.equal((await data(presenter)).selected.feedback.grade.credit,partial);
   for(const student of [phone,bob,second]){
    assert.equal((await data(student)).scoring.awarded,null);
    assert.equal((await student.evaluate(()=>window.bplusUIState.me.score)),0);
    assert.equal(await student.locator('[data-bp="grade"] table').count(),0);
   }
   assert.equal(await presenter.locator('[data-bp="inspection"] [data-bp="grade"] table').count(),1);
   assert(await action(presenter,"share").isDisabled());assert.equal(await projector.locator(".bp-overlay:visible").count(),0);
   await activate(presenter,"close");await until(async()=>(await data(presenter)).phase==="closed","closed");
   await activate(presenter,"share");await projector.locator(".bp-overlay:visible").waitFor();
   const shared=await data(projector);assert.deepEqual(shared.demonstration,{answer:wrong});
   const serialized=JSON.stringify(await descriptor(projector));
   for(const hidden of ['"selected":','"participants":','"feedback":','"worked":','"correlation":'])assert(!serialized.includes(hidden),hidden);
   await activate(presenter,"replay-next");await until(async()=>(await data(projector))?.replay?.step===0,"shared replay");
   await activate(presenter,"replay-next");await until(async()=>(await data(projector))?.replay?.step===1,"next replay");
   if(name==="insert"){
    await presenter.screenshot({path:path.join(output,"presenter-private.png"),fullPage:true});
    await projector.screenshot({path:path.join(output,"projector-shared.png"),fullPage:true});
   }
   await activate(presenter,"clear-share");await until(async()=>await projector.locator(".bp-overlay:visible").count()===0,"clear shared overlay");
   await activate(presenter,"reveal");await until(async()=>(await data(phone))?.own?.feedback?.correct===true,"released correct feedback");
   await projector.locator(".bp-overlay:visible").waitFor();
   await until(async()=>(await data(bob))?.scoring?.awarded===partial,"published partial credit");
   await until(async()=>(await phone.evaluate(()=>window.bplusUIState.me.score))===1000&&
     (await bob.evaluate(()=>window.bplusUIState.me.score))===partial,"scoreboard totals");
   assert.equal((await phone.evaluate(()=>window.bplusUIState.me.rank)),1);
   assert.equal((await bob.evaluate(()=>window.bplusUIState.me.rank)),2);
   assert.equal((await data(phone)).own.feedback.grade.credit,1000);
   assert.equal((await data(phone)).scoring.awarded,1000);
   assert((await action(bob,"awarded").innerText()).includes(partial+" / 1000"));
   assert.equal(await bob.locator('[data-bp="grade"] table').count(),1);
   const session=await presenter.evaluate(()=>window.bplusUIState.session.id);
   const response=await fetch(base+"/api/results/"+session+".csv",{headers:{"X-Texquiz-Key":"plugin-demo-key"}});
   assert.equal(response.status,200);
   // This fixture uses controlled ASCII nicknames and item IDs without CSV quoting.
   const csv=(await response.text()).replace(/^\uFEFF/,"").trim().split(/\r?\n/).map(row=>row.split(","));
   const creditColumn=csv[0].indexOf(name+" activity credit"),pointsColumn=csv[0].indexOf(name+" activity points");
   assert(creditColumn>=0&&pointsColumn>=0);
   assert.equal(Number(csv.find(row=>row[1]==="Alice")[pointsColumn]),1000);
   assert.equal(Number(csv.find(row=>row[1]==="Bob")[pointsColumn]),partial);
   assert.equal(Number(csv.find(row=>row[1]==="Bob")[creditColumn]),partial/1000);
   if(name==="insert"){
    await bob.screenshot({path:path.join(output,"phone-partial-credit.png"),fullPage:true});
    await action(bob,"score").screenshot({path:path.join(output,"partial-credit-panel.png")});
    await phone.screenshot({path:path.join(output,"phone-feedback.png"),fullPage:true});
    await projector.screenshot({path:path.join(output,"projector-worked.png"),fullPage:true});
   }
   await activate(presenter,"reset");await activate(presenter,"confirm-reset");
   await until(async()=>(await data(phone))?.phase==="introduce"&&!(await data(phone))?.own,"reset "+name);
   await until(async()=>(await phone.evaluate(()=>window.bplusUIState.me.score))===0&&
     (await bob.evaluate(()=>window.bplusUIState.me.score))===0,"reset withdraws scoreboard points");
   assert.equal(await phone.locator('[data-bp="grade"] table').count(),0);
  }
  // Keep an unsaved draft explicitly across an epoch change; never submit on reset.
  await input(phone,"height").selectOption("2");
  await activate(presenter,"reset");await activate(presenter,"confirm-reset");
  await action(phone,"conflict").waitFor({state:"visible"});
  assert.equal(await input(phone,"height").inputValue(),"2");assert.equal((await data(phone)).own,undefined);
  await activate(phone,"keep");assert.equal((await data(phone)).own,undefined);
  // Reflow and accessibility structure at 200% equivalent viewport width.
  const layout=await geometry(phone);await phone.setViewportSize({width:320,height:420});await geometry(phone);
  await phone.screenshot({path:path.join(output,"phone-reflow.png"),fullPage:true});
  assert.equal(await phone.locator(".bp-participant [role=alert]").innerText(),"");
  await activate(presenter,"dismiss-controls");await presenter.locator("#prev").click();
  await until(async()=>!(await descriptor(phone)),"navigation disposes");
  await presenter.locator("#next").click();await until(async()=>!!await descriptor(phone),"return remount");
  assert.equal(await phone.locator(".bp-participant").count(),1);
  const sources=Object.fromEntries(["lookup","insert","large"].map(name=>[name,JSON.parse(fs.readFileSync(path.join(root,"examples/bplus/activities",name+".json")))]));
  const lifecycleReport=await lifecycle(phone,modules,sources);
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),language,operations:timings.map(t=>t.operation),actualUI:true,
   touch:true,keyboard:true,undoRedo:true,preview:true,draftFocus:true,sameActorConflict:true,resetConflict:true,
   fixedScoring:true,partialCredit:true,privateBeforeReveal:true,scoreboardTotalsAndRanks:true,resultsCSV:true,resetWithdrawsPoints:true,
   privateInspection:true,predictionOnlySharing:true,replay:true,reveal:true,navigation:true,layout,
   reducedMotion:true,ariaSnapshot:true,physicalPhone:false,lifecycle:lifecycleReport,timings,pageErrors:errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(error){
  for(let i=0;i<pages.length;i++){
   fs.writeFileSync(path.join(output,"failure-"+i+".json"),JSON.stringify(await pages[i].evaluate(()=>window.bplusUIState).catch(()=>null),null,2));
   await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
  }throw error;
 }finally{await browser?.close();}
})().catch(e=>{console.error(e.stack||e);process.exitCode=1;}).finally(async()=>{
 if(server&&server.exitCode===null){const exited=new Promise(r=>server.once("exit",r));server.kill();await exited;}log?.end();
});

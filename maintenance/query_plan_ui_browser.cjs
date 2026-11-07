// SPDX-License-Identifier: Apache-2.0
// Q4 real controls on the installed host and evaluator.
// Socket instrumentation observes privacy and state; classroom actions use controls.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn}=require("node:child_process"),pw=require("playwright");
const root=path.resolve(__dirname,".."),bundle=path.resolve(process.argv[2]);
const family=process.env.BROWSER||"chromium",output=path.resolve(process.argv[3]||"artifacts/query-plan-ui/"+family);
fs.mkdirSync(output,{recursive:true});
let base,server,log;
async function freePort(){
  const net=require("node:net"),socket=net.createServer();
  return new Promise((resolve,reject)=>{socket.once("error",reject);socket.listen(0,"127.0.0.1",()=>{
    const port=socket.address().port;socket.close(error=>error?reject(error):resolve(port));
  });});
}
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const profile=fs.mkdtempSync(path.join(output,"profile-"));

const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let n=0;n<160;n++){if(await fn())return;await delay(100);}throw Error("Timed out: "+label);}
function instrumentation(){
  const Native=window.WebSocket;
  window.qpState=null;
  window.WebSocket=class extends Native {
    constructor(...args){super(...args);
      this.addEventListener("message",event=>{const m=JSON.parse(event.data);if(m.t==="state")window.qpState=m;});
    }
  };

}
async function descriptor(page,item="selective"){
  return page.evaluate(item=>window.qpState?.plugins?.items?.find(d=>d.item===item),item);
}
async function data(page,item="selective"){const d=await descriptor(page,item);return d&&Object.values(d.views)[0]?.data;}
(async()=>{
 let browser;const pages=[],errors=[];
 try{
  const port=Number(process.env.TEXSTAGE_TEST_PORT)||await freePort();
  base="http://127.0.0.1:"+port;
  server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",String(port)],{windowsHide:true});
  log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
  await until(()=>{if(server.exitCode!==null)throw Error("Test server exited before readiness");
    return fetch(base+"/").then(r=>r.ok).catch(()=>false);},"server");
  browser=await pw[family].launch({headless:true,...(process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  async function context(options={}){const c=await browser.newContext(options);await c.addInitScript(instrumentation);return c;}
  function watch(page){pages.push(page);page.on("pageerror",e=>errors.push(e.message));return page;}
  const desktop=await context({viewport:{width:1440,height:1000}});
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const presenter=watch(await desktop.newPage());
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  await presenter.locator("#next").click();await presenter.locator("#next").click();
  await until(async()=>!!await data(presenter),"selective");
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const projector=watch(await desktop.newPage());
  await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  await until(async()=>!!await data(projector),"projector");
  const mobile=await context({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const phone=watch(await mobile.newPage());
  await phone.goto(base+"/play?pin="+pin);
  await phone.locator("#nick").fill("Alice");await phone.locator("#join button[type=submit]").click();
  await until(async()=>!!await data(phone),"joined Alice");
  const same=await context({storageState:await mobile.storageState(),viewport:{width:390,height:844}});
  const second=watch(await same.newPage());await second.goto(base+"/play?pin="+pin);
  await until(async()=>!!await data(second),"same actor device");
  const other=await context({viewport:{width:390,height:844}});
  const bob=watch(await other.newPage());await bob.goto(base+"/play?pin="+pin);
  await bob.locator("#nick").fill("Bob");await bob.locator("#join button[type=submit]").click();
  await until(async()=>!!await data(bob),"joined Bob");
  const controls=presenter.locator(".qp-controls");
  await controls.locator("summary").first().click();
  const clickControl=name=>controls.getByRole("button",{name,exact:true}).click();
  const input=phone.locator(".qp-participant");
  const submit=page=>page.locator(".qp-participant").getByRole("button",{name:"Submit plan",exact:true}).click();
  const preview=page=>page.locator(".qp-participant").getByRole("button",{name:"Estimate my plan",exact:true}).click();
  const method=(page,i)=>page.locator('[data-qp-node="'+i+'"]');
  function tree(answer,i=answer.nodes.length-1){const n=answer.nodes[i];return n.op==="scan"?n.relation:"("+tree(answer,n.left)+" ⋈ "+tree(answer,n.right)+")";}
  async function choose(page,answer){
   const order=page.locator('[data-qp="order"]');
   if(await order.isVisible())await order.selectOption({label:tree(answer)});
   for(const [i,n]of answer.nodes.entries()){
    await method(page,i).selectOption(n.method.startsWith("hash")?"hash":n.method);
    if(n.method.startsWith("hash"))await page.locator('[data-qp-build="'+i+'"]').selectOption(n.method);
   }
  }
  async function settled(page,item="selective",version=1){
   await until(async()=>{const d=await data(page,item);return d?.own?.version===version&&d.own.status==="saved";},"saved answer "+item);
  }
  await clickControl("Open answers");
  await until(()=>input.getByRole("button",{name:"Submit plan",exact:true}).isEnabled(),"enabled input");
  await method(phone,0).selectOption("index");
  await preview(phone);assert((await input.innerText()).includes("5,210"));
  // A local estimate must not submit or disclose a private reference.
  assert(!(await data(phone)).own);
  await input.getByRole("button",{name:"Submit plan",exact:true}).tap();await settled(phone);
  // Edit locally, then receive an unrelated participant update with focus intact.
  await method(phone,0).selectOption("seq");await method(phone,0).focus();
  await submit(bob);await settled(bob);
  assert.equal(await method(phone,0).inputValue(),"seq");
  assert(await method(phone,0).evaluate(n=>n===document.activeElement));
  assert(!(await data(phone)).own.feedback);
  assert.equal(await phone.evaluate(()=>window.qpState.me.score),0,"points stay private before reveal");
  assert.equal((await data(phone)).own.points,undefined);
  // A second device saving the same actor forces an explicit decision.
  await until(async()=>(await data(second))?.own?.version===1,"second device synchronized");
  await submit(second);await settled(second,"selective",2);
  await input.getByRole("button",{name:"Keep my draft",exact:true}).waitFor();
  assert(await input.getByRole("button",{name:"Submit plan",exact:true}).isDisabled());
  await input.getByRole("button",{name:"Keep my draft",exact:true}).click();
  assert.equal(await method(phone,0).inputValue(),"seq");
  await input.getByRole("button",{name:"Undo edit",exact:true}).click();assert.equal(await method(phone,0).inputValue(),"index");
  await preview(phone);
  // Keyboard submission and presenter selection use the actual visible controls.
  await input.getByRole("button",{name:"Submit plan",exact:true}).focus();await phone.keyboard.press("Enter");await settled(phone,"selective",3);
  const actor=(await data(presenter)).participants[0].actor;
  await controls.locator('[data-qp="roster"]').selectOption(actor);
  await clickControl("Inspect privately");
  await until(()=>controls.locator(".qp-private").isVisible(),"private inspection");
  assert(!(await data(projector)).demonstration);
  for(const page of [phone,bob,projector]){
   const d=await descriptor(page),text=JSON.stringify(d);
   for(const hidden of ['"private":','"reference":','"correlation":','"digest":','"evaluations":','"selected":','"participants":','"solution":'])
    assert(!text.includes(hidden),"unrevealed leak "+hidden);
  }
  await clickControl("Close answers");await clickControl("Share selected plan anonymously");
  await until(()=>projector.locator(".qp-overlay").isVisible(),"shared overlay");
  assert(!JSON.stringify(await data(projector)).includes(actor));
  await projector.screenshot({path:path.join(output,"projector-shared.png"),fullPage:true});
  await clickControl("Clear shared plan");await until(()=>projector.locator(".qp-overlay").isHidden(),"cleared overlay");
  await clickControl("Reveal solution");await until(async()=>!!(await data(phone))?.solution,"revealed solution");
  await input.getByText("Worked solution",{exact:true}).click();
  assert((await input.innerText()).includes("Goal met"));
  await until(async()=>Number.isInteger((await data(phone))?.own?.points),"released game points");
  const firstAward=(await data(phone)).own;
  assert.equal(firstAward.base_points,Math.round(1000*(1-Math.min(firstAward.answer_ms/120000,1)/2)));
  assert.equal(firstAward.bonus,0);assert.equal(firstAward.points,firstAward.base_points);
  assert.equal(await phone.evaluate(()=>window.qpState.me.score),firstAward.points);
  assert((await input.innerText()).includes("Streak bonus"));
  assert.equal(await bob.evaluate(()=>window.qpState.me.score),0,"missed target earns zero");
  assert((await input.innerText()).includes("1,000"));
  await phone.screenshot({path:path.join(output,"phone-index.png"),fullPage:true});
  await presenter.screenshot({path:path.join(output,"presenter-controls.png"),fullPage:true});
  await projector.screenshot({path:path.join(output,"projector-revealed.png"),fullPage:true});
  assert(await controls.getByRole("button",{name:"Open answers",exact:true}).isDisabled());
  await method(phone,0).selectOption("seq");
  await clickControl("Reset activity");await clickControl("Yes, reset activity");
  await input.getByRole("button",{name:"Load saved plan",exact:true}).waitFor();
  assert.equal(await method(phone,0).inputValue(),"seq");
  await input.getByRole("button",{name:"Load saved plan",exact:true}).click();
  assert.equal(await method(phone,0).inputValue(),"seq");assert(!(await data(phone)).own);
  await until(()=>phone.evaluate(()=>window.qpState.me.score===0),"reset withdraws activity award");
  assert.equal(await phone.evaluate(()=>window.qpState.me.streak),0);
  await controls.locator("summary").first().click();
  let cumulativePoints=0;
  // All prepared activities, including both join shapes and limited workspace.
  for(const item of ["broad","library","memory"]){
   await presenter.locator("#next").click();await until(async()=>!!await data(phone,item),item+" visible");
   await presenter.locator(".qp-controls summary").first().click();
   await presenter.locator(".qp-controls").getByRole("button",{name:"Open answers",exact:true}).click();
   const lesson=JSON.parse(fs.readFileSync(path.join(root,"examples/query-plan/activities/"+item+".json")));
   await until(()=>phone.getByRole("button",{name:"Submit plan",exact:true}).isEnabled(),"phone opened "+item);
   await choose(phone,lesson.worked_answer);await preview(phone);
   if(item==="memory"){
    const disabled=await phone.locator('[data-qp-build] option:disabled').count();assert(disabled>0);
    assert((await input.innerText()).includes("Hash workspace limit per join: 1,024"));
   }
   await submit(phone);await settled(phone,item);
   await until(async()=>(await data(presenter,item))?.counts["goal-met"]===1,"real evaluation "+item);
   assert((await phone.evaluate(()=>document.documentElement.scrollWidth))<=320,"320px page overflow");
   for(const select of await phone.locator(".qp-participant select:visible").all()){
    assert(await select.evaluate(n=>n.labels.length>0||!!n.getAttribute("aria-label")));
    assert((await select.boundingBox()).height>=44);
   }
   if(item==="library"){
    await phone.locator('[aria-label="Inspect node"]').first().selectOption("4");
    assert((await phone.evaluate(()=>document.documentElement.scrollWidth))<=320,"selected long node label overflow");
    await phone.screenshot({path:path.join(output,"phone-joins.png"),fullPage:true});
    // Enlarge text without changing the viewport; controls remain reachable.
    await phone.locator(".qp-participant").evaluate(n=>n.style.fontSize="32px");
    assert((await phone.evaluate(()=>document.documentElement.scrollWidth))<=320,"200% text overflow");
    assert.equal(await phone.locator('[data-qp-node="0"]').evaluate(n=>getComputedStyle(n).fontSize),"32px","select honors enlarged text");
    await phone.screenshot({path:path.join(output,"phone-zoom.png"),fullPage:true});
    await phone.locator(".qp-participant").evaluate(n=>n.style.fontSize="");
    await phone.setViewportSize({width:600,height:800});await preview(phone);await phone.setViewportSize({width:320,height:740});
   }
   await presenter.locator(".qp-controls").getByRole("button",{name:"Close answers",exact:true}).click();
   await presenter.locator(".qp-controls").getByRole("button",{name:"Reveal solution",exact:true}).click();
   await until(async()=>!!(await data(projector,item))?.solution,"reveal "+item);
   await until(async()=>Number.isInteger((await data(phone,item))?.own?.points),"activity game points "+item);
   const award=(await data(phone,item)).own,streak=["broad","library","memory"].indexOf(item)+1;
   assert.equal(award.streak,streak);assert.equal(award.bonus,100*(streak-1));
   assert.equal(award.base_points,Math.round(lesson.points*(1-Math.min(award.answer_ms/(lesson.time*1000),1)/2)));
   assert.equal(award.points,award.base_points+award.bonus);cumulativePoints+=award.points;
   await until(()=>phone.evaluate(expected=>window.qpState.me.score===expected,cumulativePoints),"cumulative game points "+item);
   assert.equal(await phone.evaluate(()=>window.qpState.me.streak),streak);
   if(item==="library"||item==="memory")await projector.screenshot({path:path.join(output,"projector-"+item+".png"),fullPage:true});
   await presenter.locator(".qp-controls summary").first().click();
  }
  // Focused lifecycle/race probes import the installed renderer from its actual
  // host URL. Fake dispatch only controls delivery order; it does not grade.
  const d=await descriptor(phone,"memory"),pd=await descriptor(presenter,"memory");
  const fixture=watch(await desktop.newPage());await fixture.goto(base+"/");
  const races=await fixture.evaluate(async({d,pd})=>{
   const participant=await import(d.modules["participant-input"]),presenterModule=await import(pd.modules["presenter-controls"]);
   const signal=new AbortController(),container=document.createElement("div");document.body.replaceChildren(container);
   let resolve,reject,calls=[];
   const ctx={container,item:{id:d.item,...d.public},language:"de",signal:signal.signal,dispatch:(op,payload)=>{calls.push({op,payload});return new Promise((a,b)=>{resolve=a;reject=b;});}};
   const m=participant.mount(ctx),base={epoch:1,revision:0,data:{phase:"open",phase_version:1,active:true,count:0}};
   m.update(base);
   const button=text=>[...container.querySelectorAll("button")].find(n=>n.textContent===text);
   const select=container.querySelector('[data-qp-node="0"]');
   const german=container.textContent.includes("Join-Reihenfolge")&&container.textContent.includes("Hash-Speicherlimit");
   button("Plan absenden").click();const sent=calls.at(-1).payload.answer;
   resolve({accepted:true,epoch:1,revision:1});await Promise.resolve();await Promise.resolve();
   if(!button("Plan absenden").disabled)throw Error("receipt enabled save before view");
   m.update({epoch:1,revision:1,data:{...base.data,count:1,own:{version:1,status:"pending",answer:sent}}});
   if(button("Plan absenden").disabled)throw Error("receipt view never unlocked");
   // A view may also precede the receipt. New edits must survive that saved snapshot.
   button("Plan absenden").click();const inFlight=calls.at(-1).payload.answer;
   select.value=select.value==="seq"?"index":"seq";select.dispatchEvent(new Event("change",{bubbles:true}));
   const laterEdit=select.value;
   m.update({epoch:1,revision:2,data:{...base.data,count:1,own:{version:2,status:"pending",answer:inFlight}}});
   resolve({accepted:true,epoch:1,revision:2});await Promise.resolve();await Promise.resolve();
   if(select.value!==laterEdit||!container.textContent.includes("Änderungen am Entwurf"))throw Error("ack overwrote in-flight edit");
   // Queue rejection preserves a draft; a later reset invalidates an in-flight callback.
   select.value=select.value==="seq"?"index":"seq";select.dispatchEvent(new Event("change",{bubbles:true}));
   const value=select.value;button("Plan absenden").click();reject(Object.assign(Error(),{code:"queue-full"}));await Promise.resolve();await Promise.resolve();
   if(select.value!==value||!container.textContent.includes("ausgelastet"))throw Error("rejected save lost draft/error");
   button("Plan absenden").click();m.update({epoch:2,revision:0,data:{...base.data,phase:"introduce"}});
   resolve({accepted:true,epoch:1,revision:2});await Promise.resolve();await Promise.resolve();
   if(!container.textContent.includes("Meinen Entwurf behalten")||select.value!==value)throw Error("reset lost draft");
   m.destroy();signal.abort();if(container.children.length)throw Error("participant leaked mount");
   const pcSignal=new AbortController();let pcResolve,pcCommand;
   const pc=presenterModule.mount({...ctx,language:"en",signal:pcSignal.signal,item:{id:pd.item,...pd.public},dispatch:(op,payload)=>{pcCommand={op,payload};return new Promise(r=>{pcResolve=r;});}});
   const data={...Object.values(pd.views)[0].data,phase:"introduce",control_version:0,count:0,participants:[]};delete data.selected;delete data.demonstration;
   pc.update({epoch:1,revision:0,data});button("Open answers").click();pcResolve({accepted:true,epoch:1,revision:1});await Promise.resolve();await Promise.resolve();
   if(!button("Close answers").disabled)throw Error("presenter receipt unlocked old control");
   pc.update({epoch:1,revision:1,data:{...data,phase:"open",control_version:1}});
   if(button("Close answers").disabled)throw Error("presenter new control stayed locked");
   pc.update({epoch:1,revision:2,data:{...data,phase:"open",control_version:1,count:26,page:0,pages:2}});
   if(!button("Previous answers").disabled||button("Next answers").disabled)throw Error("first page boundary");
   button("Next answers").click();
   if(pcCommand.op!=="roster-page"||pcCommand.payload.page!==1||pcCommand.payload.control!==1)throw Error("page command");
   pcResolve({accepted:true,epoch:1,revision:3});await Promise.resolve();await Promise.resolve();
   if(!button("Next answers").disabled)throw Error("page receipt unlocked stale view");
   pc.update({epoch:1,revision:3,data:{...data,phase:"open",control_version:2,count:26,page:1,pages:2}});
   if(button("Previous answers").disabled||!button("Next answers").disabled||!container.textContent.includes("Page 2 / 2"))throw Error("last page boundary");
   pc.destroy();pcSignal.abort();if(container.children.length)throw Error("presenter leaked mount");
   return {german,receiptBeforeView:true,viewBeforeReceipt:true,editDuringSave:true,queueFailure:true,resetInFlight:true,pagination:true,cleanup:true};
  },{d,pd});
  assert(races.german);
  await presenter.locator("#next").click();await presenter.locator(".presenter-controls").waitFor({state:"detached"});
  await projector.locator(".projector-overlay").waitFor({state:"detached"});
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),items:4,realWorker:true,actualControls:true,rolePrivacy:true,
   touch320:true,keyboard:true,zoom200:true,resize:true,draftFocus:true,sameActorConflict:true,undo:true,reset:true,
   points:{privateUntilReveal:true,quizSpeed:true,sharedStreak:true,firstAward:firstAward.points,missedTarget:0,
    resetWithdraws:true,cumulativeTotal:cumulativePoints,lastStreak:3},...races,errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));

 }catch(error){
  for(let i=0;i<pages.length;i++){
   fs.writeFileSync(path.join(output,"failure-"+i+".json"),JSON.stringify(await pages[i].evaluate(()=>window.qpState).catch(()=>null),null,2));
   await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
  }
  throw error;
 }finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
  if(server&&server.exitCode===null){const exited=new Promise(r=>server.once("exit",r));server.kill();await exited;}
  log?.end();
});

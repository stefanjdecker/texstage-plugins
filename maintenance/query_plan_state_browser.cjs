// SPDX-License-Identifier: Apache-2.0
// Q3 protocol on the actual host/evaluator. Calls use authenticated page sockets;
// there is intentionally no claim that these test commands are a finished UI.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn}=require("node:child_process"),pw=require("playwright");
const root=path.resolve(__dirname,".."),bundle=path.resolve(process.argv[2]);
const family=process.env.BROWSER||"chromium",output=path.resolve(process.argv[3]||"artifacts/query-plan-state/"+family);
fs.mkdirSync(output,{recursive:true});
let base,server,log;
async function freePort(){
  const net=require("node:net"),socket=net.createServer();
  return new Promise((resolve,reject)=>{socket.once("error",reject);socket.listen(0,"127.0.0.1",()=>{
    const port=socket.address().port;socket.close(error=>error?reject(error):resolve(port));
  });});
}
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const source=JSON.parse(fs.readFileSync(path.join(root,"examples/query-plan/activities/selective.json")));
const profile=fs.mkdtempSync(path.join(output,"profile-"));

const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let n=0;n<160;n++){if(await fn())return;await delay(100);}throw Error("Timed out: "+label);}
function instrumentation(){
  const Native=window.WebSocket;
  window.qpState=null;window.qpSequence=0;
  window.WebSocket=class extends Native {
    constructor(...args){super(...args);window.qpSocket=this;
      this.addEventListener("message",event=>{const m=JSON.parse(event.data);if(m.t==="state")window.qpState=m;});
    }
  };
  window.qpSend=message=>new Promise((resolve,reject)=>{
    const socket=window.qpSocket,id="q3-test-"+(++window.qpSequence);
    const onmessage=event=>{const m=JSON.parse(event.data);if(m.re===id){clearTimeout(timer);socket.removeEventListener("message",onmessage);resolve(m);}};
    const timer=setTimeout(()=>{socket.removeEventListener("message",onmessage);reject(Error("receipt timeout"));},10000);
    socket.addEventListener("message",onmessage);
    socket.send(JSON.stringify({...message,id}));
  });
}
async function descriptor(page,item="selective"){
  return page.evaluate(item=>window.qpState?.plugins?.items?.find(d=>d.item===item),item);
}
async function data(page,item="selective"){const d=await descriptor(page,item);return d&&Object.values(d.views)[0]?.data;}
async function envelope(page,operation,payload,request_id,item="selective"){
  const d=await descriptor(page,item),v=Object.values(d.views)[0];
  return {type:d.type,item,operation,payload,request_id,epoch:v.epoch,expected_revision:v.revision};
}
async function send(page,command){return page.evaluate(command=>window.qpSend({t:"plugin.command",command}),command);}
async function accepted(page,command){
  const r=await send(page,command);assert.equal(r.receipt?.accepted,true,JSON.stringify(r));
  // The receipt can precede the pushed view (notably in WebKit). A subsequent
  // control must use the authoritative new token, not the previous frame.
  await until(async()=>{
    const d=await descriptor(page,command.item),v=d&&Object.values(d.views)[0];
    return v&&v.epoch===r.receipt.epoch&&v.revision>=r.receipt.revision;
  },"committed command projection");
  return r.receipt;
}
let request=0;
async function control(page,op,payload={}){
  const d=await data(page);
  return accepted(page,await envelope(page,op,{control:d.control_version,...payload},"control"+String(++request).padStart(8,"0")));
}
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
  const oldControl=await envelope(presenter,"close",{control:0},"secondpresenter1");
  await control(presenter,"open");
  await until(async()=>(await data(phone))?.phase==="open","open phase");
  const submission=await envelope(phone,"submit-plan",{phase:1,version:0,answer:source.worked_answer},"answer000001");
  const first=await accepted(phone,submission);
  assert.deepEqual(await accepted(phone,submission),first);
  const stale=await send(second,{...submission,request_id:"seconddevice1"});
  assert.equal(stale.receipt.error,"stale-answer");
  const invalid={format:1,nodes:[{op:"scan",relation:"missing",method:"seq"}]};
  await accepted(bob,await envelope(bob,"submit-plan",{phase:1,version:0,answer:invalid},"bobanswer0001"));
  await until(async()=>{const d=await data(presenter);return d?.counts["goal-met"]===1&&d?.counts.invalid===1;},"real worker outcomes");
  assert(!(await data(phone)).own.feedback && !(await data(bob)).own.feedback);
  assert.deepEqual((await data(phone)).own.answer,source.worked_answer);
  assert.deepEqual((await data(bob)).own.answer,invalid);
  const staleTeacher=await send(presenter,oldControl);assert.equal(staleTeacher.receipt.error,"stale-control");
  const actor=(await data(presenter)).participants[0].actor;
  await control(presenter,"select-answer",{actor});
  assert((await data(presenter)).selected.feedback.correct);
  assert(!(await data(projector)).demonstration);
  await control(presenter,"close");
  await control(presenter,"share-selected");
  await until(async()=>!!(await data(projector))?.demonstration,"anonymous share");
  const projected=await data(projector);
  assert.deepEqual(projected.demonstration,source.worked_answer);
  assert(!JSON.stringify(projected).includes(actor) && !projected.solution && !projected.counts);
  for(const page of [phone,bob,projector]){
    const d=await descriptor(page),text=JSON.stringify(d);
    for(const hidden of ['"private":','"reference":','"correlation":','"digest":','"evaluations":','"selected":','"participants":','"solution":'])
      assert(!text.includes(hidden),"unrevealed leak "+hidden);
  }
  await control(presenter,"clear-shared");
  await control(presenter,"open");
  await until(async()=>(await data(phone))?.phase_version===3,"reopened");
  await accepted(phone,await envelope(phone,"submit-plan",{phase:3,version:1,answer:source.baseline},"replace00001"));
  await until(async()=>(await data(presenter))?.counts["target-missed"]===1,"target miss");
  assert(!(await data(presenter)).selected && !(await data(projector)).demonstration);
  await control(presenter,"close");await control(presenter,"reveal");
  await until(async()=>(await data(phone))?.own?.feedback?.code==="target-missed","released feedback");
  assert.equal((await data(bob)).own.feedback.code,"invalid");
  assert.equal((await data(projector)).solution.minimum,5210);
  assert(!(await data(projector)).participants && !(await data(projector)).own);
  const reopen=await send(presenter,await envelope(presenter,"open",{control:(await data(presenter)).control_version},"badreopen001"));
  assert.equal(reopen.receipt.error,"reset-required");
  const reset=await envelope(presenter,"_reset",{},"reset0000001");
  const resetReceipt=await accepted(presenter,reset);
  assert.equal(resetReceipt.epoch,2);
  assert.deepEqual(await accepted(presenter,reset),resetReceipt);
  const resetRace=await send(presenter,{...reset,request_id:"reset0000002"});
  assert.equal(resetRace.receipt.error,"stale-epoch");
  await until(async()=>(await data(phone))?.phase==="introduce"&&!(await data(phone))?.own,"reset projection");
  const denied=await send(phone,await envelope(phone,"open",{control:0},"forged000001"));
  assert.equal(denied.t,"error");
  await control(presenter,"open");
  await presenter.locator("#next").click();
  await until(async()=>!!await data(phone,"broad"),"next slide");
  await presenter.locator("#prev").click();
  await until(async()=>(await data(phone))?.phase==="closed","navigation closes");
  await phone.locator(".qp-participant").waitFor();
  await presenter.locator(".presenter-controls .qp-controls").waitFor();
  assert.equal(await presenter.locator(".presenter-controls").count(),1);
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),realWorker:true,rolePrivacy:true,sameActor:true,
    twoParticipants:true,receiptReplay:true,staleControls:true,explicitSharing:true,reveal:true,reset:true,navigation:true,
    ui:"protocol probe; actual controls covered by query_plan_ui_browser.cjs",errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  for(const [name,page]of[["presenter",presenter],["projector",projector],["phone",phone]])
    await page.screenshot({path:path.join(output,name+".png"),fullPage:true});
  console.log(JSON.stringify(report));
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

// SPDX-License-Identifier: Apache-2.0
// Authenticated synthetic students; actual presenter, isolated workers and CSP.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),os=require("node:os");
const {spawn}=require("node:child_process"),{randomBytes}=require("node:crypto");
const pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const bundle=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);
const actors=Number(process.env.BPLUS_ACTORS||600),family=process.env.BROWSER||"chromium";
assert(Number.isInteger(actors)&&actors>=2&&actors<=1000);
// 600 is the normal class target; 1000 is the slower peak-load ceiling.
const ackBudget=actors<=600?5000:10000,readyBudget=actors<=600?30000:60000;
fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const example=JSON.parse(fs.readFileSync(path.join(__dirname,"../examples/bplus/activities/insert.json")));
const correct=example.worked.answer,wrong={...correct,height:3},item="insert";
const delay=ms=>new Promise(r=>setTimeout(r,ms)),now=()=>performance.now();
const errors=[],rows=[],workerTimes=[],phases=[],students=[];
const browserEvents=[];
const scoring={maximum:1000,privateBeforeReveal:false,allPublished:false,resetWithdraws:false};
let base,server,browser,teacher,page,metrics,stopped=false,failure=null,browserFailure=null,report;
async function until(test,label,timeout=180000){
 const start=now();while(now()-start<timeout){if(browserFailure)throw Error(browserFailure+": "+label);if(await test())return;await delay(100);}throw Error("Timed out: "+label);
}
function summary(values){
 const a=values.filter(Number.isFinite).sort((a,b)=>a-b),q=p=>a.length?+a[Math.ceil(a.length*p)-1].toFixed(2):null;
 return {n:a.length,p50_ms:q(.5),p95_ms:q(.95),p99_ms:q(.99),max_ms:q(1)};
}
async function freePort(){
 const s=require("node:net").createServer();return new Promise((resolve,reject)=>{
  s.once("error",reject);s.listen(0,"127.0.0.1",()=>{const p=s.address().port;s.close(e=>e?reject(e):resolve(p));});
 });
}
class Student{
 constructor(index){this.index=index;this.counter=0;this.pending=new Map();this.target=null;this.bytes=0;this.messages=0;}
 descriptor(){return this.state?.plugins?.items?.find(d=>d.item===item);}
 view(){const d=this.descriptor();return d&&(d.views["participant-input"]||d.views["presenter-controls"]);}
 async connect(login){
  this.state=null;this.socket=new WebSocket(base.replace("http:","ws:")+"/ws");
  this.socket.addEventListener("message",event=>{
   this.bytes+=event.data.length;this.messages++;const m=JSON.parse(String(event.data));
   if(m.t==="state"){
    this.state=m;if(m.plugins?.error)errors.push(m.plugins.error);
    const d=this.descriptor(),v=d?.views["participant-input"]?.data;
    if(v&&v.phase!=="revealed"&&(v.own?.feedback||v.worked))errors.push("Premature feedback");
    if(v&&v.phase!=="revealed"&&(v.scoring?.awarded!=null||m.me?.score>0))errors.push("Premature score");
    if(v&&("participants" in v||"selected" in v||"binding" in v))errors.push("Private roster leaked");
    if(this.target&&v?.own?.version===this.target.version&&v.own.status==="saved"&&this.target.checked_ms===undefined){
     try{assert.deepEqual(v.own.answer,this.target.answer);}catch{errors.push("Latest answer mismatch");}
     this.target.checked_ms=now()-this.target.start;
    }
    if(v?.own?.status==="unavailable")errors.push("Evaluation unavailable");
   }
   if(m.t==="plugin.error")errors.push(m.message);
   const p=this.pending.get(m.re);if(p){this.pending.delete(m.re);clearTimeout(p.timer);
    m.t==="error"?p.reject(Error(m.error+": "+m.message)):p.resolve(m);}
  });
  await new Promise((resolve,reject)=>{this.socket.addEventListener("open",resolve,{once:true});this.socket.addEventListener("error",reject,{once:true});});
  this.welcome=await this.send(login);await until(()=>this.view(),"student initial state");
 }
 send(message){
  const id="load-"+this.index+"-"+(++this.counter);
  return new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>{this.pending.delete(id);reject(Error("ACK timeout "+id));},180000);
   this.pending.set(id,{resolve,reject,timer});this.socket.send(JSON.stringify({...message,id}));
  });
 }
 envelope(operation,payload){
  const d=this.descriptor(),v=this.view();
  return {type:d.type,item,operation,payload,epoch:v.epoch,expected_revision:v.revision,request_id:"load-"+randomBytes(12).toString("hex")};
 }
 command(operation,payload){return this.send({t:"plugin.command",command:this.envelope(operation,payload)});}
 async submit(answer,phase,version){
  const v=this.view().data;
  const row={phase,actor:this.index,version:version??(v.own?.version||0)+1,start:now()};
  Object.defineProperty(row,"answer",{value:answer});
  rows.push(row);this.target=row;
  const envelope=this.envelope("submit-answer",{phase_version:v.phase_version,answer_version:row.version-1,answer});
  Object.defineProperty(row,"envelope",{value:envelope});
  const result=await this.send({t:"plugin.command",command:envelope});
  row.ack_ms=now()-row.start;row.accepted=result.receipt?.accepted;row.jobs=Object.values(result.receipt?.jobs||{});
  Object.defineProperty(row,"receipt",{value:result.receipt});
  assert(row.accepted,JSON.stringify(result));return row;
 }
 close(){
  const socket=this.socket;if(!socket||socket.readyState===WebSocket.CLOSED)return Promise.resolve();
  return new Promise(resolve=>{
   const timer=setTimeout(()=>{errors.push("student close timeout");resolve();},5000);
   socket.addEventListener("close",()=>{clearTimeout(timer);resolve();},{once:true});socket.close();
  });
 }
}
(async()=>{
 try{
  const port=await freePort();base="http://127.0.0.1:"+port;metrics=path.join(output,"server-events.jsonl");
  server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"bplus_load_server.py"),"--bundle",bundle,
   "--data",fs.mkdtempSync(path.join(output,"profile-")),"--metrics",metrics,"--port",String(port)],{windowsHide:true,stdio:["pipe","pipe","pipe"]});
  const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
  await until(async()=>{if(server.exitCode!==null)throw Error("Server exited");try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server",30000);
  browser=await pw[family].launch({headless:true,...(family==="chromium"&&process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{
   localStorage.setItem("texquiz:presenter-key","synthetic-load-key");window.__loadWorker=[];
   window.__loadLive=new Set();window.__loadPulse=Date.now();
   setInterval(()=>{window.__loadPulse=Date.now();},1000);
   const Native=window.Worker;
   window.Worker=class extends Native{
    constructor(url,options){super(url,options);this.probe=String(url).includes("plugin-evaluator-worker.js");
     if(this.probe)window.__loadLive.add(this);
     if(this.probe)this.addEventListener("message",e=>{if(this.metric){window.__loadWorker.push({...this.metric,
      duration_ms:performance.now()-this.metric.start,status:e.data.result?.status||e.data.t});this.metric=null;}});
    }
    postMessage(m,...rest){if(this.probe){if(m.t==="init")this.job=m.job.id;this.metric={job:this.job,kind:m.t,start:performance.now()};}return super.postMessage(m,...rest);}
    terminate(){window.__loadLive.delete(this);return super.terminate();}
   };
  });
  async function presenter(hold=false){
   const p=await context.newPage();p.on("pageerror",e=>errors.push(e.message));
   const note=event=>{browserEvents.push({ms:now(),...event});if(browserEvents.length>200)browserEvents.shift();};
   p.on("crash",()=>{browserFailure="Presenter browser page crashed";note({event:"crash"});});p.on("close",()=>note({event:"page-closed"}));
   p.on("websocket",socket=>{
    for(const direction of ["framesent","framereceived"])socket.on(direction,event=>{
     try{const m=JSON.parse(event.payload);note({event:direction,t:m.t,id:m.id,re:m.re,jobs:m.jobs?.length});}catch{}
    });
    socket.on("close",()=>note({event:"socket-closed"}));
   });
   if(hold)await p.route("**/static/stage/plugin-evaluator-worker.js",()=>{});
   await p.goto(base+"/stage?bundle="+deck.bundle);await p.locator("#next").waitFor();return p;
  }
  page=await presenter();await page.locator("#next").click();
  await page.locator("#next").click();await page.locator("#next").click();
  teacher=new Student("teacher");
  await teacher.connect({t:"hello",role:"host",key:"synthetic-load-key",deck:deck.deck,bundle:deck.bundle});
  assert.equal(teacher.view().data.phase,"introduce");
  assert((await teacher.command("open",{control_version:teacher.view().data.control_version})).receipt.accepted);
  await until(()=>teacher.view().data.phase==="open","open");
  const pin=(await page.locator("#pin").innerText()).replace(/\D/g,"");
  for(let i=0;i<actors;i++)students.push(new Student(i));
  const joined=now();
  await Promise.all(students.map((s,i)=>s.connect({t:"join",pin,nickname:"Synthetic "+(i+1),join_nonce:randomBytes(16).toString("hex")})));
  phases.push({name:"join",duration_ms:now()-joined});console.log("Joined "+actors+" students");
  async function batch(answer,label){
   const start=now(),batch=await Promise.all(students.map(s=>s.submit(answer,label)));
   await until(()=>batch.every(r=>r.checked_ms!==undefined),label+" saved");
   phases.push({name:label,duration_ms:now()-start});console.log(label+" saved");
   return batch;
  }
  const first=await batch(correct,"initial");
  const retry=await students[0].send({t:"plugin.command",command:first[0].envelope});
  assert.deepEqual(retry.receipt,first[0].receipt);
  if(actors===1000){
   const extra=new Student("capacity");
   try{
    await assert.rejects(extra.connect({t:"join",pin,nickname:"Synthetic capacity",join_nonce:randomBytes(16).toString("hex")}),/^Error: full:/);
   }finally{await extra.close();}
  }
  if(process.env.BPLUS_SMOKE!=="1"){
   const start=now(),latest=[];
   await Promise.all(students.map(async s=>{
    const old=await s.submit(wrong,"replacement-old");
    latest.push(await s.submit(correct,"replacement-latest",old.version+1));
   }));
   await until(()=>latest.every(r=>r.checked_ms!==undefined),"replacement saved");
   phases.push({name:"replacement",duration_ms:now()-start});console.log("Replacement saved");
   // Same authenticated actor on a reconnected phone recovers the persisted answer.
   const returning=students[0],token=returning.welcome.token;
   await returning.close();await returning.connect({t:"resume",token});
   assert.equal(returning.view().data.own.version,3);
   assert.deepEqual(returning.view().data.own.answer,correct);
   // Close an evaluator that has real outstanding leases, then recover all jobs.
   workerTimes.push(...await page.evaluate(()=>window.__loadWorker));await page.close();
   page=await presenter(true);
   const pending=await Promise.all(students.map(s=>s.submit(correct,"reconnect")));
   await until(()=>fs.readFileSync(metrics,"utf8").trim().split("\n").some(line=>{
    const e=JSON.parse(line);return e.event==="lease"&&e.jobs.some(j=>pending.some(r=>r.jobs.includes(j.id)));
   }),"held lease");
   await page.close();page=await presenter();
   await until(()=>pending.every(r=>r.checked_ms!==undefined),"reconnected evaluator");
   console.log("Evaluator recovery saved");
  }
  await until(()=>teacher.view().data.counts.saved===actors,"all saved");
  async function control(op,payload={}){
   const result=await teacher.command(op,{control_version:teacher.view().data.control_version,...payload});
   assert(result.receipt.accepted);
   await until(()=>teacher.view().revision>=result.receipt.revision,"control projection");
  }
  // Verify bounded pages and stable response numbers through the actual controls.
  const firstPage=teacher.view().data.participants;
  assert.equal(firstPage.length,Math.min(25,actors));
  assert.deepEqual(firstPage.map(r=>r.number),Array.from({length:firstPage.length},(_,i)=>i+1));
  const lastPage=Math.floor((actors-1)/25);
  await control("roster-page",{page:lastPage});
  const roster=teacher.view().data.participants;
  assert.equal(roster.length,actors-lastPage*25);
  assert.equal(roster.at(-1).number,actors);
  assert.equal(teacher.view().data.roster_page.total,actors);
  assert.equal(teacher.view().data.roster_page.pages,lastPage+1);
  await control("close");
  await control("select-answer",{actor:roster.at(-1).actor,answer_version:roster.at(-1).version});
  await control("share-answer",{actor:roster.at(-1).actor,answer_version:roster.at(-1).version});
  assert(students.every(s=>s.state.me?.score===0&&s.view().data.scoring?.awarded==null));
  scoring.privateBeforeReveal=true;
  const publicationStart=now();
  await control("reveal");
  await until(()=>students.every(s=>s.view().data.phase==="revealed"),"reveal reached every student");
  await until(()=>students.every(s=>s.state.me?.score===1000&&s.view().data.scoring?.awarded===1000),"all scoreboard totals");
  for(const s of students){
   assert.equal(s.view().data.own.feedback.correct,true);
   assert.equal(s.view().data.own.feedback.grade.credit,1000);
  }
  assert.deepEqual(students.map(s=>s.state.me.rank).sort((a,b)=>a-b),Array.from({length:actors},(_,i)=>i+1));
  scoring.allPublished=true;
  phases.push({name:"score-publication",duration_ms:now()-publicationStart});
  await page.locator(".bp-controls > details > summary").click();
  assert.equal(await page.locator('[data-bp="roster"] option').count(),roster.length+1);
  if(lastPage){
   await page.locator('[data-bp="roster-previous"]').click();
   await until(()=>teacher.view().data.roster_page.page===lastPage-1,"previous roster page");
   await page.locator('[data-bp="roster-next"]').click();
   await until(()=>teacher.view().data.roster_page.page===lastPage,"next roster page");
  }
  // A receipt on the teacher socket can precede the browser's projection.
  // Capture the settled controls, not the disabled waiting-for-update state.
  await until(async()=>
   (await page.locator('[data-bp="roster-page"]').innerText()).endsWith((lastPage+1)+" / "+(lastPage+1))&&
   !(await page.locator('[data-bp="roster"]').isDisabled()),"presenter roster settled");
  assert.equal(await page.locator('[data-bp="roster"] option').count(),roster.length+1);
  await page.screenshot({path:path.join(output,"presenter-"+actors+".png")});
  workerTimes.push(...await page.evaluate(()=>window.__loadWorker));
  const resetStart=now(),reset=await teacher.command("_reset",{});
  assert(reset.receipt.accepted);
  await until(()=>students.every(s=>s.view().data.phase==="introduce"&&!s.view().data.own&&s.state.me?.score===0),"reset withdraws every score");
  scoring.resetWithdraws=true;
  phases.push({name:"score-withdrawal",duration_ms:now()-resetStart});
  assert.deepEqual(errors,[]);
 }catch(e){failure=String(e.stack);console.error(failure);
  const snapshot=await Promise.race([
   page?.evaluate(()=>({now:Date.now(),pulse:window.__loadPulse,liveWorkers:window.__loadLive?.size,
     workers:window.__loadWorker?.slice(-20),text:document.body.innerText.slice(0,2000)})).catch(error=>({error:String(error)})),
   delay(5000).then(()=>({error:"presenter JavaScript did not respond within 5s"}))]);
  fs.writeFileSync(path.join(output,"failure-diagnostics.json"),JSON.stringify({browserEvents,snapshot},null,2));
 }
 finally{
  await Promise.all(students.map(s=>s.close()));await teacher?.close();await browser?.close();
  if(server&&server.exitCode===null){server.stdin.end("stop\n");
   await Promise.race([new Promise(r=>server.once("exit",()=>{stopped=true;r();})),delay(10000)]);
   if(!stopped&&server.exitCode===null){server.kill();errors.push("forced shutdown");}
  }
  const events=metrics&&fs.existsSync(metrics)?fs.readFileSync(metrics,"utf8").trim().split("\n").filter(Boolean).map(JSON.parse):[];
  const queued=new Map(),waits=[],finished=new Set();
  for(const e of events){
   if(e.event==="command")for(const id of Object.values(e.receipt?.jobs||{}))if(!queued.has(id))queued.set(id,e.ms);
   if(e.event==="lease")for(const j of e.jobs)if(queued.has(j.id))waits.push({id:j.id,generation:j.generation,ms:e.ms-queued.get(j.id)});
   if(e.event==="finish"&&e.accepted&&e.outcome==="ok")finished.add(e.id);
  }
  const groups={};
  for(const phase of new Set(rows.map(r=>r.phase))){
   const group=rows.filter(r=>r.phase===phase),ids=new Set(group.flatMap(r=>r.jobs||[]));
   groups[phase]={submitted:group.length,accepted:group.filter(r=>r.accepted).length,
    acknowledgement:summary(group.map(r=>r.ack_ms)),feedback:summary(group.map(r=>r.checked_ms)),
    queue_wait:summary(waits.filter(r=>ids.has(r.id)&&r.generation===1).map(r=>r.ms)),
    evaluation:summary(workerTimes.filter(r=>ids.has(r.job)&&r.kind==="eval").map(r=>r.duration_ms)),
    accepted_results:[...ids].filter(id=>finished.has(id)).length};
   if(phase!=="replacement-old"&&groups[phase].accepted_results!==actors)errors.push("Missing validated results: "+phase);
  }
  const hooks={};for(const method of ["initial_state","transition","view","view_batch"]){
   const calls=events.filter(e=>e.event==="hook"&&e.method===method);
   hooks[method]={...summary(calls.map(e=>e.duration_ms)),errors:calls.filter(e=>e.error).length};
  }
  report={format:1,scoring,actors,browser:family,browser_version:browser?.version(),phases,groups,hooks,
   broadcast:summary(events.filter(e=>e.event==="broadcast").map(e=>e.duration_ms)),
   recovery_leases:waits.filter(r=>r.generation>1).length,
   bytes_to_students:students.reduce((n,s)=>n+s.bytes,0),errors,failure,graceful_shutdown:stopped,
   environment:{platform:os.platform(),release:os.release(),cpu:os.cpus()[0]?.model,logical_cpus:os.cpus().length},
   scope:{synthetic_student_sockets:true,presenter_browser:true,network:"loopback",physical_phones:false,
    normal_ack_budget_ms:ackBudget,normal_feedback_budget_ms:readyBudget,reconnect_budget_ms:150000}};
  report.correctness_pass=!failure&&errors.length===0&&Object.values(hooks).every(h=>h.errors===0);
  report.normal_budget_pass=Object.entries(groups).filter(([n])=>!["replacement-old","reconnect"].includes(n))
   .every(([,g])=>g.feedback.n===actors&&g.acknowledgement.p95_ms<=ackBudget&&g.feedback.p95_ms<=readyBudget);
  report.recovery_budget_pass=!groups.reconnect||(groups.reconnect.feedback.n===actors&&groups.reconnect.feedback.max_ms<=150000&&report.recovery_leases>0);
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  fs.writeFileSync(path.join(output,"client-events.json"),JSON.stringify({rows,workerTimes},null,2)+"\n");
  console.log(JSON.stringify(report,null,2));
  if(!report.correctness_pass||!report.normal_budget_pass||!report.recovery_budget_pass)process.exitCode=1;
 }
})();

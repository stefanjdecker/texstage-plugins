// SPDX-License-Identifier: Apache-2.0
// Synthetic authenticated sockets + actual presenter/browser worker. No course data.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn}=require("node:child_process"),{randomBytes}=require("node:crypto");
const playwright=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const {verifyWorkload}=require("./normalization_load_checks.cjs");
const bundle=path.resolve(process.argv[2]||""),family=process.env.BROWSER||"chromium";
const pointsExperiment=process.env.NORMALIZATION_POINTS==="1";
let pointsResult=null;
const actors=Number(process.env.NORMALIZATION_ACTORS||600);
assert(Number.isInteger(actors)&&actors>=2&&actors<=1000,"actors must be 2..1000");
const output=path.resolve(process.env.NORMALIZATION_LOAD_OUTPUT||path.join(__dirname,"../artifacts/normalization-load",family));
fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,"profile-"));
const port=Number(process.env.TEXSTAGE_TEST_PORT||18835),base="http://127.0.0.1:"+port;
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const digest=file=>require("node:crypto").createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const harnessHash=digest(__filename),deckHash=digest(path.join(bundle,"deck.json"));
const metrics=path.join(output,"server-events.jsonl"),errors=[],submissions=[],workerTimes=[],phases=[];
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"normalization_load_server.py"),
 "--bundle",bundle,"--data",profile,"--metrics",metrics,"--port",String(port)],{windowsHide:true,stdio:["pipe","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const now=()=>performance.now();
async function until(test,label,timeout=180000){
 const start=now();while(now()-start<timeout){if(await test())return;await delay(100);}throw Error("Timed out: "+label);
}
function summary(values){
 const sorted=values.filter(Number.isFinite).sort((a,b)=>a-b);
 const q=p=>sorted.length?+sorted[Math.max(0,Math.ceil(sorted.length*p)-1)].toFixed(2):null;
 return {n:sorted.length,p50_ms:q(.5),p95_ms:q(.95),p99_ms:q(.99),max_ms:q(1)};
}
class Student {
 constructor(index,role="player"){this.index=index;this.role=role;this.pending=new Map();this.counter=0;this.targets=new Map();this.state=null;}
 async connect(login){
  this.socket=new WebSocket(base.replace("http:","ws:")+"/ws");
  this.socket.addEventListener("message",event=>{
   const m=JSON.parse(String(event.data));
   if(m.t==="state"){
    this.state=m;
    if(m.plugins?.error)errors.push(m.plugins.error);
    for(const d of m.plugins?.items||[]){
     const v=d.views?.["participant-input"]?.data;
     if(v&&v.phase!=="revealed"&&(v.feedback!==null||v.analysis!==null||v.worked!==null||v.points!=null))errors.push("Private feedback before reveal");
     const target=this.targets.get(d.item);
     if(target&&v?.answer_version===target.version&&v.status==="checked"&&target.checked_ms===undefined){
      try{assert.deepEqual(v.answer,target.expectedAnswer);}
      catch{errors.push("Checked state does not contain the latest submitted answer");}
      target.checked_ms=now()-target.start;
     }
    }
   }
   if(m.t==="plugin.error")errors.push(m.message);
   const p=this.pending.get(m.re);
   if(p){this.pending.delete(m.re);clearTimeout(p.timer);m.t==="error"?p.reject(Error(m.error+": "+m.message)):p.resolve(m);}
  });
  await new Promise((resolve,reject)=>{this.socket.addEventListener("open",resolve,{once:true});this.socket.addEventListener("error",reject,{once:true});});
  this.welcome=await this.send(login);
  await until(()=>this.state?.plugins?.items?.length,"initial state");
 }
 send(message){
  const id="load-"+this.index+"-"+(++this.counter);
  return new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>{this.pending.delete(id);reject(Error("ACK timeout "+id));},180000);
   this.pending.set(id,{resolve,reject,timer});this.socket.send(JSON.stringify({...message,id}));
  });
 }
 descriptor(item){return this.state.plugins.items.find(d=>d.item===item);}
 async command(item,operation,payload){
  const d=this.descriptor(item),view=Object.values(d.views)[0];
  const request="load-"+randomBytes(12).toString("hex");
  this.lastEnvelope={type:d.type,item,operation,payload,epoch:view.epoch,
   expected_revision:view.revision,request_id:request};
  return this.send({t:"plugin.command",command:this.lastEnvelope});
 }
 async submit(item,answer,phase,label){
  const v=this.descriptor(item).views["participant-input"].data;
  const row={phase:label,actor:this.index,item,version:v.answer_version+1,start:now()};
  Object.defineProperty(row,"expectedAnswer",{value:answer}); // Do not add answer content to the log.
  submissions.push(row);this.targets.set(item,row);
  const reply=await this.command(item,"submit",{phase,version:v.answer_version,answer});
  row.ack_ms=now()-row.start;row.accepted=reply.receipt?.accepted;row.error=reply.receipt?.error;
  row.jobs=Object.values(reply.receipt?.jobs||{});
  assert(row.accepted,JSON.stringify(reply));return row;
 }
 close(){for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(Error("closing"));}this.pending.clear();this.socket?.close();}
}
(async()=>{
 let browser,context,page,teacher,projector;const students=[];
 let failure=null,stopped=false;
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server",30000);
  browser=await playwright[family].launch({headless:true,...(process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  context=await browser.newContext({viewport:{width:1440,height:1000}});
  // Observe Worker messaging without replacing any evaluator or changing its policy.
  await context.addInitScript(()=>{
   localStorage.setItem("texquiz:presenter-key","synthetic-load-key");
   window.__loadWorker=[];
   const Original=window.Worker;
   window.Worker=class extends Original{
    constructor(url,options){super(url,options);this.probe=String(url).includes("plugin-evaluator-worker.js");
     if(this.probe)this.addEventListener("message",event=>{
      if(!this.pendingProbe)return;
      window.__loadWorker.push({...this.pendingProbe,duration_ms:performance.now()-this.pendingProbe.start,
       status:event.data.result?.status||event.data.t});this.pendingProbe=null;
     });
    }
    postMessage(message,...args){
     if(this.probe){if(message.t==="init")this.job=message.job.id;
      this.pendingProbe={job:this.job,kind:message.t,start:performance.now()};}
     return super.postMessage(message,...args);
    }
   };
  });
  async function presenter(hold=false){
   const p=await context.newPage();p.on("pageerror",e=>errors.push(e.message));
   if(hold)await p.route("**/static/stage/plugin-evaluator-worker.js",()=>{}); // Simulate a lost presenter with outstanding leases.
   await p.goto(base+"/stage?bundle="+deck.bundle);
   await p.locator(".presenter-controls").first().waitFor();
   return p;
  }
  page=await presenter();
  const pin=(await page.locator("#pin").innerText()).replace(/\D/g,"");
  teacher=new Student("teacher","host");
  await teacher.connect({t:"hello",role:"host",key:"synthetic-load-key",deck:deck.deck,bundle:deck.bundle});
  projector=await context.newPage();projector.on("pageerror",e=>errors.push(e.message));
  await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  async function open(item){
   await until(()=>teacher.descriptor(item),"teacher item");
   const v=teacher.descriptor(item).views["presenter-controls"].data;
   if(v.phase!=="open")assert((await teacher.command(item,"open",{control:v.control_version})).receipt.accepted);
   await until(()=>teacher.descriptor(item).views["presenter-controls"].data.phase==="open","open");
  }
  await open("registration");
  for(let i=0;i<actors;i++)students.push(new Student(i));
  await Promise.all(students.map((s,i)=>s.connect({t:"join",pin,nickname:"Synthetic "+(i+1),join_nonce:randomBytes(16).toString("hex")})));
  const correct={mode:"decompose",relations:[3,5,28,48]},wrong={mode:"decompose",relations:[3,28,48]};
  async function batch(item,answer,label){
   const start=now(),rows=await Promise.all(students.map(s=>s.submit(item,typeof answer==="function"?answer(s.index):answer,
    s.descriptor(item).views["participant-input"].data.phase_version,label)));
   return {start,rows};
  }
  async function completed(rows,label){
   await until(()=>rows.every(r=>r.checked_ms!==undefined),label);
  }
  // 32 variants (30 distinct decompositions), including correct, lossy and non-normal forms.
  // Cache reuse is measured explicitly; this is not 600 unique worst-case inputs.
  const varied=i=>({mode:"decompose",relations:[...new Set([3,5,28,48,1+(i%32)])].sort((a,b)=>a-b)});
  let round=await batch("registration",varied,"initial");await completed(round.rows,"initial checked");
  phases.push({name:"initial",duration_ms:now()-round.start});
  if(actors>16){
   const controls=page.locator(".presenter-controls").first(),
    a=controls.getByLabel("Answer A",{exact:true}),b=controls.getByLabel("Answer B",{exact:true});
   await a.selectOption({index:1});const retained=await a.inputValue();
   await controls.getByRole("button",{name:"Next page",exact:true}).click();
   await until(()=>teacher.descriptor("registration").views["presenter-controls"].data.page===1,"roster page");
   await until(async()=>await controls.locator("nav").textContent().then(t=>t.includes("Page 2 /")),"rendered roster page");
   assert.equal(await a.inputValue(),retained,"off-page answer A retained");
   const secondValue=await b.locator("option").evaluateAll((options,retained)=>options.find(o=>o.value&&o.value!==retained)?.value,retained);
   assert(secondValue);await b.selectOption(secondValue);
   await controls.getByRole("button",{name:"Compare privately",exact:true}).click();
   await until(()=>teacher.descriptor("registration").views["presenter-controls"].data.selected.length===2,"cross-page private comparison");
   assert.equal(teacher.descriptor("registration").views["presenter-controls"].data.selected[0].handle,retained.split(":")[0]);
   await until(async()=>await controls.getByRole("button",{name:"Clear selection",exact:true}).isEnabled(),"rendered comparison",15000);
   await page.screenshot({path:path.join(output,"cross-page-comparison.png"),fullPage:true});
   await controls.getByRole("button",{name:"Previous page",exact:true}).click();
   await until(()=>teacher.descriptor("registration").views["presenter-controls"].data.page===0,"first roster page",15000);
  }
  // Per-actor ACK ordering deliberately replaces an answer while other actors remain queued.
  const replacementStart=now(),newest=[];
  await Promise.all(students.map(async s=>{
   const phase=s.descriptor("registration").views["participant-input"].data.phase_version;
   await s.submit("registration",wrong,phase,"replacement-old");
   await until(()=>s.descriptor("registration").views["participant-input"].data.answer_version===2,"replacement version");
   newest.push(await s.submit("registration",correct,phase,"replacement-latest"));
  }));
  await completed(newest,"replacements checked");phases.push({name:"replacement",duration_ms:now()-replacementStart});
  if(actors===1000){
   const extra=new Student("capacity");students.push(extra);
   await assert.rejects(extra.connect({t:"join",pin,nickname:"Synthetic capacity",join_nonce:randomBytes(16).toString("hex")}),/full/i);
   extra.close();students.pop();
  }
  await page.locator("#next").click();
  await open("classify");
  await until(()=>students.every(s=>s.descriptor("classify")),"two active items");
  const multiStart=now(),multi=[];
  // Both activities are active. Stagger classroom-wide bursts to respect the
  // unchanged 1,000-job session queue, including at the 1,000-student ceiling.
  multi.push(await batch("registration",correct,"multi-registration"));
  await completed(multi[0].rows,"first active item checked");
  multi.push(await batch("classify",{mode:"classify",normal_form:"3nf",witness:[4,2]},"multi-classify"));
  await completed(multi.flatMap(r=>r.rows),"two-item checked");
  phases.push({name:"multi",duration_ms:now()-multiStart});
  if(process.env.NORMALIZATION_SKIP_RECONNECT!=="1"){
   workerTimes.push(...await page.evaluate(()=>window.__loadWorker));await page.close();
   page=await presenter(true);
   const reconnectStart=now(),pending=await batch("registration",{mode:"decompose",relations:[1,2,4,8,16,32]},"reconnect");
   // Wait for a real durable lease, not merely a sent submission.
   await until(()=>fs.readFileSync(metrics,"utf8").trim().split("\n").some(line=>{
    const e=JSON.parse(line);return e.event==="lease"&&e.jobs.some(j=>pending.rows.some(r=>r.jobs.includes(j.id)));
   }),"held lease");
   await page.close();page=await presenter();
   await completed(pending.rows,"lease recovery after presenter reconnect");
   phases.push({name:"reconnect",duration_ms:now()-reconnectStart});
  }
  if(pointsExperiment){
   const pointRound=await batch("registration",correct,"points-correct");
   await completed(pointRound.rows,"scored latest answers");
   assert(students.every(s=>s.state.me.score===0&&s.descriptor("registration").views["participant-input"].data.points===null));
   async function control(op){
    const d=teacher.descriptor("registration").views["presenter-controls"].data;
    assert((await teacher.command("registration",op,{control:d.control_version})).receipt.accepted);
    await until(()=>teacher.descriptor("registration").views["presenter-controls"].data.phase===(op==="close"?"closed":"revealed"),op);
   }
   await control("close");await control("reveal");
   const revealEnvelope=teacher.lastEnvelope;
   await until(()=>students.every(s=>s.state.me.score===1000&&s.descriptor("registration").views["participant-input"].data.points===1000),"published one award each");
   const replay=await teacher.send({t:"plugin.command",command:revealEnvelope});
   assert(replay.receipt.accepted);
   assert(students.every(s=>s.state.me.score===1000),"receipt replay cannot add another award");
   assert((await teacher.command("registration","_reset",{})).receipt.accepted);
   await until(()=>students.every(s=>s.state.me.score===0&&s.descriptor("registration").views["participant-input"].data.answer_version===0),"reset withdraws full class awards");
   pointsResult={actors,maximum:1000,privateBeforeReveal:true,publishedOnReveal:true,noReplayBonus:true,resetWithdraws:true};
  }
  workerTimes.push(...await page.evaluate(()=>window.__loadWorker));
  assert.deepEqual(errors,[]);
 }catch(e){failure=String(e.stack);console.error(failure);}
 finally{
  for(const s of students)s.close();teacher?.close();
  // Wait for the socket close handshakes before asking uvicorn to stop.
  await until(()=>[...students,teacher].filter(Boolean).every(s=>!s.socket||s.socket.readyState===WebSocket.CLOSED),"socket shutdown",30000).catch(e=>errors.push(String(e)));
  await browser?.close();
  if(server.exitCode===null){
   server.stdin.end("stop\n");
   await new Promise(resolve=>{
    const timer=setTimeout(resolve,30000);
    server.once("exit",()=>{stopped=true;clearTimeout(timer);resolve();});
   });
   if(!stopped&&server.exitCode===null){server.kill();errors.push("server required forced shutdown");}
  }
  const events=fs.existsSync(metrics)?fs.readFileSync(metrics,"utf8").trim().split("\n").filter(Boolean).map(JSON.parse):[];
  const queued=new Map(),leases=new Map(),waits=[],completion=[],finishStatus={};
  for(const e of events){
   if(e.event==="command")for(const id of Object.values(e.receipt?.jobs||{}))queued.set(id,{ms:e.ms,item:e.item});
   if(e.event==="lease")for(const j of e.jobs){
    const q=queued.get(j.id);if(q){waits.push({id:j.id,item:q.item,generation:j.generation,ms:e.ms-q.ms});leases.set(j.id,e.ms);}
   }
   if(e.event==="finish"){
    finishStatus[e.outcome]=(finishStatus[e.outcome]||0)+1;
    if(e.accepted)completion.push({id:e.id,ms:e.ms-(leases.get(e.id)||e.ms)});
   }
  }
  const hooks={};for(const method of ["initial_state","transition","view"]){
   const calls=events.filter(e=>e.event==="hook"&&e.method===method);
   hooks[method]={...summary(calls.map(e=>e.duration_ms)),errors:calls.filter(e=>e.error).length};
  }
  const groups={};
  for(const phase of [...new Set(submissions.map(r=>r.phase))]){
   const rows=submissions.filter(r=>r.phase===phase),ids=new Set(rows.flatMap(r=>r.jobs||[]));
   groups[phase]={submitted:rows.length,accepted:rows.filter(r=>r.accepted).length,
    acknowledgement:summary(rows.map(r=>r.ack_ms)),checked:summary(rows.map(r=>r.checked_ms)),
    queue_wait:summary(waits.filter(r=>ids.has(r.id)&&r.generation===1).map(r=>r.ms)),
    worker:summary(workerTimes.filter(r=>ids.has(r.job)&&r.kind==="eval").map(r=>r.duration_ms))};
  }
  const workload=verifyWorkload({actors,submissions,events,points:pointsExperiment,reconnect:process.env.NORMALIZATION_SKIP_RECONNECT!=="1"});
  errors.push(...workload.failures);
  const report={format:4,synthetic:true,points:pointsResult,harness_sha256:harnessHash,deck_sha256:deckHash,actors,browser:family,browser_version:browser?.version(),phases,groups,hooks,workload,
   worker_startup:summary(workerTimes.filter(r=>r.kind==="init").map(r=>r.duration_ms)),
   leased_to_accepted_result:summary(completion.map(r=>r.ms)),releases:waits.filter(r=>r.generation>1),
   outcome_counts:finishStatus,errors,failure,graceful_shutdown:stopped,
   assumptions:{student_rendering:false,initial_distinct_inputs:30,simultaneous_activity_bursts:false,network:"loopback",physical_phones:false,
    normal_feedback_budget_ms:30000,normal_ack_budget_ms:5000,reconnect_budget_ms:150000}};
  report.normal_budget_pass=Object.entries(groups).filter(([name])=>!["replacement-old","reconnect"].includes(name))
   .every(([,r])=>r.checked.n===actors&&r.checked.p95_ms<=30000&&r.acknowledgement.p95_ms<=5000);
  report.reconnect_budget_pass=groups.reconnect
   ? groups.reconnect.checked.n===actors&&groups.reconnect.checked.max_ms<=150000 : null;
  report.budget_pass=report.normal_budget_pass&&report.reconnect_budget_pass!==false;
  report.correctness_pass=!failure&&errors.length===0;
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  fs.writeFileSync(path.join(output,"client-events.json"),JSON.stringify({submissions,workerTimes},null,2)+"\n");
  console.log(JSON.stringify(report,null,2));
  if(!report.correctness_pass||!report.budget_pass)process.exitCode=1;
 }
})();

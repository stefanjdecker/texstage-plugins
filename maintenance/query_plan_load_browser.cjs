// SPDX-License-Identifier: Apache-2.0
// Synthetic clients on the actual authenticated host protocol. Only the real
// presenter page evaluates jobs; this probe never fabricates engine results.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),os=require("node:os");
const {spawn}=require("node:child_process"),{performance}=require("node:perf_hooks"),pw=require("playwright");
const bundle=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]||"artifacts/query-plan-load");
const count=Number(process.env.QUERY_PLAN_LOAD_ACTORS||600),rounds=Number(process.env.QUERY_PLAN_LOAD_ROUNDS||3);
const interval=Number(process.env.QUERY_PLAN_LOAD_INTERVAL_MS||1000);
const leasedLoss=process.env.QUERY_PLAN_LOAD_LEASE_LOSS!=="0";
assert(Number.isInteger(count)&&count>=2&&count<=1000);assert(Number.isInteger(rounds)&&rounds>=1&&rounds<=10);
assert(Number.isInteger(interval)&&interval>=0&&interval<=30000);
const family=process.env.BROWSER||"chromium",root=path.resolve(__dirname,"..");
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const lesson=JSON.parse(fs.readFileSync(path.join(root,"examples/query-plan/activities/library.json")));
const item="library",kind="io.github.stefanjdecker.queryplan.challenge";
fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,"session-"));
const clients=[],events=[],errors=[];let server,log,browser,context,presenter,presenterLogin,base,host,pin,request=0;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label,ms=180000){
 const start=performance.now();
 while(performance.now()-start<ms){if(await fn())return;await delay(50);}
 throw Error("Timed out: "+label);
}
function stats(values){
 const sorted=[...values].sort((a,b)=>a-b),at=p=>sorted[Math.max(0,Math.ceil(p*sorted.length)-1)];
 return {count:sorted.length,min:sorted[0]??null,p50:at(.5)??null,p95:at(.95)??null,max:sorted.at(-1)??null};
}
function descriptor(state){return state?.plugins?.items?.find(d=>d.item===item);}
function view(state){const d=descriptor(state);return d&&Object.values(d.views)[0];}
function digestPlan(answer){return JSON.stringify(answer,(_,v)=>v&&typeof v==="object"&&!Array.isArray(v)?Object.fromEntries(Object.entries(v).sort()):v);}
function assertPrivate(state){
 const d=descriptor(state);if(!d)return;
 const v=view(state).data;
 assert(!("participants" in v)&&!("selected" in v)&&!("counts" in v));
 if(v.phase!=="revealed")assert(!v.solution&&!v.own?.feedback,"unrevealed participant feedback leaked");
 for(const k of ['"private":','"reference":','"evaluations":','"correlation":','"digest":'])assert(!JSON.stringify(d).includes(k));
}
class Client {
 constructor(index){
  this.index=index;this.state=null;this.pending=new Map();this.sequence=0;this.completions=new Map();this.bytes=0;this.pushes=0;
  this.ws=new WebSocket(base.replace("http","ws")+"/ws");
  this.opened=new Promise((resolve,reject)=>{this.ws.addEventListener("open",resolve,{once:true});this.ws.addEventListener("error",()=>reject(Error("socket open failed")),{once:true});});
  this.ws.addEventListener("message",event=>{
   const m=JSON.parse(event.data),now=performance.now();
   this.bytes+=Buffer.byteLength(event.data);
   if(m.t==="state"){
    this.state=m;this.pushes++;
    if(this.index>=0) {
     try{assertPrivate(m);}catch(e){errors.push(e.message);}
     const v=view(m),own=v?.data.own;
     if(own&&own.status!=="pending"){
      const key=v.epoch+":"+own.version;if(!this.completions.has(key))this.completions.set(key,{at:now,status:own.status});
     }
    }
   }
   if(this.pending.has(m.re)){
    const p=this.pending.get(m.re);this.pending.delete(m.re);clearTimeout(p.timer);
    if(m.t==="error")p.reject(Object.assign(Error(m.message),{code:m.error}));else p.resolve(m);
   }
  });
  this.ws.addEventListener("close",()=>{
   for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(Error("socket closed"));}this.pending.clear();
  });
  clients.push(this);
 }
 async login(message){await this.opened;return this.send(message);}
 send(message){
  const id="load-"+this.index+"-"+(++this.sequence);
  return new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>{this.pending.delete(id);reject(Error("receipt deadline"));},180000);
   this.pending.set(id,{resolve,reject,timer});this.ws.send(JSON.stringify({...message,id}));
  });
 }
 close(){this.ws.close();}
}
function command(client,operation,payload){
 const v=view(client.state);assert(v,"missing activity view");
 return {type:kind,item,operation,payload,epoch:v.epoch,expected_revision:v.revision,request_id:"load-request-"+(++request).toString().padStart(10,"0")};
}
async function dispatch(client,op,payload){
 const envelope=command(client,op,payload),started=performance.now();
 const response=await client.send({t:"plugin.command",command:envelope});
 assert(response.receipt,JSON.stringify(response));
 return {receipt:response.receipt,started,ack:performance.now()};
}
async function control(op){
 const payload=op==="_reset"?{}:{control:view(host.state).data.control_version};
 const r=await dispatch(host,op,payload);assert(r.receipt.accepted,JSON.stringify(r.receipt));
 await until(()=>{const v=view(host.state);return v&&v.epoch===r.receipt.epoch&&v.revision>=r.receipt.revision;},"control view");
}
async function submit(client,answer,label,expectedError=null){
 const before=view(client.state),version=before.data.own?.version||0;
 const r=await dispatch(client,"submit-plan",{phase:before.data.phase_version,version,answer});
 const event={scenario:label,actor:client.index,epoch:before.epoch,version:version+1,started:r.started,ack_ms:r.ack-r.started,
  accepted:r.receipt.accepted,error:r.receipt.error||null,revision:r.receipt.revision,answer:digestPlan(answer)};
 events.push(event);
 if(expectedError){assert.equal(r.receipt.error,expectedError);assert.equal(r.receipt.accepted,false);return event;}
 assert(r.receipt.accepted,JSON.stringify(r.receipt));
 await until(()=>{const v=view(client.state);return v?.epoch===event.epoch&&v.data.own?.version===event.version;},"actor "+client.index+" saved projection");
 assert.equal(digestPlan(view(client.state).data.own.answer),event.answer);
 return event;
}
async function complete(batch,label,ms=180000){
 await until(()=>batch.every(e=>clients.find(c=>c.index===e.actor)?.completions.has(e.epoch+":"+e.version)),label,ms);
 for(const e of batch){
  const c=clients.find(c=>c.index===e.actor).completions.get(e.epoch+":"+e.version);
  assert.equal(c.status,"saved",label+" unavailable actor "+e.actor);
  e.complete_ms=c.at-e.started;
 }
 await until(()=>view(host.state)?.data.counts.pending===0,label+" presenter totals",ms);
}
async function openPresenter(){
 presenter=await context.newPage();presenter.on("pageerror",e=>errors.push(e.message));
 presenter.on("websocket",socket=>socket.on("framesent",({payload})=>{
  const m=JSON.parse(String(payload));if(m.t==="hello")presenterLogin=m;
 }));
 await presenter.goto(base+"/stage?bundle="+deck.bundle);
 await presenter.locator("#pin").waitFor();await presenter.bringToFront();
}
function summarize(label,batch,start,end){
 const complete=batch.filter(e=>e.complete_ms!==undefined);
 const sorted=[...complete].sort((a,b)=>(a.started+a.complete_ms)-(b.started+b.complete_ms));
 const quartiles=[0,1,2,3].map(q=>stats(complete.filter(e=>Math.floor(e.actor*4/count)===q).map(e=>e.complete_ms)));
 return {label,offered:batch.length,accepted:batch.filter(e=>e.accepted).length,
  wall_ms:end-start,accepted_per_second:batch.filter(e=>e.accepted).length/((end-start)/1000),
  acknowledgement_ms:stats(batch.map(e=>e.ack_ms)),completion_ms:stats(complete.map(e=>e.complete_ms)),
  completion_actor_order:sorted.map(e=>e.actor),actor_quartile_completion_ms:quartiles};
}
async function freePort(){const net=require("node:net"),s=net.createServer();return new Promise((resolve,reject)=>{s.once("error",reject);s.listen(0,"127.0.0.1",()=>{const port=s.address().port;s.close(e=>e?reject(e):resolve(port));});});}
(async()=>{
 const report={format:1,started_at:new Date().toISOString(),passed:false,actors:count,rounds,interval_ms:interval,
  runtime:"Real host WebSockets; one real browser presenter evaluator; synthetic participants",
  browser:family,node:process.version,platform:os.platform(),release:os.release(),cpus:os.cpus().length,
  scenarios:[],limits:{receipt_ms:180000,completion_ms:180000,lease_recovery_ms:200000,burst_ack_p95_ms:5000,burst_completion_max_ms:60000},
  interpretation:"Observed loopback workload, not a physical-device/LAN capacity guarantee."};
 try{
  const port=await freePort();base="http://127.0.0.1:"+port;
  server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",String(port)],{windowsHide:true});
  log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
  await until(()=>{if(server.exitCode!==null)throw Error("server stopped");return fetch(base+"/").then(r=>r.ok).catch(()=>false);},"server",30000);
  browser=await pw[family].launch({headless:true,...(process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  report.browser_version=browser.version();
  context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  await openPresenter();
  for(let i=0;i<4;i++)await presenter.locator("#next").click();
  await until(()=>!!presenterLogin,"presenter login");
  host=new Client(-1);const welcome=await host.login({...presenterLogin,role:"host"});
  pin=welcome.pin;await until(()=>!!view(host.state),"host activity");
  report.provider=descriptor(host.state).modules["presenter-controls"].split("/")[2];
  // Join sequentially: the measured bursts start only after every actor is ready.
  const students=[];
  for(let i=0;i<count;i++){const c=new Client(i);await c.login({t:"join",pin,nickname:"Load "+(i+1),join_nonce:require("node:crypto").randomBytes(16).toString("hex")});students.push(c);}
  await until(()=>students.every(c=>view(c.state)),"all participants");
  await control("open");await until(()=>students.every(c=>view(c.state).data.phase==="open"),"open projection");
  console.log("Starting "+count+"-actor burst.");
  let start=performance.now(),batch=await Promise.all(students.map((c,i)=>submit(c,i%2?lesson.baseline:lesson.worked_answer,"burst")));
  await complete(batch,"burst evaluations");report.scenarios.push(summarize("burst",batch,start,performance.now()));
  assert.equal(view(host.state).data.count,count);
  const burst=report.scenarios[0];
  assert(burst.acknowledgement_ms.p95<=5000,"burst receipt p95 exceeds 5 seconds");
  assert(burst.completion_ms.max<=60000,"burst completion exceeds 60 seconds");
  // Every roster page is bounded; selection is private and can address the last page.
  const roster=[];
  for(let page=0;page<Math.ceil(count/25);page++){
   if(page){
    const r=await dispatch(host,"roster-page",{control:view(host.state).data.control_version,page});
    assert(r.receipt.accepted);
    await until(()=>view(host.state).data.page===page,"roster page "+page);
   }
   const rows=view(host.state).data.participants;assert(rows.length<=25);roster.push(...rows);
  }
  assert.equal(new Set(roster.map(r=>r.actor)).size,count);
  assert.deepEqual(roster.map(r=>r.number),Array.from({length:count},(_,i)=>i+1));
  const selected=roster.at(-1).actor;
  const selection=await dispatch(host,"select-answer",{control:view(host.state).data.control_version,actor:selected});
  assert(selection.receipt.accepted);
  await until(()=>!!view(host.state).data.selected,"last-page selection");
  report.roster={pages:Math.ceil(count/25),page_size:25,unique_actors:count,last_page_selection:true};
  if(count===1000){
   const extra=new Client(count);await extra.login({t:"join",pin,nickname:"Capacity check",join_nonce:require("node:crypto").randomBytes(16).toString("hex")});
   await until(()=>!!view(extra.state),"capacity actor");
   await submit(extra,lesson.baseline,"capacity","capacity");assert(!view(extra.state).data.own);
   extra.close();report.capacity_1001st_refused=true;
  }
  console.log("Burst complete; starting paced replacement rounds.");
  start=performance.now();const replacement=[];
  for(let round=0;round<rounds;round++){
   if(round)await delay(interval);
   batch=await Promise.all(students.map((c,i)=>submit(c,(i+round)%2?lesson.worked_answer:lesson.baseline,"replacement-"+round)));
   replacement.push(...batch);
  }
  await complete(batch,"latest replacement evaluations");
  for(const e of replacement){
   const c=students[e.actor].completions.get(e.epoch+":"+e.version);
   if(c)e.complete_ms=c.at-e.started;else e.superseded=true;
  }
  report.scenarios.push(summarize("paced replacements",replacement,start,performance.now()));
  report.scenarios.at(-1).superseded=replacement.filter(e=>e.superseded).length;
  console.log("Replacements complete; checking evaluator absence and recovery.");
  await presenter.close();presenter=null;
  start=performance.now();batch=await Promise.all(students.map(c=>submit(c,lesson.baseline,"absent")));
  await delay(2000);assert(students.every(c=>view(c.state).data.own.status==="pending"));
  const recovered=await Promise.all(students.map(c=>submit(c,lesson.worked_answer,"absent replacement")));
  await control("close"); // Pending evaluations remain meaningful after collection closes.
  const recovery=performance.now();await openPresenter();await complete(recovered,"evaluator return");
  report.scenarios.push({...summarize("absent evaluator replacements",recovered,start,performance.now()),
   absent_pending:count,recovery_ms:performance.now()-recovery,completed_after_close:true});
  assert.equal(view(host.state).data.counts["goal-met"],count);
  if(leasedLoss){
   for(const silent of [false,true]){
    const label=silent?"silent evaluator lease":"disconnected evaluator lease";
    console.log("Testing "+label+"; the production 120-second lease remains unchanged.");
    await presenter.close();presenter=null;
    if(view(host.state).data.phase!=="open")await control("open");
    await until(()=>students.every(c=>view(c.state).data.phase==="open"),"reopened for lease test");
    batch=await Promise.all(students.slice(0,Math.min(6,count)).map(c=>submit(c,lesson.baseline,label)));
    const abandoned=new Client(silent?-3:-2);await abandoned.login({...presenterLogin,role:"stage"});
    const jobs=(await abandoned.send({t:"plugin.work"})).jobs;assert.equal(jobs.length,2);
    // An observable disconnect may requeue immediately. A silent peer keeps its
    // socket open but sends no results, exercising the real expiry fallback.
    if(!silent)abandoned.close();
    const lost=performance.now();
    await openPresenter();await complete(batch,label+" recovery",200000);
    abandoned.close();
    report.scenarios.push({...summarize(label,batch,lost,performance.now()),abandoned_jobs:jobs.length,
     recovery_ms:performance.now()-lost,production_lease_seconds:120,observed_disconnect:!silent});
   }
  }
  if(view(host.state).data.phase==="open")await control("close");
  assert(students.every(c=>c.state.me.score===0),"no points before reveal");
  await control("reveal");
  await until(()=>students.every(c=>view(c.state).data.phase==="revealed"),"final feedback");
  students.forEach(c=>{
   const own=view(c.state).data.own;assert(own.feedback&&own.status==="saved");
   assert.equal(own.feedback.correct,digestPlan(own.answer)===digestPlan(lesson.worked_answer));
   assert.equal(own.points,own.feedback.correct?lesson.points:0);
   assert.equal(c.state.me.score,own.points,"host total agrees with released award");
  });
  report.final={count:view(host.state).data.count,counts:view(host.state).data.counts,
   actors_with_latest_feedback:students.length,actors_with_verified_points:students.length,participant_bytes:students.reduce((n,c)=>n+c.bytes,0),
   participant_pushes:students.reduce((n,c)=>n+c.pushes,0)};
  // Reset while everyone remains connected: no old answer/solution may survive.
  const epoch=view(host.state).epoch;await control("_reset");
  await until(()=>students.every(c=>view(c.state)?.epoch===epoch+1&&!view(c.state).data.own),count+"-actor reset");
  assert(students.every(c=>c.state.me.score===0),"reset withdraws all activity awards");
  report.reset_all_actors=true;assert.deepEqual(errors,[]);report.passed=true;
 }catch(e){report.error=e.stack;throw e;}
 finally{
  report.finished_at=new Date().toISOString();report.errors=errors;
  report.events=events.map(({answer,...e})=>e);
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  for(const c of clients)c.close();await browser?.close();
  if(server&&server.exitCode===null){const exited=new Promise(r=>server.once("exit",r));server.kill();await exited;}
  log?.end();
 }
 console.log(JSON.stringify({...report,events:undefined},null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});

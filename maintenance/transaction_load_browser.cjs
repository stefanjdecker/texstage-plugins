// SPDX-License-Identifier: Apache-2.0
// Authenticated synthetic students; actual presenter, isolated workers and CSP.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),os=require("node:os");
const {spawn}=require("node:child_process"),{randomBytes}=require("node:crypto");
const pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const bundle=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);
const actors=Number(process.env.TRANSACTION_ACTORS||600),family=process.env.BROWSER||"chromium";
assert(Number.isInteger(actors)&&actors>=2&&actors<=1000);
// 600 is the normal class target; 1000 is the slower peak-load ceiling.
const ackBudget=actors<=600?5000:10000,readyBudget=actors<=600?30000:60000;
fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const TYPE='io.github.stefanjdecker.transactionactivity.schedule',item='chain';
const source=JSON.parse(fs.readFileSync(path.join(__dirname,'../examples/transactions/activities/chain.lesson.json')));
const prepared=JSON.parse(fs.readFileSync(path.join(bundle,'keys.json'))).items[TYPE][item];
const worked=prepared.private.worked,wave=Number(process.env.TRANSACTION_WAVE_SECONDS||0);
const orders=[];
function interleave(prefix,left){if(left.every(p=>!p.length)){orders.push(prefix);return;}left.forEach((p,i)=>{if(p.length)interleave([...prefix,p[0]],left.map((q,j)=>i===j?q.slice(1):q));});}
interleave([],source.exercise.transactions.map(t=>t.operations.map(o=>o.id)));
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
   this.bytes+=Buffer.byteLength(event.data,"utf8");this.messages++;const m=JSON.parse(String(event.data));
   if(m.t==="state"){
    this.state=m;if(m.plugins?.error)errors.push(m.plugins.error);
    const d=this.descriptor(),v=d?.views["participant-input"]?.data;
    if(v&&v.phase!=='reveal'&&(v.own?.diagnosis?.feedback||v.own?.repair?.feedback||v.worked))errors.push('Premature feedback');
    if(v&&('roster'in v||'selected'in v||'binding'in v||'counts'in v))errors.push('Private view leaked');
    const own=v?.own?.[this.target?.field];
    if(this.target&&own?.version===this.target.version&&own.status==='saved'&&this.target.checked_ms===undefined){
     try{assert.deepEqual(own.answer,this.target.answer);}catch{errors.push('Latest answer mismatch');}
     this.target.checked_ms=now()-this.target.start;
    }
    if(v?.own?.repair?.status==='unavailable')errors.push('Evaluation unavailable');
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
 async submit(answer,phase,version,field=phase){
  const v=this.view().data;
  const row={phase,field,actor:this.index,version:version??(v.own?.[field]?.version||0)+1,start:now()};
  Object.defineProperty(row,"answer",{value:answer});
  rows.push(row);this.target=row;
  const envelope=this.envelope("submit-"+field,{phase_token:v.phase_token,answer_version:row.version-1,answer});
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
(async()=>{const controls=[],checks={};let log,browserHeap=null,browserVersion=null;try{
 base='http://127.0.0.1:'+await freePort();metrics=path.join(output,'server-events.jsonl');
 server=spawn(process.env.PYTHON||'python',[path.join(__dirname,'transaction_load_server.py'),'--bundle',bundle,'--data',fs.mkdtempSync(path.join(output,'profile-')),'--metrics',metrics,'--port',new URL(base).port],{windowsHide:true});
 log=fs.createWriteStream(path.join(output,'server.log'));server.stdout.pipe(log);server.stderr.pipe(log);
 await until(()=>fetch(base+'/api/status').then(r=>r.ok).catch(()=>false),'server',30000);
 browser=await pw[family].launch({headless:true});browserVersion=browser.version();const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.addInitScript(()=>{localStorage.setItem('texquiz:presenter-key','synthetic-load-key');window.loadWorkers=[];window.loadPeakHeap=null;setInterval(()=>{if(performance.memory)window.loadPeakHeap=Math.max(window.loadPeakHeap||0,performance.memory.usedJSHeapSize);},1000);const Native=window.Worker;window.Worker=class extends Native{
  constructor(url,...args){super(url,...args);this.probe=String(url).includes('plugin-evaluator-worker.js');if(this.probe)this.addEventListener('message',e=>{if(this.metric){window.loadWorkers.push({...this.metric,duration_ms:performance.now()-this.metric.start,status:e.data.result?.status||e.data.t});this.metric=null;}});}
  postMessage(m,...args){if(this.probe){if(m.t==='init')this.job=m.job.id;this.metric={job:this.job,kind:m.t,start:performance.now(),bytes:new TextEncoder().encode(JSON.stringify(m)).byteLength};}return super.postMessage(m,...args);}};});
 async function captureWorkers(){const sample=await page.evaluate(()=>({workers:window.loadWorkers,heap:window.loadPeakHeap}));workerTimes.push(...sample.workers);if(sample.heap)browserHeap=Math.max(browserHeap||0,sample.heap);}
 async function presenter(hold=false){
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));p.on('crash',()=>browserFailure='Presenter crashed');
  p.on('response',r=>{if(r.status()>=400)browserEvents.push({event:'http',path:new URL(r.url()).pathname,status:r.status()});});
  p.on('requestfailed',r=>browserEvents.push({event:'request-failed',path:new URL(r.url()).pathname,error:r.failure()?.errorText}));
  if(hold)await p.route('**/static/stage/plugin-evaluator-worker.js',()=>{});
  try{await p.goto(base+'/stage?bundle='+deck.bundle);await p.locator('#next').waitFor();}
  catch(e){
   // Synthetic profile only; preserve the visible error without recording keys.
   try{fs.writeFileSync(path.join(output,'presenter-open-failure.txt'),await p.locator('body').innerText({timeout:2000}));await p.screenshot({path:path.join(output,'presenter-open-failure.png'),timeout:2000});}catch{}
   throw e;
  }
  return p;
 }
 // Wait for acknowledged navigation: rapid clicks can arrive before the page
 // applies the preceding state, leaving a slow runner on the wrong lesson.
 await context.addInitScript(()=>{const Native=window.WebSocket;window.loadState=null;window.WebSocket=class extends Native{constructor(...args){super(...args);this.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.t==='state')window.loadState=m;});}};});
 page=await presenter();await until(()=>page.evaluate(()=>!!window.loadState?.session?.slide),'initial slide');
 for(let n=0;n<5;n++){
  const before=await page.evaluate(()=>window.loadState.session.slide);
  await page.locator('#next').click();
  await until(()=>page.evaluate(before=>window.loadState?.session?.slide!==before,before),'slide acknowledgement');
 }
 await until(()=>page.evaluate(item=>window.loadState?.plugins?.items?.some(d=>d.item===item),item),'chain activity');
 teacher=new Student('teacher');await teacher.connect({t:'hello',role:'host',key:'synthetic-load-key',deck:deck.deck,bundle:deck.bundle});
 async function control(op,payload={}){const start=now();const receipt=(await teacher.command(op,op==='_reset'?{}:{control_version:teacher.view().data.control_version,...payload})).receipt;assert(receipt.accepted);await until(()=>teacher.view().epoch>=receipt.epoch&&teacher.view().revision>=receipt.revision,'control projection');controls.push({operation:op,ms:now()-start});}
 async function advance(expected){await control('advance-phase');await until(()=>teacher.view().data.phase===expected,'phase '+expected);if(students.length)await until(()=>students.every(s=>s.view()?.data.phase===expected),'class phase '+expected);}
 await advance('predict');const pin=(await page.locator('#pin').innerText()).replace(/\D/g,'');
 for(let i=0;i<actors;i++)students.push(new Student(i));const joined=now();await Promise.all(students.map((s,i)=>s.connect({t:'join',pin,nickname:'Synthetic '+(i+1),join_nonce:randomBytes(16).toString('hex')})));phases.push({name:'join',duration_ms:now()-joined});console.log('Joined '+actors);
 async function batch(field,answer){const start=now();const batch=await Promise.all(students.map(async(s,i)=>{if(wave)await delay(wave*1000*i/actors);return s.submit(answer(i),field);}));await until(()=>batch.every(r=>r.checked_ms!==undefined),field+' checked');phases.push({name:field,duration_ms:now()-start,lastSubmitToDoneMs:now()-Math.max(...batch.map(r=>r.start))});console.log(field+' saved');return batch;}
 const prediction=await batch('prediction',i=>({values:Object.fromEntries(Object.entries(worked.original.final).map(([k,v])=>[k,i%3?v:0]))}));
 assert.deepEqual((await students[0].send({t:'plugin.command',command:prediction[0].envelope})).receipt,prediction[0].receipt);checks.receiptRetry=true;
 await advance('inspect');await control('seek-step',{cursor:4});await advance('diagnose');
 await batch('diagnosis',i=>i%2?worked.original.diagnosis:{edges:[],certificate:{kind:'serial',vertices:['T1','T2','T3']}});
 await advance('repair');const repaired=await batch('repair',i=>({order:orders[i%orders.length]}));
 const replacements=await Promise.all(students.slice(0,Math.ceil(actors/10)).map((s,i)=>s.submit({order:orders[(i+actors)%orders.length]},'replacement',undefined,'repair')));await until(()=>replacements.every(r=>r.checked_ms!==undefined),'replacements');checks.distinctRepairs=new Set(rows.filter(r=>r.field==='repair').map(r=>JSON.stringify(r.answer))).size;
 const returning=students[0],token=returning.welcome.token;await returning.close();await returning.connect({t:'resume',token});assert.equal(returning.view().data.own.repair.version,2);checks.reconnect=true;
 // A stale device cannot replace the accepted version.
 const conflict=await returning.command('submit-repair',{phase_token:returning.view().data.phase_token,answer_version:0,answer:{order:orders[0]}});assert.equal(conflict.receipt.accepted,false);checks.conflict=true;
 if(actors===1000){const extra=new Student('overflow');try{await assert.rejects(extra.connect({t:'join',pin,nickname:'Overflow',join_nonce:randomBytes(16).toString('hex')}),/^Error: full:/);}finally{await extra.close();}checks.ceiling=true;}
 // Hold a genuine lease, disconnect its evaluator, and finish after phase closure.
 await captureWorkers();await page.close();page=await presenter(true);
 const recover=await Promise.all(students.slice(0,Math.ceil(actors/10)).map((s,i)=>s.submit({order:orders[(i+31)%orders.length]},'recovery',undefined,'repair')));
 await until(()=>fs.readFileSync(metrics,'utf8').split('\n').filter(Boolean).map(JSON.parse).some(e=>e.event==='lease'&&e.jobs.some(j=>recover.some(r=>r.jobs.includes(j.id)))),'held lease');
 await advance('reveal');await page.close();page=await presenter();await until(()=>recover.every(r=>r.checked_ms!==undefined),'evaluator recovery');checks.evaluatorRecovery=true;
 for(const s of students){assert.equal(s.view().data.own.repair.status,'saved');assert.equal(s.state.me.score,0);assert.equal(typeof s.view().data.own.repair.feedback.correct,'boolean');}checks.noPoints=true;
 await control('roster-page',{page:Math.floor((actors-1)/25)});assert.equal(teacher.view().data.roster.rows.at(-1).number,actors);
 const sid=teacher.welcome.session,headers={'X-Texquiz-Key':'synthetic-load-key'};
 const privateExport=await (await fetch(base+'/api/archive/'+sid+'/plugins.json',{headers})).json();assert.equal(privateExport.actor_records.length,actors);
 const publicExport=await (await fetch(base+'/api/archive/'+sid+'/plugins-public.json',{headers})).json();assert(publicExport.items.find(x=>x.item===item).snapshot.data.worked);assert(!JSON.stringify(publicExport).includes('"actor"'));checks.archives=true;
 await control('_reset');await until(()=>students.every(s=>s.view().epoch===2&&!s.view().data.own),'reset');checks.reset=true;
 await captureWorkers();assert.deepEqual(errors,[]);
 }catch(e){failure=String(e.stack);console.error(failure);}
 finally{await Promise.all(students.map(s=>s.close()));await teacher?.close();await browser?.close();if(server&&server.exitCode===null){server.stdin.end('stop\n');await Promise.race([new Promise(r=>server.once('exit',r)),delay(10000)]);if(server.exitCode===null)server.kill();}if(log)await new Promise(r=>log.end(r));
 const events=fs.existsSync(metrics)?fs.readFileSync(metrics,'utf8').split('\n').filter(Boolean).map(JSON.parse):[],groups={};
 for(const name of new Set(rows.map(r=>r.phase))){const group=rows.filter(r=>r.phase===name);groups[name]={count:group.length,accepted:group.filter(r=>r.accepted).length,acknowledgement:summary(group.map(r=>r.ack_ms)),completion:summary(group.map(r=>r.checked_ms))};}
 const ack=summary(rows.map(r=>r.ack_ms)),healthy=phases.find(p=>p.name==='repair');
 const controlSummary=summary(controls.map(r=>r.ms));
 const gates={ackP95:ack.n>0&&ack.p95_ms<=(actors<=600?2000:3000),ackMaximum:ack.n>0&&ack.max_ms<=(actors<=600?5000:10000),repairDrain:healthy?.lastSubmitToDoneMs<=(actors<=600?60000:120000),controlsP95:controlSummary.n>0&&controlSummary.p95_ms<=(actors<=600?1000:2000),controlsMaximum:controlSummary.n>0&&controlSummary.max_ms<=(actors<=600?3000:5000),correctness:!failure&&!errors.length};
 const queued=new Map(),queueWait=[],retries=[];for(const e of events){if(e.event==='command')for(const id of Object.values(e.receipt?.jobs||{}))queued.set(id,e.ms);if(e.event==='lease')for(const j of e.jobs){if(queued.has(j.id))queueWait.push(e.ms-queued.get(j.id));if(j.generation>1)retries.push(j.id);}}
 report={byteMetricUnit:'UTF-8 serialized payload bytes (not transport overhead)',actors,family,browserVersion,wave_seconds:wave,serverPeakRSS:fs.existsSync(metrics.replace(/\.jsonl$/,'.memory.json'))?JSON.parse(fs.readFileSync(metrics.replace(/\.jsonl$/,'.memory.json'),'utf8')).server_peak_rss_bytes:null,browserPeakJSHeapBytes:browserHeap,syntheticClientRSS:process.memoryUsage().rss,queueWait:summary(queueWait),retryLeases:retries.length,os:os.platform(),cpus:os.cpus()[0]?.model,totalMemory:os.totalmem(),groups,phases,controls,checks,gates,errors,failure,hook:summary(events.filter(e=>e.event==='hook').map(e=>e.duration_ms)),worker:summary(workerTimes.filter(w=>w.kind==='eval').map(w=>w.duration_ms)),workerIPCBytes:workerTimes.reduce((n,w)=>n+w.bytes,0),projectionBytes:students.reduce((n,s)=>n+s.bytes,0)};
 report.acknowledgement=ack;report.controlLatency=controlSummary;report.browserEvents=browserEvents;
 fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({actors,family,gates,ack,repairDrainMs:healthy?.lastSubmitToDoneMs}));if(failure||Object.values(gates).includes(false))process.exitCode=1;
 }
})().catch(e=>{console.error(e);process.exitCode=1;});

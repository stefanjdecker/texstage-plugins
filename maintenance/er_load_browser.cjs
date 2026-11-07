// SPDX-License-Identifier: Apache-2.0
// Synthetic protocol clients + the real presenter evaluator. This is not a
// measurement of 600 rendered physical phones or an internet deployment.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),os=require("node:os"),{spawn,spawnSync}=require("node:child_process");
const pw=require("playwright"),bundle=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);
const count=Number(process.env.ER_LOAD_ACTORS||600),family=process.env.BROWSER||"chromium";
assert(Number.isInteger(count)&&count>=1&&count<=600);
fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const seed=JSON.parse(fs.readFileSync(path.join(__dirname,"../examples/er-decisions/activities/registrations.json")));
const port=Number(process.env.TEXSTAGE_TEST_PORT||18802),base="http://127.0.0.1:"+port;
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,
 "--data",fs.mkdtempSync(path.join(output,"profile-")),"--port",String(port)],{windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let browser;
 const errors=[];
 try{
  for(let i=0;i<150;i++){try{if((await fetch(base+"/api/status")).ok)break;}catch{}await delay(100);}
  browser=await pw[family].launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1100}});
  await context.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  let presenter=await context.newPage();presenter.on("pageerror",e=>errors.push(e.message));
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  await presenter.getByRole("button",{name:"Open answers",exact:true}).waitFor();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  // Node protocol peers avoid a single browser's per-origin WebSocket ceiling.
  // The presenter and its restricted evaluator still run in the real browser.
  globalThis.location=new URL(base);
  globalThis.erLoadPresenter=async action=>{
    if(action==="pause"){await presenter.close();return;}
    assert.equal(action,"resume");
    presenter=await context.newPage();presenter.on("pageerror",e=>errors.push(e.message));
    await presenter.goto(base+"/stage?bundle="+deck.bundle);
    await presenter.locator(".presenter-controls").waitFor();
  };
  globalThis.erLoadProgress=value=>{
    fs.writeFileSync(path.join(output,"progress.json"),JSON.stringify(value,null,2));
    console.log(JSON.stringify(value));
  };
  const run=async({deck,pin,count,answers,recoveryEnabled})=>{
   const source=await (await fetch(base+"/static/shared/client.js")).text();
   const {Client}=await import("data:text/javascript;base64,"+Buffer.from(source).toString("base64"));
   const peers=[],all=[],violations=[];let request=0,samples=0,maxStateBytes=0;
   const wait=async(fn,label,ms=240000)=>{
    const until=performance.now()+ms;
    while(!fn()){if(performance.now()>until)throw Error("Timed out: "+label);await new Promise(r=>setTimeout(r,25));}
   };
   const deadline=async(promise,label)=>{
    let timer;
    try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error("Timed out: "+label)),180000);})]);}
    finally{clearTimeout(timer);}
   };
   const connect=async(login,role)=>{
    const row={state:null,role,measurement:null};
    const c=row.client=new Client({onState:m=>{
      row.state=m;
      const item=m.plugins?.items?.[0],view=item?.views["participant-input"]?.data;
      if(role==="participant"&&item){
       samples++;maxStateBytes=Math.max(maxStateBytes,new TextEncoder().encode(JSON.stringify(item)).length);
       if((view?.phase!=="revealed"&&(view?.own?.feedback||view?.teaching||Number.isInteger(view?.own?.points)))||view?.participants||view?.selected)violations.push("private-or-unrevealed");
       const v=row.measurement;
       if(v&&view?.own?.version===v.version&&view.own.status!=="pending"&&v.finished===null){
        v.finished=performance.now();v.status=view.own.status;
       }
      }
    }});
    all.push(c);row.welcome=await deadline(c.login(login),"login");
    await wait(()=>row.state?.plugins?.items?.length,"initial state");
    return row;
   };
   const item=row=>row.state.plugins.items[0];
   const projection=(row,surface)=>item(row).views[surface];
   const send=async(row,surface,op,payload,existing)=>{
    const v=projection(row,surface);
    const command=existing||{type:item(row).type,item:item(row).item,operation:op,payload,
      epoch:v.epoch,expected_revision:v.revision,request_id:"load_"+String(++request).padStart(10,"0")};
    const reply=await row.client.send({t:"plugin.command",command});
    return {reply,command};
   };
   const good=reply=>{if(!reply.receipt?.accepted)throw Error("Command refusal: "+JSON.stringify(reply));};
   const stats=values=>{const v=[...values].sort((a,b)=>a-b);return {min:v[0],median:v[Math.ceil(v.length*.5)-1],p95:v[Math.ceil(v.length*.95)-1],max:v.at(-1)};};
   try{
    const teacherLogin={t:"hello",role:"stage",key:"plugin-demo-key",deck:deck.deck,bundle:deck.bundle};
    let teacher=await connect(teacherLogin,"presenter");
    const control=()=>projection(teacher,"presenter-controls").data;
    // Join before measurement. The first wave is cold browser evaluation, not
    // cold Python startup: the host has already produced these initial views.
    for(let i=0;i<count;i++){
     peers.push(await deadline(connect({t:"join",pin,nickname:"Load "+String(i+1).padStart(2,"0")},"participant"),"join"));
     if((i+1)%8===0)await globalThis.erLoadProgress({joined:i+1,total:count});
    }
    const c=control().control_version;good((await send(teacher,"presenter-controls","open",{control_version:c})).reply);
    await wait(()=>peers.every(p=>projection(p,"participant-input").data.phase==="open"),"open");
    const maximum=item(peers[0]).public.points||0,points=[];
    const key=choices=>JSON.stringify([...choices].sort());
    const accepted=new Set(seed.solutions.map(s=>key(s.answer.choices)));
    const publishAndCheck=async offset=>{
     const before=performance.now();
     good((await send(teacher,"presenter-controls","close",{control_version:control().control_version})).reply);
     await wait(()=>control().phase==="closed","close before points");
     const publication=await send(teacher,"presenter-controls","reveal",{control_version:control().control_version});
     good(publication.reply);
     const expected=peers.map((_,i)=>accepted.has(key(answers[(i+offset)%answers.length].choices))?maximum:0);
     await wait(()=>peers.every((p,i)=>projection(p,"participant-input").data.phase==="revealed"&&
       p.state.me.score===expected[i]&&projection(p,"participant-input").data.own.points===expected[i]),"released scores and own awards");
     good((await send(teacher,"presenter-controls","reveal",{},publication.command)).reply);
     const refusal=await send(teacher,"presenter-controls","open",{control_version:control().control_version});
     assertLocal(!refusal.reply.receipt.accepted&&refusal.reply.receipt.error==="reset-required","scored round cannot reopen");
     points.push({maximum,actors:count,correct:expected.filter(n=>n>0).length,publication_ms:performance.now()-before,
       all_totals_match:true,replay_idempotent:true,reopen_refused:true});
    };
    const waves=[];
    for(const [waveIndex,label]of ["cold-evaluation","warm-replacement"].entries()){
     const started=performance.now();let lastSent=started;
     const pending=peers.map((row,index)=>{
      const d=projection(row,"participant-input").data,version=(d.own?.version||0)+1;
      const choice=answers[(index+waveIndex)%answers.length].choices;
      row.measurement={actor:index,version,sent:performance.now(),ack:null,finished:null,status:null};
      lastSent=row.measurement.sent;
      return send(row,"participant-input","submit",{phase_version:d.phase_version,answer_version:version-1,choices:choice})
       .then(({reply,command})=>{good(reply);row.measurement.ack=performance.now();row.lastCommand=command;});
     });
     await deadline(Promise.all(pending),label+" acknowledgements");
     await wait(()=>peers.every(p=>p.measurement.finished!==null),label);
     await wait(()=>control().counts.correct+control().counts.incorrect===count&&control().counts.pending===0,"teacher result count");
     assertLocal(!maximum||peers.every(p=>p.state.me.score===0),"no points before reveal");
     const rows=peers.map(p=>({...p.measurement}));
     const report={label,actors:count,send_window_ms:lastSent-started,
      acknowledged_ms:stats(rows.map(v=>v.ack-v.sent)),evaluated_ms:stats(rows.map(v=>v.finished-v.sent)),
      elapsed_ms:performance.now()-started,versions:rows.map(r=>r.version),unavailable:rows.filter(r=>r.status!=="saved").length,
      rows:rows.map(r=>({actor:r.actor,version:r.version,ack_ms:r.ack-r.sent,evaluated_ms:r.finished-r.sent,status:r.status}))};
     report.target_pass=report.evaluated_ms.p95<=10000&&report.evaluated_ms.max<=30000;
     waves.push(report);
     await globalThis.erLoadProgress({wave:label,evaluated_ms:report.evaluated_ms,target_pass:report.target_pass});
    }
    let recovery=null;
    if(recoveryEnabled){
     if(maximum)await publishAndCheck(1);
     // Stop evaluation, then simulate a presenter connection disappearing
     // after leasing two jobs. Keep the real 120-second lease policy.
     good((await send(teacher,"presenter-controls","_reset",{})).reply);
     await wait(()=>peers.every(p=>!projection(p,"participant-input").data.own),"reset clears saved answers");
     await wait(()=>projection(teacher,"presenter-controls").epoch===projection(peers[0],"participant-input").epoch,"presenter observes reset epoch");
     if(maximum)await wait(()=>peers.every(p=>p.state.me.score===0),"reset withdraws points");
     good((await send(teacher,"presenter-controls","open",{control_version:control().control_version})).reply);
     await wait(()=>peers.every(p=>projection(p,"participant-input").data.phase==="open"),"reopen after reset");
     await globalThis.erLoadPresenter("pause");
     await Promise.all(peers.map(async(row,index)=>{
      const d=projection(row,"participant-input").data;
      row.measurement={actor:index,version:(d.own?.version||0)+1,sent:performance.now(),ack:null,finished:null,status:null};
      good((await send(row,"participant-input","submit",{phase_version:d.phase_version,
        answer_version:d.own?.version||0,choices:answers[index%answers.length].choices})).reply);
     }));
     await wait(()=>control().counts.pending===count,"queued without evaluator");
     const {jobs}=await teacher.client.send({t:"plugin.work"});
     assertLocal(jobs.length===Math.min(2,count),"bounded abandoned lease");
     const leasedAt=performance.now();teacher.client.close();
     teacher=await connect(teacherLogin,"presenter");
     await globalThis.erLoadProgress({recovery:"checking disconnect requeue with unchanged lease fallback",abandoned_jobs:jobs.length});
     await globalThis.erLoadPresenter("resume");
     await wait(()=>control().counts.correct+control().counts.incorrect>=count-jobs.length,"remaining queue makes progress",60000);
     const unleasedMs=performance.now()-leasedAt;
     await wait(()=>peers.every(p=>p.measurement.finished!==null)&&control().counts.pending===0,"expired leases recovered",150000);
     recovery={reset_before_recovery:true,abandoned_jobs:jobs.length,actors:count,unleased_jobs_completed_ms:unleasedMs,
       all_completed_ms:performance.now()-leasedAt,all_saved:peers.every(p=>p.measurement.status==="saved"),
       versions:peers.map(p=>p.measurement.version),lease_policy_seconds:120};
     assertLocal(recovery.all_saved,"all recovered outcomes available");
     await globalThis.erLoadProgress({recovery});
    }
    // Replaying an already accepted envelope must not append another version.
    const before=projection(peers[0],"participant-input").data.own.version;
    good((await send(peers[0],"participant-input","submit",{},peers[0].lastCommand)).reply);
    await new Promise(r=>setTimeout(r,100));
    assertLocal(projection(peers[0],"participant-input").data.own.version===before,"receipt replay");
    let capacity=null;
    if(count===600){
     const extra=await connect({t:"join",pin,nickname:"Capacity probe"},"participant");
     const d=projection(extra,"participant-input").data;
     const {reply}=await send(extra,"participant-input","submit",{phase_version:d.phase_version,answer_version:0,choices:answers[0].choices});
     assertLocal(!reply.receipt.accepted&&reply.receipt.error==="capacity","601st actor refusal");
     capacity={refused:true,code:reply.receipt.error};
    }
    if(maximum)await publishAndCheck(recoveryEnabled?0:1);
    assertLocal(!violations.length,"public role privacy");
    assertLocal(waves.every(w=>w.unavailable===0),"all outcomes available");
    return {waves,recovery,capacity,points,receiptReplay:true,privacy:true,state_samples:samples,max_participant_view_utf8_bytes:maxStateBytes,
      target_pass:waves[1].target_pass,measurement:"Protocol clients; latency from each send to observed saved status, before feedback reveal."};
   }finally{for(const c of all)c.close();}
   function assertLocal(ok,label){if(!ok)throw Error(label);}
  };
  const result=await run({deck,pin,count,answers:seed.exercise.decisions.reduce((rows,d)=>rows.flatMap(a=>d.options.map(o=>({choices:[...a.choices,[d.id,o.id]]}))),[{choices:[]}]),recoveryEnabled:process.env.ER_LOAD_RECOVERY==="1"});
  assert.deepEqual(errors,[]);
  const report={date:new Date().toISOString(),browser:family,browser_version:browser.version(),node:process.version,
    platform:os.platform(),cpu:os.cpus()[0]?.model,logical_cpus:os.cpus().length,total_memory_bytes:os.totalmem(),
    bundle:deck.bundle,provider:deck.plugins,answer_combinations:seed.exercise.decisions.reduce((n,d)=>n*d.options.length,1),result,page_errors:errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({...report,result:{...result,waves:result.waves.map(({rows,...rest})=>rest)}}));
  if(process.env.ER_REQUIRE_LOAD_TARGETS==="1"&&!result.target_pass)process.exitCode=2;
 }catch(e){fs.writeFileSync(path.join(output,"failure.json"),JSON.stringify({error:e.stack,page_errors:errors},null,2));throw e;}
 finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{
 // Windows venv launchers may have an interpreter child; stop only our tree.
 if(process.platform==="win32")spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});
 else server.kill();
 log.end();
});


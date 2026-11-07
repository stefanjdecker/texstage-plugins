// SPDX-License-Identifier: Apache-2.0
// B3 protocol through authenticated sockets and the actual host engine evaluator.
// These scripted submissions do not claim a completed visual phone editor.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn} = require("node:child_process");
const pw = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, ".."), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || "chromium";
const output = path.resolve(process.argv[3] || "artifacts/bplus-classroom", family);
fs.mkdirSync(output, {recursive:true});
const deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
const profile = fs.mkdtempSync(path.join(output, "profile-"));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, label) {
  for (let i=0; i<200; i++) {if (await fn()) return; await delay(100);}
  throw Error("Timed out: " + label);
}
async function freePort() {
  const server = require("node:net").createServer();
  return new Promise((resolve,reject) => {
    server.once("error",reject); server.listen(0,"127.0.0.1",() => {
      const port=server.address().port; server.close(error => error ? reject(error) : resolve(port));
    });
  });
}
function instrumentation() {
  const Native=window.WebSocket;
  window.bplusState=null; window.bplusSequence=0;
  window.WebSocket=class extends Native {
    constructor(...args) {super(...args); window.bplusSocket=this;
      this.addEventListener("message",event => {const m=JSON.parse(event.data); if(m.t==="state") window.bplusState=m;});
    }
  };
  window.bplusSend=message => new Promise((resolve,reject) => {
    const socket=window.bplusSocket, id="b3-test-"+(++window.bplusSequence);
    const onmessage=event => {
      const m=JSON.parse(event.data); if(m.re===id) {
        clearTimeout(timer); socket.removeEventListener("message",onmessage); resolve(m);
      }
    };
    const timer=setTimeout(() => {socket.removeEventListener("message",onmessage); reject(Error("receipt timeout"));},10000);
    socket.addEventListener("message",onmessage); socket.send(JSON.stringify({...message,id}));
  });
}
let item="lookup", request=0;
async function descriptor(page) {return page.evaluate(item => window.bplusState?.plugins?.items?.find(d => d.item===item),item);}
async function data(page) {
  const d=await descriptor(page);
  return d && (d.views["presenter-controls"] || Object.values(d.views)[0])?.data;
}
async function envelope(page,operation,payload) {
  const d=await descriptor(page), v=Object.values(d.views)[0];
  return {type:d.type,item,operation,payload,request_id:"bplus"+String(++request).padStart(10,"0"),
    epoch:v.epoch,expected_revision:v.revision};
}
async function send(page,command) {return page.evaluate(command => window.bplusSend({t:"plugin.command",command}),command);}
async function accepted(page,command) {
  const result=await send(page,command);
  assert.equal(result.receipt?.accepted,true,JSON.stringify(result));
  // Receipt and view arrive independently, particularly in WebKit.
  await until(async () => {
    const d=await descriptor(page),v=d&&Object.values(d.views)[0];
    return v && v.epoch===result.receipt.epoch && v.revision>=result.receipt.revision;
  },"committed projection");
  return result.receipt;
}
async function control(page,op,payload={}) {
  return accepted(page,await envelope(page,op,{control_version:(await data(page)).control_version,...payload}));
}
let server,log;
(async () => {
  let browser;
  const pages=[],errors=[];
  try {
    const port=await freePort(),base="http://127.0.0.1:"+port;
    server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),
      "--bundle",bundle,"--data",profile,"--port",String(port)],{windowsHide:true});
    log=fs.createWriteStream(path.join(output,"server.log")); server.stdout.pipe(log); server.stderr.pipe(log);
    await until(() => {
      if(server.exitCode!==null) throw Error("Test server exited");
      return fetch(base+"/api/status").then(r=>r.ok).catch(()=>false);
    },"server");
    browser=await pw[family].launch({headless:true,...(family==="chromium"&&process.env.TEXSTAGE_BROWSER_CHANNEL
      ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
    async function context(options={}) {
      const c=await browser.newContext(options); await c.addInitScript(instrumentation); return c;
    }
    function watch(page) {pages.push(page); page.on("pageerror",e=>errors.push(e.message)); return page;}
    const desktop=await context({viewport:{width:1440,height:1000}});
    await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
    const presenter=watch(await desktop.newPage()); await presenter.goto(base+"/stage?bundle="+deck.bundle);
    await presenter.locator("#next").click();
    await until(async()=>!!await data(presenter),"first exercise");
    const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
    const projector=watch(await desktop.newPage()); await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
    await until(async()=>!!await data(projector),"projector");
    const mobile=await context({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
    const phone=watch(await mobile.newPage()); await phone.goto(base+"/play?pin="+pin);
    await phone.locator("#nick").fill("Alice"); await phone.locator("#join button[type=submit]").click();
    await until(async()=>!!await data(phone),"Alice");
    const same=await context({storageState:await mobile.storageState(),viewport:{width:390,height:844}});
    const second=watch(await same.newPage()); await second.goto(base+"/play?pin="+pin);
    await until(async()=>!!await data(second),"same actor");
    const other=await context({viewport:{width:390,height:844}});
    const bob=watch(await other.newPage()); await bob.goto(base+"/play?pin="+pin);
    await bob.locator("#nick").fill("Bob"); await bob.locator("#join button[type=submit]").click();
    await until(async()=>!!await data(bob),"Bob");
    for(const name of ["lookup","range","insert","delete"]) {
      if(name!==item) {await presenter.locator("#next").click(); item=name;}
      await until(async()=>!!await data(presenter)&&!!await data(phone)&&!!await data(bob),"task "+name);
      const source=JSON.parse(fs.readFileSync(path.join(root,"examples/bplus/activities",name+".json")));
      const answer=source.worked.answer,wrong=structuredClone(answer);
      if("height" in wrong) wrong.height=3; else wrong.keys=[];
      const oldControl=await envelope(presenter,"close",{control_version:0});
      await control(presenter,"open");
      await until(async()=>(await data(phone))?.phase==="open","open "+name);
      const firstCommand=await envelope(phone,"submit-answer",{phase_version:1,answer_version:0,answer});
      const receipt=await accepted(phone,firstCommand);
      assert.deepEqual(await accepted(phone,firstCommand),receipt);
      const stale=await send(second,{...firstCommand,request_id:"bplus"+String(++request).padStart(10,"0")});
      assert.equal(stale.receipt.error,"stale-answer");
      await accepted(bob,await envelope(bob,"submit-answer",{phase_version:1,answer_version:0,answer:wrong}));
      await until(async()=>(await data(presenter))?.counts.saved===2,"actual browser evaluations "+name);
      assert(!(await data(phone)).own.feedback && !(await data(bob)).own.feedback);
      assert.deepEqual((await data(phone)).own.answer,answer);
      assert.equal((await send(presenter,oldControl)).receipt.error,"stale-control");
      let selected;
      for(const row of (await data(presenter)).participants) {
        await control(presenter,"select-answer",{actor:row.actor,answer_version:row.version});
        if((await data(presenter)).selected.feedback.correct===false) {selected=row; break;}
      }
      assert(selected);
      assert(!(await data(projector)).selected && !(await data(projector)).demonstration);
      await control(presenter,"close");
      await control(presenter,"share-answer",{actor:selected.actor,answer_version:selected.version});
      await control(presenter,"replay-step",{source:"shared",step:0});
      await until(async()=>!!(await data(projector))?.replay,"shared prediction "+name);
      assert.deepEqual((await data(projector)).demonstration,{answer:wrong});
      for(const page of [phone,bob,projector]) {
        const text=JSON.stringify(await descriptor(page));
        for(const hidden of ['"private":','"worked":','"correlation":','"evaluations":','"selected":','"participants":','"feedback":'])
          assert(!text.includes(hidden),"unrevealed leak "+hidden);
        assert(!text.includes(selected.actor),"private actor digest");
      }
      await control(presenter,"clear-share");
      await control(presenter,"open");
      await until(async()=>(await data(phone))?.phase_version===3,"reopened");
      await accepted(phone,await envelope(phone,"submit-answer",{phase_version:3,answer_version:1,answer}));
      await until(async()=>(await data(phone))?.own.status==="saved","replacement checked");
      await control(presenter,"close"); await control(presenter,"reveal");
      await until(async()=>(await data(phone))?.own.feedback?.correct===true,"released feedback");
      await until(async()=>(await data(bob))?.own.feedback?.correct===false,"released wrong prediction");
      await control(presenter,"replay-step",{source:"worked",step:0});
      await until(async()=>(await data(projector))?.replay?.source==="worked","worked replay");
      const projected=await data(projector);
      assert(projected.worked && !projected.selected && !projected.own && !projected.participants);
      const reopen=await send(presenter,await envelope(presenter,"open",{control_version:(await data(presenter)).control_version}));
      assert.equal(reopen.receipt.error,"reset-required");
      const reset=await envelope(presenter,"_reset",{});
      const resetReceipt=await accepted(presenter,reset);
      assert.equal(resetReceipt.epoch,2); assert.deepEqual(await accepted(presenter,reset),resetReceipt);
      const race=await send(presenter,{...reset,request_id:"bplus"+String(++request).padStart(10,"0")});
      assert.equal(race.receipt.error,"stale-epoch");
      await until(async()=>(await data(phone))?.phase==="introduce"&&!(await data(phone))?.own,"reset");
    }
    assert.equal((await send(phone,await envelope(phone,"open",{control_version:0}))).t,"error");
    await control(presenter,"open");
    await presenter.locator("#next").click();
    await until(async()=>!(await descriptor(phone)),"leave delete");
    await presenter.locator("#prev").click();
    await until(async()=>(await data(phone))?.phase==="closed","return keeps closed");
    assert.deepEqual(errors,[]);
    const report={browser:family,version:browser.version(),operations:["lookup","range","insert","delete"],
      actualEvaluator:true,twoActors:true,sameActorDevices:true,receiptRetry:true,staleControl:true,
      privateInspection:true,predictionOnlySharing:true,feedbackRelease:true,replacement:true,reset:true,
      replay:true,navigation:true,pageErrors:errors,scope:"Classroom protocol regression; visual editing covered separately"};
    fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report));
  } catch(error) {
    for(let i=0;i<pages.length;i++)
      fs.writeFileSync(path.join(output,"failure-"+i+".json"),JSON.stringify(await pages[i].evaluate(()=>window.bplusState).catch(()=>null),null,2));
    throw error;
  } finally {await browser?.close();}
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;}).finally(async()=>{
  if(server&&server.exitCode===null) {const exited=new Promise(resolve=>server.once("exit",resolve));server.kill();await exited;}
  log?.end();
});

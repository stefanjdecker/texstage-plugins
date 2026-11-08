// SPDX-License-Identifier: Apache-2.0
// Installed-wheel rehearsal; LANGUAGE=en|de. Browser locale intentionally differs by default.
const fs=require("node:fs"),path=require("node:path"),{spawn}=require("node:child_process");
const pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright"),family=process.env.BROWSER||"chromium";
const example=__dirname, root=path.resolve(example,"../..");
const language=process.env.LANGUAGE||"en",de=language==="de";
if (!["en","de"].includes(language)) throw Error("LANGUAGE must be en or de");
const locale=process.env.BROWSER_LOCALE||(de?"en-GB":"de-DE");
const port=Number(process.env.TEXSTAGE_TEST_PORT||18811),base="http://127.0.0.1:"+port,key="plugin-demo-key";
const stem=de?"database-de":"database";
const bundle=path.join(example,"texquiz-out",stem+".bundle");
const output=path.join(example,"texquiz-out/browser-tests",language+"-"+family+"-"+locale);fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json"),"utf8"));
if(deck.language!==language)throw Error("Bundle language mismatch; rebuild with matching master and sidecar");
const server=spawn(process.env.PYTHON||"python",[path.join(root,"maintenance/serve_lesson.py"),"--bundle",bundle,"--data",fs.mkdtempSync(path.join(output,"profile-")),"--port",String(port)],{windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));
server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser,control;const watched=[];
(async()=>{
  let ready=false;
  for(let i=0;i<60;i++){
    if(server.exitCode!==null)throw Error("Review server exited");
    try{ready=(await fetch(base+"/api/status",{signal:AbortSignal.timeout(500)})).ok;}catch{}
    if(ready)break;await delay(250);
  }
  if(!ready)throw Error("Review server did not start");
  browser=await pw[family].launch({headless:true});
  const ctx=await browser.newContext({viewport:{width:1440,height:1000},locale});
  await ctx.addInitScript(k=>localStorage.setItem("texquiz:presenter-key",k),key);
  const presenter=await ctx.newPage(), errors=[];watched.push(["presenter",presenter]);
  presenter.on("pageerror",e=>errors.push(e.message));
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  await presenter.locator("#next").waitFor();
  await presenter.waitForFunction(()=>document.querySelector("#pin").innerText.replace(/\D/g,"").length>=4);
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:family!=="firefox",hasTouch:true,locale});
  const phone=await mobile.newPage();watched.push(["phone",phone]);phone.on("pageerror",e=>errors.push(e.message));
  await phone.goto(base+"/play?pin="+pin);
  await phone.locator("#nick").fill("Database learner");
  await phone.locator("#join button[type=submit]").click();
  const mobile2=await browser.newContext({viewport:{width:390,height:844},isMobile:family!=="firefox",hasTouch:true,locale});
  const phone2=await mobile2.newPage();phone2.on("pageerror",e=>errors.push(e.message));
  await phone2.goto(base+"/play?pin="+pin);
  await phone2.locator("#nick").fill("Second learner");
  await phone2.locator("#join button[type=submit]").click();
  const projector=await ctx.newPage();watched.push(["projector",projector]);projector.on("pageerror",e=>errors.push(e.message));
  await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  control=new WebSocket(base.replace("http","ws")+"/ws");
  await new Promise((resolve,reject)=>{control.addEventListener("open",resolve,{once:true});control.addEventListener("error",reject,{once:true});});
  const pending=new Map();let seq=0;
  control.addEventListener("message",e=>{
    const m=JSON.parse(e.data);if(pending.has(m.re)){
      const {resolve,reject}=pending.get(m.re);pending.delete(m.re);
      if(m.t==="error")reject(Error(JSON.stringify(m)));else resolve(m);
    }
  });
  const send=message=>new Promise((resolve,reject)=>{
    const id="review-"+(++seq);
    const timer=setTimeout(()=>{pending.delete(id);reject(Error("Command timeout: "+message.t));},10000);
    pending.set(id,{resolve:m=>{clearTimeout(timer);resolve(m);},reject:e=>{clearTimeout(timer);reject(e);}});
    control.send(JSON.stringify({...message,id}));
  });
  await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error("No control welcome")),10000);
    const welcome=e=>{
      const m=JSON.parse(e.data);
      if(m.t==="welcome"){clearTimeout(timer);control.removeEventListener("message",welcome);resolve(m);}
      if(m.t==="error"){clearTimeout(timer);reject(Error(JSON.stringify(m)));}
    };
    control.addEventListener("message",welcome);
    control.send(JSON.stringify({t:"hello",role:"stage",key,deck:deck.deck,bundle:deck.bundle}));
  });
  const checked=[];
  for(const [id,activity] of (process.env.PLUGIN_ONLY ? [] : Object.entries(deck.items.activity))){
    console.log("Checking "+id);
    const slide=deck.slides.find(s=>(s.live||[]).some(b=>b.type==="activity"&&b.item===id));
    if(!slide)throw Error("No live slide for "+id);
    await send({t:"slide",slide:slide.id});
    if(activity.input!=="code"){
      if(activity.open==="manual")await send({t:"activity.open",activity:id});
      await phone.locator('input[data-field="0"]').waitFor();
      await phone.waitForFunction(n=>document.querySelectorAll('input[data-field]').length===n,activity.fields.length);
      const fields=id==="crowd-facts"?["Ada","borrows","Database Basics"]:["Database Basics","databases"];
      async function submitTuple(p){
        for(let i=0;i<fields.length;i++)await p.locator('input[data-field="'+i+'"]').fill(fields[i]);
        await p.locator('form.act button[type=submit]').click();
        await p.locator('[data-role=mine] li:not(.empty)').waitFor();
      }
      await submitTuple(phone);
      let picture=(await send({t:"activity.view",activity:id})).picture;
      if(picture.edges.length!==0)throw Error("Graph shown before review or agreement");
      if(id==="crowd-facts"){
        for(const term of picture.terms)await send({t:"activity.approve",activity:id,role:term.role,term:term.key,on:true});
      }else await submitTuple(phone2);
      picture=(await send({t:"activity.view",activity:id})).picture;
      if(picture.edges.length!==1)throw Error("Expected one accepted graph edge");
      checked.push({id,fields:activity.fields.length,graphGatePassed:true});continue;
    }
    await send({t:"activity.open",activity:id});
    const suffix=activity.engine==="sql"?".sql":activity.engine==="sparql"?".rq":".ttl";
    await phone.locator("#act-text").fill(fs.readFileSync(path.join(example,"answers",id+suffix),"utf8"));
    await phone.locator("form:has(#act-text) button[type=submit]").click();
    await phone.locator(".actstate.ok").waitFor({timeout:15000});
    await send({t:"activity.close",activity:id});
    await send({t:"activity.reveal",activity:id});
    await phone.locator(".actstate .good").waitFor({timeout:15000});
    await presenter.locator(".tq-cluster.tq-ref").first().waitFor();
    await projector.locator(".tq-cluster.tq-ref").first().waitFor();
    checked.push({id,engine:activity.engine,referenceMatched:true});
    if(["sql-count","turtle-one"].includes(id)){
      await phone.screenshot({path:path.join(output,"phone-"+id+".png"),fullPage:true});
      await presenter.screenshot({path:path.join(output,"presenter-"+id+".png"),fullPage:true});
      await projector.screenshot({path:path.join(output,"projector-"+id+".png"),fullPage:true});
    }
  }

  const index=JSON.parse(fs.readFileSync(path.join(example,"activity-index.json")));
  const pluginChecked=[];
  const selectedScreens=new Set();
  const controls=presenter.locator(".presenter-controls");
  async function until(check,label,ms=20000){const start=Date.now();while(Date.now()-start<ms){if(await check())return;await delay(100);}throw Error("Timeout: "+label);}
  const latest={};
  for(const [role,page] of [["phone",phone],["projector",projector],["presenter",presenter]]){
    page.on("websocket",s=>s.on("framereceived",({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==="state")latest[role]=m;}catch{}}));
  }
  // Existing page websocket listeners need to be attached to the live sockets as well.
  // Reload once before the plugin section; persisted login reconnects the synthetic learner.
  await Promise.all([phone.reload(),projector.reload(),presenter.reload()]);
  await presenter.locator("#next").waitFor();
  for(const entry of [index.coordinate,...index.prepared]){
    console.log("Start plugin "+entry.id);
    const slide=deck.slides.find(s=>(s.live||[]).some(b=>b.type===entry.type&&b.item===entry.id));
    if(!slide)throw Error("Missing plugin slide "+entry.id);
    // Exercise lifecycle between each example, and wait for acknowledged navigation.
    await send({t:"slide",slide:deck.slides[0].id});
    await phone.locator(".participant-input").waitFor({state:"detached"});
    await send({t:"slide",slide:slide.id});
    await until(()=>latest.phone?.plugins?.items?.some(d=>d.item===entry.id),"phone state "+entry.id);
    await phone.locator(".participant-input").waitFor();
    await until(()=>["presenter","projector"].every(role=>latest[role]?.plugins?.items?.some(d=>d.item===entry.id)),"all roles "+entry.id);
    await until(async()=> (await phone.locator(".participant-input").innerText()).trim().length>20,"phone mount");
    await controls.waitFor();
    await until(async()=> (await controls.innerText()).trim().length>10,"presenter controls");
    if((await presenter.locator("body").innerText()).includes("Plugin view unavailable"))throw Error("Unavailable "+entry.id);
    for(const role of ["phone","presenter","projector"]){
      if(latest[role]?.language!==language)throw Error("Wrong plugin language for "+role);
    }
    if(entry.id==="shelf-point"){
      await phone.getByRole("heading",{name:de?"Wähle deinen Punkt":"Choose your point",exact:true}).waitFor();
      for(const surface of [phone.locator(".participant-input"),presenter.locator(".presenter-overlay"),projector.locator(".projector-overlay")]){
        const label=await surface.locator("svg").getAttribute("aria-label");
        if(!label.startsWith(de?"Koordinatenebene":"Coordinate plane"))throw Error("Grid label language");
      }
      const initial=latest.phone.plugins.items.find(d=>d.item===entry.id).views["participant-input"].data;
      if("answer" in initial)throw Error("Coordinate reference leaked before reveal");
      await phone.getByLabel((de?"X-Koordinate":"X coordinate")).fill("3");
      await phone.getByLabel((de?"Y-Koordinate":"Y coordinate")).fill("4");
      await phone.getByLabel(de?"Y-Koordinate":"Y coordinate").press("Enter");
      await phone.getByRole("status").filter({hasText:de?"Abstand vom Ursprung: 5,00":"Distance from the origin: 5.00"}).waitFor();
      await controls.getByRole("button",{name:(de?"Punkt auflösen":"Reveal point"),exact:true}).click();
      await phone.getByText(de?"Richtiger Punkt!":"Correct point!",{exact:false}).waitFor();
      await controls.getByRole("button",{name:de?"Antworten zurücksetzen":"Reset responses",exact:true}).click();
      await until(()=>!latest.phone?.plugins?.items?.find(d=>d.item===entry.id)?.views["participant-input"].data.own,"coordinate reset");
      await phone.getByLabel(de?"X-Koordinate":"X coordinate").fill("0");
      await phone.getByLabel(de?"Y-Koordinate":"Y coordinate").fill("5");
      await phone.getByRole("button",{name:de?"Punkt senden":"Send point",exact:true}).tap();
      await phone.getByRole("status").filter({hasText:de?"Abstand vom Ursprung: 5,00":"Distance from the origin: 5.00"}).waitFor();
      await controls.getByRole("button",{name:de?"Punkt auflösen":"Reveal point",exact:true}).click();
      await phone.getByText(de?"Lösungspunkt: (3, 4)":"Reference: (3, 4)",{exact:false}).waitFor();
      if(await phone.getByText(de?"Richtiger Punkt!":"Correct point!",{exact:false}).count())throw Error("Equidistant wrong point accepted");
    }else{
      for(const details of await controls.locator("details").all()){
        if(!await details.evaluate(e=>e.open) && await details.locator("summary").first().isVisible())await details.locator("summary").first().click();
      }
      if(entry.id.startsWith("tx_")){
        await controls.locator('[data-tx="advance"]').click();
        await until(()=>latest.phone?.plugins?.items?.find(d=>d.item===entry.id)?.views["participant-input"].data.phase==="predict","predict phase");
        if(entry.id==="tx_counter"){
          await phone.locator('[data-tx-value]').first().fill("110");
          await phone.locator('[data-tx-submit="prediction"]').click();
          await until(()=>latest.phone?.plugins?.items?.find(d=>d.item===entry.id)?.views["participant-input"].data.own?.prediction,"saved prediction");
        }
      }else{
        await controls.getByRole("button",{name:de?"Antworten öffnen":"Open answers",exact:true}).click();
        await until(()=>latest.phone?.plugins?.items?.find(d=>d.item===entry.id)?.views["participant-input"].data.phase==="open","open phase "+entry.id);
      }
    }
    if(entry.id!=="shelf-point"){
      const save=entry.id.startsWith("plan_")?(de?"Plan absenden":"Submit plan"):
        entry.id.startsWith("bplus_")?(de?"Antwort absenden":"Submit answer"):(de?"Antwort speichern":"Save answer");
      await phone.locator(".participant-input").getByRole("button",{name:save,exact:true}).first().waitFor();
    }
    // Check one representative of each content type at 390px; capture both roles.
    if(!selectedScreens.has(entry.type)){
      selectedScreens.add(entry.type);
      await phone.screenshot({path:path.join(output,"phone-"+entry.id+".png"),fullPage:true});
      await presenter.screenshot({path:path.join(output,"presenter-"+entry.id+".png"),fullPage:true});
      await projector.screenshot({path:path.join(output,"projector-"+entry.id+".png"),fullPage:true});
    }
    if(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error("Phone overflow "+entry.id);
    const publicDescriptor=latest.projector?.plugins?.items?.find(d=>d.item===entry.id);
    if(publicDescriptor&&("private" in publicDescriptor.public))throw Error("Private public field");
    pluginChecked.push({id:entry.id,type:entry.type,phoneMounted:true,controlsOpened:true,languageChecked:true});
    console.log("Plugin smoke "+entry.id);
  }
  await send({t:"slide",slide:deck.slides[0].id});
  await phone.locator(".participant-input").waitFor({state:"detached"});


  if(errors.length)throw Error(errors.join("\n"));
  const report={language,browserLocale:locale,family,browser:browser.version(),checked,plugins:pluginChecked,pageErrors:errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
  control?.close();await browser?.close();
  if(server.pid){
    if(process.platform==="win32")require("node:child_process").spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore",timeout:10000});
    else server.kill();
  }
  server.stdout?.destroy();server.stderr?.destroy();server.unref();log.end();
});

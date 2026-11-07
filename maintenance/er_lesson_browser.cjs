// SPDX-License-Identifier: Apache-2.0
// Real installed host/provider, presenter/projector and narrow phone interactions.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),{spawn,spawnSync}=require("node:child_process");
const playwright=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||"chromium";
const output=path.resolve(process.argv[3]||"artifacts/er-lesson",family);
fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,"profile-")),port=Number(process.env.TEXSTAGE_TEST_PORT||18782);
const base="http://127.0.0.1:"+port,deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",String(port)],
 {windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(test,label){for(let i=0;i<150;i++){if(await test())return;await delay(100);}throw new Error("Timeout: "+label);}
(async()=>{
 let browser;const errors=[],pages=[],states={presenter:[],projector:[],phone:[],other:[],peer:[]};
 const watch=(page,role)=>{pages.push(page);page.on("pageerror",e=>errors.push(e.message));
  page.on("websocket",ws=>ws.on("framereceived",({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==="state")states[role].push(m);}catch{}}));};
 const item=role=>states[role].at(-1)?.plugins?.items?.[0];
 const view=role=>Object.values(item(role)?.views||{})[0]?.data;
 const named=(loc,name)=>loc.getByRole("button",{name,exact:true});
 const choice=(page,d,o)=>page.locator('[data-choice="'+d+":"+o+'"]');
 const choose=async(page,form="relationship",owner="registration")=>{
  for(const [d,o] of [["person-links","zero-many"],["status-owner",owner],["registration-form",form]])await choice(page,d,o).check();
 };
 const reason=page=>page.getByLabel("Reason for your choices (optional)");
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server");
  browser=await playwright[family].launch({headless:true});
  const desktop=await browser.newContext({viewport:{width:1440,height:1100}});
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const presenter=await desktop.newPage();watch(presenter,"presenter");
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  const controls=presenter.locator(".presenter-controls");
  await named(controls,"Open answers").waitFor();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const projector=await desktop.newPage();watch(projector,"projector");
  await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  await projector.locator(".projector-overlay .er-overlay").waitFor({state:"attached"});
  assert(await projector.locator(".er-overlay").isHidden(),"Static task remains visible before sharing");
  const mobile=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const phone=await mobile.newPage();watch(phone,"phone");await phone.goto(base+"/play?pin="+pin);
  await phone.locator("#nick").fill("ER learner");await phone.locator("#join button[type=submit]").click();
  await reason(phone).waitFor();
  assert(await named(phone,"Save answer").isDisabled());
  assert.equal(await phone.locator(".er-lesson input:checked").count(),0,"No leaked default answer");
  await named(controls,"Open answers").click();await until(()=>named(phone,"Save answer").isEnabled(),"open reaches phone");
  await named(phone,"Save answer").tap();await phone.getByText("Choose one option in every card before saving.",{exact:true}).waitFor();
  await choose(phone);await reason(phone).fill("Each registration needs its own status.");
  await named(phone,"View model").tap();
  await phone.getByRole("heading",{name:"Your model preview",exact:true}).waitFor();
  await phone.getByText("Each individual Person participates in 0..* links.",{exact:true}).waitFor();
  await phone.screenshot({path:path.join(output,"phone-model.png"),fullPage:true});
  await named(phone,"Back to decisions").tap();
  assert.equal(await reason(phone).inputValue(),"Each registration needs its own status.");
  // A second browser context resumes exactly the same authenticated learner.
  const second=await browser.newContext({storageState:await mobile.storageState(),viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const other=await second.newPage();watch(other,"other");await other.goto(base+"/play?pin="+pin);await reason(other).waitFor();
  await choose(other,"entity-pair-key");await reason(other).fill("Unique pairs identify registrations.");
  await reason(phone).focus();
  await named(controls,"Inspect an answer privately").click();
  assert(await reason(phone).evaluate(n=>n===document.activeElement));
  assert.equal(await reason(phone).inputValue(),"Each registration needs its own status.");
  await named(other,"Save answer").tap();await named(phone,"Keep my draft").waitFor();
  assert(await named(phone,"Save answer").isDisabled());
  await named(phone,"Keep my draft").tap();assert.equal(await reason(phone).inputValue(),"Each registration needs its own status.");
  // Keyboard path: radio keys, visible focus and tab order through preview to save.
  await choice(phone,"person-links","zero-many").focus();await phone.keyboard.press("ArrowDown");await phone.keyboard.press("ArrowUp");
  assert(await choice(phone,"person-links","zero-many").isChecked());
  assert.notEqual(await choice(phone,"person-links","zero-many").evaluate(n=>getComputedStyle(n).outlineStyle),"none");
  await reason(phone).focus();await phone.keyboard.press("Tab");
  assert.equal(await phone.evaluate(()=>document.activeElement.textContent),"View model");await phone.keyboard.press("Tab");
  assert.equal(await phone.evaluate(()=>document.activeElement.textContent),"Save answer");await phone.keyboard.press("Enter");
  await until(()=>view("phone")?.own?.version===2&&view("phone").own.status==="saved","actual evaluated answer");
  assert(!view("phone").own.feedback&&!view("phone").teaching,"feedback withheld before reveal");
  // Another learner submits a plausible but wrong ownership decision.
  const third=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const peer=await third.newPage();watch(peer,"peer");await peer.goto(base+"/play?pin="+pin);
  await peer.locator("#nick").fill("Other ER learner");await peer.locator("#join button[type=submit]").click();
  await reason(peer).waitFor();await choose(peer,"relationship","person");await reason(peer).fill("A person has a status.");
  await reason(phone).fill("Unsaved after submission");await reason(phone).focus();
  await named(peer,"Save answer").tap();await until(()=>view("peer")?.own?.status==="saved","wrong model evaluated");
  assert.equal(await reason(phone).inputValue(),"Unsaved after submission");
  assert(await reason(phone).evaluate(n=>n===document.activeElement),"unrelated answer preserves focus");
  assert(await named(phone,"Keep my draft").isHidden(),"unrelated actor is not a draft conflict");
  await named(controls,"Close answers").click();await until(()=>named(phone,"Save answer").isDisabled(),"closed phase");
  const select=controls.getByLabel("Inspect an answer privately");
  const learnerActor=Object.values(item("presenter").views).find(v=>v.data.participants)?.data.participants.find(r=>r.version===2).actor;
  await select.selectOption(learnerActor);await named(controls,"Inspect an answer privately").click();
  await controls.getByRole("heading",{name:"Private inspection",exact:true}).waitFor();
  assert(await projector.locator(".er-overlay").isHidden(),"Private selection stays private");
  await named(controls,"Share selected answer anonymously").click();
  await projector.getByRole("heading",{name:"Anonymously shared model",exact:true}).waitFor();
  assert(!view("projector").demonstration.rationale,"Reason not released by default");
  await controls.getByLabel("Also share the reason with the class").check();
  await named(controls,"Share selected answer anonymously").click();
  await projector.getByText("Each registration needs its own status.",{exact:true}).waitFor();
  await named(controls,"Clear shared answer").click();
  await until(()=>!view("projector")?.demonstration,"share cleared");
  await named(controls,"Reveal alternatives").click();
  await phone.getByText("Draft; not saved yet.",{exact:true}).waitFor();
  await peer.getByText(/This model conflicts with the configured examples/).waitFor();
  await other.getByText("This model passes the configured examples.",{exact:true}).waitFor();
  await named(controls,"Open answers").click();
  await until(()=>named(peer,"Save answer").isEnabled(),"repair phase");
  assert(!view("phone").teaching&&!view("peer").own.feedback,"reopening hides released feedback");
  await choose(peer,"entity-pair-key");await named(peer,"Save answer").tap();
  await until(()=>view("peer")?.own?.version===2&&view("peer").own.status==="saved","repair evaluates");
  await named(controls,"Close answers").click();await named(controls,"Reveal alternatives").click();
  await peer.getByText("This model passes the configured examples.",{exact:true}).waitFor();
  await phone.locator("summary").filter({hasText:"Checked alternatives"}).click();
  assert.equal(await reason(phone).inputValue(),"Unsaved after submission","Teaching does not replace draft");
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"320px overflow");
  for(const [name,page] of [["phone",phone],["presenter",presenter],["projector",projector]])
    await page.screenshot({path:path.join(output,name+".png"),fullPage:true});
  const overlay=projector.locator(".er-overlay");
  const presenterSize=await presenter.locator("#currentbox").boundingBox();
  assert(presenterSize.height>=300,"Expanded controls must leave a usable presenter preview");
  const fit=await overlay.evaluate(n=>({height:n.clientHeight,scroll:n.scrollHeight,width:n.clientWidth,scrollWidth:n.scrollWidth}));
  assert(fit.scroll<=fit.height+2&&fit.scrollWidth<=fit.width+2,"Projected alternatives must fit: "+JSON.stringify(fit));
  // Text zoom and viewport resizing leave controls usable without horizontal clipping.
  await phone.locator(".er-lesson").evaluate(n=>n.style.fontSize="32px");
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"200% text overflow");
  await phone.screenshot({path:path.join(output,"phone-text-zoom.png"),fullPage:true});
  await phone.locator(".er-lesson").evaluate(n=>n.style.fontSize="");await phone.setViewportSize({width:390,height:844});
  await named(phone,"View model").tap();await named(phone,"Back to decisions").tap();
  // Reset reaches the existing mount and cannot silently submit the old draft.
  await phone.locator(".er-lesson").evaluate(n=>n.dataset.mountMarker="retained");
  presenter.once("dialog",d=>d.accept());await named(controls,"Reset activity").click();
  await named(phone,"Reload saved answer").waitFor();
  assert.equal(await phone.locator(".er-lesson").getAttribute("data-mount-marker"),"retained");
  await named(phone,"Reload saved answer").tap();
  assert.equal(await phone.locator(".er-lesson input:checked").count(),0);assert.equal(await reason(phone).inputValue(),"");
  assert.equal(view("phone").own,undefined);
  assert.equal(view("phone").count,undefined);
  await named(controls,"Open answers").click();await reason(phone).fill("Discard this unsaved draft on navigation.");
  await presenter.locator("#next").click();await phone.locator(".participant-input").waitFor({state:"detached"});
  await controls.waitFor({state:"detached"});await presenter.locator("#prev").click();await reason(phone).waitFor();
  assert.equal(await reason(phone).inputValue(),"","Only saved answers survive navigation");
  // Check every captured public transport, not only the pixels.
  for(const role of ["phone","other","peer","projector"])for(const message of states[role])for(const d of message.plugins?.items||[]){
    const raw=JSON.stringify(d);
    for(const bad of ['"private":','"evaluations":','"exercise_digest":','"checks":','duplicate-pair','two-workshops'])
      assert(!raw.includes(bad),role+" leaked "+bad);
    for(const v of Object.values(d.views)){
      assert(!v.data.participants&&!v.data.selected,"private inspection in public projection");
      if(v.data.phase!=="revealed")assert(!v.data.teaching&&!v.data.own?.feedback,"early feedback");
      if(role==="projector"&&v.data.demonstration)assert(!("actor" in v.data.demonstration)&&!("version" in v.data.demonstration));
    }
  }
  const revealed=states.phone.flatMap(m=>m.plugins?.items||[]).find(d=>d.views["participant-input"]?.data.teaching);
  const teacherData=Object.values(item("presenter").views).find(v=>v.data.participants).data;
  const testDescriptor={...item("phone"),modules:{...item("phone").modules,...item("presenter").modules}};
  // Use the bundle's original Unicode data for synthetic renderer fixtures;
  // the separate German deck test verifies text through the native client.
  testDescriptor.public=deck.items[testDescriptor.type][testDescriptor.item];
  const rendererChecks=await require("./er_ui_contracts.cjs")(phone,testDescriptor,teacherData,
    revealed.views["participant-input"].data.teaching,output);

  const germanProjection=await projector.evaluate(async({descriptor,teaching})=>{
    const module=await import(descriptor.modules["projector-overlay"]);
    const container=document.createElement("div");container.id="er-german-projector";
    container.style.cssText="position:fixed;inset:0;width:1200px;height:680px;z-index:10000";
    document.body.append(container);
    const item=structuredClone(descriptor.public);
    item.labels.entities[0].text.de="Teilnehmende Kursteilnehmerin";
    item.labels.entities[1].text.de="Fortbildungsworkshop";
    item.labels.relationship.de="Verbindliche Workshopanmeldung";
    const controller=new AbortController();
    const mounted=module.mount({container,item,language:"de",role:"projector",surface:"projector-overlay",signal:controller.signal});
    mounted.place({box:{x:0,y:0,w:1200,h:680}});
    mounted.update({epoch:1,revision:1,data:{phase:"revealed",teaching}});
    const n=container.querySelector(".er-overlay");
    globalThis.__erGermanCleanup=()=>{controller.abort();mounted.destroy();container.remove();};
    return {height:n.clientHeight,scroll:n.scrollHeight,font:getComputedStyle(n).fontSize};
  },{descriptor:{...item("projector"),public:testDescriptor.public},teaching:revealed.views["participant-input"].data.teaching});
  await projector.locator("#er-german-projector").screenshot({path:path.join(output,"german-projector.png")});
  assert(germanProjection.scroll<=germanProjection.height+2,"Long German projection: "+JSON.stringify(germanProjection));
  await projector.evaluate(()=>{globalThis.__erGermanCleanup();delete globalThis.__erGermanCleanup;});

  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),viewport:320,realWorker:true,twoDevicesOneActor:true,
    distinctLearners:true,keyboard:true,touch:true,draftAndFocus:true,preview:true,repair:true,sharing:true,privacy:true,
    resetExistingMount:true,navigation:true,textZoom:2,projectorFits:fit,germanProjection,rendererChecks,errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(e){
  for(const [i,page]of pages.entries()){
    await page.screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
    fs.writeFileSync(path.join(output,"failure-"+i+".txt"),await page.locator("body").innerText().catch(()=>""));
  }
  console.error("Page errors:",errors);throw e;
 }finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{if(process.platform==="win32")spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});else server.kill();log.end();});


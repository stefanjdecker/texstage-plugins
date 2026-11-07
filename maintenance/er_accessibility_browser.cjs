// SPDX-License-Identifier: Apache-2.0
// Keyboard and accessibility-tree checks, not a physical-device/screen-reader test.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn,spawnSync}=require("node:child_process"),pw=require("playwright");
const bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||"chromium";
const nativeZoom=process.env.ER_NATIVE_ZOOM==="2";
assert(!nativeZoom||family==="chromium","Native zoom uses a disposable Chrome profile; select BROWSER=chromium");
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json"))),language=deck.language?.startsWith("de")?"de":"en";
const output=path.resolve(process.argv[3]||"artifacts/er-accessibility",language,family+(nativeZoom?"-zoom2":""));fs.mkdirSync(output,{recursive:true});
const port=Number(process.env.TEXSTAGE_TEST_PORT||18871),base="http://127.0.0.1:"+port;
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,
 "--data",fs.mkdtempSync(path.join(output,"profile-")),"--port",String(port)],{windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const w=language==="de"?{open:"Antworten öffnen",close:"Antworten schließen",reveal:"Alternativen auflösen",reset:"Aktivität zurücksetzen",
 save:"Antwort speichern",reason:"Begründung Ihrer Entscheidungen (optional)",preview:"Modell ansehen",heading:"Ihre Modellvorschau",back:"Zurück zu den Entscheidungen",
 keep:"Meinen Entwurf behalten",reload:"Gespeicherte Antwort laden",constraints:"Bedingungen in Worten",phase:"Phase: Aufgelöst.",passed:"Dieses Modell besteht die konfigurierten Beispiele."}:
 {open:"Open answers",close:"Close answers",reveal:"Reveal alternatives",reset:"Reset activity",save:"Save answer",reason:"Reason for your choices (optional)",
 preview:"View model",heading:"Your model preview",back:"Back to decisions",keep:"Keep my draft",reload:"Reload saved answer",constraints:"Constraints in words",
 phase:"Phase: Revealed.",passed:"This model passes the configured examples."};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<200;i++){if(await fn())return;await delay(100);}throw Error("Timed out: "+label);}
async function tabTo(page,target,radioGroup=false){
 await target.waitFor();await until(()=>target.isEnabled(),"enabled keyboard target");
 for(let i=0;i<120;i++){
  if(await target.evaluate((n,group)=>n===document.activeElement||(group&&document.activeElement?.type==="radio"&&document.activeElement.name===n.name),radioGroup))return;
  const backwards=await target.evaluate(n=>document.activeElement!==document.body&&Boolean(document.activeElement.compareDocumentPosition(n)&Node.DOCUMENT_POSITION_PRECEDING));
  await page.keyboard.press(backwards?"Shift+Tab":"Tab");
 }
 throw Error("Keyboard cannot reach: "+await target.evaluate(n=>n.outerHTML));
}
async function activate(page,target,key="Enter"){await tabTo(page,target);await page.keyboard.press(key);}
async function screenshot(page,name){
 await page.bringToFront();
 const target=path.join(output,name);
 if(nativeZoom){
  // Capture the actual zoomed compositor, not a CSS clip rescaled by Playwright.
  const session=await page.context().newCDPSession(page);
  try{const {data}=await session.send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false,fromSurface:true});
   fs.writeFileSync(target,Buffer.from(data,"base64"));
  }finally{await session.detach();}
 }else await page.screenshot({path:target,fullPage:true});
}
const viewport=page=>page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,scale:visualViewport.scale}));
(async()=>{
 let browser,desktop;const contexts=[],browserProfiles=[],pages=[],errors=[],frames=[],keyboardTrace=[],zoomBaselines=[];
 const watch=page=>{pages.push(page);page.on("pageerror",e=>errors.push(e.message));};
 async function zoomContext(locale){
  const profile=fs.mkdtempSync(path.join(output,"browser-"));
  browserProfiles.push(profile);
  const context=await pw.chromium.launchPersistentContext(profile,{headless:true,
   channel:process.env.TEXSTAGE_BROWSER_CHANNEL||"chrome",viewport:null,locale,args:["--window-size=1440,1000"]});
  contexts.push(context);
  const page=await context.newPage();zoomBaselines.push(await viewport(page));
  await page.goto("chrome://settings/appearance");
  await page.evaluate(()=>new Promise(resolve=>chrome.settingsPrivate.setDefaultZoom(2,resolve)));
  assert.equal(await page.evaluate(()=>new Promise(resolve=>chrome.settingsPrivate.getDefaultZoom(resolve))),2);
  await page.close();return context;
 }
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server");
  if(nativeZoom)desktop=await zoomContext(language==="de"?"de-DE":"en-US");
  else{
   browser=await pw[family].launch({headless:true});
   desktop=await browser.newContext({viewport:{width:1440,height:1100},locale:language==="de"?"de-DE":"en-US"});
  }
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const presenter=await desktop.newPage();watch(presenter);presenter.on("dialog",d=>d.accept());
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  const controls=presenter.locator(".presenter-controls"),action=name=>activate(presenter,controls.getByRole("button",{name,exact:true}));
  await controls.getByRole("button",{name:w.open,exact:true}).waitFor();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  // Opposite browser locale proves that the provider uses the deck language.
  const mobile=nativeZoom?await zoomContext(language==="de"?"en-US":"de-DE"):
   await browser.newContext({viewport:{width:320,height:740},locale:language==="de"?"en-US":"de-DE"});
  const phone=await mobile.newPage();watch(phone);
  phone.on("websocket",ws=>ws.on("framereceived",({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==="state")frames.push(m);}catch{}}));
  const item=()=>frames.at(-1)?.plugins?.items?.[0],view=()=>item()?.views["participant-input"]?.data;
  await phone.goto(base+"/play?pin="+pin);await tabTo(phone,phone.locator("#nick"));await phone.keyboard.type("Keyboard learner");
  await activate(phone,phone.locator("#join button[type=submit]"));
  const root=phone.locator(".participant-input .er-lesson"),save=phone.getByRole("button",{name:w.save,exact:true});
  const reason=phone.getByRole("textbox",{name:w.reason,exact:true}),named=name=>phone.getByRole("button",{name,exact:true});
  await save.waitFor();assert.equal(await root.getAttribute("lang"),language);
  const metrics={presenter:await viewport(presenter),participant:await viewport(phone)};
  if(nativeZoom)for(const [i,m] of Object.values(metrics).entries()){
   assert(Math.abs(m.dpr/zoomBaselines[i].dpr-2)<0.05,"Native zoom doubles pixel ratio");
   assert(Math.abs(m.width/zoomBaselines[i].width-0.5)<0.02&&m.scale===1,"Native page zoom, not viewport or pinch emulation");
  }
  assert(await root.getAttribute("aria-label"),"Named activity region");await action(w.open);
  await activate(phone,named(w.preview));
  await activate(phone,save);
  const first=root.locator("fieldset input").first();
  assert(await first.evaluate(n=>n===document.activeElement),"Empty answer focuses first missing decision");
  const errorId=await first.getAttribute("aria-describedby");assert(errorId);
  assert.equal(await first.getAttribute("aria-invalid"),"true");
  assert(await phone.locator('[id="'+errorId+'"]').innerText(),"Named validation message");
  await screenshot(phone,"missing-decision.png");
  const choices=[["person-links","zero-many"],["status-owner","registration"],["registration-form","relationship"]];
  const trace=async step=>keyboardTrace.push({step,...await root.evaluate(n=>({active:document.activeElement?.outerHTML,
    checked:[...n.querySelectorAll('input:checked')].map(x=>x.dataset.choice)}))});
  async function choose(){for(const [decision,value] of choices){
   const group=root.locator('[data-decision="'+decision+'"]'),selected=group.locator("input:checked");
   await tabTo(phone,await selected.count()?selected:group.locator("input").first(),true);await trace(decision+" focused");await phone.keyboard.press("Space");await trace(decision+" Space");
   // Native WebKit radios need not wrap at the ends of a group. Move toward
   // the target using either arrow, without replacing native keyboard events.
   for(let i=0;i<4&&!(await group.locator('[value="'+value+'"]').isChecked());i++){
    const key=await group.evaluate((n,value)=>{
     const nodes=[...n.querySelectorAll("input")];return nodes.findIndex(n=>n.value===value)<nodes.indexOf(document.activeElement)?"ArrowUp":"ArrowDown";
    },value);
    await phone.keyboard.press(key);await trace(decision+" "+key);
   }
   assert(await group.locator('[value="'+value+'"]').isChecked(),"Keyboard choice "+decision);
  }}
  await choose();await tabTo(phone,reason);await phone.keyboard.insertText("x".repeat(161));
  await activate(phone,named(w.preview));assert(await phone.getByRole("heading",{name:w.heading,exact:true}).evaluate(n=>n===document.activeElement));
  await activate(phone,save);assert(await reason.evaluate(n=>n===document.activeElement),"Invalid reason leaves preview and focuses visible field");
  assert.equal(await reason.getAttribute("aria-invalid"),"true");assert.equal(await reason.getAttribute("aria-describedby"),errorId);
  await phone.keyboard.press("Control+A");await phone.keyboard.insertText("A reason for my choices.");
  assert.equal(await reason.getAttribute("aria-invalid"),null);
  await activate(phone,named(w.preview));
  for(const choice of [w.keep,w.reload]){
   await action(w.reset);await activate(phone,named(choice));
   assert(await phone.getByRole("heading",{name:w.heading,exact:true}).evaluate(n=>n===document.activeElement&&n.getClientRects().length),"Conflict returns to visible preview heading");
   assert(!view().own,"Conflict resolution must not submit");
  }
  await activate(phone,named(w.back));await choose();await action(w.open);
  await activate(phone,save);await until(()=>view()?.own?.status==="saved","evaluation");
  assert(!view().own.feedback&&!view().teaching,"Feedback stays private before reveal");
  await action(w.close);await action(w.reveal);await until(()=>view()?.own?.feedback?.correct,"reveal");
  assert.equal(await root.locator(".er-phase").innerText(),w.phase);
  assert.equal(await root.locator(".er-answer-status").innerText(),w.passed);
  await activate(phone,named(w.preview));
  const constraints=root.getByRole("list",{name:w.constraints,exact:true});await constraints.waitFor();
  const snapshot=await root.ariaSnapshot();assert(snapshot.includes(w.constraints)&&snapshot.includes(w.heading));
  fs.writeFileSync(path.join(output,"phone-aria.yml"),snapshot+"\n");
  fs.writeFileSync(path.join(output,"presenter-aria.yml"),await controls.ariaSnapshot()+"\n");
  assert(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"No horizontal participant page overflow");
  await screenshot(phone,"phone-model.png");
  const presenterLayout=await presenter.evaluate(()=>{
   const side=document.querySelector(".side").getBoundingClientRect(),toolbar=document.querySelector(".toolbar").getBoundingClientRect();
   const workspace=document.querySelector("main");
   return {separate:side.bottom<=toolbar.top+1,scrollable:workspace.scrollHeight>workspace.clientHeight,
    overflow:getComputedStyle(workspace).overflowY,noPageOverflow:document.documentElement.scrollWidth<=innerWidth+1};
  });
  if(nativeZoom)assert(presenterLayout.separate&&presenterLayout.scrollable&&presenterLayout.overflow==="auto"&&presenterLayout.noPageOverflow,
   "Zoomed presenter panes and toolbar remain separate and scrollable: "+JSON.stringify(presenterLayout));
  await screenshot(presenter,"presenter.png");
  let zoomControls=null;
  if(nativeZoom){
   const inspect=language==="de"?"Antwort privat ansehen":"Inspect an answer privately";
   const share=language==="de"?"Ausgewählte Antwort anonym teilen":"Share selected answer anonymously";
   const select=controls.getByRole("combobox",{name:inspect,exact:true});
   await tabTo(presenter,select);await presenter.keyboard.press("Home");await presenter.keyboard.press("ArrowDown");await presenter.keyboard.press("Enter");
   await action(inspect);const shareButton=controls.getByRole("button",{name:share,exact:true});
   await tabTo(presenter,shareButton);
   assert(await shareButton.evaluate(n=>{
    const r=n.getBoundingClientRect(),s=n.closest(".er-lesson").getBoundingClientRect();
    return n===document.activeElement&&r.top>=Math.max(0,s.top)-1&&r.bottom<=Math.min(innerHeight,s.bottom)+1;
   }),"Private inspection and sharing control are reachable in the zoomed scroll pane");
   await screenshot(presenter,"presenter-inspection.png");zoomControls={privateInspection:true,sharingControlReachable:true};
  }
  const projector=await desktop.newPage();watch(projector);await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  const overlay=projector.locator(".projector-overlay .er-overlay");await overlay.waitFor();
  fs.writeFileSync(path.join(output,"projector-aria.yml"),await overlay.ariaSnapshot()+"\n");
  await screenshot(projector,"projector.png");
  if(nativeZoom){
   await tabTo(projector,overlay);await projector.keyboard.press("End");
   await until(()=>overlay.evaluate(n=>n.scrollTop+n.clientHeight>=n.scrollHeight-1),"Keyboard reaches end of projected alternatives");
   assert(await overlay.evaluate(n=>n===document.activeElement),"Projector scrolling keeps the activity focused");
   zoomControls.projectorKeyboardScroll=true;
   await screenshot(projector,"projector-end.png");
  }
  // Browser text zoom emulation supplements, not replaces, native browser zoom.
  if(!nativeZoom){
   await phone.evaluate(()=>{document.querySelector('.participant-input .er-lesson').style.fontSize='32px';});
   assert(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"No horizontal phone overflow at doubled text");
   await screenshot(phone,"phone-text-zoom.png");
  }
  const descriptor={...item(),public:deck.items[item().type][item().item]};
  const contracts=await require('./er_accessibility_contracts.cjs')(phone,descriptor,language);
  assert.deepEqual(errors,[]);
  const report={browser:family,version:(browser||desktop.browser()).version(),language,bundle:deck.bundle,provider:deck.plugins,viewport:metrics.participant.width,
   metrics,nativeZoom:nativeZoom?2:1,zoomBaselines,presenterLayout,zoomControls,
   keyboardOnly:true,fieldErrors:true,previewConflictFocus:true,phaseAndFeedbackSemantics:true,privateUntilReveal:true,
   modelTextAlternative:true,accessibleNames:true,textZoom:nativeZoom?1:2,contracts,errors,
   scope:"Installed-wheel keyboard and accessibility-tree/DOM checks; no physical phone or screen-reader speech output verified."};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(e){for(const [i,p] of pages.entries()){
  await screenshot(p,"failure-"+i+".png").catch(()=>{});
  fs.writeFileSync(path.join(output,"failure-"+i+".txt"),await p.locator("body").innerText().catch(()=>""));
 }throw e;}
 finally{fs.writeFileSync(path.join(output,"keyboard-trace.json"),JSON.stringify(keyboardTrace,null,2)+"\n");
  await browser?.close();for(const context of contexts)await context.close();
  for(const profile of browserProfiles){
   // Only remove profiles created by this invocation within its evidence folder.
   assert(path.dirname(path.resolve(profile))===output&&path.basename(profile).startsWith("browser-"));
   fs.rmSync(profile,{recursive:true,force:true,maxRetries:3,retryDelay:100});
  }
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{
 if(process.platform==="win32")spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});else server.kill();log.end();
});

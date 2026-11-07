// SPDX-License-Identifier: Apache-2.0
// Actual installed host/provider, keyboard input and isolated browser profiles.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn}=require("node:child_process"),pw=require("playwright");
const root=path.resolve(__dirname,".."),bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||"chromium";
const baseline=process.env.NORMALIZATION_BASELINE==="1",zoom=process.env.NORMALIZATION_ZOOM==="2";
const output=path.join(root,"artifacts","normalization-accessibility",family+(zoom?"-zoom2":""));
fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,"server-")),port=Number(process.env.TEXSTAGE_TEST_PORT||18815),base="http://127.0.0.1:"+port;
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",String(port)],
 {windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function snapshot(page,name){
 await page.bringToFront();
 if(await page.locator(".presenter-controls").count())await until(()=>page.getByRole("button",{name:"Aufgabe zurücksetzen",exact:true}).isEnabled(),"presenter settled");
 const target=path.join(output,name);
 if(zoom){
  // Native page zoom is distinct from Playwright device emulation. Capture the
  // browser's actual compositor surface, avoiding CSS-clip scaling in screenshot().
  const session=await page.context().newCDPSession(page);
  const {data}=await session.send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false,fromSurface:true});
  fs.writeFileSync(target,Buffer.from(data,"base64"));await session.detach();
 }else await page.screenshot({path:target,fullPage:true});
}
async function until(fn,label){for(let i=0;i<150;i++){if(await fn())return;await delay(100);}throw Error("Timed out: "+label);}
async function tabTo(page,locator){
 await page.bringToFront();await locator.waitFor();await until(()=>locator.isEnabled(),"enabled control");
 for(let i=0;i<200;i++){if(await locator.evaluate(n=>n===document.activeElement))return;const backwards=await locator.evaluate(n=>Boolean(document.activeElement!==document.body&&(document.activeElement.compareDocumentPosition(n)&Node.DOCUMENT_POSITION_PRECEDING)));await page.keyboard.press(backwards?"Shift+Tab":"Tab");}
 throw Error("Unreachable by Tab: "+await locator.innerText()+"; active="+await page.evaluate(()=>document.activeElement?.outerHTML));
}
async function activate(page,locator,key="Enter"){await tabTo(page,locator);await page.keyboard.press(key);}
(async()=>{
 let browser,desktop;const pages=[],errors=[],frames=[];
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server");
  if(zoom){
   assert.equal(family,"chromium");
   const browserProfile=fs.mkdtempSync(path.join(output,"browser-"));
   desktop=await pw.chromium.launchPersistentContext(browserProfile,{headless:true,channel:process.env.TEXSTAGE_BROWSER_CHANNEL||"chrome",
     viewport:null,locale:"de-DE",args:["--window-size=1440,1000"]});
   const settings=await desktop.newPage();await settings.goto("chrome://settings/appearance");
   await settings.evaluate(()=>new Promise(r=>chrome.settingsPrivate.setDefaultZoom(2,r)));
   assert.equal(await settings.evaluate(()=>new Promise(r=>chrome.settingsPrivate.getDefaultZoom(r))),2);
   await settings.close();
  }else{
   browser=await pw[family].launch({headless:true,...(process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
   desktop=await browser.newContext({viewport:{width:1440,height:1100},locale:"de-DE"});
  }
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const watch=p=>{pages.push(p);p.on("pageerror",e=>errors.push(e.message));};
  const presenter=await desktop.newPage();watch(presenter);await presenter.goto(base+"/stage?bundle="+deck.bundle);
  const controls=presenter.locator(".presenter-controls"),action=name=>activate(presenter,controls.getByRole("button",{name,exact:true}));
  await controls.getByRole("button",{name:"Antworten öffnen",exact:true}).waitFor();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const mobile=zoom?desktop:await browser.newContext({viewport:{width:320,height:740},locale:"de-DE",hasTouch:true,isMobile:family!=="firefox"});
  const phone=await mobile.newPage();watch(phone);
  phone.on("websocket",s=>s.on("framereceived",({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==="state")frames.push(m);}catch{}}));
  const view=()=>Object.values(frames.at(-1)?.plugins?.items?.[0]?.views||{})[0]?.data;
  await phone.goto(base+"/play?pin="+pin);
  await tabTo(phone,phone.locator("#nick"));await phone.keyboard.type("Tastaturtest");
  await activate(phone,phone.locator("#join button[type=submit]"));
  const editor=phone.locator(".nw-editor"),save=phone.getByRole("button",{name:"Antwort speichern",exact:true});
  await save.waitFor();
  const metrics=await phone.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,scale:visualViewport.scale}));
  if(zoom){assert(metrics.dpr>=1.95&&metrics.width<800&&metrics.scale===1,JSON.stringify(metrics));}
  await action("Antworten öffnen");await until(async()=>!(await save.isDisabled()),"open");
  await activate(phone,editor.getByRole("button",{name:"Relation hinzufügen",exact:true}));
  assert(await editor.locator("fieldset").nth(1).locator("input").first().evaluate(n=>n===document.activeElement),"focus newly added relation");
  await activate(phone,editor.getByRole("button",{name:"Entfernen 2",exact:true}));
  const removedFocus=await editor.locator("input").first().evaluate(n=>n===document.activeElement);
  const language=await phone.locator(".nw-workshop").getAttribute("lang");
  if(baseline){
   fs.writeFileSync(path.join(output,"baseline.json"),JSON.stringify({removedFocus,language,metrics},null,2)+"\n");
   console.log(JSON.stringify({removedFocus,language,metrics}));return;
  }
  assert(removedFocus,"removal must keep focus in the adjacent relation");
  assert.equal(language,"de");
  assert.equal(await editor.locator("input").first().getAttribute("aria-description"),"Studierende");
  // Reset a dirty draft; both explicit choices retain focus and never submit.
  await phone.keyboard.press("Space");
  for(const label of ["Entwurf behalten","Gespeicherte Antwort laden"]){
   await action("Aufgabe zurücksetzen");
   const choice=phone.getByRole("button",{name:label,exact:true});await choice.waitFor();await activate(phone,choice);
   assert(await editor.locator("input").first().evaluate(n=>n===document.activeElement));
   assert.equal(view().answer_version,0);
  }
  await action("Antworten öffnen");
  async function relations(sets){
   while(await editor.locator("fieldset").count()<sets.length)await activate(phone,editor.getByRole("button",{name:"Relation hinzufügen",exact:true}));
   for(let i=0;i<sets.length;i++){
    const inputs=editor.locator("fieldset").nth(i).locator("input");
    for(let j=0;j<await inputs.count();j++){
     const input=inputs.nth(j);
     if((await input.isChecked())!==sets[i].includes(await input.getAttribute("aria-label")))await activate(phone,input,"Space");
    }
   }
  }
  await relations([["S","N"],["C","T","I"],["I","O"]]);
  await activate(phone,save);await until(()=>view()?.status==="checked","checked lossy answer");
  assert.equal(view().analysis,null);
  await action("Antworten schließen");await action("Privat ansehen 1");await action("Antwort mit Prüfungen teilen 1");
  await action("Verbundtreue erklären");
  const projector=await desktop.newPage();watch(projector);await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  const projectedTrace=projector.locator(".nw-trace");await projectedTrace.locator("summary").waitFor();
  const position=await presenter.locator("#where").innerText();
  await activate(projector,projectedTrace.locator("summary"));
  await activate(projector,projectedTrace.getByRole("button",{name:"Nächster Schritt",exact:true}));
  assert.equal(await presenter.locator("#where").innerText(),position,"projector proof keys must not navigate");
  await snapshot(projector,"projector-de.png");
  await action("Lösung aufdecken");
  await until(()=>view()?.analysis?.facts?.join?.lossless===false,"lossy evidence");
  const proof=phone.locator("summary").filter({hasText:/^Verbundtreue erklären$/});
  await activate(phone,proof);
  const trace=phone.locator(".nw-trace");await activate(phone,trace.locator("summary"));
  const next=trace.getByRole("button",{name:"Nächster Schritt",exact:true}),prev=trace.getByRole("button",{name:"Vorheriger Schritt",exact:true});
  await activate(phone,next);
  assert(await next.evaluate(n=>n===document.activeElement),"boundary keeps focus");
  assert.equal(await next.getAttribute("aria-disabled"),"true");
  const finalText=await trace.getByRole("status").innerText();await phone.keyboard.press("Enter");
  assert.equal(await trace.getByRole("status").innerText(),finalText,"bounded chase");
  await action("Überblick");
  assert(await next.evaluate(n=>n===document.activeElement));
  await activate(phone,prev);
  assert.equal(await prev.getAttribute("aria-disabled"),"true");assert(await prev.evaluate(n=>n===document.activeElement));
  await activate(phone,trace.getByRole("button",{name:"Finale Tabelle",exact:true}));
  await tabTo(phone,trace.locator(".nw-table"));await phone.keyboard.press("ArrowRight");
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"page overflow");
  await snapshot(phone,"phone-chase-de.png");
  if(zoom){
    const layout=await presenter.evaluate(()=>{
      const side=document.querySelector(".side").getBoundingClientRect();
      const toolbar=document.querySelector(".toolbar").getBoundingClientRect();
      const workspace=document.querySelector("main");
      return {separate:side.bottom<=toolbar.top+1,scrollable:workspace.scrollHeight>workspace.clientHeight,
        overflow:getComputedStyle(workspace).overflowY};
    });
    assert(layout.separate&&layout.scrollable&&layout.overflow==="auto",JSON.stringify(layout));
   }
   await snapshot(presenter,"presenter-de.png");
  // Native select and FD witness, using keyboard events only.
  await activate(presenter,presenter.locator("#next"));
  const form=phone.getByLabel("Höchste Normalform",{exact:true});await form.waitFor();await action("Antworten öffnen");
  await tabTo(phone,form);await phone.keyboard.press("Home");await phone.keyboard.press("ArrowDown");await phone.keyboard.press("ArrowDown");
  assert.equal(await form.inputValue(),"3nf");
  await activate(phone,phone.locator("fieldset").getByLabel("U",{exact:true}),"Space");
  const rhs=phone.getByLabel("Rechte Seite",{exact:true});await tabTo(phone,rhs);await phone.keyboard.press("Home");await phone.keyboard.press("ArrowDown");
  await activate(phone,save);await until(()=>view()?.status==="checked","classification");
  await action("Antworten schließen");await action("Lösung aufdecken");await until(()=>view()?.feedback?.accepted,"classification accepted");
  assert.equal(await phone.locator(".nw-workshop").getAttribute("lang"),"de");
  await snapshot(phone,"phone-classification-de.png");
  // Constant FD: the empty candidate key remains visible and meaningful.
  await activate(presenter,presenter.locator("#next"));await activate(presenter,presenter.locator("#next"));
  await phone.getByRole("heading",{name:"Ein fester Wert",exact:true}).waitFor();await action("Antworten öffnen");
  await activate(phone,save);await until(()=>view()?.status==="checked","constant relation");
  await action("Antworten schließen");await action("Lösung aufdecken");await until(()=>view()?.feedback?.accepted,"constant accepted");
  await phone.getByText("Kandidatenschlüssel: ∅",{exact:true}).waitFor();
  await snapshot(phone,"phone-empty-key-de.png");
  const descriptionSnapshot=await phone.locator(".nw-workshop").ariaSnapshot();
  assert(descriptionSnapshot.includes("Höchste Normalform")&&descriptionSnapshot.includes("Kandidatenschlüssel"));
  fs.writeFileSync(path.join(output,"accessibility-tree.txt"),descriptionSnapshot);
  assert.deepEqual(errors,[]);
  const report={browser:family,version:zoom?desktop.browser().version():browser.version(),language:"de",metrics,nativeZoom:zoom?2:1,
   keyboardOnlyLearner:true,keyboardPresenterActions:true,addRemoveFocus:true,conflictChoiceFocus:true,noImplicitSubmit:true,
   chaseBoundariesKeepFocus:true,projectorKeyboardProof:true,proofFocusAcrossUpdates:true,localizedAttributeDescription:true,emptyKey:true,
   accessibleNamesSnapshot:true,errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(e){
  fs.writeFileSync(path.join(output,"failure.txt"),String(e.stack));
  for(let i=0;i<pages.length;i++)await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true,timeout:5000}).catch(()=>{});
  throw e;
 }finally{await desktop?.close();await browser?.close();server.kill();log.end();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});

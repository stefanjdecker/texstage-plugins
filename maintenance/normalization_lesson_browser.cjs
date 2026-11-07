// SPDX-License-Identifier: Apache-2.0
// Installed host/provider: native controls, real evaluator and role-filtered transport.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {spawn}=require("node:child_process");
const playwright=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||"playwright");
const root=path.resolve(__dirname,".."),bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||"chromium";
const output=path.join(root,"artifacts","normalization-discussion",family);fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,"profile-")),port=Number(process.env.TEXSTAGE_TEST_PORT||18759),base="http://127.0.0.1:"+port;
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,"--data",profile,"--port",String(port)],
  {windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<150;i++){if(await fn())return;await delay(100);}throw Error("Timed out: "+label);}
(async()=>{
 let browser;const errors=[],sockets={phone:[],bob:[],projector:[],presenter:[]},pages=[];
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}},"server");
  browser=await playwright[family].launch({headless:true,...(process.env.TEXSTAGE_BROWSER_CHANNEL?{channel:process.env.TEXSTAGE_BROWSER_CHANNEL}:{})});
  const desktop=await browser.newContext({viewport:{width:1440,height:1100}});
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const watch=(page,role)=>{
   pages.push(page);page.on("pageerror",e=>errors.push(e.message));
   if(sockets[role])page.on("websocket",socket=>socket.on("framereceived",({payload})=>{
    try{const m=JSON.parse(String(payload));if(m.t==="state")sockets[role].push(m);}catch{}
   }));
  };
  const descriptor=role=>sockets[role].at(-1)?.plugins?.items?.[0];
  const view=(role,surface)=>{const d=descriptor(role);return surface?d?.views?.[surface]?.data:Object.values(d?.views||{})[0]?.data;};
  const presenter=await desktop.newPage();watch(presenter,"presenter");
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  await presenter.locator("#next").click();await presenter.locator("#next").click();
  const controls=presenter.locator(".presenter-controls");
  const action=name=>controls.getByRole("button",{name,exact:true}).click();
  await controls.getByRole("button",{name:"Open answers",exact:true}).waitFor();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const projector=await desktop.newPage();watch(projector,"projector");await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
  const mobile=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const phone=await mobile.newPage();watch(phone,"phone");await phone.goto(base+"/play?pin="+pin);
  await phone.locator("#nick").fill("Test learner");await phone.locator("#join button[type=submit]").click();
  const save=phone.getByRole("button",{name:"Save answer",exact:true});
  await save.waitFor();assert(await save.isDisabled());
  await action("Open answers");
  await save.click();await phone.getByRole("alert").filter({hasText:"nonempty"}).waitFor();
  async function setRelations(page,sets){
   const editor=page.locator(".nw-editor");
   while(await editor.locator("fieldset").count()<sets.length)await editor.getByRole("button",{name:"Add relation",exact:true}).click();
   while(await editor.locator("fieldset").count()>sets.length)await editor.getByRole("button",{name:/^Remove /}).last().click();
   for(let i=0;i<sets.length;i++){
    const row=editor.locator("fieldset").nth(i),inputs=row.locator('input[type="checkbox"]');
    for(let j=0;j<await inputs.count();j++){
     const input=inputs.nth(j);await input.setChecked(sets[i].includes(await input.getAttribute("aria-label")));
    }
   }
  }
  await setRelations(phone,[["S","N"],["S","C"],["C","T","I"],["I","O"]]);
  const otherContext=await browser.newContext({storageState:await mobile.storageState(),viewport:{width:390,height:844}});
  const other=await otherContext.newPage();watch(other);await other.goto(base+"/play?pin="+pin);await other.locator(".nw-editor").waitFor();
  const focused=phone.locator(".nw-editor input").first();await focused.focus();
  await action("Close answers");await action("Open answers");
  assert(await focused.evaluate(n=>document.activeElement===n));assert(await focused.isChecked());
  await setRelations(other,[["S","N"],["C","T","I"],["I","O"]]);
  await other.getByRole("button",{name:"Save answer",exact:true}).click();
  await phone.getByRole("button",{name:"Keep my draft",exact:true}).waitFor();
  assert(await focused.isChecked());
  await phone.getByRole("button",{name:"Keep my draft",exact:true}).click();
  // Keyboard activation, not a programmatic dispatch.
  await save.focus();await phone.keyboard.press("Enter");
  await until(()=>view("phone")?.answer_version===2&&view("phone")?.status==="checked","independent checked result");
  for(const role of ["phone","projector"]){
   const d=descriptor(role),v=view(role),s=JSON.stringify(d);
   assert(!v.worked&&!v.feedback&&!v.analysis&&!v.shared?.length);
   assert(!s.includes('"private":')&&!s.includes('"explanation":')&&!s.includes('"evaluations":'));
  }

  const bobContext=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const bob=await bobContext.newPage();watch(bob,"bob");await bob.goto(base+"/play?pin="+pin);
  await bob.locator("#nick").fill("Second learner");await bob.locator("#join button[type=submit]").click();
  await bob.locator(".nw-editor").waitFor();
  await setRelations(bob,[["S","N"],["S","C"],["C","T"],["C","I"],["I","O"]]);
  await bob.getByRole("button",{name:"Save answer",exact:true}).tap();
  await until(()=>view("bob")?.status==="checked","second valid answer");
  await action("Close answers");
  await action("Inspect privately 1");await presenter.getByText("Private selection",{exact:true}).waitFor();
  assert.equal(view("projector").shared.length,0);
  await action("Share with class 1");await projector.getByText("Shared answer",{exact:true}).waitFor();
  assert(!JSON.stringify(descriptor("projector")).includes("Test learner")&&!JSON.stringify(view("projector")).includes('"handle"'));
  await projector.screenshot({path:path.join(output,"projector-shared.png"),fullPage:true});
  await presenter.screenshot({path:path.join(output,"presenter-inspection.png"),fullPage:true});
  assert.equal(view("projector").shared[0].analysis,null,"answer-only sharing must not release checks");
  await action("Stop sharing");await action("Clear selection");
  await until(()=>view("presenter","presenter-controls")?.selected?.length===0,"cleared selection");
  await controls.getByLabel("Answer A",{exact:true}).selectOption({index:1});
  await controls.getByLabel("Answer B",{exact:true}).selectOption({index:2});
  await action("Compare privately");
  await until(()=>view("presenter","presenter-overlay")?.selected?.length===2,"private pair");
  assert.equal(view("projector").shared.length,0);
  await action("Share comparison and checks");
  await until(()=>view("projector")?.shared?.length===2,"shared pair");
  assert(view("projector").shared.every(a=>a.analysis.facts.join.lossless&&a.analysis.facts.preservation.preserved));
  assert(!JSON.stringify(view("projector")).includes('"handle"'));
  await projector.screenshot({path:path.join(output,"comparison-valid.png"),fullPage:true});
  // Reopening clears both projections. A new wrong answer needs fresh selection.
  await action("Open answers");
  await until(()=>view("projector")?.shared?.length===0,"unshared on reopen");
  await setRelations(bob,[["S","N"],["C","T","I"],["I","O"]]);
  await bob.getByRole("button",{name:"Save answer",exact:true}).tap();
  await until(()=>view("bob")?.answer_version===2&&view("bob")?.status==="checked","lossy replacement");
  await action("Close answers");
  await controls.getByLabel("Answer A",{exact:true}).selectOption({index:1});
  await controls.getByLabel("Answer B",{exact:true}).selectOption({index:2});
  await action("Compare privately");await action("Share comparison and checks");await action("Explain lossless join");
  await projector.getByText("The final relation satisfies every stated FD.",{exact:true}).waitFor();
  await projector.screenshot({path:path.join(output,"comparison-lossy.png"),fullPage:true});
  assert.equal(view("bob").analysis,null,"private phone evidence before reveal");
  await action("Stop sharing");await action("Clear selection");await action("Reveal answer");
  await until(()=>view("phone")?.feedback?.accepted===true,"reveal feedback");
  await phone.getByText("One worked answer",{exact:true}).waitFor();
  await until(()=>view("bob")?.analysis?.facts?.join?.lossless===false,"own lossy proof");
  await bob.locator("summary").filter({hasText:/^Explain lossless join$/}).click();
  await bob.getByText("The final relation satisfies every stated FD.",{exact:true}).waitFor();
  const trace=bob.locator(".nw-trace");
  await trace.locator("summary").click();
  const nextStep=trace.getByRole("button",{name:"Next step",exact:true});
  await nextStep.focus();await bob.keyboard.press("Enter");
  assert((await trace.getByRole("status").innerText()).startsWith("Step 1 /"));
  const previousStep=trace.getByRole("button",{name:"Previous step",exact:true});
  await previousStep.focus();await action("Inspect privately 1");await action("Overview");
  assert(await previousStep.evaluate(n=>document.activeElement===n));
  assert((await trace.getByRole("status").innerText()).startsWith("Step 1 /"));
  await previousStep.click();
  assert((await trace.getByRole("status").innerText()).startsWith("Step 0 /"));
  await trace.getByRole("button",{name:"Final table",exact:true}).click();
  assert.equal(await trace.getByRole("button",{name:"Next step",exact:true}).getAttribute("aria-disabled"),"true");
  await bob.screenshot({path:path.join(output,"phone-lossy-evidence.png"),fullPage:true});
  assert(!(await bob.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"proof table overflow");
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"320px overflow");
  await phone.screenshot({path:path.join(output,"phone-decomposition.png"),fullPage:true});
  await projector.screenshot({path:path.join(output,"projector-revealed.png"),fullPage:true});
  assert(await controls.getByRole("button",{name:"Open answers",exact:true}).isDisabled());
  // Reset never silently submits an old draft.
  await focused.uncheck();await action("Reset activity");
  await phone.getByRole("button",{name:"Load saved answer",exact:true}).waitFor();
  await phone.getByRole("button",{name:"Load saved answer",exact:true}).click();
  assert.equal(await phone.locator(".nw-editor input:checked").count(),0);
  assert.equal(view("phone").answer_version,0);
  // Classification with a checked FD witness.
  await presenter.locator("#next").click();await phone.getByLabel("Highest normal form").waitFor();await action("Open answers");
  await phone.getByLabel("Highest normal form").selectOption("3nf");await phone.locator("fieldset").getByLabel("U",{exact:true}).check();
  await phone.getByLabel("Right side",{exact:true}).selectOption("2");await save.tap();
  await until(()=>view("phone")?.status==="checked","classification result");
  await action("Close answers");await action("Reveal answer");await until(()=>view("phone")?.feedback?.accepted===true,"classification reveal");
  await phone.screenshot({path:path.join(output,"phone-classification.png"),fullPage:true});
  // Navigation/remount retains the authoritative saved answer.
  await presenter.locator("#next").click();await phone.getByRole("heading",{name:"A BCNF trade-off",exact:true}).waitFor();
  await presenter.locator("#prev").click();await phone.getByLabel("Highest normal form").waitFor();
  assert.equal(await phone.getByLabel("Highest normal form").inputValue(),"3nf");
  await presenter.locator("#next").click();await phone.getByRole("heading",{name:"A BCNF trade-off",exact:true}).waitFor();await action("Open answers");
  await setRelations(phone,[["S","U"],["T","U"]]);await save.tap();await until(()=>view("phone")?.status==="checked","tradeoff result");
  await action("Close answers");await action("Reveal answer");await until(()=>view("phone")?.feedback?.accepted===true,"tradeoff reveal");
  assert.equal(view("phone").feedback.preserved,false);
  await phone.locator("summary").filter({hasText:/^Explain FD preservation$/}).click();
  await phone.getByText("These two rows violate the original FD. Their projections still satisfy every component's projected FDs.",{exact:true}).waitFor();
  await phone.screenshot({path:path.join(output,"phone-lost-fd.png"),fullPage:true});
  await action("Share answer and checks 1");await action("Explain FD preservation");
  await projector.getByText(/Closure under the union of the projected FDs/).waitFor();
  await projector.screenshot({path:path.join(output,"projector-lost-fd.png"),fullPage:true});
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),"FD proof overflow");
  await presenter.locator("#next").click();await phone.locator(".participant-input").waitFor({state:"detached"});
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),modes:["classify","decompose"],viewport:320,
    installedWorker:true,privacy:true,draftAndFocus:true,keyboardActivation:true,touch:true,sameActorConflict:true,
     sharing:true,reset:true,navigationRestoresSaved:true,teardown:true,comparison:true,explicitChecksSharing:true,lossyCounterexample:true,lostFDExample:true,chasePlayback:true,proofFocusPreserved:true,errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(error){
  console.error(error.stack);fs.writeFileSync(path.join(output,"failure-error.txt"),String(error.stack));
  for(let i=0;i<pages.length;i++){
   await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
   fs.writeFileSync(path.join(output,"failure-"+i+".txt"),await pages[i].locator("body").innerText().catch(()=>""));
  }
  console.error("Browser errors:",errors);throw error;
 }finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{server.kill();log.end();});

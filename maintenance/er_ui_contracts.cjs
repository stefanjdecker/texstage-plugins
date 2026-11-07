// SPDX-License-Identifier: Apache-2.0
// Focused lifecycle/error probes using the installed renderer modules.
// These supplement, rather than substitute for, the real classroom scenario.
module.exports=async function(page,descriptor,presenterData,teaching,output){
 const result=await page.evaluate(async({descriptor,presenterData,teaching})=>{
  const assert=(ok,label)=>{if(!ok)throw new Error(label);};
  const make=async(surface,language="en",data=descriptor.public)=>{
   const container=document.createElement("div");document.body.append(container);
   container.style.cssText="position:relative;width:300px;background:white";
   const controller=new AbortController(),calls=[];
   let dispatch=async(op,payload)=>{calls.push({op,payload});return {accepted:true};};
   const module=await import(descriptor.modules[surface]);
   const ctx={container,item:{id:descriptor.item,...structuredClone(data)},role:surface==="participant-input"?"participant":"presenter",
    surface,language,clock:Date.now,signal:controller.signal,resolveAsset:()=>{throw Error("No assets");},
    dispatch:(...args)=>dispatch(...args)};
   const mounted=module.mount(ctx);
   return {container,controller,calls,mounted,setDispatch:f=>{dispatch=f;},dispose(){controller.abort();mounted.destroy();container.remove();}};
  };
  const check=(root,name)=>{const b=[...root.querySelectorAll("button")].find(n=>n.textContent===name);assert(b,"Missing "+name);return b;};
  const state=(epoch=1,version=0)=>({epoch,revision:version,data:{phase:"open",phase_version:1,active:true,count:version?1:0}});
  const setChoices=(root,choices)=>{
   for(const [d,o]of choices){const n=root.querySelector('[data-choice="'+d+":"+o+'"]');n.checked=true;n.dispatchEvent(new Event("change",{bubbles:true}));}
  };
  const valid=teaching.worked[0].answer.choices;
  const wait=()=>new Promise(r=>setTimeout(r,0));
  const test=await make("participant-input");test.mounted.update(state());
  setChoices(test.container,valid);
  const input=test.container.querySelector("textarea");input.value="Saved reason";input.dispatchEvent(new Event("input"));
  test.setDispatch(async()=>{throw Object.assign(new Error("opaque"),{code:"queue-full"});});
  check(test.container,"Save answer").click();await wait();
  assert(test.container.textContent.includes("Evaluation is busy. Please retry."),"Structured error code");
  assert(input.value==="Saved reason"&&!check(test.container,"Save answer").disabled,"Operational failure preserves draft and retry");
  // A late rejection from an older epoch must not disturb the reset decision.
  let reject;test.setDispatch(()=>new Promise((_resolve,r)=>{reject=r;}));
  check(test.container,"Save answer").click();
  test.mounted.update(state(2));check(test.container,"Keep my draft").click();
  reject(Object.assign(new Error("old"),{code:"stale-answer"}));await wait();
  assert(test.container.querySelector(".er-conflict").hidden,"Late rejection cannot resurrect obsolete conflict");
  assert(!check(test.container,"Save answer").disabled,"Kept reset draft is editable, not auto-sent");
  let sent;test.setDispatch(async(op,payload)=>{sent={op,payload};return {accepted:true};});
  check(test.container,"Save answer").click();await wait();input.value="Edited while saving";input.dispatchEvent(new Event("input"));
  const acknowledged=state(2,1);acknowledged.data.own={version:1,answer:{format:1,choices:valid},rationale:"Saved reason",status:"pending"};
  test.mounted.update(acknowledged);
  assert(input.value==="Edited while saving"&&test.container.textContent.includes("Draft; not saved yet."),"In-flight edits survive own acknowledgement");
  assert(sent.payload.answer_version===0&&sent.payload.phase_version===1,"Semantic versions");
  // Untrusted labels remain plain text. No HTML injection in any public-derived preview.
  assert(!test.container.querySelector("script"),"No injected script");
  test.dispose();assert(!test.container.isConnected,"destroy removes mount");
  const controls=await make("presenter-controls");
  const d=structuredClone(presenterData);d.page=0;d.pages=4;d.control_version=9;
  controls.mounted.update({epoch:4,revision:20,data:d});
  check(controls.container,"Next answers").click();await wait();
  assert(JSON.stringify(controls.calls[0])===JSON.stringify({op:"set-page",payload:{control_version:9,page:1}}),"Paging command");
  d.page=3;controls.mounted.update({epoch:4,revision:21,data:d});
  assert(check(controls.container,"Next answers").disabled,"Last page disabled");
  controls.dispose();
  // German labels, unknown choices, safe authored text, actual localized submit.
  const publicData=structuredClone(descriptor.public);
  publicData.labels.entities[0].text.de="Teilnehmende Kursteilnehmerin";
  publicData.labels.entities[1].text.de="Fortbildungsworkshop";
  publicData.labels.relationship.de="Verbindliche Workshopanmeldung";
  const german=await make("participant-input","de",publicData);
  german.container.id="er-german-probe";german.mounted.update(state());
  assert(german.container.querySelector("section").lang==="de","German language semantics");
  assert(german.container.querySelectorAll("fieldset").length===3,"Three decisions");
  assert(!german.container.querySelector("input:checked"),"Empty public-only preview");
  setChoices(german.container,valid);check(german.container,"Modell ansehen").click();
  assert(german.container.textContent.includes("Jede einzelne Entität Teilnehmende Kursteilnehmerin nimmt an"),"Localized endpoint orientation");
  check(german.container,"Zurück zu den Entscheidungen").click();check(german.container,"Antwort speichern").click();await wait();
  assert(german.calls[0].op==="submit","German submit");
  assert(german.container.scrollWidth<=german.container.clientWidth+1,"Long German phone layout");
  // Keep the probe mounted for a real screenshot, then clean up from the caller.
  globalThis.__erProbeDispose=()=>german.dispose();
  return {operationalError:true,lateRejection:true,inFlightDraft:true,paging:true,german:true,teardown:true};
 },{descriptor,presenterData,teaching});
 await page.locator("#er-german-probe").screenshot({path:require("node:path").join(output,"german-decisions.png")});
 await page.evaluate(()=>{globalThis.__erProbeDispose();delete globalThis.__erProbeDispose;});
 return result;
};


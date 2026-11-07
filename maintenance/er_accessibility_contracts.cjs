// SPDX-License-Identifier: Apache-2.0
// Installed-renderer checks; live regions/DOM semantics are not speech output.
module.exports=async(page,descriptor,language)=>page.evaluate(async({descriptor,language})=>{
 const assert=(ok,label)=>{if(!ok)throw Error(label);};
 const module=await import(descriptor.modules["participant-input"]);
 const instances=[];
 const make=()=>{
  const container=document.createElement("div");document.body.append(container);
  const controller=new AbortController(),calls=[];
  const mounted=module.mount({container,item:{id:descriptor.item,...structuredClone(descriptor.public)},
   language,signal:controller.signal,dispatch:async(...args)=>{calls.push(args);return {accepted:true};}});
  const state={epoch:1,revision:0,data:{phase:"open",phase_version:1,active:true,count:0}};
  mounted.update(state);const row={container,controller,mounted,state,calls};instances.push(row);return row;
 };
 const settle=()=>new Promise(r=>setTimeout(r,0));
 try{
  const a=make(),b=make(),input=a.container.querySelector("input"),other=b.container.querySelector("input");
  input.checked=true;input.dispatchEvent(new Event("change"));other.checked=true;other.dispatchEvent(new Event("change"));
  assert(input.checked&&other.checked,"Independent mounts must not share a radio group");
  assert(input.name!==other.name,"Scoped radio names");
  const ids=[...document.querySelectorAll("[id]")].map(n=>n.id);
  for(const node of a.container.querySelectorAll("[id]"))assert(ids.filter(id=>id===node.id).length===1,"Unique error IDs");
  const live=[...a.container.querySelectorAll('[role="status"],[role="alert"]')];
  let mutations=0;const observer=new MutationObserver(rows=>{mutations+=rows.length;});
  live.forEach(node=>observer.observe(node,{childList:true,characterData:true,subtree:true}));
  input.focus();
  for(let i=0;i<8;i++)a.mounted.update({...a.state,revision:i+1,data:{...a.state.data,count:i+1}});
  await settle();assert(mutations===0,"Unrelated count/revision updates must not repeat live announcements");
  assert(document.activeElement===input,"Unrelated updates preserve input focus");
  a.mounted.update({...a.state,revision:10,data:{...a.state.data,phase:"closed",phase_version:2}});
  await settle();assert(mutations===1,"A phase transition changes exactly its live message");
  mutations=0;a.mounted.update({...a.state,revision:11,data:{...a.state.data,phase:"closed",phase_version:2,count:42}});
  await settle();assert(mutations===0,"Unchanged closed phase is not re-announced");observer.disconnect();
  a.mounted.update(a.state);
  const buttons=[...a.container.querySelectorAll("button")];
  const preview=buttons.find(n=>n.textContent===(language==="de"?"Modell ansehen":"View model"));preview.click();
  const model=a.container.querySelector(".er-model"),list=model.querySelector("ul");
  a.mounted.update({...a.state,revision:12,data:{...a.state.data,count:50}});
  assert(a.container.querySelector(".er-model")===model&&model.querySelector("ul")===list,"Unchanged preview preserves reading nodes");
  assert(model.querySelector(".er-diagram").getAttribute("aria-hidden")==="true","Diagram has a separate textual alternative");
  // Preview focus must remain visible for either explicit conflict choice.
  for(const name of language==="de"?["Meinen Entwurf behalten","Gespeicherte Antwort laden"]:["Keep my draft","Reload saved answer"]){
   input.checked=true;input.dispatchEvent(new Event("change"));a.state.epoch++;
   a.mounted.update(structuredClone(a.state));
   const conflict=a.container.querySelector(".er-conflict");assert(!conflict.hidden,"Conflict shown");
   assert(conflict.querySelector('[role="alert"]').textContent,"Conflict announcement");
   [...conflict.querySelectorAll("button")].find(n=>n.textContent===name).click();
   assert(document.activeElement.tagName==="H3"&&document.activeElement.getClientRects().length,"Restore visible preview heading");
   assert(a.calls.length===0,"Conflict choices never submit");
  }
  buttons.find(n=>n.textContent===(language==="de"?"Zurück zu den Entscheidungen":"Back to decisions")).click();
  input.checked=true;input.dispatchEvent(new Event("change"));a.state.epoch++;a.mounted.update(structuredClone(a.state));
  [...a.container.querySelector(".er-conflict").querySelectorAll("button")].find(n=>n.textContent===(language==="de"?"Meinen Entwurf behalten":"Keep my draft")).click();
  assert(document.activeElement===input&&input.getClientRects().length,"Editing conflict restores first decision focus");
  assert(a.calls.length===0,"Editing conflict never submits");
  return {isolatedRadioGroups:true,uniqueIds:true,stableAnnouncements:true,phaseAnnouncement:true,
   focusPreserved:true,stablePreviewNodes:true,conflictFocus:true,noAutomaticSubmission:true};
 }finally{for(const row of instances){row.controller.abort();row.mounted.destroy();row.container.remove();}}
},{descriptor,language});

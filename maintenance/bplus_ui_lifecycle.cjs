// SPDX-License-Identifier: Apache-2.0
// Controlled completion ordering for the installed UI modules. The main browser
// harness separately exercises authenticated commands against the real host.
module.exports=async function lifecycle(page,urls,sources){
 return page.evaluate(async({urls,sources})=>{
  const participant=await import(urls.participant),controls=await import(urls.controls),overlay=await import(urls.overlay);
  const check=(condition,message)=>{if(!condition)throw Error("UI lifecycle: "+message);};
  const wait=()=>new Promise(resolve=>setTimeout(resolve,25));
  const item=s=>({format:1,id:"lifecycle",title:s.title,prompt:s.prompt,exercise:s.exercise,interaction:"classroom"});
  const base=(epoch=1,revision=1,data={})=>({epoch,revision,data:{
   format:2,phase:"open",phase_version:1,active:true,count:1,...data}});
  const own=(answer,version=1)=>({version,answer,status:"saved"});
  const make=(module,source,role="participant")=>{
   const container=document.createElement("div");document.body.append(container);
   const controller=new AbortController(),requests=[];
   const ctx={container,item:item(source),role,surface:role==="participant"?"participant-input":"presenter-controls",
    language:"en",signal:controller.signal,dispatch(op,payload){
     return new Promise((resolve,reject)=>requests.push({op,payload,resolve,reject}));
    }};
   const handle=module.mount(ctx);
   return {container,handle,requests,controller,
    get:name=>container.querySelector('[data-bp="'+name+'"]'),
    field:name=>container.querySelector('[data-bp-field="'+name+'"]'),
    destroy(){controller.abort();handle.destroy();check(container.childElementCount===0,"disposed root remains");container.remove();}};
  };
  const lookup=sources.lookup,insert=sources.insert,answer=lookup.worked.answer;
  const a=make(participant,lookup);a.handle.update(base(1,1,{own:own(answer)}));
  a.get("submit").click();check(a.requests.length===1,"submission missing");
  a.field("keys").value="-9999";a.field("keys").dispatchEvent(new Event("input"));
  // The view can arrive before its command receipt. Edits made while saving survive.
  a.handle.update(base(1,2,{own:own(answer,2)}));
  a.requests[0].resolve({epoch:1,revision:2});await wait();
  check(a.field("keys").value==="-9999"&&!a.get("submit").disabled&&a.get("conflict").hidden,"view-before-receipt discarded edit");
  a.get("submit").click();check(a.requests.length===2,"replacement missing");
  a.handle.update(base(2,0,{phase:"introduce",phase_version:0,count:0}));
  a.requests[1].resolve({epoch:1,revision:3});await wait();
  check(!a.get("conflict").hidden&&a.field("keys").value==="-9999","late receipt replaced reset draft");
  a.get("keep").click();check(a.requests.length===2,"keep draft submitted automatically");
  a.handle.update(base(2,1,{count:0}));a.get("submit").click();
  check(a.requests.length===3&&a.requests[2].payload.answer_version===0,"reset did not rebase explicitly kept draft");
  a.destroy();a.requests[2].resolve({epoch:2,revision:2});await wait();
  check(a.container.childElementCount===0,"late receipt revived participant");

  const b=make(participant,lookup);b.handle.update(base(1,1,{own:own(answer)}));
  b.get("submit").click();b.requests[0].reject(Object.assign(new Error("queue full"),{code:"queue-full"}));await wait();
  check(!b.get("submit").disabled&&b.get("error").textContent.length>0,"operational refusal locked draft");
  check(b.field("keys").value===answer.keys.join(", "),"refusal cleared answer");
  b.get("submit").click();b.requests[1].reject(Object.assign(new Error("stale"),{code:"stale-answer"}));await wait();
  check(!b.get("conflict").hidden&&b.get("submit").disabled,"stale answer conflict missing");
  b.get("reload").click();check(b.get("conflict").hidden&&!b.get("submit").disabled,"load saved did not resolve conflict");b.destroy();

  const c=make(participant,insert);c.handle.update(base(1,1,{own:own(insert.worked.answer)}));
  c.field("repair-0-op").focus();c.field("repair-0-op").value="borrow";c.field("repair-0-op").dispatchEvent(new Event("change"));
  check(document.activeElement===c.field("repair-0-op"),"structural field lost focus");
  c.get("undo").click();
  const remove=c.get("remove-repair");remove.focus();remove.click();
  check(document.activeElement===c.get("add-repair"),"removed repair lost keyboard focus");
  c.get("undo").click();check(c.field("repair-0-op").value==="split","undo failed structural edit");
  const child=c.get("focused-page").querySelector("button");
  if(child){child.focus();child.click();check(document.activeElement===c.get("focus"),"page navigation lost focus");}
  c.get("preview").click();c.field("height").value="2";c.field("height").dispatchEvent(new Event("change"));await wait();
  check(c.get("preview-frame").parentElement.hidden,"obsolete preview became visible");
  check(c.requests.length===0,"preview/edit sent a command");
  c.get("undo").click();c.get("preview").click();c.destroy();await wait();
  check(c.container.childElementCount===0,"late preview revived participant");

  const d=make(controls,lookup,"presenter");
  const controlData={control_version:1,counts:{pending:0,saved:0,unavailable:0},participants:[]};
  d.handle.update(base(1,1,controlData));d.get("close").click();check(d.requests.length===1,"close missing");
  d.handle.update(base(2,0,{...controlData,phase:"introduce",control_version:0}));
  d.requests[0].resolve({epoch:1,revision:2});await wait();
  check(!d.get("open").disabled&&d.get("close").disabled,"late presenter receipt restored old controls");
  d.get("open").click();d.destroy();d.requests[1].resolve({epoch:2,revision:1});await wait();
  check(d.container.childElementCount===0,"late receipt revived controls");

  const e=make(overlay,insert,"presenter");
  e.handle.place({box:{x:0,y:0,w:900,h:500}});
  const revealed={phase:"revealed",worked:{answer:insert.worked.answer,explanation:insert.worked.explanation}};
  e.handle.update(base(1,1,revealed));e.handle.update(base(2,0,{phase:"introduce"}));await wait();
  check(e.container.querySelector(".bp-overlay").hidden,"obsolete preview exposed hidden overlay");
  e.handle.update(base(2,1,revealed));e.destroy();await wait();
  check(e.container.childElementCount===0,"late preview revived overlay");
  const tree=await import(new URL("tree-view.mjs",urls.participant).href);
  const large=tree.treeView("en",new AbortController().signal,{presentation:true});
  large.update(sources.large.exercise.tree);
  check(large.root.querySelector("svg").viewBox.baseVal.width===1000,"large tree was shrunk instead of focused");
  check(large.root.textContent.includes("Large tree:"),"large-tree partial-view notice missing");
  return {viewBeforeReceipt:true,editWhileSaving:true,lateReceiptAfterReset:true,lateReceiptAfterDestroy:true,
   refusalKeepsDraft:true,staleAnswerConflict:true,structuralFocus:true,obsoletePreview:true,disposedPreview:true,
   presenterReset:true,overlayTeardown:true,largeTreeFocus:true};
 },{urls,sources});
};

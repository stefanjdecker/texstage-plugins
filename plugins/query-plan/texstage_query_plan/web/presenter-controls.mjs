// SPDX-License-Identifier: Apache-2.0
import {words,el,button,field,option,details,shell,feedback,commandError,delivered,number,local} from "./lesson-ui.mjs";
import {planView} from "./cost-inspector.mjs";
import {key} from "./plan-editor.mjs";
export function mount(ctx) {
 const w=words(ctx.language),root=shell(ctx,"qp-controls"),panel=details(w.title),body=el("div",undefined,{class:"qp-panel"});
 function position(){
  if(!panel.open)return;
  const top=panel.firstElementChild.getBoundingClientRect().top;
  body.style.bottom=Math.max(12,innerHeight-top+8)+"px";
  body.style.maxHeight=Math.max(160,top-24)+"px";
 }
 panel.addEventListener("toggle",position,{signal:ctx.signal});
 window.addEventListener("resize",position,{signal:ctx.signal});
 const dismiss=button(w.dismiss,()=>{panel.open=false;panel.firstElementChild.focus();},ctx.signal);
 root.addEventListener("keydown",event=>{if(event.key==="Escape"&&panel.open){event.stopPropagation();panel.open=false;panel.firstElementChild.focus();}},{signal:ctx.signal});
 root.append(el("style",`
 .qp-controls{padding:3px 8px;background:#f1f6fa}.qp-controls>details>summary{padding:5px;min-height:44px}
 .qp-controls .qp-panel{position:fixed;left:12px;bottom:76px;width:min(620px,calc(100vw - 24px));max-height:70vh;overflow:auto;background:#fff;padding:14px;border:2px solid #457ba1;border-radius:8px;box-shadow:0 4px 24px #0005;z-index:100}
 .qp-controls button{height:auto;min-height:44px;padding:8px}
 `));
 const phase=el("p",undefined,{"aria-live":"polite"}),counts=el("p"),error=el("p",undefined,{role:"alert"}),waiting=el("p",undefined,{role:"status"});
 let current=null,busy=false,receipt=null,alive=true,generation=0,rosterKey="",selectedKey="",solutionKey="",confirming=false;
 const buttons={};const actions=el("div",undefined,{class:"qp-actions"});
 for(const [op,text]of[["open",w.openButton],["close",w.closeButton],["reveal",w.reveal]]){
  buttons[op]=button(text,()=>send(op),ctx.signal);actions.append(buttons[op]);
 }
 const reset=button(w.reset,()=>{confirming=true;confirmBox.hidden=false;paint();confirm.focus();},ctx.signal);
 actions.append(reset);
 const confirmBox=el("div",undefined,{class:"qp-conflict"});confirmBox.hidden=true;
 const confirm=button(w.confirm,()=>{confirming=false;confirmBox.hidden=true;send("_reset");},ctx.signal);
 const cancel=button(w.cancel,()=>{confirming=false;confirmBox.hidden=true;paint();reset.focus();},ctx.signal);
 confirmBox.append(el("p",w.resetConfirm),confirm,cancel);
 const roster=el("select",undefined,{"data-qp":"roster"});roster.append(option("",w.none));
 roster.addEventListener("change",paint,{signal:ctx.signal});
 buttons.inspect=button(w.inspect,()=>send("select-answer",{actor:roster.value||null}),ctx.signal);
 buttons.share=button(w.share,()=>send("share-selected"),ctx.signal);
 buttons.clear=button(w.clear,()=>send("clear-shared"),ctx.signal);
 const shareActions=el("div",undefined,{class:"qp-actions"});shareActions.append(buttons.inspect,buttons.share,buttons.clear);
 const selected=el("section",undefined,{class:"qp-private","aria-label":w.inspect}),selectedStatus=el("p");
 const selectedView=planView(ctx.item.exercise,ctx.language,ctx.signal);selected.append(selectedStatus,selectedView.root);selected.hidden=true;
 const solution=details(w.private+" — "+w.worked),solutionView=planView(ctx.item.exercise,ctx.language,ctx.signal),explanation=el("p"),minimum=el("p");
 const optimal=details(w.optimal),optimalView=planView(ctx.item.exercise,ctx.language,ctx.signal);optimal.append(optimalView.root);
 solution.append(explanation,minimum,solutionView.root,optimal);
 body.append(dismiss,el("h2",w.title),phase,counts,actions,confirmBox,error,waiting,field(w.select,roster),shareActions,selected,solution);
 panel.append(body);root.append(panel);
 function paint(){
  const d=current?.data;
  if(d){
   phase.textContent=w.phase+": "+w[d.phase]+" · "+w.count+": "+d.count;
   counts.textContent=Object.entries(d.counts).map(([k,n])=>(k==="pending"?w.pendingLabel:k==="unavailable"?w.unavailableLabel:w[k])+": "+n).join(" · ");
  }
  const lock=!d?.active||busy||confirming;
  buttons.open.disabled=lock||!["introduce","closed"].includes(d?.phase);
  buttons.close.disabled=lock||d?.phase!=="open";
  buttons.reveal.disabled=lock||d?.phase!=="closed";
  reset.disabled=lock;
  buttons.inspect.disabled=lock||!roster.value;buttons.share.disabled=lock||!d?.selected;
  buttons.clear.disabled=lock||!d?.demonstration;roster.disabled=busy||confirming;
  waiting.textContent=busy?w.waiting:"";
 }
 async function send(op,payload={}){
  if(!current||busy||!alive)return;
  const token=generation;busy=true;receipt=null;error.textContent="";paint();
  try{
   const received=await ctx.dispatch(op,op==="_reset"?{}:{control:current.data.control_version,...payload});
   if(!alive||generation!==token)return;
   receipt=received;
   if(delivered(current,receipt)){busy=false;receipt=null;}
  }catch(e){
   if(!alive||generation!==token)return;busy=false;receipt=null;error.textContent=commandError(e,w);
  }
  if(alive)paint();
 }
 paint();
 return {
  update(view){
   if(!alive)return;
   if(current&&current.epoch!==view.epoch){generation++;busy=false;receipt=null;confirming=false;confirmBox.hidden=true;error.textContent="";}
   current=view;const d=view.data;
   if(receipt&&delivered(view,receipt)){busy=false;receipt=null;}
   const rk=key(d.participants);
   if(rk!==rosterKey){
    rosterKey=rk;const value=roster.value;
    roster.replaceChildren(option("",w.none),...d.participants.map(p=>option(p.actor,w.response+" "+p.number+" — "+(p.status==="pending"?w.pendingLabel:p.status==="unavailable"?w.unavailableLabel:w[p.status]))));
    if(d.participants.some(p=>p.actor===value))roster.value=value;
   }
   selected.hidden=!d.selected;const sk=key(d.selected);
   if(d.selected&&sk!==selectedKey){selectedStatus.textContent=w.private+": "+feedback(d.selected,w,ctx.language);selectedView.update(d.selected.answer);}
   selectedKey=sk;
   const sol=key(d.solution);
   if(sol!==solutionKey&&d.solution){
    solutionKey=sol;explanation.textContent=local(d.solution.explanation,ctx.language);
    minimum.textContent=w.minimum+": "+number(d.solution.minimum,ctx.language)+" · "+w.ties+": "+d.solution.ties;
    solutionView.update(d.solution.worked_answer);
    optimal.hidden=key(d.solution.worked_answer)===key(d.solution.optimal_answer);
    if(!optimal.hidden)optimalView.update(d.solution.optimal_answer);
   }
   paint();
  },
  destroy(){alive=false;generation++;root.remove();}
 };
}

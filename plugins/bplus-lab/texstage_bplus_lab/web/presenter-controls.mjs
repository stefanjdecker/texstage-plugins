// SPDX-License-Identifier: Apache-2.0
import {key,steps,preview} from "./editor-model.mjs";
import {words,local,el,button,field,option,details,shell,feedback,rubricView,gradeView,commandError,delivered,setText,taskText} from "./ui.mjs";
import {treeView} from "./tree-view.mjs";
import {answerView,stepLabel} from "./answer-view.mjs";
export function mount(ctx) {
  const w=words(ctx.language),root=shell(ctx,"bp-controls"),panel=details(w.controls),body=el("div",undefined,{class:"bp-panel","data-bp":"controls-panel"});
  const phase=el("p",undefined,{role:"status"}),counts=el("p"),error=el("p",undefined,{role:"alert","data-bp":"control-error"}),waiting=el("p",undefined,{role:"status"});
  const actions=el("div",undefined,{class:"bp-actions"}),buttons={},roster=el("select",undefined,{"data-bp":"roster"});
  const pageLabel=el("p",undefined,{role:"status","data-bp":"roster-page"});
  const pagePrevious=button(w.rosterPrevious,()=>send("roster-page",{page:current.data.roster_page.page-1}),ctx.signal,{"data-bp":"roster-previous"});
  const pageNext=button(w.rosterNext,()=>send("roster-page",{page:current.data.roster_page.page+1}),ctx.signal,{"data-bp":"roster-next"});
  const pageActions=el("div",undefined,{class:"bp-actions"});pageActions.append(pagePrevious,pageLabel,pageNext);
  const selected=el("section",undefined,{class:"bp-private","data-bp":"inspection"}),selectedBody=el("div"),selectedStatus=el("p",undefined,{role:"status"});
  const previewBox=el("div"),previewStatus=el("p",undefined,{role:"status"}),selectedTree=treeView(ctx.language,ctx.signal);
  const revealBox=details(w.worked),source=el("select",undefined,{"data-bp":"replay-source"}),cursor=el("p",undefined,{role:"status","data-bp":"replay-cursor"});
  let current=null,busy=false,receipt=null,alive=true,generation=0,previewGeneration=0,rosterKey="",selectedKey="",workedKey="",cursorKey="",confirming=false;
  const dismiss=button(w.dismiss,()=>{panel.open=false;panel.firstElementChild.focus();},ctx.signal,{"data-bp":"dismiss-controls"});
  root.addEventListener("keydown",event=>{
    if(event.key==="Escape"&&panel.open){event.stopPropagation();panel.open=false;panel.firstElementChild.focus();}
  },{signal:ctx.signal});
  for(const [op,label]of [["open",w.openButton],["close",w.closeButton],["reveal",w.reveal]]) {
    buttons[op]=button(label,()=>send(op),ctx.signal,{"data-bp":op});actions.append(buttons[op]);
  }
  const reset=button(w.reset,()=>{confirming=true;confirmBox.hidden=false;paint();confirm.focus();},ctx.signal,{"data-bp":"reset"});
  const confirmBox=el("div",undefined,{class:"bp-conflict"}),confirm=button(w.confirm,()=>{
    confirming=false;confirmBox.hidden=true;send("_reset");
  },ctx.signal,{"data-bp":"confirm-reset"}),cancel=button(w.cancel,()=>{confirming=false;confirmBox.hidden=true;paint();reset.focus();},ctx.signal);
  confirmBox.append(el("p",w.confirmReset),confirm,cancel);confirmBox.hidden=true;actions.append(reset);
  roster.append(option("",w.none));roster.addEventListener("change",paint,{signal:ctx.signal});
  const inspect=button(w.inspect,()=>{
    const row=current.data.participants.find(p=>p.actor===roster.value);
    if(row)send("select-answer",{actor:row.actor,answer_version:row.version});
  },ctx.signal,{"data-bp":"inspect"});
  const clearInspection=button(w.clearInspection,()=>send("select-answer",{actor:"",answer_version:0}),ctx.signal,{"data-bp":"clear-inspection"});
  const share=button(w.share,()=>{
    const row=current?.data.selected;if(row)send("share-answer",{actor:row.actor,answer_version:row.version});
  },ctx.signal,{"data-bp":"share"});
  const clearShare=button(w.clearShare,()=>send("clear-share"),ctx.signal,{"data-bp":"clear-share"});
  const shareActions=el("div",undefined,{class:"bp-actions"});shareActions.append(inspect,clearInspection,share,clearShare);
  const simulate=button(w.showPreview,async()=>{
    if(!current?.data.selected)return;
    const token=++previewGeneration,answer=current.data.selected.answer;
    previewBox.hidden=false;selectedTree.root.hidden=true;setText(previewStatus,w.previewBusy);
    try{
      const result=await preview(ctx.item.exercise,answer,{signal:ctx.signal,valid:()=>alive&&token===previewGeneration});
      if(!result||!alive||token!==previewGeneration)return;
      const frame=result.frames.at(-1);selectedTree.update(frame.tree,{pending:frame.pending});selectedTree.root.hidden=false;
      setText(previewStatus,result.facts.replay.state==="complete"?w.previewComplete:w.previewStopped+": "+w.reason[result.facts.replay.reason]);
    }catch{if(alive&&token===previewGeneration)setText(previewStatus,w.invalid);}
  },ctx.signal,{"data-bp":"inspect-preview"});
  previewBox.append(previewStatus,selectedTree.root);previewBox.hidden=true;
  selected.append(el("h3",w.private),selectedStatus,selectedBody,simulate,previewBox);
  const previous=button(w.previous,()=>move(-1),ctx.signal,{"data-bp":"replay-previous"}),next=button(w.next,()=>move(1),ctx.signal,{"data-bp":"replay-next"});
  source.addEventListener("change",paint,{signal:ctx.signal});
  const replayActions=el("div",undefined,{class:"bp-actions"});replayActions.append(previous,next);
  body.append(dismiss,el("h2",w.title),el("p",taskText(ctx.item.exercise,w)),rubricView(ctx.item,w),phase,counts,actions,confirmBox,error,waiting,
    pageActions,field(w.roster,roster),shareActions,selected,el("h3",w.replay),field(w.source,source),cursor,replayActions,revealBox);
  panel.append(body);root.append(panel);
  function currentAnswer(){
    return source.value==="shared"?current?.data.demonstration?.answer:source.value==="worked"?current?.data.worked?.answer:null;
  }
  function position(){
    const replay=current?.data.replay;return replay?.source===source.value?replay.step:-1;
  }
  function move(delta){
    const answer=currentAnswer();if(!answer)return;
    const step=Math.max(0,Math.min(steps(answer).length-1,position()+delta));
    send("replay-step",{source:source.value,step});
  }
  function paint(){
    const d=current?.data,lock=!d?.active||busy||confirming;
    if(d){
      setText(phase,w.phase+": "+w[d.phase]+" · "+w.count+": "+d.count);
      setText(counts,["pending","saved","unavailable"].map(s=>w["status"+s[0].toUpperCase()+s.slice(1)]+": "+d.counts[s]).join(" · "));
    }
    buttons.open.disabled=lock||!["introduce","closed"].includes(d?.phase);
    buttons.close.disabled=lock||d?.phase!=="open";buttons.reveal.disabled=lock||d?.phase!=="closed";reset.disabled=lock;
    pagePrevious.disabled=lock||!d||d.roster_page.page===0;
    pageNext.disabled=lock||!d||d.roster_page.page+1>=d.roster_page.pages;
    if(d)setText(pageLabel,w.rosterPage+" "+(d.roster_page.page+1)+" / "+d.roster_page.pages);
    inspect.disabled=lock||!roster.value;clearInspection.disabled=lock||!d?.selected;
    share.disabled=lock||!d?.selected||!["closed","revealed"].includes(d?.phase);
    clearShare.disabled=lock||!d?.demonstration;roster.disabled=busy||confirming;source.disabled=lock;
    const answer=currentAnswer(),at=position(),total=answer?steps(answer).length:0;
    previous.disabled=lock||!answer||at<=0;next.disabled=lock||!answer||at>=total-1;
    setText(cursor,answer?w.step+" "+(at+1)+" / "+total+" · "+stepLabel(at>=0?steps(answer)[at]:null,w):w.none);
    setText(waiting,busy?w.waiting:"");
  }
  async function send(op,payload={}){
    if(!current||busy||!alive)return;
    const token=generation;busy=true;receipt=null;error.textContent="";paint();
    try{
      const r=await ctx.dispatch(op,op==="_reset"?{}:{control_version:current.data.control_version,...payload});
      if(!alive||token!==generation)return;receipt=r;
      if(delivered(current,r)){busy=false;receipt=null;}
    }catch(e){if(!alive||token!==generation)return;busy=false;receipt=null;setText(error,commandError(e,w));}
    paint();
  }
  paint();
  return {
    update(view){
      if(!alive)return;
      if(current&&current.epoch!==view.epoch){generation++;previewGeneration++;busy=false;receipt=null;confirming=false;confirmBox.hidden=true;error.textContent="";}
      current=view;const d=view.data;
      if(receipt&&delivered(view,receipt)){busy=false;receipt=null;}
      const rk=key(d.participants);
      if(rk!==rosterKey){
        const old=roster.value;rosterKey=rk;
        roster.replaceChildren(option("",w.none),...d.participants.map((p,i)=>option(p.actor,w.response+" "+p.number+" · "+w["status"+p.status[0].toUpperCase()+p.status.slice(1)]+" · v"+p.version)));
        if(d.participants.some(p=>p.actor===old))roster.value=old;
      }
      const sk=key(d.selected);selected.hidden=!d.selected;
      if(sk!==selectedKey){
        selectedKey=sk;previewGeneration++;previewBox.hidden=true;
        if(d.selected){setText(selectedStatus,feedback(d.selected,w));selectedBody.replaceChildren(gradeView(d.selected.feedback?.grade,ctx.item,w),answerView(d.selected.answer,ctx.language));}
        else selectedBody.replaceChildren();
      }
      const wk=key(d.worked);revealBox.hidden=!d.worked;
      if(wk!==workedKey){workedKey=wk;revealBox.replaceChildren(el("summary",w.worked));
        if(d.worked)revealBox.append(el("p",local(d.worked.explanation,ctx.language)),answerView(d.worked.answer,ctx.language));}
      const available=[...(d.demonstration?[["shared",w.shared]]:[]),...(d.worked?[["worked",w.worked]]:[])];
      const nextKey=key([available,d.replay]);
      if(nextKey!==cursorKey){
        const old=source.value;cursorKey=nextKey;source.replaceChildren(...available.map(([v,t])=>option(v,t)));
        if(d.replay&&available.some(([v])=>v===d.replay.source))source.value=d.replay.source;
        else if(available.some(([v])=>v===old))source.value=old;
      }
      paint();
    },
    destroy(){alive=false;generation++;previewGeneration++;root.remove();}
  };
}

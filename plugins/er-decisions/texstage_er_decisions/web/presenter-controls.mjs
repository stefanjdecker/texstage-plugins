// SPDX-License-Identifier: Apache-2.0
import {el,button,shell,words,feedback,errorText,decisionText,setText} from "./lesson-ui.mjs";
import {modelView} from "./diagram.mjs";
import {teachingPanel} from "./teaching.mjs";
export function mount(ctx) {
  const w=words(ctx.language),root=shell(ctx),phase=el("p"),counts=el("p"),error=el("p","",{role:"alert"});
  const phaseText=el("span","",{role:"status","aria-live":"polite","aria-atomic":"true"}),countText=el("span");phase.append(phaseText,countText);
  // The host places controls in its toolbar. Bound this surface so expanded
  // inspections cannot consume the slide-preview row above it.
  Object.assign(root.style,{maxHeight:"40vh",overflow:"auto",width:"min(800px, calc(100vw - 32px))"});
  let current,busy=false,roster="",selection="",detailKey="";
  const send=async(op,extra={})=>{
    if(!current||busy)return;
    busy=true;error.textContent="";draw();
    try{await ctx.dispatch(op,op==="_reset"?{}:{control_version:current.data.control_version,...extra});}
    catch(e){error.textContent=errorText(e,w);}finally{busy=false;draw();}
  };
  const open=button(w.openButton,()=>send("open"),ctx.signal),close=button(w.closeButton,()=>send("close"),ctx.signal);
  const reveal=button(w.reveal,()=>send("reveal"),ctx.signal);
  const reset=button(w.reset,()=>{if(globalThis.confirm(ctx.item.points?w.scoredReset:w.resetConfirm))send("_reset");},ctx.signal);
  const points=el("p",ctx.item.points?ctx.item.points+" "+w.pointsRule:"");points.hidden=!ctx.item.points;
  const round=el("p",w.scoredRound,{hidden:""});
  const select=el("select",undefined,{"aria-label":w.inspect}),page=el("span","",{role:"status","aria-live":"polite","aria-atomic":"true"});
  const prev=button(w.previous,()=>send("set-page",{page:current.data.page-1}),ctx.signal);
  const next=button(w.next,()=>send("set-page",{page:current.data.page+1}),ctx.signal);
  const target=()=>current.data.participants.find(r=>r.actor===select.value);
  const inspect=button(w.inspect,()=>{const r=target();send("select-answer",{actor:r?.actor||"",answer_version:r?.version||0});},ctx.signal);
  const include=el("input",undefined,{type:"checkbox"}),includeLabel=el("label",undefined,{class:"er-option"});
  includeLabel.append(include,el("span",w.include));
  const share=button(w.share,()=>{const s=current.data.selected;if(s)send("share-answer",{actor:s.actor,answer_version:s.version,include_rationale:include.checked});},ctx.signal);
  const clear=button(w.clear,()=>send("clear-share"),ctx.signal);
  const detail=el("div"),optionDetails=el("details"),optionBody=el("div");
  optionDetails.append(el("summary",w.options),optionBody);
  root.append(phase,points,open,close,reveal,reset,round,counts,optionDetails,prev,page,next,el("p",w.inspect),select,inspect,detail,includeLabel,share,clear,error);
  const teaching=teachingPanel(ctx,root);
  select.addEventListener("change",()=>{include.checked=false;draw();},{signal:ctx.signal});
  function draw(){
    if(!current)return;
    const d=current.data;setText(phaseText,w.phase+": "+w[d.phase]+".");setText(countText," "+w.count+": "+d.count+".");
    counts.textContent=w.counts+": "+["pending","correct","incorrect","unavailable"].map(k=>d.counts[k]).join(" / ");
    const scoredClosed=Boolean(ctx.item.points)&&d.phase==="revealed";
    round.hidden=!scoredClosed;
    open.disabled=busy||d.phase==="open"||scoredClosed;close.disabled=busy||d.phase!=="open";reveal.disabled=busy||d.phase!=="closed";
    reset.disabled=busy;inspect.disabled=busy;prev.disabled=busy||d.page===0;next.disabled=busy||d.page+1>=d.pages;
    setText(page,w.page+" "+(d.page+1)+" / "+d.pages);
    share.disabled=busy||!d.selected||d.selected.actor!==select.value||!["closed","revealed"].includes(d.phase);
    clear.disabled=busy||!d.demonstration;include.disabled=share.disabled;
    const nextSelection=JSON.stringify([current.epoch,d.selected?.actor,d.selected?.version]);
    if(selection!==nextSelection){include.checked=false;selection=nextSelection;}
    const key=JSON.stringify(d.selected);
    if(key!==detailKey){
      detail.replaceChildren();detailKey=key;
      if(d.selected)detail.append(el("h3",w.selected),modelView(ctx.item,d.selected.model,ctx.language),
        el("p",d.selected.rationale),el("p",feedback(d.selected,w,ctx.item.points)));
    }
    const rows=el("div");
    for(const decision of ctx.item.decisions){
      const text=decisionText(ctx.item,decision,ctx.language),list=el("ul");
      for(const option of text.options){const count=d.options.find(r=>r.decision===decision.id)?.counts.find(r=>r.option===option.id)?.count||0;
        list.append(el("li",option.text+" — "+option.detail+": "+count));}
      rows.append(el("h3",text.title),list);
    }
    optionBody.replaceChildren(rows);teaching(d.teaching);
  }
  return {
    update(next){
      current=next;const key=JSON.stringify([next.epoch,next.data.participants]);
      if(key!==roster){
        const value=select.value;select.replaceChildren(el("option",w.none,{value:""}));
        for(const row of next.data.participants)select.append(el("option",w.response+" "+row.number+" · v"+row.version,{value:row.actor}));
        select.value=value;if(select.selectedIndex<0)select.value="";roster=key;
      }
      draw();
    },
    destroy(){root.remove();}
  };
}


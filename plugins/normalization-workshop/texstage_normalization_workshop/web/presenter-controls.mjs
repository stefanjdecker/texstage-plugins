// SPDX-License-Identifier: Apache-2.0
import {words,el,button,shell,errorText} from "./lesson-ui.mjs";
import {discussionWords} from "./discussion-words.mjs";
const valueOf=ref=>ref.handle+":"+ref.version;
export function mount(ctx){
  const w=words(ctx.language),t=discussionWords(ctx.language),root=shell(ctx),summary=el("p"),actions=el("div"),
    list=el("div"),paging=el("nav",undefined,{"aria-label":ctx.language==="de"?"Antwortseiten":"Answer pages"}),comparison=el("fieldset"),topics=el("div"),error=el("p","",{role:"alert"});
  // Keep the slide preview readable even when all 16 roster rows are present.
  Object.assign(root.style,{maxHeight:"40vh",overflow:"auto",width:"min(900px, calc(100vw - 32px))"});
  root.setAttribute("tabindex","0");
  root.setAttribute("aria-label",String(ctx.language).startsWith("de")?"Workshop-Steuerung":"Workshop controls");
  let current,busy=false,signature="",rows=[],selectionSignature="",epoch;
  async function dispatch(op,extra={}){
    if(!current||busy)return;busy=true;error.textContent="";draw();
    try{await ctx.dispatch(op,op==="_reset"?{}:{control:current.data.control_version,...extra});}
    catch(e){error.textContent=errorText(e,w);}finally{busy=false;draw();}
  }
  const buttons={};
  for(const [op,label]of [["open","openButton"],["close","closeButton"],["reveal","reveal"],["unshare","unshare"],["clear-selection","clear"],["_reset","reset"]]){
    buttons[op]=button(w[label],()=>dispatch(op),ctx.signal);actions.append(buttons[op]);
  }
  const first=el("select",undefined,{"aria-label":t.first}),second=el("select",undefined,{"aria-label":t.second});
  comparison.append(el("legend",t.comparison));
  for(const [name,select]of [[t.first,first],[t.second,second]]){
    const label=el("label",name);label.append(select);comparison.append(label);
    select.addEventListener("change",draw,{signal:ctx.signal});
  }
  const chosen=()=>[first,second].map(select=>{
    if(!select.value)return null;
    const [handle,version]=select.value.split(":");return {handle,version:Number(version)};
  });
  const compare=button(t.compare,()=>dispatch("compare-answers",{answers:chosen()}),ctx.signal),
    share=button(t.shareComparison,()=>dispatch("share-comparison",{answers:chosen()}),ctx.signal);
  comparison.append(compare,share);
  const topicButtons={};
  for(const topic of ["summary","lossless","preservation"]){
    const b=button(t[topic],()=>dispatch("show-evidence",{topic}),ctx.signal);
    topicButtons[topic]=b;topics.append(b);
  }
  const previousPage=button(ctx.language==="de"?"Vorherige Seite":"Previous page",()=>dispatch("page",{page:current.data.page-1}),ctx.signal),
    nextPage=button(ctx.language==="de"?"Nächste Seite":"Next page",()=>dispatch("page",{page:current.data.page+1}),ctx.signal),
    pageLabel=el("span",undefined,{"aria-live":"polite"});
  paging.append(previousPage,pageLabel,nextPage);
  root.append(summary,actions,comparison,topics,paging,list,error);
  function draw(){
    if(!current)return;const d=current.data;
    summary.textContent=w.phase+": "+w[d.phase]+". "+w.received+": "+d.counts.received+" · "+
      t.pending+": "+d.counts.pending+" · "+t.checked+": "+d.counts.checked+" · "+t.unavailable+": "+d.counts.unavailable+" · "+
      (ctx.item.points?w.pointsMaximum+": "+ctx.item.points+". "+w.pointsReveal:w.pointsPractice);
    for(const [op,b]of Object.entries(buttons)){
      const legal=op==="open"?["introduce","closed"].includes(d.phase):op==="close"?d.phase==="open":op==="reveal"?d.phase==="closed":
        op==="unshare"?d.shared.length>0:op==="clear-selection"?d.selected.length>0:true;
      b.disabled=busy||!d.active||!legal;
    }
    previousPage.disabled=busy||!d.active||d.page===0;
    nextPage.disabled=busy||!d.active||d.page+1>=d.pages;
    pageLabel.textContent=(ctx.language==="de"?"Seite ":"Page ")+(d.page+1)+" / "+d.pages;
    if(epoch!==current.epoch){first.replaceChildren();second.replaceChildren();signature="";selectionSignature="";}
    const sig=JSON.stringify([d.answers,d.pinned,current.epoch]);
    if(sig!==signature){
      const focus=document.activeElement?.dataset?.actionKey;
      signature=sig;rows=[];list.replaceChildren();
      for(const select of [first,second]){
        const previous=select.value,oldOption=select.selectedOptions[0]?.cloneNode(true);
        select.replaceChildren(el("option",t.choose,{value:""}));
        const available=[...new Map([...d.answers,...d.pinned].map(a=>[a.handle,a])).values()];
        available.forEach(a=>{if(a.status==="checked")select.append(el("option","#"+a.number+" · v"+a.version,{value:valueOf(a)}));});
        // Retain only this selector's chosen off-page reference, never the full roster.
        // The reducer revalidates its version and checked status before comparison.
        if(previous&&oldOption&&!available.some(a=>a.handle===previous.split(":")[0]))select.append(oldOption);
        select.value=Array.from(select.options).some(o=>o.value===previous)?previous:"";
      }
      d.answers.forEach((a,i)=>{
        const row=el("div"),ref={handle:a.handle,version:a.version},
          inspect=button(w.inspect+" "+a.number,()=>dispatch("select-answer",ref),ctx.signal),
          answer=button(w.share+" "+a.number,()=>dispatch("share-answer",ref),ctx.signal),
          analysis=button(t.shareAnalysis+" "+a.number,()=>dispatch("share-analysis",ref),ctx.signal);
        for(const [name,b]of [["inspect",inspect],["answer",answer],["analysis",analysis]])b.dataset.actionKey=name+"-"+a.handle;
        row.append(el("span","#"+a.number+" · v"+a.version+" · "+t[a.status]),inspect,answer,analysis);
        rows.push({inspect,answer,analysis,status:a.status});list.append(row);
      });
      if(focus)Array.from(list.querySelectorAll("button")).find(b=>b.dataset.actionKey===focus)?.focus();
    }
    const selected=JSON.stringify(d.selected);
    if(epoch!==current.epoch||selectionSignature!==selected){
      epoch=current.epoch;selectionSignature=selected;
      first.value=d.selected[0]?valueOf(d.selected[0]):"";
      second.value=d.selected[1]?valueOf(d.selected[1]):"";
    }
    const refs=chosen(),valid=refs.every(Boolean)&&refs[0].handle!==refs[1].handle;
    compare.disabled=busy||!d.active||!valid;
    share.disabled=busy||!d.active||!valid||JSON.stringify(refs)!==selected||!["closed","revealed"].includes(d.phase);
    rows.forEach(({inspect,answer,analysis,status})=>{
      inspect.disabled=busy||!d.active;
      answer.disabled=busy||!d.active||!["closed","revealed"].includes(d.phase);
      analysis.disabled=answer.disabled||status!=="checked";
    });
    for(const [topic,b]of Object.entries(topicButtons)){
      b.disabled=busy||!d.active||!(d.selected.length||(d.shared.length&&d.share_checks))||
        (topic!=="summary"&&ctx.item.task.mode!=="decompose");
      b.setAttribute("aria-pressed",String(d.topic===topic));
    }
  }
  return{update(next){current=next;draw();},destroy(){root.remove();}};
}

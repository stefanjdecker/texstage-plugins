// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
import {picker} from "./attribute-picker.mjs";
import {analysisPanel} from "./analysis-view.mjs";
import {discussionWords} from "./discussion-words.mjs";
import {words,local,el,button,shell,material,feedback,errorText,workedPanel} from "./lesson-ui.mjs";
export function mount(ctx){
  const w=words(ctx.language),root=shell(ctx);material(ctx,root,w);
  const phase=el("p"),editor=el("div",undefined,{class:"nw-editor"}),notice=el("p",local(ctx.item.sharing_notice,ctx.language));
  const message=el("p","",{role:"status","aria-live":"polite",class:"nw-answer"}),error=el("p","",{role:"alert"});
  const conflict=el("div",undefined,{class:"nw-conflict",hidden:""});conflict.append(el("p",w.conflict));
  const initial=()=>ctx.item.task.mode==="classify"?{mode:"classify",normal_form:"bcnf",witness:null}:{mode:"decompose",relations:[0]};
  let draft=initial(),current,epoch,version=0,dirty=false,busy=false,pending=null,hasConflict=false;
  const canonicalAnswer=()=>{
    if(draft.mode==="decompose"){
      if(!draft.relations.length || draft.relations.some(x=>!x) || new Set(draft.relations).size!==draft.relations.length)throw Error("relations");
      return {mode:"decompose",relations:[...draft.relations].sort((a,b)=>a-b)};
    }
    return structuredClone(draft);
  };
  function changed(){dirty=true;error.textContent="";draw();}
  function focusEditor(index=0){
    const row=editor.querySelectorAll("fieldset").item(index);
    (row?.querySelector("input")||editor.querySelector("select,input,button:not(:disabled)"))?.focus();
  }
  function renderEditor(){
    editor.replaceChildren();
    if(draft.mode==="classify"){
      const label=el("label",w.form),select=el("select",undefined,{"aria-label":w.form});
      for(const f of ["1nf","2nf","3nf","bcnf"]){const o=el("option",f.toUpperCase(),{value:f});select.append(o);}
      select.value=draft.normal_form;label.append(select);editor.append(label);
      const witness=el("div");editor.append(witness);
      function renderWitness(){
        witness.replaceChildren();
        if(draft.normal_form==="bcnf"){witness.append(el("p",w.bcnf));return;}
        witness.append(el("p",w.witness),el("p",w.help),picker(ctx,w.lhs,draft.witness[0],x=>{draft.witness[0]=x;changed();}));
        const rhs=el("select",undefined,{"aria-label":w.rhs}),rlabel=el("label",w.rhs);
        ctx.item.attributes.forEach((a,i)=>rhs.append(el("option",a.id,{value:String(1<<i)})));
        rhs.value=String(draft.witness[1]);rhs.addEventListener("change",()=>{draft.witness[1]=Number(rhs.value);changed();},{signal:ctx.signal});
        rlabel.append(rhs);witness.append(rlabel);
      }
      select.addEventListener("change",()=>{draft.normal_form=select.value;draft.witness=select.value==="bcnf"?null:(draft.witness||[0,1]);renderWitness();changed();},{signal:ctx.signal});
      renderWitness();
    }else{
      draft.relations.forEach((mask,i)=>{
        const card=picker(ctx,w.relation+" "+(i+1),mask,value=>{draft.relations[i]=value;changed();});
        card.dataset.relation=String(i+1);
        const remove=button(w.remove+" "+(i+1),()=>{draft.relations.splice(i,1);renderEditor();changed();focusEditor(Math.min(i,draft.relations.length-1));},ctx.signal);
        remove.disabled=draft.relations.length===1;card.append(remove);editor.append(card);
      });
      const add=button(w.add,()=>{draft.relations.push(0);renderEditor();changed();editor.querySelectorAll("fieldset").item(draft.relations.length-1)?.querySelector("input")?.focus();},ctx.signal);
      add.disabled=draft.relations.length>=8;editor.append(add);
    }
  }
  function adopt(keep=false){
    epoch=current.epoch;version=current.data.answer_version;
    if(!keep){draft=structuredClone(current.data.answer||initial());dirty=false;renderEditor();}else dirty=true;
    pending=null;hasConflict=false;error.textContent="";draw();
  }
  conflict.append(button(w.reload,()=>{adopt();focusEditor();},ctx.signal),button(w.keep,()=>{adopt(true);focusEditor();},ctx.signal));
  const save=button(w.save,async()=>{
    if(!current||save.disabled)return;
    let answer;try{answer=canonicalAnswer();}catch{error.textContent=w.bad;return;}
    pending=canonical(answer);busy=true;error.textContent="";draw();
    try{await ctx.dispatch("submit",{phase:current.data.phase_version,version,answer});}
    catch(e){pending=null;error.textContent=errorText(e,w);if(["stale-answer","stale-epoch"].includes(e?.code))hasConflict=true;}
    finally{busy=false;draw();}
  },ctx.signal);
  root.append(phase,notice,editor,conflict,save,message,error);
  const evidence=el("section",undefined,{class:"nw-saved-evidence"}),t=discussionWords(ctx.language);
  root.append(evidence);
  let evidenceKey="";
  const worked=workedPanel(root,ctx.item,w);
  function draw(){
    if(!current)return;const d=current.data;
    phase.textContent=w.phase+": "+w[d.phase];conflict.hidden=!hasConflict;
    save.disabled=busy||pending!==null||hasConflict||!d.active||d.phase!=="open";
    message.textContent=dirty?w.draft:d.feedback?feedback(d.feedback,ctx.item,w):w[d.status||"empty"];
    worked(d.worked);
    evidence.hidden=!d.analysis;
    const key=JSON.stringify([current.epoch,d.answer_version,d.analysis]);
    if(key!==evidenceKey){
      evidenceKey=key;evidence.replaceChildren();
      if(d.analysis)evidence.append(el("h3",t.savedEvidence+" · v"+d.answer_version),el("p",t.oneKind),
        analysisPanel(ctx,d.answer,d.analysis,w,{phone:true}));
    }
  }
  return {update(next){
    current=next;const d=next.data;
    if(epoch===undefined)adopt();
    else if(next.epoch!==epoch){pending=null;if(dirty)hasConflict=true;else adopt();}
    else if(d.answer_version!==version){
      if(pending && d.answer && canonical(d.answer)===pending){
        version=d.answer_version;try{dirty=canonical(canonicalAnswer())!==pending;}catch{dirty=true;}pending=null;
      }else if(dirty||busy||hasConflict)hasConflict=true;else adopt();
    }
    draw();
  },destroy(){root.remove();}};
}

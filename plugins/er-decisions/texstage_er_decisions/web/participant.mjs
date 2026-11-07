// SPDX-License-Identifier: Apache-2.0
import {el,button,shell,words,publicMaterial,feedback,errorText,uniqueId,setText} from "./lesson-ui.mjs";
import {decisionEditor} from "./decision-editor.mjs";
import {modelView,previewModel} from "./diagram.mjs";
import {teachingPanel} from "./teaching.mjs";
const signature=(choices,rationale)=>JSON.stringify([choices,rationale.normalize("NFC")]);
const asciiSize=text=>JSON.stringify(text.normalize("NFC")).replace(/[\u007f-\uffff]/g,c=>"\\u"+c.charCodeAt(0).toString(16).padStart(4,"0")).length;
export function mount(ctx) {
  const w=words(ctx.language),root=shell(ctx);publicMaterial(ctx,root,w);
  const phase=el("p"),phaseText=el("span","",{role:"status","aria-live":"polite","aria-atomic":"true",class:"er-phase"});phase.append(phaseText);
  const status=el("p","",{role:"status","aria-live":"polite","aria-atomic":"true",class:"er-answer-status"});
  const points=el("p","",{role:"status","aria-live":"polite","aria-atomic":"true",class:"er-points",hidden:""});
  const error=el("p","",{id:uniqueId(),role:"alert","aria-atomic":"true"});
  const conflict=el("div",undefined,{class:"er-conflict",hidden:""}),conflictMessage=el("p","",{role:"alert","aria-atomic":"true"});conflict.append(conflictMessage);
  let current,epoch,version=0,dirty=false,busy=false,pending=null,hasConflict=false,preview=false,previewKey="",generation=0;
  const edit=el("div"),heading=el("h3",w.decisions);edit.append(heading,el("p",w.help));
  const clearValidation=()=>{setText(error,"");editor.clearValidation();rationale.removeAttribute("aria-invalid");rationale.removeAttribute("aria-describedby");};
  const changed=()=>{dirty=true;clearValidation();draw();};
  const editor=decisionEditor(ctx,edit,changed);
  const rationale=el("textarea",undefined,{"aria-label":w.rationale,rows:"3"});
  const label=el("label",w.rationale);label.append(rationale);edit.append(label,el("p",w.sharing,{class:"er-muted"}));
  rationale.addEventListener("input",changed,{signal:ctx.signal});
  const model=el("div",undefined,{hidden:""}),modelHeading=el("h3",w.preview,{tabindex:"-1"}),modelBody=el("div");
  const toggle=button(w.model,()=>{preview=true;draw();modelHeading.focus();},ctx.signal);
  const back=button(w.back,()=>{preview=false;draw();toggle.focus();},ctx.signal);
  model.append(modelHeading,modelBody,back);
  const adopt=(keep=false)=>{
    generation++;epoch=current.epoch;version=current.data.own?.version||0;
    if (!keep){editor.set(current.data.own?.answer.choices||[]);rationale.value=current.data.own?.rationale||"";dirty=false;}
    else dirty=true;
    hasConflict=false;pending=null;busy=false;clearValidation();draw();
  };
  const restoreFocus=()=>{if(preview)modelHeading.focus();else editor.focus();};
  conflict.append(button(w.reload,()=>{adopt();restoreFocus();},ctx.signal),button(w.keep,()=>{adopt(true);restoreFocus();},ctx.signal));
  const save=button(w.save,async()=>{
    if (!current||save.disabled)return;
    const choices=editor.get(), reason=rationale.value.normalize("NFC");
    clearValidation();
    const missing=editor.validate(error.id);
    if(missing){setText(error,w.incomplete);preview=false;draw();missing.focus();return;}
    if([...reason].length>160||asciiSize(reason)>1280||/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\ud800-\udfff]/u.test(reason)){
      setText(error,w.badRationale);rationale.setAttribute("aria-invalid","true");rationale.setAttribute("aria-describedby",error.id);
      preview=false;draw();rationale.focus();return;
    }
    pending=signature(choices,reason);busy=true;const ticket=generation;draw();
    try {await ctx.dispatch("submit",{phase_version:current.data.phase_version,answer_version:version,choices,rationale:reason});}
    catch(e){if(ticket===generation){pending=null;setText(error,errorText(e,w));
      if(["stale-answer","stale-epoch"].includes(e?.code))hasConflict=true;}}
    finally {if(ticket===generation){busy=false;draw();}}
  },ctx.signal);save.dataset.primary="";
  root.append(phase,status,points,conflict,edit,toggle,model,save,error);
  const teaching=teachingPanel(ctx,root);
  function draw(){
    if(!current)return;
    const d=current.data;
    setText(phaseText,w.phase+": "+w[d.phase]+".");
    setText(status,dirty?w.draft:feedback(d.own,w,ctx.item.points));
    points.hidden=!Number.isInteger(d.own?.points);
    setText(points,points.hidden?"":w.pointsLabel+": "+d.own.points+" / "+ctx.item.points);
    conflict.hidden=!hasConflict;edit.hidden=preview;toggle.hidden=preview;model.hidden=!preview;
    setText(conflictMessage,hasConflict?w.conflict:"");
    if(preview){
      const choices=editor.get(),key=JSON.stringify(choices);
      if(previewKey!==key){modelBody.replaceChildren(modelView(ctx.item,previewModel(ctx.item,choices),ctx.language));previewKey=key;}
    }
    save.disabled=busy||pending!==null||hasConflict||!d.active||d.phase!=="open";
    teaching(d.teaching);
  }
  return {
    update(next){
      current=next;const own=next.data.own,incoming=own?.version||0;
      if(epoch===undefined){epoch=next.epoch;version=incoming;editor.set(own?.answer.choices||[]);rationale.value=own?.rationale||"";}
      else if(next.epoch!==epoch){pending=null;generation++;busy=false;if(dirty)hasConflict=true;else adopt();}
      else if(incoming!==version){
        if(pending&&own&&signature(own.answer.choices,own.rationale)===pending){
          version=incoming;dirty=signature(editor.get(),rationale.value)!==pending;pending=null;
        }else if(dirty||busy||hasConflict)hasConflict=true;else adopt();
      }
      draw();
    },
    destroy(){generation++;root.remove();}
  };
}


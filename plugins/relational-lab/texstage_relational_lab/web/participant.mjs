// SPDX-License-Identifier: Apache-2.0
import {canonical} from './identity.mjs';
import {starter} from './editor-model.mjs';
import {createEditor} from './tree-editor.mjs';
import {local,words,el,button,shell,publicMaterial,feedback,errorText,workedPanel} from './lesson-ui.mjs';

export function mount(ctx){
  const w=words(ctx.language),root=shell(ctx);publicMaterial(ctx,root,w);
  const phase=el('p'),notice=el('p',local(ctx.item.sharing_notice,ctx.language)),editorRoot=el('div');
  const status=el('p','',{role:'status','aria-live':'polite'}),error=el('p','',{role:'alert'}),conflict=el('div',undefined,{class:'rl-conflict',hidden:''});
  conflict.append(el('p',w.conflict));
  let current,epoch,version=0,dirty=false,busy=false,pending=null,hasConflict=false,sequence=0,dead=false;
  const editor=createEditor(ctx,editorRoot,()=>{dirty=true;error.textContent='';draw();});
  function adopt(keep=false){
    sequence++;busy=false;pending=null;epoch=current.epoch;version=current.data.own?.version||0;
    if(!keep){editor.setValue(current.data.own?.answer||starter(ctx.item));dirty=false;}else dirty=true;
    hasConflict=false;error.textContent='';draw();
  }
  conflict.append(button(w.reload,()=>adopt(),ctx.signal),button(w.keep,()=>adopt(true),ctx.signal));
  const save=button(w.save,async()=>{
    if(!current||save.disabled)return;
    const answer=editor.value(),token=++sequence,sendEpoch=current.epoch;
    pending={key:canonical(answer),epoch:sendEpoch};busy=true;error.textContent='';draw();
    try{await ctx.dispatch(ctx.item.mode==='construct'?'submit-tree':'submit-rewrite',{phase:current.data.phase_version,version,answer});}
    catch(e){if(dead||token!==sequence||current.epoch!==sendEpoch)return;pending=null;error.textContent=errorText(e,w);if(['stale-answer','stale-epoch'].includes(e?.code))hasConflict=true;}
    finally{if(!dead&&token===sequence){busy=false;draw();}}
  },ctx.signal);
  root.append(phase,notice,el('p',ctx.item.mode==='rewrite'?w.rewriteHelp:w.help),editorRoot,conflict,save,status,error);
  const worked=workedPanel(root,w,ctx);
  function draw(){
    if(!current||dead)return;
    const d=current.data;phase.textContent=`${w.phase}: ${w[d.phase]}. ${w.count}: ${d.count}.`;
    conflict.hidden=!hasConflict;
    save.disabled=busy||pending!==null||hasConflict||!d.active||d.phase!=='open'||!editor.valid();
    status.textContent=pending?w.waiting:dirty?w.draft:feedback(d.own,w);worked(d.worked,ctx.language);
  }
  return {
    update(next){
      current=next;const own=next.data.own,incoming=own?.version||0;
      if(epoch===undefined)adopt();
      else if(next.epoch!==epoch){sequence++;busy=false;pending=null;if(dirty||editor.pending())hasConflict=true;else adopt();}
      else if(incoming!==version){
        if(pending&&pending.epoch===next.epoch&&own&&canonical(own.answer)===pending.key){
          version=incoming;dirty=editor.pending()||canonical(editor.value())!==pending.key;pending=null;
        }else if(dirty||busy||hasConflict)hasConflict=true;else adopt();
      }
      draw();
    },
    destroy(){dead=true;sequence++;pending=null;editor.destroy();worked.destroy();root.remove();}
  };
}

// SPDX-License-Identifier: Apache-2.0
import {copy,key,blank,fromAnswer,toAnswer,isRead,preview} from "./editor-model.mjs";
import {words,local,el,button,field,option,details,shell,feedback,rubricView,scoreView,commandError,delivered,setText,taskText} from "./ui.mjs";
import {treeView} from "./tree-view.mjs";
import {answerView} from "./answer-view.mjs";
export function mount(ctx) {
  const w=words(ctx.language),seed=ctx.item.exercise,root=shell(ctx,"bp-participant");
  const phase=el("p",undefined,{role:"status","data-bp":"phase"}),problem=el("div",undefined,{class:"bp-card"});
  problem.append(el("h3",local(ctx.item.title,ctx.language)),el("p",local(ctx.item.prompt,ctx.language)),
    el("p",taskText(seed,w),{class:"bp-badge"}),el("p",w.capacity+": "+seed.leaf_capacity+" "+w.leafCap+" / "+seed.internal_capacity+" "+w.internalCap,{class:"bp-note"}));
  const conflict=el("div",undefined,{class:"bp-conflict",role:"status","data-bp":"conflict"}),conflictText=el("p");
  const error=el("p",undefined,{role:"alert","data-bp":"error"}),draftStatus=el("p",undefined,{role:"status","data-bp":"draft-status"});
  const ownStatus=el("p",undefined,{role:"status","data-bp":"feedback"}),formStatus=el("p",undefined,{class:"bp-note"});
  const scoreBox=el("div");let scoreKey="";
  problem.append(rubricView(ctx.item,w));
  const pathText=el("p",undefined,{class:"bp-sequence","data-bp":"path"}),leavesText=el("p",undefined,{class:"bp-sequence","data-bp":"leaves"});
  const editor=el("div"),fields=el("div"),actions=el("div",undefined,{class:"bp-actions"});
  const previewBox=details(w.previewTitle),previewStatus=el("p",w.previewHint,{role:"status","data-bp":"preview-status"});
  const previewFrames=el("select",undefined,{"data-bp":"preview-frame"}),previewTree=treeView(ctx.language,ctx.signal,{interactive:true,focusTag:"preview-focus"});
  const sharedBox=details(w.shared),workedBox=details(w.worked);
  sharedBox.hidden=workedBox.hidden=true;
  let draft=blank(seed),past=[],future=[],current=null,epoch=null,version=0,dirty=false,busy=false,conflicted=false,conflictKind="conflict";
  let receipt=null,pending=null,alive=true,generation=0,previewGeneration=0,analysis=null,sharedKey="",workedKey="";
  const initialTree=treeView(ctx.language,ctx.signal,{interactive:true,onFocus:()=>paint()});
  initialTree.update(seed.tree);
  const addPath=button(w.addPath,()=>change(d=>d.path.push(initialTree.focused),false),ctx.signal,{"data-bp":"add-path"});
  const removePath=button(w.removePath,()=>change(d=>d.path.pop(),false),ctx.signal,{"data-bp":"remove-path"});
  const pathButtons=el("div",undefined,{class:"bp-actions"});pathButtons.append(addPath,removePath);
  const addLeaf=button(w.addLeaf,()=>change(d=>d.leaves.push(initialTree.focused),false),ctx.signal,{"data-bp":"add-leaf"});
  const removeLeaf=button(w.removeLeaf,()=>change(d=>d.leaves.pop(),false),ctx.signal,{"data-bp":"remove-leaf"});
  const leafButtons=el("div",undefined,{class:"bp-actions"});leafButtons.append(addLeaf,removeLeaf);
  const undo=button(w.undo,()=>travel(past,future),ctx.signal,{"data-bp":"undo"});
  const redo=button(w.redo,()=>travel(future,past),ctx.signal,{"data-bp":"redo"});
  const clear=button(w.clearDraft,()=>change(d=>Object.assign(d,blank(seed))),ctx.signal,{"data-bp":"fresh-draft"});
  const simulate=button(w.preview,runPreview,ctx.signal,{"data-bp":"preview"});
  const save=button(w.save,submit,ctx.signal,{class:"bp-primary","data-bp":"submit"});
  const reload=button(w.reload,()=>{
    conflicted=false;past=[];future=[];draft=fromAnswer(seed,current?.data.own?.answer);dirty=false;
    renderFields();invalidatePreview();paint();
  },ctx.signal,{"data-bp":"reload"});
  const keep=button(w.keep,()=>{conflicted=false;dirty=true;paint();},ctx.signal,{"data-bp":"keep"});
  conflict.append(conflictText,reload,keep);conflict.hidden=true;
  editor.append(el("h3",w.descent),el("p",w.focusHint,{class:"bp-note"}),initialTree.root,el("strong",w.path),pathText,pathButtons);
  if(seed.task.kind==="range")editor.append(el("h3",w.scan),el("strong",w.leaves),leavesText,leafButtons);
  editor.append(fields);actions.append(undo,redo,clear,simulate,save);
  previewFrames.addEventListener("change",paintPreview,{signal:ctx.signal});
  previewBox.append(previewStatus,field(w.step,previewFrames),previewTree.root);previewFrames.parentElement.hidden=true;previewTree.root.hidden=true;
  root.append(el("h2",w.title),phase,problem,el("p",w.notice,{class:"bp-note"}),conflict,editor,formStatus,actions,error,draftStatus,
    el("h3",w.feedback),ownStatus,scoreBox,previewBox,sharedBox,workedBox);
  function snapshotFocus() {
    const node=document.activeElement;
    if(!fields.contains(node))return null;
    return {field:node.dataset.bpField,action:node.dataset.bp,start:node.selectionStart,end:node.selectionEnd};
  }
  function restoreFocus(saved) {
    if(!saved)return;
    let n=saved.field?[...fields.querySelectorAll("[data-bp-field]")].find(n=>n.dataset.bpField===saved.field):null;
    if(!n&&saved.action){
      n=[...fields.querySelectorAll("[data-bp]")].find(n=>n.dataset.bp===saved.action);
      if(!n)n=fields.querySelector('[data-bp="'+(saved.action.includes("separator")?"add-separator":"add-repair")+'"]');
    }
    if(n){n.focus();if(n.setSelectionRange&&saved.start!==null)try{n.setSelectionRange(saved.start,saved.end);}catch{}}
  }
  function input(label,value,id,onInput,hint) {
    const node=el("input",undefined,{type:"text",autocomplete:"off","data-bp-field":id});
    node.value=value;node.addEventListener("input",()=>change(d=>onInput(d,node.value),false),{signal:ctx.signal});
    return field(label,node,hint);
  }
  function select(label,value,id,items,onChange) {
    const node=el("select",undefined,{"data-bp-field":id});node.append(...items.map(([value,text])=>option(value,text)));node.value=value;
    node.addEventListener("change",()=>change(d=>onChange(d,node.value)),{signal:ctx.signal});
    return field(label,node);
  }
  function renderFields() {
    const focus=snapshotFocus();fields.replaceChildren();
    if(isRead(seed)){
      fields.append(input(w.returned,draft.keys,"keys",(d,v)=>d.keys=v,w.listHint));restoreFocus(focus);return;
    }
    fields.append(el("h3",w.repairs),el("p",w.repairHint,{class:"bp-note"}));
    draft.repairs.forEach((r,i)=>{
      const group=el("fieldset",undefined,{"data-bp-repair":i});group.append(el("legend",w.repair+" "+(i+1)));
      group.append(select(w.operation,r.op,"repair-"+i+"-op",["split","borrow","merge"].map(op=>[op,w[op]]),(d,v)=>{
        const old=d.repairs[i];d.repairs[i]=v==="split"?{op:v,node:old.node,left_count:old.left_count||"",separator:old.separator||""}:
          {op:v,node:old.node,sibling:old.sibling||""};
      }),input(w.node,r.node,"repair-"+i+"-node",(d,v)=>d.repairs[i].node=v));
      if(r.op==="split")group.append(
        input(w.leftCount,r.left_count,"repair-"+i+"-left_count",(d,v)=>d.repairs[i].left_count=v),
        input(w.separator,r.separator,"repair-"+i+"-separator",(d,v)=>d.repairs[i].separator=v));
      else group.append(input(w.sibling,r.sibling,"repair-"+i+"-sibling",(d,v)=>d.repairs[i].sibling=v));
      group.append(button(w.removeRepair,()=>change(d=>d.repairs.splice(i,1)),ctx.signal,{"data-bp":"remove-repair","aria-label":w.removeRepair+" "+(i+1)}));fields.append(group);
    });
    const add=button(w.addRepair,()=>change(d=>d.repairs.push(seed.task.kind==="insert"?
      {op:"split",node:String(initialTree.focused),left_count:"",separator:""}:
      {op:"borrow",node:String(initialTree.focused),sibling:""})),ctx.signal,{"data-bp":"add-repair"});
    add.disabled=draft.repairs.length>=3;fields.append(add,el("h3",w.predictions),el("p",w.separators));
    draft.separators.forEach((r,i)=>{
      const group=el("fieldset");group.append(el("legend",w.internal+" "+(i+1)),
        input(w.page,r.node,"separator-"+i+"-node",(d,v)=>d.separators[i].node=v),
        input(w.keys,r.keys,"separator-"+i+"-keys",(d,v)=>d.separators[i].keys=v,w.listHint),
        button(w.removeSeparator,()=>change(d=>d.separators.splice(i,1)),ctx.signal,{"data-bp":"remove-separator","aria-label":w.removeSeparator+" "+(i+1)}));
      fields.append(group);
    });
    const addSep=button(w.addSeparator,()=>change(d=>d.separators.push({node:"",keys:""})),ctx.signal,{"data-bp":"add-separator"});
    addSep.disabled=draft.separators.length>=10;
    fields.append(addSep,select(w.height,draft.height,"height",[["",w.choose],...Array.from({length:4},(_,i)=>[String(i),String(i)])],(d,v)=>d.height=v));
    restoreFocus(focus);
  }
  function invalidatePreview(){previewGeneration++;analysis=null;setText(previewStatus,w.previewStale);previewFrames.parentElement.hidden=true;previewTree.root.hidden=true;}
  function change(fn,rebuild=true) {
    const next=copy(draft);fn(next);if(key(next)===key(draft))return;
    past.push(copy(draft));if(past.length>50)past.shift();future=[];draft=next;changed(rebuild);
  }
  function changed(rebuild=true) {
    dirty=key(draft)!==key(fromAnswer(seed,current?.data.own?.answer));error.textContent="";
    if(rebuild)renderFields();invalidatePreview();paint();
  }
  function travel(from,to) {
    if(!from.length)return;to.push(copy(draft));if(to.length>50)to.shift();draft=from.pop();changed();
  }
  function validAnswer(){try{return toAnswer(seed,draft);}catch{return null;}}
  function canSave(){return !!(current?.data.active&&current.data.phase==="open"&&!busy&&!conflicted&&validAnswer());}
  function paint() {
    if(!alive)return;
    const d=current?.data,focus=seed.tree.nodes.find(n=>n.id===initialTree.focused);
    conflict.hidden=!conflicted;setText(conflictText,w[conflictKind]);
    undo.disabled=!past.length;redo.disabled=!future.length;save.disabled=!canSave();simulate.disabled=!validAnswer();
    addPath.disabled=draft.path.length>=3;removePath.disabled=!draft.path.length;
    addLeaf.disabled=focus?.kind!=="leaf"||draft.leaves?.length>=20;removeLeaf.disabled=!draft.leaves?.length;
    setText(pathText,draft.path.map(n=>"P"+n).join(" → ")||w.empty);
    setText(leavesText,(draft.leaves||[]).map(n=>"P"+n).join(" → ")||w.empty);
    setText(draftStatus,busy?(receipt?w.waiting:w.saving):dirty?w.dirty:(d?.own?w.clean:""));
    setText(ownStatus,feedback(d?.own,w)+(d?.own?" · "+w.version+" "+d.own.version:""));
    const nextScore=JSON.stringify([d?.own?.feedback,d?.scoring]);
    if(nextScore!==scoreKey){scoreKey=nextScore;scoreBox.replaceChildren(scoreView(d?.own,d?.scoring,ctx.item,w));}
    setText(formStatus,!validAnswer()?w.invalid:d?.phase!=="open"?w.roundClosed:"");
    if(d)setText(phase,w.phase+": "+w[d.phase]);
  }
  function paintPreview(){
    if(!analysis)return;
    const frame=analysis.frames[Number(previewFrames.value)]||analysis.frames.at(-1);
    previewTree.update(frame.tree,{pending:frame.pending});
  }
  async function runPreview() {
    const answer=validAnswer();if(!answer){setText(error,w.invalid);return;}
    const token=++previewGeneration;analysis=null;previewBox.open=true;setText(previewStatus,w.previewBusy);
    try{
      const result=await preview(seed,answer,{signal:ctx.signal,valid:()=>alive&&token===previewGeneration});
      if(!result||!alive||token!==previewGeneration)return;
      analysis=result;
      setText(previewStatus,result.facts.replay.state==="complete"?w.previewComplete:
        w.previewStopped+": "+(w.reason[result.facts.replay.reason]||w.invalid));
      previewFrames.replaceChildren(...result.frames.map((f,i)=>option(i,f.kind==="repair"?w.afterRepair+" "+(f.index+1):w[f.kind==="edit"?"edit":"initial"])));
      previewFrames.value=String(result.frames.length-1);previewFrames.parentElement.hidden=false;previewTree.root.hidden=false;paintPreview();
    }catch{if(alive&&token===previewGeneration)setText(previewStatus,w.invalid);}
  }
  async function submit() {
    if(!canSave())return;const answer=validAnswer(),token=generation;
    pending={epoch,version,answer:key(answer)};busy=true;receipt=null;error.textContent="";paint();
    try{
      const r=await ctx.dispatch("submit-answer",{phase_version:current.data.phase_version,answer_version:version,answer});
      if(!alive||token!==generation)return;receipt=r;
      if(delivered(current,r)){busy=false;pending=null;receipt=null;}
    }catch(e){
      if(!alive||token!==generation)return;busy=false;pending=null;receipt=null;setText(error,commandError(e,w));
      if(["stale-answer","stale-epoch"].includes(e?.code)){conflicted=true;conflictKind=e.code==="stale-epoch"?"resetConflict":"conflict";}
    }
    paint();
  }
  renderFields();paint();
  return {
    update(view) {
      if(!alive)return;
      const d=view.data,nextVersion=d.own?.version||0,first=epoch===null,reset=!first&&epoch!==view.epoch;
      const ack=pending&&pending.epoch===view.epoch&&nextVersion>pending.version&&key(d.own?.answer)===pending.answer;
      if(first){draft=fromAnswer(seed,d.own?.answer);dirty=false;renderFields();}
      else if(reset){
        generation++;previewGeneration++;receipt=null;pending=null;analysis=null;
        if(dirty||busy||conflicted){conflicted=true;conflictKind="resetConflict";}
        else{draft=fromAnswer(seed,d.own?.answer);past=[];future=[];renderFields();}
        busy=false;invalidatePreview();
      }else if(nextVersion!==version){
        if(ack)dirty=key(validAnswer())!==pending.answer;
        else if(dirty||busy||conflicted){conflicted=true;conflictKind="conflict";}
        else{draft=fromAnswer(seed,d.own?.answer);past=[];future=[];renderFields();invalidatePreview();}
      }
      current=view;epoch=view.epoch;version=nextVersion;
      if(receipt&&delivered(view,receipt)){busy=false;pending=null;receipt=null;}
      sharedBox.hidden=!d.demonstration;workedBox.hidden=!d.worked;
      const nextSharedKey=key([d.demonstration,d.replay?.source==="shared"?d.replay.focus:null]);
      if(nextSharedKey!==sharedKey){
        sharedKey=nextSharedKey;sharedBox.replaceChildren(el("summary",w.shared));
        if(d.demonstration)sharedBox.append(el("p",d.phase==="revealed"?feedback({status:"saved",feedback:d.demonstration.feedback},w):w.predictionsOnly),
          answerView(d.demonstration.answer,ctx.language,{focus:d.replay?.source==="shared"?d.replay.focus:null}));
      }
      if(key(d.worked)!==workedKey){
        workedKey=key(d.worked);workedBox.replaceChildren(el("summary",w.worked));
        if(d.worked){const viewer=treeView(ctx.language,ctx.signal,{interactive:true,focusTag:"worked-focus"});viewer.update(d.worked.result.final||seed.tree,{highlight:d.worked.result.read?.leaves||[]});
          workedBox.append(el("p",local(d.worked.explanation,ctx.language)),viewer.root,answerView(d.worked.answer,ctx.language));}
      }
      paint();
    },
    destroy(){alive=false;generation++;previewGeneration++;root.remove();}
  };
}

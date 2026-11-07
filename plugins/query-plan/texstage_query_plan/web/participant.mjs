// SPDX-License-Identifier: Apache-2.0
import {copy,key,topologies,topology,label,retopologize,supported,geometry} from "./plan-editor.mjs";
import {words,el,button,field,option,shell,problem,estimate,feedback,commandError,delivered,number,details,local} from "./lesson-ui.mjs";
import {planView} from "./cost-inspector.mjs";
export function mount(ctx) {
 const w=words(ctx.language),root=shell(ctx,"qp-participant"),exercise=ctx.item.exercise;
 const phase=el("p",undefined,{"aria-live":"polite"}),ownStatus=el("p",undefined,{"aria-live":"polite","data-qp":"saved-status"});
 const error=el("p",undefined,{role:"alert"}),draftStatus=el("p",w.empty,{"aria-live":"polite","data-qp":"draft-status"});
 const conflict=el("div",undefined,{class:"qp-conflict",role:"status"});conflict.hidden=true;
 const fields=el("div"),actions=el("div",undefined,{class:"qp-actions"}),preview=el("section",undefined,{"aria-label":w.preview});
 const previewStatus=el("p",w.previewHint,{"aria-live":"polite"}),comparison=el("p",undefined,{class:"qp-summary"});
 const viewer=planView(exercise,ctx.language,ctx.signal);
 const solution=details(w.worked),solutionView=planView(exercise,ctx.language,ctx.signal),explanation=el("p"),minimum=el("p");
 const optimal=details(w.optimal),optimalView=planView(exercise,ctx.language,ctx.signal);optimal.append(optimalView.root);
 solution.append(explanation,minimum,solutionView.root,optimal);solution.hidden=true;
 let draft=copy(ctx.item.baseline),history=[],current=null,epoch=null,version=0,dirty=false,busy=false,hasConflict=false;
 let pending=null,receipt=null,alive=true,generation=0,solutionKey="",layoutKey="";
 const selectors=[];
 const trees=topologies(exercise),order=el("select",undefined,{"data-qp":"order"});
 trees.forEach((t,i)=>order.append(option(String(i),label(t))));
 order.addEventListener("change",()=>edit(retopologize(draft,trees[Number(order.value)])),{signal:ctx.signal});
 const orderField=field(w.order,order);orderField.hidden=trees.length===1;
 const unsupported=el("p",w.unsupported,{class:"qp-error"});unsupported.hidden=true;
 fields.append(orderField,unsupported);
 const nodesBox=el("div");fields.append(nodesBox);
 const undo=button(w.undo,()=>{const value=history.pop();if(value){draft=value;changed();}},ctx.signal);
 const reset=button(w.resetDraft,()=>edit(copy(ctx.item.baseline)),ctx.signal);
 const estimateButton=button(w.estimate,()=>{
  const result=estimate(exercise,draft);previewStatus.textContent=result.valid?w.preview:(w[result.reason]||w.invalid);
  comparison.textContent=w.baseline+": "+number(ctx.item.baseline_analysis.cost,ctx.language)+(result.valid?" · "+w.draftCost+": "+number(result.cost,ctx.language)+" · "+w.difference+": "+number(result.cost-ctx.item.baseline_analysis.cost,ctx.language):"");
  viewer.update(draft,result);viewer.root.hidden=false;save.disabled=!canSave();
 },ctx.signal);
 const save=button(w.save,submit,ctx.signal);save.classList.add("qp-primary");
 const reload=button(w.reload,()=>{hasConflict=false;history=[];draft=copy(current?.data.own?.answer||ctx.item.baseline);dirty=false;refreshEditor();invalidate();paint();},ctx.signal);
 const keep=button(w.keep,()=>{hasConflict=false;dirty=true;paint();},ctx.signal);
 conflict.append(el("p",w.conflict),reload,keep);
 actions.append(undo,reset,estimateButton,save);
 preview.append(previewStatus,comparison,viewer.root);viewer.root.hidden=true;
 root.append(el("h2",w.title),phase,el("p",ctx.item.points?w.pointsTarget+": "+number(ctx.item.points,ctx.language)+" · "+w.speedWindow+": "+ctx.item.time+" s. "+w.scoringHint:w.practice,{"data-qp":"points-policy"}),problem(ctx.item,ctx.language),el("p",w.notice,{class:"qp-note"}),conflict,fields,actions,error,draftStatus,ownStatus,preview,solution);
 function canSave(){return current?.data.active&&current.data.phase==="open"&&!busy&&!hasConflict&&supported(exercise,draft);}
 function invalidate(){previewStatus.textContent=w.stalePreview;comparison.textContent="";viewer.root.hidden=true;}
 function changed(){
  dirty=key(draft)!==key(current?.data.own?.answer||ctx.item.baseline);error.textContent="";
  refreshEditor();invalidate();paint();
 }
 function edit(value){if(key(value)===key(draft))return;history.push(copy(draft));if(history.length>50)history.shift();draft=value;changed();}
 function refreshEditor(){
  const ok=supported(exercise,draft);unsupported.hidden=ok;nodesBox.hidden=!ok;order.disabled=!ok;
  if(!ok)return;
  const shape=key(topology(draft));order.value=String(trees.findIndex(t=>key(t)===shape));
  // Method changes update existing elements; unrelated pushes never rebuild them.
  if(layoutKey!==shape){
   layoutKey=shape;nodesBox.replaceChildren();selectors.length=0;
   draft.nodes.forEach((n,i)=>{
    const group=el("fieldset");group.append(el("legend",w.node+" "+(i+1)+": "+(n.op==="scan"?n.relation:w.join+" ("+(n.left+1)+" + "+(n.right+1)+")")));
    const method=el("select",undefined,{"data-qp-node":String(i),"aria-label":w.node+" "+(i+1)+" "+w.method});
    if(n.op==="scan")method.append(option("seq",w.seq),option("index",w.index));
    else method.append(option("nested",w.nested),option("hash",w.hash));
    method.addEventListener("change",()=>{
     const value=copy(draft);
     value.nodes[i].method=method.value==="hash"?(geometry(exercise,draft)[i].leftBytes<=exercise.limits.hash_bytes?"hash-left":"hash-right"):method.value;
     edit(value);
    },{signal:ctx.signal});
    group.append(field(w.method,method));
    let build,buildField;
    if(n.op==="join"){
     build=el("select",undefined,{"data-qp-build":String(i),"aria-label":w.node+" "+(i+1)+" "+w.build});
     build.append(option("hash-left",w.left),option("hash-right",w.right));
     build.addEventListener("change",()=>{const value=copy(draft);value.nodes[i].method=build.value;edit(value);},{signal:ctx.signal});
     buildField=field(w.build,build);group.append(buildField);
    }
    const hint=el("p",undefined,{class:"qp-note"});group.append(hint);nodesBox.append(group);
    selectors.push({method,build,buildField,hint});
   });
  }
  const facts=geometry(exercise,draft),limit=exercise.limits.hash_bytes;
  draft.nodes.forEach((n,i)=>{
   const c=selectors[i];
   c.method.value=n.method.startsWith("hash")?"hash":n.method;
   if(n.op==="scan"){
    const indexed=!!exercise.query.relations.find(r=>r.id===n.relation)?.index;
    c.method.options[1].disabled=!indexed;c.method.options[1].textContent=w.index+(!indexed?" — "+w.noIndex:"");
    c.hint.textContent=indexed?"":w.noIndex;
   }else{
    const f=facts[i];c.method.options[1].disabled=f.leftBytes>limit&&f.rightBytes>limit;
    c.buildField.hidden=n.method==="nested";c.build.value=n.method==="nested"?"hash-left":n.method;
    for(const [k,bytes]of[f.leftBytes,f.rightBytes].entries()){
     c.build.options[k].disabled=bytes>limit;c.build.options[k].textContent=w[k===0?"left":"right"]+" · "+number(bytes,ctx.language)+" "+w.bytes+(bytes>limit?" — "+w.tooLarge:"");
    }
    c.hint.textContent=w.workspace+": "+w.left+" "+number(f.leftBytes,ctx.language)+", "+w.right+" "+number(f.rightBytes,ctx.language)+" "+w.bytes+". "+w.hashLimit+": "+number(limit,ctx.language)+".";
   }
  });
 }
 function paint(){
  conflict.hidden=!hasConflict;undo.disabled=!history.length;save.disabled=!canSave();
  draftStatus.textContent=busy?(receipt?w.waiting:w.saving):dirty?w.dirty:"";
  const own=current?.data.own;
  ownStatus.textContent=feedback(own,w,ctx.language)+(own?.points!==undefined?" · "+w.pointsAwarded+": "+number(own.points,ctx.language)+(own.bonus!==undefined?" ("+w.speedPoints+": "+number(own.base_points,ctx.language)+" + "+w.streakBonus+": "+number(own.bonus,ctx.language)+")":""):"");
  if(current){const d=current.data;phase.textContent=w.phase+": "+w[d.phase]+" · "+w.count+": "+d.count;}
 }
 async function submit(){
  if(!canSave())return;
  const token=generation,snapshot=copy(draft);
  pending={epoch,version,answer:key(snapshot)};busy=true;receipt=null;error.textContent="";paint();
  try{
   const received=await ctx.dispatch("submit-plan",{phase:current.data.phase_version,version,answer:snapshot});
   if(!alive||token!==generation)return;
   receipt=received;
   if(delivered(current,receipt)){busy=false;pending=null;receipt=null;}
  }catch(e){
   if(!alive||token!==generation)return;
   busy=false;pending=null;receipt=null;error.textContent=commandError(e,w);
  }
  if(alive)paint();
 }
 refreshEditor();paint();
 return {
  update(view){
   if(!alive)return;
   const d=view.data,newVersion=d.own?.version||0,first=epoch===null;
   const resetEpoch=!first&&epoch!==view.epoch;
   const ack=pending&&pending.epoch===view.epoch&&newVersion>pending.version&&key(d.own?.answer)===pending.answer;
   const changedVersion=!first&&newVersion!==version;
   if(first){draft=copy(d.own?.answer||ctx.item.baseline);dirty=false;refreshEditor();}
   else if(resetEpoch){
    generation++;receipt=null;pending=null;
    if(dirty||busy||hasConflict)hasConflict=true;
    else{draft=copy(d.own?.answer||ctx.item.baseline);history=[];refreshEditor();invalidate();}
    busy=false;
   }else if(changedVersion){
    if(ack)dirty=key(draft)!==pending.answer;
    else if(dirty||busy||hasConflict)hasConflict=true;
    else{draft=copy(d.own?.answer||ctx.item.baseline);history=[];refreshEditor();invalidate();}
   }
   epoch=view.epoch;version=newVersion;current=view;
   if(receipt&&delivered(view,receipt)){busy=false;pending=null;receipt=null;}
   const nextSolution=key(d.solution);
   solution.hidden=!d.solution;
   if(d.solution&&nextSolution!==solutionKey){
    solutionKey=nextSolution;explanation.textContent=local(d.solution.explanation,ctx.language);
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

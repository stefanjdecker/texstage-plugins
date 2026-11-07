// SPDX-License-Identifier: Apache-2.0
import {words,el,button,field,option,shell,problem,operations,operation,legal,key,setText,answersView,workedView,commandError} from './layout.mjs';

export function mount(ctx){
 const w=words(ctx.language),exercise=ctx.item.exercise,ops=operations(exercise),root=shell(ctx,'tx-participant');
 const phase=el('p','',{class:'tx-phase','data-tx':'phase'}),notice=el('p','',{role:'status','aria-live':'polite'}),error=el('p','',{role:'alert',class:'tx-error','data-tx':'error'});
 const material=el('details');material.append(el('summary',w.programs),problem(exercise,w,ctx.language));
 root.append(phase,el('p',w.sharing,{class:'tx-note'}),material,notice,error);
 const parts={},state={};let current=null,epoch,alive=true,busy=false,pending=null,generation=0,feedbackKey='',workedKey='';
 const values={};const prediction=el('fieldset');prediction.append(el('legend',w.prediction),el('p',w.predictionHelp));
 for(const name of Object.keys(exercise.initial).sort()){const input=el('input',undefined,{type:'number',step:'1',min:'-1120000',max:'1120000','data-tx-value':name});values[name]=input;prediction.append(field(name,input));}
 const diagnosis=el('fieldset');diagnosis.append(el('legend',w.diagnosis),el('p',w.diagnosisHelp));
 const edges=[],vertices=exercise.transactions.map(t=>t.id).sort();
 for(const a of vertices)for(const b of vertices)if(a!==b){
  const card=el('div',undefined,{class:'tx-card'}),toggle=el('input',undefined,{type:'checkbox','data-tx-edge':a+'-'+b}),selects=[];
  card.append(field(a+' → '+b,toggle));
  for(const [i,label]of[w.earlier,w.later].entries()){const select=el('select',undefined,{'data-tx-witness':a+'-'+b+'-'+i});select.append(option('',w.choose));for(const op of Object.values(ops))select.append(option(op.id,op.id+' · '+op.transaction+' · '+operation(op)));selects.push(select);card.append(field(label,select));}
  const entry={a,b,toggle,selects};edges.push(entry);diagnosis.append(card);
  toggle.addEventListener('change',()=>{mark('diagnosis');paint();},{signal:ctx.signal});
 }
 const certKind=el('select',undefined,{'data-tx':'certificate-kind'});certKind.append(option('serial',w.serial),option('cycle',w.cycle));diagnosis.append(field(w.certificate,certKind));
 const certBox=el('div',undefined,{class:'tx-cert'}),cert=[];
 for(let i=0;i<4;i++){const select=el('select',undefined,{'data-tx-vertex':i});select.append(option('',w.choose));vertices.forEach(v=>select.append(option(v)));cert.push(select);certBox.append(field(w.vertex+' '+(i+1),select));}diagnosis.append(certBox);
 const repair=el('fieldset');repair.append(el('legend',w.repair),el('p',w.repairHelp));
 let order=[...exercise.schedule],history=[];
 const cards=el('div',undefined,{'data-tx':'operation-cards'}),undo=button(w.undo,()=>{if(history.length){order=history.pop();renderOrder();mark('repair');}},ctx.signal,{'data-tx':'undo'});
 repair.append(undo,cards);
 function move(id,index,focus){const next=order.filter(o=>o!==id);next.splice(index,0,id);if(!legal(exercise,next)){setText(error,w.programOrder);error.hidden=false;return;}
  history.push([...order]);if(history.length>30)history.shift();order=next;mark('repair');renderOrder();cards.querySelector('[data-tx-op="'+id+'"] [data-tx-move="'+focus+'"]')?.focus();}
 function renderOrder(){cards.replaceChildren();for(const [i,id]of order.entries()){const op=ops[id],card=el('div',undefined,{class:'tx-card','data-tx-op':id});card.append(el('strong',id+' · '+op.transaction),el('p',operation(op)));
  const actions=el('div',undefined,{class:'tx-actions'}),up=button(w.up,()=>move(id,i-1,'up'),ctx.signal,{'data-tx-move':'up'}),down=button(w.down,()=>move(id,i+1,'down'),ctx.signal,{'data-tx-move':'down'});
  up.dataset.boundary=String(i===0);down.dataset.boundary=String(i===order.length-1);actions.append(up,down);
  const before=el('select',undefined,{'data-tx-move':'before'});before.append(option('',w.choose));order.filter(x=>x!==id).forEach(x=>before.append(option(x)));
  before.addEventListener('change',()=>{if(before.value){const index=order.filter(x=>x!==id).indexOf(before.value);move(id,index,'before');}},{signal:ctx.signal});card.append(actions,field(w.before,before));cards.append(card);}paint();}
 const boxes={prediction,diagnosis,repair};
 for(const name of Object.keys(boxes)){state[name]={version:0,dirty:false,conflict:false};const box=boxes[name];
  const conflict=el('div',undefined,{class:'tx-conflict','data-tx-conflict':name});conflict.append(el('p',w.conflict),button(w.reload,()=>adopt(name,false),ctx.signal,{'data-tx-reload':name}),button(w.keep,()=>adopt(name,true),ctx.signal,{'data-tx-keep':name}));
  const save=button(w.submit,()=>submit(name),ctx.signal,{'data-tx-submit':name}),status=el('p','',{role:'status','aria-live':'polite','data-tx-status':name});
  const retry=name==='repair'?button(w.retry,()=>submit(name,true),ctx.signal,{'data-tx':'retry'}):null;
  root.append(box,conflict,save);if(retry)root.append(retry);root.append(status);parts[name]={box,conflict,save,status,retry};
  box.addEventListener('input',()=>mark(name),{signal:ctx.signal});box.addEventListener('change',()=>{mark(name);paint();},{signal:ctx.signal});
 }
 const feedback=el('section',undefined,{'data-tx':'saved-answers'}),worked=el('section',undefined,{'data-tx':'worked'});root.append(feedback,worked);renderOrder();
 function mark(name){state[name].dirty=true;error.textContent='';paint();}
 function load(name,answer){
  if(name==='prediction')for(const [id,input]of Object.entries(values))input.value=answer?.values[id]??'';
  if(name==='diagnosis'){for(const e of edges){const saved=answer?.edges.find(x=>x.from===e.a&&x.to===e.b);e.toggle.checked=!!saved;e.selects.forEach((s,i)=>s.value=saved?.witness[i]||'');}certKind.value=answer?.certificate.kind||'serial';cert.forEach((s,i)=>s.value=answer?.certificate.vertices[i]||'');}
  if(name==='repair'){order=answer?[...answer.order]:[...exercise.schedule];history=[];renderOrder();}
 }
 function read(name){if(name==='prediction'){const result={};for(const[id,input]of Object.entries(values)){if(!input.value.trim())throw Error('value');const value=Number(input.value);if(!Number.isSafeInteger(value)||Math.abs(value)>1120000)throw Error('value');result[id]=value;}return{values:result};}
  if(name==='diagnosis'){const selected=edges.filter(e=>e.toggle.checked);if(selected.some(e=>e.selects.some(s=>!s.value)))throw Error('witness');return{edges:selected.map(e=>({from:e.a,to:e.b,witness:e.selects.map(s=>s.value)})),certificate:{kind:certKind.value,vertices:cert.slice(0,certKind.value==='serial'?3:4).map(s=>s.value).filter(Boolean)}};}
  return{order:[...order]};}
 function adopt(name,keep){const own=current?.data.own?.[name];state[name].version=own?.version||0;state[name].conflict=false;state[name].dirty=keep;if(!keep)load(name,own?.answer);error.textContent='';paint();}
 function paint(){if(!current)return;const d=current.data,active={predict:'prediction',diagnose:'diagnosis',repair:'repair'}[d.phase];setText(phase,w.phase+': '+w[d.phase]);
  setText(notice,!d.active?w.inactive:d.paused?w.paused:d.phase==='reveal'?w.pendingReveal:'');error.hidden=!error.textContent;
  for(const[name,p]of Object.entries(parts)){const s=state[name],visible=name===active,lock=!visible||!d.active||d.paused||busy||!!pending||s.conflict;
   p.box.hidden=!visible;p.box.disabled=lock;p.save.hidden=!visible;p.save.disabled=lock;
   p.conflict.hidden=!visible||!s.conflict;p.status.hidden=!visible;
   const own=d.own?.[name];setText(p.status,busy||pending?w.waiting:s.dirty?w.draft:own?w[own.status]:w.none);
   if(p.retry){p.retry.hidden=own?.status!=='unavailable';p.retry.disabled=busy||!!pending||!d.active||s.conflict;}
  }
  edges.forEach(e=>e.selects.forEach(s=>{s.disabled=!e.toggle.checked;}));
  cert[3].parentElement.hidden=certKind.value==='serial';
  for(const b of cards.querySelectorAll('button[data-boundary]'))b.disabled=b.dataset.boundary==='true';undo.disabled=!history.length;
  const ownKey=key(d.own);if(ownKey!==feedbackKey){feedbackKey=ownKey;feedback.replaceChildren(el('h3',w.feedback),answersView(d.own,w));feedback.hidden=!d.own;}
  const solutionKey=key(d.worked);if(solutionKey!==workedKey){workedKey=solutionKey;worked.replaceChildren(workedView(d.worked,w,ctx.language));worked.hidden=!d.worked;}
 }
 async function submit(name,retry=false){if(!current||busy||pending||!alive)return;const token=generation;let answer;try{answer=retry?current.data.own.repair.answer:read(name);}catch{setText(error,w.structural);paint();return;}
  const version=state[name].version;pending={name,answer:key(answer),version:version+(retry?0:1),retry};busy=true;error.textContent='';paint();
  try{await ctx.dispatch(retry?'retry-analysis':'submit-'+name,{phase_token:current.data.phase_token,answer_version:version,...(retry?{}:{answer})});
   if(!alive||generation!==token)return;
   if(retry){pending=null;state[name].dirty=false;}
  }catch(e){if(!alive||generation!==token)return;pending=null;setText(error,commandError(e,w));if(e.code==='stale-answer')state[name].conflict=true;
  }finally{if(alive&&generation===token){busy=false;paint();}}
 }
 return{update(next){if(!alive)return;const changedEpoch=epoch!==undefined&&epoch!==next.epoch;current=next;
   if(epoch===undefined||changedEpoch){epoch=next.epoch;generation++;pending=null;busy=false;for(const name of Object.keys(parts))adopt(name,false);if(changedEpoch)setText(error,w.resetNotice);}
   else for(const name of Object.keys(parts)){const own=next.data.own?.[name],version=own?.version||0,s=state[name];
    if(pending?.name===name&&own&&version===pending.version&&key(own.answer)===pending.answer){s.version=version;s.dirty=false;s.conflict=false;pending=null;}
    else if(version!==s.version){if(s.dirty||s.conflict||busy)s.conflict=true;else adopt(name,false);}
   }paint();},destroy(){alive=false;generation++;root.remove();}};
}

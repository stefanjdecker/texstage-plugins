// SPDX-License-Identifier: Apache-2.0
import {words,el,shell,problem,valuesView,answersView,workedView,aggregateView,operations,operation,key,setText} from './layout.mjs';
export function mount(ctx){const w=words(ctx.language),root=shell(ctx,'tx-overlay'),phase=el('p','',{class:'tx-phase'}),body=el('div');root.append(phase,body);root.hidden=true;let placed=false,current=null,last='',mode='',alive=true;
 function paint(){if(!alive||!current)return;root.hidden=!placed;const d=current.data;setText(phase,w.phase+': '+w[d.phase]);const token=key([d.phase,d.cursor,d.trace,d.final,d.shared,d.worked,d.count,d.counts,d.outcomes]);if(token===last)return;last=token;
  const nextMode=d.phase+(d.shared?'-shared':'');if(mode!==nextMode){root.scrollTop=0;mode=nextMode;}body.replaceChildren();
  if(d.phase==='ready'||d.phase==='predict'||d.phase==='diagnose'||d.phase==='repair'){body.append(problem(ctx.item.exercise,w,ctx.language,{compact:true}));if(d.count!==undefined)body.append(el('p',w.count+': '+d.count,{class:'tx-badge'}));}
  if(d.phase==='inspect'){const columns=el('div',undefined,{class:'tx-columns'}),list=el('div'),snapshot=el('div');list.append(el('h3',w.step+' '+d.cursor+' / '+ctx.item.exercise.schedule.length));
   const ops=operations(ctx.item.exercise);if(d.trace?.operation)list.append(el('p',d.trace.operation+': '+operation(ops[d.trace.operation])));
   ctx.item.exercise.schedule.forEach((id,i)=>list.append(el('div',(i+1)+'. '+id+' · '+ops[id].transaction,{class:'tx-order'+(id===d.trace?.operation?' tx-current':'')})));
   snapshot.append(el('h3',w.database),valuesView(d.trace?.values),el('h3',w.remembered),valuesView(d.trace?.reads));columns.append(list,snapshot);body.append(columns);}
  if(d.phase==='reveal'){body.append(aggregateView(d.outcomes,w));if(d.shared){const shared=el('div',undefined,{'data-tx':'shared-answer'});shared.append(el('h3',w.shared),answersView(d.shared,w));body.append(shared);}else body.append(workedView(d.worked,w,ctx.language));}
 }
 return{place(rects){const b=rects.box;placed=!!b;if(b)Object.assign(root.style,{left:b.x+'px',top:b.y+'px',width:b.w+'px',height:b.h+'px',fontSize:Math.max(12,Math.min(20,b.w/55))+'px'});paint();},update(next){current=next.data?next:null;paint();},destroy(){alive=false;root.remove();}};
}
